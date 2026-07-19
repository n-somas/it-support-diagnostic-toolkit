import socket
import subprocess

from src.utils.hidden_process import get_hidden_process_options


def check_ping(target: str) -> bool:
    """
    Prüft per Ping, ob ein Ziel erreichbar ist.
    Der Prozess läuft ohne sichtbares Konsolenfenster.
    """

    result = subprocess.run(
        [
            "ping",
            "-n",
            "1",
            "-w",
            "2000",
            target,
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
        **get_hidden_process_options(),
    )

    return result.returncode == 0


def check_dns(domain: str) -> dict:
    """Prüft, ob eine Domain per DNS aufgelöst werden kann."""

    try:
        ip_address = socket.gethostbyname(domain)

        return {
            "status": "OK",
            "domain": domain,
            "ip_address": ip_address,
        }

    except socket.gaierror:
        return {
            "status": "Fehler",
            "domain": domain,
            "ip_address": "Nicht auflösbar",
        }


def get_active_ip_address() -> str:
    """Ermittelt die aktive lokale IPv4-Adresse."""

    temp_socket = socket.socket(
        socket.AF_INET,
        socket.SOCK_DGRAM,
    )

    try:
        temp_socket.connect(("8.8.8.8", 80))
        return temp_socket.getsockname()[0]

    except OSError:
        return "Nicht ermittelbar"

    finally:
        temp_socket.close()


def get_default_gateway() -> str:
    """Ermittelt das Standardgateway über PowerShell."""

    command = [
        "powershell.exe",
        "-NoLogo",
        "-NoProfile",
        "-NonInteractive",
        "-Command",
        (
            "Get-NetRoute -DestinationPrefix '0.0.0.0/0' | "
            "Sort-Object RouteMetric | "
            "Select-Object -First 1 -ExpandProperty NextHop"
        ),
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="ignore",
        check=False,
        **get_hidden_process_options(),
    )

    gateway = result.stdout.strip()

    if gateway:
        return gateway

    return "Nicht ermittelbar"


def get_network_info() -> dict:
    """Führt grundlegende Netzwerkprüfungen durch."""

    dns_result = check_dns("google.com")
    google_ping = check_ping("8.8.8.8")
    cloudflare_ping = check_ping("1.1.1.1")

    network_available = (
        google_ping
        or cloudflare_ping
        or dns_result["status"] == "OK"
    )

    return {
        "Aktive IP-Adresse": get_active_ip_address(),
        "Standardgateway": get_default_gateway(),
        "Ping Google DNS 8.8.8.8": (
            "OK" if google_ping else "Fehler"
        ),
        "Ping Cloudflare DNS 1.1.1.1": (
            "OK" if cloudflare_ping else "Fehler"
        ),
        "DNS-Auflösung google.com": dns_result["status"],
        "DNS-IP google.com": dns_result["ip_address"],
        "Bewertung": (
            "OK" if network_available else "WARNUNG"
        ),
    }