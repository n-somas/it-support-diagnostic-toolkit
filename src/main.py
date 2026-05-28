from checks.system_info import get_system_info
from checks.network_check import get_network_info
from checks.disk_check import get_disk_info
from checks.firewall_check import get_firewall_info

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

    # Systeminformationen auslesen und anzeigen
    system_info = get_system_info()
    print_section("Systeminformationen", system_info)

    # Netzwerkinformationen auslesen und anzeigen
    network_info = get_network_info()
    print_section("Netzwerkprüfung", network_info)

    # Speicherplatz prüfen und anzeigen
    disk_info = get_disk_info()
    print_section("Speicherplatzprüfung", disk_info)

    # Windows-Firewall prüfen und anzeigen
    firewall_info = get_firewall_info()
    print_section("Firewallprüfung", firewall_info)


if __name__ == "__main__":
    main()