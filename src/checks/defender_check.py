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


def convert_boolean_status(value):
    """
    Wandelt True/False-Werte aus PowerShell in verständliche deutsche Werte um.
    """

    value = value.strip().lower()

    if value == "true":
        return "Aktiv"

    if value == "false":
        return "Inaktiv"

    return "Nicht ermittelbar"


def evaluate_defender_status(real_time_protection, antivirus_enabled):
    """
    Bewertet den Windows Defender Status.
    Echtzeitschutz und Antivirus müssen aktiv sein.
    """

    if real_time_protection == "Aktiv" and antivirus_enabled == "Aktiv":
        return "OK"

    return "WARNUNG"


def get_defender_info():
    """
    Prüft grundlegende Informationen zum Microsoft Defender.
    Dieser Check ist relevant für IT-Support und Security-Grundlagen.
    """

    real_time_status = run_powershell_command(
        "(Get-MpComputerStatus).RealTimeProtectionEnabled"
    )

    antivirus_status = run_powershell_command(
        "(Get-MpComputerStatus).AntivirusEnabled"
    )

    signature_version = run_powershell_command(
        "(Get-MpComputerStatus).AntivirusSignatureVersion"
    )

    last_signature_update = run_powershell_command(
        "(Get-MpComputerStatus).AntivirusSignatureLastUpdated"
    )

    real_time_protection = convert_boolean_status(real_time_status)
    antivirus_enabled = convert_boolean_status(antivirus_status)

    return {
        "Echtzeitschutz": real_time_protection,
        "Antivirus aktiviert": antivirus_enabled,
        "Signaturversion": signature_version if signature_version else "Nicht ermittelbar",
        "Letztes Signaturupdate": last_signature_update if last_signature_update else "Nicht ermittelbar",
        "Bewertung": evaluate_defender_status(real_time_protection, antivirus_enabled),
    }