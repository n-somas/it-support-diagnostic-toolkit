"""Zentrale Ausführung der vorhandenen Diagnoseprüfungen."""

from collections.abc import Callable

from src.checks.bitlocker_check import get_bitlocker_info
from src.checks.defender_check import get_defender_info
from src.checks.disk_check import get_disk_info
from src.checks.firewall_check import get_firewall_info
from src.checks.network_check import get_network_info
from src.checks.open_ports_check import get_open_ports_info
from src.checks.system_info import get_system_info
from src.checks.windows_update_check import get_windows_update_info

ProgressCallback = Callable[[str, int, int], None]


DIAGNOSTIC_CHECKS = [
    ("Systeminformationen", get_system_info),
    ("Netzwerkprüfung", get_network_info),
    ("Speicherplatzprüfung", get_disk_info),
    ("Firewallprüfung", get_firewall_info),
    ("Defenderprüfung", get_defender_info),
    ("Windows Update Prüfung", get_windows_update_info),
    ("Offene Ports Prüfung", get_open_ports_info),
    ("BitLocker Prüfung", get_bitlocker_info),
]


def run_all_diagnostics(
    progress_callback: ProgressCallback | None = None,
) -> list[tuple[str, dict]]:
    """
    Führt alle vorhandenen Diagnoseprüfungen nacheinander aus.

    Der optionale Callback erhält den Namen der Prüfung sowie den aktuellen
    Schritt und die Gesamtzahl aller Prüfungen.
    """

    results: list[tuple[str, dict]] = []
    total_checks = len(DIAGNOSTIC_CHECKS)

    for current_step, (title, check_function) in enumerate(
        DIAGNOSTIC_CHECKS,
        start=1,
    ):
        if progress_callback is not None:
            progress_callback(title, current_step, total_checks)

        try:
            result = check_function()
        except Exception as error:
            result = {
                "Bewertung": "FEHLER",
                "Fehler": str(error),
            }

        results.append((title, result))

    return results