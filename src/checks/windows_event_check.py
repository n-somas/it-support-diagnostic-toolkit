"""Datenschutzfreundliche Auswertung relevanter Windows-Ereignisse."""

from __future__ import annotations

import json
import subprocess
from collections import Counter
from collections.abc import Iterable, Mapping
from datetime import datetime
from typing import Any

from src.utils.hidden_process import get_hidden_process_options


LOOKBACK_HOURS = 24
MAX_EVENTS_PER_LOG = 250
MAX_VISIBLE_GROUPS = 12

SEVERITY_ORDER = {
    "KRITISCH": 0,
    "WARNUNG": 1,
    "HINWEIS": 2,
}


def run_powershell_command(command: str, timeout: int = 25) -> str:
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


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []

    if isinstance(value, list):
        return value

    return [value]


def parse_event_payload(
    payload: str,
) -> tuple[list[dict[str, Any]], list[str], list[str]]:
    """Normalisiert die PowerShell-JSON-Ausgabe."""

    if not payload.strip():
        raise ValueError("Die Ereignisabfrage hat keine Daten geliefert.")

    parsed = json.loads(payload)

    if not isinstance(parsed, Mapping):
        raise ValueError("Unerwartetes Format der Ereignisdaten.")

    events = [
        dict(item)
        for item in _as_list(parsed.get("Events"))
        if isinstance(item, Mapping)
    ]
    errors = [
        str(item)
        for item in _as_list(parsed.get("Errors"))
        if str(item).strip()
    ]
    successful_logs = [
        str(item)
        for item in _as_list(parsed.get("SuccessfulLogs"))
        if str(item).strip()
    ]

    return events, errors, successful_logs


def classify_event(event: Mapping[str, Any]) -> dict[str, str]:
    """Ordnet ein Ereignis einer nachvollziehbaren Supportkategorie zu."""

    provider = str(event.get("ProviderName", "Unbekannte Quelle")).strip()
    provider_key = provider.casefold()
    log_name = str(event.get("LogName", "Unbekannt")).strip()
    level = int(event.get("Level", 0) or 0)

    try:
        event_id = int(event.get("Id", 0) or 0)
    except (TypeError, ValueError):
        event_id = 0

    if (
        provider_key == "microsoft-windows-kernel-power"
        and event_id == 41
    ):
        return {
            "severity": "KRITISCH",
            "category": "Unerwarteter Neustart",
            "description": (
                "Windows wurde neu gestartet, ohne zuvor sauber "
                "herunterzufahren."
            ),
            "recommendation": (
                "Stromversorgung, Temperaturen, Treiber und mögliche "
                "Systemabstürze prüfen."
            ),
        }

    if provider_key == "eventlog" and event_id == 6008:
        return {
            "severity": "KRITISCH",
            "category": "Unerwartetes Herunterfahren",
            "description": (
                "Das vorherige Herunterfahren wurde von Windows als "
                "unerwartet protokolliert."
            ),
            "recommendation": (
                "Zeitpunkt mit Kernel-Power-, Bugcheck- und "
                "Hardwareereignissen vergleichen."
            ),
        }

    if (
        "wer-systemerrorreporting" in provider_key
        and event_id == 1001
    ):
        return {
            "severity": "KRITISCH",
            "category": "Windows-Fehlerüberprüfung",
            "description": (
                "Windows wurde nach einem schwerwiegenden Systemfehler "
                "beziehungsweise Bugcheck neu gestartet."
            ),
            "recommendation": (
                "Minidump oder MEMORY.DMP mit geeigneten Debuggingtools "
                "analysieren und kürzliche Treiberänderungen prüfen."
            ),
        }

    storage_tokens = (
        "whea-logger",
        "disk",
        "ntfs",
        "storport",
        "stornvme",
        "storahci",
        "iastor",
    )

    if (
        level in {1, 2}
        and any(token in provider_key for token in storage_tokens)
    ):
        return {
            "severity": "KRITISCH",
            "category": "Hardware oder Datenträger",
            "description": (
                "Ein kritisches oder fehlerhaftes Hardware-, Speicher- "
                "oder Datenträgerereignis wurde protokolliert."
            ),
            "recommendation": (
                "Datenträgerzustand, Kabel, Controller, Treiber und "
                "Hardwarediagnose prüfen."
            ),
        }

    if provider_key == "application error" and event_id == 1000:
        return {
            "severity": "WARNUNG",
            "category": "Anwendungsabsturz",
            "description": (
                "Windows hat den Absturz einer Anwendung protokolliert."
            ),
            "recommendation": (
                "Bei wiederholtem Auftreten Anwendung, Updates und "
                "fehlerhaftes Modul untersuchen."
            ),
        }

    if (
        provider_key == "windows error reporting"
        and event_id == 1001
        and log_name.casefold() == "application"
    ):
        return {
            "severity": "WARNUNG",
            "category": "Windows-Fehlerbericht",
            "description": (
                "Windows Error Reporting hat einen Anwendungsfehler "
                "erfasst."
            ),
            "recommendation": (
                "Mit einem zeitnahen Application-Error-Ereignis "
                "abgleichen."
            ),
        }

    if "service control manager" in provider_key and level in {1, 2}:
        return {
            "severity": "WARNUNG",
            "category": "Windows-Dienstfehler",
            "description": (
                "Ein Windows-Dienst konnte nicht ordnungsgemäß starten, "
                "enden oder weiterarbeiten."
            ),
            "recommendation": (
                "Betroffenen Dienst, Starttyp, Abhängigkeiten und "
                "Dienstkonto prüfen."
            ),
        }

    if level == 1:
        return {
            "severity": "KRITISCH",
            "category": "Weiteres kritisches Ereignis",
            "description": (
                "Windows hat ein weiteres Ereignis der Ebene Kritisch "
                "protokolliert."
            ),
            "recommendation": (
                "Quelle und Ereignis-ID in der Windows-Ereignisanzeige "
                "gezielt untersuchen."
            ),
        }

    return {
        "severity": "HINWEIS",
        "category": "Weiteres Fehlerereignis",
        "description": (
            "Windows hat ein Fehlerereignis ohne spezielle "
            "Projektklassifizierung protokolliert."
        ),
        "recommendation": (
            "Bei wiederholtem Auftreten Quelle und Ereignis-ID in der "
            "Ereignisanzeige prüfen."
        ),
    }


def _format_timestamp(value: Any) -> str:
    text = str(value or "").strip()

    if not text:
        return "Zeitpunkt unbekannt"

    try:
        normalized = text.replace("Z", "+00:00")
        parsed = datetime.fromisoformat(normalized)
        return parsed.astimezone().strftime("%d.%m.%Y %H:%M")
    except (ValueError, OSError):
        return text.replace("T", " ")[:16]


def _event_id(event: Mapping[str, Any]) -> int:
    try:
        return int(event.get("Id", 0) or 0)
    except (TypeError, ValueError):
        return 0


def evaluate_events(
    events: Iterable[Mapping[str, Any]],
    query_errors: Iterable[str] | None = None,
    successful_logs: Iterable[str] | None = None,
) -> dict[str, Any]:
    """Gruppiert und bewertet Ereignisse ohne Meldungstexte zu speichern."""

    event_list = [dict(event) for event in events]
    errors = [str(error) for error in (query_errors or []) if str(error)]
    logs = sorted({str(log) for log in (successful_logs or []) if str(log)})

    if not logs and errors:
        return {
            "Zeitraum": f"Letzte {LOOKBACK_HOURS} Stunden",
            "Gelesene Protokolle": "Keine",
            "Abfragehinweise": errors,
            "Datenschutz": (
                "Es werden keine vollständigen Ereignismeldungen "
                "gespeichert."
            ),
            "Bewertung": "FEHLER",
            "Fehler": (
                "Die Ereignisprotokolle konnten nicht gelesen werden."
            ),
        }

    grouped: dict[tuple[str, int, str, str], dict[str, Any]] = {}
    raw_levels = Counter()

    for event in event_list:
        provider = str(
            event.get("ProviderName", "Unbekannte Quelle")
        ).strip()
        log_name = str(event.get("LogName", "Unbekannt")).strip()
        event_id = _event_id(event)
        level = int(event.get("Level", 0) or 0)
        raw_levels[level] += 1

        classification = classify_event(event)
        key = (
            provider,
            event_id,
            log_name,
            classification["category"],
        )

        group = grouped.setdefault(
            key,
            {
                "provider": provider,
                "event_id": event_id,
                "log_name": log_name,
                "severity": classification["severity"],
                "category": classification["category"],
                "description": classification["description"],
                "recommendation": classification["recommendation"],
                "count": 0,
                "latest": "",
            },
        )

        group["count"] += 1
        timestamp = str(event.get("TimeCreated", "") or "")

        if timestamp > str(group["latest"]):
            group["latest"] = timestamp

    groups = list(grouped.values())
    groups.sort(
        key=lambda item: (
            SEVERITY_ORDER.get(str(item["severity"]), 9),
            -int(item["count"]),
            str(item["latest"]),
        )
    )

    critical_count = sum(
        int(item["count"])
        for item in groups
        if item["severity"] == "KRITISCH"
    )
    warning_count = sum(
        int(item["count"])
        for item in groups
        if item["severity"] == "WARNUNG"
    )
    hint_count = sum(
        int(item["count"])
        for item in groups
        if item["severity"] == "HINWEIS"
    )

    if critical_count:
        rating = "KRITISCH"
        summary = (
            f"{critical_count} kritische Ereignisse in den letzten "
            f"{LOOKBACK_HOURS} Stunden erkannt."
        )
    elif warning_count:
        rating = "WARNUNG"
        summary = (
            f"{warning_count} relevante Fehlerereignisse in den letzten "
            f"{LOOKBACK_HOURS} Stunden erkannt."
        )
    elif hint_count or errors:
        rating = "HINWEIS"
        summary = (
            f"{hint_count} weitere Fehlerereignisse wurden erfasst. "
            "Sie sollten bei wiederholtem Auftreten geprüft werden."
        )
    else:
        rating = "OK"
        summary = (
            "Keine kritischen oder fehlerhaften Ereignisse im "
            f"Auswertungszeitraum erkannt."
        )

    overview = [
        (
            f"{_format_timestamp(group['latest'])} | "
            f"{group['severity']} | {group['category']} | "
            f"{group['provider']} | ID {group['event_id']} | "
            f"{group['count']}×"
        )
        for group in groups[:MAX_VISIBLE_GROUPS]
    ]

    recommendations: list[str] = []

    for group in groups:
        recommendation = str(group["recommendation"])
        if recommendation not in recommendations:
            recommendations.append(recommendation)

        if len(recommendations) >= 6:
            break

    result: dict[str, Any] = {
        "Zeitraum": f"Letzte {LOOKBACK_HOURS} Stunden",
        "Gelesene Protokolle": ", ".join(logs) if logs else "System, Application",
        "Erfasste Ereignisse": len(event_list),
        "Kritische Ebene": raw_levels.get(1, 0),
        "Fehlerebene": raw_levels.get(2, 0),
        "Kritisch bewertet": critical_count,
        "Als Warnung bewertet": warning_count,
        "Weitere Fehlerhinweise": hint_count,
        "Zusammenfassung": summary,
        "Datenschutz": (
            "Gespeichert werden nur Protokoll, Quelle, Ereignis-ID, "
            "Ebene, Zeitpunkt und Häufigkeit. Vollständige "
            "Ereignismeldungen werden nicht übernommen."
        ),
    }

    if overview:
        result["Ereignisübersicht"] = overview

    if recommendations:
        result["Handlungsempfehlungen"] = recommendations

    if len(groups) > MAX_VISIBLE_GROUPS:
        result["Weitere Ereignismuster"] = (
            len(groups) - MAX_VISIBLE_GROUPS
        )

    if errors:
        result["Abfragehinweise"] = errors

    result["Bewertung"] = rating
    return result


def get_windows_event_info() -> dict[str, Any]:
    """Liest kritische und fehlerhafte System- und Anwendungsereignisse."""

    command = rf"""
    $start = (Get-Date).AddHours(-{LOOKBACK_HOURS})
    $allEvents = @()
    $errors = @()
    $successfulLogs = @()

    foreach ($logName in @('System', 'Application')) {{
        try {{
            $events = @(
                Get-WinEvent -FilterHashtable @{{
                    LogName = $logName
                    StartTime = $start
                    Level = @(1, 2)
                }} -MaxEvents {MAX_EVENTS_PER_LOG} -ErrorAction Stop |
                Select-Object @{{
                    Name = 'LogName'
                    Expression = {{ $_.LogName }}
                }}, @{{
                    Name = 'ProviderName'
                    Expression = {{ $_.ProviderName }}
                }}, @{{
                    Name = 'Id'
                    Expression = {{ $_.Id }}
                }}, @{{
                    Name = 'Level'
                    Expression = {{ $_.Level }}
                }}, @{{
                    Name = 'TimeCreated'
                    Expression = {{ $_.TimeCreated.ToString('o') }}
                }}
            )

            $allEvents += $events
            $successfulLogs += $logName
        }}
        catch {{
            if ($_.FullyQualifiedErrorId -like '*NoMatchingEventsFound*') {{
                $successfulLogs += $logName
            }}
            else {{
                $errors += ($logName + ': ' + $_.Exception.Message)
            }}
        }}
    }}

    [PSCustomObject]@{{
        Events = @(
            $allEvents |
            Sort-Object TimeCreated -Descending |
            Select-Object -First {MAX_EVENTS_PER_LOG * 2}
        )
        Errors = @($errors)
        SuccessfulLogs = @($successfulLogs)
    }} | ConvertTo-Json -Depth 5 -Compress
    """

    try:
        payload = run_powershell_command(command)
        events, errors, successful_logs = parse_event_payload(payload)

        return evaluate_events(
            events,
            query_errors=errors,
            successful_logs=successful_logs,
        )
    except subprocess.TimeoutExpired:
        return {
            "Bewertung": "FEHLER",
            "Fehler": (
                "Die Windows-Ereignisauswertung hat das Zeitlimit "
                "überschritten."
            ),
            "Hinweis": (
                "Die restliche Systemdiagnose kann fortgesetzt werden."
            ),
        }
    except (json.JSONDecodeError, OSError, RuntimeError, ValueError) as error:
        return {
            "Bewertung": "FEHLER",
            "Fehler": str(error),
            "Hinweis": (
                "Die Windows-Ereignisprotokolle konnten nicht "
                "vollständig ausgewertet werden."
            ),
        }
