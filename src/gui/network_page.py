"""Eigene Netzwerkübersicht für das Diagnostic Toolkit."""

from __future__ import annotations

import os
from typing import Any

import customtkinter as ctk
from tkinter import messagebox

from src.gui.detail_window import ResultDetailWindow
from src.gui.theme import Colors


STATUS_STYLES = {
    "OK": ("NETZWERK OK", Colors.SUCCESS_SOFT, Colors.SUCCESS),
    "INFO": ("INFORMATION", Colors.SURFACE_SOFT, Colors.PRIMARY),
    "HINWEIS": ("HINWEIS", Colors.SURFACE_SOFT, Colors.MUTED),
    "WARNUNG": ("WARNUNG", Colors.WARNING_SOFT, Colors.WARNING),
    "KRITISCH": ("KRITISCH", Colors.DANGER_SOFT, Colors.DANGER),
    "FEHLER": ("FEHLER", Colors.DANGER_SOFT, Colors.DANGER),
}


class NetworkPage(ctk.CTkFrame):
    """Zeigt Adapter, IP-Konfiguration und Verbindungstests."""

    def __init__(self, master) -> None:
        super().__init__(master, fg_color="transparent")

        self.result: dict[str, Any] = {}
        self.metric_values: dict[str, ctk.CTkLabel] = {}
        self.metric_details: dict[str, ctk.CTkLabel] = {}

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self._create_status_panel()
        self._create_metric_row()
        self._create_tabs()
        self.reset()

    def _create_status_panel(self) -> None:
        panel = ctk.CTkFrame(
            self,
            height=104,
            corner_radius=18,
            border_width=1,
            border_color=Colors.BORDER,
            fg_color=Colors.SURFACE_RAISED,
        )
        panel.grid(row=0, column=0, pady=(0, 12), sticky="ew")
        panel.grid_propagate(False)
        panel.grid_columnconfigure(0, weight=1)

        self.status_title = ctk.CTkLabel(
            panel,
            text="Noch keine Netzwerkdaten",
            anchor="w",
            text_color=Colors.TEXT,
            font=ctk.CTkFont(size=20, weight="bold"),
        )
        self.status_title.grid(
            row=0,
            column=0,
            padx=18,
            pady=(17, 2),
            sticky="w",
        )

        self.status_summary = ctk.CTkLabel(
            panel,
            text="Führe eine Diagnose durch.",
            anchor="w",
            justify="left",
            wraplength=620,
            text_color=Colors.MUTED,
            font=ctk.CTkFont(size=12),
        )
        self.status_summary.grid(
            row=1,
            column=0,
            padx=18,
            pady=(0, 17),
            sticky="w",
        )

        self.status_badge = ctk.CTkLabel(
            panel,
            text="NICHT GEPRÜFT",
            height=30,
            corner_radius=8,
            fg_color=Colors.SURFACE_SOFT,
            text_color=Colors.MUTED,
            font=ctk.CTkFont(size=10, weight="bold"),
        )
        self.status_badge.grid(
            row=0,
            column=1,
            rowspan=2,
            padx=(10, 6),
            pady=34,
        )

        self.details_button = ctk.CTkButton(
            panel,
            text="Alle Netzwerkdetails",
            width=164,
            height=36,
            state="disabled",
            command=self._open_details,
        )
        self.details_button.grid(
            row=0,
            column=2,
            rowspan=2,
            padx=6,
            pady=34,
        )

        ctk.CTkButton(
            panel,
            text="Windows-Einstellungen",
            width=174,
            height=36,
            fg_color=Colors.SURFACE_SOFT,
            hover_color=Colors.NAV_HOVER,
            text_color=Colors.TEXT,
            border_width=1,
            border_color=Colors.BORDER,
            command=self._open_network_settings,
        ).grid(
            row=0,
            column=3,
            rowspan=2,
            padx=(6, 18),
            pady=34,
        )

    def _create_metric_row(self) -> None:
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.grid(row=1, column=0, pady=(0, 12), sticky="ew")

        metrics = (
            ("active", "AKTIVE ADAPTER"),
            ("physical", "PHYSISCHE ADAPTER"),
            ("tests", "VERBINDUNGSTESTS"),
            ("dns", "DNS-AUFLÖSUNG"),
        )

        for column, (key, title) in enumerate(metrics):
            frame.grid_columnconfigure(
                column,
                weight=1,
                uniform="network_metrics",
            )

            card = ctk.CTkFrame(
                frame,
                height=104,
                corner_radius=16,
                border_width=1,
                border_color=Colors.BORDER,
                fg_color=Colors.SURFACE_RAISED,
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

            value = ctk.CTkLabel(
                card,
                text="–",
                anchor="w",
                text_color=Colors.TEXT,
                font=ctk.CTkFont(size=22, weight="bold"),
            )
            value.grid(row=1, column=0, padx=14, sticky="w")

            detail = ctk.CTkLabel(
                card,
                text="Noch nicht ermittelt",
                anchor="w",
                justify="left",
                wraplength=220,
                text_color=Colors.MUTED,
                font=ctk.CTkFont(size=10),
            )
            detail.grid(
                row=2,
                column=0,
                padx=14,
                pady=(1, 11),
                sticky="ew",
            )

            self.metric_values[key] = value
            self.metric_details[key] = detail

    def _create_tabs(self) -> None:
        self.tabview = ctk.CTkTabview(
            self,
            corner_radius=16,
            border_width=1,
            border_color=Colors.BORDER,
            fg_color=Colors.SURFACE_RAISED,
            segmented_button_fg_color=Colors.SURFACE_SOFT,
            segmented_button_selected_color=Colors.PRIMARY,
            segmented_button_selected_hover_color=Colors.PRIMARY_HOVER,
        )
        self.tabview.grid(row=2, column=0, sticky="nsew")

        adapters_tab = self.tabview.add("Netzwerkadapter")
        tests_tab = self.tabview.add("Verbindungstests")
        configuration_tab = self.tabview.add("IP-Konfiguration")

        for tab in (adapters_tab, tests_tab, configuration_tab):
            tab.grid_columnconfigure(0, weight=1)
            tab.grid_rowconfigure(0, weight=1)

        self.adapters_frame = self._new_scroll_frame(adapters_tab)
        self.tests_frame = self._new_scroll_frame(tests_tab)
        self.configuration_frame = self._new_scroll_frame(
            configuration_tab
        )

    @staticmethod
    def _new_scroll_frame(master) -> ctk.CTkScrollableFrame:
        frame = ctk.CTkScrollableFrame(
            master,
            fg_color="transparent",
        )
        frame.grid(
            row=0,
            column=0,
            padx=4,
            pady=4,
            sticky="nsew",
        )
        frame.grid_columnconfigure(
            (0, 1),
            weight=1,
            uniform="network_cards",
        )
        return frame

    def reset(self) -> None:
        self.result = {}
        self.status_title.configure(text="Noch keine Netzwerkdaten")
        self.status_summary.configure(text="Führe eine Diagnose durch.")
        self.status_badge.configure(
            text="NICHT GEPRÜFT",
            fg_color=Colors.SURFACE_SOFT,
            text_color=Colors.MUTED,
        )
        self.details_button.configure(state="disabled")

        for label in self.metric_values.values():
            label.configure(text="–")
        for label in self.metric_details.values():
            label.configure(text="Noch nicht ermittelt")

        self._show_placeholder(
            self.adapters_frame,
            "Nach der Diagnose werden hier die aktiven "
            "physischen und virtuellen Adapter angezeigt.",
        )
        self._show_placeholder(
            self.tests_frame,
            "Nach der Diagnose werden hier Paketverlust "
            "und Latenz angezeigt.",
        )
        self._show_placeholder(
            self.configuration_frame,
            "Nach der Diagnose werden hier IPv4, Gateway, "
            "DNS und Hinweise angezeigt.",
        )

    def update_from_results(
        self,
        results: list[tuple[str, dict]],
    ) -> None:
        result = next(
            (
                item
                for title, item in results
                if title == "Netzwerkprüfung"
            ),
            {},
        )
        self.update_result(result)

    def update_result(self, result: dict[str, Any]) -> None:
        self.result = dict(result)

        if not self.result:
            self.reset()
            return

        rating = str(
            self.result.get("Bewertung", "INFO")
        ).upper()
        label, foreground, text_color = STATUS_STYLES.get(
            rating,
            STATUS_STYLES["INFO"],
        )

        self.status_title.configure(
            text=self._status_title(rating)
        )
        self.status_summary.configure(
            text=str(
                self.result.get(
                    "Zusammenfassung",
                    self.result.get(
                        "Hinweis",
                        "Netzwerkdaten wurden erfasst.",
                    ),
                )
            )
        )
        self.status_badge.configure(
            text=label,
            fg_color=foreground,
            text_color=text_color,
        )
        self.details_button.configure(state="normal")

        active = self.result.get("Aktive Adapter", "–")
        physical = self.result.get("Physische Adapter", "–")
        virtual = self.result.get("Virtuelle Adapter", "–")

        self.metric_values["active"].configure(text=str(active))
        self.metric_details["active"].configure(
            text=f"{virtual} virtuelle Adapter"
        )
        self.metric_values["physical"].configure(text=str(physical))
        self.metric_details["physical"].configure(
            text="Direkte Netzwerkverbindungen"
        )
        self.metric_values["tests"].configure(
            text=str(
                self.result.get(
                    "Erfolgreiche Verbindungstests",
                    "–",
                )
            )
        )
        self.metric_details["tests"].configure(
            text="Externe Erreichbarkeit"
        )
        self.metric_values["dns"].configure(
            text=str(
                self.result.get("DNS-Auflösung", "–")
            )
        )
        self.metric_details["dns"].configure(
            text=str(
                self.result.get(
                    "DNS-Zieladressen",
                    "Keine Zieladresse",
                )
            )
        )

        self._render_adapters()
        self._render_tests()
        self._render_configuration()

    def _render_adapters(self) -> None:
        self._clear(self.adapters_frame)
        adapters = self.result.get("Adapterdetails", [])

        if not isinstance(adapters, list) or not adapters:
            self._show_placeholder(
                self.adapters_frame,
                "Keine aktiven Netzwerkadapter gefunden.",
            )
            return

        for index, adapter in enumerate(adapters):
            if not isinstance(adapter, dict):
                continue

            card = self._new_card(
                self.adapters_frame,
                row=index // 2,
                column=index % 2,
            )

            ctk.CTkLabel(
                card,
                text=str(
                    adapter.get("Name", "Unbekannter Adapter")
                ),
                anchor="w",
                text_color=Colors.TEXT,
                font=ctk.CTkFont(size=14, weight="bold"),
            ).grid(
                row=0,
                column=0,
                padx=14,
                pady=(13, 1),
                sticky="w",
            )

            ctk.CTkLabel(
                card,
                text=str(
                    adapter.get(
                        "Beschreibung",
                        "Keine Beschreibung",
                    )
                ),
                anchor="w",
                justify="left",
                wraplength=420,
                text_color=Colors.MUTED,
                font=ctk.CTkFont(size=10),
            ).grid(
                row=1,
                column=0,
                padx=14,
                pady=(0, 9),
                sticky="ew",
            )

            values = (
                (
                    "Typ",
                    "Virtuell"
                    if adapter.get("Virtuell") == "Ja"
                    else "Physisch",
                ),
                (
                    "Link",
                    adapter.get(
                        "Link-Geschwindigkeit",
                        "Nicht ermittelt",
                    ),
                ),
                (
                    "IPv4",
                    adapter.get(
                        "IPv4-Adresse",
                        "Nicht vorhanden",
                    ),
                ),
                (
                    "Gateway",
                    adapter.get(
                        "Standardgateway",
                        "Nicht vorhanden",
                    ),
                ),
                (
                    "DHCP",
                    adapter.get("DHCP", "Nicht ermittelt"),
                ),
                (
                    "Profil",
                    adapter.get(
                        "Netzwerkprofil",
                        "Nicht ermittelt",
                    ),
                ),
            )

            for row, (name, value) in enumerate(values, start=2):
                self._add_value_row(card, row, name, value)

            ctk.CTkLabel(
                card,
                text=self._format_messages(
                    adapter.get("Hinweise", [])
                ),
                anchor="w",
                justify="left",
                wraplength=420,
                text_color=Colors.MUTED,
                font=ctk.CTkFont(size=10),
            ).grid(
                row=8,
                column=0,
                padx=14,
                pady=(8, 13),
                sticky="ew",
            )

    def _render_tests(self) -> None:
        self._clear(self.tests_frame)
        tests = self.result.get("Verbindungstests", [])

        if not isinstance(tests, list) or not tests:
            self._show_placeholder(
                self.tests_frame,
                "Keine Verbindungstests vorhanden.",
            )
            return

        for column, test in enumerate(tests):
            if not isinstance(test, dict):
                continue

            card = self._new_card(
                self.tests_frame,
                row=0,
                column=column,
            )

            ctk.CTkLabel(
                card,
                text=str(test.get("Ziel", "Unbekannt")),
                anchor="w",
                text_color=Colors.TEXT,
                font=ctk.CTkFont(size=17, weight="bold"),
            ).grid(
                row=0,
                column=0,
                padx=16,
                pady=(16, 6),
                sticky="w",
            )

            sent = test.get("Gesendet", "–")
            received = test.get("Empfangen", "–")
            rows = (
                ("Pakete", f"{received} von {sent} empfangen"),
                (
                    "Paketverlust",
                    test.get(
                        "Paketverlust",
                        "Nicht messbar",
                    ),
                ),
                (
                    "Mittlere Latenz",
                    test.get(
                        "Mittlere Latenz",
                        "Nicht messbar",
                    ),
                ),
            )

            for row, (name, value) in enumerate(rows, start=1):
                self._add_value_row(card, row, name, value)

            ctk.CTkFrame(
                card,
                height=4,
                corner_radius=3,
                fg_color=self._test_color(
                    test.get("Paketverlust", "")
                ),
            ).grid(
                row=4,
                column=0,
                padx=16,
                pady=(12, 16),
                sticky="ew",
            )

    def _render_configuration(self) -> None:
        self._clear(self.configuration_frame)

        values = (
            (
                "IPv4-Adressen",
                self.result.get(
                    "IPv4-Adressen",
                    "Nicht vorhanden",
                ),
            ),
            (
                "Standardgateway",
                self.result.get(
                    "Standardgateways",
                    "Nicht vorhanden",
                ),
            ),
            (
                "DNS-Server",
                self.result.get(
                    "DNS-Server",
                    "Nicht vorhanden",
                ),
            ),
            (
                "DNS-Auflösung",
                self.result.get(
                    "DNS-Auflösung",
                    "Nicht ermittelt",
                ),
            ),
        )

        for index, (title, value) in enumerate(values):
            card = self._new_card(
                self.configuration_frame,
                row=index // 2,
                column=index % 2,
            )
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
                pady=(13, 3),
                sticky="w",
            )
            ctk.CTkLabel(
                card,
                text=str(value),
                anchor="w",
                justify="left",
                wraplength=440,
                text_color=Colors.TEXT,
                font=ctk.CTkFont(size=14, weight="bold"),
            ).grid(
                row=1,
                column=0,
                padx=14,
                pady=(0, 14),
                sticky="ew",
            )

        self._add_message_card(
            "Warnungen",
            self._format_messages(
                self.result.get("Warnungen", []),
                "Keine Warnungen erkannt.",
            ),
            row=2,
            color=Colors.WARNING,
        )
        self._add_message_card(
            "Hinweise",
            self._format_messages(
                self.result.get("Hinweise", []),
                "Keine zusätzlichen Hinweise.",
            ),
            row=3,
            color=Colors.PRIMARY,
        )

    @staticmethod
    def _new_card(master, row: int, column: int) -> ctk.CTkFrame:
        card = ctk.CTkFrame(
            master,
            corner_radius=14,
            border_width=1,
            border_color=Colors.BORDER,
            fg_color=Colors.SURFACE_SOFT,
        )
        card.grid(
            row=row,
            column=column,
            padx=6,
            pady=6,
            sticky="nsew",
        )
        card.grid_columnconfigure(0, weight=1)
        return card

    @staticmethod
    def _add_value_row(
        master,
        row: int,
        name: str,
        value: Any,
    ) -> None:
        frame = ctk.CTkFrame(
            master,
            fg_color="transparent",
        )
        frame.grid(
            row=row,
            column=0,
            padx=14,
            pady=3,
            sticky="ew",
        )
        frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            frame,
            text=name,
            width=112,
            anchor="w",
            text_color=Colors.SUBTLE,
            font=ctk.CTkFont(size=10),
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(
            frame,
            text=str(value),
            anchor="w",
            justify="left",
            wraplength=310,
            text_color=Colors.TEXT,
            font=ctk.CTkFont(size=11),
        ).grid(row=0, column=1, sticky="ew")

    def _add_message_card(
        self,
        title: str,
        text: str,
        row: int,
        color,
    ) -> None:
        card = self._new_card(
            self.configuration_frame,
            row=row,
            column=0,
        )
        card.grid_configure(columnspan=2)
        card.grid_columnconfigure(1, weight=1)

        ctk.CTkFrame(
            card,
            width=5,
            corner_radius=3,
            fg_color=color,
        ).grid(
            row=0,
            column=0,
            rowspan=2,
            padx=(0, 12),
            pady=10,
            sticky="ns",
        )

        ctk.CTkLabel(
            card,
            text=title,
            anchor="w",
            text_color=Colors.TEXT,
            font=ctk.CTkFont(size=13, weight="bold"),
        ).grid(
            row=0,
            column=1,
            padx=(0, 14),
            pady=(12, 2),
            sticky="w",
        )

        ctk.CTkLabel(
            card,
            text=text,
            anchor="w",
            justify="left",
            wraplength=900,
            text_color=Colors.MUTED,
            font=ctk.CTkFont(size=11),
        ).grid(
            row=1,
            column=1,
            padx=(0, 14),
            pady=(0, 12),
            sticky="ew",
        )

    @staticmethod
    def _clear(frame) -> None:
        for widget in frame.winfo_children():
            widget.destroy()

    def _show_placeholder(self, frame, text: str) -> None:
        self._clear(frame)
        card = self._new_card(frame, row=0, column=0)
        card.grid_configure(columnspan=2)

        ctk.CTkLabel(
            card,
            text=text,
            anchor="w",
            justify="left",
            wraplength=850,
            text_color=Colors.MUTED,
            font=ctk.CTkFont(size=12),
        ).grid(
            row=0,
            column=0,
            padx=16,
            pady=22,
            sticky="ew",
        )

    @staticmethod
    def _format_messages(
        value: Any,
        fallback: str = "Keine Auffälligkeit erkannt.",
    ) -> str:
        if isinstance(value, list):
            messages = [
                str(item).strip()
                for item in value
                if str(item).strip()
            ]
            return (
                "\n".join(
                    f"• {message}"
                    for message in messages
                )
                if messages
                else fallback
            )

        text = str(value).strip()
        return text or fallback

    @staticmethod
    def _test_color(loss: Any):
        text = str(loss).replace("%", "").strip()

        try:
            value = float(text.replace(",", "."))
        except ValueError:
            return Colors.MUTED

        if value == 0:
            return Colors.SUCCESS
        if value < 25:
            return Colors.WARNING
        return Colors.DANGER

    @staticmethod
    def _status_title(rating: str) -> str:
        if rating == "OK":
            return "Netzwerkverbindung ist unauffällig"
        if rating == "HINWEIS":
            return "Netzwerkverbindung mit Hinweisen"
        if rating == "WARNUNG":
            return "Netzwerkauffälligkeiten erkannt"
        if rating in {"KRITISCH", "FEHLER"}:
            return "Netzwerkprüfung nicht vollständig abgeschlossen"
        return "Netzwerkdaten wurden erfasst"

    def _open_details(self) -> None:
        if not self.result:
            return

        rating = str(
            self.result.get("Bewertung", "INFO")
        ).upper()
        _, _, status_color = STATUS_STYLES.get(
            rating,
            STATUS_STYLES["INFO"],
        )

        ResultDetailWindow(
            master=self,
            title="Netzwerkprüfung",
            result=self.result,
            status_color=status_color,
        )

    @staticmethod
    def _open_network_settings() -> None:
        try:
            os.startfile("ms-settings:network-status")
        except OSError as error:
            messagebox.showerror(
                "Netzwerkeinstellungen",
                (
                    "Die Windows-Netzwerkeinstellungen "
                    "konnten nicht geöffnet werden.\n\n"
                    f"{error}"
                ),
            )
