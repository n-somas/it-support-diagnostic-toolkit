"""Tests für Speicherwerte in der Scan-Historie."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from src.services.scan_history_service import ScanHistoryService


DISK_RESULT = {
    "Laufwerk": "C:",
    "Gesamtspeicher": "500.0 GB",
    "Belegter Speicher": "325.5 GB",
    "Freier Speicher": "174.5 GB",
    "Freier Speicher in Prozent": "34.9 %",
    "Bewertung": "OK",
}


class ScanHistoryServiceTests(unittest.TestCase):
    def test_new_scan_contains_structured_disk_usage(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            service = ScanHistoryService(directory)
            path = service.save(
                [("Speicherplatzprüfung", DISK_RESULT)]
            )

            payload = json.loads(
                path.read_text(encoding="utf-8")
            )

            self.assertEqual(payload["schema_version"], 3)
            self.assertEqual(
                payload["disk_usage"]["used_gb"],
                325.5,
            )
            self.assertEqual(
                payload["disk_usage"]["free_gb"],
                174.5,
            )

    def test_old_scan_gets_disk_usage_when_loaded(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            scan_directory = Path(directory)
            path = scan_directory / "scan_2026-07-26_10-00-00.json"
            path.write_text(
                json.dumps(
                    {
                        "schema_version": 2,
                        "created_at": "2026-07-26T10:00:00",
                        "status_counts": {"OK": 1},
                        "results": [
                            {
                                "title": "Speicherplatzprüfung",
                                "status": "OK",
                                "details": DISK_RESULT,
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            service = ScanHistoryService(scan_directory)
            scans = service.list_scans()

            self.assertEqual(len(scans), 1)
            self.assertEqual(
                scans[0]["disk_usage"]["total_gb"],
                500.0,
            )

    def test_extract_disk_usage_accepts_comma_values(self) -> None:
        result = dict(DISK_RESULT)
        result["Belegter Speicher"] = "325,5 GB"

        usage = ScanHistoryService.extract_disk_usage(
            [("Speicherplatzprüfung", result)]
        )

        self.assertIsNotNone(usage)
        self.assertEqual(usage["used_gb"], 325.5)


if __name__ == "__main__":
    unittest.main()
