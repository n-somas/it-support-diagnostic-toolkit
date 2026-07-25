"""Tests für die Windows-Ereignisauswertung."""

from __future__ import annotations

import unittest

from src.checks.windows_event_check import (
    classify_event,
    evaluate_events,
    parse_event_payload,
)


def event(
    provider: str,
    event_id: int,
    level: int = 2,
    log_name: str = "System",
    time_created: str = "2026-07-25T18:30:00+02:00",
) -> dict[str, object]:
    return {
        "ProviderName": provider,
        "Id": event_id,
        "Level": level,
        "LogName": log_name,
        "TimeCreated": time_created,
    }


class WindowsEventCheckTests(unittest.TestCase):
    def test_empty_successful_query_is_ok(self) -> None:
        result = evaluate_events(
            [],
            successful_logs=["System", "Application"],
        )

        self.assertEqual(result["Bewertung"], "OK")
        self.assertEqual(result["Erfasste Ereignisse"], 0)

    def test_kernel_power_41_is_critical(self) -> None:
        result = evaluate_events(
            [
                event(
                    "Microsoft-Windows-Kernel-Power",
                    41,
                    level=1,
                )
            ],
            successful_logs=["System", "Application"],
        )

        self.assertEqual(result["Bewertung"], "KRITISCH")
        self.assertEqual(result["Kritisch bewertet"], 1)

    def test_eventlog_6008_is_critical(self) -> None:
        classification = classify_event(
            event("EventLog", 6008)
        )

        self.assertEqual(
            classification["category"],
            "Unerwartetes Herunterfahren",
        )
        self.assertEqual(
            classification["severity"],
            "KRITISCH",
        )

    def test_application_error_1000_is_warning(self) -> None:
        result = evaluate_events(
            [
                event(
                    "Application Error",
                    1000,
                    log_name="Application",
                )
            ],
            successful_logs=["System", "Application"],
        )

        self.assertEqual(result["Bewertung"], "WARNUNG")
        self.assertEqual(result["Als Warnung bewertet"], 1)

    def test_unknown_error_is_hint(self) -> None:
        result = evaluate_events(
            [event("Example Provider", 9001)],
            successful_logs=["System"],
        )

        self.assertEqual(result["Bewertung"], "HINWEIS")
        self.assertEqual(result["Weitere Fehlerhinweise"], 1)

    def test_duplicate_events_are_grouped(self) -> None:
        records = [
            event("Application Error", 1000),
            event(
                "Application Error",
                1000,
                time_created="2026-07-25T19:00:00+02:00",
            ),
        ]

        result = evaluate_events(
            records,
            successful_logs=["Application"],
        )

        self.assertEqual(len(result["Ereignisübersicht"]), 1)
        self.assertIn("2×", result["Ereignisübersicht"][0])

    def test_failed_logs_without_success_are_error(self) -> None:
        result = evaluate_events(
            [],
            query_errors=["System: Zugriff verweigert"],
            successful_logs=[],
        )

        self.assertEqual(result["Bewertung"], "FEHLER")

    def test_payload_normalization(self) -> None:
        payload = (
            '{"Events":{"ProviderName":"EventLog","Id":6008,'
            '"Level":2,"LogName":"System","TimeCreated":"2026-07-25"},'
            '"Errors":[],"SuccessfulLogs":"System"}'
        )

        events, errors, logs = parse_event_payload(payload)

        self.assertEqual(len(events), 1)
        self.assertEqual(errors, [])
        self.assertEqual(logs, ["System"])


if __name__ == "__main__":
    unittest.main()
