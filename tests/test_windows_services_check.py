"""Tests für die Bewertung ausgewählter Windows-Dienste."""

from __future__ import annotations

import unittest

from src.checks.windows_services_check import (
    SERVICE_RULES,
    evaluate_services,
    parse_service_payload,
)


def service_record(
    name: str,
    state: str = "Running",
    start_mode: str = "Auto",
) -> dict[str, str]:
    return {
        "Name": name,
        "DisplayName": name,
        "State": state,
        "StartMode": start_mode,
        "Status": "OK",
    }


class WindowsServicesCheckTests(unittest.TestCase):
    def test_healthy_services_are_ok(self) -> None:
        records = []

        for name, rule in SERVICE_RULES.items():
            if rule["expected_running"]:
                records.append(service_record(name))
            else:
                records.append(
                    service_record(
                        name,
                        state="Stopped",
                        start_mode="Manual",
                    )
                )

        result = evaluate_services(records)

        self.assertEqual(result["Bewertung"], "OK")
        self.assertEqual(
            result["Gefundene Dienste"],
            len(SERVICE_RULES),
        )
        self.assertNotIn("Warnungen", result)

    def test_stopped_required_service_is_warning(self) -> None:
        records = [
            service_record(name)
            for name in SERVICE_RULES
        ]

        for record in records:
            if record["Name"] == "EventLog":
                record["State"] = "Stopped"

        result = evaluate_services(records)

        self.assertEqual(result["Bewertung"], "WARNUNG")
        self.assertTrue(
            any(
                "Windows-Ereignisprotokoll" in warning
                for warning in result["Warnungen"]
            )
        )

    def test_disabled_windows_update_is_warning(self) -> None:
        records = [
            service_record(name)
            for name in SERVICE_RULES
        ]

        for record in records:
            if record["Name"] == "wuauserv":
                record["State"] = "Stopped"
                record["StartMode"] = "Disabled"

        result = evaluate_services(records)

        self.assertEqual(result["Bewertung"], "WARNUNG")
        self.assertEqual(result["Deaktiviert"], 1)

    def test_optional_disabled_service_is_hint(self) -> None:
        records = []

        for name in SERVICE_RULES:
            if name == "W32Time":
                records.append(
                    service_record(
                        name,
                        state="Stopped",
                        start_mode="Disabled",
                    )
                )
            else:
                records.append(service_record(name))

        result = evaluate_services(records)

        self.assertEqual(result["Bewertung"], "HINWEIS")
        self.assertIn("Hinweise", result)

    def test_single_json_object_becomes_list(self) -> None:
        parsed = parse_service_payload(
            '{"Name":"EventLog","State":"Running"}'
        )

        self.assertEqual(len(parsed), 1)
        self.assertEqual(parsed[0]["Name"], "EventLog")


if __name__ == "__main__":
    unittest.main()
