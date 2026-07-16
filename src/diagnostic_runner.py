"""Zentrale Ausführung der vorhandenen Diagnoseprüfungen."""

from checks.bitlocker_check import get_bitlocker_info
from checks.defender_check import get_defender_info
from checks.disk_check import get_disk_info
from checks.firewall_check import get_firewall_info
from checks.network_check import get_network_info
from checks.open_ports_check import get_open_ports_info
from checks.system_info import get_system_info
from checks.windows_update_check import get_windows_update_info


def run_all_diagnostics() -> list[tuple[str, dict]]:
    """Führt alle vorhandenen Diagnoseprüfungen nacheinander aus."""

    return [
        ("Systeminformationen", get_system_info()),
        ("Netzwerkprüfung", get_network_info()),
        ("Speicherplatzprüfung", get_disk_info()),
        ("Firewallprüfung", get_firewall_info()),
        ("Defenderprüfung", get_defender_info()),
        ("Windows Update Prüfung", get_windows_update_info()),
        ("Offene Ports Prüfung", get_open_ports_info()),
        ("BitLocker Prüfung", get_bitlocker_info()),
    ]