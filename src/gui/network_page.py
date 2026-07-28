"""Professionelle Netzwerkübersicht für das Diagnostic Toolkit."""

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
    "HINWEIS": ("HINWEIS", Colors.SURFACE_SOFT, Colors.PRIMARY),
    "WARNUNG": ("WARNUNG", Colors.WARNING_SOFT, Colors.WARNING),
    "KRITISCH": ("KRITISCH", Colors.DANGER_SOFT, Colors.DANGER),
    "FEHLER": ("FEHLER", Colors.DANGER_SOFT, Colors.DANGER),
}


class NetworkPage(ctk.CTkFrame):
    """Zeigt die primäre Verbindung und zusätzliche Netzwerkadapter."""

    def __init__(self, master) -> None:
        super().__init__(master, fg_color="transparent")

        self.result: dict[str, Any] = {}
        self.metric_values: dict[str, ctk.CTkLabel] = {}
        self.metric_details: dict[str, ctk.CTkLabel] = {}

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self._create_status_panel()
        self._create_metric_row()
        self._create_content()
        self.reset()

    def _create_status_panel(self) -> None:
        panel = ctk.CTkFrame(
            self,
            height=96,
            corner_radius=16,
            border_width=1,
            border_color=Colors.BORDER,
            fg_color=Colors.SURFACE_RAISED,
        )
        panel.grid(row=0, column=0, pady=(0, 10), sticky="ew")
        panel.grid_propagate(False)
        panel.grid_columnconfigure(1, weight=1)

        self.status_accent = ctk.CTkFrame(
            panel,
            width=5,
            corner_radius=3,
            fg_color=Colors.PRIMARY,
        )
        self.status_accent.grid(
            row=0,
            column=0,
            rowspan=2,
            padx=(0, 16),
            pady=14,
            sticky="ns",
        )

        self.status_title = ctk.CTkLabel(
            panel,
            text="Noch keine Netzwerkdaten",
            anchor="w",
            text_color=Colors.TEXT,
            font=ctk.CTkFont(size=18, weight="bold"),
        )
        self.status_title.grid(
            row=0,
            column=1,
            padx=(0, 12),
            pady=(16, 2),
            sticky="w",
        )

        self.status_summary = ctk.CTkLabel(
            panel,
            text="Führe eine Diagnose durch.",
            anchor="w",
            justify="left",
            wraplength=540,
            text_color=Colors.MUTED,
            font=ctk.CTkFont(size=11),
        )
        self.status_summary.grid(
            row=1,
            column=1,
            padx=(0, 12),
            pady=(0, 16),
            sticky="w",
        )

        self.status_badge = ctk.CTkLabel(
            panel,
            text="NICHT GEPRÜFT",
            height=28,
            corner_radius=8,
            fg_color=Colors.SURFACE_SOFT,
            text_color=Colors.MUTED,
            font=ctk.CTkFont(size=9, weight="bold"),
        )
        self.status_badge.grid(
            row=0,
            column=2,
            rowspan=2,
            padx=6,
            pady=34,
        )

        self.details_button = ctk.CTkButton(
            panel,
            text="Details",
            width=98,
            height=34,
            state="disabled",
            command=self._open_details,
        )
        self.details_button.grid(
            row=0,
            column=3,
            rowspan=2,
            padx=6,
            pady=31,
        )

        ctk.CTkButton(
            panel,
            text="Netzwerkeinstellungen",
            width=168,
            height=34,
            fg_color=Colors.SURFACE_SOFT,
            hover_color=Colors.NAV_HOVER,
            text_color=Colors.TEXT,
            border_width=1,
            border_color=Colors.BORDER,
            command=self._open_network_settings,
        ).grid(
            row=0,
            column=4,
            rowspan=2,
            padx=(6, 16),
            pady=31,
        )

    def _create_metric_row(self) -> None:
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.grid(row=1, column=0, pady=(0, 10), sticky="ew")

        metrics = (
            ("active", "AKTIVE ADAPTER"),
            ("physical", "PHYSISCHE VERBINDUNG"),
            ("tests", "ERREICHBARKEIT"),
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
                height=94,
                corner_radius=14,
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
                font=ctk.CTkFont(size=9, weight="bold"),
            ).grid(
                row=0,
                column=0,
                padx=13,
                pady=(11, 2),
                sticky="w",
            )

            value = ctk.CTkLabel(
                card,
                text="–",
                anchor="w",
                text_color=Colors.TEXT,
                font=ctk.CTkFont(size=20, weight="bold"),
            )
            value.grid(
                row=1,
                column=0,
                padx=13,
                sticky="w",
            )

            detail = ctk.CTkLabel(
                card,
                text="Noch nicht ermittelt",
                anchor="w",
                text_color=Colors.MUTED,
                font=ctk.CTkFont(size=9),
            )
            detail.grid(
                row=2,
                column=0,
                padx=13,
                pady=(2, 11),
                sticky="w",
            )

            self.metric_values[key] = value
            self.metric_details[key] = detail

    def _create_content(self) -> None:
        self.content = ctk.CTkScrollableFrame(
            self,
            corner_radius=16,
            border_width=1,
            border_color=Colors.BORDER,
            fg_color=Colors.SURFACE_RAISED,
        )
        self.content.grid(
            row=2,
            column=0,
            sticky="nsew",
        )
        self.content.grid_columnconfigure(
            0,
            weight=3,
            uniform="network_content",
        )
        self.content.grid_columnconfigure(
            1,
            weight=2,
            uniform="network_content",
        )

        self.primary_panel = self._create_panel(
            row=0,
            column=0,
            title="Primäre Verbindung",
            padx=(6, 5),
        )
        self.primary_content = ctk.CTkFrame(
            self.primary_panel,
            fg_color="transparent",
        )
        self.primary_content.grid(
            row=1,
            column=0,
            padx=14,
            pady=(0, 14),
            sticky="ew",
        )
        self.primary_content.grid_columnconfigure((0, 1), weight=1)

        self.quality_panel = self._create_panel(
            row=0,
            column=1,
            title="Verbindungsqualität",
            padx=(5, 6),
        )
        self.quality_content = ctk.CTkFrame(
            self.quality_panel,
            fg_color="transparent",
        )
        self.quality_content.grid(
            row=1,
            column=0,
            padx=14,
            pady=(0, 14),
            sticky="ew",
        )
        self.quality_content.grid_columnconfigure(0, weight=1)

        self.adapters_panel = self._create_panel(
            row=1,
            column=0,
            title="Weitere Netzwerkadapter",
            padx=(6, 5),
            pady=(5, 6),
        )
        self.adapters_content = ctk.CTkFrame(
            self.adapters_panel,
            fg_color="transparent",
        )
        self.adapters_content.grid(
            row=1,
            column=0,
            padx=14,
            pady=(0, 14),
            sticky="ew",
        )
        self.adapters_content.grid_columnconfigure(0, weight=1)

        self.configuration_panel = self._create_panel(
            row=1,
            column=1,
            title="IP-Konfiguration",
            padx=(5, 6),
            pady=(5, 6),
        )
        self.configuration_content = ctk.CTkFrame(
            self.configuration_panel,
            fg_color="transparent",
        )
        self.configuration_content.grid(
            row=1,
            column=0,
            padx=14,
            pady=(0, 14),
            sticky="ew",
        )
        self.configuration_content.grid_columnconfigure(0, weight=1)

    def _create_panel(
        self,
        row: int,
        column: int,
        title: str,
        padx,
        pady=(6, 5),
    ) -> ctk.CTkFrame:
        panel = ctk.CTkFrame(
            self.content,
            corner_radius=14,
            border_width=1,
            border_color=Colors.BORDER,
            fg_color=Colors.SURFACE_SOFT,
        )
        panel.grid(
            row=row,
            column=column,
            padx=padx,
            pady=pady,
            sticky="nsew",
        )
        panel.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            panel,
            text=title,
            anchor="w",
            text_color=Colors.TEXT,
            font=ctk.CTkFont(size=14, weight="bold"),
        ).grid(
            row=0,
            column=0,
            padx=14,
            pady=(13, 9),
            sticky="w",
        )
        return panel

    def reset(self) -> None:
        self.result = {}

        self.status_title.configure(text="Noch keine Netzwerkdaten")
        self.status_summary.configure(text="Führe eine Diagnose durch.")
        self.status_badge.configure(
            text="NICHT GEPRÜFT",
            fg_color=Colors.SURFACE_SOFT,
            text_color=Colors.MUTED,
        )
        self.status_accent.configure(fg_color=Colors.PRIMARY)
        self.details_button.configure(state="disabled")

        for label in self.metric_values.values():
            label.configure(text="–")
        for label in self.metric_details.values():
            label.configure(text="Noch nicht ermittelt")

        self._placeholder(
            self.primary_content,
            "Die primäre Verbindung erscheint nach der Diagnose.",
        )
        self._placeholder(
            self.quality_content,
            "Latenz und Paketverlust erscheinen nach der Diagnose.",
        )
        self._placeholder(
            self.adapters_content,
            "Weitere Adapter erscheinen nach der Diagnose.",
        )
        self._placeholder(
            self.configuration_content,
            "IPv4, Gateway und DNS erscheinen nach der Diagnose.",
        )
        self._scroll_to_top()

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
        badge, background, color = STATUS_STYLES.get(
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
            text=badge,
            fg_color=background,
            text_color=color,
        )
        self.status_accent.configure(fg_color=color)
        self.details_button.configure(state="normal")

        active = self.result.get("Aktive Adapter", "–")
        physical = self.result.get("Physische Adapter", "–")
        virtual = self.result.get("Virtuelle Adapter", "–")
        tests = self.result.get(
            "Erfolgreiche Verbindungstests",
            "–",
        )

        self.metric_values["active"].configure(text=str(active))
        self.metric_details["active"].configure(
            text=f"{virtual} virtuelle Adapter"
        )
        self.metric_values["physical"].configure(text=str(physical))
        self.metric_details["physical"].configure(
            text="direkte Verbindung"
        )
        self.metric_values["tests"].configure(text=str(tests))
        self.metric_details["tests"].configure(
            text=self._loss_summary()
        )
        self.metric_values["dns"].configure(
            text=str(
                self.result.get("DNS-Auflösung", "–")
            )
        )
        self.metric_details["dns"].configure(
            text="Namensauflösung"
        )

        adapters = self.result.get("Adapterdetails", [])
        physical_adapter = None
        additional_adapters: list[dict[str, Any]] = []

        if isinstance(adapters, list):
            for adapter in adapters:
                if not isinstance(adapter, dict):
                    continue
                if (
                    physical_adapter is None
                    and adapter.get("Virtuell") != "Ja"
                ):
                    physical_adapter = adapter
                else:
                    additional_adapters.append(adapter)

        self._render_primary(physical_adapter)
        self._render_quality()
        self._render_additional(additional_adapters)
        self._render_configuration()
        self._scroll_to_top()

    def _render_primary(
        self,
        adapter: dict[str, Any] | None,
    ) -> None:
        self._clear(self.primary_content)

        if adapter is None:
            self._placeholder(
                self.primary_content,
                "Keine aktive physische Verbindung erkannt.",
            )
            return

        header = ctk.CTkFrame(
            self.primary_content,
            fg_color="transparent",
        )
        header.grid(
            row=0,
            column=0,
            columnspan=2,
            pady=(0, 10),
            sticky="ew",
        )
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header,
            text=str(adapter.get("Name", "Unbekannter Adapter")),
            anchor="w",
            text_color=Colors.TEXT,
            font=ctk.CTkFont(size=16, weight="bold"),
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(
            header,
            text=self._translate_profile(
                adapter.get("Netzwerkprofil", "Nicht ermittelt")
            ).upper(),
            height=24,
            corner_radius=7,
            fg_color=Colors.SURFACE_RAISED,
            text_color=Colors.PRIMARY,
            font=ctk.CTkFont(size=8, weight="bold"),
        ).grid(row=0, column=1, padx=(8, 0), sticky="e")

        ctk.CTkLabel(
            header,
            text=str(
                adapter.get(
                    "Beschreibung",
                    "Keine Beschreibung",
                )
            ),
            anchor="w",
            justify="left",
            wraplength=500,
            text_color=Colors.MUTED,
            font=ctk.CTkFont(size=9),
        ).grid(
            row=1,
            column=0,
            columnspan=2,
            pady=(1, 0),
            sticky="ew",
        )

        fields = (
            (
                "IPv4-Adresse",
                adapter.get("IPv4-Adresse", "Nicht vorhanden"),
            ),
            (
                "Standardgateway",
                adapter.get("Standardgateway", "Nicht vorhanden"),
            ),
            (
                "DNS-Server",
                adapter.get("DNS-Server", "Nicht vorhanden"),
            ),
            (
                "Link-Geschwindigkeit",
                adapter.get(
                    "Link-Geschwindigkeit",
                    "Nicht ermittelt",
                ),
            ),
            (
                "DHCP",
                self._translate_dhcp(adapter.get("DHCP")),
            ),
            (
                "Netzwerkprofil",
                self._translate_profile(
                    adapter.get(
                        "Netzwerkprofil",
                        "Nicht ermittelt",
                    )
                ),
            ),
        )

        for index, (title, value) in enumerate(fields):
            self._field_card(
                self.primary_content,
                row=1 + index // 2,
                column=index % 2,
                title=title,
                value=value,
            )

        hints = adapter.get("Hinweise", [])
        messages = self._messages(hints)

        if messages:
            ctk.CTkLabel(
                self.primary_content,
                text="  ".join(f"• {item}" for item in messages),
                anchor="w",
                justify="left",
                wraplength=520,
                text_color=Colors.MUTED,
                font=ctk.CTkFont(size=9),
            ).grid(
                row=4,
                column=0,
                columnspan=2,
                pady=(8, 0),
                sticky="ew",
            )

    @staticmethod
    def _field_card(
        master,
        row: int,
        column: int,
        title: str,
        value: Any,
    ) -> None:
        card = ctk.CTkFrame(
            master,
            height=54,
            corner_radius=10,
            fg_color=Colors.SURFACE_RAISED,
        )
        card.grid(
            row=row,
            column=column,
            padx=(0, 5) if column == 0 else (5, 0),
            pady=4,
            sticky="ew",
        )
        card.grid_propagate(False)
        card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            card,
            text=title.upper(),
            anchor="w",
            text_color=Colors.MUTED,
            font=ctk.CTkFont(size=8, weight="bold"),
        ).grid(
            row=0,
            column=0,
            padx=11,
            pady=(7, 0),
            sticky="w",
        )

        ctk.CTkLabel(
            card,
            text=str(value),
            anchor="w",
            justify="left",
            wraplength=230,
            text_color=Colors.TEXT,
            font=ctk.CTkFont(size=10, weight="bold"),
        ).grid(
            row=1,
            column=0,
            padx=11,
            pady=(0, 7),
            sticky="ew",
        )

    def _render_quality(self) -> None:
        self._clear(self.quality_content)
        tests = self.result.get("Verbindungstests", [])

        if not isinstance(tests, list) or not tests:
            self._placeholder(
                self.quality_content,
                "Keine Verbindungstests vorhanden.",
            )
            return

        for row, test in enumerate(tests):
            if not isinstance(test, dict):
                continue

            loss = str(
                test.get("Paketverlust", "Nicht messbar")
            )
            color = self._test_color(loss)

            item = ctk.CTkFrame(
                self.quality_content,
                height=64,
                corner_radius=11,
                fg_color=Colors.SURFACE_RAISED,
            )
            item.grid(
                row=row,
                column=0,
                pady=(0, 7),
                sticky="ew",
            )
            item.grid_propagate(False)
            item.grid_columnconfigure(1, weight=1)

            ctk.CTkFrame(
                item,
                width=8,
                height=8,
                corner_radius=4,
                fg_color=color,
            ).grid(
                row=0,
                column=0,
                rowspan=2,
                padx=(12, 10),
                pady=28,
            )

            ctk.CTkLabel(
                item,
                text=str(test.get("Ziel", "Unbekannt")),
                anchor="w",
                text_color=Colors.TEXT,
                font=ctk.CTkFont(size=11, weight="bold"),
            ).grid(
                row=0,
                column=1,
                pady=(12, 0),
                sticky="w",
            )

            received = test.get("Empfangen", "–")
            sent = test.get("Gesendet", "–")
            ctk.CTkLabel(
                item,
                text=f"{received} von {sent} Paketen empfangen",
                anchor="w",
                text_color=Colors.MUTED,
                font=ctk.CTkFont(size=8),
            ).grid(
                row=1,
                column=1,
                pady=(0, 11),
                sticky="w",
            )

            ctk.CTkLabel(
                item,
                text=str(
                    test.get(
                        "Mittlere Latenz",
                        "Nicht messbar",
                    )
                ),
                anchor="e",
                text_color=Colors.TEXT,
                font=ctk.CTkFont(size=12, weight="bold"),
            ).grid(
                row=0,
                column=2,
                padx=(8, 12),
                pady=(12, 0),
                sticky="e",
            )

            ctk.CTkLabel(
                item,
                text=f"{loss} Verlust",
                anchor="e",
                text_color=Colors.MUTED,
                font=ctk.CTkFont(size=8),
            ).grid(
                row=1,
                column=2,
                padx=(8, 12),
                pady=(0, 11),
                sticky="e",
            )

    def _render_additional(
        self,
        adapters: list[dict[str, Any]],
    ) -> None:
        self._clear(self.adapters_content)

        if not adapters:
            self._placeholder(
                self.adapters_content,
                "Keine weiteren aktiven Adapter erkannt.",
            )
            return

        for row, adapter in enumerate(adapters):
            item = ctk.CTkFrame(
                self.adapters_content,
                height=58,
                corner_radius=10,
                fg_color=Colors.SURFACE_RAISED,
            )
            item.grid(
                row=row,
                column=0,
                pady=(0, 7),
                sticky="ew",
            )
            item.grid_propagate(False)
            item.grid_columnconfigure(0, weight=1)

            ctk.CTkLabel(
                item,
                text=str(
                    adapter.get("Name", "Unbekannter Adapter")
                ),
                anchor="w",
                text_color=Colors.TEXT,
                font=ctk.CTkFont(size=10, weight="bold"),
            ).grid(
                row=0,
                column=0,
                padx=11,
                pady=(9, 0),
                sticky="w",
            )

            ctk.CTkLabel(
                item,
                text=str(
                    adapter.get(
                        "Beschreibung",
                        "Keine Beschreibung",
                    )
                ),
                anchor="w",
                text_color=Colors.MUTED,
                font=ctk.CTkFont(size=8),
            ).grid(
                row=1,
                column=0,
                padx=11,
                pady=(0, 8),
                sticky="w",
            )

            ctk.CTkLabel(
                item,
                text=str(
                    adapter.get(
                        "IPv4-Adresse",
                        "Keine IPv4-Adresse",
                    )
                ),
                anchor="e",
                text_color=Colors.TEXT,
                font=ctk.CTkFont(size=9, weight="bold"),
            ).grid(
                row=0,
                column=1,
                rowspan=2,
                padx=11,
                pady=19,
                sticky="e",
            )

    def _render_configuration(self) -> None:
        self._clear(self.configuration_content)

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
        )

        for row, (title, value) in enumerate(values):
            frame = ctk.CTkFrame(
                self.configuration_content,
                fg_color="transparent",
            )
            frame.grid(
                row=row,
                column=0,
                pady=4,
                sticky="ew",
            )
            frame.grid_columnconfigure(1, weight=1)

            ctk.CTkLabel(
                frame,
                text=title,
                width=112,
                anchor="w",
                text_color=Colors.MUTED,
                font=ctk.CTkFont(size=9),
            ).grid(row=0, column=0, sticky="w")

            ctk.CTkLabel(
                frame,
                text=str(value),
                anchor="w",
                justify="left",
                wraplength=280,
                text_color=Colors.TEXT,
                font=ctk.CTkFont(size=9, weight="bold"),
            ).grid(row=0, column=1, sticky="ew")

        messages = []
        messages.extend(self._messages(self.result.get("Warnungen", [])))
        messages.extend(self._messages(self.result.get("Hinweise", [])))

        note = ctk.CTkFrame(
            self.configuration_content,
            corner_radius=10,
            fg_color=(
                Colors.SURFACE_RAISED
                if messages
                else Colors.SUCCESS_SOFT
            ),
        )
        note.grid(
            row=len(values),
            column=0,
            pady=(10, 0),
            sticky="ew",
        )
        note.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            note,
            text=(
                "Hinweise"
                if messages
                else "Keine Auffälligkeiten"
            ),
            anchor="w",
            text_color=(
                Colors.TEXT
                if messages
                else Colors.SUCCESS
            ),
            font=ctk.CTkFont(size=9, weight="bold"),
        ).grid(
            row=0,
            column=0,
            padx=11,
            pady=(9, 2),
            sticky="w",
        )

        ctk.CTkLabel(
            note,
            text=(
                "\n".join(f"• {item}" for item in messages)
                if messages
                else "Die geprüften Netzwerkwerte sind unauffällig."
            ),
            anchor="w",
            justify="left",
            wraplength=380,
            text_color=Colors.MUTED,
            font=ctk.CTkFont(size=8),
        ).grid(
            row=1,
            column=0,
            padx=11,
            pady=(0, 9),
            sticky="ew",
        )

    @staticmethod
    def _messages(value: Any) -> list[str]:
        if isinstance(value, list):
            return [
                str(item).strip()
                for item in value
                if str(item).strip()
                and "Keine Auffälligkeit" not in str(item)
            ]

        text = str(value).strip()
        return [text] if text else []

    def _loss_summary(self) -> str:
        tests = self.result.get("Verbindungstests", [])
        losses: list[float] = []

        if isinstance(tests, list):
            for test in tests:
                if not isinstance(test, dict):
                    continue
                text = str(
                    test.get("Paketverlust", "")
                ).replace("%", "").strip()
                try:
                    losses.append(float(text.replace(",", ".")))
                except ValueError:
                    continue

        if not losses:
            return "Paketverlust nicht messbar"
        return f"{max(losses):g} % Paketverlust"

    @staticmethod
    def _translate_dhcp(value: Any) -> str:
        text = str(value or "").casefold()
        if text == "enabled":
            return "Aktiv"
        if text == "disabled":
            return "Deaktiviert"
        return "Nicht ermittelt"

    @staticmethod
    def _translate_profile(value: Any) -> str:
        text = str(value)
        translations = {
            "Public": "Öffentlich",
            "Private": "Privat",
            "DomainAuthenticated": "Domäne",
        }
        return translations.get(text, text)

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
            return "Netzwerkverbindung mit Hinweis"
        if rating == "WARNUNG":
            return "Netzwerkauffälligkeiten erkannt"
        if rating in {"KRITISCH", "FEHLER"}:
            return "Netzwerkprüfung nicht vollständig abgeschlossen"
        return "Netzwerkdaten wurden erfasst"

    @staticmethod
    def _clear(frame) -> None:
        for widget in frame.winfo_children():
            widget.destroy()

    def _placeholder(self, frame, text: str) -> None:
        self._clear(frame)

        ctk.CTkLabel(
            frame,
            text=text,
            anchor="w",
            justify="left",
            wraplength=480,
            text_color=Colors.MUTED,
            font=ctk.CTkFont(size=9),
        ).grid(
            row=0,
            column=0,
            columnspan=2,
            pady=12,
            sticky="ew",
        )

    def _scroll_to_top(self) -> None:
        def move() -> None:
            try:
                self.content._parent_canvas.yview_moveto(0)
            except (AttributeError, RuntimeError):
                pass

        self.after_idle(move)

    def _open_details(self) -> None:
        if not self.result:
            return

        rating = str(
            self.result.get("Bewertung", "INFO")
        ).upper()
        _, _, color = STATUS_STYLES.get(
            rating,
            STATUS_STYLES["INFO"],
        )

        ResultDetailWindow(
            master=self,
            title="Netzwerkprüfung",
            result=self.result,
            status_color=color,
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
