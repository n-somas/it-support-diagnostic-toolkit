"""Analyse von Netzwerkadaptern und Verbindungsqualität unter Windows."""

from __future__ import annotations

import json
import re
import socket
import subprocess
from collections.abc import Iterable, Mapping
from typing import Any

from src.utils.hidden_process import get_hidden_process_options


VIRTUAL_MARKERS = (
    "virtual", "hyper-v", "vmware", "virtualbox",
    "vpn", "tap-", "wsl", "docker", "loopback", "bluetooth",
)


def run_powershell_command(command: str, timeout: int = 30) -> str:
    encoding_setup = (
        "[Console]::OutputEncoding = [System.Text.Encoding]::UTF8; "
        "$OutputEncoding = [System.Text.Encoding]::UTF8; "
    )
    completed = subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-NonInteractive",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            encoding_setup + command,
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        **get_hidden_process_options(),
    )
    if completed.returncode != 0:
        raise RuntimeError(
            completed.stderr.strip()
            or f"PowerShell-Code {completed.returncode}"
        )
    return completed.stdout.lstrip("\ufeff").strip()


def parse_json_payload(payload: str) -> list[dict[str, Any]]:
    if not payload.strip():
        return []
    parsed = json.loads(payload)
    if isinstance(parsed, Mapping):
        return [dict(parsed)]
    if isinstance(parsed, list):
        return [dict(item) for item in parsed if isinstance(item, Mapping)]
    raise ValueError("Unerwartetes Format der Netzwerkdaten.")


def resolve_domain(domain: str) -> dict[str, str]:
    try:
        addresses = sorted(set(socket.gethostbyname_ex(domain)[2]))
    except socket.gaierror:
        return {"Status": "FEHLER", "Adressen": "Nicht auflösbar"}
    return {"Status": "OK", "Adressen": ", ".join(addresses)}


def parse_link_speed_mbps(value: Any) -> float | None:
    if value is None:
        return None
    text = str(value).strip().replace(",", ".")
    match = re.search(r"(\d+(?:\.\d+)?)\s*([GMK]?bps)", text, re.I)
    if match is None:
        try:
            return float(text)
        except ValueError:
            return None
    number = float(match.group(1))
    unit = match.group(2).casefold()
    if unit == "gbps":
        return number * 1000
    if unit == "kbps":
        return number / 1000
    return number


def is_virtual_adapter(adapter: Mapping[str, Any]) -> bool:
    combined = " ".join(
        str(adapter.get(key, ""))
        for key in ("Name", "InterfaceDescription", "MediaType")
    ).casefold()
    return any(marker in combined for marker in VIRTUAL_MARKERS)


def as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value).strip()
    return [text] if text else []


def number(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(str(value).replace(",", "."))
    except ValueError:
        return None


def evaluate_network_quality(
    adapters: Iterable[Mapping[str, Any]],
    probes: Iterable[Mapping[str, Any]],
    dns_result: Mapping[str, Any],
) -> dict[str, Any]:
    adapter_list = [dict(item) for item in adapters]
    probe_list = [dict(item) for item in probes]
    active = [
        item for item in adapter_list
        if str(item.get("Status", "")).casefold() == "up"
    ]
    physical = [item for item in active if not is_virtual_adapter(item)]
    virtual = [item for item in active if is_virtual_adapter(item)]

    warnings: list[str] = []
    hints: list[str] = []
    details: list[dict[str, Any]] = []
    gateways: list[str] = []
    dns_servers: list[str] = []
    ipv4_values: list[str] = []

    for item in active:
        name = str(item.get("Name", "Unbekannter Adapter"))
        ipv4 = as_list(item.get("IPv4Address"))
        adapter_gateways = as_list(item.get("IPv4DefaultGateway"))
        adapter_dns = as_list(item.get("DnsServers"))
        speed = parse_link_speed_mbps(item.get("LinkSpeed"))
        virtual_adapter = is_virtual_adapter(item)
        profile = str(item.get("NetworkCategory", "Nicht ermittelt"))

        ipv4_values.extend(ipv4)
        gateways.extend(adapter_gateways)
        dns_servers.extend(adapter_dns)

        adapter_messages: list[str] = []

        if any(value.startswith("169.254.") for value in ipv4):
            message = "APIPA-Adresse erkannt; DHCP oder Netzwerk prüfen."
            warnings.append(f"{name}: {message}")
            adapter_messages.append(message)

        if not ipv4 and not virtual_adapter:
            message = "Aktiver physischer Adapter besitzt keine IPv4-Adresse."
            warnings.append(f"{name}: {message}")
            adapter_messages.append(message)

        if speed is not None and speed < 100 and not virtual_adapter:
            message = f"Niedrige Link-Geschwindigkeit von {speed:g} Mbit/s."
            hints.append(f"{name}: {message}")
            adapter_messages.append(message)

        if profile.casefold() in {"public", "öffentlich"}:
            message = "Öffentliches Netzwerkprofil aktiv."
            hints.append(f"{name}: {message}")
            adapter_messages.append(message)

        details.append(
            {
                "Name": name,
                "Beschreibung": str(
                    item.get("InterfaceDescription", "Nicht ermittelt")
                ),
                "Virtuell": "Ja" if virtual_adapter else "Nein",
                "Link-Geschwindigkeit": (
                    f"{speed:g} Mbit/s"
                    if speed is not None
                    else "Nicht ermittelt"
                ),
                "DHCP": str(item.get("Dhcp", "Nicht ermittelt")),
                "IPv4-Adresse": ", ".join(ipv4) or "Nicht vorhanden",
                "Standardgateway": (
                    ", ".join(adapter_gateways) or "Nicht vorhanden"
                ),
                "DNS-Server": ", ".join(adapter_dns) or "Nicht vorhanden",
                "Netzwerkprofil": profile,
                "Hinweise": adapter_messages or ["Keine Auffälligkeit erkannt."],
            }
        )

    unique_gateways = sorted(set(gateways))
    unique_dns = sorted(set(dns_servers))
    unique_ipv4 = sorted(set(ipv4_values))

    if not physical:
        warnings.append("Kein aktiver physischer Netzwerkadapter erkannt.")
    if len(unique_gateways) > 1:
        hints.append("Mehrere Standardgateways erkannt.")
    if physical and not unique_gateways:
        hints.append("Kein IPv4-Standardgateway erkannt.")
    if physical and not unique_dns:
        warnings.append("Keine DNS-Server auf aktiven Adaptern erkannt.")

    successful = 0
    probe_details: list[dict[str, Any]] = []

    for probe in probe_list:
        target = str(probe.get("Target", "Unbekannt"))
        sent = int(number(probe.get("Sent")) or 0)
        received = int(number(probe.get("Received")) or 0)
        loss = number(probe.get("LossPercent"))
        latency = number(probe.get("AverageMs"))

        if sent > 0 and loss is None:
            loss = max(0, sent - received) / sent * 100
        if received > 0:
            successful += 1

        if loss is not None:
            if loss >= 50:
                warnings.append(f"{target}: {loss:g} % Paketverlust.")
            elif loss > 0:
                hints.append(f"{target}: {loss:g} % Paketverlust.")

        if latency is not None:
            if latency >= 250:
                warnings.append(
                    f"{target}: sehr hohe mittlere Latenz von {latency:g} ms."
                )
            elif latency >= 100:
                hints.append(
                    f"{target}: erhöhte mittlere Latenz von {latency:g} ms."
                )

        probe_details.append(
            {
                "Ziel": target,
                "Gesendet": sent,
                "Empfangen": received,
                "Paketverlust": (
                    f"{loss:g} %" if loss is not None else "Nicht messbar"
                ),
                "Mittlere Latenz": (
                    f"{latency:g} ms"
                    if latency is not None
                    else "Nicht messbar"
                ),
            }
        )

    dns_ok = str(dns_result.get("Status", "")).upper() == "OK"

    if successful == 0 and not dns_ok:
        warnings.append(
            "Weder externe Ziele noch die DNS-Auflösung waren erfolgreich."
        )
    elif successful == 0 and dns_ok:
        hints.append(
            "Ping-Antworten fehlen, die DNS-Auflösung funktioniert."
        )
    elif successful > 0 and not dns_ok:
        warnings.append(
            "Externe Ziele sind erreichbar, aber DNS ist fehlgeschlagen."
        )

    if warnings:
        rating = "WARNUNG"
        summary = f"{len(warnings)} Netzwerkauffälligkeiten erkannt."
    elif hints:
        rating = "HINWEIS"
        summary = f"{len(hints)} Hinweise zur Netzwerkverbindung erkannt."
    else:
        rating = "OK"
        summary = "Netzwerkadapter und Verbindungsqualität sind unauffällig."

    result: dict[str, Any] = {
        "Aktive Adapter": len(active),
        "Physische Adapter": len(physical),
        "Virtuelle Adapter": len(virtual),
        "IPv4-Adressen": ", ".join(unique_ipv4) or "Nicht vorhanden",
        "Standardgateways": ", ".join(unique_gateways) or "Nicht vorhanden",
        "DNS-Server": ", ".join(unique_dns) or "Nicht vorhanden",
        "Erfolgreiche Verbindungstests": (
            f"{successful} von {len(probe_list)}"
        ),
        "DNS-Auflösung": str(dns_result.get("Status", "FEHLER")),
        "DNS-Zieladressen": str(
            dns_result.get("Adressen", "Nicht auflösbar")
        ),
        "Zusammenfassung": summary,
        "Adapterdetails": details,
        "Verbindungstests": probe_details,
        "Bewertung": rating,
    }
    if warnings:
        result["Warnungen"] = warnings
    if hints:
        result["Hinweise"] = hints
    return result


def get_adapter_data() -> list[dict[str, Any]]:
    """Liest Adapterdaten über getrennte Windows-Schnittstellen aus."""

    command = r"""
$ErrorActionPreference = 'Stop'

$profiles = @{}
Get-NetConnectionProfile -ErrorAction SilentlyContinue |
    ForEach-Object {
        $profiles[[int]$_.InterfaceIndex] = [string]$_.NetworkCategory
    }

$configurations = @{}
Get-CimInstance `
    -ClassName Win32_NetworkAdapterConfiguration `
    -ErrorAction SilentlyContinue |
    Where-Object { $_.InterfaceIndex -ne $null } |
    ForEach-Object {
        $configurations[[int]$_.InterfaceIndex] = $_
    }

$items = @(
    Get-NetAdapter -ErrorAction Stop |
        Where-Object { $_.Status -eq 'Up' } |
        ForEach-Object {
            $adapter = $_
            $index = [int]$adapter.ifIndex
            $configuration = $configurations[$index]

            $ipv4 = @(
                Get-NetIPAddress `
                    -InterfaceIndex $index `
                    -AddressFamily IPv4 `
                    -ErrorAction SilentlyContinue |
                    Where-Object {
                        $_.IPAddress -and
                        $_.IPAddress -ne '127.0.0.1'
                    } |
                    ForEach-Object {
                        [string]$_.IPAddress
                    }
            )

            $gateways = @(
                Get-NetRoute `
                    -InterfaceIndex $index `
                    -AddressFamily IPv4 `
                    -DestinationPrefix '0.0.0.0/0' `
                    -ErrorAction SilentlyContinue |
                    Where-Object {
                        $_.NextHop -and
                        $_.NextHop -ne '0.0.0.0'
                    } |
                    Sort-Object RouteMetric |
                    ForEach-Object {
                        [string]$_.NextHop
                    }
            )

            $dnsServers = @(
                Get-DnsClientServerAddress `
                    -InterfaceIndex $index `
                    -AddressFamily IPv4 `
                    -ErrorAction SilentlyContinue |
                    ForEach-Object {
                        $_.ServerAddresses
                    } |
                    Where-Object {
                        $_ -match '^\d{1,3}(?:\.\d{1,3}){3}$'
                    } |
                    ForEach-Object {
                        [string]$_
                    }
            )

            $dhcp = 'Nicht ermittelt'

            if ($configuration -ne $null) {
                if ($configuration.DHCPEnabled) {
                    $dhcp = 'Enabled'
                }
                else {
                    $dhcp = 'Disabled'
                }
            }

            [pscustomobject]@{
                Name = [string]$adapter.Name
                InterfaceDescription = [string]$adapter.InterfaceDescription
                InterfaceIndex = $index
                Status = [string]$adapter.Status
                MediaType = [string]$adapter.MediaType
                LinkSpeed = [string]$adapter.LinkSpeed
                Dhcp = $dhcp
                IPv4Address = $ipv4
                IPv4DefaultGateway = $gateways
                DnsServers = $dnsServers
                NetworkCategory = if (
                    $profiles.ContainsKey($index)
                ) {
                    $profiles[$index]
                }
                else {
                    'Nicht ermittelt'
                }
            }
        }
)

if ($items.Count -eq 0) {
    '[]'
}
else {
    $items |
        Sort-Object Name |
        ConvertTo-Json -Depth 5 -Compress
}
"""

    return parse_json_payload(
        run_powershell_command(command)
    )


def measure_connection_quality(
    targets: Iterable[str],
) -> list[dict[str, Any]]:
    values = ", ".join(f"'{target}'" for target in targets)
    command = f"""
$targets = @({values})
$results = @(
    foreach ($target in $targets) {{
        $replies = @(
            Test-Connection -ComputerName $target -Count 4 `
                -ErrorAction SilentlyContinue
        )
        $times = @(
            $replies | ForEach-Object {{
                if ($_.ResponseTime -ne $null) {{
                    [double]$_.ResponseTime
                }} elseif ($_.Latency -ne $null) {{
                    [double]$_.Latency
                }}
            }}
        )
        $received = $replies.Count
        $average = $null
        if ($times.Count -gt 0) {{
            $average = [math]::Round(
                ($times | Measure-Object -Average).Average,
                1
            )
        }}
        [pscustomobject]@{{
            Target = [string]$target
            Sent = 4
            Received = [int]$received
            LossPercent = [math]::Round(
                ((4 - $received) / 4) * 100,
                1
            )
            AverageMs = $average
        }}
    }}
)
$results | ConvertTo-Json -Depth 3 -Compress
"""
    return parse_json_payload(
        run_powershell_command(command, timeout=25)
    )


def get_network_info() -> dict[str, Any]:
    try:
        adapters = get_adapter_data()
    except (
        json.JSONDecodeError,
        OSError,
        RuntimeError,
        subprocess.TimeoutExpired,
        ValueError,
    ) as error:
        return {
            "Bewertung": "FEHLER",
            "Fehler": str(error),
            "Hinweis": (
                "Die Netzwerkadapter konnten nicht vollständig "
                "ausgelesen werden."
            ),
        }

    try:
        probes = measure_connection_quality(("1.1.1.1", "8.8.8.8"))
    except Exception:
        probes = [
            {
                "Target": "1.1.1.1",
                "Sent": 0,
                "Received": 0,
                "LossPercent": None,
                "AverageMs": None,
            },
            {
                "Target": "8.8.8.8",
                "Sent": 0,
                "Received": 0,
                "LossPercent": None,
                "AverageMs": None,
            },
        ]

    return evaluate_network_quality(
        adapters,
        probes,
        resolve_domain("www.microsoft.com"),
    )
