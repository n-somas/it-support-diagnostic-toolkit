"""Kompakte Ergebniszeilen im modernen Dashboard-Stil."""

from __future__ import annotations

import customtkinter as ctk

from src.gui.detail_window import ResultDetailWindow
from src.gui.theme import Colors, STATUS_COLORS


STATUS_LABELS = {
    "OK": "OK",
    "INFO": "INFO",
    "HINWEIS": "HINWEIS",
    "WARNUNG": "WARNUNG",
    "KRITISCH": "KRITISCH",
    "FEHLER": "FEHLER",
}


class ResultCard(ctk.CTkFrame):
    """Zeigt ein Diagnoseergebnis als kompakte, anklickbare Karte."""

    def __init__(self, master, title: str, result: dict) -> None:
        super().__init__(
            master,
            corner_radius=16,
            border_width=1,
            border_color=Colors.BORDER,
            fg_color=Colors.SURFACE_RAISED,
        )
        self.title = title
        self.result = result
        self.rating = self._get_rating()
        self.status_color = STATUS_COLORS.get(
            self.rating,
            STATUS_COLORS["INFO"],
        )
        self.grid_columnconfigure(1, weight=1)
        self._create_content()
        self._bind_click(self)

    def _create_content(self) -> None:
        indicator = ctk.CTkFrame(
            self,
            width=5,
            corner_radius=4,
            fg_color=self.status_color,
        )
        indicator.grid(
            row=0,
            column=0,
            rowspan=3,
            pady=10,
            sticky="ns",
        )
        indicator.grid_propagate(False)

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(
            row=0,
            column=1,
            padx=(18, 16),
            pady=(15, 5),
            sticky="ew",
        )
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header,
            text=self.title,
            anchor="w",
            text_color=Colors.TEXT,
            font=ctk.CTkFont(size=16, weight="bold"),
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(
            header,
            text=STATUS_LABELS.get(self.rating, "INFO"),
            width=92,
            height=25,
            corner_radius=8,
            fg_color=self.status_color,
            text_color="#FFFFFF",
            font=ctk.CTkFont(size=10, weight="bold"),
        ).grid(row=0, column=1, padx=(12, 0), sticky="e")

        ctk.CTkLabel(
            self,
            text=self._create_details_text(),
            justify="left",
            anchor="w",
            wraplength=820,
            text_color=Colors.MUTED,
            font=ctk.CTkFont(size=12),
        ).grid(
            row=1,
            column=1,
            padx=(18, 16),
            pady=(0, 8),
            sticky="ew",
        )

        ctk.CTkButton(
            self,
            text="Details öffnen  ›",
            width=122,
            height=30,
            corner_radius=9,
            fg_color=Colors.SURFACE_SOFT,
            hover_color=Colors.NAV_HOVER,
            border_width=1,
            border_color=Colors.BORDER,
            text_color=Colors.TEXT,
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self._open_details,
        ).grid(
            row=2,
            column=1,
            padx=(18, 16),
            pady=(0, 14),
            sticky="e",
        )

    def _bind_click(self, widget) -> None:
        if not isinstance(widget, ctk.CTkButton):
            widget.bind("<Button-1>", lambda _event: self._open_details())
            try:
                widget.configure(cursor="hand2")
            except (TypeError, ValueError):
                pass
        for child in widget.winfo_children():
            self._bind_click(child)

    def _open_details(self) -> None:
        ResultDetailWindow(
            master=self.winfo_toplevel(),
            title=self.title,
            result=self.result,
            status_color=self.status_color,
        )

    def _get_rating(self) -> str:
        rating = self.result.get(
            "Bewertung",
            self.result.get("Status", "INFO"),
        )
        normalized = str(rating).upper()
        return normalized if normalized in STATUS_LABELS else "INFO"

    def _create_details_text(self) -> str:
        ignored_keys = {"Bewertung", "Status"}
        preferred_keys = (
            "Hinweis",
            "Empfehlung",
            "Zusammenfassung",
            "Ergebnis",
            "Details",
        )
        details: list[str] = []

        for key in preferred_keys:
            value = self.result.get(key)
            if value not in (None, ""):
                details.append(f"{key}: {self._format_value(value)}")
                break

        for key, value in self.result.items():
            if key in ignored_keys or key in preferred_keys:
                continue
            if value in (None, ""):
                continue
            details.append(f"{key}: {self._format_value(value)}")
            if len(details) >= 3:
                break

        return "\n".join(details) if details else "Keine weiteren Details vorhanden."

    @staticmethod
    def _format_value(value) -> str:
        if isinstance(value, bool):
            return "Ja" if value else "Nein"
        if isinstance(value, list):
            if not value:
                return "Keine Einträge"
            text = ", ".join(str(item) for item in value[:2])
            return text + (f" und {len(value) - 2} weitere" if len(value) > 2 else "")
        if isinstance(value, dict):
            if not value:
                return "Keine Einträge"
            text = ", ".join(
                f"{key}={item}" for key, item in list(value.items())[:2]
            )
            return text + (f" und {len(value) - 2} weitere" if len(value) > 2 else "")
        return str(value)
