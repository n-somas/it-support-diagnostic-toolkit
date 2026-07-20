"""Vergleicht Status und Detailwerte zweier Diagnoseläufe."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


STATUS_RANK = {
    "OK": 0,
    "INFO": 1,
    "HINWEIS": 2,
    "WARNUNG": 3,
    "KRITISCH": 4,
    "FEHLER": 5,
}

MISSING = "Nicht vorhanden"


@dataclass(frozen=True)
class DetailChange:
    path: str
    old_value: str
    new_value: str
    changed: bool


@dataclass(frozen=True)
class ComparisonItem:
    title: str
    old_status: str
    new_status: str
    change: str
    detail_changes: tuple[DetailChange, ...]

    @property
    def changed_detail_count(self) -> int:
        return sum(detail.changed for detail in self.detail_changes)


class ScanComparisonService:
    def compare(self, old_scan: dict, new_scan: dict) -> dict:
        old_results = self._index(old_scan)
        new_results = self._index(new_scan)
        titles = sorted(set(old_results) | set(new_results))

        summary = {
            "VERBESSERT": 0,
            "UNVERÄNDERT": 0,
            "VERSCHLECHTERT": 0,
            "NEU": 0,
            "ENTFERNT": 0,
        }
        items: list[ComparisonItem] = []

        for title in titles:
            old_item = old_results.get(title)
            new_item = new_results.get(title)

            if old_item is None:
                old_status = MISSING.upper()
                new_status = new_item["status"]
                change = "NEU"
                old_details = {}
                new_details = new_item["details"]
            elif new_item is None:
                old_status = old_item["status"]
                new_status = MISSING.upper()
                change = "ENTFERNT"
                old_details = old_item["details"]
                new_details = {}
            else:
                old_status = old_item["status"]
                new_status = new_item["status"]
                change = self._classify(old_status, new_status)
                old_details = old_item["details"]
                new_details = new_item["details"]

            detail_changes = tuple(
                self._compare_details(old_details, new_details)
            )

            summary[change] += 1
            items.append(
                ComparisonItem(
                    title=title,
                    old_status=old_status,
                    new_status=new_status,
                    change=change,
                    detail_changes=detail_changes,
                )
            )

        return {
            "old_created_at": old_scan.get("created_at", "Unbekannt"),
            "new_created_at": new_scan.get("created_at", "Unbekannt"),
            "old_status_counts": old_scan.get("status_counts", {}),
            "new_status_counts": new_scan.get("status_counts", {}),
            "summary": summary,
            "items": items,
        }

    @staticmethod
    def _index(scan: dict) -> dict[str, dict]:
        indexed = {}

        for item in scan.get("results", []):
            title = str(item.get("title", "Unbenannte Prüfung"))
            details = item.get("details", {})

            if not isinstance(details, dict):
                details = {"Wert": details}

            indexed[title] = {
                "status": str(item.get("status", "INFO")).upper(),
                "details": details,
            }

        return indexed

    def _compare_details(
        self,
        old_details: dict,
        new_details: dict,
    ) -> list[DetailChange]:
        old_flat = self._flatten(old_details)
        new_flat = self._flatten(new_details)
        keys = sorted(set(old_flat) | set(new_flat))

        return [
            DetailChange(
                path=key,
                old_value=self._display_value(
                    old_flat.get(key, MISSING)
                ),
                new_value=self._display_value(
                    new_flat.get(key, MISSING)
                ),
                changed=self._normalized(
                    old_flat.get(key, MISSING)
                )
                != self._normalized(
                    new_flat.get(key, MISSING)
                ),
            )
            for key in keys
            if key not in {"Bewertung", "Status"}
        ]

    def _flatten(
        self,
        value: Any,
        prefix: str = "",
    ) -> dict[str, Any]:
        flattened: dict[str, Any] = {}

        if isinstance(value, dict):
            if not value and prefix:
                flattened[prefix] = {}

            for key, item in value.items():
                path = f"{prefix} > {key}" if prefix else str(key)
                flattened.update(self._flatten(item, path))

            return flattened

        if isinstance(value, (list, tuple)):
            if not value and prefix:
                flattened[prefix] = []

            for index, item in enumerate(value, start=1):
                path = f"{prefix} > Eintrag {index}"
                flattened.update(self._flatten(item, path))

            return flattened

        flattened[prefix or "Wert"] = value
        return flattened

    @staticmethod
    def _display_value(value: Any) -> str:
        if value is None:
            return "—"

        if isinstance(value, bool):
            return "Ja" if value else "Nein"

        if isinstance(value, (dict, list, tuple)):
            return str(value) if value else "Leer"

        text = str(value).strip()
        return text or "Leer"

    @staticmethod
    def _normalized(value: Any) -> str:
        if value is None:
            return ""

        if isinstance(value, bool):
            return str(value).lower()

        return str(value).strip()

    @staticmethod
    def _classify(old_status: str, new_status: str) -> str:
        old_rank = STATUS_RANK.get(old_status, 1)
        new_rank = STATUS_RANK.get(new_status, 1)

        if new_rank < old_rank:
            return "VERBESSERT"

        if new_rank > old_rank:
            return "VERSCHLECHTERT"

        return "UNVERÄNDERT"
