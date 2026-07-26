"""Tests für die Analyse von Windows-Autostartprogrammen."""

from __future__ import annotations

import unittest

from src.checks.startup_programs_check import (
    evaluate_startup_programs,
    parse_startup_payload,
)


def startup_item(
    name: str = "Beispiel",
    command: str = r'"C:\Program Files\Example\example.exe"',
    target_path: str = r"C:\Program Files\Example\example.exe",
    target_exists: bool | None = True,
    signature_status: str = "Valid",
) -> dict:
    return {
        "Name": name,
        "Command": command,
        "Location": "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run",
        "User": "Test",
        "TargetPath": target_path,
        "TargetExists": target_exists,
        "SignatureStatus": signature_status,
        "Publisher": "CN=Example",
    }


class StartupProgramsCheckTests(unittest.TestCase):
    def test_valid_signed_program_is_ok(self) -> None:
        result = evaluate_startup_programs(
            [startup_item()]
        )

        self.assertEqual(result["Bewertung"], "OK")
        self.assertEqual(result["Autostartprogramme"], 1)
        self.assertEqual(result["Auffällige Einträge"], 0)

    def test_missing_target_is_warning(self) -> None:
        result = evaluate_startup_programs(
            [
                startup_item(
                    target_exists=False,
                )
            ]
        )

        self.assertEqual(result["Bewertung"], "WARNUNG")
        self.assertEqual(result["Fehlende Zieldateien"], 1)

    def test_powershell_start_is_warning(self) -> None:
        result = evaluate_startup_programs(
            [
                startup_item(
                    command=(
                        'powershell.exe -ExecutionPolicy Bypass '
                        '-File "C:\\Users\\Test\\script.ps1"'
                    ),
                    target_path="powershell.exe",
                    target_exists=True,
                )
            ]
        )

        self.assertEqual(result["Bewertung"], "WARNUNG")
        self.assertTrue(result["Warnungen"])

    def test_unsigned_normal_program_is_hint(self) -> None:
        result = evaluate_startup_programs(
            [
                startup_item(
                    signature_status="NotSigned",
                )
            ]
        )

        self.assertEqual(result["Bewertung"], "HINWEIS")
        self.assertEqual(result["Prüfhinweise"], 1)

    def test_duplicate_items_are_counted_once(self) -> None:
        item = startup_item()
        result = evaluate_startup_programs([item, dict(item)])

        self.assertEqual(result["Autostartprogramme"], 1)

    def test_single_json_object_becomes_list(self) -> None:
        payload = (
            '{"Name":"Example","Command":"example.exe",'
            '"Location":"Run","User":"Test"}'
        )
        parsed = parse_startup_payload(payload)

        self.assertEqual(len(parsed), 1)
        self.assertEqual(parsed[0]["Name"], "Example")


if __name__ == "__main__":
    unittest.main()
