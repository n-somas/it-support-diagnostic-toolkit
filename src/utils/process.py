import subprocess


def get_hidden_process_options() -> dict:
    """Liefert Windows-Optionen für unsichtbare Hintergrundprozesse."""

    startup_info = subprocess.STARTUPINFO()
    startup_info.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startup_info.wShowWindow = subprocess.SW_HIDE

    return {
        "startupinfo": startup_info,
        "creationflags": subprocess.CREATE_NO_WINDOW,
    }