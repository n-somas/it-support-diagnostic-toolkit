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
    """Zeigt einen kompakten Trend der letzten Diagnosen."""

    def __init__(self, master) -> None:
        super().__init__(
            master,
            "Diagnoseverlauf",
            "Entwicklung von stabilen Ergebnissen, Hinweisen und Handlungsbedarf",
            350,
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

        from matplotlib.ticker import MaxNLocator

        labels = [
            self._label(
                str(record.get("created_at", ""))
            )
            for record in records
        ]
        positions = list(range(len(labels)))

        counts = [
            record.get("status_counts", {})
            for record in records
        ]

        stable = [
            int(item.get("OK", 0))
            for item in counts
        ]
        notes = [
            int(item.get("INFO", 0))
            + int(item.get("HINWEIS", 0))
            for item in counts
        ]
        action = [
            int(item.get("WARNUNG", 0))
            + int(item.get("KRITISCH", 0))
            + int(item.get("FEHLER", 0))
            for item in counts
        ]

        self.axes.clear()
        self.apply_theme()

        dark = ctk.get_appearance_mode() == "Dark"
        text_color = (
            "#F2F4F7"
            if dark
            else "#182230"
        )
        grid_color = (
            "#405069"
            if dark
            else "#D8DEE8"
        )

        stable_color = "#55B5A5"
        notes_color = "#7C93B8"
        action_color = "#D5953F"
        latest_color = (
            "#4F86F7"
            if dark
            else "#2563EB"
        )

        self.axes.axvspan(
            positions[-1] - 0.42,
            positions[-1] + 0.42,
            color=latest_color,
            alpha=0.06,
            zorder=0,
        )

        self.axes.plot(
            positions,
            stable,
            color=stable_color,
            linewidth=2.4,
            marker="o",
            markersize=5,
            label="Stabil",
            zorder=3,
        )
        self.axes.plot(
            positions,
            notes,
            color=notes_color,
            linewidth=2.2,
            marker="o",
            markersize=5,
            label="Info und Hinweise",
            zorder=3,
        )
        self.axes.plot(
            positions,
            action,
            color=action_color,
            linewidth=2.6,
            marker="o",
            markersize=6,
            label="Handlungsbedarf",
            zorder=4,
        )
        self.axes.fill_between(
            positions,
            action,
            0,
            color=action_color,
            alpha=0.08,
            zorder=1,
        )

        self.axes.set_xticks(positions)
        self.axes.set_xticklabels(labels)
        self.axes.set_ylabel("Prüfungen")
        self.axes.yaxis.set_major_locator(
            MaxNLocator(integer=True)
        )
        self.axes.grid(
            axis="y",
            color=grid_color,
            alpha=0.16,
            linewidth=0.8,
        )
        self.axes.set_axisbelow(True)
        self.axes.margins(x=0.035)

        upper = max(
            stable
            + notes
            + action
            + [1]
        )
        self.axes.set_ylim(
            0,
            upper + max(1, upper * 0.18),
        )

        self.axes.legend(
            loc="upper center",
            bbox_to_anchor=(0.5, 1.15),
            ncol=3,
            frameon=False,
            fontsize=9,
            labelcolor=text_color,
            handlelength=1.8,
            columnspacing=1.6,
        )

        last_values = (
            (
                stable[-1],
                stable_color,
                "Stabil",
                12,
            ),
            (
                notes[-1],
                notes_color,
                "Hinweise",
                0,
            ),
            (
                action[-1],
                action_color,
                "Bedarf",
                -12,
            ),
        )

        for value, color, label, offset in last_values:
            self.axes.annotate(
                f"{label} {value}",
                xy=(positions[-1], value),
                xytext=(-10, offset),
                textcoords="offset points",
                ha="right",
                va="center",
                fontsize=8,
                fontweight="bold",
                color=color,
                bbox={
                    "boxstyle": "round,pad=0.25",
                    "facecolor": (
                        "#202C3C"
                        if dark
                        else "#FFFFFF"
                    ),
                    "edgecolor": color,
                    "linewidth": 0.7,
                    "alpha": 0.95,
                },
            )

        self.axes.text(
            positions[-1],
            -0.16,
            "AKTUELL",
            transform=self.axes.get_xaxis_transform(),
            ha="center",
            va="top",
            fontsize=7,
            fontweight="bold",
            color=latest_color,
        )

        self.figure.tight_layout(
            pad=1.1,
            rect=(0.01, 0.03, 0.99, 0.90),
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
    """Zeigt eine moderne Speicherentwicklung."""

    def __init__(self, master) -> None:
        super().__init__(
            master,
            "Speicherentwicklung",
            "Belegter und freier Speicher der letzten zehn Scans",
            350,
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

            used = self._number(
                usage.get("used_gb")
            )
            free = self._number(
                usage.get("free_gb")
            )
            total = self._number(
                usage.get("total_gb")
            )

            if used is None or free is None:
                continue

            if total is None:
                total = used + free

            points.append(
                (
                    self._label(
                        str(
                            record.get(
                                "created_at",
                                "",
                            )
                        )
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

        labels = [
            point[0]
            for point in points
        ]
        used_values = [
            point[1]
            for point in points
        ]
        free_values = [
            point[2]
            for point in points
        ]
        total_values = [
            point[3]
            for point in points
        ]
        positions = list(range(len(points)))

        self.axes.clear()
        self.apply_theme()

        dark = ctk.get_appearance_mode() == "Dark"
        text_color = (
            "#F2F4F7"
            if dark
            else "#182230"
        )
        grid_color = (
            "#405069"
            if dark
            else "#D8DEE8"
        )
        used_color = "#5B8DEF"
        free_color = "#55B5A5"
        total_color = (
            "#A3AFBF"
            if dark
            else "#667085"
        )
        latest_color = (
            "#4F86F7"
            if dark
            else "#2563EB"
        )

        self.axes.axvspan(
            positions[-1] - 0.42,
            positions[-1] + 0.42,
            color=latest_color,
            alpha=0.06,
            zorder=0,
        )

        self.axes.plot(
            positions,
            used_values,
            color=used_color,
            marker="o",
            linewidth=2.6,
            markersize=5,
            label="Belegt",
            zorder=4,
        )
        self.axes.fill_between(
            positions,
            used_values,
            0,
            color=used_color,
            alpha=0.08,
            zorder=1,
        )
        self.axes.plot(
            positions,
            free_values,
            color=free_color,
            marker="o",
            linewidth=2.4,
            markersize=5,
            label="Frei",
            zorder=3,
        )
        self.axes.plot(
            positions,
            total_values,
            color=total_color,
            linestyle="--",
            linewidth=1.4,
            label="Gesamt",
            zorder=2,
        )

        self.axes.set_xticks(positions)
        self.axes.set_xticklabels(labels)
        self.axes.set_ylabel("Gigabyte")
        self.axes.grid(
            axis="y",
            color=grid_color,
            alpha=0.16,
            linewidth=0.8,
        )
        self.axes.set_axisbelow(True)
        self.axes.margins(x=0.035, y=0.15)

        self.axes.legend(
            loc="upper center",
            bbox_to_anchor=(0.5, 1.15),
            ncol=3,
            frameon=False,
            fontsize=9,
            labelcolor=text_color,
            handlelength=1.8,
            columnspacing=1.6,
        )

        annotations = (
            (
                used_values[-1],
                used_color,
                f"Belegt {used_values[-1]:.1f} GB",
                12,
            ),
            (
                free_values[-1],
                free_color,
                f"Frei {free_values[-1]:.1f} GB",
                -12,
            ),
        )

        for value, color, label, offset in annotations:
            self.axes.annotate(
                label,
                xy=(positions[-1], value),
                xytext=(-10, offset),
                textcoords="offset points",
                ha="right",
                va="center",
                fontsize=8,
                fontweight="bold",
                color=color,
                bbox={
                    "boxstyle": "round,pad=0.25",
                    "facecolor": (
                        "#202C3C"
                        if dark
                        else "#FFFFFF"
                    ),
                    "edgecolor": color,
                    "linewidth": 0.7,
                    "alpha": 0.95,
                },
            )

        self.axes.text(
            positions[-1],
            -0.16,
            "AKTUELL",
            transform=self.axes.get_xaxis_transform(),
            ha="center",
            va="top",
            fontsize=7,
            fontweight="bold",
            color=latest_color,
        )

        self.figure.tight_layout(
            pad=1.1,
            rect=(0.01, 0.03, 0.99, 0.90),
        )
        self.canvas.draw_idle()

    @staticmethod
    def _number(value) -> float | None:
        if value is None:
            return None

        try:
            return float(
                str(value).replace(",", ".")
            )
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
