import subprocess


def get_hidden_process_options() -> dict:
    """Startet externe Windows-Prozesse ohne sichtbares Konsolenfenster."""

    startup_info = subprocess.STARTUPINFO()
    startup_info.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startup_info.wShowWindow = subprocess.SW_HIDE

    return {
        "startupinfo": startup_info,
        "creationflags": subprocess.CREATE_NO_WINDOW,
    }
