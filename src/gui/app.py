import threading

import customtkinter as ctk

from src.diagnostic_runner import run_all_diagnostics
from src.gui.result_card import ResultCard


class DiagnosticApp(ctk.CTk):
    """Hauptfenster des IT Support Diagnostic Toolkit."""

    def __init__(self) -> None:
        super().__init__()

        self.title("IT Support Diagnostic Toolkit")
        self.geometry("980x760")
        self.minsize(820, 620)

        ctk.set_appearance_mode("system")
        ctk.set_default_color_theme("blue")

        self.diagnostic_results: list[tuple[str, dict]] = []

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
        """Erstellt Steuerung, Fortschritt und Ergebnisbereich."""

        content = ctk.CTkFrame(self)
        content.grid(
            row=1,
            column=0,
            padx=24,
            pady=24,
            sticky="nsew",
        )
        content.grid_columnconfigure(0, weight=1)
        content.grid_rowconfigure(4, weight=1)

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

        self.results_frame = ctk.CTkScrollableFrame(
            content,
            label_text="Diagnoseergebnisse",
        )
        self.results_frame.grid(
            row=4,
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

    def _start_scan(self) -> None:
        """Startet die Diagnose in einem Hintergrund-Thread."""

        self._clear_results()

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
        """Zeigt die Ergebnisse nach abgeschlossener Diagnose an."""

        self.diagnostic_results = results

        self.progress_bar.set(1)

        error_count = sum(
            1
            for _, result in results
            if self._get_rating(result) == "FEHLER"
        )

        warning_count = sum(
            1
            for _, result in results
            if self._get_rating(result) in {
                "WARNUNG",
                "KRITISCH",
            }
        )

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

        self._display_results(results)

        self.scan_button.configure(
            state="normal",
            text="Erneut prüfen",
        )

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

        return str(
            result.get(
                "Bewertung",
                result.get("Status", "INFO"),
            )
        ).upper()

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