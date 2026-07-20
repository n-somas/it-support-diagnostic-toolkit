"""Speichert und lädt Diagnoseläufe für Verlauf und Vergleich."""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

STATUSES = ("OK", "INFO", "HINWEIS", "WARNUNG", "KRITISCH", "FEHLER")


class ScanHistoryService:
    def __init__(self, directory: str | Path = "data/scans") -> None:
        self.directory = Path(directory)

    def save(self, results: list[tuple[str, dict]]) -> Path:
        self.directory.mkdir(parents=True, exist_ok=True)
        now = datetime.now()
        counts = Counter(self._rating(result) for _, result in results)

        payload = {
            "schema_version": 2,
            "created_at": now.isoformat(timespec="seconds"),
            "status_counts": {
                status: counts.get(status, 0)
                for status in STATUSES
            },
            "results": [
                {
                    "title": title,
                    "status": self._rating(result),
                    "details": self._json_safe(result),
                }
                for title, result in results
            ],
        }

        path = self.directory / now.strftime("scan_%Y-%m-%d_%H-%M-%S.json")
        path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return path

    def load_recent(self, limit: int = 10) -> list[dict]:
        return list(reversed(self.list_scans(limit=limit)))

    def list_scans(self, limit: int | None = None) -> list[dict]:
        if not self.directory.exists():
            return []

        paths = sorted(self.directory.glob("scan_*.json"), reverse=True)
        if limit is not None:
            paths = paths[:limit]

        scans = []
        for path in paths:
            try:
                scan = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue

            scan["_path"] = str(path.resolve())
            scan["_filename"] = path.name
            scan["_has_details"] = bool(scan.get("results"))
            scans.append(scan)

        return scans

    @staticmethod
    def _rating(result: dict) -> str:
        value = result.get("Bewertung", result.get("Status", "INFO"))
        status = str(value).upper()
        return status if status in STATUSES else "INFO"

    @classmethod
    def _json_safe(cls, value: Any) -> Any:
        if isinstance(value, dict):
            return {str(key): cls._json_safe(item) for key, item in value.items()}
        if isinstance(value, (list, tuple, set)):
            return [cls._json_safe(item) for item in value]
        if isinstance(value, (str, int, float, bool)) or value is None:
            return value
        return str(value)
