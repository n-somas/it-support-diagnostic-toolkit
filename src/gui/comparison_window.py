"""Fenster zum Vergleich zweier Diagnoseläufe."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from src.services.scan_comparison_service import ScanComparisonService
from src.services.scan_history_service import STATUSES, ScanHistoryService

CHANGE_STYLES = {
    "VERBESSERT": ("Verbessert", ("#15803D", "#22C55E")),
    "UNVERÄNDERT": ("Unverändert", ("#475569", "#94A3B8")),
    "VERSCHLECHTERT": ("Verschlechtert", ("#B91C1C", "#EF4444")),
    "NEU": ("Neu", ("#0369A1", "#38BDF8")),
    "ENTFERNT": ("Entfernt", ("#7E22CE", "#A855F7")),
}


class ComparisonWindow(ctk.CTkToplevel):
    def __init__(self, master, history_service: ScanHistoryService) -> None:
        super().__init__(master)
        self.history_service = history_service
        self.service = ScanComparisonService()
        self.scan_by_label = {}
        self.current = None

        self.title("Diagnoseläufe vergleichen")
        self.geometry("1100x800")
        self.minsize(900, 650)
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
        ).grid(row=0, column=0, padx=28, pady=(20, 3), sticky="w")
        ctk.CTkLabel(
            frame,
            text="Vergleicht zwei gespeicherte Diagnoseläufe.",
            text_color=("gray40", "gray70"),
        ).grid(row=1, column=0, padx=28, pady=(0, 18), sticky="w")

    def _create_body(self) -> None:
        body = ctk.CTkScrollableFrame(self, fg_color="transparent")
        body.grid(row=1, column=0, padx=14, pady=14, sticky="nsew")
        body.grid_columnconfigure(0, weight=1)

        selection = ctk.CTkFrame(body, corner_radius=12)
        selection.grid(row=0, column=0, padx=8, pady=(4, 12), sticky="ew")
        selection.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkLabel(selection, text="Älterer Scan").grid(
            row=0, column=0, padx=16, pady=(14, 5), sticky="w"
        )
        ctk.CTkLabel(selection, text="Neuerer Scan").grid(
            row=0, column=1, padx=16, pady=(14, 5), sticky="w"
        )

        self.old_menu = ctk.CTkOptionMenu(selection, values=["Keine Scans"])
        self.old_menu.grid(row=1, column=0, padx=16, pady=(0, 14), sticky="ew")
        self.new_menu = ctk.CTkOptionMenu(selection, values=["Keine Scans"])
        self.new_menu.grid(row=1, column=1, padx=16, pady=(0, 14), sticky="ew")

        actions = ctk.CTkFrame(selection, fg_color="transparent")
        actions.grid(row=2, column=0, columnspan=2, pady=(0, 16))
        self.compare_button = ctk.CTkButton(
            actions, text="Scans vergleichen", command=self._compare
        )
        self.compare_button.grid(row=0, column=0, padx=6)
        self.export_button = ctk.CTkButton(
            actions,
            text="Vergleich exportieren",
            state="disabled",
            command=self._export,
        )
        self.export_button.grid(row=0, column=1, padx=6)

        self.summary = ctk.CTkFrame(body, fg_color="transparent")
        self.summary.grid(row=1, column=0, padx=8, pady=(0, 12), sticky="ew")
        self.summary_labels = {}
        for column, change in enumerate(CHANGE_STYLES):
            self.summary.grid_columnconfigure(column, weight=1, uniform="sum")
            label, color = CHANGE_STYLES[change]
            card = ctk.CTkFrame(self.summary, corner_radius=10, border_width=1)
            card.grid(row=0, column=column, padx=4, sticky="ew")
            ctk.CTkFrame(card, height=5, fg_color=color).grid(
                row=0, column=0, padx=7, pady=(7, 3), sticky="ew"
            )
            value = ctk.CTkLabel(
                card, text="0", font=ctk.CTkFont(size=22, weight="bold")
            )
            value.grid(row=1, column=0)
            ctk.CTkLabel(card, text=label).grid(row=2, column=0, pady=(0, 9))
            card.grid_columnconfigure(0, weight=1)
            self.summary_labels[change] = value
        self.summary.grid_remove()

        self.chart_frame = ctk.CTkFrame(body, corner_radius=12)
        self.chart_frame.grid(row=2, column=0, padx=8, pady=(0, 12), sticky="ew")
        self.chart_frame.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            self.chart_frame,
            text="Statusvergleich",
            font=ctk.CTkFont(size=17, weight="bold"),
        ).grid(row=0, column=0, padx=18, pady=(14, 3), sticky="w")

        self.figure = Figure(figsize=(8.5, 2.8), dpi=100)
        self.axes = self.figure.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.chart_frame)
        widget = self.canvas.get_tk_widget()
        widget.configure(height=280)
        widget.grid(row=1, column=0, padx=12, pady=(0, 12), sticky="ew")
        self.chart_frame.grid_remove()

        self.results_section = ctk.CTkFrame(body, corner_radius=12)
        self.results_section.grid(
            row=3, column=0, padx=8, pady=(0, 16), sticky="ew"
        )
        self.results_section.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            self.results_section,
            text="Änderungen nach Diagnosebereich",
            font=ctk.CTkFont(size=17, weight="bold"),
        ).grid(row=0, column=0, padx=18, pady=(14, 8), sticky="w")
        self.results = ctk.CTkFrame(self.results_section, fg_color="transparent")
        self.results.grid(row=1, column=0, padx=10, pady=(0, 12), sticky="ew")
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
                "Führe nach dem Upgrade zwei neue Diagnosen aus.",
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
        old_scan = self.scan_by_label.get(self.old_menu.get())
        new_scan = self.scan_by_label.get(self.new_menu.get())
        if not old_scan or not new_scan:
            return
        if old_scan["_path"] == new_scan["_path"]:
            messagebox.showwarning(
                "Gleicher Scan",
                "Wähle zwei unterschiedliche Scans.",
                parent=self,
            )
            return
        if old_scan.get("created_at", "") > new_scan.get("created_at", ""):
            old_scan, new_scan = new_scan, old_scan

        self.current = self.service.compare(old_scan, new_scan)
        self._render_summary()
        self._render_chart()
        self._render_items()
        self.summary.grid()
        self.chart_frame.grid()
        self.results_section.grid()
        self.export_button.configure(state="normal")

    def _render_summary(self) -> None:
        for change, label in self.summary_labels.items():
            label.configure(text=str(self.current["summary"].get(change, 0)))

    def _render_chart(self) -> None:
        self.axes.clear()
        dark = ctk.get_appearance_mode() == "Dark"
        bg = "#2B2B2B" if dark else "#F7F7F7"
        fg = "#F3F4F6" if dark else "#1F2937"
        self.figure.patch.set_facecolor(bg)
        self.axes.set_facecolor(bg)

        positions = list(range(len(STATUSES)))
        width = 0.36
        old_values = [
            int(self.current["old_status_counts"].get(status, 0))
            for status in STATUSES
        ]
        new_values = [
            int(self.current["new_status_counts"].get(status, 0))
            for status in STATUSES
        ]
        self.axes.bar(
            [p - width / 2 for p in positions],
            old_values,
            width,
            label="Älterer Scan",
            color="#64748B",
        )
        self.axes.bar(
            [p + width / 2 for p in positions],
            new_values,
            width,
            label="Neuerer Scan",
            color="#3B82F6",
        )
        self.axes.set_xticks(
            positions,
            ["OK", "Info", "Hinweis", "Warnung", "Kritisch", "Fehler"],
        )
        self.axes.set_ylabel("Anzahl")
        self.axes.grid(axis="y", alpha=0.16)
        self.axes.tick_params(colors=fg)
        self.axes.yaxis.label.set_color(fg)
        for spine in self.axes.spines.values():
            spine.set_visible(False)
        self.axes.legend(frameon=False, labelcolor=fg)
        self.figure.tight_layout(pad=1.1)
        self.canvas.draw_idle()

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
            key=lambda item: (order.get(item.change, 9), item.title),
        )

        for row, item in enumerate(items):
            label, color = CHANGE_STYLES[item.change]
            card = ctk.CTkFrame(self.results, corner_radius=9, border_width=1)
            card.grid(row=row, column=0, padx=6, pady=5, sticky="ew")
            card.grid_columnconfigure(0, weight=1)
            ctk.CTkLabel(
                card,
                text=item.title,
                anchor="w",
                font=ctk.CTkFont(size=14, weight="bold"),
            ).grid(row=0, column=0, padx=12, pady=(10, 2), sticky="w")
            ctk.CTkLabel(
                card,
                text=f"{item.old_status}  →  {item.new_status}",
                anchor="w",
                text_color=("gray40", "gray70"),
            ).grid(row=1, column=0, padx=12, pady=(0, 10), sticky="w")
            ctk.CTkLabel(
                card,
                text=label,
                width=140,
                fg_color=color,
                corner_radius=7,
                font=ctk.CTkFont(size=11, weight="bold"),
            ).grid(row=0, column=1, rowspan=2, padx=12, pady=12)

    def _export(self) -> None:
        path = filedialog.asksaveasfilename(
            parent=self,
            title="Diagnosevergleich speichern",
            defaultextension=".md",
            filetypes=[("Markdown", "*.md"), ("Text", "*.txt")],
            initialfile="Diagnosevergleich.md",
        )
        if not path:
            return

        lines = [
            "# Vergleich zweier Diagnoseläufe",
            "",
            f"Älterer Scan: {self.current['old_created_at']}",
            f"Neuerer Scan: {self.current['new_created_at']}",
            "",
            "## Zusammenfassung",
            "",
        ]
        for change, count in self.current["summary"].items():
            lines.append(f"- {CHANGE_STYLES[change][0]}: {count}")

        lines += [
            "",
            "## Änderungen",
            "",
            "| Diagnosebereich | Vorher | Nachher | Änderung |",
            "|---|---|---|---|",
        ]
        for item in self.current["items"]:
            lines.append(
                f"| {item.title} | {item.old_status} | "
                f"{item.new_status} | {CHANGE_STYLES[item.change][0]} |"
            )

        Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")
        messagebox.showinfo(
            "Gespeichert",
            f"Vergleich gespeichert:\n\n{path}",
            parent=self,
        )

    @staticmethod
    def _label(scan: dict) -> str:
        value = str(scan.get("created_at", ""))
        try:
            formatted = datetime.fromisoformat(value).strftime("%d.%m.%Y %H:%M:%S")
        except ValueError:
            formatted = value or scan.get("_filename", "Scan")
        return f"{formatted} | {scan.get('_filename', '')}"
