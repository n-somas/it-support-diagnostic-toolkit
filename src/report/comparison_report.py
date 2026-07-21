"""Professioneller Markdown-Bericht für zwei Diagnoseläufe."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Iterable

from src.services.scan_comparison_service import ComparisonItem


STATUS_LABELS = {
    "OK": "OK",
    "INFO": "Information",
    "HINWEIS": "Hinweis",
    "WARNUNG": "Warnung",
    "KRITISCH": "Kritisch",
    "FEHLER": "Fehler",
    "NICHT VORHANDEN": "Nicht vorhanden",
}

CHANGE_LABELS = {
    "VERBESSERT": "Verbessert",
    "UNVERÄNDERT": "Unverändert",
    "VERSCHLECHTERT": "Verschlechtert",
    "NEU": "Neu hinzugekommen",
    "ENTFERNT": "Nicht mehr vorhanden",
}

STATUS_ORDER = (
    "FEHLER",
    "KRITISCH",
    "WARNUNG",
    "HINWEIS",
    "INFO",
    "OK",
)


def save_comparison_report(
    comparison: dict,
    file_path: str | Path,
) -> Path:
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        build_comparison_report(comparison),
        encoding="utf-8",
    )
    return path.resolve()


def build_comparison_report(comparison: dict) -> str:
    items: list[ComparisonItem] = list(
        comparison.get("items", [])
    )
    summary = comparison.get("summary", {})
    old_counts = comparison.get("old_status_counts", {})
    new_counts = comparison.get("new_status_counts", {})

    changed_items = [
        item
        for item in items
        if (
            item.change != "UNVERÄNDERT"
            or item.changed_detail_count > 0
        )
    ]
    unchanged_items = [
        item
        for item in items
        if item not in changed_items
    ]
    priority_items = sorted(
        changed_items,
        key=_priority_sort_key,
    )

    old_computer, new_computer = _find_metadata(
        items,
        (
            "computername",
            "computer name",
            "hostname",
            "rechnername",
            "gerätebezeichnung",
        ),
    )
    old_os, new_os = _find_metadata(
        items,
        (
            "betriebssystem",
            "operating system",
            "windows-version",
            "windows version",
            "os version",
        ),
    )

    lines = [
        "# IT-Support-Diagnosevergleich",
        "",
        "## Berichtsangaben",
        "",
        "| Angabe | Älterer Scan | Neuerer Scan |",
        "|---|---|---|",
        (
            f"| Zeitpunkt | "
            f"{_escape(_format_time(comparison.get('old_created_at')))} | "
            f"{_escape(_format_time(comparison.get('new_created_at')))} |"
        ),
        (
            f"| Computername | {_escape(old_computer)} | "
            f"{_escape(new_computer)} |"
        ),
        (
            f"| Betriebssystem | {_escape(old_os)} | "
            f"{_escape(new_os)} |"
        ),
        (
            f"| Gesamtbewertung | "
            f"{_status_label(_overall_status(old_counts))} | "
            f"{_status_label(_overall_status(new_counts))} |"
        ),
        "",
        (
            "Bericht erstellt am "
            f"{datetime.now().strftime('%d.%m.%Y %H:%M:%S')}."
        ),
        "",
        "## Management-Zusammenfassung",
        "",
        f"**Gesamtentwicklung:** {_trend(summary, changed_items)}",
        "",
        _summary_text(items, summary),
        "",
        "### Veränderungsübersicht",
        "",
        "| Kategorie | Anzahl |",
        "|---|---:|",
        f"| Verschlechtert | {int(summary.get('VERSCHLECHTERT', 0))} |",
        f"| Verbessert | {int(summary.get('VERBESSERT', 0))} |",
        f"| Neu hinzugekommen | {int(summary.get('NEU', 0))} |",
        f"| Nicht mehr vorhanden | {int(summary.get('ENTFERNT', 0))} |",
        f"| Status unverändert | {int(summary.get('UNVERÄNDERT', 0))} |",
        (
            f"| Geänderte Detailwerte | "
            f"{sum(item.changed_detail_count for item in items)} |"
        ),
        "",
        "## Statusverteilung",
        "",
        "| Status | Älterer Scan | Neuerer Scan | Differenz |",
        "|---|---:|---:|---:|",
    ]

    for status in (
        "OK",
        "INFO",
        "HINWEIS",
        "WARNUNG",
        "KRITISCH",
        "FEHLER",
    ):
        old_value = int(old_counts.get(status, 0))
        new_value = int(new_counts.get(status, 0))
        difference = new_value - old_value
        difference_text = (
            f"+{difference}"
            if difference > 0
            else str(difference)
        )
        lines.append(
            f"| {_status_label(status)} | {old_value} | "
            f"{new_value} | {difference_text} |"
        )

    lines.extend(["", "## Priorisierte Bewertung", ""])

    if priority_items:
        lines.extend(
            [
                "| Priorität | Diagnosebereich | Veränderung | "
                "Status vorher | Status nachher | Empfehlung |",
                "|---|---|---|---|---|---|",
            ]
        )
        for item in priority_items:
            lines.append(
                f"| {_priority(item)} | {_escape(item.title)} | "
                f"{CHANGE_LABELS[item.change]} | "
                f"{_status_label(item.old_status)} | "
                f"{_status_label(item.new_status)} | "
                f"{_escape(_recommendation(item))} |"
            )
    else:
        lines.append(
            "Keine relevanten Veränderungen festgestellt."
        )

    lines.extend(
        ["", "## Relevante technische Änderungen", ""]
    )

    if priority_items:
        for item in priority_items:
            lines.extend(_item_section(item))
    else:
        lines.extend(
            [
                "Keine geänderten Status- oder Detailwerte vorhanden.",
                "",
            ]
        )

    lines.extend(
        ["## Unveränderte Diagnosebereiche", ""]
    )

    if unchanged_items:
        for item in sorted(
            unchanged_items,
            key=lambda value: value.title.lower(),
        ):
            lines.append(f"- {_escape(item.title)}")
    else:
        lines.append(
            "Alle Diagnosebereiche weisen mindestens eine Änderung auf."
        )

    lines.extend(
        [
            "",
            "## Technischer Hinweis",
            "",
            (
                "Die Gesamtbewertung entspricht dem höchsten im jeweiligen "
                "Scan vorhandenen Status. Die Priorisierung dient als "
                "technische Orientierung und ersetzt keine manuelle Prüfung "
                "der betroffenen Windows-Konfiguration."
            ),
            "",
        ]
    )

    return "\n".join(lines)


def _item_section(item: ComparisonItem) -> list[str]:
    changed_details = [
        detail
        for detail in item.detail_changes
        if detail.changed
    ]
    lines = [
        f"### {_escape(item.title)}",
        "",
        f"- **Veränderung:** {CHANGE_LABELS[item.change]}",
        (
            f"- **Status:** {_status_label(item.old_status)} → "
            f"{_status_label(item.new_status)}"
        ),
        f"- **Priorität:** {_priority(item)}",
        f"- **Empfehlung:** {_recommendation(item)}",
        "",
    ]

    if changed_details:
        lines.extend(
            [
                "| Geänderter Wert | Älterer Scan | Neuerer Scan |",
                "|---|---|---|",
            ]
        )
        for detail in changed_details:
            lines.append(
                f"| {_escape(detail.path)} | "
                f"{_escape(detail.old_value)} | "
                f"{_escape(detail.new_value)} |"
            )
        lines.append("")
    else:
        lines.extend(
            [
                (
                    "Der Status hat sich geändert, ohne dass in den "
                    "gespeicherten Detailfeldern eine abweichende "
                    "Ausgabe erkannt wurde."
                ),
                "",
            ]
        )

    return lines


def _overall_status(counts: dict) -> str:
    for status in STATUS_ORDER:
        if int(counts.get(status, 0)) > 0:
            return status
    return "UNBEKANNT"


def _trend(
    summary: dict,
    changed_items: list[ComparisonItem],
) -> str:
    worse = int(summary.get("VERSCHLECHTERT", 0))
    better = int(summary.get("VERBESSERT", 0))

    if worse and better:
        return "Gemischte Entwicklung"
    if worse:
        return "Verschlechtert"
    if better:
        return "Verbessert"
    if any(
        item.change in {"NEU", "ENTFERNT"}
        for item in changed_items
    ):
        return "Prüfumfang oder Systemstruktur verändert"
    if any(
        item.changed_detail_count > 0
        for item in changed_items
    ):
        return "Status stabil, technische Werte verändert"
    return "Unverändert"


def _summary_text(
    items: list[ComparisonItem],
    summary: dict,
) -> str:
    worse = int(summary.get("VERSCHLECHTERT", 0))
    better = int(summary.get("VERBESSERT", 0))
    unchanged = int(summary.get("UNVERÄNDERT", 0))
    details = sum(
        item.changed_detail_count
        for item in items
    )
    high = sum(
        _priority(item) == "Hoch"
        for item in items
    )

    parts = []

    if worse:
        parts.append(
            f"{worse} Diagnosebereich(e) haben sich verschlechtert"
            + (
                f", davon {high} mit hoher Priorität"
                if high
                else ""
            )
            + "."
        )
    else:
        parts.append(
            "Es wurde keine Statusverschlechterung festgestellt."
        )

    if better:
        parts.append(
            f"{better} Diagnosebereich(e) haben sich verbessert."
        )

    parts.append(
        f"{unchanged} Diagnosebereich(e) behielten ihren Status."
    )
    parts.append(
        f"Insgesamt wurden {details} geänderte Detailwerte erkannt."
    )
    return " ".join(parts)


def _priority(item: ComparisonItem) -> str:
    if item.change == "VERSCHLECHTERT":
        if item.new_status in {"FEHLER", "KRITISCH"}:
            return "Hoch"
        return "Mittel"
    if item.change in {"NEU", "ENTFERNT"}:
        return "Mittel"
    if (
        item.change == "UNVERÄNDERT"
        and item.changed_detail_count > 0
    ):
        return "Niedrig"
    return "Information"


def _priority_sort_key(
    item: ComparisonItem,
) -> tuple[int, str]:
    order = {
        "Hoch": 0,
        "Mittel": 1,
        "Niedrig": 2,
        "Information": 3,
    }
    return (
        order.get(_priority(item), 9),
        item.title.lower(),
    )


def _recommendation(item: ComparisonItem) -> str:
    if item.change == "VERSCHLECHTERT":
        if item.new_status in {"FEHLER", "KRITISCH"}:
            return (
                "Ursache zeitnah prüfen, Systembereich validieren "
                "und Diagnose anschließend wiederholen."
            )
        return (
            "Abweichung prüfen, Ursache dokumentieren und "
            "beim nächsten Scan kontrollieren."
        )
    if item.change == "VERBESSERT":
        return (
            "Verbesserung dokumentieren und Stabilität "
            "beim nächsten Scan bestätigen."
        )
    if item.change == "NEU":
        return (
            "Prüfen, ob der neue Diagnosebereich oder Systemwert "
            "durch eine beabsichtigte Änderung entstanden ist."
        )
    if item.change == "ENTFERNT":
        return (
            "Prüfen, ob der Bereich bewusst entfernt wurde oder "
            "beim neueren Scan nicht erfasst werden konnte."
        )
    return (
        "Geänderte Messwerte fachlich prüfen und "
        "beim nächsten Diagnoselauf erneut vergleichen."
    )


def _find_metadata(
    items: Iterable[ComparisonItem],
    terms: tuple[str, ...],
) -> tuple[str, str]:
    for item in items:
        for detail in item.detail_changes:
            path = detail.path.casefold()
            if any(term in path for term in terms):
                return (
                    detail.old_value,
                    detail.new_value,
                )
    return ("Nicht ermittelt", "Nicht ermittelt")


def _format_time(value: object) -> str:
    text = str(value or "Unbekannt")
    try:
        return datetime.fromisoformat(text).strftime(
            "%d.%m.%Y %H:%M:%S"
        )
    except ValueError:
        return text


def _status_label(status: str) -> str:
    return STATUS_LABELS.get(status, status)


def _escape(value: object) -> str:
    return (
        str(value)
        .replace("|", "\\|")
        .replace("\r\n", "<br>")
        .replace("\n", "<br>")
    )
