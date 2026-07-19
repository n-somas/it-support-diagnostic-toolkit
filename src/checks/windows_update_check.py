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


def get_last_installed_update():
    """
    Ermittelt das zuletzt installierte Windows Update.
    Dafür wird Get-HotFix verwendet.
    """

    command = (
        "Get-HotFix | "
        "Sort-Object InstalledOn -Descending | "
        "Select-Object -First 1 -Property HotFixID,InstalledOn | "
        "Format-List"
    )

    output = run_powershell_command(command)

    if output:
        return output

    return "Nicht ermittelbar"


def get_windows_update_service_status():
    """
    Prüft den Status des Windows Update Dienstes.
    Der Dienst heißt unter Windows: wuauserv
    """

    command = "(Get-Service -Name wuauserv).Status"

    status = run_powershell_command(command)

    if status == "Running":
        return "Aktiv"

    if status == "Stopped":
        return "Gestoppt"

    if status:
        return status

    return "Nicht ermittelbar"


def evaluate_windows_update_status(service_status, last_update):
    """
    Bewertet den Windows Update Status.

    Wichtig:
    Der Windows Update Dienst muss nicht dauerhaft laufen.
    Entscheidend ist hier vor allem, ob ein installiertes Update ermittelt werden kann.
    """

    if last_update != "Nicht ermittelbar":
        return "OK"

    if service_status == "Nicht ermittelbar":
        return "WARNUNG"

    return "HINWEIS"


def get_windows_update_note(service_status):
    """
    Gibt einen kurzen Hinweis zum Windows Update Dienst zurück.
    """

    if service_status == "Aktiv":
        return "Windows Update Dienst läuft aktuell."

    if service_status == "Gestoppt":
        return "Windows Update Dienst läuft aktuell nicht dauerhaft. Das kann normal sein, da der Dienst bei Bedarf gestartet wird."

    return "Windows Update Dienst konnte nicht eindeutig bewertet werden."


def get_windows_update_info():
    """
    Prüft grundlegende Informationen zu Windows Update.
    Dieser Check ist typisch für IT-Support und Systemwartung.
    """

    service_status = get_windows_update_service_status()
    last_update = get_last_installed_update()

    return {
        "Windows Update Dienst": service_status,
        "Letztes installiertes Update": last_update,
        "Hinweis": get_windows_update_note(service_status),
        "Bewertung": evaluate_windows_update_status(service_status, last_update),
    }