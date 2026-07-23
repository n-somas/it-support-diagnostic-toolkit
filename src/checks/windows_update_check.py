"""Erweiterte Prüfung auf Windows- und Treiberupdates."""

from __future__ import annotations

import json
import subprocess
from typing import Any

from src.utils.hidden_process import get_hidden_process_options


SCRIPT = r"""
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

try {
    $service = Get-Service wuauserv -ErrorAction Stop
    $serviceStatus = if ($service.Status -eq 'Running') {'Aktiv'} else {'Gestoppt'}
} catch {
    $serviceStatus = 'Nicht ermittelbar'
}

$lastUpdate = 'Nicht ermittelbar'
try {
    $hotfix = Get-HotFix | Sort-Object InstalledOn -Descending | Select-Object -First 1
    if ($hotfix) {
        $date = if ($hotfix.InstalledOn) {
            $hotfix.InstalledOn.ToString('dd.MM.yyyy')
        } else {
            'Datum unbekannt'
        }
        $lastUpdate = "$($hotfix.HotFixID) vom $date"
    }
} catch {}

$pendingReboot = (
    (Test-Path 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Component Based Servicing\RebootPending') -or
    (Test-Path 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\WindowsUpdate\Auto Update\RebootRequired')
)

try {
    $pendingRename = Get-ItemProperty(
        'HKLM:\SYSTEM\CurrentControlSet\Control\Session Manager'
    ) -Name PendingFileRenameOperations -ErrorAction SilentlyContinue
    if ($pendingRename) {$pendingReboot = $true}
} catch {}

$updates = @()
$queryOk = $false
$queryError = ''

try {
    $session = New-Object -ComObject Microsoft.Update.Session
    $searcher = $session.CreateUpdateSearcher()
    $result = $searcher.Search('IsInstalled=0 and IsHidden=0')

    for ($i = 0; $i -lt $result.Updates.Count; $i++) {
        $update = $result.Updates.Item($i)
        $updates += [PSCustomObject]@{
            Title = [string]$update.Title
            Type = if ([int]$update.Type -eq 2) {'Treiber'} else {'Windows'}
            Severity = [string]$update.MsrcSeverity
        }
    }
    $queryOk = $true
} catch {
    $queryError = $_.Exception.Message
}

[PSCustomObject]@{
    ServiceStatus = $serviceStatus
    LastUpdate = $lastUpdate
    PendingReboot = [bool]$pendingReboot
    QueryOk = [bool]$queryOk
    QueryError = $queryError
    Updates = $updates
} | ConvertTo-Json -Depth 6 -Compress
"""


def get_windows_update_info() -> dict[str, Any]:
    try:
        process = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", SCRIPT],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
            timeout=150,
            check=False,
            **get_hidden_process_options(),
        )
    except subprocess.TimeoutExpired:
        return {
            "Update erforderlich": "Nicht ermittelbar",
            "Hinweis": "Die Update-Suche hat zu lange gedauert.",
            "Bewertung": "HINWEIS",
        }

    if process.returncode != 0 or not process.stdout.strip():
        return {
            "Update erforderlich": "Nicht ermittelbar",
            "Hinweis": process.stderr.strip() or "Keine Updatedaten erhalten.",
            "Bewertung": "HINWEIS",
        }

    try:
        raw = json.loads(process.stdout.strip().lstrip("\ufeff"))
    except json.JSONDecodeError as error:
        return {
            "Update erforderlich": "Nicht ermittelbar",
            "Hinweis": f"Updatedaten ungültig: {error}",
            "Bewertung": "HINWEIS",
        }

    updates = _list(raw.get("Updates"))
    windows = [item for item in updates if item.get("Type") != "Treiber"]
    drivers = [item for item in updates if item.get("Type") == "Treiber"]
    reboot = bool(raw.get("PendingReboot"))
    query_ok = bool(raw.get("QueryOk"))

    if reboot:
        status = "Ja – Neustart erforderlich"
        rating = "WARNUNG"
        note = "Windows meldet einen ausstehenden Neustart."
    elif windows:
        status = f"Ja – {len(windows)} Windows-Update(s) verfügbar"
        rating = "WARNUNG"
        note = "Windows-Updates sind verfügbar und sollten geprüft werden."
    elif drivers:
        status = f"Optional – {len(drivers)} Treiberupdate(s) verfügbar"
        rating = "HINWEIS"
        note = "Optionale Treiberupdates sind über Windows Update verfügbar."
    elif query_ok:
        status = "Nein – keine ausstehenden Updates gemeldet"
        rating = "OK"
        note = "Windows meldet aktuell keine ausstehenden Updates."
    else:
        status = "Nicht vollständig ermittelbar"
        rating = "HINWEIS"
        note = "Die Suche nach verfügbaren Updates war nicht vollständig möglich."

    titles = []
    for item in updates[:12]:
        label = f"{item.get('Type', 'Windows')}: {item.get('Title', 'Unbekanntes Update')}"
        if item.get("Severity"):
            label += f" | Schweregrad {item['Severity']}"
        titles.append(label)

    result = {
        "Windows Update Dienst": raw.get("ServiceStatus") or "Nicht ermittelbar",
        "Letztes installiertes Update": raw.get("LastUpdate") or "Nicht ermittelbar",
        "Update erforderlich": status,
        "Verfügbare Windows-Updates": len(windows),
        "Verfügbare Treiberupdates": len(drivers),
        "Neustart erforderlich": "Ja" if reboot else "Nein",
        "Ausstehende Updates": titles or ["Keine"],
        "Hinweis": note,
        "Bewertung": rating,
    }

    if raw.get("QueryError"):
        result["Technischer Hinweis"] = str(raw["QueryError"])

    return result


def _list(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    if isinstance(value, dict):
        return [value]
    return []
