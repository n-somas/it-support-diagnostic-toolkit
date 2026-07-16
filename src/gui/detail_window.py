import customtkinter as ctk


class ResultDetailWindow(ctk.CTkToplevel):
    """Zeigt alle Werte eines Diagnoseergebnisses an."""

    def __init__(
        self,
        master,
        title: str,
        result: dict,
        status_color,
    ) -> None:
        super().__init__(master)

        self.result_title = title
        self.result = result
        self.status_color = status_color

        self.title(f"Diagnosedetails - {title}")
        self.geometry("760x620")
        self.minsize(620, 480)

        self.transient(master)
        self.grab_set()

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._create_header()
        self._create_details()
        self._create_footer()

        self.after(100, self.focus_force)

    def _create_header(self) -> None:
        """Erstellt Überschrift und Statusanzeige."""

        header = ctk.CTkFrame(
            self,
            corner_radius=0,
        )
        header.grid(
            row=0,
            column=0,
            sticky="ew",
        )
        header.grid_columnconfigure(0, weight=1)

        title_label = ctk.CTkLabel(
            header,
            text=self.result_title,
            anchor="w",
            font=ctk.CTkFont(
                size=22,
                weight="bold",
            ),
        )
        title_label.grid(
            row=0,
            column=0,
            padx=24,
            pady=(20, 8),
            sticky="w",
        )

        rating = self._get_rating()

        status_label = ctk.CTkLabel(
            header,
            text=rating,
            width=110,
            height=30,
            corner_radius=8,
            fg_color=self.status_color,
            text_color="white",
            font=ctk.CTkFont(
                size=13,
                weight="bold",
            ),
        )
        status_label.grid(
            row=1,
            column=0,
            padx=24,
            pady=(0, 20),
            sticky="w",
        )

    def _create_details(self) -> None:
        """Erstellt die scrollbare Detailansicht."""

        details_frame = ctk.CTkScrollableFrame(
            self,
            label_text="Vollständige Ergebnisse",
        )
        details_frame.grid(
            row=1,
            column=0,
            padx=24,
            pady=24,
            sticky="nsew",
        )
        details_frame.grid_columnconfigure(0, weight=1)

        visible_items = [
            (key, value)
            for key, value in self.result.items()
            if key not in {"Bewertung", "Status"}
        ]

        if not visible_items:
            empty_label = ctk.CTkLabel(
                details_frame,
                text="Keine weiteren Details vorhanden.",
            )
            empty_label.grid(
                row=0,
                column=0,
                padx=20,
                pady=30,
            )
            return

        for row_index, (key, value) in enumerate(visible_items):
            detail_card = ctk.CTkFrame(
                details_frame,
                corner_radius=8,
                border_width=1,
            )
            detail_card.grid(
                row=row_index,
                column=0,
                padx=8,
                pady=6,
                sticky="ew",
            )
            detail_card.grid_columnconfigure(0, weight=1)

            key_label = ctk.CTkLabel(
                detail_card,
                text=str(key),
                anchor="w",
                font=ctk.CTkFont(
                    size=14,
                    weight="bold",
                ),
            )
            key_label.grid(
                row=0,
                column=0,
                padx=16,
                pady=(12, 4),
                sticky="w",
            )

            value_label = ctk.CTkLabel(
                detail_card,
                text=self._format_value(value),
                justify="left",
                anchor="w",
                wraplength=640,
                font=ctk.CTkFont(size=13),
            )
            value_label.grid(
                row=1,
                column=0,
                padx=16,
                pady=(0, 12),
                sticky="ew",
            )

    def _create_footer(self) -> None:
        """Erstellt den unteren Bereich des Fensters."""

        close_button = ctk.CTkButton(
            self,
            text="Schließen",
            width=160,
            height=40,
            command=self.destroy,
        )
        close_button.grid(
            row=2,
            column=0,
            padx=24,
            pady=(0, 24),
        )

    def _get_rating(self) -> str:
        """Ermittelt den Status des Ergebnisses."""

        rating = self.result.get(
            "Bewertung",
            self.result.get("Status", "INFO"),
        )

        return str(rating).upper()

    @classmethod
    def _format_value(cls, value) -> str:
        """Formatiert auch verschachtelte Ergebniswerte lesbar."""

        if isinstance(value, bool):
            return "Ja" if value else "Nein"

        if isinstance(value, list):
            if not value:
                return "Keine Einträge"

            return "\n".join(
                f"• {cls._format_value(item)}"
                for item in value
            )

        if isinstance(value, dict):
            if not value:
                return "Keine Einträge"

            return "\n".join(
                f"{key}: {cls._format_value(item)}"
                for key, item in value.items()
            )

        if value is None or value == "":
            return "Keine Angabe"

        return str(value)