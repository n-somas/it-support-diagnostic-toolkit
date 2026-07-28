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
            corner_radius=16,
            border_width=1,
            border_color=Colors.BORDER,
            fg_color=Colors.SURFACE_RAISED,
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
        background = "#192433" if dark else "#FFFFFF"
        foreground = "#F2F4F7" if dark else "#101722"

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
                "#A3AFBF"
                if ctk.get_appearance_mode() == "Dark"
                else "#667085"
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
            210,
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
            color="#5B8DEF",
            label="Belegt",
            height=0.38,
        )
        self.axes.barh(
            ["C:"],
            [free],
            left=[used],
            color="#55B5A5",
            label="Frei",
            height=0.38,
        )
        self.axes.set_xlabel("Gigabyte", labelpad=3)
        self.axes.legend(
            loc="upper center",
            bbox_to_anchor=(0.5, 1.18),
            ncol=2,
            frameon=False,
            labelcolor=(
                "#F2F4F7"
                if ctk.get_appearance_mode() == "Dark"
                else "#101722"
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
    """Zeigt Statusverteilung und Problemtrend der letzten Scans."""

    def __init__(self, master) -> None:
        super().__init__(
            master,
            "Diagnoseverlauf",
            "Statusverteilung und Problemtrend der letzten zehn Scans",
            330,
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
            self._label(str(record.get("created_at", "")))
            for record in records
        ]
        positions = list(range(len(labels)))

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

        bottom = [0] * len(labels)

        for status in STATUS_ORDER:
            series = values[status]

            if not any(series):
                continue

            self.axes.bar(
                positions,
                series,
                bottom=bottom,
                width=0.66,
                color=STATUS_COLORS[status],
                label=STATUS_LABELS[status],
                alpha=0.88,
            )
            bottom = [
                current + addition
                for current, addition in zip(bottom, series)
            ]

        problems = [
            values["WARNUNG"][index]
            + values["KRITISCH"][index]
            + values["FEHLER"][index]
            for index in range(len(labels))
        ]

        text_color = (
            "#F2F4F7"
            if ctk.get_appearance_mode() == "Dark"
            else "#101722"
        )

        self.axes.plot(
            positions,
            problems,
            marker="o",
            markersize=5,
            linewidth=2.1,
            color=text_color,
            markerfacecolor="#FFFFFF",
            markeredgecolor=text_color,
            label="Probleme gesamt",
            zorder=5,
        )

        self.axes.set_xticks(positions)
        self.axes.set_xticklabels(labels)
        self.axes.set_ylabel("Prüfungen")
        self.axes.grid(
            axis="y",
            alpha=0.12,
            linewidth=0.8,
        )
        self.axes.set_axisbelow(True)
        self.axes.margins(x=0.025)
        self.axes.set_ylim(
            0,
            max(bottom + problems + [1]) + 1,
        )

        self.axes.legend(
            loc="upper center",
            bbox_to_anchor=(0.5, 1.17),
            ncol=7,
            frameon=False,
            fontsize=8,
            labelcolor=text_color,
            handlelength=1.4,
            columnspacing=1.0,
        )

        self.axes.annotate(
            f"{problems[-1]} Probleme",
            xy=(positions[-1], problems[-1]),
            xytext=(-7, 12),
            textcoords="offset points",
            ha="right",
            fontsize=8,
            color=text_color,
        )

        self.figure.tight_layout(
            pad=1.1,
            rect=(0.01, 0.01, 0.99, 0.90),
        )
        self.canvas.draw_idle()

    @staticmethod
    def _label(value: str) -> str:
        try:
            date_part, time_part = value.split("T", 1)
            return (
                f"{date_part[8:10]}.{date_part[5:7]}.\n"
                f"{time_part[:5]}"
            )
        except (ValueError, IndexError):
            return value


class StorageHistoryChart(BaseChart):
    """Zeigt die Entwicklung von belegtem und freiem Speicher."""

    def __init__(self, master) -> None:
        super().__init__(
            master,
            "Verlauf der Speicherbelegung",
            "Belegter und freier Speicher der letzten zehn Scans",
            330,
        )
        self.show_empty(
            "Nach gespeicherten Diagnosen erscheint hier "
            "die Speicherentwicklung."
        )

    def update_records(self, records: list[dict]) -> None:
        points: list[tuple[str, float, float, float]] = []

        for record in records:
            usage = record.get("disk_usage")

            if not isinstance(usage, dict):
                continue

            used = self._number(usage.get("used_gb"))
            free = self._number(usage.get("free_gb"))
            total = self._number(usage.get("total_gb"))

            if used is None or free is None:
                continue

            if total is None:
                total = used + free

            points.append(
                (
                    self._label(
                        str(record.get("created_at", ""))
                    ),
                    used,
                    free,
                    total,
                )
            )

        if not points:
            self.show_empty(
                "In den gespeicherten Diagnosen wurden "
                "keine Speicherwerte gefunden."
            )
            return

        labels = [point[0] for point in points]
        used_values = [point[1] for point in points]
        free_values = [point[2] for point in points]
        total_values = [point[3] for point in points]
        positions = list(range(len(points)))

        self.axes.clear()
        self.apply_theme()

        self.axes.plot(
            positions,
            used_values,
            color="#5B8DEF",
            marker="o",
            linewidth=2.3,
            markersize=5,
            label="Belegt",
        )
        self.axes.fill_between(
            positions,
            used_values,
            color="#5B8DEF",
            alpha=0.10,
        )
        self.axes.plot(
            positions,
            free_values,
            color="#55B5A5",
            marker="o",
            linewidth=2.1,
            markersize=5,
            label="Frei",
        )
        self.axes.plot(
            positions,
            total_values,
            color=(
                "#A3AFBF"
                if ctk.get_appearance_mode() == "Dark"
                else "#667085"
            ),
            linestyle="--",
            linewidth=1.3,
            label="Gesamt",
        )

        self.axes.set_xticks(positions)
        self.axes.set_xticklabels(labels)
        self.axes.set_ylabel("Gigabyte")
        self.axes.grid(
            axis="y",
            alpha=0.12,
            linewidth=0.8,
        )
        self.axes.set_axisbelow(True)
        self.axes.margins(x=0.03, y=0.15)

        text_color = (
            "#F2F4F7"
            if ctk.get_appearance_mode() == "Dark"
            else "#101722"
        )
        self.axes.legend(
            loc="upper center",
            bbox_to_anchor=(0.5, 1.16),
            ncol=3,
            frameon=False,
            fontsize=9,
            labelcolor=text_color,
        )

        self.axes.annotate(
            f"{used_values[-1]:.1f} GB belegt",
            xy=(positions[-1], used_values[-1]),
            xytext=(-8, 12),
            textcoords="offset points",
            ha="right",
            fontsize=8,
            color=text_color,
        )

        self.figure.tight_layout(
            pad=1.1,
            rect=(0.01, 0.01, 0.99, 0.90),
        )
        self.canvas.draw_idle()

    @staticmethod
    def _number(value) -> float | None:
        if value is None:
            return None

        try:
            return float(str(value).replace(",", "."))
        except ValueError:
            return None

    @staticmethod
    def _label(value: str) -> str:
        try:
            date_part, time_part = value.split("T", 1)
            return (
                f"{date_part[8:10]}.{date_part[5:7]}.\n"
                f"{time_part[:5]}"
            )
        except (ValueError, IndexError):
            return value
