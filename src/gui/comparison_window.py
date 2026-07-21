"""Fenster zum Vergleich zweier Diagnoseläufe."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from src.report.comparison_report import save_comparison_report
from src.services.scan_comparison_service import (
    ComparisonItem,
    ScanComparisonService,
)
from src.services.scan_history_service import (
    STATUSES,
    ScanHistoryService,
)


CHANGE_STYLES = {
    "VERBESSERT": ("Verbessert", ("#15803D", "#22C55E")),
    "UNVERÄNDERT": ("Unverändert", ("#475569", "#94A3B8")),
    "VERSCHLECHTERT": (
        "Verschlechtert",
        ("#B91C1C", "#EF4444"),
    ),
    "NEU": ("Neu", ("#0369A1", "#38BDF8")),
    "ENTFERNT": ("Entfernt", ("#7E22CE", "#A855F7")),
}


class ComparisonWindow(ctk.CTkToplevel):
    def __init__(
        self,
        master,
        history_service: ScanHistoryService,
    ) -> None:
        super().__init__(master)

        self.history_service = history_service
        self.service = ScanComparisonService()
        self.scan_by_label: dict[str, dict] = {}
        self.current: dict | None = None
        self.only_changes = True
        self.expanded_titles: set[str] = set()

        self.title("Diagnoseläufe vergleichen")
        self.geometry("1160x840")
        self.minsize(920, 680)
        self.transient(master)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._create_header()
        self._create_body()
        self._load_options()

    def _create_header(self) -> None:
        frame = ctk.CTkFrame(self, corner_radius=0)
        frame.grid(row=0, column=0, sticky="ew")

        ctk.CTkLabel(
            frame,
            text="Diagnosevergleich",
            font=ctk.CTkFont(size=25, weight="bold"),
        ).grid(
            row=0,
            column=0,
            padx=28,
            pady=(20, 3),
            sticky="w",
        )

        ctk.CTkLabel(
            frame,
            text=(
                "Vergleicht Status und einzelne Messwerte "
                "zweier Diagnoseläufe."
            ),
            text_color=("gray40", "gray70"),
        ).grid(
            row=1,
            column=0,
            padx=28,
            pady=(0, 18),
            sticky="w",
        )

    def _create_body(self) -> None:
        body = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
        )
        body.grid(
            row=1,
            column=0,
            padx=14,
            pady=14,
            sticky="nsew",
        )
        body.grid_columnconfigure(0, weight=1)

        self._create_selection(body)
        self._create_summary(body)
        self._create_chart(body)
        self._create_results(body)

    def _create_selection(self, body) -> None:
        selection = ctk.CTkFrame(body, corner_radius=12)
        selection.grid(
            row=0,
            column=0,
            padx=8,
            pady=(4, 12),
            sticky="ew",
        )
        selection.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkLabel(
            selection,
            text="Älterer Scan",
            font=ctk.CTkFont(weight="bold"),
        ).grid(
            row=0,
            column=0,
            padx=16,
            pady=(14, 5),
            sticky="w",
        )

        ctk.CTkLabel(
            selection,
            text="Neuerer Scan",
            font=ctk.CTkFont(weight="bold"),
        ).grid(
            row=0,
            column=1,
            padx=16,
            pady=(14, 5),
            sticky="w",
        )

        self.old_menu = ctk.CTkOptionMenu(
            selection,
            values=["Keine Scans"],
        )
        self.old_menu.grid(
            row=1,
            column=0,
            padx=16,
            pady=(0, 14),
            sticky="ew",
        )

        self.new_menu = ctk.CTkOptionMenu(
            selection,
            values=["Keine Scans"],
        )
        self.new_menu.grid(
            row=1,
            column=1,
            padx=16,
            pady=(0, 14),
            sticky="ew",
        )

        actions = ctk.CTkFrame(
            selection,
            fg_color="transparent",
        )
        actions.grid(
            row=2,
            column=0,
            columnspan=2,
            pady=(0, 16),
        )

        self.compare_button = ctk.CTkButton(
            actions,
            text="Scans vergleichen",
            width=180,
            command=self._compare,
        )
        self.compare_button.grid(
            row=0,
            column=0,
            padx=6,
        )

        self.export_button = ctk.CTkButton(
            actions,
            text="Professionellen Bericht exportieren",
            width=180,
            state="disabled",
            command=self._export,
        )
        self.export_button.grid(
            row=0,
            column=1,
            padx=6,
        )

    def _create_summary(self, body) -> None:
        self.summary = ctk.CTkFrame(
            body,
            fg_color="transparent",
        )
        self.summary.grid(
            row=1,
            column=0,
            padx=8,
            pady=(0, 12),
            sticky="ew",
        )
        self.summary_labels = {}

        for column, change in enumerate(CHANGE_STYLES):
            self.summary.grid_columnconfigure(
                column,
                weight=1,
                uniform="sum",
            )

            label, color = CHANGE_STYLES[change]
            card = ctk.CTkFrame(
                self.summary,
                corner_radius=10,
                border_width=1,
            )
            card.grid(
                row=0,
                column=column,
                padx=4,
                sticky="ew",
            )
            card.grid_columnconfigure(0, weight=1)

            ctk.CTkFrame(
                card,
                height=5,
                fg_color=color,
            ).grid(
                row=0,
                column=0,
                padx=7,
                pady=(7, 3),
                sticky="ew",
            )

            value = ctk.CTkLabel(
                card,
                text="0",
                font=ctk.CTkFont(
                    size=22,
                    weight="bold",
                ),
            )
            value.grid(row=1, column=0)

            ctk.CTkLabel(
                card,
                text=label,
            ).grid(
                row=2,
                column=0,
                pady=(0, 9),
            )

            self.summary_labels[change] = value

        self.summary.grid_remove()

    def _create_chart(self, body) -> None:
        self.chart_frame = ctk.CTkFrame(
            body,
            corner_radius=12,
        )
        self.chart_frame.grid(
            row=2,
            column=0,
            padx=8,
            pady=(0, 12),
            sticky="ew",
        )
        self.chart_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            self.chart_frame,
            text="Statusvergleich",
            font=ctk.CTkFont(
                size=17,
                weight="bold",
            ),
        ).grid(
            row=0,
            column=0,
            padx=18,
            pady=(14, 3),
            sticky="w",
        )

        self.figure = Figure(
            figsize=(8.5, 2.8),
            dpi=100,
        )
        self.axes = self.figure.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(
            self.figure,
            master=self.chart_frame,
        )

        widget = self.canvas.get_tk_widget()
        widget.configure(height=280)
        widget.grid(
            row=1,
            column=0,
            padx=12,
            pady=(0, 12),
            sticky="ew",
        )

        self.chart_frame.grid_remove()

    def _create_results(self, body) -> None:
        self.results_section = ctk.CTkFrame(
            body,
            corner_radius=12,
        )
        self.results_section.grid(
            row=3,
            column=0,
            padx=8,
            pady=(0, 16),
            sticky="ew",
        )
        self.results_section.grid_columnconfigure(0, weight=1)

        title_row = ctk.CTkFrame(
            self.results_section,
            fg_color="transparent",
        )
        title_row.grid(
            row=0,
            column=0,
            padx=18,
            pady=(14, 8),
            sticky="ew",
        )
        title_row.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            title_row,
            text="Änderungen nach Diagnosebereich",
            font=ctk.CTkFont(
                size=17,
                weight="bold",
            ),
        ).grid(
            row=0,
            column=0,
            sticky="w",
        )

        self.filter_switch = ctk.CTkSwitch(
            title_row,
            text="Nur geänderte Werte",
            command=self._toggle_detail_filter,
        )
        self.filter_switch.grid(
            row=0,
            column=1,
            sticky="e",
        )
        self.filter_switch.select()

        self.feedback_label = ctk.CTkLabel(
            self.results_section,
            text="",
            anchor="w",
            justify="left",
            font=ctk.CTkFont(
                size=13,
                weight="bold",
            ),
        )
        self.feedback_label.grid(
            row=1,
            column=0,
            padx=18,
            pady=(0, 8),
            sticky="ew",
        )
        self.feedback_label.grid_remove()

        self.results = ctk.CTkFrame(
            self.results_section,
            fg_color="transparent",
        )
        self.results.grid(
            row=2,
            column=0,
            padx=10,
            pady=(0, 12),
            sticky="ew",
        )
        self.results.grid_columnconfigure(0, weight=1)

        self.results_section.grid_remove()

    def _load_options(self) -> None:
        scans = [
            scan
            for scan in self.history_service.list_scans()
            if scan.get("_has_details")
        ]

        if len(scans) < 2:
            self.compare_button.configure(state="disabled")
            messagebox.showinfo(
                "Zwei neue Scans erforderlich",
                "Führe zwei Diagnosen im neuen Format aus.",
                parent=self,
            )
            return

        labels = []

        for scan in scans:
            label = self._label(scan)
            labels.append(label)
            self.scan_by_label[label] = scan

        self.old_menu.configure(values=labels)
        self.new_menu.configure(values=labels)
        self.old_menu.set(labels[-1])
        self.new_menu.set(labels[0])

    def _compare(self) -> None:
        old_scan = self.scan_by_label.get(
            self.old_menu.get()
        )
        new_scan = self.scan_by_label.get(
            self.new_menu.get()
        )

        if not old_scan or not new_scan:
            return

        if old_scan["_path"] == new_scan["_path"]:
            messagebox.showwarning(
                "Gleicher Scan",
                "Wähle zwei unterschiedliche Scans.",
                parent=self,
            )
            return

        if old_scan.get("created_at", "") > new_scan.get(
            "created_at",
            "",
        ):
            old_scan, new_scan = new_scan, old_scan

        self.current = self.service.compare(
            old_scan,
            new_scan,
        )

        changed_items = [
            item
            for item in self.current["items"]
            if item.changed_detail_count > 0
        ]

        if self.only_changes:
            self.expanded_titles = {
                item.title
                for item in changed_items
            }
        else:
            self.expanded_titles.clear()

        total_changed_values = sum(
            item.changed_detail_count
            for item in self.current["items"]
        )

        if total_changed_values == 0:
            self.feedback_label.configure(
                text=(
                    "Zwischen den ausgewählten Scans wurden "
                    "keine Detailwerte verändert."
                ),
                text_color=("#475569", "#CBD5E1"),
            )
        else:
            changed_areas = len(changed_items)
            self.feedback_label.configure(
                text=(
                    f"{total_changed_values} geänderte Detailwerte "
                    f"in {changed_areas} Diagnosebereichen gefunden."
                ),
                text_color=("#166534", "#86EFAC"),
            )

        self.feedback_label.grid()

        self._render_summary()
        self._render_chart()
        self._render_items()

        self.summary.grid()
        self.chart_frame.grid()
        self.results_section.grid()
        self.export_button.configure(state="normal")

    def _render_summary(self) -> None:
        for change, label in self.summary_labels.items():
            label.configure(
                text=str(
                    self.current["summary"].get(change, 0)
                )
            )

    def _render_chart(self) -> None:
        self.axes.clear()

        dark = ctk.get_appearance_mode() == "Dark"
        background = "#2B2B2B" if dark else "#F7F7F7"
        foreground = "#F3F4F6" if dark else "#1F2937"

        self.figure.patch.set_facecolor(background)
        self.axes.set_facecolor(background)

        positions = list(range(len(STATUSES)))
        width = 0.36

        old_values = [
            int(
                self.current["old_status_counts"].get(
                    status,
                    0,
                )
            )
            for status in STATUSES
        ]
        new_values = [
            int(
                self.current["new_status_counts"].get(
                    status,
                    0,
                )
            )
            for status in STATUSES
        ]

        self.axes.bar(
            [position - width / 2 for position in positions],
            old_values,
            width,
            label="Älterer Scan",
            color="#64748B",
        )
        self.axes.bar(
            [position + width / 2 for position in positions],
            new_values,
            width,
            label="Neuerer Scan",
            color="#3B82F6",
        )

        self.axes.set_xticks(
            positions,
            [
                "OK",
                "Info",
                "Hinweis",
                "Warnung",
                "Kritisch",
                "Fehler",
            ],
        )
        self.axes.set_ylabel("Anzahl")
        self.axes.grid(axis="y", alpha=0.16)
        self.axes.set_axisbelow(True)
        self.axes.tick_params(colors=foreground)
        self.axes.yaxis.label.set_color(foreground)

        for spine in self.axes.spines.values():
            spine.set_visible(False)

        self.axes.legend(
            frameon=False,
            labelcolor=foreground,
        )
        self.figure.tight_layout(pad=1.1)
        self.canvas.draw_idle()

    def _toggle_detail_filter(self) -> None:
        self.only_changes = bool(
            self.filter_switch.get()
        )

        if not self.current:
            return

        if self.only_changes:
            self.expanded_titles = {
                item.title
                for item in self.current["items"]
                if item.changed_detail_count > 0
            }

        self._render_items()

    def _render_items(self) -> None:
        for widget in self.results.winfo_children():
            widget.destroy()

        order = {
            "VERSCHLECHTERT": 0,
            "VERBESSERT": 1,
            "NEU": 2,
            "ENTFERNT": 3,
            "UNVERÄNDERT": 4,
        }

        items = sorted(
            self.current["items"],
            key=lambda item: (
                order.get(item.change, 9),
                item.title,
            ),
        )

        for row, item in enumerate(items):
            self._create_comparison_card(
                row,
                item,
            )

    def _create_comparison_card(
        self,
        row: int,
        item: ComparisonItem,
    ) -> None:
        label, color = CHANGE_STYLES[item.change]
        card = ctk.CTkFrame(
            self.results,
            corner_radius=9,
            border_width=1,
        )
        card.grid(
            row=row,
            column=0,
            padx=6,
            pady=5,
            sticky="ew",
        )
        card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            card,
            text=item.title,
            anchor="w",
            font=ctk.CTkFont(
                size=14,
                weight="bold",
            ),
        ).grid(
            row=0,
            column=0,
            padx=12,
            pady=(10, 2),
            sticky="w",
        )

        ctk.CTkLabel(
            card,
            text=(
                f"{item.old_status}  →  {item.new_status}   "
                f"|   {item.changed_detail_count} "
                f"geänderte Werte"
            ),
            anchor="w",
            text_color=("gray40", "gray70"),
        ).grid(
            row=1,
            column=0,
            padx=12,
            pady=(0, 10),
            sticky="w",
        )

        ctk.CTkLabel(
            card,
            text=label,
            width=140,
            fg_color=color,
            corner_radius=7,
            font=ctk.CTkFont(
                size=11,
                weight="bold",
            ),
        ).grid(
            row=0,
            column=1,
            rowspan=2,
            padx=(8, 6),
            pady=12,
        )

        button_text = (
            "Details ausblenden"
            if item.title in self.expanded_titles
            else "Details anzeigen"
        )

        ctk.CTkButton(
            card,
            text=button_text,
            width=145,
            command=lambda selected=item: (
                self._toggle_item_details(selected)
            ),
        ).grid(
            row=0,
            column=2,
            rowspan=2,
            padx=(6, 12),
            pady=12,
        )

        if item.title in self.expanded_titles:
            self._create_detail_table(
                card,
                item,
            )

    def _toggle_item_details(
        self,
        item: ComparisonItem,
    ) -> None:
        if item.title in self.expanded_titles:
            self.expanded_titles.remove(item.title)
        else:
            self.expanded_titles.add(item.title)

        self._render_items()

    def _create_detail_table(
        self,
        card,
        item: ComparisonItem,
    ) -> None:
        details = [
            detail
            for detail in item.detail_changes
            if detail.changed or not self.only_changes
        ]

        table = ctk.CTkFrame(
            card,
            corner_radius=7,
            fg_color=("gray92", "gray18"),
        )
        table.grid(
            row=2,
            column=0,
            columnspan=3,
            padx=12,
            pady=(0, 12),
            sticky="ew",
        )
        table.grid_columnconfigure(0, weight=2)
        table.grid_columnconfigure(1, weight=2)
        table.grid_columnconfigure(2, weight=2)

        headers = (
            "Eigenschaft",
            "Älterer Scan",
            "Neuerer Scan",
        )

        for column, text in enumerate(headers):
            ctk.CTkLabel(
                table,
                text=text,
                anchor="w",
                font=ctk.CTkFont(
                    size=12,
                    weight="bold",
                ),
            ).grid(
                row=0,
                column=column,
                padx=10,
                pady=(9, 6),
                sticky="ew",
            )

        if not details:
            ctk.CTkLabel(
                table,
                text=(
                    "Keine geänderten Detailwerte vorhanden."
                    if self.only_changes
                    else "Keine Detailwerte vorhanden."
                ),
                text_color=("gray40", "gray70"),
            ).grid(
                row=1,
                column=0,
                columnspan=3,
                padx=10,
                pady=14,
            )
            return

        for row, detail in enumerate(details, start=1):
            text_color = (
                ("#9A3412", "#FDBA74")
                if detail.changed
                else ("gray35", "gray70")
            )

            values = (
                detail.path,
                detail.old_value,
                detail.new_value,
            )

            for column, value in enumerate(values):
                ctk.CTkLabel(
                    table,
                    text=value,
                    anchor="w",
                    justify="left",
                    wraplength=300,
                    text_color=text_color,
                ).grid(
                    row=row,
                    column=column,
                    padx=10,
                    pady=5,
                    sticky="ew",
                )

    def _export(self) -> None:
        """Exportiert einen priorisierten Markdown-Vergleichsbericht."""

        if not self.current:
            return

        suggested_name = (
            "IT-Support-Diagnosevergleich_"
            f"{datetime.now().strftime('%Y-%m-%d_%H-%M')}.md"
        )

        path = filedialog.asksaveasfilename(
            parent=self,
            title="Professionellen Diagnosevergleich speichern",
            defaultextension=".md",
            filetypes=[
                ("Markdown-Bericht", "*.md"),
                ("Textdatei", "*.txt"),
            ],
            initialfile=suggested_name,
        )

        if not path:
            return

        try:
            saved_path = save_comparison_report(
                self.current,
                path,
            )
        except OSError as error:
            messagebox.showerror(
                "Export fehlgeschlagen",
                str(error),
                parent=self,
            )
            return

        messagebox.showinfo(
            "Vergleichsbericht gespeichert",
            (
                "Der professionelle Vergleichsbericht "
                "wurde gespeichert.\n\n"
                f"{saved_path}"
            ),
            parent=self,
        )

    @staticmethod
    def _escape(value: str) -> str:
        return value.replace("|", "\\|").replace("\n", "<br>")

    @staticmethod
    def _label(scan: dict) -> str:
        value = str(scan.get("created_at", ""))

        try:
            created = datetime.fromisoformat(value)
            text = created.strftime("%d.%m.%Y %H:%M:%S")
        except ValueError:
            text = value or scan.get(
                "_filename",
                "Unbekannter Scan",
            )

        return f"{text} | {scan.get('_filename', '')}"
