import threading

import customtkinter as ctk

from src.diagnostic_runner import run_all_diagnostics


class DiagnosticApp(ctk.CTk):
    """Hauptfenster des IT Support Diagnostic Toolkit."""

    def __init__(self) -> None:
        super().__init__()

        self.title("IT Support Diagnostic Toolkit")
        self.geometry("900x600")
        self.minsize(760, 500)

        ctk.set_appearance_mode("system")
        ctk.set_default_color_theme("blue")

        self.diagnostic_results: list[tuple[str, dict]] = []

        self._create_layout()

    def _create_layout(self) -> None:
        """Erstellt die grundlegenden Elemente des Hauptfensters."""

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(self, corner_radius=0)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(0, weight=1)

        title_label = ctk.CTkLabel(
            header,
            text="IT Support Diagnostic Toolkit",
            font=ctk.CTkFont(size=26, weight="bold"),
        )
        title_label.grid(row=0, column=0, padx=30, pady=(24, 4))

        subtitle_label = ctk.CTkLabel(
            header,
            text="Windows-Systemdiagnose",
            font=ctk.CTkFont(size=15),
        )
        subtitle_label.grid(row=1, column=0, padx=30, pady=(0, 24))

        content = ctk.CTkFrame(self)
        content.grid(row=1, column=0, padx=30, pady=30, sticky="nsew")
        content.grid_columnconfigure(0, weight=1)
        content.grid_rowconfigure(0, weight=1)

        self.status_label = ctk.CTkLabel(
            content,
            text="System wurde noch nicht geprüft.",
            font=ctk.CTkFont(size=18),
        )
        self.status_label.grid(row=0, column=0, padx=20, pady=(80, 20))

        self.scan_button = ctk.CTkButton(
            content,
            text="Diagnose starten",
            width=220,
            height=48,
            font=ctk.CTkFont(size=16, weight="bold"),
            command=self._start_scan,
        )
        self.scan_button.grid(row=1, column=0, padx=20, pady=20)

        self.progress_bar = ctk.CTkProgressBar(content, width=400)
        self.progress_bar.grid(row=2, column=0, padx=20, pady=20)
        self.progress_bar.set(0)

        self.result_label = ctk.CTkLabel(
            content,
            text="Bereit",
            font=ctk.CTkFont(size=14),
        )
        self.result_label.grid(row=3, column=0, padx=20, pady=(10, 60))

    def _start_scan(self) -> None:
        """Startet die Diagnose in einem separaten Hintergrund-Thread."""

        self.scan_button.configure(
            state="disabled",
            text="Diagnose läuft ...",
        )

        self.status_label.configure(text="Systemdiagnose wird ausgeführt.")
        self.result_label.configure(text="Prüfungen werden vorbereitet ...")
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
            self.after(
                0,
                lambda: self._scan_failed(str(error)),
            )

    def _report_progress(
        self,
        title: str,
        current_step: int,
        total_steps: int,
    ) -> None:
        """Überträgt den aktuellen Fortschritt sicher an die Oberfläche."""

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
            text=f"Prüfe {title} ... "
            f"({current_step} von {total_steps})"
        )

    def _scan_finished(
        self,
        results: list[tuple[str, dict]],
    ) -> None:
        """Aktualisiert die Oberfläche nach erfolgreicher Diagnose."""

        self.diagnostic_results = results

        error_count = sum(
            1
            for _, result in results
            if result.get("Bewertung") == "FEHLER"
        )

        self.progress_bar.set(1)

        self.status_label.configure(
            text="Systemdiagnose abgeschlossen."
        )

        if error_count == 0:
            result_text = (
                f"{len(results)} Prüfungen wurden erfolgreich ausgeführt."
            )
        else:
            result_text = (
                f"{len(results)} Prüfungen abgeschlossen. "
                f"{error_count} Prüfung(en) konnten nicht vollständig "
                "ausgeführt werden."
            )

        self.result_label.configure(text=result_text)

        self.scan_button.configure(
            state="normal",
            text="Erneut prüfen",
        )

    def _scan_failed(self, error_message: str) -> None:
        """Zeigt einen unerwarteten Fehler des gesamten Scanvorgangs an."""

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