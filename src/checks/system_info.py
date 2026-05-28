import getpass
import os
import platform
import shutil


def format_bytes(size_in_bytes):
    """
    Wandelt Bytes in Gigabyte um.
    Beispiel: 17179869184 Bytes -> 16.00 GB
    """
    gb_value = size_in_bytes / (1024 ** 3)
    return f"{gb_value:.2f} GB"


def get_system_info():
    """
    Liest grundlegende Systeminformationen des Windows-PCs aus.
    Diese Informationen sind für typische IT-Supportfälle wichtig.
    """

    # Speicherplatz von Laufwerk C: auslesen
    total, used, free = shutil.disk_usage("C:\\")

    # Systeminformationen als Dictionary zurückgeben
    return {
        "Computername": platform.node(),
        "Benutzername": getpass.getuser(),
        "Betriebssystem": platform.system(),
        "Windows-Version": platform.version(),
        "Windows-Release": platform.release(),
        "Architektur": platform.machine(),
        "Prozessor": platform.processor(),
        "CPU-Kerne": os.cpu_count(),
        "Speicher Gesamt": format_bytes(total),
        "Speicher Belegt": format_bytes(used),
        "Speicher Frei": format_bytes(free),
    }