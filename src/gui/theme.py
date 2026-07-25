"""Zentrale Designwerte für die Desktopoberfläche."""


class Colors:
    """Helles und dunkles Farbsystem im technischen Neon-Dashboard-Stil."""

    BACKGROUND = ("#F4F6FC", "#171833")
    SIDEBAR = ("#171833", "#111226")
    SIDEBAR_RAISED = ("#222342", "#1A1B38")
    SIDEBAR_TEXT = ("#F7F7FF", "#F7F7FF")

    SURFACE = ("#FFFFFF", "#222342")
    SURFACE_RAISED = ("#FFFFFF", "#292A50")
    SURFACE_SOFT = ("#EFF2FA", "#1D1E3C")

    BORDER = ("#DDE2F1", "#35375F")
    BORDER_STRONG = ("#C9D0E6", "#474A78")

    TEXT = ("#171833", "#F7F7FF")
    MUTED = ("#68708A", "#A8A9C2")
    SUBTLE = ("#8A91A8", "#777A9B")

    PRIMARY = ("#3568FF", "#3568FF")
    PRIMARY_HOVER = ("#2555E8", "#4778FF")
    CYAN = ("#00A7CC", "#00B8D9")
    MINT = ("#00C98F", "#00E6A8")
    VIOLET = ("#7C4DFF", "#9B6CFF")

    NAV_HOVER = ("#E9EDFF", "#242645")
    SUCCESS_SOFT = ("#E7FFF5", "#123B35")
    WARNING_SOFT = ("#FFF5E0", "#3C2A19")
    DANGER_SOFT = ("#FFE9EF", "#3A1828")

    SUCCESS = ("#00A878", "#00D89B")
    WARNING = ("#E99500", "#FFB020")
    DANGER = ("#D93455", "#FF4D6D")


class Spacing:
    XS = 4
    SM = 8
    MD = 12
    LG = 16
    XL = 24
    XXL = 32


class Radius:
    BUTTON = 10
    CARD = 16
    PANEL = 18


class FontSize:
    CAPTION = 11
    BODY = 13
    LABEL = 14
    SECTION = 17
    TITLE = 29
    METRIC = 27


STATUS_COLORS = {
    "OK": "#00D89B",
    "INFO": "#3B82F6",
    "HINWEIS": "#9B6CFF",
    "WARNUNG": "#FFB020",
    "KRITISCH": "#FF4D6D",
    "FEHLER": "#E02D4F",
}
