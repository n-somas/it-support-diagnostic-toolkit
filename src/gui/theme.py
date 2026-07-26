"""Zentrale Designwerte für eine zeitlose Enterprise-Oberfläche."""


class Colors:
    """Neutrales Farbsystem für professionelle Windows-Software."""

    BACKGROUND = ("#F5F7FA", "#101722")
    SIDEBAR = ("#0C1320", "#0C1320")
    SIDEBAR_RAISED = ("#121C2A", "#121C2A")
    SIDEBAR_TEXT = ("#E7ECF3", "#E7ECF3")

    SURFACE = ("#FFFFFF", "#151E2B")
    SURFACE_RAISED = ("#FFFFFF", "#192433")
    SURFACE_SOFT = ("#F3F5F8", "#202C3C")

    BORDER = ("#D8DEE8", "#2D3A4D")
    BORDER_STRONG = ("#C5CEDA", "#405069")

    TEXT = ("#182230", "#F2F4F7")
    MUTED = ("#667085", "#A3AFBF")
    SUBTLE = ("#8A94A3", "#728096")

    PRIMARY = ("#2563EB", "#4F86F7")
    PRIMARY_HOVER = ("#1D4ED8", "#6797FA")

    CYAN = PRIMARY
    MINT = PRIMARY
    VIOLET = ("#64748B", "#8290A6")

    NAV_HOVER = ("#182436", "#182436")
    SUCCESS_SOFT = ("#EAF5F1", "#17342F")
    WARNING_SOFT = ("#FFF4E5", "#3B2E20")
    DANGER_SOFT = ("#FDECEF", "#3B222A")

    SUCCESS = ("#358C7F", "#55B5A5")
    WARNING = ("#B97824", "#D5953F")
    DANGER = ("#C4485D", "#DD5A6E")


class Fonts:
    PRIMARY = "Segoe UI Variable"
    FALLBACK = "Segoe UI"


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
    "OK": "#55B5A5",
    "INFO": "#5B8DEF",
    "HINWEIS": "#8292AE",
    "WARNUNG": "#D5953F",
    "KRITISCH": "#DD5A6E",
    "FEHLER": "#C94359",
}
