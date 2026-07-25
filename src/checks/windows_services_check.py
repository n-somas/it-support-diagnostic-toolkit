"""Prüfung ausgewählter Windows-Dienste für Support und Wartung."""

from __future__ import annotations

import json
import subprocess
from collections.abc import Iterable, Mapping
from typing import Any

from src.utils.hidden_process import get_hidden_process_options


SERVICE_RULES: dict[str, dict[str, Any]] = {
    "EventLog": {
        "label": "Windows-Ereignisprotokoll",
        "expected_running": True,
        "disabled_severity": "WARNUNG",
    },
    "MpsSvc": {
        "label": "Windows Defender Firewall",
        "expected_running": True,
        "disabled_severity": "WARNUNG",
    },
    "Dnscache": {
        "label": "DNS-Client",
        "expected_running": True,
        "disabled_severity": "WARNUNG",
    },
    "Dhcp": {
        "label": "DHCP-Client",
        "expected_running": False,
        "disabled_severity": "HINWEIS",
    },
    "wuauserv": {
        "label": "Windows Update",
        "expected_running": False,
        "disabled_severity": "WARNUNG",
    },
    "BITS": {
        "label": "Intelligenter Hintergrundübertragungsdienst",
        "expected_running": False,
        "disabled_severity": "WARNUNG",
    },
    "W32Time": {
        "label": "Windows-Zeitgeber",
        "expected_running": False,
        "disabled_severity": "HINWEIS",
    },
    "LanmanWorkstation": {
        "label": "Arbeitsstationsdienst",
        "expected_running": False,
        "disabled_severity": "HINWEIS",
    },
}

STATE_LABELS = {
    "Running": "Läuft",
    "Stopped": "Gestoppt",
    "Paused": "Pausiert",
    "Start Pending": "Wird gestartet",
    "Stop Pending": "Wird beendet",
    "Continue Pending": "Wird fortgesetzt",
    "Pause Pending": "Wird pausiert",
}

START_MODE_LABELS = {
    "Auto": "Automatisch",
    "Manual": "Manuell",
    "Disabled": "Deaktiviert",
}


def run_powershell_command(command: str, timeout: int = 20) -> str:
    """Führt PowerShell ohne sichtbares Konsolenfenster aus."""

    encoding_setup = (
        "[Console]::OutputEncoding = "
        "[System.Text.Encoding]::UTF8; "
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
        error_text = completed.stderr.strip() or (
            f"PowerShell wurde mit Code {completed.returncode} beendet."
        )
        raise RuntimeError(error_text)

    return completed.stdout.lstrip("\ufeff").strip()


def parse_service_payload(payload: str) -> list[dict[str, Any]]:
    """Wandelt die PowerShell-JSON-Ausgabe in eine einheitliche Liste um."""

    if not payload.strip():
        return []

    parsed = json.loads(payload)

    if isinstance(parsed, Mapping):
        return [dict(parsed)]

    if isinstance(parsed, list):
        return [
            dict(item)
            for item in parsed
            if isinstance(item, Mapping)
        ]

    raise ValueError("Unerwartetes Format der Dienstedaten.")


def evaluate_services(
    services: Iterable[Mapping[str, Any]],
) -> dict[str, Any]:
    """Bewertet Dienststatus und Starttyp ohne unnötige Fehlalarme."""

    service_map = {
        str(service.get("Name", "")).casefold(): service
        for service in services
        if service.get("Name")
    }

    details: dict[str, str] = {}
    warnings: list[str] = []
    hints: list[str] = []

    running_count = 0
    stopped_on_demand_count = 0
    disabled_count = 0
    found_count = 0

    for service_name, rule in SERVICE_RULES.items():
        label = str(rule["label"])
        service = service_map.get(service_name.casefold())

        if service is None:
            details[label] = "Nicht gefunden"
            hints.append(f"{label}: Dienst wurde nicht gefunden.")
            continue

        found_count += 1
        state = str(service.get("State", "Unbekannt"))
        start_mode = str(service.get("StartMode", "Unbekannt"))

        state_label = STATE_LABELS.get(state, state or "Unbekannt")
        start_mode_label = START_MODE_LABELS.get(
            start_mode,
            start_mode or "Unbekannt",
        )

        assessment = "Unauffällig"

        if state == "Running":
            running_count += 1
            assessment = "Läuft erwartungsgemäß"
        elif start_mode == "Disabled":
            disabled_count += 1
            assessment = "Dienst ist deaktiviert"
            message = f"{label}: Starttyp ist deaktiviert."

            if rule["disabled_severity"] == "WARNUNG":
                warnings.append(message)
            else:
                hints.append(message)
        elif bool(rule["expected_running"]):
            assessment = "Sollte normalerweise laufen"
            warnings.append(
                f"{label}: Dienst ist {state_label.lower()}."
            )
        else:
            stopped_on_demand_count += 1
            assessment = "Bedarfsgesteuerter Ruhezustand"

        details[label] = (
            f"{state_label} | Starttyp: {start_mode_label} | "
            f"{assessment}"
        )

    if warnings:
        rating = "WARNUNG"
        summary = (
            f"{len(warnings)} relevante Dienstauffälligkeiten erkannt."
        )
    elif hints:
        rating = "HINWEIS"
        summary = (
            f"{len(hints)} Hinweise zu Windows-Diensten erkannt."
        )
    else:
        rating = "OK"
        summary = (
            "Die ausgewählten Windows-Dienste sind unauffällig."
        )

    result: dict[str, Any] = {
        "Geprüfte Dienste": len(SERVICE_RULES),
        "Gefundene Dienste": found_count,
        "Laufend": running_count,
        "Bedarfsgesteuert gestoppt": stopped_on_demand_count,
        "Deaktiviert": disabled_count,
        "Zusammenfassung": summary,
    }

    if warnings:
        result["Warnungen"] = warnings

    if hints:
        result["Hinweise"] = hints

    result.update(details)
    result["Bewertung"] = rating
    return result


def get_windows_services_info() -> dict[str, Any]:
    """Liest ausgewählte Windows-Dienste aus und bewertet sie."""

    service_names = ", ".join(
        f"'{service_name}'"
        for service_name in SERVICE_RULES
    )

    command = (
        f"$names = @({service_names}); "
        "$services = Get-CimInstance Win32_Service | "
        "Where-Object { $names -contains $_.Name } | "
        "Select-Object Name, DisplayName, State, StartMode, Status; "
        "$services | ConvertTo-Json -Depth 3 -Compress"
    )

    try:
        payload = run_powershell_command(command)
        services = parse_service_payload(payload)
        return evaluate_services(services)
    except subprocess.TimeoutExpired:
        return {
            "Bewertung": "FEHLER",
            "Fehler": "Die Dienstprüfung hat das Zeitlimit überschritten.",
            "Hinweis": (
                "Die restliche Systemdiagnose kann fortgesetzt werden."
            ),
        }
    except (json.JSONDecodeError, OSError, RuntimeError, ValueError) as error:
        return {
            "Bewertung": "FEHLER",
            "Fehler": str(error),
            "Hinweis": (
                "Die Windows-Dienste konnten nicht vollständig "
                "ausgelesen werden."
            ),
        }
