import customtkinter as ctk


class ResultCard(ctk.CTkFrame):
    """Stellt das Ergebnis eines Diagnosebereichs dar."""

    def __init__(
        self,
        master,
        title: str,
        result: dict,
    ) -> None:
        super().__init__(master)

        self.title = title
        self.result = result

        self.grid_columnconfigure(0, weight=1)

        self._create_content()

    def _create_content(self) -> None:
        """Erstellt Überschrift, Status und Ergebnisdetails."""

        rating = str(
            self.result.get(
                "Bewertung",
                self.result.get("Status", "INFO"),
            )
        ).upper()

        header = ctk.CTkFrame(
            self,
            fg_color="transparent",
        )
        header.grid(
            row=0,
            column=0,
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
            text=rating,
            width=100,
            font=ctk.CTkFont(
                size=13,
                weight="bold",
            ),
        )
        rating_label.grid(
            row=0,
            column=1,
            padx=(12, 0),
            sticky="e",
        )

        details_text = self._create_details_text()

        details_label = ctk.CTkLabel(
            self,
            text=details_text,
            justify="left",
            anchor="w",
            wraplength=680,
        )
        details_label.grid(
            row=1,
            column=0,
            padx=18,
            pady=(0, 14),
            sticky="ew",
        )

    def _create_details_text(self) -> str:
        """Erstellt eine kompakte Detailansicht des Ergebnisses."""

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
        """Formatiert Listen, Dictionaries und einfache Werte."""

        if isinstance(value, list):
            if not value:
                return "Keine Einträge"

            return ", ".join(str(item) for item in value[:5])

        if isinstance(value, dict):
            if not value:
                return "Keine Einträge"

            entries = [
                f"{key}={item}"
                for key, item in list(value.items())[:5]
            ]
            return ", ".join(entries)

        return str(value)