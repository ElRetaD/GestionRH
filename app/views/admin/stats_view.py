"""
Vue Statistiques — graphiques détaillés avec design premium.
"""
from datetime import datetime

from PySide6.QtWidgets import QComboBox, QGridLayout, QHBoxLayout, QFrame, QSizePolicy, QWidget, QListView

from app.database.connection import db
from app.services.attendance_service import AttendanceService
from app.utils.theme import COLORS
from app.widgets.chart_widget import ChartWidget
from app.widgets.ui_primitives import (
    FilterField,
    IconButton,
    MiniStatCard,
    PageHeader,
    build_scroll_page,
    make_chart_card,
)


class StatsView(QWidget):
    """Vue des statistiques avancées — design moderne."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background-color: {COLORS['bg_primary']};")
        self._stat_cards: dict[str, MiniStatCard] = {}
        self._build_ui()

    def _build_ui(self):
        _, layout = build_scroll_page(self)

        header = PageHeader(
            "Statistiques Avancées",
            "Analyse des tendances, retards et performance par département",
            icon_name="stats",
        )
        refresh_btn = IconButton("refresh", "Actualiser", COLORS["accent_secondary"])
        refresh_btn.clicked.connect(self.refresh)
        header.add_action(refresh_btn)
        layout.addWidget(header)

        year_row = QHBoxLayout()
        year_row.setSpacing(14)
        self.year_combo = QComboBox()
        self.year_combo.setView(QListView())
        year = datetime.now().year
        for y in range(year - 3, year + 1):
            self.year_combo.addItem(str(y))
        self.year_combo.setCurrentText(str(year))
        self.year_combo.currentTextChanged.connect(self.refresh)
        year_row.addWidget(FilterField("Année", "calendar", self.year_combo), 0)
        year_row.addStretch()
        layout.addLayout(year_row)

        stats_row = QHBoxLayout()
        stats_row.setSpacing(14)
        for key, label, val, icon, color in [
            ("presents", "Présents (année)", "0", "status", COLORS["accent_online"]),
            ("absents", "Absents (année)", "0", "calendar", COLORS["accent_danger"]),
            ("retards", "Retards (année)", "0", "filter", COLORS["accent_warning"]),
            ("depts", "Départements", "0", "building", COLORS["accent_primary"]),
        ]:
            card = MiniStatCard(label, val, icon, color)
            self._stat_cards[key] = card
            stats_row.addWidget(card, 1)
        layout.addLayout(stats_row)

        self.grid = QGridLayout()
        self.grid.setSpacing(16)

        chart_defs = [
            ("monthly_att", "Présences vs absences", "Comparatif mensuel consolidé"),
            ("monthly_late", "Évolution des retards", "Tendance des retards par mois"),
            ("dept_hours", "Heures par département", "Volume sur les 30 derniers jours"),
            ("dept_rate", "Taux de présence", "Performance par département (%)"),
        ]
        self.charts: dict[str, ChartWidget] = {}
        self._chart_cards: list[QFrame] = []
        for key, title, subtitle in chart_defs:
            card = make_chart_card(title, subtitle)
            card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            widget = ChartWidget()
            card.layout().addWidget(widget)
            self.charts[key] = widget
            self._chart_cards.append(card)

        layout.addLayout(self.grid)
        self._reflow_chart_cards()

        self.top_card = make_chart_card(
            "Top 5 — Heures travaillées ce mois",
            "Classement des collaborateurs les plus actifs",
        )
        self.chart_top = ChartWidget()
        self.top_card.layout().addWidget(self.chart_top)
        layout.addWidget(self.top_card)

    def _clear_grid(self):
        while self.grid.count():
            item = self.grid.takeAt(0)
            w = item.widget()
            if w is not None:
                w.setParent(None)

    def _reflow_chart_cards(self):
        if not hasattr(self, "grid"):
            return
        self._clear_grid()
        cols = 1 if self.width() < 1100 else 2
        for idx, card in enumerate(self._chart_cards):
            self.grid.addWidget(card, idx // cols, idx % cols)
        for col in range(cols):
            self.grid.setColumnStretch(col, 1)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._reflow_chart_cards()

    def refresh(self):
        year = int(self.year_combo.currentText())
        data = AttendanceService.get_monthly_chart_data(year)
        labels = data["labels"]

        total_present = sum(data["presents"])
        total_absent = sum(data["absents"])
        total_retard = sum(data["retards"])

        dept_data = AttendanceService.get_department_hours()
        self._stat_cards["presents"].set_value(str(total_present))
        self._stat_cards["absents"].set_value(str(total_absent))
        self._stat_cards["retards"].set_value(str(total_retard))
        self._stat_cards["depts"].set_value(str(len(dept_data["labels"])))

        self.charts["monthly_att"].plot_bar(
            labels, {"Présents": data["presents"], "Absents": data["absents"]}
        )
        self.charts["monthly_late"].plot_line(labels, {"Retards": data["retards"]})
        self.charts["dept_hours"].plot_hbar(
            dept_data["labels"], dept_data["heures"], color=COLORS["accent_info"]
        )

        mois = datetime.now().strftime("%Y-%m")
        dept_rows = db.fetchall(
            """
            SELECT e.departement,
                   COUNT(DISTINCT e.id) as total,
                   COUNT(p.id) FILTER(WHERE p.statut='present') as pres
            FROM employes e
            LEFT JOIN presences p ON p.employe_id=e.id
                AND strftime('%Y-%m', p.date)=?
            WHERE e.actif=1 AND e.departement!=''
            GROUP BY e.departement
            """,
            (mois,),
        )
        dept_labels, dept_rates = [], []
        for row in dept_rows:
            rate = round(row["pres"] / max(row["total"], 1) * 100, 1)
            dept_labels.append(row["departement"])
            dept_rates.append(rate)
        self.charts["dept_rate"].plot_bar(
            dept_labels, {"Taux (%)": dept_rates}, "Taux de présence (%)"
        )

        mois_courant = datetime.now().strftime("%Y-%m")
        top = db.fetchall(
            """SELECT e.prenom || ' ' || e.nom as nom,
                      ROUND(COALESCE(SUM(p.heures_travaillees),0),1) as h
               FROM presences p JOIN employes e ON e.id=p.employe_id
               WHERE strftime('%Y-%m', p.date)=?
               GROUP BY e.id ORDER BY h DESC LIMIT 5""",
            (mois_courant,),
        )
        if top:
            self.chart_top.plot_hbar(
                [r["nom"] for r in top],
                [r["h"] for r in top],
                color=COLORS["accent_purple"],
            )
