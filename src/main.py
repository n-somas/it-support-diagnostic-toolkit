from checks.system_info import get_system_info
from checks.network_check import get_network_info
from checks.disk_check import get_disk_info
from checks.firewall_check import get_firewall_info
from checks.defender_check import get_defender_info
from checks.windows_update_check import get_windows_update_info
from checks.open_ports_check import get_open_ports_info
from report.markdown_report import save_markdown_report


def print_section(title, data):
    """
    Gibt einen Abschnitt mit Überschrift und Key-Value-Daten aus.
    So bleibt die Konsolenausgabe übersichtlich.
    """

    print(f"\n{title}:")
    print("-" * 35)

    for key, value in data.items():
        print(f"{key}: {value}")


def main():
    """
    Einstiegspunkt des Programms.
    Hier werden die einzelnen Diagnose-Checks gestartet.
    """

    print("IT Support Diagnostic Toolkit")
    print("=" * 35)

    # Alle Diagnose-Checks ausführen
    system_info = get_system_info()
    network_info = get_network_info()
    disk_info = get_disk_info()
    firewall_info = get_firewall_info()
    defender_info = get_defender_info()
    windows_update_info = get_windows_update_info()
    open_ports_info = get_open_ports_info()

    # Ergebnisse als Abschnitte sammeln
    sections = [
        ("Systeminformationen", system_info),
        ("Netzwerkprüfung", network_info),
        ("Speicherplatzprüfung", disk_info),
        ("Firewallprüfung", firewall_info),
        ("Defenderprüfung", defender_info),
        ("Windows Update Prüfung", windows_update_info),
        ("Offene Ports Prüfung", open_ports_info),
    ]

    # Ergebnisse in der Konsole anzeigen
    for title, data in sections:
        print_section(title, data)

    # Markdown-Bericht speichern
    report_path = save_markdown_report(sections)

    print("\nBericht erstellt:")
    print("-" * 35)
    print(report_path)


if __name__ == "__main__":
    main()