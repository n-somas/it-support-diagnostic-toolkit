from collections.abc import Mapping

import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure


STATUS_ORDER = [
    "OK",
    "INFO",
    "HINWEIS",
    "WARNUNG",
    "KRITISCH",
    "FEHLER",
]

STATUS_LABELS = {
    "OK": "OK",
    "INFO": "Info",
    "HINWEIS": "Hinweise",
    "WARNUNG": "Warnungen",
    "KRITISCH": "Kritisch",
    "FEHLER": "Fehler",
}

STATUS_COLORS = {
    "OK": "#22C55E",
    "INFO": "#3B82F6",
    "HINWEIS": "#A855F7",
    "WARNUNG": "#F59E0B",
    "KRITISCH": "#EF4444",
    "FEHLER": "#DC2626",
}


class StatusBarChart(ctk.CTkFrame):
    """Zeigt die Statusverteilung eines Diagnoselaufs."""

    def __init__(self, master) -> None:
        super().__init__(
            master,
            corner_radius=10,
            border_width=1,
        )

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._create_header()
        self._create_chart()

    def _create_header(self) -> None:
        """Erstellt Überschrift und Beschreibung."""

        header = ctk.CTkFrame(
            self,
            fg_color="transparent",
        )
        header.grid(
            row=0,
            column=0,
            padx=18,
            pady=(16, 4),
            sticky="ew",
        )
        header.grid_columnconfigure(0, weight=1)

        title_label = ctk.CTkLabel(
            header,
            text="Statusverteilung",
            anchor="w",
            font=ctk.CTkFont(
                size=17,
                weight="bold",
            ),
        )
        title_label.grid(
            row=0,
            column=0,
            sticky="w",
        )

        description_label = ctk.CTkLabel(
            header,
            text="Ergebnisse des aktuellen Diagnoselaufs",
            anchor="w",
            text_color=("gray40", "gray70"),
            font=ctk.CTkFont(size=12),
        )
        description_label.grid(
            row=1,
            column=0,
            pady=(2, 0),
            sticky="w",
        )

    def _create_chart(self) -> None:
        """Erstellt das eingebettete Matplotlib-Diagramm."""

        self.figure = Figure(
            figsize=(8.8, 2.8),
            dpi=100,
        )

        self.axes = self.figure.add_subplot(111)

        self.canvas = FigureCanvasTkAgg(
            self.figure,
            master=self,
        )
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.grid(
            row=1,
            column=0,
            padx=14,
            pady=(4, 14),
            sticky="nsew",
        )

        self.clear()

    def update_data(
        self,
        status_counts: Mapping[str, int],
    ) -> None:
        """Aktualisiert das Diagramm mit neuen Statuswerten."""

        labels = [
            STATUS_LABELS[status]
            for status in STATUS_ORDER
        ]

        values = [
            int(status_counts.get(status, 0))
            for status in STATUS_ORDER
        ]

        colors = [
            STATUS_COLORS[status]
            for status in STATUS_ORDER
        ]

        self.axes.clear()
        self._apply_theme()

        bars = self.axes.barh(
            labels,
            values,
            color=colors,
            height=0.58,
        )

        maximum_value = max(values, default=0)
        axis_maximum = max(1, maximum_value + 1)

        self.axes.set_xlim(0, axis_maximum)
        self.axes.invert_yaxis()
        self.axes.set_xlabel("Anzahl der Prüfungen")
        self.axes.grid(
            axis="x",
            alpha=0.18,
            linewidth=0.8,
        )
        self.axes.set_axisbelow(True)

        for bar, value in zip(bars, values):
            self.axes.text(
                value + 0.08,
                bar.get_y() + bar.get_height() / 2,
                str(value),
                va="center",
                fontsize=10,
                fontweight="bold",
                color=self._text_color(),
            )

        self.figure.tight_layout(
            pad=1.2
        )
        self.canvas.draw_idle()

    def clear(self) -> None:
        """Zeigt einen leeren Ausgangszustand."""

        self.axes.clear()
        self._apply_theme()

        self.axes.text(
            0.5,
            0.5,
            "Nach der Diagnose wird hier die Statusverteilung angezeigt.",
            horizontalalignment="center",
            verticalalignment="center",
            transform=self.axes.transAxes,
            fontsize=11,
            color=self._secondary_text_color(),
        )

        self.axes.set_xticks([])
        self.axes.set_yticks([])

        for spine in self.axes.spines.values():
            spine.set_visible(False)

        self.figure.tight_layout(
            pad=1.2
        )
        self.canvas.draw_idle()

    def _apply_theme(self) -> None:
        """Passt Diagrammfarben an Hell- und Dunkelmodus an."""

        background_color = self._background_color()
        text_color = self._text_color()

        self.figure.patch.set_facecolor(
            background_color
        )
        self.axes.set_facecolor(
            background_color
        )

        self.axes.tick_params(
            axis="both",
            colors=text_color,
            labelsize=10,
        )

        self.axes.xaxis.label.set_color(
            text_color
        )
        self.axes.yaxis.label.set_color(
            text_color
        )

        for spine in self.axes.spines.values():
            spine.set_visible(False)

    @staticmethod
    def _background_color() -> str:
        if ctk.get_appearance_mode() == "Dark":
            return "#242424"

        return "#F7F7F7"

    @staticmethod
    def _text_color() -> str:
        if ctk.get_appearance_mode() == "Dark":
            return "#F3F4F6"

        return "#1F2937"

    @staticmethod
    def _secondary_text_color() -> str:
        if ctk.get_appearance_mode() == "Dark":
            return "#9CA3AF"

        return "#6B7280"
