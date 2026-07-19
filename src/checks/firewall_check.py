import subprocess
from src.utils.hidden_process import get_hidden_process_options


def run_powershell_command(command):
    """
    Führt einen PowerShell-Befehl aus und gibt die Ausgabe zurück.
    Encoding-Probleme werden abgefangen, damit das Tool stabil läuft.
    """

    result = subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-NonInteractive",
            "-Command",
            command
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="ignore",
    **get_hidden_process_options(),
    )

    return result.stdout.strip()


def convert_firewall_status(value):
    """
    Wandelt True/False aus PowerShell in verständliche deutsche Werte um.
    """

    if value.strip().lower() == "true":
        return "Aktiv"

    if value.strip().lower() == "false":
        return "Inaktiv"

    return "Nicht ermittelbar"


def evaluate_firewall_status(domain, private, public):
    """
    Bewertet den Firewall-Status.
    Wenn alle Profile aktiv sind, ist die Bewertung OK.
    Sobald ein Profil inaktiv ist, gibt es eine Warnung.
    """

    if domain == "Aktiv" and private == "Aktiv" and public == "Aktiv":
        return "OK"

    return "WARNUNG"


def get_firewall_info():
    """
    Prüft den Status der Windows-Firewall-Profile:
    Domäne, Privat und Öffentlich.
    """

    domain_status = run_powershell_command(
        "(Get-NetFirewallProfile -Profile Domain).Enabled"
    )

    private_status = run_powershell_command(
        "(Get-NetFirewallProfile -Profile Private).Enabled"
    )

    public_status = run_powershell_command(
        "(Get-NetFirewallProfile -Profile Public).Enabled"
    )

    domain = convert_firewall_status(domain_status)
    private = convert_firewall_status(private_status)
    public = convert_firewall_status(public_status)

    return {
        "Domänenprofil": domain,
        "Privates Profil": private,
        "Öffentliches Profil": public,
        "Bewertung": evaluate_firewall_status(domain, private, public),
    }