"""Intelligenter Markdown-Bericht für zwei Diagnoseläufe."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable

from src.services.scan_comparison_service import (
    ComparisonItem,
    DetailChange,
)


STATUS_LABELS = {
    "OK": "OK",
    "INFO": "Information",
    "HINWEIS": "Hinweis",
    "WARNUNG": "Warnung",
    "KRITISCH": "Kritisch",
    "FEHLER": "Fehler",
    "NICHT VORHANDEN": "Nicht vorhanden",
}

STATUS_ORDER = (
    "FEHLER",
    "KRITISCH",
    "WARNUNG",
    "HINWEIS",
    "INFO",
    "OK",
)

CHANGE_LABELS = {
    "VERBESSERT": "Verbessert",
    "UNVERÄNDERT": "Unverändert",
    "VERSCHLECHTERT": "Verschlechtert",
    "NEU": "Neu hinzugekommen",
    "ENTFERNT": "Nicht mehr vorhanden",
}

CATEGORY_LABELS = {
    "RELEVANT": "Relevant",
    "BEOBACHTEN": "Beobachten",
    "ERWARTET": "Erwartete Änderung",
    "FLUECHTIG": "Flüchtiger Systemwert",
    "INFORMATION": "Information",
}

CATEGORY_ORDER = {
    "RELEVANT": 0,
    "BEOBACHTEN": 1,
    "ERWARTET": 2,
    "FLUECHTIG": 3,
    "INFORMATION": 4,
}

CATEGORY_MEANINGS = {
    "RELEVANT": (
        "Kann auf eine sicherheits- oder betriebsrelevante "
        "Verschlechterung hinweisen."
    ),
    "BEOBACHTEN": (
        "Ist nicht automatisch kritisch, sollte aber beim nächsten "
        "Diagnoselauf erneut geprüft werden."
    ),
    "ERWARTET": (
        "Entsteht typischerweise durch Updates oder reguläre "
        "Systempflege."
    ),
    "FLUECHTIG": (
        "Kann sich durch Lastverteilung, Netzwerkzustand oder "
        "Laufzeitbedingungen ändern."
    ),
    "INFORMATION": (
        "Normale Messwertabweichung ohne unmittelbaren "
        "Handlungsbedarf."
    ),
}


@dataclass(frozen=True)
class ClassifiedDetail:
    item_title: str
    item_change: str
    old_status: str
    new_status: str
    path: str
    old_value: str
    new_value: str
    category: str
    reason: str
    recommendation: str


def save_comparison_report(
    comparison: dict,
    file_path: str | Path,
) -> Path:
    """Speichert den intelligent bewerteten Vergleichsbericht."""

    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        build_comparison_report(comparison),
        encoding="utf-8",
    )
    return path.resolve()


def build_comparison_report(comparison: dict) -> str:
    """Erstellt den vollständigen Markdown-Bericht."""

    items: list[ComparisonItem] = list(
        comparison.get("items", [])
    )
    summary = comparison.get("summary", {})
    old_counts = comparison.get("old_status_counts", {})
    new_counts = comparison.get("new_status_counts", {})

    classified, duplicate_count = _classify_changes(items)
    category_counts = {
        category: sum(
            change.category == category
            for change in classified
        )
        for category in CATEGORY_LABELS
    }

    current_findings = [
        item
        for item in items
        if item.new_status in {
            "WARNUNG",
            "KRITISCH",
            "FEHLER",
        }
    ]

    status_changed_items = [
        item
        for item in items
        if item.change != "UNVERÄNDERT"
    ]

    unchanged_items = [
        item
        for item in items
        if (
            item.change == "UNVERÄNDERT"
            and item.changed_detail_count == 0
        )
    ]

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

    raw_change_count = sum(
        item.changed_detail_count
        for item in items
    )
    relevant_count = (
        category_counts["RELEVANT"]
        + category_counts["BEOBACHTEN"]
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
        (
            f"**Gesamtentwicklung:** "
            f"{_overall_trend(summary, category_counts)}"
        ),
        "",
        _management_summary(
            current_findings=current_findings,
            status_changed_items=status_changed_items,
            raw_change_count=raw_change_count,
            relevant_count=relevant_count,
            category_counts=category_counts,
            duplicate_count=duplicate_count,
        ),
        "",
        "### Intelligente Änderungsbewertung",
        "",
        "| Einordnung | Anzahl | Bedeutung |",
        "|---|---:|---|",
    ]

    for category in CATEGORY_LABELS:
        lines.append(
            f"| {CATEGORY_LABELS[category]} | "
            f"{category_counts[category]} | "
            f"{CATEGORY_MEANINGS[category]} |"
        )

    lines.extend(
        [
            (
                f"| Gefilterte Duplikate | {duplicate_count} | "
                "Identische Speicherwerte aus mehreren "
                "Diagnosebereichen wurden nur einmal berücksichtigt. |"
            ),
            "",
            "## Aktueller Handlungsbedarf im neueren Scan",
            "",
        ]
    )

    if current_findings:
        lines.extend(
            [
                "| Priorität | Diagnosebereich | Aktueller Status | "
                "Empfohlene Prüfung |",
                "|---|---|---|---|",
            ]
        )

        for item in sorted(
            current_findings,
            key=_current_finding_sort_key,
        ):
            lines.append(
                f"| {_current_priority(item.new_status)} | "
                f"{_escape(item.title)} | "
                f"{_status_label(item.new_status)} | "
                f"{_escape(_current_recommendation(item))} |"
            )
    else:
        lines.append(
            "Im neueren Scan sind keine Warnungen, kritischen "
            "Ergebnisse oder Fehler vorhanden."
        )

    lines.extend(
        [
            "",
            "## Statusverteilung",
            "",
            "| Status | Älterer Scan | Neuerer Scan | Differenz |",
            "|---|---:|---:|---:|",
        ]
    )

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

    lines.extend(
        [
            "",
            "## Statusänderungen nach Diagnosebereich",
            "",
        ]
    )

    if status_changed_items:
        lines.extend(
            [
                "| Diagnosebereich | Vorher | Nachher | Veränderung |",
                "|---|---|---|---|",
            ]
        )

        for item in sorted(
            status_changed_items,
            key=_status_change_sort_key,
        ):
            lines.append(
                f"| {_escape(item.title)} | "
                f"{_status_label(item.old_status)} | "
                f"{_status_label(item.new_status)} | "
                f"{CHANGE_LABELS[item.change]} |"
            )
    else:
        lines.append(
            "Die Statusbewertung aller Diagnosebereiche blieb "
            "zwischen beiden Scans unverändert."
        )

    actionable = [
        change
        for change in classified
        if change.category in {
            "RELEVANT",
            "BEOBACHTEN",
        }
    ]

    lines.extend(
        [
            "",
            "## Relevante Änderungen und Beobachtungspunkte",
            "",
        ]
    )

    if actionable:
        lines.extend(
            [
                "| Einordnung | Diagnosebereich | Wert | "
                "Älterer Scan | Neuerer Scan | Empfehlung |",
                "|---|---|---|---|---|---|",
            ]
        )

        for change in sorted(
            actionable,
            key=_classified_sort_key,
        ):
            lines.append(
                f"| {CATEGORY_LABELS[change.category]} | "
                f"{_escape(change.item_title)} | "
                f"{_escape(change.path)} | "
                f"{_escape(change.old_value)} | "
                f"{_escape(change.new_value)} | "
                f"{_escape(change.recommendation)} |"
            )
    else:
        lines.append(
            "Es wurden keine relevanten Detailverschlechterungen "
            "oder Beobachtungspunkte erkannt."
        )

    normal_changes = [
        change
        for change in classified
        if change.category in {
            "ERWARTET",
            "FLUECHTIG",
            "INFORMATION",
        }
    ]

    lines.extend(
        [
            "",
            "## Erwartbare und informative Änderungen",
            "",
        ]
    )

    if normal_changes:
        lines.extend(
            [
                "| Einordnung | Diagnosebereich | Wert | "
                "Älterer Scan | Neuerer Scan | Begründung |",
                "|---|---|---|---|---|---|",
            ]
        )

        for change in sorted(
            normal_changes,
            key=_classified_sort_key,
        ):
            lines.append(
                f"| {CATEGORY_LABELS[change.category]} | "
                f"{_escape(change.item_title)} | "
                f"{_escape(change.path)} | "
                f"{_escape(change.old_value)} | "
                f"{_escape(change.new_value)} | "
                f"{_escape(change.reason)} |"
            )
    else:
        lines.append(
            "Keine erwartbaren, flüchtigen oder rein informativen "
            "Detailänderungen vorhanden."
        )

    lines.extend(
        [
            "",
            "## Unveränderte Diagnosebereiche",
            "",
        ]
    )

    if unchanged_items:
        for item in sorted(
            unchanged_items,
            key=lambda value: value.title.lower(),
        ):
            lines.append(f"- {_escape(item.title)}")
    else:
        lines.append(
            "Alle Diagnosebereiche weisen mindestens eine "
            "Status- oder Detailänderung auf."
        )

    lines.extend(
        [
            "",
            "## Bewertungsregeln",
            "",
            "- Defender-Signaturupdates gelten als erwartete Änderung.",
            (
                "- Wechselnde DNS-Zieladressen und ähnliche "
                "Netzwerkwerte gelten als flüchtig."
            ),
            (
                "- Speicheränderungen werden erst bei deutlichen "
                "Rückgängen oder kritischen Restwerten hervorgehoben."
            ),
            (
                "- Änderungen offener Listening-Ports werden abhängig "
                "von Richtung und Inhalt als Information oder "
                "Beobachtungspunkt bewertet."
            ),
            (
                "- Identische Speicherwerte aus Systeminformationen und "
                "Speicherplatzprüfung werden nicht doppelt gezählt."
            ),
            "",
            "## Technischer Hinweis",
            "",
            (
                "Die automatische Einordnung reduziert typische "
                "Fehlalarme, ersetzt aber keine manuelle Prüfung. "
                "Insbesondere neue Dienste, öffentlich erreichbare Ports "
                "und deaktivierte Schutzfunktionen sollten fachlich "
                "validiert werden."
            ),
            "",
        ]
    )

    return "\n".join(lines)


def _classify_changes(
    items: list[ComparisonItem],
) -> tuple[list[ClassifiedDetail], int]:
    ordered_items = sorted(
        items,
        key=lambda item: (
            0 if "speicherplatz" in item.title.casefold() else 1,
            item.title.casefold(),
        ),
    )

    seen_storage_values: set[tuple[str, str, str]] = set()
    classified: list[ClassifiedDetail] = []
    duplicate_count = 0

    for item in ordered_items:
        for detail in item.detail_changes:
            if not detail.changed:
                continue

            metric = _canonical_storage_metric(detail.path)

            if metric:
                duplicate_key = (
                    metric,
                    detail.old_value,
                    detail.new_value,
                )

                if duplicate_key in seen_storage_values:
                    duplicate_count += 1
                    continue

                seen_storage_values.add(duplicate_key)

            classified.append(
                _classify_detail(item, detail)
            )

    return classified, duplicate_count


def _classify_detail(
    item: ComparisonItem,
    detail: DetailChange,
) -> ClassifiedDetail:
    title = item.title.casefold()
    path = detail.path.casefold()
    old_text = detail.old_value.casefold()
    new_text = detail.new_value.casefold()

    category = "INFORMATION"
    reason = (
        "Der Messwert hat sich verändert, ohne dass daraus allein "
        "ein Fehlerzustand abgeleitet werden kann."
    )
    recommendation = (
        "Beim nächsten Diagnoselauf erneut vergleichen."
    )

    if item.change == "VERSCHLECHTERT":
        category = "RELEVANT"
        reason = (
            "Der Status des Diagnosebereichs hat sich verschlechtert."
        )
        recommendation = (
            "Ursache prüfen, betroffenen Systembereich validieren "
            "und Diagnose nach der Korrektur wiederholen."
        )

    elif _protection_disabled(path, new_text):
        category = "RELEVANT"
        reason = (
            "Eine Windows-Schutzfunktion wird als deaktiviert oder "
            "nicht aktiv gemeldet."
        )
        recommendation = (
            "Schutzfunktion aktivieren oder dokumentierte Ausnahme "
            "fachlich prüfen."
        )

    elif (
        "defender" in title
        and (
            "signaturversion" in path
            or "signaturupdate" in path
            or "definitionsversion" in path
        )
    ):
        category = "ERWARTET"
        reason = (
            "Microsoft Defender aktualisiert Signaturen regelmäßig. "
            "Eine neuere Version oder ein neueres Aktualisierungsdatum "
            "ist normal und grundsätzlich positiv."
        )
        recommendation = (
            "Keine Maßnahme erforderlich, sofern das Update aktuell ist."
        )

    elif _is_dns_target(path):
        category = "FLUECHTIG"
        reason = (
            "DNS-Ziele können durch Lastverteilung, Anycast oder "
            "regionale Serverauswahl unterschiedliche IP-Adressen liefern."
        )
        recommendation = (
            "Nur prüfen, wenn gleichzeitig DNS-Fehler oder "
            "Verbindungsprobleme auftreten."
        )

    elif _is_transient_network_value(path):
        category = "FLUECHTIG"
        reason = (
            "Netzwerkadressen und Laufzeitmessungen können sich zwischen "
            "zwei Diagnosen regulär ändern."
        )
        recommendation = (
            "Nur bei reproduzierbaren Verbindungsproblemen untersuchen."
        )

    elif _is_port_value(title, path):
        old_number = _first_number(detail.old_value)
        new_number = _first_number(detail.new_value)

        if (
            old_number is not None
            and new_number is not None
            and new_number <= old_number
        ):
            category = "INFORMATION"
            reason = (
                "Die Anzahl erreichbarer oder lauschender Ports ist "
                "nicht gestiegen."
            )
            recommendation = (
                "Keine unmittelbare Maßnahme. Portliste bei Bedarf "
                "stichprobenartig prüfen."
            )
        elif (
            old_text == "nicht vorhanden"
            and new_text != "nicht vorhanden"
        ):
            category = "BEOBACHTEN"
            reason = (
                "Ein neuer Port-, Prozess- oder Listening-Eintrag "
                "ist hinzugekommen."
            )
            recommendation = (
                "Zugehörigen Prozess und Bindungsadresse prüfen und "
                "bestätigen, dass der Dienst benötigt wird."
            )
        else:
            category = "BEOBACHTEN"
            reason = (
                "Die Port- oder Prozesslandschaft hat sich verändert."
            )
            recommendation = (
                "Neue oder geänderte Listening-Ports mit dem "
                "zugehörigen Prozess abgleichen."
            )

    elif _is_storage_value(path):
        category, reason, recommendation = _classify_storage(detail)

    elif _is_expected_timestamp(path):
        category = "ERWARTET"
        reason = (
            "Zeitstempel und laufzeitabhängige Angaben ändern sich "
            "bei regulärem Systembetrieb."
        )
        recommendation = "Keine Maßnahme erforderlich."

    elif _is_version_change(path):
        category = "BEOBACHTEN"
        reason = (
            "Eine Software- oder Systemversion hat sich geändert."
        )
        recommendation = (
            "Prüfen, ob die Versionsänderung durch ein geplantes "
            "Update entstanden ist."
        )

    return ClassifiedDetail(
        item_title=item.title,
        item_change=item.change,
        old_status=item.old_status,
        new_status=item.new_status,
        path=detail.path,
        old_value=detail.old_value,
        new_value=detail.new_value,
        category=category,
        reason=reason,
        recommendation=recommendation,
    )


def _classify_storage(
    detail: DetailChange,
) -> tuple[str, str, str]:
    path = detail.path.casefold()
    old_number = _first_number(detail.old_value)
    new_number = _first_number(detail.new_value)

    if old_number is None or new_number is None:
        return (
            "INFORMATION",
            (
                "Der Speicherwert hat sich verändert, kann aber nicht "
                "numerisch bewertet werden."
            ),
            "Speicherentwicklung beim nächsten Scan erneut prüfen.",
        )

    difference = new_number - old_number

    if "prozent" in path or "%" in detail.new_value:
        if new_number < 15:
            return (
                "RELEVANT",
                (
                    "Der freie Speicher liegt unter 15 Prozent und "
                    "kann Updates oder den stabilen Betrieb beeinträchtigen."
                ),
                (
                    "Speicher bereinigen und freien Speicherplatz "
                    "zeitnah erhöhen."
                ),
            )

        if difference <= -5:
            return (
                "BEOBACHTEN",
                (
                    "Der freie Speicher ist um mindestens fünf "
                    "Prozentpunkte gesunken."
                ),
                (
                    "Ursache des Speicherverbrauchs prüfen und "
                    "Entwicklung weiter beobachten."
                ),
            )

        return (
            "INFORMATION",
            (
                "Eine geringe prozentuale Speicheränderung ist bei "
                "normaler Nutzung üblich."
            ),
            "Keine unmittelbare Maßnahme erforderlich.",
        )

    if "frei" in path:
        if new_number < 20:
            return (
                "RELEVANT",
                (
                    "Der freie Speicher liegt unter 20 GB."
                ),
                (
                    "Nicht benötigte Dateien entfernen oder "
                    "Speicherkapazität erweitern."
                ),
            )

        if difference <= -20:
            return (
                "BEOBACHTEN",
                (
                    "Der freie Speicher ist um mindestens 20 GB gesunken."
                ),
                (
                    "Größte Speicherverbraucher ermitteln und "
                    "weiteren Rückgang beobachten."
                ),
            )

        return (
            "INFORMATION",
            (
                "Die Änderung des freien Speichers liegt innerhalb "
                "einer üblichen Betriebsschwankung."
            ),
            "Keine unmittelbare Maßnahme erforderlich.",
        )

    if "belegt" in path and difference >= 20:
        return (
            "BEOBACHTEN",
            (
                "Der belegte Speicher ist um mindestens 20 GB gestiegen."
            ),
            (
                "Neue große Dateien, Updates oder Anwendungen prüfen."
            ),
        )

    return (
        "INFORMATION",
        (
            "Die Speicherbelegung hat sich nur in normalem Umfang verändert."
        ),
        "Keine unmittelbare Maßnahme erforderlich.",
    )


def _management_summary(
    current_findings: list[ComparisonItem],
    status_changed_items: list[ComparisonItem],
    raw_change_count: int,
    relevant_count: int,
    category_counts: dict[str, int],
    duplicate_count: int,
) -> str:
    parts = []

    if current_findings:
        parts.append(
            f"Der neuere Scan enthält {len(current_findings)} aktuelle "
            "Warn-, Kritisch- oder Fehlerbewertung(en)."
        )
    else:
        parts.append(
            "Der neuere Scan enthält keinen aktuellen Warn-, "
            "Kritisch- oder Fehlerstatus."
        )

    if status_changed_items:
        parts.append(
            f"Bei {len(status_changed_items)} Diagnosebereich(en) "
            "hat sich der Status verändert."
        )
    else:
        parts.append(
            "Die Statusstufen aller Diagnosebereiche blieben unverändert."
        )

    parts.append(
        f"Von {raw_change_count} erkannten Detailänderungen wurden "
        f"{relevant_count} als relevant oder beobachtungswürdig eingestuft."
    )

    normal_count = (
        category_counts["ERWARTET"]
        + category_counts["FLUECHTIG"]
        + category_counts["INFORMATION"]
    )

    if normal_count:
        parts.append(
            f"{normal_count} Änderung(en) wurden als erwartbar, "
            "flüchtig oder rein informativ bewertet."
        )

    if duplicate_count:
        parts.append(
            f"{duplicate_count} doppelte Speicherwert(e) wurden "
            "aus der fachlichen Bewertung entfernt."
        )

    return " ".join(parts)


def _overall_trend(
    summary: dict,
    category_counts: dict[str, int],
) -> str:
    worse = int(summary.get("VERSCHLECHTERT", 0))
    better = int(summary.get("VERBESSERT", 0))

    if worse and better:
        return "Gemischte Entwicklung"

    if worse:
        return "Verschlechtert"

    if better:
        return "Verbessert"

    if category_counts["RELEVANT"]:
        return "Status stabil, relevante Detailänderung erkannt"

    if category_counts["BEOBACHTEN"]:
        return "Status stabil, Beobachtung empfohlen"

    return "Status stabil, nur normale Systemänderungen erkannt"


def _current_recommendation(item: ComparisonItem) -> str:
    title = item.title.casefold()

    if "defender" in title:
        return (
            "Windows-Sicherheit öffnen und den konkreten Grund der "
            "Warnung prüfen. Signaturstand und Schutzfunktionen kontrollieren."
        )

    if "port" in title:
        return (
            "Listening-Ports, Bindungsadressen und zugehörige Prozesse "
            "prüfen. Nur benötigte Dienste offen lassen."
        )

    if "firewall" in title:
        return (
            "Status aller Firewallprofile prüfen und deaktivierte "
            "Profile nur bei dokumentierter Ausnahme belassen."
        )

    if "bitlocker" in title:
        return (
            "Verschlüsselungs- und Schutzstatus des Systemlaufwerks prüfen."
        )

    if "update" in title:
        return (
            "Ausstehende Windows-Updates prüfen und erforderliche "
            "Neustarts durchführen."
        )

    if "speicher" in title:
        return (
            "Freien Speicher und größte Speicherverbraucher kontrollieren."
        )

    if "netzwerk" in title:
        return (
            "Gateway, DNS-Auflösung und Erreichbarkeit erneut testen."
        )

    return (
        "Detailwerte des Diagnosebereichs prüfen und Ergebnis "
        "nach einer Korrektur erneut erfassen."
    )


def _current_priority(status: str) -> str:
    if status in {"FEHLER", "KRITISCH"}:
        return "Hoch"

    if status == "WARNUNG":
        return "Mittel"

    return "Niedrig"


def _current_finding_sort_key(
    item: ComparisonItem,
) -> tuple[int, str]:
    order = {
        "FEHLER": 0,
        "KRITISCH": 1,
        "WARNUNG": 2,
    }
    return (
        order.get(item.new_status, 9),
        item.title.casefold(),
    )


def _status_change_sort_key(
    item: ComparisonItem,
) -> tuple[int, str]:
    order = {
        "VERSCHLECHTERT": 0,
        "NEU": 1,
        "ENTFERNT": 2,
        "VERBESSERT": 3,
    }
    return (
        order.get(item.change, 9),
        item.title.casefold(),
    )


def _classified_sort_key(
    change: ClassifiedDetail,
) -> tuple[int, str, str]:
    return (
        CATEGORY_ORDER.get(change.category, 9),
        change.item_title.casefold(),
        change.path.casefold(),
    )


def _canonical_storage_metric(path: str) -> str | None:
    normalized = path.casefold()

    if "speicher" not in normalized:
        return None

    if "frei" in normalized and (
        "prozent" in normalized
        or "%" in normalized
    ):
        return "storage_free_percent"

    if "frei" in normalized:
        return "storage_free"

    if "belegt" in normalized:
        return "storage_used"

    if "gesamt" in normalized:
        return "storage_total"

    return None


def _protection_disabled(
    path: str,
    new_value: str,
) -> bool:
    protection_terms = (
        "echtzeitschutz",
        "firewall",
        "schutzstatus",
        "antivirus",
        "cloudschutz",
        "manipulationsschutz",
    )
    disabled_values = (
        "deaktiviert",
        "inaktiv",
        "aus",
        "false",
        "nein",
        "off",
        "nicht aktiv",
    )

    return (
        any(term in path for term in protection_terms)
        and any(value in new_value for value in disabled_values)
    )


def _is_dns_target(path: str) -> bool:
    return (
        "dns-ip" in path
        or "dns ip" in path
        or ("dns" in path and "adresse" in path)
    )


def _is_transient_network_value(path: str) -> bool:
    terms = (
        "ping",
        "latenz",
        "antwortzeit",
        "lokale ip",
        "ipv4-adresse",
        "ipv6-adresse",
        "öffentliche ip",
    )
    return any(term in path for term in terms)


def _is_port_value(
    title: str,
    path: str,
) -> bool:
    return (
        "port" in title
        or "port" in path
        or "listening" in path
        or "prozess" in path
    )


def _is_storage_value(path: str) -> bool:
    return "speicher" in path.casefold()


def _is_expected_timestamp(path: str) -> bool:
    terms = (
        "zeitstempel",
        "laufzeit",
        "uptime",
        "letzter start",
        "startzeit",
        "prüfzeit",
        "scanzeit",
    )
    return any(term in path for term in terms)


def _is_version_change(path: str) -> bool:
    return (
        "version" in path
        and "signaturversion" not in path
    )


def _first_number(value: str) -> float | None:
    match = re.search(
        r"-?\d+(?:[.,]\d+)?",
        value.replace("\u00a0", " "),
    )

    if not match:
        return None

    try:
        return float(
            match.group(0).replace(",", ".")
        )
    except ValueError:
        return None


def _overall_status(counts: dict) -> str:
    for status in STATUS_ORDER:
        if int(counts.get(status, 0)) > 0:
            return status

    return "UNBEKANNT"


def _find_metadata(
    items: Iterable[ComparisonItem],
    search_terms: tuple[str, ...],
) -> tuple[str, str]:
    for item in items:
        for detail in item.detail_changes:
            normalized_path = detail.path.casefold()

            if any(
                term in normalized_path
                for term in search_terms
            ):
                return (
                    detail.old_value,
                    detail.new_value,
                )

    return ("Nicht ermittelt", "Nicht ermittelt")


def _format_time(value: object) -> str:
    text = str(value or "Unbekannt")

    try:
        parsed = datetime.fromisoformat(text)
        return parsed.strftime("%d.%m.%Y %H:%M:%S")
    except ValueError:
        return text


def _status_label(status: str) -> str:
    return STATUS_LABELS.get(status, status.title())


def _escape(value: object) -> str:
    return (
        str(value)
        .replace("|", "\\|")
        .replace("\r\n", "<br>")
        .replace("\n", "<br>")
    )
