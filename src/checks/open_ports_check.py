import subprocess


SUSPICIOUS_PORTS = {
    21: "FTP",
    22: "SSH",
    23: "Telnet",
    80: "HTTP",
    135: "Windows RPC",
    139: "NetBIOS",
    445: "SMB",
    1433: "Microsoft SQL Server",
    3306: "MySQL/MariaDB",
    3389: "Remote Desktop",
    5432: "PostgreSQL",
    5900: "VNC",
    8080: "HTTP Alternative",
}


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


def get_tcp_listening_connections():
    """
    Ermittelt lokal lauschende TCP-Verbindungen als CSV.
    CSV ist besser als Format-Table, weil die Daten danach sauber verarbeitet werden können.
    """

    command = (
        "Get-NetTCPConnection -State Listen | "
        "Select-Object LocalAddress,LocalPort,OwningProcess | "
        "Sort-Object LocalPort | "
        "ConvertTo-Csv -NoTypeInformation"
    )

    output = run_powershell_command(command)

    if not output:
        return []

    lines = output.splitlines()
    data_lines = lines[1:]

    connections = []

    for line in data_lines:
        parts = [part.strip().strip('"') for part in line.split(",")]

        if len(parts) != 3:
            continue

        local_address = parts[0]
        local_port = parts[1]
        owning_process = parts[2]

        try:
            local_port = int(local_port)
            owning_process = int(owning_process)
        except ValueError:
            continue

        connections.append(
            {
                "local_address": local_address,
                "local_port": local_port,
                "owning_process": owning_process,
            }
        )

    return connections


def get_process_name(process_id):
    """
    Ermittelt den Prozessnamen zu einer Prozess-ID.
    Wenn kein Prozess gefunden wird, wird ein neutraler Wert zurückgegeben.
    """

    command = (
        f"Get-Process -Id {process_id} -ErrorAction SilentlyContinue | "
        "Select-Object -ExpandProperty ProcessName"
    )

    output = run_powershell_command(command)

    if output:
        return output

    return "Nicht ermittelbar"


def is_local_only_address(address):
    """
    Prüft, ob eine Adresse nur lokal auf dem eigenen Gerät erreichbar ist.
    """

    return address in ["127.0.0.1", "::1"]


def is_network_reachable_address(address):
    """
    Prüft, ob eine Adresse potenziell im Netzwerk erreichbar ist.
    """

    if address in ["0.0.0.0", "::"]:
        return True

    if address.startswith("192.168."):
        return True

    if address.startswith("10."):
        return True

    if address.startswith("172."):
        return True

    return False


def get_suspicious_ports(connections):
    """
    Prüft, ob bekannte sensible Ports offen sind.
    Zusätzlich wird der zugehörige Prozessname ermittelt.
    """

    found_ports = {}

    for connection in connections:
        port = connection["local_port"]
        process_id = connection["owning_process"]

        if port in SUSPICIOUS_PORTS:
            process_name = get_process_name(process_id)

            found_ports[port] = {
                "service": SUSPICIOUS_PORTS[port],
                "process_id": process_id,
                "process_name": process_name,
            }

    return found_ports


def format_suspicious_ports(suspicious_ports):
    """
    Formatiert auffällige Ports inklusive Dienst und Prozessname.
    """

    if not suspicious_ports:
        return "Keine auffälligen Standardports erkannt"

    formatted_ports = []

    for port, info in suspicious_ports.items():
        service_name = info["service"]
        process_name = info["process_name"]
        process_id = info["process_id"]

        formatted_ports.append(
            f"{port} ({service_name}) → {process_name} [PID: {process_id}]"
        )

    return ", ".join(formatted_ports)


def evaluate_open_ports(network_reachable_count, suspicious_ports):
    """
    Bewertet die offenen Ports.
    """

    if suspicious_ports:
        return "WARNUNG"

    if network_reachable_count > 10:
        return "WARNUNG"

    if network_reachable_count > 0:
        return "HINWEIS"

    return "OK"


def create_open_ports_note(suspicious_ports):
    """
    Erstellt einen verständlichen Hinweis für den Support-Bericht.
    """

    if 3306 in suspicious_ports:
        return "Port 3306 ist häufig MySQL/MariaDB. Der Dienst sollte nicht unnötig im Netzwerk erreichbar sein."

    if 445 in suspicious_ports:
        return "Port 445 wird für SMB-Dateifreigaben verwendet. Der Dienst sollte nur in vertrauenswürdigen Netzwerken erreichbar sein."

    if 3389 in suspicious_ports:
        return "Port 3389 wird für Remote Desktop verwendet. Remote-Zugriff sollte besonders geschützt werden."

    if suspicious_ports:
        return "Es wurden auffällige Standardports erkannt. Diese sollten geprüft und dokumentiert werden."

    return "Offene Ports sind nicht automatisch gefährlich, sollten aber nachvollziehbar sein."


def get_open_ports_info():
    """
    Prüft lokal offene TCP-Listening-Ports und bewertet sie.
    """

    connections = get_tcp_listening_connections()

    total_count = len(connections)

    local_only_count = sum(
        1 for connection in connections
        if is_local_only_address(connection["local_address"])
    )

    network_reachable_count = sum(
        1 for connection in connections
        if is_network_reachable_address(connection["local_address"])
    )

    suspicious_ports = get_suspicious_ports(connections)

    return {
        "Anzahl offener TCP-Listening-Ports": total_count,
        "Nur lokal erreichbare Ports": local_only_count,
        "Im Netzwerk erreichbare Ports": network_reachable_count,
        "Auffällige Standardports": format_suspicious_ports(suspicious_ports),
        "Bewertung": evaluate_open_ports(network_reachable_count, suspicious_ports),
        "Hinweis": create_open_ports_note(suspicious_ports),
    }