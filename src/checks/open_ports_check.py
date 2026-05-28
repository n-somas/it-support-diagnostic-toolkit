import subprocess


def run_powershell_command(command):
    """
    Führt einen PowerShell-Befehl aus und gibt die Ausgabe zurück.
    Encoding-Probleme werden abgefangen, damit das Tool stabil läuft.
    """

    result = subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-Command",
            command
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="ignore"
    )

    return result.stdout.strip()


def get_listening_tcp_ports():
    """
    Ermittelt lokal lauschende TCP-Ports.
    Das ist relevant, um zu sehen, welche Dienste auf dem System Verbindungen annehmen.
    """

    command = (
        "Get-NetTCPConnection -State Listen | "
        "Select-Object -Property LocalAddress,LocalPort,OwningProcess | "
        "Sort-Object LocalPort | "
        "Format-Table -AutoSize"
    )

    output = run_powershell_command(command)

    if output:
        return output

    return "Keine offenen TCP-Listening-Ports ermittelbar"


def count_listening_tcp_ports():
    """
    Zählt lokal lauschende TCP-Ports.
    """

    command = (
        "(Get-NetTCPConnection -State Listen | "
        "Measure-Object).Count"
    )

    output = run_powershell_command(command)

    if output.isdigit():
        return int(output)

    return 0


def evaluate_open_ports(port_count):
    """
    Bewertet die Anzahl offener Listening-Ports grob.

    Diese Bewertung ist bewusst vorsichtig:
    Offene Ports sind nicht automatisch gefährlich.
    Sie sollten aber im Support- oder Security-Kontext geprüft werden.
    """

    if port_count == 0:
        return "OK"

    if port_count <= 20:
        return "HINWEIS"

    return "WARNUNG"


def get_open_ports_info():
    """
    Prüft lokal offene TCP-Listening-Ports.
    """

    port_count = count_listening_tcp_ports()
    listening_ports = get_listening_tcp_ports()

    return {
        "Anzahl offener TCP-Listening-Ports": port_count,
        "Offene TCP-Listening-Ports": listening_ports,
        "Bewertung": evaluate_open_ports(port_count),
        "Hinweis": "Offene Ports sind nicht automatisch gefährlich, sollten aber nachvollziehbar sein.",
    }