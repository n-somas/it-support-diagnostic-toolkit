import socket
import subprocess


def check_ping(target):
    """
    Prüft per Ping, ob ein Ziel erreichbar ist.
    Die Ausgabe wird bewusst unterdrückt, weil Windows-Ausgaben je nach Sprache
    Encoding-Probleme verursachen können.
    """

    result = subprocess.run(
        ["ping", "-n", "1", "-w", "2000", target],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    return result.returncode == 0


def check_dns(domain):
    """
    Prüft, ob eine Domain per DNS aufgelöst werden kann.
    Beispiel: google.com -> IP-Adresse
    """

    try:
        ip_address = socket.gethostbyname(domain)
        return {
            "status": "OK",
            "domain": domain,
            "ip_address": ip_address
        }
    except socket.gaierror:
        return {
            "status": "Fehler",
            "domain": domain,
            "ip_address": "Nicht auflösbar"
        }


def get_active_ip_address():
    """
    Ermittelt die aktive lokale IP-Adresse.
    Diese Methode ist genauer als socket.gethostbyname(hostname),
    weil Windows sonst oft VirtualBox-, VPN- oder interne Adapter zurückgibt.
    """

    try:
        temp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        temp_socket.connect(("8.8.8.8", 80))
        ip_address = temp_socket.getsockname()[0]
        temp_socket.close()
        return ip_address
    except OSError:
        return "Nicht ermittelbar"


def get_default_gateway():
    """
    Ermittelt das Standardgateway über PowerShell.
    Das Standardgateway ist meist der Router im lokalen Netzwerk.
    """

    command = [
        "powershell",
        "-NoProfile",
        "-Command",
        "Get-NetRoute -DestinationPrefix '0.0.0.0/0' | "
        "Sort-Object RouteMetric | "
        "Select-Object -First 1 -ExpandProperty NextHop"
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="ignore",
        creationflags=subprocess.CREATE_NO_WINDOW,
    )

    gateway = result.stdout.strip()

    if gateway:
        return gateway

    return "Nicht ermittelbar"


def get_network_info():
    """
    Führt grundlegende Netzwerkprüfungen durch.
    Diese Checks sind typisch für IT-Support und Fehlerdiagnose.
    """

    dns_result = check_dns("google.com")

    return {
        "Aktive IP-Adresse": get_active_ip_address(),
        "Standardgateway": get_default_gateway(),
        "Ping Google DNS 8.8.8.8": "OK" if check_ping("8.8.8.8") else "Fehler",
        "Ping Cloudflare DNS 1.1.1.1": "OK" if check_ping("1.1.1.1") else "Fehler",
        "DNS-Auflösung google.com": dns_result["status"],
        "DNS-IP google.com": dns_result["ip_address"],
    }