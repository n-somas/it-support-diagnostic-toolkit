import subprocess
from src.utils.hidden_process import get_hidden_process_options


def run_powershell_command(command):
    """
    Führt einen PowerShell-Befehl aus und gibt stdout, stderr und returncode zurück.
    Dadurch können auch Fehler wie fehlende Administratorrechte erkannt werden.
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

    return {
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
        "returncode": result.returncode,
    }


def get_bitlocker_volume_info():
    """
    Liest BitLocker-Informationen für Laufwerk C: aus.
    Die Ausgabe wird als CSV erzeugt, damit Python sie einfach verarbeiten kann.
    """

    command = (
        "$volume = Get-BitLockerVolume -MountPoint 'C:' -ErrorAction Stop; "
        "[PSCustomObject]@{"
        "MountPoint=$volume.MountPoint;"
        "VolumeStatus=$volume.VolumeStatus;"
        "ProtectionStatus=$volume.ProtectionStatus;"
        "EncryptionPercentage=$volume.EncryptionPercentage;"
        "LockStatus=$volume.LockStatus"
        "} | ConvertTo-Csv -NoTypeInformation"
    )

    result = run_powershell_command(command)
    output = result["stdout"]
    error_output = result["stderr"]

    if "Zugriff verweigert" in error_output or "Access is denied" in error_output:
        return {
            "error": "ACCESS_DENIED"
        }

    if not output:
        return None

    lines = output.splitlines()

    if len(lines) < 2:
        return None

    values = [part.strip().strip('"') for part in lines[1].split(",")]

    if len(values) != 5:
        return None

    return {
        "mount_point": values[0],
        "volume_status": values[1],
        "protection_status": values[2],
        "encryption_percentage": values[3],
        "lock_status": values[4],
    }


def translate_protection_status(status):
    """
    Übersetzt den BitLocker-Schutzstatus in verständliche deutsche Werte.
    """

    if status == "On":
        return "Aktiv"

    if status == "Off":
        return "Inaktiv"

    return status if status else "Nicht ermittelbar"


def translate_volume_status(status):
    """
    Übersetzt den BitLocker-Volume-Status grob in verständliche Werte.
    """

    translations = {
        "FullyEncrypted": "Vollständig verschlüsselt",
        "FullyDecrypted": "Nicht verschlüsselt",
        "EncryptionInProgress": "Verschlüsselung läuft",
        "DecryptionInProgress": "Entschlüsselung läuft",
        "UsedSpaceOnlyEncrypted": "Benutzter Speicher verschlüsselt",
    }

    return translations.get(status, status if status else "Nicht ermittelbar")


def evaluate_bitlocker_status(volume_status, protection_status):
    """
    Bewertet den BitLocker-Status.
    OK ist nur, wenn Schutz aktiv ist und das Laufwerk verschlüsselt ist.
    """

    encrypted_states = ["FullyEncrypted", "UsedSpaceOnlyEncrypted"]

    if protection_status == "On" and volume_status in encrypted_states:
        return "OK"

    return "WARNUNG"


def get_bitlocker_info():
    """
    Prüft den BitLocker-Status von Laufwerk C:.
    """

    volume_info = get_bitlocker_volume_info()

    if volume_info == {"error": "ACCESS_DENIED"}:
        return {
            "Laufwerk": "C:",
            "Verschlüsselungsstatus": "Nicht ermittelbar",
            "Schutzstatus": "Nicht ermittelbar",
            "Verschlüsselung in Prozent": "Nicht ermittelbar",
            "Sperrstatus": "Nicht ermittelbar",
            "Bewertung": "HINWEIS",
            "Hinweis": "BitLocker-Informationen konnten wegen fehlender Administratorrechte nicht ausgelesen werden.",
        }

    if volume_info is None:
        return {
            "Laufwerk": "C:",
            "Verschlüsselungsstatus": "Nicht ermittelbar",
            "Schutzstatus": "Nicht ermittelbar",
            "Verschlüsselung in Prozent": "Nicht ermittelbar",
            "Sperrstatus": "Nicht ermittelbar",
            "Bewertung": "HINWEIS",
            "Hinweis": "BitLocker-Informationen konnten nicht ausgelesen werden. Das kann an der Windows-Edition, fehlender BitLocker-Konfiguration oder fehlenden Berechtigungen liegen.",
        }

    volume_status = volume_info["volume_status"]
    protection_status = volume_info["protection_status"]

    return {
        "Laufwerk": volume_info["mount_point"],
        "Verschlüsselungsstatus": translate_volume_status(volume_status),
        "Schutzstatus": translate_protection_status(protection_status),
        "Verschlüsselung in Prozent": f"{volume_info['encryption_percentage']} %",
        "Sperrstatus": volume_info["lock_status"],
        "Bewertung": evaluate_bitlocker_status(volume_status, protection_status),
        "Hinweis": "BitLocker schützt Daten bei Geräteverlust oder Diebstahl, wenn der Schutz aktiv ist.",
    }