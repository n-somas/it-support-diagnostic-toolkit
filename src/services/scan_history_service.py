"""Speichert und lädt Diagnoseläufe für Verlauf und Vergleich."""

from __future__ import annotations

import json
import re
from collections import Counter
from collections.abc import Mapping, Sequence
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
            "schema_version": 3,
            "created_at": now.isoformat(timespec="seconds"),
            "status_counts": {
                status: counts.get(status, 0)
                for status in STATUSES
            },
            "disk_usage": self.extract_disk_usage(results),
            "results": [
                {
                    "title": title,
                    "status": self._rating(result),
                    "details": self._json_safe(result),
                }
                for title, result in results
            ],
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
        return list(reversed(self.list_scans(limit=limit)))

    def list_scans(self, limit: int | None = None) -> list[dict]:
        if not self.directory.exists():
            return []

        paths = sorted(
            self.directory.glob("scan_*.json"),
            reverse=True,
        )
        if limit is not None:
            paths = paths[:limit]

        scans = []
        for path in paths:
            try:
                scan = json.loads(
                    path.read_text(encoding="utf-8")
                )
            except (OSError, json.JSONDecodeError):
                continue

            if not isinstance(scan.get("disk_usage"), Mapping):
                scan["disk_usage"] = self.extract_disk_usage(
                    scan.get("results", [])
                )

            scan["_path"] = str(path.resolve())
            scan["_filename"] = path.name
            scan["_has_details"] = bool(scan.get("results"))
            scans.append(scan)

        return scans

    @classmethod
    def extract_disk_usage(
        cls,
        results: Sequence[Any],
    ) -> dict[str, Any] | None:
        """Extrahiert Speicherwerte aus aktuellen und älteren Scans."""

        for item in results:
            title = ""
            details: Mapping[str, Any] | None = None

            if (
                isinstance(item, (list, tuple))
                and len(item) >= 2
            ):
                title = str(item[0])
                if isinstance(item[1], Mapping):
                    details = item[1]
            elif isinstance(item, Mapping):
                title = str(item.get("title", ""))
                candidate = item.get(
                    "details",
                    item.get("result"),
                )
                if isinstance(candidate, Mapping):
                    details = candidate

            if details is None:
                continue

            title_lower = title.casefold()
            if (
                "speicher" not in title_lower
                and "disk" not in title_lower
                and "laufwerk" not in title_lower
            ):
                continue

            total = cls._number(
                details.get("Gesamtspeicher")
            )
            used = cls._number(
                details.get("Belegter Speicher")
            )
            free = cls._number(
                details.get("Freier Speicher")
            )
            free_percent = cls._number(
                details.get("Freier Speicher in Prozent")
            )

            if total is None and used is not None and free is not None:
                total = used + free
            if used is None and total is not None and free is not None:
                used = max(0.0, total - free)
            if free is None and total is not None and used is not None:
                free = max(0.0, total - used)

            if total is None or used is None or free is None:
                continue

            if free_percent is None and total > 0:
                free_percent = free / total * 100

            return {
                "drive": str(details.get("Laufwerk", "C:")),
                "total_gb": round(total, 2),
                "used_gb": round(used, 2),
                "free_gb": round(free, 2),
                "free_percent": (
                    round(free_percent, 2)
                    if free_percent is not None
                    else None
                ),
            }

        return None

    @staticmethod
    def _number(value: Any) -> float | None:
        if value is None:
            return None

        match = re.search(
            r"-?\d+(?:[.,]\d+)?",
            str(value),
        )
        if match is None:
            return None

        try:
            return float(match.group(0).replace(",", "."))
        except ValueError:
            return None

    @staticmethod
    def _rating(result: dict) -> str:
        value = result.get(
            "Bewertung",
            result.get("Status", "INFO"),
        )
        status = str(value).upper()
        return status if status in STATUSES else "INFO"

    @classmethod
    def _json_safe(cls, value: Any) -> Any:
        if isinstance(value, dict):
            return {
                str(key): cls._json_safe(item)
                for key, item in value.items()
            }
        if isinstance(value, (list, tuple, set)):
            return [
                cls._json_safe(item)
                for item in value
            ]
        if (
            isinstance(value, (str, int, float, bool))
            or value is None
        ):
            return value
        return str(value)
