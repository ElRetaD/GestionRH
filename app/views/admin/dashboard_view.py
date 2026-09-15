"""
Tableau de bord administrateur — KPIs et graphiques avec design premium.
"""
from datetime import datetime

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QGridLayout, QLabel, QWidget

from app.services.attendance_service import AttendanceService
from app.utils.theme import COLORS
from app.widgets.chart_widget import ChartWidget
from app.widgets.ui_primitives import (
    IconButton,
    MiniStatCard,
    PageHeader,
    build_scroll_page,
    make_chart_card,
)


class DashboardView(QWidget):
    """Tableau de bord — design moderne avec KPIs et graphiques."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background-color: {COLORS['bg_primary']};")
        self._stat_cards: dict[str, MiniStatCard] = {}
        self._build_ui()

        self._data_timer = QTimer(self)
        self._data_timer.timeout.connect(self.refresh)
        self._data_timer.start(60_000)

        self._clock_timer = QTimer(self)
        self._clock_timer.timeout.connect(self._update_clock)
        self._clock_timer.start(1000)

    def _update_clock(self):
        self.clock_lbl.setText(
            datetime.now().strftime("%A %d %B %Y  ·  %H:%M:%S")
        )

    def _build_ui(self):
        _, layout = build_scroll_page(self)

        header = PageHeader(
            "Tableau de Bord",
            "Vue globale des indicateurs, retards, absences et volumes d'activité",
            icon_name="dashboard",
        )
        refresh_btn = IconButton("refresh", "Actualiser", COLORS["accent_secondary"])
        refresh_btn.clicked.connect(self.refresh)
        header.add_action(refresh_btn)
        layout.addWidget(header)

        self.clock_lbl = QLabel()
        self.clock_lbl.setFont(QFont("Segoe UI", 12, QFont.DemiBold))
        self.clock_lbl.setStyleSheet(
            f"color: {COLORS['accent_secondary']}; background: transparent; padding-left: 4px;"
        )
        self._update_clock()
        layout.addWidget(self.clock_lbl)

        self.cards_grid = QGridLayout()
        self.cards_grid.setSpacing(14)
        stat_defs = [
            ("total", "Total Employés", "0", "employees", COLORS["accent_primary"]),
            ("present", "Présents", "0", "status", COLORS["accent_online"]),
            ("absent", "Absents", "0", "calendar", COLORS["accent_danger"]),
            ("conge", "Congés/Maladie", "0", "absences", COLORS["accent_warning"]),
            ("retard", "Retards", "0", "filter", COLORS["accent_secondary"]),
            ("heures", "Heures Travaillées", "0h", "chart", COLORS["accent_success"]),
        ]
        self._card_keys = []
        for key, label, val, icon, color in stat_defs:
            card = MiniStatCard(label, val, icon, color)
            self._stat_cards[key] = card
            self._card_keys.append(key)
        layout.addLayout(self.cards_grid)
        self._reflow_cards()

        self.charts_grid = QGridLayout()
        self.charts_grid.setSpacing(16)

        self.chart_monthly = make_chart_card(
            "Présences mensuelles", "Comparatif présents, absents et congés"
        )
        self.chart_monthly_widget = ChartWidget()
        self.chart_monthly.layout().addWidget(self.chart_monthly_widget)

        self.chart_today = make_chart_card(
            "Répartition du jour", "Poids de chaque statut de présence"
        )
        self.chart_today_widget = ChartWidget()
        self.chart_today.layout().addWidget(self.chart_today_widget)

        self.chart_retards = make_chart_card(
            "Retards par mois", "Évolution des retards cumulés"
        )
        self.chart_retards_widget = ChartWidget()
        self.chart_retards.layout().addWidget(self.chart_retards_widget)

        self.chart_depts = make_chart_card(
            "Heures par département", "Répartition sur les 30 derniers jours"
        )
        self.chart_depts_widget = ChartWidget()
        self.chart_depts.layout().addWidget(self.chart_depts_widget)

        self.chart_cards = [
            self.chart_monthly,
            self.chart_today,
            self.chart_retards,
            self.chart_depts,
        ]
        layout.addLayout(self.charts_grid)
        self._reflow_charts()

    def _clear_layout(self, grid: QGridLayout):
        while grid.count():
            item = grid.takeAt(0)
            w = item.widget()
            if w is not None:
                w.setParent(None)

    def _reflow_cards(self):
        if not hasattr(self, "cards_grid"):
            return
        available = max(1, self.width() - 64)
        cols = max(1, min(3, int((available + 14) / (200 + 14))))
        self._clear_layout(self.cards_grid)
        for i in range(cols):
            self.cards_grid.setColumnStretch(i, 1)
        for idx, key in enumerate(self._card_keys):
            self.cards_grid.addWidget(self._stat_cards[key], idx // cols, idx % cols)

    def _reflow_charts(self):
        if not hasattr(self, "charts_grid"):
            return
        self._clear_layout(self.charts_grid)
        available = max(1, self.width() - 64)
        if available < 980:
            for idx, card in enumerate(self.chart_cards):
                self.charts_grid.addWidget(card, idx, 0, 1, 1)
            self.charts_grid.setColumnStretch(0, 1)
            return
        self.charts_grid.addWidget(self.chart_monthly, 0, 0, 1, 2)
        self.charts_grid.addWidget(self.chart_today, 0, 2, 1, 1)
        self.charts_grid.addWidget(self.chart_retards, 1, 0, 1, 1)
        self.charts_grid.addWidget(self.chart_depts, 1, 1, 1, 2)
        for col in range(3):
            self.charts_grid.setColumnStretch(col, 1)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._reflow_cards()
        self._reflow_charts()

    def refresh(self):
        self._update_clock()
        stats = AttendanceService.get_today_stats()

        self._stat_cards["total"].set_value(str(stats.total_employes))
        self._stat_cards["present"].set_value(str(stats.presents_aujourd_hui))
        self._stat_cards["absent"].set_value(str(stats.absents_aujourd_hui))
        self._stat_cards["conge"].set_value(str(stats.conges_aujourd_hui))
        self._stat_cards["retard"].set_value(str(stats.retards_aujourd_hui))
        self._stat_cards["heures"].set_value(f"{stats.heures_travaillees_aujourd_hui:.1f}h")

        data = AttendanceService.get_monthly_chart_data()
        self.chart_monthly_widget.plot_bar(
            data["labels"],
            {
                "Présents": data["presents"],
                "Absents": data["absents"],
                "Congés": data["conges"],
            },
        )
        self.chart_today_widget.plot_pie(
            ["Présents", "Absents", "Congés/Maladie"],
            [
                stats.presents_aujourd_hui,
                stats.absents_aujourd_hui,
                stats.conges_aujourd_hui,
            ],
        )
        self.chart_retards_widget.plot_line(
            data["labels"], {"Retards": data["retards"]}
        )
        dept_data = AttendanceService.get_department_hours()
        self.chart_depts_widget.plot_hbar(
            dept_data["labels"],
            dept_data["heures"],
            color=COLORS["accent_secondary"],
        )
