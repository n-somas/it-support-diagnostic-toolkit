"""Speichert Diagnoseläufe für Verlaufsdiagramme."""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime
from pathlib import Path


class ScanHistoryService:
    def __init__(self, directory: str | Path = "data/scans") -> None:
        self.directory = Path(directory)

    def save(self, results: list[tuple[str, dict]]) -> Path:
        self.directory.mkdir(parents=True, exist_ok=True)
        now = datetime.now()
        counts = Counter(self._rating(result) for _, result in results)

        payload = {
            "created_at": now.isoformat(timespec="seconds"),
            "status_counts": {
                status: counts.get(status, 0)
                for status in (
                    "OK",
                    "INFO",
                    "HINWEIS",
                    "WARNUNG",
                    "KRITISCH",
                    "FEHLER",
                )
            },
        }

        path = self.directory / now.strftime(
            "scan_%Y-%m-%d_%H-%M-%S.json"
        )
        path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return path

    def load_recent(self, limit: int = 10) -> list[dict]:
        if not self.directory.exists():
            return []

        records = []

        for path in sorted(
            self.directory.glob("scan_*.json"),
            reverse=True,
        )[:limit]:
            try:
                records.append(
                    json.loads(path.read_text(encoding="utf-8"))
                )
            except (OSError, json.JSONDecodeError):
                continue

        return list(reversed(records))

    @staticmethod
    def _rating(result: dict) -> str:
        value = result.get(
            "Bewertung",
            result.get("Status", "INFO"),
        )
        return str(value).upper()
