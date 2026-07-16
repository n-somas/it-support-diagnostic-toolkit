import customtkinter as ctk

from src.gui.detail_window import ResultDetailWindow


STATUS_STYLES = {
    "OK": {
        "color": ("#2E7D32", "#4CAF50"),
        "text": "OK",
    },
    "INFO": {
        "color": ("#1565C0", "#42A5F5"),
        "text": "INFO",
    },
    "HINWEIS": {
        "color": ("#6A1B9A", "#AB47BC"),
        "text": "HINWEIS",
    },
    "WARNUNG": {
        "color": ("#EF6C00", "#FFA726"),
        "text": "WARNUNG",
    },
    "KRITISCH": {
        "color": ("#C62828", "#EF5350"),
        "text": "KRITISCH",
    },
    "FEHLER": {
        "color": ("#8E0000", "#D32F2F"),
        "text": "FEHLER",
    },
}


class ResultCard(ctk.CTkFrame):
    """Stellt das Ergebnis eines Diagnosebereichs dar."""

    def __init__(
        self,
        master,
        title: str,
        result: dict,
    ) -> None:
        super().__init__(
            master,
            corner_radius=10,
            border_width=1,
        )

        self.title = title
        self.result = result
        self.rating = self._get_rating()
        self.status_style = STATUS_STYLES.get(
            self.rating,
            STATUS_STYLES["INFO"],
        )

        self.grid_columnconfigure(1, weight=1)

        self._create_content()

    def _create_content(self) -> None:
        """Erstellt Statusindikator, Überschrift und Ergebnisdetails."""

        status_indicator = ctk.CTkFrame(
            self,
            width=6,
            corner_radius=4,
            fg_color=self.status_style["color"],
        )
        status_indicator.grid(
            row=0,
            column=0,
            rowspan=3,
            pady=8,
            sticky="ns",
        )
        status_indicator.grid_propagate(False)

        header = ctk.CTkFrame(
            self,
            fg_color="transparent",
        )
        header.grid(
            row=0,
            column=1,
            padx=18,
            pady=(14, 8),
            sticky="ew",
        )
        header.grid_columnconfigure(0, weight=1)

        title_label = ctk.CTkLabel(
            header,
            text=self.title,
            anchor="w",
            font=ctk.CTkFont(
                size=16,
                weight="bold",
            ),
        )
        title_label.grid(
            row=0,
            column=0,
            sticky="w",
        )

        rating_label = ctk.CTkLabel(
            header,
            text=self.status_style["text"],
            width=105,
            height=28,
            corner_radius=8,
            fg_color=self.status_style["color"],
            text_color="white",
            font=ctk.CTkFont(
                size=12,
                weight="bold",
            ),
        )
        rating_label.grid(
            row=0,
            column=1,
            padx=(12, 0),
            sticky="e",
        )

        details_label = ctk.CTkLabel(
            self,
            text=self._create_details_text(),
            justify="left",
            anchor="w",
            wraplength=720,
            font=ctk.CTkFont(size=13),
        )
        details_label.grid(
            row=1,
            column=1,
            padx=18,
            pady=(0, 8),
            sticky="ew",
        )

        details_button = ctk.CTkButton(
            self,
            text="Details anzeigen",
            width=145,
            height=32,
            command=self._open_details,
        )
        details_button.grid(
            row=2,
            column=1,
            padx=18,
            pady=(0, 16),
            sticky="e",
        )

    def _open_details(self) -> None:
        """Öffnet ein Fenster mit allen Ergebniswerten."""

        ResultDetailWindow(
            master=self.winfo_toplevel(),
            title=self.title,
            result=self.result,
            status_color=self.status_style["color"],
        )

    def _get_rating(self) -> str:
        """Ermittelt den Status des Diagnoseergebnisses."""

        rating = self.result.get(
            "Bewertung",
            self.result.get("Status", "INFO"),
        )

        return str(rating).upper()

    def _create_details_text(self) -> str:
        """Erstellt eine kompakte Vorschau des Ergebnisses."""

        ignored_keys = {
            "Bewertung",
            "Status",
        }

        details: list[str] = []

        for key, value in self.result.items():
            if key in ignored_keys:
                continue

            if value is None or value == "":
                continue

            formatted_value = self._format_value(value)
            details.append(f"{key}: {formatted_value}")

            if len(details) >= 4:
                break

        if not details:
            return "Keine weiteren Details vorhanden."

        return "\n".join(details)

    @staticmethod
    def _format_value(value) -> str:
        """Formatiert Werte für die kompakte Kartenansicht."""

        if isinstance(value, bool):
            return "Ja" if value else "Nein"

        if isinstance(value, list):
            if not value:
                return "Keine Einträge"

            visible_items = [
                str(item)
                for item in value[:3]
            ]

            formatted_value = ", ".join(visible_items)

            if len(value) > 3:
                formatted_value += f" und {len(value) - 3} weitere"

            return formatted_value

        if isinstance(value, dict):
            if not value:
                return "Keine Einträge"

            entries = [
                f"{key}={item}"
                for key, item in list(value.items())[:3]
            ]

            formatted_value = ", ".join(entries)

            if len(value) > 3:
                formatted_value += f" und {len(value) - 3} weitere"

            return formatted_value

        return str(value)