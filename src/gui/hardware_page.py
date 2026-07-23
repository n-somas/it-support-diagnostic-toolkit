"""Moderne Hardware- und Updateübersicht."""

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

STATUS_LABELS = {
    "OK": "OK",
    "INFO": "Information",
    "HINWEIS": "Hinweis",
    "WARNUNG": "Warnung",
    "KRITISCH": "Kritisch",
    "FEHLER": "Fehler",
}


class HardwarePage(ctk.CTkFrame):
    """Zeigt die wichtigsten Hardwaredaten in einer kompakten Ansicht."""

    def __init__(self, master) -> None:
        super().__init__(master, fg_color="transparent")

        self.hardware_result: dict[str, Any] = {}
        self.update_result: dict[str, Any] = {}

        self.metric_values: dict[str, ctk.CTkLabel] = {}
        self.metric_details: dict[str, ctk.CTkLabel] = {}
        self.detail_labels: dict[str, ctk.CTkLabel] = {}
        self.detail_panels: dict[str, ctk.CTkFrame] = {}

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self._create_system_header()
        self._create_metric_row()
        self._create_detail_tabs()
        self.reset()

    def _create_system_header(self) -> None:
        self.system_header = ctk.CTkFrame(
            self,
            height=92,
            corner_radius=14,
            border_width=1,
            border_color=Colors.BORDER,
            fg_color=Colors.SURFACE,
        )
        self.system_header.grid(
            row=0,
            column=0,
            pady=(0, 12),
            sticky="ew",
        )
        self.system_header.grid_propagate(False)
        self.system_header.grid_columnconfigure(0, weight=1)

        self.system_label = ctk.CTkLabel(
            self.system_header,
            text="Noch keine Hardwaredaten",
            anchor="w",
            text_color=Colors.TEXT,
            font=ctk.CTkFont(size=20, weight="bold"),
        )
        self.system_label.grid(
            row=0,
            column=0,
            padx=18,
            pady=(15, 2),
            sticky="w",
        )

        self.system_subtitle = ctk.CTkLabel(
            self.system_header,
            text="Führe eine Diagnose durch.",
            anchor="w",
            text_color=Colors.MUTED,
            font=ctk.CTkFont(size=12),
        )
        self.system_subtitle.grid(
            row=1,
            column=0,
            padx=18,
            pady=(0, 14),
            sticky="w",
        )

        self.hardware_badge = self._create_status_badge(
            self.system_header,
            "Hardware nicht geprüft",
        )
        self.hardware_badge.grid(
            row=0,
            column=1,
            rowspan=2,
            padx=(8, 6),
            pady=22,
        )

        self.update_badge = self._create_status_badge(
            self.system_header,
            "Updates nicht geprüft",
        )
        self.update_badge.grid(
            row=0,
            column=2,
            rowspan=2,
            padx=6,
            pady=22,
        )

        self.hardware_button = ctk.CTkButton(
            self.system_header,
            text="Alle Hardwaredetails",
            width=150,
            height=34,
            state="disabled",
            command=self._open_hardware,
        )
        self.hardware_button.grid(
            row=0,
            column=3,
            rowspan=2,
            padx=(8, 16),
            pady=22,
        )

    @staticmethod
    def _create_status_badge(
        master,
        text: str,
    ) -> ctk.CTkLabel:
        return ctk.CTkLabel(
            master,
            text=text,
            height=30,
            corner_radius=8,
            fg_color=("gray88", "gray25"),
            text_color=Colors.MUTED,
            font=ctk.CTkFont(size=11, weight="bold"),
        )

    def _create_metric_row(self) -> None:
        frame = ctk.CTkFrame(
            self,
            fg_color="transparent",
        )
        frame.grid(
            row=1,
            column=0,
            pady=(0, 12),
            sticky="ew",
        )

        metrics = (
            ("cpu", "PROZESSOR"),
            ("ram", "ARBEITSSPEICHER"),
            ("gpu", "GRAFIK"),
            ("updates", "UPDATE-STATUS"),
        )

        for column, (key, title) in enumerate(metrics):
            frame.grid_columnconfigure(
                column,
                weight=1,
                uniform="hardware_metrics",
            )

            card = ctk.CTkFrame(
                frame,
                height=108,
                corner_radius=12,
                border_width=1,
                border_color=Colors.BORDER,
                fg_color=Colors.SURFACE,
            )
            card.grid(
                row=0,
                column=column,
                padx=(
                    (0, 5)
                    if column == 0
                    else (5, 5)
                    if column < len(metrics) - 1
                    else (5, 0)
                ),
                sticky="ew",
            )
            card.grid_propagate(False)
            card.grid_columnconfigure(0, weight=1)

            ctk.CTkLabel(
                card,
                text=title,
                anchor="w",
                text_color=Colors.MUTED,
                font=ctk.CTkFont(size=10, weight="bold"),
            ).grid(
                row=0,
                column=0,
                padx=14,
                pady=(12, 3),
                sticky="w",
            )

            value_label = ctk.CTkLabel(
                card,
                text="Nicht ermittelt",
                anchor="w",
                justify="left",
                wraplength=225,
                text_color=Colors.TEXT,
                font=ctk.CTkFont(size=15, weight="bold"),
            )
            value_label.grid(
                row=1,
                column=0,
                padx=14,
                sticky="ew",
            )

            detail_label = ctk.CTkLabel(
                card,
                text="",
                anchor="w",
                justify="left",
                wraplength=225,
                text_color=Colors.MUTED,
                font=ctk.CTkFont(size=11),
            )
            detail_label.grid(
                row=2,
                column=0,
                padx=14,
                pady=(2, 11),
                sticky="ew",
            )

            self.metric_values[key] = value_label
            self.metric_details[key] = detail_label

    def _create_detail_tabs(self) -> None:
        self.tabview = ctk.CTkTabview(
            self,
            corner_radius=12,
            border_width=1,
            border_color=Colors.BORDER,
            fg_color=Colors.SURFACE,
            segmented_button_fg_color=("gray88", "gray23"),
            segmented_button_selected_color=("#2563EB", "#2563EB"),
            segmented_button_selected_hover_color=("#1D4ED8", "#1D4ED8"),
        )
        self.tabview.grid(
            row=2,
            column=0,
            sticky="nsew",
        )

        components_tab = self.tabview.add("Komponenten")
        connectivity_tab = self.tabview.add("Speicher & Netzwerk")
        maintenance_tab = self.tabview.add("Wartung")

        self._configure_tab(components_tab)
        self._configure_tab(connectivity_tab)
        self._configure_tab(maintenance_tab)

        self._create_detail_panel(
            components_tab,
            key="board",
            title="Mainboard und BIOS",
            row=0,
            column=0,
        )
        self._create_detail_panel(
            components_tab,
            key="memory",
            title="RAM-Module",
            row=0,
            column=1,
        )
        self._create_detail_panel(
            components_tab,
            key="graphics",
            title="Grafikkarten und Treiber",
            row=1,
            column=0,
            columnspan=2,
        )

        self._create_detail_panel(
            connectivity_tab,
            key="storage",
            title="Laufwerke",
            row=0,
            column=0,
        )
        self._create_detail_panel(
            connectivity_tab,
            key="network",
            title="Aktive Netzwerkadapter",
            row=0,
            column=1,
        )

        self._create_detail_panel(
            maintenance_tab,
            key="devices",
            title="Gerätestatus",
            row=0,
            column=0,
        )
        self._create_detail_panel(
            maintenance_tab,
            key="update_details",
            title="Windows- und Treiberupdates",
            row=0,
            column=1,
            button_text="Vollständige Updatedetails",
            button_command=self._open_updates,
        )

    @staticmethod
    def _configure_tab(tab) -> None:
        tab.grid_columnconfigure((0, 1), weight=1, uniform="detail")
        tab.grid_rowconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)

    def _create_detail_panel(
        self,
        master,
        key: str,
        title: str,
        row: int,
        column: int,
        columnspan: int = 1,
        button_text: str | None = None,
        button_command=None,
    ) -> None:
        panel = ctk.CTkFrame(
            master,
            corner_radius=10,
            border_width=1,
            border_color=Colors.BORDER,
            fg_color=("gray96", "gray17"),
        )
        panel.grid(
            row=row,
            column=column,
            columnspan=columnspan,
            padx=6,
            pady=6,
            sticky="nsew",
        )
        panel.grid_columnconfigure(0, weight=1)
        panel.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            panel,
            text=title,
            anchor="w",
            text_color=Colors.TEXT,
            font=ctk.CTkFont(size=13, weight="bold"),
        ).grid(
            row=0,
            column=0,
            padx=14,
            pady=(12, 4),
            sticky="w",
        )

        label = ctk.CTkLabel(
            panel,
            text="Noch nicht ermittelt",
            anchor="nw",
            justify="left",
            wraplength=470 if columnspan == 1 else 960,
            text_color=Colors.MUTED,
            font=ctk.CTkFont(size=12),
        )
        label.grid(
            row=1,
            column=0,
            padx=14,
            pady=(0, 12 if not button_text else 4),
            sticky="nsew",
        )

        if button_text and button_command:
            ctk.CTkButton(
                panel,
                text=button_text,
                width=180,
                height=30,
                command=button_command,
            ).grid(
                row=2,
                column=0,
                padx=14,
                pady=(0, 12),
                sticky="e",
            )

        self.detail_panels[key] = panel
        self.detail_labels[key] = label

    def reset(self) -> None:
        self.hardware_result = {}
        self.update_result = {}

        self.system_label.configure(text="Noch keine Hardwaredaten")
        self.system_subtitle.configure(text="Führe eine Diagnose durch.")
        self.hardware_button.configure(state="disabled")

        self._set_badge(
            self.hardware_badge,
            text="Hardware nicht geprüft",
            status="INFO",
            muted=True,
        )
        self._set_badge(
            self.update_badge,
            text="Updates nicht geprüft",
            status="INFO",
            muted=True,
        )

        for key in self.metric_values:
            self.metric_values[key].configure(
                text="Nicht ermittelt",
                text_color=Colors.TEXT,
            )
            self.metric_details[key].configure(text="")

        for label in self.detail_labels.values():
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
            self.system_subtitle.configure(
                text="Hardwareinventar konnte nicht geladen werden."
            )
            return

        hardware_status = str(
            self.hardware_result.get("Bewertung", "INFO")
        ).upper()
        update_status = str(
            self.update_result.get("Bewertung", "INFO")
        ).upper()

        self.system_label.configure(
            text=str(
                self.hardware_result.get(
                    "System",
                    "Windows-PC",
                )
            )
        )
        self.system_subtitle.configure(
            text=(
                f"{self.hardware_result.get('Systemtyp', 'Systemtyp unbekannt')}"
                f"    |    BIOS vom "
                f"{self.hardware_result.get('BIOS-Datum', 'unbekannt')}"
            )
        )
        self.hardware_button.configure(state="normal")

        self._set_badge(
            self.hardware_badge,
            text=f"Hardware: {STATUS_LABELS.get(hardware_status, hardware_status)}",
            status=hardware_status,
        )
        self._set_badge(
            self.update_badge,
            text=self._update_badge_text(),
            status=update_status,
        )

        cpu_name = str(
            self.hardware_result.get(
                "Prozessor",
                "Nicht ermittelbar",
            )
        )
        self.metric_values["cpu"].configure(
            text=self._short_cpu_name(cpu_name)
        )
        self.metric_details["cpu"].configure(
            text=str(
                self.hardware_result.get(
                    "CPU-Details",
                    "",
                )
            )
        )

        self.metric_values["ram"].configure(
            text=str(
                self.hardware_result.get(
                    "Arbeitsspeicher",
                    "Nicht ermittelbar",
                )
            )
        )
        ram_modules = self.hardware_result.get("RAM-Module")
        self.metric_details["ram"].configure(
            text=self._compact_count_text(
                ram_modules,
                singular="Modul",
                plural="Module",
            )
        )

        graphics = self.hardware_result.get("Grafikkarten")
        self.metric_values["gpu"].configure(
            text=self._first_line(graphics)
        )
        self.metric_details["gpu"].configure(
            text=self._compact_count_text(
                graphics,
                singular="Grafikadapter",
                plural="Grafikadapter",
            )
        )

        update_required = str(
            self.update_result.get(
                "Update erforderlich",
                "Nicht ermittelbar",
            )
        )
        self.metric_values["updates"].configure(
            text=self._short_update_text(update_required),
            text_color=(
                STATUS_COLORS.get(update_status, Colors.TEXT)
                if update_status in {"WARNUNG", "KRITISCH", "FEHLER"}
                else Colors.TEXT
            ),
        )
        self.metric_details["updates"].configure(
            text=(
                f"Windows: "
                f"{self.update_result.get('Verfügbare Windows-Updates', '?')}"
                f"  |  Treiber: "
                f"{self.update_result.get('Verfügbare Treiberupdates', '?')}"
            )
        )

        self.detail_labels["board"].configure(
            text=(
                f"Mainboard\n"
                f"{self.hardware_result.get('Mainboard', 'Nicht ermittelbar')}\n\n"
                f"BIOS\n"
                f"{self.hardware_result.get('BIOS-Hersteller', 'Unbekannt')} "
                f"{self.hardware_result.get('BIOS-Version', 'unbekannt')}\n"
                f"Datum: {self.hardware_result.get('BIOS-Datum', 'unbekannt')}"
            )
        )
        self.detail_labels["memory"].configure(
            text=self._list_text(
                self.hardware_result.get("RAM-Module"),
                limit=4,
            )
        )
        self.detail_labels["graphics"].configure(
            text=self._list_text(
                self.hardware_result.get("Grafikkarten"),
                limit=4,
            )
        )
        self.detail_labels["storage"].configure(
            text=self._list_text(
                self.hardware_result.get("Laufwerke"),
                limit=4,
            )
        )
        self.detail_labels["network"].configure(
            text=self._list_text(
                self.hardware_result.get("Netzwerkadapter"),
                limit=4,
            )
        )
        self.detail_labels["devices"].configure(
            text=(
                f"{self.hardware_result.get('Hinweis', 'Nicht ermittelbar')}\n\n"
                f"{self._list_text(
                    self.hardware_result.get('Geräte mit Fehlerstatus'),
                    limit=5,
                )}"
            ),
            text_color=(
                STATUS_COLORS.get(hardware_status, Colors.MUTED)
                if hardware_status in {"WARNUNG", "KRITISCH", "FEHLER"}
                else Colors.MUTED
            ),
        )
        self.detail_labels["update_details"].configure(
            text=(
                f"{update_required}\n\n"
                f"Windows-Updates: "
                f"{self.update_result.get('Verfügbare Windows-Updates', '?')}\n"
                f"Treiberupdates: "
                f"{self.update_result.get('Verfügbare Treiberupdates', '?')}\n"
                f"Neustart erforderlich: "
                f"{self.update_result.get('Neustart erforderlich', '?')}\n\n"
                f"{self.update_result.get('Hinweis', '')}"
            ),
            text_color=(
                STATUS_COLORS.get(update_status, Colors.MUTED)
                if update_status in {"WARNUNG", "KRITISCH", "FEHLER"}
                else Colors.MUTED
            ),
        )

    def _set_badge(
        self,
        badge: ctk.CTkLabel,
        text: str,
        status: str,
        muted: bool = False,
    ) -> None:
        if muted:
            badge.configure(
                text=text,
                fg_color=("gray88", "gray25"),
                text_color=Colors.MUTED,
            )
            return

        color = STATUS_COLORS.get(
            status,
            STATUS_COLORS["INFO"],
        )
        badge.configure(
            text=text,
            fg_color=color,
            text_color="white",
        )

    def _update_badge_text(self) -> str:
        restart = str(
            self.update_result.get(
                "Neustart erforderlich",
                "Nein",
            )
        ).casefold()

        if restart == "ja":
            return "Updates: Neustart erforderlich"

        windows_count = self.update_result.get(
            "Verfügbare Windows-Updates",
            0,
        )
        driver_count = self.update_result.get(
            "Verfügbare Treiberupdates",
            0,
        )

        try:
            total = int(windows_count) + int(driver_count)
        except (TypeError, ValueError):
            return "Updates: Status prüfen"

        if total:
            return f"Updates: {total} verfügbar"

        return "Updates: aktuell"

    def _open_hardware(self) -> None:
        if not self.hardware_result:
            return

        rating = str(
            self.hardware_result.get(
                "Bewertung",
                "INFO",
            )
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
            self.update_result.get(
                "Bewertung",
                "INFO",
            )
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
    def _short_cpu_name(value: str) -> str:
        cleaned = value.replace("(R)", "").replace("(TM)", "")
        cleaned = " ".join(cleaned.split())

        for suffix in (
            "8-Core Processor",
            "16-Core Processor",
            "Processor",
            "CPU",
        ):
            if cleaned.endswith(suffix):
                cleaned = cleaned[: -len(suffix)].strip()

        return cleaned or "Nicht ermittelbar"

    @staticmethod
    def _short_update_text(value: str) -> str:
        if "Neustart erforderlich" in value:
            return "Neustart erforderlich"
        if "keine ausstehenden" in value.casefold():
            return "System aktuell"
        if "Windows-Update" in value:
            return value.replace("Ja – ", "")
        if "Treiberupdate" in value:
            return value.replace("Optional – ", "")
        return value

    @staticmethod
    def _first_line(value: Any) -> str:
        if isinstance(value, list) and value:
            first = str(value[0])
        else:
            first = str(value or "Nicht ermittelbar")

        return first.split("|", 1)[0].strip()

    @staticmethod
    def _compact_count_text(
        value: Any,
        singular: str,
        plural: str,
    ) -> str:
        if not isinstance(value, list):
            return ""

        count = len(value)
        label = singular if count == 1 else plural
        return f"{count} {label}"

    @staticmethod
    def _list_text(
        value: Any,
        limit: int = 3,
    ) -> str:
        if not isinstance(value, list) or not value:
            return str(value or "Nicht ermittelbar")

        visible = [
            f"• {item}"
            for item in value[:limit]
        ]
        text = "\n".join(visible)

        if len(value) > limit:
            text += f"\n• {len(value) - limit} weitere Einträge"

        return text
