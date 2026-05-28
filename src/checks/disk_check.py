import shutil


def bytes_to_gb(size_in_bytes):
    """
    Wandelt Bytes in Gigabyte um.
    Der Wert wird auf zwei Nachkommastellen gerundet.
    """
    gb_value = size_in_bytes / (1024 ** 3)
    return round(gb_value, 2)


def evaluate_disk_status(free_percent):
    """
    Bewertet den freien Speicherplatz.

    OK:
    Mehr als 20 Prozent frei.

    WARNUNG:
    Zwischen 10 und 20 Prozent frei.

    KRITISCH:
    Weniger als 10 Prozent frei.
    """

    if free_percent < 10:
        return "KRITISCH"
    elif free_percent < 20:
        return "WARNUNG"
    else:
        return "OK"


def get_disk_info():
    """
    Prüft den Speicherplatz von Laufwerk C:
    und gibt eine einfache Support-Bewertung zurück.
    """

    total, used, free = shutil.disk_usage("C:\\")

    total_gb = bytes_to_gb(total)
    used_gb = bytes_to_gb(used)
    free_gb = bytes_to_gb(free)

    free_percent = round((free / total) * 100, 2)

    status = evaluate_disk_status(free_percent)

    return {
        "Laufwerk": "C:",
        "Gesamtspeicher": f"{total_gb} GB",
        "Belegter Speicher": f"{used_gb} GB",
        "Freier Speicher": f"{free_gb} GB",
        "Freier Speicher in Prozent": f"{free_percent} %",
        "Bewertung": status,
    }