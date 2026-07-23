"""Lokale Hardwareinventarisierung für Windows."""

from __future__ import annotations

import json
import subprocess
from typing import Any

from src.utils.hidden_process import get_hidden_process_options


SCRIPT = r"""
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$computer = Get-CimInstance Win32_ComputerSystem
$cpu = Get-CimInstance Win32_Processor | Select-Object -First 1
$board = Get-CimInstance Win32_BaseBoard | Select-Object -First 1
$bios = Get-CimInstance Win32_BIOS | Select-Object -First 1

$ram = @(
    Get-CimInstance Win32_PhysicalMemory | ForEach-Object {
        $type = switch ([int]$_.SMBIOSMemoryType) {
            20 {'DDR'} 21 {'DDR2'} 24 {'DDR3'} 26 {'DDR4'} 34 {'DDR5'}
            default {'Unbekannt'}
        }
        [PSCustomObject]@{
            Capacity = [uint64]$_.Capacity
            Speed = [int]$_.ConfiguredClockSpeed
            Manufacturer = [string]$_.Manufacturer
            Type = $type
        }
    }
)

$gpus = @(
    Get-CimInstance Win32_VideoController | ForEach-Object {
        [PSCustomObject]@{
            Name = [string]$_.Name
            DriverVersion = [string]$_.DriverVersion
            DriverDate = if ($_.DriverDate) {
                $_.DriverDate.ToString('yyyy-MM-dd')
            } else {''}
        }
    }
)

try {
    $disks = @(
        Get-PhysicalDisk -ErrorAction Stop | ForEach-Object {
            [PSCustomObject]@{
                Name = [string]$_.FriendlyName
                MediaType = [string]$_.MediaType
                BusType = [string]$_.BusType
                Size = [uint64]$_.Size
                Health = [string]$_.HealthStatus
            }
        }
    )
} catch {
    $disks = @(
        Get-CimInstance Win32_DiskDrive | ForEach-Object {
            [PSCustomObject]@{
                Name = [string]$_.Model
                MediaType = [string]$_.MediaType
                BusType = [string]$_.InterfaceType
                Size = [uint64]$_.Size
                Health = [string]$_.Status
            }
        }
    )
}

$network = @(
    Get-CimInstance Win32_NetworkAdapter |
        Where-Object {$_.PhysicalAdapter -eq $true -and $_.NetEnabled -eq $true} |
        ForEach-Object {
            [PSCustomObject]@{
                Name = [string]$_.Name
                Connection = [string]$_.NetConnectionID
                Speed = if ($_.Speed) {[uint64]$_.Speed} else {0}
            }
        }
)

$errors = @()
try {
    $errors = @(
        Get-PnpDevice -PresentOnly -ErrorAction Stop |
            Where-Object {$_.Status -ne 'OK'} |
            Select-Object -First 15 |
            ForEach-Object {
                [PSCustomObject]@{
                    Name = [string]$_.FriendlyName
                    Class = [string]$_.Class
                    Status = [string]$_.Status
                }
            }
    )
} catch {}

[PSCustomObject]@{
    Computer = [PSCustomObject]@{
        Manufacturer = [string]$computer.Manufacturer
        Model = [string]$computer.Model
        SystemType = [string]$computer.SystemType
        TotalMemory = [uint64]$computer.TotalPhysicalMemory
    }
    CPU = [PSCustomObject]@{
        Name = [string]$cpu.Name
        Cores = [int]$cpu.NumberOfCores
        Threads = [int]$cpu.NumberOfLogicalProcessors
    }
    RAM = $ram
    GPUs = $gpus
    Board = [PSCustomObject]@{
        Manufacturer = [string]$board.Manufacturer
        Product = [string]$board.Product
    }
    BIOS = [PSCustomObject]@{
        Manufacturer = [string]$bios.Manufacturer
        Version = [string]$bios.SMBIOSBIOSVersion
        Date = if ($bios.ReleaseDate) {
            $bios.ReleaseDate.ToString('yyyy-MM-dd')
        } else {''}
    }
    Disks = $disks
    Network = $network
    DeviceErrors = $errors
} | ConvertTo-Json -Depth 7 -Compress
"""


def get_hardware_info() -> dict[str, Any]:
    try:
        process = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", SCRIPT],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
            timeout=90,
            check=False,
            **get_hidden_process_options(),
        )
    except subprocess.TimeoutExpired:
        return {
            "Hinweis": "Hardwareabfrage hat zu lange gedauert.",
            "Bewertung": "FEHLER",
        }

    if process.returncode != 0 or not process.stdout.strip():
        return {
            "Hinweis": process.stderr.strip() or "Keine Hardwaredaten erhalten.",
            "Bewertung": "FEHLER",
        }

    try:
        raw = json.loads(process.stdout.strip().lstrip("\ufeff"))
    except json.JSONDecodeError as error:
        return {
            "Hinweis": f"Hardwaredaten ungültig: {error}",
            "Bewertung": "FEHLER",
        }

    return _format(raw)


def _format(raw: dict[str, Any]) -> dict[str, Any]:
    computer = raw.get("Computer") or {}
    cpu = raw.get("CPU") or {}
    board = raw.get("Board") or {}
    bios = raw.get("BIOS") or {}

    ram = _list(raw.get("RAM"))
    gpus = _list(raw.get("GPUs"))
    disks = _list(raw.get("Disks"))
    network = _list(raw.get("Network"))
    errors = _list(raw.get("DeviceErrors"))

    system = " ".join(
        item
        for item in (
            _clean(computer.get("Manufacturer")),
            _clean(computer.get("Model")),
        )
        if item
    ) or "Nicht ermittelbar"

    ram_lines = []
    for item in ram:
        line = f"{_gb(item.get('Capacity'))} {item.get('Type') or 'RAM'}"
        if item.get("Speed"):
            line += f" mit {item['Speed']} MHz"
        manufacturer = _clean(item.get("Manufacturer"))
        if manufacturer:
            line += f" von {manufacturer}"
        ram_lines.append(line)

    gpu_lines = []
    for item in gpus:
        line = _clean(item.get("Name")) or "Unbekannte Grafikkarte"
        version = _clean(item.get("DriverVersion"))
        date = _clean(item.get("DriverDate"))
        if version:
            line += f" | Treiber {version}"
        if date:
            line += f" vom {date}"
        gpu_lines.append(line)

    disk_lines = [
        (
            f"{_clean(item.get('Name')) or 'Unbekanntes Laufwerk'} | "
            f"{_clean(item.get('MediaType')) or 'Datenträger'}, "
            f"{_gb(item.get('Size'))}, "
            f"{_clean(item.get('BusType')) or 'Bus unbekannt'}, "
            f"Status {_clean(item.get('Health')) or 'unbekannt'}"
        )
        for item in disks
    ]

    network_lines = []
    for item in network:
        title = (
            _clean(item.get("Connection"))
            or _clean(item.get("Name"))
            or "Netzwerkadapter"
        )
        extras = []
        hardware_name = _clean(item.get("Name"))
        if hardware_name and hardware_name != title:
            extras.append(hardware_name)
        speed = _speed(item.get("Speed"))
        if speed:
            extras.append(speed)
        network_lines.append(
            title + (f" | {', '.join(extras)}" if extras else "")
        )

    error_lines = []
    for item in errors:
        line = (
            f"{_clean(item.get('Name')) or 'Unbekanntes Gerät'} | "
            f"{_clean(item.get('Status')) or 'Fehler'}"
        )
        device_class = _clean(item.get("Class"))
        if device_class:
            line += f", {device_class}"
        error_lines.append(line)

    return {
        "System": system,
        "Systemtyp": _clean(computer.get("SystemType")) or "Nicht ermittelbar",
        "Prozessor": _clean(cpu.get("Name")) or "Nicht ermittelbar",
        "CPU-Details": (
            f"{cpu.get('Cores', 0)} Kerne, "
            f"{cpu.get('Threads', 0)} logische Prozessoren"
        ),
        "Arbeitsspeicher": _gb(computer.get("TotalMemory")),
        "RAM-Module": ram_lines or ["Nicht ermittelbar"],
        "Grafikkarten": gpu_lines or ["Nicht ermittelbar"],
        "Mainboard": " ".join(
            item
            for item in (
                _clean(board.get("Manufacturer")),
                _clean(board.get("Product")),
            )
            if item
        ) or "Nicht ermittelbar",
        "BIOS-Version": _clean(bios.get("Version")) or "Nicht ermittelbar",
        "BIOS-Hersteller": _clean(bios.get("Manufacturer")) or "Nicht ermittelbar",
        "BIOS-Datum": _clean(bios.get("Date")) or "Nicht ermittelbar",
        "Laufwerke": disk_lines or ["Nicht ermittelbar"],
        "Netzwerkadapter": network_lines or ["Nicht ermittelbar"],
        "Geräte mit Fehlerstatus": error_lines or ["Keine"],
        "Hinweis": (
            f"{len(error_lines)} Gerät(e) melden einen Fehlerstatus."
            if error_lines
            else "Keine Geräte mit Fehlerstatus erkannt."
        ),
        "Bewertung": "WARNUNG" if error_lines else "INFO",
    }


def _list(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    if isinstance(value, dict):
        return [value]
    return []


def _gb(value: Any) -> str:
    try:
        return f"{float(value) / (1024 ** 3):.2f} GB"
    except (TypeError, ValueError):
        return "Nicht ermittelbar"


def _speed(value: Any) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return ""
    if number >= 1_000_000_000:
        return f"{number / 1_000_000_000:.1f} Gbit/s"
    if number > 0:
        return f"{number / 1_000_000:.0f} Mbit/s"
    return ""


def _clean(value: Any) -> str:
    return " ".join(str(value or "").split())
