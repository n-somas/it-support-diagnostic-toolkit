"""Kompakte Hardware- und Updateübersicht."""

from __future__ import annotations

from typing import Any

import customtkinter as ctk

from src.gui.detail_window import ResultDetailWindow
from src.gui.theme import Colors


STATUS_COLORS = {
    "OK": ("#15803D", "#22C55E"),
    "INFO": ("#1D4ED8", "#3B82F6"),
    "HINWEIS": ("#7E22CE", "#A855F7"),
    "WARNUNG": ("#C2410C", "#F59E0B"),
    "KRITISCH": ("#B91C1C", "#EF4444"),
    "FEHLER": ("#991B1B", "#DC2626"),
}


class HardwarePage(ctk.CTkFrame):
    """Zeigt Hardware und Updatebedarf ohne lange Listen."""

    def __init__(self, master) -> None:
        super().__init__(master, fg_color="transparent")

        self.hardware_result: dict[str, Any] = {}
        self.update_result: dict[str, Any] = {}
        self.labels: dict[str, ctk.CTkLabel] = {}

        self.grid_columnconfigure((0, 1), weight=1, uniform="hardware")
        for row in range(1, 5):
            self.grid_rowconfigure(row, weight=1)

        self._create_header()
        self._create_cards()
        self.reset()

    def _create_header(self) -> None:
        frame = ctk.CTkFrame(
            self,
            corner_radius=14,
            border_width=1,
            border_color=Colors.BORDER,
            fg_color=Colors.SURFACE,
        )
        frame.grid(
            row=0,
            column=0,
            columnspan=2,
            pady=(0, 10),
            sticky="ew",
        )
        frame.grid_columnconfigure(0, weight=1)

        self.system_label = ctk.CTkLabel(
            frame,
            text="Noch keine Hardwaredaten",
            anchor="w",
            text_color=Colors.TEXT,
            font=ctk.CTkFont(size=18, weight="bold"),
        )
        self.system_label.grid(
            row=0,
            column=0,
            padx=18,
            pady=(14, 2),
            sticky="w",
        )

        self.summary_label = ctk.CTkLabel(
            frame,
            text="Führe eine Diagnose durch.",
            anchor="w",
            text_color=Colors.MUTED,
            font=ctk.CTkFont(size=12),
        )
        self.summary_label.grid(
            row=1,
            column=0,
            padx=18,
            pady=(0, 14),
            sticky="w",
        )

        self.hardware_button = ctk.CTkButton(
            frame,
            text="Hardwaredetails",
            width=140,
            height=34,
            state="disabled",
            command=self._open_hardware,
        )
        self.hardware_button.grid(
            row=0,
            column=1,
            rowspan=2,
            padx=(8, 8),
            pady=12,
        )

        self.update_button = ctk.CTkButton(
            frame,
            text="Updatedetails",
            width=130,
            height=34,
            state="disabled",
            command=self._open_updates,
        )
        self.update_button.grid(
            row=0,
            column=2,
            rowspan=2,
            padx=(0, 18),
            pady=12,
        )

    def _create_cards(self) -> None:
        items = (
            ("cpu", "Prozessor", 1, 0),
            ("ram", "Arbeitsspeicher", 1, 1),
            ("gpu", "Grafikkarte", 2, 0),
            ("board", "Mainboard und BIOS", 2, 1),
            ("storage", "Laufwerke", 3, 0),
            ("network", "Netzwerkhardware", 3, 1),
            ("devices", "Gerätestatus", 4, 0),
            ("updates", "Update-Status", 4, 1),
        )

        for key, title, row, column in items:
            frame = ctk.CTkFrame(
                self,
                corner_radius=12,
                border_width=1,
                border_color=Colors.BORDER,
                fg_color=Colors.SURFACE,
            )
            frame.grid(
                row=row,
                column=column,
                padx=(0, 5) if column == 0 else (5, 0),
                pady=5,
                sticky="nsew",
            )
            frame.grid_columnconfigure(0, weight=1)

            ctk.CTkLabel(
                frame,
                text=title,
                anchor="w",
                text_color=Colors.TEXT,
                font=ctk.CTkFont(size=14, weight="bold"),
            ).grid(
                row=0,
                column=0,
                padx=14,
                pady=(11, 3),
                sticky="w",
            )

            label = ctk.CTkLabel(
                frame,
                text="Noch nicht ermittelt",
                anchor="nw",
                justify="left",
                wraplength=410,
                text_color=Colors.MUTED,
                font=ctk.CTkFont(size=12),
            )
            label.grid(
                row=1,
                column=0,
                padx=14,
                pady=(0, 11),
                sticky="nsew",
            )
            self.labels[key] = label

    def reset(self) -> None:
        self.hardware_result = {}
        self.update_result = {}
        self.system_label.configure(text="Noch keine Hardwaredaten")
        self.summary_label.configure(text="Führe eine Diagnose durch.")
        self.hardware_button.configure(state="disabled")
        self.update_button.configure(state="disabled")

        for label in self.labels.values():
            label.configure(
                text="Noch nicht ermittelt",
                text_color=Colors.MUTED,
            )

    def update_from_results(
        self,
        results: list[tuple[str, dict]],
    ) -> None:
        self.hardware_result = next(
            (
                result
                for title, result in results
                if title == "Hardwareinventar"
            ),
            {},
        )
        self.update_result = next(
            (
                result
                for title, result in results
                if title == "Windows Update Prüfung"
            ),
            {},
        )

        if not self.hardware_result:
            self.reset()
            self.summary_label.configure(
                text="Hardwareinventar konnte nicht geladen werden."
            )
            return

        self.system_label.configure(
            text=str(self.hardware_result.get("System", "Windows-PC"))
        )
        self.summary_label.configure(
            text=(
                f"Hardwarestatus: "
                f"{self.hardware_result.get('Hinweis', 'Nicht ermittelt')}"
                f"    |    Updates: "
                f"{self.update_result.get('Update erforderlich', 'Nicht ermittelt')}"
            )
        )
        self.hardware_button.configure(state="normal")
        self.update_button.configure(
            state="normal" if self.update_result else "disabled"
        )

        self.labels["cpu"].configure(
            text=(
                f"{self.hardware_result.get('Prozessor', 'Nicht ermittelbar')}\n"
                f"{self.hardware_result.get('CPU-Details', '')}"
            )
        )
        self.labels["ram"].configure(
            text=(
                f"Gesamt: "
                f"{self.hardware_result.get('Arbeitsspeicher', 'Nicht ermittelbar')}\n"
                f"{self._list_text(self.hardware_result.get('RAM-Module'))}"
            )
        )
        self.labels["gpu"].configure(
            text=self._list_text(
                self.hardware_result.get("Grafikkarten")
            )
        )
        self.labels["board"].configure(
            text=(
                f"{self.hardware_result.get('Mainboard', 'Nicht ermittelbar')}\n"
                f"BIOS {self.hardware_result.get('BIOS-Version', 'unbekannt')} "
                f"vom {self.hardware_result.get('BIOS-Datum', 'unbekannt')}"
            )
        )
        self.labels["storage"].configure(
            text=self._list_text(
                self.hardware_result.get("Laufwerke")
            )
        )
        self.labels["network"].configure(
            text=self._list_text(
                self.hardware_result.get("Netzwerkadapter")
            )
        )
        self.labels["devices"].configure(
            text=(
                f"{self.hardware_result.get('Hinweis', 'Nicht ermittelbar')}\n"
                f"{self._list_text(
                    self.hardware_result.get('Geräte mit Fehlerstatus')
                )}"
            )
        )

        update_rating = str(
            self.update_result.get("Bewertung", "INFO")
        ).upper()
        update_color = (
            STATUS_COLORS.get(update_rating, Colors.MUTED)
            if update_rating in {"WARNUNG", "KRITISCH", "FEHLER"}
            else Colors.MUTED
        )
        self.labels["updates"].configure(
            text=(
                f"{self.update_result.get('Update erforderlich', 'Nicht ermittelbar')}\n"
                f"Windows-Updates: "
                f"{self.update_result.get('Verfügbare Windows-Updates', '?')}\n"
                f"Treiberupdates: "
                f"{self.update_result.get('Verfügbare Treiberupdates', '?')}\n"
                f"Neustart: "
                f"{self.update_result.get('Neustart erforderlich', '?')}"
            ),
            text_color=update_color,
        )

    def _open_hardware(self) -> None:
        if not self.hardware_result:
            return

        rating = str(
            self.hardware_result.get("Bewertung", "INFO")
        ).upper()
        ResultDetailWindow(
            master=self.winfo_toplevel(),
            title="Hardwareinventar",
            result=self.hardware_result,
            status_color=STATUS_COLORS.get(
                rating,
                STATUS_COLORS["INFO"],
            ),
        )

    def _open_updates(self) -> None:
        if not self.update_result:
            return

        rating = str(
            self.update_result.get("Bewertung", "INFO")
        ).upper()
        ResultDetailWindow(
            master=self.winfo_toplevel(),
            title="Windows Update Prüfung",
            result=self.update_result,
            status_color=STATUS_COLORS.get(
                rating,
                STATUS_COLORS["INFO"],
            ),
        )

    @staticmethod
    def _list_text(value: Any, limit: int = 2) -> str:
        if not isinstance(value, list) or not value:
            return str(value or "Nicht ermittelbar")

        text = "\n".join(str(item) for item in value[:limit])
        if len(value) > limit:
            text += f"\n+ {len(value) - limit} weitere"
        return text
