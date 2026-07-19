import os
import threading
from collections import Counter
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk

from src.diagnostic_runner import run_all_diagnostics
from src.gui.components.charts.status_bar_chart import StatusBarChart
from src.gui.result_card import ResultCard
from src.report.markdown_report import save_markdown_report


SUMMARY_STYLES = {
    "OK": {
        "color": ("#2E7D32", "#4CAF50"),
        "label": "OK",
    },
    "INFO": {
        "color": ("#1565C0", "#42A5F5"),
        "label": "Info",
    },
    "HINWEIS": {
        "color": ("#6A1B9A", "#AB47BC"),
        "label": "Hinweise",
    },
    "WARNUNG": {
        "color": ("#EF6C00", "#FFA726"),
        "label": "Warnungen",
    },
    "KRITISCH": {
        "color": ("#C62828", "#EF5350"),
        "label": "Kritisch",
    },
    "FEHLER": {
        "color": ("#8E0000", "#D32F2F"),
        "label": "Fehler",
    },
}


class DiagnosticApp(ctk.CTk):
    """Hauptfenster des IT Support Diagnostic Toolkit."""

    def __init__(self) -> None:
        super().__init__()

        self.title("IT Support Diagnostic Toolkit")
        self.geometry("1050x840")
        self.minsize(860, 680)

        ctk.set_appearance_mode("system")
        ctk.set_default_color_theme("blue")

        self.diagnostic_results: list[tuple[str, dict]] = []
        self.summary_value_labels: dict[str, ctk.CTkLabel] = {}
        self.latest_report_path: Path | None = None

        self._create_layout()

    def _create_layout(self) -> None:
        """Erstellt die grundlegenden Elemente des Hauptfensters."""

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._create_header()
        self._create_content()

    def _create_header(self) -> None:
        """Erstellt den Kopfbereich der Anwendung."""

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
            text="IT Support Diagnostic Toolkit",
            font=ctk.CTkFont(
                size=26,
                weight="bold",
            ),
        )
        title_label.grid(
            row=0,
            column=0,
            padx=30,
            pady=(22, 4),
        )

        subtitle_label = ctk.CTkLabel(
            header,
            text="Windows-Systemdiagnose",
            font=ctk.CTkFont(size=15),
        )
        subtitle_label.grid(
            row=1,
            column=0,
            padx=30,
            pady=(0, 22),
        )

    def _create_content(self) -> None:
        """Erstellt Steuerung, Dashboard und Ergebnisbereich."""

        content = ctk.CTkFrame(self)
        content.grid(
            row=1,
            column=0,
            padx=24,
            pady=24,
            sticky="nsew",
        )
        content.grid_columnconfigure(0, weight=1)
        content.grid_rowconfigure(6, weight=1)

        self.status_label = ctk.CTkLabel(
            content,
            text="System wurde noch nicht geprüft.",
            font=ctk.CTkFont(size=18),
        )
        self.status_label.grid(
            row=0,
            column=0,
            padx=20,
            pady=(20, 12),
        )

        self.scan_button = ctk.CTkButton(
            content,
            text="Diagnose starten",
            width=220,
            height=46,
            font=ctk.CTkFont(
                size=16,
                weight="bold",
            ),
            command=self._start_scan,
        )
        self.scan_button.grid(
            row=1,
            column=0,
            padx=20,
            pady=12,
        )

        self.progress_bar = ctk.CTkProgressBar(
            content,
            width=440,
        )
        self.progress_bar.grid(
            row=2,
            column=0,
            padx=20,
            pady=12,
        )
        self.progress_bar.set(0)

        self.result_label = ctk.CTkLabel(
            content,
            text="Bereit",
            font=ctk.CTkFont(size=14),
        )
        self.result_label.grid(
            row=3,
            column=0,
            padx=20,
            pady=(4, 14),
        )

        self._create_summary_dashboard(content)
        self._create_report_actions(content)

        self.results_frame = ctk.CTkScrollableFrame(
            content,
            label_text="Diagnoseergebnisse",
        )
        self.results_frame.grid(
            row=6,
            column=0,
            padx=20,
            pady=(6, 20),
            sticky="nsew",
        )
        self.results_frame.grid_columnconfigure(
            0,
            weight=1,
        )

        self.empty_results_label = ctk.CTkLabel(
            self.results_frame,
            text="Nach einer Diagnose werden hier die Ergebnisse angezeigt.",
        )
        self.empty_results_label.grid(
            row=0,
            column=0,
            padx=20,
            pady=40,
        )

    def _create_summary_dashboard(self, master) -> None:
        """Erstellt die kompakte Statusübersicht."""

        self.summary_frame = ctk.CTkFrame(
            master,
            corner_radius=10,
        )
        self.summary_frame.grid(
            row=4,
            column=0,
            padx=20,
            pady=(0, 12),
            sticky="ew",
        )

        statuses = list(SUMMARY_STYLES.keys())

        for column_index, status in enumerate(statuses):
            self.summary_frame.grid_columnconfigure(
                column_index,
                weight=1,
                uniform="summary",
            )

            style = SUMMARY_STYLES[status]

            card = ctk.CTkFrame(
                self.summary_frame,
                corner_radius=9,
                border_width=1,
            )
            card.grid(
                row=0,
                column=column_index,
                padx=6,
                pady=10,
                sticky="ew",
            )
            card.grid_columnconfigure(0, weight=1)

            indicator = ctk.CTkFrame(
                card,
                height=5,
                corner_radius=4,
                fg_color=style["color"],
            )
            indicator.grid(
                row=0,
                column=0,
                padx=8,
                pady=(8, 4),
                sticky="ew",
            )

            value_label = ctk.CTkLabel(
                card,
                text="0",
                font=ctk.CTkFont(
                    size=24,
                    weight="bold",
                ),
            )
            value_label.grid(
                row=1,
                column=0,
                padx=10,
                pady=(2, 0),
            )

            description_label = ctk.CTkLabel(
                card,
                text=style["label"],
                font=ctk.CTkFont(size=12),
            )
            description_label.grid(
                row=2,
                column=0,
                padx=10,
                pady=(0, 10),
            )

            self.summary_value_labels[status] = value_label

        self.status_chart = StatusBarChart(
            self.summary_frame,
        )
        self.status_chart.grid(
            row=1,
            column=0,
            columnspan=len(statuses),
            padx=6,
            pady=(0, 10),
            sticky="ew",
        )
        self.status_chart.grid_remove()

        self.summary_frame.grid_remove()

    def _create_report_actions(self, master) -> None:
        """Erstellt die Schaltflächen für den Diagnosebericht."""

        self.report_actions_frame = ctk.CTkFrame(
            master,
            fg_color="transparent",
        )
        self.report_actions_frame.grid(
            row=5,
            column=0,
            padx=20,
            pady=(0, 12),
        )

        self.open_report_button = ctk.CTkButton(
            self.report_actions_frame,
            text="Bericht öffnen",
            width=170,
            height=38,
            state="disabled",
            command=self._open_report,
        )
        self.open_report_button.grid(
            row=0,
            column=0,
            padx=6,
        )

        self.save_report_button = ctk.CTkButton(
            self.report_actions_frame,
            text="Bericht speichern unter",
            width=190,
            height=38,
            state="disabled",
            command=self._save_report_as,
        )
        self.save_report_button.grid(
            row=0,
            column=1,
            padx=6,
        )

        self.report_path_label = ctk.CTkLabel(
            master,
            text="",
            font=ctk.CTkFont(size=12),
        )
        self.report_path_label.grid(
            row=7,
            column=0,
            padx=20,
            pady=(0, 10),
        )

        self.report_actions_frame.grid_remove()
        self.report_path_label.grid_remove()

    def _start_scan(self) -> None:
        """Startet die Diagnose in einem Hintergrund-Thread."""

        self._clear_results()
        self._reset_summary_dashboard()

        self.summary_frame.grid_remove()
        self.report_actions_frame.grid_remove()
        self.report_path_label.grid_remove()

        self.latest_report_path = None

        self.open_report_button.configure(state="disabled")
        self.save_report_button.configure(state="disabled")

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
        """Führt die Diagnose außerhalb des GUI-Hauptthreads aus."""

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
        """Überträgt den Fortschritt an den GUI-Hauptthread."""

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
        """Aktualisiert Fortschrittsbalken und Statustext."""

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
        """Zeigt Ergebnisse und Bericht nach abgeschlossener Diagnose an."""

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
        self._display_results(results)
        self._create_default_report(results)

        self.scan_button.configure(
            state="normal",
            text="Erneut prüfen",
        )

    def _create_default_report(
        self,
        results: list[tuple[str, dict]],
    ) -> None:
        """Speichert nach dem Scan automatisch einen Markdown-Bericht."""

        try:
            report_path = save_markdown_report(
                results,
                file_path="reports/support_report.md",
            )

            self.latest_report_path = Path(report_path).resolve()

            self.open_report_button.configure(state="normal")
            self.save_report_button.configure(state="normal")

            self.report_actions_frame.grid()

            self.report_path_label.configure(
                text=f"Bericht erstellt: {self.latest_report_path}"
            )
            self.report_path_label.grid()

        except Exception as error:
            self.latest_report_path = None

            self.report_path_label.configure(
                text=f"Bericht konnte nicht erstellt werden: {error}"
            )
            self.report_path_label.grid()

    def _open_report(self) -> None:
        """Öffnet den zuletzt erstellten Bericht im Standardprogramm."""

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
        """Speichert den aktuellen Bericht an einem ausgewählten Ort."""

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

            self.latest_report_path = Path(saved_path).resolve()

            self.open_report_button.configure(state="normal")

            self.report_path_label.configure(
                text=f"Bericht gespeichert: {self.latest_report_path}"
            )
            self.report_path_label.grid()

            messagebox.showinfo(
                "Bericht gespeichert",
                f"Der Diagnosebericht wurde gespeichert.\n\n"
                f"{self.latest_report_path}",
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
        """Zählt sämtliche Statuswerte der Diagnose."""

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
        """Aktualisiert die Werte im Status-Dashboard."""

        for status, value_label in self.summary_value_labels.items():
            value_label.configure(
                text=str(status_counts.get(status, 0))
            )

        self.status_chart.update_data(status_counts)
        self.status_chart.grid()
        self.summary_frame.grid()

    def _reset_summary_dashboard(self) -> None:
        """Setzt die Werte des Status-Dashboards zurück."""

        for value_label in self.summary_value_labels.values():
            value_label.configure(text="0")

        self.status_chart.clear()
        self.status_chart.grid_remove()

    def _display_results(
        self,
        results: list[tuple[str, dict]],
    ) -> None:
        """Erstellt für jeden Diagnosebereich eine Ergebniskarte."""

        self._clear_results()

        for row_index, (title, result) in enumerate(results):
            card = ResultCard(
                self.results_frame,
                title=title,
                result=result,
            )
            card.grid(
                row=row_index,
                column=0,
                padx=10,
                pady=7,
                sticky="ew",
            )

    def _clear_results(self) -> None:
        """Entfernt alle bisherigen Elemente aus dem Ergebnisbereich."""

        for widget in self.results_frame.winfo_children():
            widget.destroy()

    @staticmethod
    def _get_rating(result: dict) -> str:
        """Liest den Status eines Diagnoseergebnisses aus."""

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
        """Erstellt die Zusammenfassung des Scanergebnisses."""

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
        """Zeigt einen Fehler des gesamten Scanvorgangs an."""

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
    """Startet die grafische Benutzeroberfläche."""

    app = DiagnosticApp()
    app.mainloop()


if __name__ == "__main__":
    run_app()