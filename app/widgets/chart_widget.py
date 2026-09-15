"""
Widget graphique — Intègre des graphiques Matplotlib dans PySide6.
Utilisé pour les courbes de présences/absences/retards et les barres par département.
"""
import matplotlib
matplotlib.use("QtAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PySide6.QtWidgets import QWidget, QVBoxLayout, QSizePolicy
from app.utils.theme import COLORS, CHART_COLORS


class ChartWidget(QWidget):
    """Widget graphique réutilisable basé sur Matplotlib."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.fig = Figure(figsize=(6, 3.5), dpi=100, facecolor=COLORS["bg_secondary"])
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setStyleSheet(f"background-color: {COLORS['bg_secondary']}; border-radius: 12px;")
        self.setMinimumHeight(250)
        self.canvas.setMinimumHeight(250)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.canvas)

    def clear(self):
        self.fig.clear()

    # ─── Graphique en barres ───────────────────────────────────────────────────

    def plot_bar(self, labels: list, datasets: dict, title: str = ""):
        """
        Graphique en barres groupées.
        datasets = {"Présents": [...], "Absences": [...], ...}
        """
        self.fig.clear()
        self.fig.set_facecolor(COLORS["bg_secondary"])
        ax = self.fig.add_subplot(111, facecolor=COLORS["bg_secondary"])

        import numpy as np
        x = np.arange(len(labels))
        n = len(datasets)
        width = 0.75 / n

        for i, (label, values) in enumerate(datasets.items()):
            offset = (i - n / 2 + 0.5) * width
            color = CHART_COLORS[i % len(CHART_COLORS)]
            bars = ax.bar(x + offset, values, width, label=label,
                          color=color, alpha=0.85, zorder=3)

        ax.set_xticks(x)
        rotation = 0 if len(labels) <= 6 else 25
        ax.set_xticklabels(labels, fontsize=9, color=COLORS["text_secondary"], rotation=rotation, ha="right" if rotation else "center")
        ax.set_facecolor(COLORS["bg_secondary"])
        ax.tick_params(colors=COLORS["text_secondary"], labelsize=9)
        ax.spines[:].set_color(COLORS["border"])
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.grid(axis="y", color=COLORS["border_light"], alpha=0.5, zorder=0)
        ax.yaxis.label.set_color(COLORS["text_secondary"])

        if title:
            ax.set_title(title, color=COLORS["text_primary"], fontsize=12, fontweight="bold", pad=12)

        ax.legend(
            loc="upper left",
            facecolor=COLORS["bg_tertiary"], edgecolor=COLORS["border"],
            labelcolor=COLORS["text_primary"], fontsize=9
        )

        bottom = 0.18 if rotation == 0 else 0.28
        self.fig.subplots_adjust(left=0.08, right=0.98, top=0.90, bottom=bottom)
        self.canvas.draw()

    # ─── Graphique linéaire ────────────────────────────────────────────────────

    def plot_line(self, labels: list, datasets: dict, title: str = ""):
        """Graphique linéaire avec remplissage sous la courbe."""
        self.fig.clear()
        self.fig.set_facecolor(COLORS["bg_secondary"])
        ax = self.fig.add_subplot(111, facecolor=COLORS["bg_secondary"])

        import numpy as np
        x = np.arange(len(labels))

        for i, (label, values) in enumerate(datasets.items()):
            color = CHART_COLORS[i % len(CHART_COLORS)]
            ax.plot(x, values, color=color, linewidth=2.5,
                    label=label, marker="o", markersize=5, zorder=3)
            ax.fill_between(x, values, alpha=0.12, color=color)

        ax.set_xticks(x)
        rotation = 0 if len(labels) <= 6 else 25
        ax.set_xticklabels(labels, fontsize=9, color=COLORS["text_secondary"], rotation=rotation, ha="right" if rotation else "center")
        ax.set_facecolor(COLORS["bg_secondary"])
        ax.tick_params(colors=COLORS["text_secondary"], labelsize=9)
        ax.spines[:].set_color(COLORS["border"])
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.grid(color=COLORS["border_light"], alpha=0.5, zorder=0)

        if title:
            ax.set_title(title, color=COLORS["text_primary"], fontsize=12, fontweight="bold", pad=12)

        ax.legend(
            loc="upper left",
            facecolor=COLORS["bg_tertiary"], edgecolor=COLORS["border"],
            labelcolor=COLORS["text_primary"], fontsize=9
        )
        bottom = 0.18 if rotation == 0 else 0.28
        self.fig.subplots_adjust(left=0.08, right=0.98, top=0.90, bottom=bottom)
        self.canvas.draw()

    # ─── Graphique camembert ──────────────────────────────────────────────────

    def plot_pie(self, labels: list, values: list, title: str = ""):
        """Graphique en donut (camembert avec trou central)."""
        self.fig.clear()
        self.fig.set_facecolor(COLORS["bg_secondary"])
        ax = self.fig.add_subplot(111, facecolor=COLORS["bg_secondary"])

        has_data = any(v > 0 for v in values)

        if not has_data:
            ax.text(0.5, 0.5, "Aucune donnée", ha="center", va="center",
                    color=COLORS["text_secondary"], fontsize=12, transform=ax.transAxes)
        else:
            wedges, _, autotexts = ax.pie(
                values,
                labels=None,
                autopct=lambda pct: f"{pct:.0f}%" if pct > 0 else "",
                colors=CHART_COLORS[:len(values)],
                wedgeprops=dict(width=0.62, edgecolor=COLORS["bg_secondary"], linewidth=2),
                pctdistance=0.74,
                startangle=90
            )
            for at in autotexts:
                at.set_color(COLORS["text_primary"])
                at.set_fontsize(9)
                at.set_fontweight("bold")

            ax.legend(
                wedges,
                labels,
                loc="center left",
                bbox_to_anchor=(1.02, 0.5),
                ncol=1,
                frameon=True,
                facecolor=COLORS["bg_tertiary"],
                edgecolor=COLORS["border"],
                labelcolor=COLORS["text_primary"],
                fontsize=9
            )

        if title:
            ax.set_title(title, color=COLORS["text_primary"], fontsize=12, fontweight="bold", pad=12)

        ax.axis("equal")
        if has_data:
            self.fig.subplots_adjust(left=0.08, right=0.66, top=0.90, bottom=0.10)
        else:
            self.fig.subplots_adjust(left=0.06, right=0.94, top=0.90, bottom=0.10)
        self.canvas.draw()

    # ─── Graphique barres horizontales ────────────────────────────────────────

    def plot_hbar(self, labels: list, values: list, title: str = "",
                  color: str | None = None):
        """Graphique en barres horizontales."""
        self.fig.clear()
        self.fig.set_facecolor(COLORS["bg_secondary"])
        ax = self.fig.add_subplot(111, facecolor=COLORS["bg_secondary"])
        color = color or COLORS["accent_primary"]

        if not labels:
            ax.text(0.5, 0.5, "Aucune donnée", ha="center", va="center",
                    color=COLORS["text_secondary"], transform=ax.transAxes)
        else:
            import numpy as np
            y = np.arange(len(labels))
            bars = ax.barh(y, values, color=color, alpha=0.92, zorder=3, height=0.56)

            ax.set_yticks(y)
            safe_labels = []
            for l in labels:
                l = str(l)
                safe_labels.append(l if len(l) <= 18 else (l[:17] + "…"))
            ax.set_yticklabels(safe_labels, fontsize=10, color=COLORS["text_primary"])
            ax.invert_yaxis()

            # Valeurs sur les barres
            for bar, val in zip(bars, values):
                offset = max(values) * 0.02 if max(values) > 0 else 0.2
                ax.text(bar.get_width() + offset, bar.get_y() + bar.get_height() / 2,
                        f"{val:.1f}h", va="center", color=COLORS["text_secondary"], fontsize=9)

        ax.set_facecolor(COLORS["bg_secondary"])
        ax.tick_params(colors=COLORS["text_secondary"], labelsize=9)
        ax.spines[:].set_color(COLORS["border"])
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.grid(axis="x", color=COLORS["border_light"], alpha=0.5, zorder=0)

        if title:
            ax.set_title(title, color=COLORS["text_primary"], fontsize=12, fontweight="bold", pad=12)

        max_len = max((len(str(l)) for l in labels), default=0)
        left = min(0.42, max(0.22, 0.18 + max_len * 0.006))
        self.fig.subplots_adjust(left=left, right=0.96, top=0.92, bottom=0.14)
        self.canvas.draw()
