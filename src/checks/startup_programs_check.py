"""Analyse automatisch gestarteter Windows-Programme."""

from __future__ import annotations

import json
import re
import subprocess
from collections.abc import Iterable, Mapping
from typing import Any

from src.utils.hidden_process import get_hidden_process_options


SCRIPT_HOSTS_WARNING = (
    "powershell",
    "pwsh",
    "mshta",
    "wscript",
    "cscript",
    "regsvr32",
)

SCRIPT_HOSTS_HINT = (
    "cmd",
    "rundll32",
)

SCRIPT_EXTENSIONS = (
    ".ps1",
    ".vbs",
    ".js",
    ".jse",
    ".bat",
    ".cmd",
)

SUSPICIOUS_PATH_PARTS = (
    "\\appdata\\local\\temp\\",
    "\\windows\\temp\\",
    "\\downloads\\",
    "\\users\\public\\",
    "\\$recycle.bin\\",
)

INVALID_SIGNATURE_STATES = {
    "hashmismatch",
    "nottrusted",
    "unknownerror",
    "notsupportedfileformat",
    "incompatible",
}


def run_powershell_command(
    command: str,
    timeout: int = 35,
) -> str:
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
            "PowerShell wurde mit Code "
            f"{completed.returncode} beendet."
        )
        raise RuntimeError(error_text)

    return completed.stdout.lstrip("\ufeff").strip()


def parse_startup_payload(
    payload: str,
) -> list[dict[str, Any]]:
    """Wandelt die PowerShell-Ausgabe in eine einheitliche Liste um."""

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

    raise ValueError("Unerwartetes Format der Autostartdaten.")


def _contains_program(command: str, names: Iterable[str]) -> str | None:
    for name in names:
        pattern = rf"(?i)(?:^|[\\/\s\"']){re.escape(name)}(?:\.exe)?(?:\s|$)"
        if re.search(pattern, command):
            return name
    return None


def _normalise_bool(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if value is None:
        return None

    text = str(value).strip().casefold()
    if text in {"true", "1", "yes", "ja"}:
        return True
    if text in {"false", "0", "no", "nein"}:
        return False
    return None


def evaluate_startup_programs(
    startup_items: Iterable[Mapping[str, Any]],
) -> dict[str, Any]:
    """Bewertet Autostarteinträge mit nachvollziehbaren Heuristiken."""

    unique_items: list[Mapping[str, Any]] = []
    seen: set[tuple[str, str, str, str]] = set()

    for item in startup_items:
        key = (
            str(item.get("Name", "")).strip().casefold(),
            str(item.get("Command", "")).strip().casefold(),
            str(item.get("Location", "")).strip().casefold(),
            str(item.get("User", "")).strip().casefold(),
        )
        if key in seen:
            continue
        seen.add(key)
        unique_items.append(item)

    details: list[dict[str, Any]] = []
    warning_messages: list[str] = []
    hint_messages: list[str] = []

    warning_count = 0
    hint_count = 0
    valid_signed_count = 0
    missing_target_count = 0

    for item in unique_items:
        name = str(item.get("Name", "")).strip() or "Unbenannter Eintrag"
        command = str(item.get("Command", "")).strip()
        location = str(item.get("Location", "")).strip() or "Unbekannt"
        user = str(item.get("User", "")).strip() or "Unbekannt"
        target_path = str(item.get("TargetPath", "") or "").strip()
        target_exists = _normalise_bool(item.get("TargetExists"))
        signature = str(
            item.get("SignatureStatus", "") or "Nicht geprüft"
        ).strip()
        publisher = str(item.get("Publisher", "") or "").strip()

        warning_reasons: list[str] = []
        hint_reasons: list[str] = []
        command_lower = command.casefold()
        target_lower = target_path.casefold()
        combined_path = target_lower or command_lower

        warning_host = _contains_program(
            command_lower,
            SCRIPT_HOSTS_WARNING,
        )
        hint_host = _contains_program(
            command_lower,
            SCRIPT_HOSTS_HINT,
        )

        if warning_host:
            warning_reasons.append(
                f"Start über den Skript- oder Systemhost {warning_host}."
            )
        elif hint_host:
            hint_reasons.append(
                f"Start über den Systemhost {hint_host}; Zweck prüfen."
            )

        if any(
            extension in command_lower
            for extension in SCRIPT_EXTENSIONS
        ):
            warning_reasons.append(
                "Der Autostart führt eine Skriptdatei aus."
            )

        if any(
            path_part in combined_path
            for path_part in SUSPICIOUS_PATH_PARTS
        ):
            warning_reasons.append(
                "Die Startdatei liegt in einem ungewöhnlichen "
                "oder leicht beschreibbaren Verzeichnis."
            )

        if target_path.startswith("\\\\"):
            warning_reasons.append(
                "Die Startdatei wird über einen Netzwerkpfad geladen."
            )

        if target_path and target_exists is False:
            missing_target_count += 1
            warning_reasons.append(
                "Die angegebene Zieldatei ist nicht vorhanden."
            )

        signature_key = signature.casefold().replace(" ", "")
        if signature_key == "valid":
            valid_signed_count += 1
        elif (
            target_exists is True
            and target_path.casefold().endswith((".exe", ".dll"))
        ):
            if signature_key in INVALID_SIGNATURE_STATES:
                warning_reasons.append(
                    f"Die digitale Signatur meldet den Status {signature}."
                )
            elif signature_key in {"notsigned", "nichtsigniert"}:
                hint_reasons.append(
                    "Die ausführbare Datei ist nicht digital signiert."
                )
            elif signature_key not in {
                "",
                "nichtgeprüft",
                "notchecked",
            }:
                hint_reasons.append(
                    f"Signaturstatus: {signature}."
                )

        if command and ".exe" in command_lower and not target_path:
            hint_reasons.append(
                "Die Zieldatei konnte aus dem Startbefehl "
                "nicht eindeutig ermittelt werden."
            )

        if warning_reasons:
            assessment = "WARNUNG"
            warning_count += 1
            warning_messages.append(
                f"{name}: {' '.join(warning_reasons)}"
            )
        elif hint_reasons:
            assessment = "HINWEIS"
            hint_count += 1
            hint_messages.append(
                f"{name}: {' '.join(hint_reasons)}"
            )
        else:
            assessment = "OK"

        details.append(
            {
                "Name": name,
                "Bewertung": assessment,
                "Speicherort": location,
                "Benutzer": user,
                "Befehl": command or "Nicht angegeben",
                "Zieldatei": target_path or "Nicht eindeutig ermittelt",
                "Datei vorhanden": (
                    "Ja"
                    if target_exists is True
                    else "Nein"
                    if target_exists is False
                    else "Nicht geprüft"
                ),
                "Signatur": signature or "Nicht geprüft",
                "Herausgeber": publisher or "Nicht ermittelt",
                "Begründung": (
                    warning_reasons
                    or hint_reasons
                    or ["Keine Auffälligkeit erkannt."]
                ),
            }
        )

    if len(unique_items) >= 16:
        hint_messages.append(
            f"{len(unique_items)} Autostartprogramme können den "
            "Anmeldevorgang merklich verlängern."
        )

    if warning_count:
        rating = "WARNUNG"
        summary = (
            f"{warning_count} auffällige Autostarteinträge erkannt."
        )
        recommendation = (
            "Die markierten Einträge in den Windows-Einstellungen "
            "oder im Task-Manager prüfen. Einträge nicht allein "
            "aufgrund dieser Heuristik löschen."
        )
    elif hint_count or hint_messages:
        rating = "HINWEIS"
        summary = (
            f"{len(unique_items)} Autostartprogramme geprüft; "
            "einzelne Einträge sollten eingeordnet werden."
        )
        recommendation = (
            "Nicht benötigte Programme können im Task-Manager unter "
            "Autostart deaktiviert werden. Vorher Hersteller und Zweck "
            "des Eintrags prüfen."
        )
    else:
        rating = "OK"
        summary = (
            f"{len(unique_items)} Autostartprogramme geprüft; "
            "keine auffälligen Startmechanismen erkannt."
        )
        recommendation = (
            "Der Autostart ist nach den verwendeten Heuristiken "
            "unauffällig."
        )

    result: dict[str, Any] = {
        "Autostartprogramme": len(unique_items),
        "Auffällige Einträge": warning_count,
        "Prüfhinweise": hint_count,
        "Gültig signierte Dateien": valid_signed_count,
        "Fehlende Zieldateien": missing_target_count,
        "Zusammenfassung": summary,
        "Empfehlung": recommendation,
        "Einträge": details,
        "Bewertung": rating,
    }

    if warning_messages:
        result["Warnungen"] = warning_messages

    if hint_messages:
        result["Hinweise"] = hint_messages

    return result


def get_startup_programs_info() -> dict[str, Any]:
    """Liest Windows-Autostarteinträge aus und bewertet sie."""

    command = r"""
$ErrorActionPreference = 'Stop'

$items = @(
    Get-CimInstance -ClassName Win32_StartupCommand |
        ForEach-Object {
            $commandText = [string]$_.Command
            $expandedCommand = [Environment]::ExpandEnvironmentVariables(
                $commandText
            )
            $targetPath = $null

            if ($expandedCommand -match '^\s*"([^"]+)"') {
                $targetPath = $matches[1]
            }
            elseif (
                $expandedCommand -match
                '^\s*([^\s]+?\.(?:exe|com|bat|cmd|ps1|vbs|js))(?:\s|$)'
            ) {
                $targetPath = $matches[1]
            }

            $targetExists = $null
            $signatureStatus = 'Nicht geprüft'
            $publisher = ''

            if ($targetPath) {
                $targetPath = $targetPath.Trim('"')
                $targetExists = Test-Path -LiteralPath $targetPath -PathType Leaf

                if (
                    $targetExists -and
                    ([IO.Path]::GetExtension($targetPath) -in @('.exe', '.dll'))
                ) {
                    try {
                        $signature = Get-AuthenticodeSignature `
                            -LiteralPath $targetPath
                        $signatureStatus = [string]$signature.Status

                        if ($signature.SignerCertificate) {
                            $publisher = [string](
                                $signature.SignerCertificate.Subject
                            )
                        }
                    }
                    catch {
                        $signatureStatus = 'Nicht geprüft'
                    }
                }
            }

            [pscustomobject]@{
                Name = [string]$_.Name
                Command = $commandText
                Location = [string]$_.Location
                User = [string]$_.User
                TargetPath = $targetPath
                TargetExists = $targetExists
                SignatureStatus = $signatureStatus
                Publisher = $publisher
            }
        }
)

if ($items.Count -eq 0) {
    '[]'
}
else {
    $items |
        Sort-Object Name, Location, User |
        ConvertTo-Json -Depth 4 -Compress
}
"""

    try:
        payload = run_powershell_command(command)
        startup_items = parse_startup_payload(payload)
        return evaluate_startup_programs(startup_items)
    except subprocess.TimeoutExpired:
        return {
            "Bewertung": "FEHLER",
            "Fehler": (
                "Die Autostartanalyse hat das Zeitlimit überschritten."
            ),
            "Hinweis": (
                "Die restliche Systemdiagnose kann fortgesetzt werden."
            ),
        }
    except (
        json.JSONDecodeError,
        OSError,
        RuntimeError,
        ValueError,
    ) as error:
        return {
            "Bewertung": "FEHLER",
            "Fehler": str(error),
            "Hinweis": (
                "Die Windows-Autostarteinträge konnten nicht "
                "vollständig ausgelesen werden."
            ),
        }
