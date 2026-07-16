import customtkinter as ctk


class DiagnosticApp(ctk.CTk):
    """Hauptfenster des IT Support Diagnostic Toolkit."""

    def __init__(self) -> None:
        super().__init__()

        self.title("IT Support Diagnostic Toolkit")
        self.geometry("900x600")
        self.minsize(760, 500)

        ctk.set_appearance_mode("system")
        ctk.set_default_color_theme("blue")

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

        status_label = ctk.CTkLabel(
            content,
            text="System wurde noch nicht geprüft.",
            font=ctk.CTkFont(size=18),
        )
        status_label.grid(row=0, column=0, padx=20, pady=(80, 20))

        scan_button = ctk.CTkButton(
            content,
            text="Diagnose starten",
            width=220,
            height=48,
            font=ctk.CTkFont(size=16, weight="bold"),
            command=self._start_scan,
        )
        scan_button.grid(row=1, column=0, padx=20, pady=20)

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
        """Platzhalter für die spätere Systemdiagnose."""

        self.result_label.configure(
            text="Die Diagnosefunktionen werden im nächsten Schritt angebunden."
        )
        self.progress_bar.set(0.15)


def run_app() -> None:
    """Startet die grafische Benutzeroberfläche."""

    app = DiagnosticApp()
    app.mainloop()


if __name__ == "__main__":
    run_app()