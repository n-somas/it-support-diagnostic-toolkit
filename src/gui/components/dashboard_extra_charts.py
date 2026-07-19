"""Speicher- und Verlaufsdiagramme des Dashboards."""

from __future__ import annotations

import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from src.gui.theme import Colors, STATUS_COLORS


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


class BaseChart(ctk.CTkFrame):
    def __init__(
        self,
        master,
        title: str,
        subtitle: str,
        height: int,
    ) -> None:
        super().__init__(
            master,
            corner_radius=12,
            border_width=1,
            border_color=Colors.BORDER,
            fg_color=Colors.SURFACE,
        )
        self.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            self,
            text=title,
            anchor="w",
            font=ctk.CTkFont(size=17, weight="bold"),
            text_color=Colors.TEXT,
        ).grid(
            row=0,
            column=0,
            padx=18,
            pady=(16, 2),
            sticky="ew",
        )

        ctk.CTkLabel(
            self,
            text=subtitle,
            anchor="w",
            font=ctk.CTkFont(size=12),
            text_color=Colors.MUTED,
        ).grid(
            row=1,
            column=0,
            padx=18,
            pady=(0, 6),
            sticky="ew",
        )

        self.figure = Figure(figsize=(6, 2.5), dpi=100)
        self.axes = self.figure.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(
            self.figure,
            master=self,
        )
        canvas_widget = self.canvas.get_tk_widget()
        canvas_widget.configure(height=height)
        canvas_widget.grid(
            row=2,
            column=0,
            padx=12,
            pady=(0, 12),
            sticky="ew",
        )

    def apply_theme(self) -> None:
        dark = ctk.get_appearance_mode() == "Dark"
        background = "#1F2937" if dark else "#FFFFFF"
        foreground = "#F8FAFC" if dark else "#111827"

        self.figure.patch.set_facecolor(background)
        self.axes.set_facecolor(background)
        self.axes.tick_params(
            axis="both",
            colors=foreground,
            labelsize=9,
        )
        self.axes.xaxis.label.set_color(foreground)
        self.axes.yaxis.label.set_color(foreground)

        for spine in self.axes.spines.values():
            spine.set_visible(False)

    def finish(self) -> None:
        self.figure.tight_layout(pad=1.0)
        self.canvas.draw_idle()

    def show_empty(self, text: str) -> None:
        self.axes.clear()
        self.apply_theme()
        self.axes.text(
            0.5,
            0.5,
            text,
            ha="center",
            va="center",
            transform=self.axes.transAxes,
            color=(
                "#94A3B8"
                if ctk.get_appearance_mode() == "Dark"
                else "#64748B"
            ),
        )
        self.axes.set_xticks([])
        self.axes.set_yticks([])
        self.finish()


class DiskUsageChart(BaseChart):
    def __init__(self, master) -> None:
        super().__init__(
            master,
            "Speicherbelegung",
            "Belegter und freier Speicher auf Laufwerk C:",
            250,
        )
        self.show_empty("Noch keine Speicherwerte vorhanden.")

    def update_results(
        self,
        results: list[tuple[str, dict]],
    ) -> None:
        disk_result = next(
            (
                result
                for title, result in results
                if "speicher" in title.lower()
                or "disk" in title.lower()
            ),
            None,
        )

        if not disk_result:
            self.show_empty("Keine Speicherwerte gefunden.")
            return

        used = self._number(
            disk_result.get("Belegter Speicher")
        )
        free = self._number(
            disk_result.get("Freier Speicher")
        )

        if used is None or free is None:
            self.show_empty("Speicherwerte nicht auswertbar.")
            return

        self.axes.clear()
        self.apply_theme()

        self.axes.barh(
            ["C:"],
            [used],
            color="#3B82F6",
            label="Belegt",
            height=0.38,
        )
        self.axes.barh(
            ["C:"],
            [free],
            left=[used],
            color="#22C55E",
            label="Frei",
            height=0.38,
        )
        self.axes.set_xlabel("Gigabyte")
        self.axes.legend(
            loc="upper center",
            bbox_to_anchor=(0.5, 1.18),
            ncol=2,
            frameon=False,
            labelcolor=(
                "#F8FAFC"
                if ctk.get_appearance_mode() == "Dark"
                else "#111827"
            ),
        )
        self.finish()

    @staticmethod
    def _number(value) -> float | None:
        if value is None:
            return None

        text = str(value).replace(",", ".")
        cleaned = "".join(
            character
            for character in text
            if character.isdigit()
            or character in ".-"
        )

        try:
            return float(cleaned)
        except ValueError:
            return None


class HistoryChart(BaseChart):
    def __init__(self, master) -> None:
        super().__init__(
            master,
            "Diagnoseverlauf",
            "Gestapelte Statusentwicklung der letzten zehn Scans",
            300,
        )
        self.show_empty(
            "Nach mehreren Scans erscheint hier die Entwicklung."
        )

    def update_records(self, records: list[dict]) -> None:
        if not records:
            self.show_empty(
                "Nach mehreren Scans erscheint hier die Entwicklung."
            )
            return

        labels = [
            self._label(record.get("created_at", ""))
            for record in records
        ]

        values = {
            status: [
                int(
                    record.get(
                        "status_counts",
                        {},
                    ).get(status, 0)
                )
                for record in records
            ]
            for status in STATUS_ORDER
        }

        self.axes.clear()
        self.apply_theme()

        self.axes.stackplot(
            labels,
            [values[status] for status in STATUS_ORDER],
            labels=[
                STATUS_LABELS[status]
                for status in STATUS_ORDER
            ],
            colors=[
                STATUS_COLORS[status]
                for status in STATUS_ORDER
            ],
            alpha=0.75,
        )

        problems = [
            values["WARNUNG"][index]
            + values["KRITISCH"][index]
            + values["FEHLER"][index]
            for index in range(len(labels))
        ]

        self.axes.plot(
            labels,
            problems,
            marker="o",
            linewidth=2,
            color=(
                "#FFFFFF"
                if ctk.get_appearance_mode() == "Dark"
                else "#111827"
            ),
            label="Probleme gesamt",
        )
        self.axes.set_ylabel("Anzahl")
        self.axes.grid(axis="y", alpha=0.16)
        self.axes.tick_params(axis="x", rotation=25)
        self.axes.legend(
            loc="upper center",
            bbox_to_anchor=(0.5, 1.25),
            ncol=4,
            frameon=False,
            fontsize=8,
            labelcolor=(
                "#F8FAFC"
                if ctk.get_appearance_mode() == "Dark"
                else "#111827"
            ),
        )
        self.finish()

    @staticmethod
    def _label(value: str) -> str:
        try:
            date_part, time_part = value.split("T", 1)
            return f"{date_part[5:]} {time_part[:5]}"
        except ValueError:
            return value
