"""Moderne Mehrseiten-Oberfläche des IT Support Diagnostic Toolkit."""

from __future__ import annotations

import os
import threading
from collections import Counter
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk

from src.diagnostic_runner import run_all_diagnostics
from src.gui.comparison_window import ComparisonWindow
from src.gui.components.charts.status_bar_chart import StatusBarChart
from src.gui.components.dashboard_extra_charts import (
    DiskUsageChart,
    HistoryChart,
)
from src.gui.result_card import ResultCard
from src.gui.theme import Colors
from src.report.markdown_report import save_markdown_report
from src.services.scan_history_service import ScanHistoryService


SUMMARY_STYLES = {
    "OK": {
        "color": ("#15803D", "#22C55E"),
        "label": "OK",
    },
    "INFO": {
        "color": ("#1D4ED8", "#3B82F6"),
        "label": "Info",
    },
    "HINWEIS": {
        "color": ("#7E22CE", "#A855F7"),
        "label": "Hinweise",
    },
    "WARNUNG": {
        "color": ("#C2410C", "#F59E0B"),
        "label": "Warnungen",
    },
    "KRITISCH": {
        "color": ("#B91C1C", "#EF4444"),
        "label": "Kritisch",
    },
    "FEHLER": {
        "color": ("#991B1B", "#DC2626"),
        "label": "Fehler",
    },
}

PAGE_TITLES = {
    "dashboard": (
        "Übersicht",
        "Systemzustand, Diagnose und wichtigste Kennzahlen",
    ),
    "results": (
        "Diagnoseergebnisse",
        "Prüfbereiche filtern und Details gezielt öffnen",
    ),
    "history": (
        "Verlauf und Vergleich",
        "Entwicklung der letzten Diagnosen nachvollziehen",
    ),
    "reports": (
        "Berichte",
        "Diagnoseberichte öffnen, speichern und weitergeben",
    ),
}


class DiagnosticApp(ctk.CTk):
    """Hauptfenster mit fester Navigation und getrennten Arbeitsbereichen."""

    def __init__(self) -> None:
        super().__init__()

        ctk.set_appearance_mode("system")
        ctk.set_default_color_theme("blue")

        self.title("IT Support Diagnostic Toolkit")
        self.geometry("1320x850")
        self.minsize(1080, 720)

        self.configure(
            fg_color=("#F3F6FA", "#111827"),
        )

        self.diagnostic_results: list[tuple[str, dict]] = []
        self.summary_value_labels: dict[str, ctk.CTkLabel] = {}
        self.summary_cards: dict[str, ctk.CTkFrame] = {}
        self.result_filter_buttons: dict[str, ctk.CTkButton] = {}
        self.navigation_buttons: dict[str, ctk.CTkButton] = {}
        self.pages: dict[str, ctk.CTkFrame] = {}

        self.active_page = "dashboard"
        self.active_status_filter: str | None = None
        self.latest_report_path: Path | None = None
        self.history_service = ScanHistoryService()

        self._create_layout()
        self._show_page("dashboard")
        self._load_history_overview()

    def _create_layout(self) -> None:
        self.grid_columnconfigure(0, minsize=230)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._create_sidebar()
        self._create_page_container()
        self._create_dashboard_page()
        self._create_results_page()
        self._create_history_page()
        self._create_reports_page()

    def _create_sidebar(self) -> None:
        self.sidebar = ctk.CTkFrame(
            self,
            width=230,
            corner_radius=0,
            fg_color=("#0F172A", "#0B1220"),
        )
        self.sidebar.grid(
            row=0,
            column=0,
            sticky="nsew",
        )
        self.sidebar.grid_propagate(False)
        self.sidebar.grid_columnconfigure(0, weight=1)
        self.sidebar.grid_rowconfigure(8, weight=1)

        brand = ctk.CTkFrame(
            self.sidebar,
            fg_color="transparent",
        )
        brand.grid(
            row=0,
            column=0,
            padx=20,
            pady=(24, 26),
            sticky="ew",
        )

        ctk.CTkLabel(
            brand,
            text="IT SUPPORT",
            anchor="w",
            text_color="#93C5FD",
            font=ctk.CTkFont(
                size=12,
                weight="bold",
            ),
        ).grid(
            row=0,
            column=0,
            sticky="w",
        )

        ctk.CTkLabel(
            brand,
            text="Diagnostic\nToolkit",
            anchor="w",
            justify="left",
            text_color="#F8FAFC",
            font=ctk.CTkFont(
                size=25,
                weight="bold",
            ),
        ).grid(
            row=1,
            column=0,
            pady=(3, 0),
            sticky="w",
        )

        nav_entries = (
            ("dashboard", "Übersicht"),
            ("results", "Ergebnisse"),
            ("history", "Verlauf & Vergleich"),
            ("reports", "Berichte"),
        )

        for row, (page_key, label) in enumerate(
            nav_entries,
            start=1,
        ):
            button = ctk.CTkButton(
                self.sidebar,
                text=label,
                height=44,
                anchor="w",
                corner_radius=8,
                fg_color="transparent",
                hover_color=("#1E293B", "#1E293B"),
                text_color="#E2E8F0",
                font=ctk.CTkFont(
                    size=14,
                    weight="bold",
                ),
                command=lambda selected=page_key: (
                    self._show_page(selected)
                ),
            )
            button.grid(
                row=row,
                column=0,
                padx=14,
                pady=4,
                sticky="ew",
            )
            self.navigation_buttons[page_key] = button

        separator = ctk.CTkFrame(
            self.sidebar,
            height=1,
            fg_color="#334155",
        )
        separator.grid(
            row=6,
            column=0,
            padx=18,
            pady=(22, 18),
            sticky="ew",
        )

        ctk.CTkLabel(
            self.sidebar,
            text="Darstellung",
            anchor="w",
            text_color="#94A3B8",
            font=ctk.CTkFont(size=12),
        ).grid(
            row=7,
            column=0,
            padx=20,
            pady=(0, 7),
            sticky="ew",
        )

        self.appearance_menu = ctk.CTkOptionMenu(
            self.sidebar,
            values=["System", "Hell", "Dunkel"],
            command=self._change_appearance,
            fg_color="#1E293B",
            button_color="#334155",
            button_hover_color="#475569",
        )
        self.appearance_menu.grid(
            row=8,
            column=0,
            padx=16,
            sticky="new",
        )
        self.appearance_menu.set("System")

        footer = ctk.CTkLabel(
            self.sidebar,
            text="Windows-Diagnose\nLokale Ausführung",
            justify="left",
            anchor="w",
            text_color="#64748B",
            font=ctk.CTkFont(size=11),
        )
        footer.grid(
            row=9,
            column=0,
            padx=20,
            pady=20,
            sticky="sw",
        )

    def _create_page_container(self) -> None:
        self.page_container = ctk.CTkFrame(
            self,
            corner_radius=0,
            fg_color="transparent",
        )
        self.page_container.grid(
            row=0,
            column=1,
            sticky="nsew",
        )
        self.page_container.grid_columnconfigure(0, weight=1)
        self.page_container.grid_rowconfigure(0, weight=1)

    def _new_page(self, key: str) -> ctk.CTkFrame:
        page = ctk.CTkFrame(
            self.page_container,
            fg_color="transparent",
        )
        page.grid(
            row=0,
            column=0,
            padx=24,
            pady=20,
            sticky="nsew",
        )
        page.grid_columnconfigure(0, weight=1)
        page.grid_rowconfigure(1, weight=1)
        page.grid_remove()

        self.pages[key] = page
        return page

    def _create_page_header(
        self,
        master,
        page_key: str,
        action_text: str | None = None,
        action_command=None,
    ) -> ctk.CTkFrame:
        title, subtitle = PAGE_TITLES[page_key]

        header = ctk.CTkFrame(
            master,
            fg_color="transparent",
        )
        header.grid(
            row=0,
            column=0,
            pady=(0, 16),
            sticky="ew",
        )
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header,
            text=title,
            anchor="w",
            text_color=Colors.TEXT,
            font=ctk.CTkFont(
                size=27,
                weight="bold",
            ),
        ).grid(
            row=0,
            column=0,
            sticky="w",
        )

        ctk.CTkLabel(
            header,
            text=subtitle,
            anchor="w",
            text_color=Colors.MUTED,
            font=ctk.CTkFont(size=13),
        ).grid(
            row=1,
            column=0,
            pady=(3, 0),
            sticky="w",
        )

        if action_text and action_command:
            ctk.CTkButton(
                header,
                text=action_text,
                height=38,
                width=170,
                font=ctk.CTkFont(
                    size=13,
                    weight="bold",
                ),
                command=action_command,
            ).grid(
                row=0,
                column=1,
                rowspan=2,
                padx=(16, 0),
                sticky="e",
            )

        return header

    def _create_dashboard_page(self) -> None:
        page = self._new_page("dashboard")
        self._create_page_header(
            page,
            "dashboard",
            action_text="Diagnose starten",
            action_command=self._start_scan,
        )

        body = ctk.CTkFrame(
            page,
            fg_color="transparent",
        )
        body.grid(
            row=1,
            column=0,
            sticky="nsew",
        )
        body.grid_columnconfigure(0, weight=1)
        body.grid_rowconfigure(3, weight=1)

        self._create_scan_panel(body)
        self._create_summary_cards(body)
        self._create_dashboard_charts(body)

    def _create_scan_panel(self, master) -> None:
        panel = ctk.CTkFrame(
            master,
            corner_radius=14,
            border_width=1,
            border_color=Colors.BORDER,
            fg_color=Colors.SURFACE,
        )
        panel.grid(
            row=0,
            column=0,
            pady=(0, 14),
            sticky="ew",
        )
        panel.grid_columnconfigure(0, weight=1)

        self.status_label = ctk.CTkLabel(
            panel,
            text="System wurde noch nicht geprüft.",
            anchor="w",
            text_color=Colors.TEXT,
            font=ctk.CTkFont(
                size=18,
                weight="bold",
            ),
        )
        self.status_label.grid(
            row=0,
            column=0,
            padx=20,
            pady=(18, 2),
            sticky="w",
        )

        self.result_label = ctk.CTkLabel(
            panel,
            text=(
                "Starte eine Diagnose, um den aktuellen "
                "Windows-Systemzustand zu erfassen."
            ),
            anchor="w",
            text_color=Colors.MUTED,
            font=ctk.CTkFont(size=13),
        )
        self.result_label.grid(
            row=1,
            column=0,
            padx=20,
            pady=(0, 12),
            sticky="w",
        )

        self.progress_bar = ctk.CTkProgressBar(
            panel,
            height=8,
        )
        self.progress_bar.grid(
            row=2,
            column=0,
            padx=20,
            pady=(0, 18),
            sticky="ew",
        )
        self.progress_bar.set(0)

        self.scan_button = ctk.CTkButton(
            panel,
            text="Diagnose starten",
            width=180,
            height=42,
            font=ctk.CTkFont(
                size=14,
                weight="bold",
            ),
            command=self._start_scan,
        )
        self.scan_button.grid(
            row=0,
            column=1,
            rowspan=3,
            padx=20,
            pady=18,
            sticky="e",
        )

    def _create_summary_cards(self, master) -> None:
        self.summary_frame = ctk.CTkFrame(
            master,
            fg_color="transparent",
        )
        self.summary_frame.grid(
            row=1,
            column=0,
            pady=(0, 14),
            sticky="ew",
        )

        statuses = list(SUMMARY_STYLES)

        for column_index, status in enumerate(statuses):
            self.summary_frame.grid_columnconfigure(
                column_index,
                weight=1,
                uniform="status",
            )

            style = SUMMARY_STYLES[status]

            card = ctk.CTkFrame(
                self.summary_frame,
                height=104,
                corner_radius=12,
                border_width=1,
                border_color=Colors.BORDER,
                fg_color=Colors.SURFACE,
            )
            card.grid(
                row=0,
                column=column_index,
                padx=(0 if column_index == 0 else 5, 5),
                sticky="ew",
            )
            card.grid_propagate(False)
            card.grid_columnconfigure(0, weight=1)

            ctk.CTkFrame(
                card,
                height=5,
                corner_radius=4,
                fg_color=style["color"],
            ).grid(
                row=0,
                column=0,
                padx=10,
                pady=(10, 4),
                sticky="ew",
            )

            value_label = ctk.CTkLabel(
                card,
                text="0",
                text_color=Colors.TEXT,
                font=ctk.CTkFont(
                    size=25,
                    weight="bold",
                ),
            )
            value_label.grid(
                row=1,
                column=0,
                pady=(0, 0),
            )

            ctk.CTkLabel(
                card,
                text=style["label"],
                text_color=Colors.MUTED,
                font=ctk.CTkFont(size=12),
            ).grid(
                row=2,
                column=0,
                pady=(0, 8),
            )

            self.summary_value_labels[status] = value_label
            self.summary_cards[status] = card
            self._bind_status_card(card, status)

    def _create_dashboard_charts(self, master) -> None:
        charts = ctk.CTkFrame(
            master,
            fg_color="transparent",
        )
        charts.grid(
            row=2,
            column=0,
            sticky="nsew",
        )
        charts.grid_columnconfigure((0, 1), weight=1)
        charts.grid_rowconfigure(0, weight=1)

        self.status_chart = StatusBarChart(charts)
        self.status_chart.grid(
            row=0,
            column=0,
            padx=(0, 7),
            sticky="nsew",
        )

        self.disk_chart = DiskUsageChart(charts)
        self.disk_chart.grid(
            row=0,
            column=1,
            padx=(7, 0),
            sticky="nsew",
        )

    def _create_results_page(self) -> None:
        page = self._new_page("results")
        self._create_page_header(
            page,
            "results",
            action_text="Neu prüfen",
            action_command=self._start_scan,
        )

        body = ctk.CTkFrame(
            page,
            fg_color="transparent",
        )
        body.grid(
            row=1,
            column=0,
            sticky="nsew",
        )
        body.grid_columnconfigure(0, weight=1)
        body.grid_rowconfigure(2, weight=1)

        filter_bar = ctk.CTkFrame(
            body,
            corner_radius=12,
            border_width=1,
            border_color=Colors.BORDER,
            fg_color=Colors.SURFACE,
        )
        filter_bar.grid(
            row=0,
            column=0,
            pady=(0, 10),
            sticky="ew",
        )
        filter_bar.grid_columnconfigure(7, weight=1)

        ctk.CTkLabel(
            filter_bar,
            text="Filter",
            text_color=Colors.TEXT,
            font=ctk.CTkFont(
                size=13,
                weight="bold",
            ),
        ).grid(
            row=0,
            column=0,
            padx=(14, 8),
            pady=12,
        )

        all_button = ctk.CTkButton(
            filter_bar,
            text="Alle",
            width=72,
            height=31,
            corner_radius=7,
            command=lambda: self._set_status_filter(None),
        )
        all_button.grid(
            row=0,
            column=1,
            padx=3,
            pady=10,
        )
        self.result_filter_buttons["ALL"] = all_button

        for column, status in enumerate(
            SUMMARY_STYLES,
            start=2,
        ):
            button = ctk.CTkButton(
                filter_bar,
                text=SUMMARY_STYLES[status]["label"],
                width=90,
                height=31,
                corner_radius=7,
                fg_color="transparent",
                border_width=1,
                border_color=Colors.BORDER,
                text_color=Colors.TEXT,
                hover_color=("#E2E8F0", "#334155"),
                command=lambda selected=status: (
                    self._set_status_filter(selected)
                ),
            )
            button.grid(
                row=0,
                column=column,
                padx=3,
                pady=10,
            )
            self.result_filter_buttons[status] = button

        self.results_overview_label = ctk.CTkLabel(
            body,
            text="Noch keine Diagnoseergebnisse vorhanden.",
            anchor="w",
            text_color=Colors.MUTED,
            font=ctk.CTkFont(size=13),
        )
        self.results_overview_label.grid(
            row=1,
            column=0,
            pady=(0, 8),
            sticky="w",
        )

        self.results_frame = ctk.CTkScrollableFrame(
            body,
            corner_radius=12,
            border_width=1,
            border_color=Colors.BORDER,
            fg_color=Colors.SURFACE,
        )
        self.results_frame.grid(
            row=2,
            column=0,
            sticky="nsew",
        )
        self.results_frame.grid_columnconfigure(0, weight=1)

        self._show_results_placeholder()
        self._update_filter_buttons()

    def _create_history_page(self) -> None:
        page = self._new_page("history")
        self._create_page_header(
            page,
            "history",
            action_text="Scans vergleichen",
            action_command=self._open_comparison,
        )

        body = ctk.CTkFrame(
            page,
            fg_color="transparent",
        )
        body.grid(
            row=1,
            column=0,
            sticky="nsew",
        )
        body.grid_columnconfigure(0, weight=1)
        body.grid_rowconfigure(0, weight=1)

        self.history_chart = HistoryChart(body)
        self.history_chart.grid(
            row=0,
            column=0,
            sticky="nsew",
        )

        info = ctk.CTkFrame(
            body,
            corner_radius=12,
            border_width=1,
            border_color=Colors.BORDER,
            fg_color=Colors.SURFACE,
        )
        info.grid(
            row=1,
            column=0,
            pady=(14, 0),
            sticky="ew",
        )
        info.grid_columnconfigure(0, weight=1)

        self.history_count_label = ctk.CTkLabel(
            info,
            text="Noch keine gespeicherten Diagnosen.",
            anchor="w",
            text_color=Colors.TEXT,
            font=ctk.CTkFont(
                size=14,
                weight="bold",
            ),
        )
        self.history_count_label.grid(
            row=0,
            column=0,
            padx=18,
            pady=(14, 3),
            sticky="w",
        )

        ctk.CTkLabel(
            info,
            text=(
                "Für einen Vergleich werden mindestens zwei "
                "Diagnoseläufe mit Detaildaten benötigt."
            ),
            anchor="w",
            text_color=Colors.MUTED,
            font=ctk.CTkFont(size=12),
        ).grid(
            row=1,
            column=0,
            padx=18,
            pady=(0, 14),
            sticky="w",
        )

        ctk.CTkButton(
            info,
            text="Diagnosen vergleichen",
            width=190,
            height=38,
            command=self._open_comparison,
        ).grid(
            row=0,
            column=1,
            rowspan=2,
            padx=18,
            pady=14,
        )

    def _create_reports_page(self) -> None:
        page = self._new_page("reports")
        self._create_page_header(
            page,
            "reports",
        )

        body = ctk.CTkFrame(
            page,
            fg_color="transparent",
        )
        body.grid(
            row=1,
            column=0,
            sticky="nsew",
        )
        body.grid_columnconfigure(0, weight=1)

        report_card = ctk.CTkFrame(
            body,
            corner_radius=14,
            border_width=1,
            border_color=Colors.BORDER,
            fg_color=Colors.SURFACE,
        )
        report_card.grid(
            row=0,
            column=0,
            sticky="ew",
        )
        report_card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            report_card,
            text="Aktueller Diagnosebericht",
            anchor="w",
            text_color=Colors.TEXT,
            font=ctk.CTkFont(
                size=18,
                weight="bold",
            ),
        ).grid(
            row=0,
            column=0,
            padx=20,
            pady=(20, 4),
            sticky="w",
        )

        self.report_path_label = ctk.CTkLabel(
            report_card,
            text=(
                "Noch kein Bericht vorhanden. Nach einer Diagnose "
                "wird automatisch ein Markdown-Bericht erstellt."
            ),
            anchor="w",
            justify="left",
            wraplength=720,
            text_color=Colors.MUTED,
            font=ctk.CTkFont(size=13),
        )
        self.report_path_label.grid(
            row=1,
            column=0,
            padx=20,
            pady=(0, 18),
            sticky="ew",
        )

        actions = ctk.CTkFrame(
            report_card,
            fg_color="transparent",
        )
        actions.grid(
            row=2,
            column=0,
            padx=14,
            pady=(0, 20),
            sticky="w",
        )

        self.open_report_button = ctk.CTkButton(
            actions,
            text="Bericht öffnen",
            width=165,
            height=40,
            state="disabled",
            command=self._open_report,
        )
        self.open_report_button.grid(
            row=0,
            column=0,
            padx=6,
        )

        self.save_report_button = ctk.CTkButton(
            actions,
            text="Speichern unter",
            width=165,
            height=40,
            state="disabled",
            command=self._save_report_as,
        )
        self.save_report_button.grid(
            row=0,
            column=1,
            padx=6,
        )

        ctk.CTkButton(
            actions,
            text="Vergleichsbericht",
            width=165,
            height=40,
            command=self._open_comparison,
        ).grid(
            row=0,
            column=2,
            padx=6,
        )

        hint_card = ctk.CTkFrame(
            body,
            corner_radius=12,
            border_width=1,
            border_color=Colors.BORDER,
            fg_color=Colors.SURFACE,
        )
        hint_card.grid(
            row=1,
            column=0,
            pady=(14, 0),
            sticky="ew",
        )

        ctk.CTkLabel(
            hint_card,
            text="Berichtsworkflow",
            anchor="w",
            text_color=Colors.TEXT,
            font=ctk.CTkFont(
                size=15,
                weight="bold",
            ),
        ).grid(
            row=0,
            column=0,
            padx=18,
            pady=(16, 5),
            sticky="w",
        )

        ctk.CTkLabel(
            hint_card,
            text=(
                "1. Diagnose durchführen    "
                "2. Ergebnisse prüfen    "
                "3. Bericht speichern oder zwei Scans vergleichen"
            ),
            anchor="w",
            text_color=Colors.MUTED,
            font=ctk.CTkFont(size=13),
        ).grid(
            row=1,
            column=0,
            padx=18,
            pady=(0, 16),
            sticky="w",
        )

    def _show_page(self, page_key: str) -> None:
        if page_key not in self.pages:
            return

        for page in self.pages.values():
            page.grid_remove()

        self.pages[page_key].grid()
        self.active_page = page_key

        for key, button in self.navigation_buttons.items():
            is_active = key == page_key
            button.configure(
                fg_color=(
                    "#2563EB"
                    if is_active
                    else "transparent"
                ),
                hover_color=(
                    "#1D4ED8"
                    if is_active
                    else "#1E293B"
                ),
                text_color="#FFFFFF" if is_active else "#E2E8F0",
            )

    def _change_appearance(self, value: str) -> None:
        mapping = {
            "System": "system",
            "Hell": "light",
            "Dunkel": "dark",
        }
        ctk.set_appearance_mode(
            mapping.get(value, "system")
        )
        self.after(100, self._refresh_charts)

    def _refresh_charts(self) -> None:
        if self.diagnostic_results:
            counts = self._count_statuses(
                self.diagnostic_results
            )
            self.status_chart.update_data(counts)
            self.disk_chart.update_results(
                self.diagnostic_results
            )
        else:
            self.status_chart.clear()
            self.disk_chart.show_empty(
                "Noch keine Speicherwerte vorhanden."
            )

        self._load_history_overview()

    def _start_scan(self) -> None:
        self._show_page("dashboard")
        self._clear_results()
        self._show_results_placeholder(
            "Diagnose wird ausgeführt. Ergebnisse erscheinen "
            "nach Abschluss."
        )
        self._reset_summary_dashboard()

        self.active_status_filter = None
        self._update_filter_buttons()
        self.latest_report_path = None

        self.open_report_button.configure(state="disabled")
        self.save_report_button.configure(state="disabled")
        self.report_path_label.configure(
            text=(
                "Die Diagnose läuft. Der Bericht wird nach "
                "Abschluss automatisch erstellt."
            )
        )

        self.scan_button.configure(
            state="disabled",
            text="Diagnose läuft ...",
        )
        self.status_label.configure(
            text="Systemdiagnose wird ausgeführt."
        )
        self.result_label.configure(
            text="Prüfungen werden vorbereitet ..."
        )
        self.progress_bar.set(0)
        self.diagnostic_results = []

        scan_thread = threading.Thread(
            target=self._run_scan,
            daemon=True,
        )
        scan_thread.start()

    def _run_scan(self) -> None:
        try:
            results = run_all_diagnostics(
                progress_callback=self._report_progress,
            )
            self.after(
                0,
                lambda: self._scan_finished(results),
            )
        except Exception as error:
            error_message = str(error)
            self.after(
                0,
                lambda: self._scan_failed(error_message),
            )

    def _report_progress(
        self,
        title: str,
        current_step: int,
        total_steps: int,
    ) -> None:
        progress = current_step / total_steps
        self.after(
            0,
            lambda: self._update_progress(
                title,
                current_step,
                total_steps,
                progress,
            ),
        )

    def _update_progress(
        self,
        title: str,
        current_step: int,
        total_steps: int,
        progress: float,
    ) -> None:
        self.progress_bar.set(progress)
        self.result_label.configure(
            text=(
                f"Prüfe {title} ... "
                f"({current_step} von {total_steps})"
            )
        )

    def _scan_finished(
        self,
        results: list[tuple[str, dict]],
    ) -> None:
        self.diagnostic_results = results
        self.progress_bar.set(1)

        status_counts = self._count_statuses(results)
        warning_count = (
            status_counts["WARNUNG"]
            + status_counts["KRITISCH"]
        )
        error_count = status_counts["FEHLER"]

        self.status_label.configure(
            text="Systemdiagnose abgeschlossen."
        )
        self.result_label.configure(
            text=self._create_summary_text(
                result_count=len(results),
                warning_count=warning_count,
                error_count=error_count,
            )
        )

        self._update_summary_dashboard(status_counts)
        self.active_status_filter = None
        self._update_filter_buttons()
        self._display_results(results)

        try:
            self.history_service.save(results)
        except OSError:
            pass

        self.disk_chart.update_results(results)
        self._load_history_overview()
        self._create_default_report(results)

        self.scan_button.configure(
            state="normal",
            text="Erneut prüfen",
        )

    def _create_default_report(
        self,
        results: list[tuple[str, dict]],
    ) -> None:
        try:
            report_path = save_markdown_report(
                results,
                file_path="reports/support_report.md",
            )
            self.latest_report_path = Path(
                report_path
            ).resolve()

            self.open_report_button.configure(state="normal")
            self.save_report_button.configure(state="normal")
            self.report_path_label.configure(
                text=(
                    "Bericht wurde automatisch erstellt.\n\n"
                    f"{self.latest_report_path}"
                )
            )
        except Exception as error:
            self.latest_report_path = None
            self.report_path_label.configure(
                text=(
                    "Bericht konnte nicht erstellt werden.\n\n"
                    f"{error}"
                )
            )

    def _load_history_overview(self) -> None:
        records = self.history_service.load_recent(
            limit=10
        )
        self.history_chart.update_records(records)

        total = len(
            self.history_service.list_scans()
        )
        if total == 0:
            text = "Noch keine gespeicherten Diagnosen."
        elif total == 1:
            text = "1 Diagnose ist lokal gespeichert."
        else:
            text = f"{total} Diagnosen sind lokal gespeichert."

        self.history_count_label.configure(text=text)

    def _open_comparison(self) -> None:
        ComparisonWindow(
            self,
            history_service=self.history_service,
        )

    def _open_report(self) -> None:
        if self.latest_report_path is None:
            messagebox.showwarning(
                "Kein Bericht",
                "Es wurde noch kein Diagnosebericht erstellt.",
            )
            return

        if not self.latest_report_path.exists():
            messagebox.showerror(
                "Datei nicht gefunden",
                "Der Diagnosebericht wurde nicht gefunden.",
            )
            return

        try:
            os.startfile(self.latest_report_path)
        except OSError as error:
            messagebox.showerror(
                "Bericht konnte nicht geöffnet werden",
                str(error),
            )

    def _save_report_as(self) -> None:
        if not self.diagnostic_results:
            messagebox.showwarning(
                "Keine Ergebnisse",
                "Führe zuerst eine Systemdiagnose durch.",
            )
            return

        selected_path = filedialog.asksaveasfilename(
            title="Diagnosebericht speichern",
            defaultextension=".md",
            filetypes=[
                ("Markdown-Bericht", "*.md"),
                ("Textdatei", "*.txt"),
                ("Alle Dateien", "*.*"),
            ],
            initialfile="IT-Support-Diagnosebericht.md",
        )

        if not selected_path:
            return

        try:
            saved_path = save_markdown_report(
                self.diagnostic_results,
                file_path=selected_path,
            )
            self.latest_report_path = Path(
                saved_path
            ).resolve()
            self.open_report_button.configure(state="normal")
            self.report_path_label.configure(
                text=(
                    "Bericht wurde gespeichert.\n\n"
                    f"{self.latest_report_path}"
                )
            )
            messagebox.showinfo(
                "Bericht gespeichert",
                (
                    "Der Diagnosebericht wurde gespeichert.\n\n"
                    f"{self.latest_report_path}"
                ),
            )
        except Exception as error:
            messagebox.showerror(
                "Speichern fehlgeschlagen",
                str(error),
            )

    def _count_statuses(
        self,
        results: list[tuple[str, dict]],
    ) -> Counter:
        status_counts = Counter(
            self._get_rating(result)
            for _, result in results
        )

        for status in SUMMARY_STYLES:
            status_counts.setdefault(status, 0)

        return status_counts

    def _update_summary_dashboard(
        self,
        status_counts: Counter,
    ) -> None:
        for status, value_label in (
            self.summary_value_labels.items()
        ):
            value_label.configure(
                text=str(
                    status_counts.get(status, 0)
                )
            )

        self.status_chart.update_data(status_counts)

    def _reset_summary_dashboard(self) -> None:
        for value_label in (
            self.summary_value_labels.values()
        ):
            value_label.configure(text="0")

        self.status_chart.clear()
        self.disk_chart.show_empty(
            "Noch keine Speicherwerte vorhanden."
        )

    def _bind_status_card(
        self,
        widget,
        status: str,
    ) -> None:
        widget.bind(
            "<Button-1>",
            lambda event, selected_status=status: (
                self._toggle_status_filter(
                    selected_status
                )
            ),
        )

        try:
            widget.configure(cursor="hand2")
        except (TypeError, ValueError):
            pass

        for child in widget.winfo_children():
            self._bind_status_card(child, status)

    def _toggle_status_filter(
        self,
        status: str,
    ) -> None:
        if not self.diagnostic_results:
            return

        if self.active_status_filter == status:
            self.active_status_filter = None
        else:
            self.active_status_filter = status

        self._apply_result_filter()
        self._show_page("results")

    def _set_status_filter(
        self,
        status: str | None,
    ) -> None:
        self.active_status_filter = status
        self._apply_result_filter()

    def _apply_result_filter(self) -> None:
        if not self.diagnostic_results:
            self._show_results_placeholder()
            self._update_filter_buttons()
            return

        if self.active_status_filter is None:
            filtered_results = self.diagnostic_results
        else:
            filtered_results = [
                (title, result)
                for title, result in self.diagnostic_results
                if self._get_rating(result)
                == self.active_status_filter
            ]

        self._update_filter_buttons()
        self._display_results(filtered_results)

    def _update_filter_buttons(self) -> None:
        active_key = (
            self.active_status_filter
            if self.active_status_filter
            else "ALL"
        )

        for key, button in (
            self.result_filter_buttons.items()
        ):
            active = key == active_key
            accent = (
                "#2563EB"
                if key == "ALL"
                else SUMMARY_STYLES[key]["color"]
            )

            button.configure(
                fg_color=accent if active else "transparent",
                text_color="#FFFFFF" if active else Colors.TEXT,
                border_width=0 if active else 1,
            )

    def _display_results(
        self,
        results: list[tuple[str, dict]],
    ) -> None:
        self._clear_results()

        total = len(self.diagnostic_results)
        visible = len(results)

        if self.active_status_filter:
            label = SUMMARY_STYLES[
                self.active_status_filter
            ]["label"]
            self.results_overview_label.configure(
                text=(
                    f"{visible} von {total} Prüfungen angezeigt "
                    f"– Filter: {label}"
                )
            )
        else:
            self.results_overview_label.configure(
                text=f"{visible} Diagnosebereiche angezeigt."
            )

        if not results:
            self._show_results_placeholder(
                "Für diesen Filter sind keine Ergebnisse vorhanden."
            )
            return

        for row_index, (title, result) in enumerate(
            results
        ):
            card = ResultCard(
                self.results_frame,
                title=title,
                result=result,
            )
            card.grid(
                row=row_index,
                column=0,
                padx=8,
                pady=6,
                sticky="ew",
            )

    def _show_results_placeholder(
        self,
        text: str = (
            "Nach einer Diagnose werden hier die "
            "Prüfbereiche angezeigt."
        ),
    ) -> None:
        self._clear_results()
        ctk.CTkLabel(
            self.results_frame,
            text=text,
            text_color=Colors.MUTED,
            font=ctk.CTkFont(size=14),
        ).grid(
            row=0,
            column=0,
            padx=20,
            pady=50,
        )

    def _clear_results(self) -> None:
        for widget in self.results_frame.winfo_children():
            widget.destroy()

    @staticmethod
    def _get_rating(result: dict) -> str:
        rating = result.get(
            "Bewertung",
            result.get("Status", "INFO"),
        )
        normalized_rating = str(rating).upper()

        if normalized_rating not in SUMMARY_STYLES:
            return "INFO"

        return normalized_rating

    @staticmethod
    def _create_summary_text(
        result_count: int,
        warning_count: int,
        error_count: int,
    ) -> str:
        if error_count > 0:
            return (
                f"{result_count} Prüfungen abgeschlossen. "
                f"{error_count} Fehler und "
                f"{warning_count} Warnungen erkannt."
            )

        if warning_count > 0:
            return (
                f"{result_count} Prüfungen abgeschlossen. "
                f"{warning_count} Warnungen erkannt."
            )

        return (
            f"{result_count} Prüfungen wurden erfolgreich ausgeführt."
        )

    def _scan_failed(self, error_message: str) -> None:
        self.status_label.configure(
            text="Die Systemdiagnose wurde abgebrochen."
        )
        self.result_label.configure(
            text=f"Fehler: {error_message}"
        )
        self.scan_button.configure(
            state="normal",
            text="Erneut versuchen",
        )


def run_app() -> None:
    app = DiagnosticApp()
    app.mainloop()


if __name__ == "__main__":
    run_app()
