"""Vergleicht zwei gespeicherte Diagnoseläufe."""

from __future__ import annotations

from dataclasses import dataclass

STATUS_RANK = {
    "OK": 0,
    "INFO": 1,
    "HINWEIS": 2,
    "WARNUNG": 3,
    "KRITISCH": 4,
    "FEHLER": 5,
}


@dataclass(frozen=True)
class ComparisonItem:
    title: str
    old_status: str
    new_status: str
    change: str


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
        items = []

        for title in titles:
            old_item = old_results.get(title)
            new_item = new_results.get(title)

            if old_item is None:
                old_status = "NICHT VORHANDEN"
                new_status = new_item["status"]
                change = "NEU"
            elif new_item is None:
                old_status = old_item["status"]
                new_status = "NICHT VORHANDEN"
                change = "ENTFERNT"
            else:
                old_status = old_item["status"]
                new_status = new_item["status"]
                change = self._classify(old_status, new_status)

            summary[change] += 1
            items.append(
                ComparisonItem(
                    title=title,
                    old_status=old_status,
                    new_status=new_status,
                    change=change,
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
        return {
            str(item.get("title", "Unbenannte Prüfung")): {
                "status": str(item.get("status", "INFO")).upper()
            }
            for item in scan.get("results", [])
        }

    @staticmethod
    def _classify(old_status: str, new_status: str) -> str:
        old_rank = STATUS_RANK.get(old_status, 1)
        new_rank = STATUS_RANK.get(new_status, 1)
        if new_rank < old_rank:
            return "VERBESSERT"
        if new_rank > old_rank:
            return "VERSCHLECHTERT"
        return "UNVERÄNDERT"
