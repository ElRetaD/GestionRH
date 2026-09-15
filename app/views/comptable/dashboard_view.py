"""
Tableau de bord comptable — Design premium avec KPIs animés, graphiques
interactifs, résumé de paie, et responsive layout.
"""
from datetime import datetime

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QFont, QColor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QGridLayout, QGraphicsDropShadowEffect,
)

from app.services.payroll_service import PayrollService
from app.utils.theme import COLORS, hex_with_alpha
from app.utils.icons import get_pixmap
from app.widgets.chart_widget import ChartWidget
from app.widgets.ui_primitives import (
    AnimatedStatCard,
    GlowButton,
    IconButton,
    InfoBanner,
    MiniStatCard,
    PageHeader,
    build_scroll_page,
    make_chart_card,
)


# ─── Quick-action card ────────────────────────────────────────────────────────

class _QuickActionCard(QFrame):
    """Carte cliquable pour une action rapide dans le dashboard."""
    clicked = Signal()

    def __init__(self, title, subtitle, icon_name, color, parent=None):
        super().__init__(parent)
        self._color = color
        self.setObjectName("quickActionCard")
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(92)
        self._apply_style(False)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(20, 16, 16, 16)
        lay.setSpacing(14)

        # Icon
        icon_wrap = QLabel()
        icon_wrap.setFixedSize(48, 48)
        icon_wrap.setAlignment(Qt.AlignCenter)
        icon_wrap.setStyleSheet(
            f"background: {hex_with_alpha(color, 32)}; border-radius: 14px; border: none;"
        )
        inner = QLabel(icon_wrap)
        inner.setPixmap(get_pixmap(icon_name, 22, color))
        inner.setAlignment(Qt.AlignCenter)
        inner.setGeometry(13, 13, 22, 22)
        lay.addWidget(icon_wrap)

        # Text
        text_col = QVBoxLayout()
        text_col.setSpacing(3)
        title_lbl = QLabel(title)
        title_lbl.setFont(QFont("Segoe UI", 13, QFont.Bold))
        title_lbl.setStyleSheet(f"color: {COLORS['text_primary']}; background: transparent; border: none;")
        sub_lbl = QLabel(subtitle)
        sub_lbl.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px; background: transparent; border: none;")
        sub_lbl.setWordWrap(True)
        text_col.addWidget(title_lbl)
        text_col.addWidget(sub_lbl)
        lay.addLayout(text_col, 1)

        # Arrow
        arrow = QLabel()
        arrow.setPixmap(get_pixmap("chevron_right", 16, COLORS["text_muted"]))
        arrow.setStyleSheet("background: transparent; border: none;")
        lay.addWidget(arrow, 0, Qt.AlignVCenter)

    def _apply_style(self, hovered):
        c = COLORS
        color = self._color
        if hovered:
            bg = hex_with_alpha(color, 22)
            border = color
        else:
            bg = c["bg_secondary"]
            border = c["border"]
        self.setStyleSheet(f"""
            QFrame#quickActionCard {{
                background: {bg};
                border: 1px solid {border};
                border-radius: 18px;
            }}
            QFrame#quickActionCard QLabel {{ background: transparent; border: none; }}
        """)

    def enterEvent(self, event):
        self._apply_style(True)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._apply_style(False)
        super().leaveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mouseReleaseEvent(event)


# ─── Summary line item ────────────────────────────────────────────────────────

class _SummaryRow(QFrame):
    """Single line in the paie summary card."""

    def __init__(self, label, value, color=None, bold=False, parent=None):
        super().__init__(parent)
        c = COLORS
        self.setStyleSheet("background: transparent; border: none;")
        lay = QHBoxLayout(self)
        lay.setContentsMargins(4, 6, 4, 6)

        lbl = QLabel(label)
        font_size = 13 if bold else 12
        weight = QFont.Bold if bold else QFont.Normal
        lbl.setFont(QFont("Segoe UI", font_size, weight))
        lbl.setStyleSheet(
            f"color: {c['text_primary'] if bold else c['text_secondary']}; "
            "background: transparent; border: none;"
        )

        self.val_lbl = QLabel(value)
        self.val_lbl.setFont(QFont("Segoe UI", font_size, QFont.DemiBold if not bold else QFont.Bold))
        self.val_lbl.setStyleSheet(
            f"color: {color or c['text_primary']}; background: transparent; border: none;"
        )
        self.val_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        lay.addWidget(lbl, 1)
        lay.addWidget(self.val_lbl)


# ─── Main Dashboard ──────────────────────────────────────────────────────────

class ComptableDashboardView(QWidget):
    """Vue d'accueil premium pour le comptable."""
    navigation_requested = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background-color: {COLORS['bg_primary']};")
        self._stat_cards: dict[str, AnimatedStatCard] = {}
        self._build_ui()

        # Auto-refresh every 60s
        self._data_timer = QTimer(self)
        self._data_timer.timeout.connect(self.refresh)
        self._data_timer.start(60_000)

        # Live clock
        self._clock_timer = QTimer(self)
        self._clock_timer.timeout.connect(self._update_clock)
        self._clock_timer.start(1000)

    def _update_clock(self):
        self._clock_lbl.setText(
            datetime.now().strftime("%A %d %B %Y  ·  %H:%M:%S")
        )

    def _build_ui(self):
        _, layout = build_scroll_page(self)

        # ── Header ────────────────────────────────────────────────────────────
        header = PageHeader(
            "Tableau de Bord Comptable",
            f"Vue d'ensemble de la paie — {datetime.now().strftime('%B %Y')}",
            icon_name="payroll",
        )
        refresh_btn = GlowButton("Actualiser", COLORS["accent_secondary"], "refresh")
        refresh_btn.clicked.connect(self.refresh)
        header.add_action(refresh_btn)
        layout.addWidget(header)

        # Live clock
        self._clock_lbl = QLabel()
        self._clock_lbl.setFont(QFont("Segoe UI", 12, QFont.DemiBold))
        self._clock_lbl.setStyleSheet(
            f"color: {COLORS['accent_secondary']}; background: transparent; padding-left: 4px;"
        )
        self._update_clock()
        layout.addWidget(self._clock_lbl)

        # ── KPI Cards (animées) ───────────────────────────────────────────────
        self.kpi_grid = QGridLayout()
        self.kpi_grid.setSpacing(14)
        kpi_defs = [
            ("employes",  "Employés actifs",       "0",     "employees", COLORS["accent_secondary"], False),
            ("salaires",  "Salaires configurés",   "0",     "salary",    COLORS["accent_online"],    False),
            ("sans",      "Sans salaire",          "0",     "shield",    COLORS["accent_danger"],    False),
            ("bulletins", "Bulletins du mois",     "0",     "payslips",  COLORS["accent_primary"],   False),
            ("masse",     "Masse salariale nette", "0 MAD", "chart",     COLORS["accent_teal"],      True),
            ("brut",      "Masse salariale brute", "0 MAD", "payroll",   COLORS["accent_warning"],   True),
        ]
        self._kpi_keys = []
        for key, label, val, icon, color, is_cur in kpi_defs:
            card = AnimatedStatCard(label, val, icon, color, is_cur)
            self._stat_cards[key] = card
            self._kpi_keys.append(key)
        layout.addLayout(self.kpi_grid)
        self._reflow_kpis()

        # ── Charts Row ────────────────────────────────────────────────────────
        self.charts_grid = QGridLayout()
        self.charts_grid.setSpacing(16)

        # Donut chart — salary config status
        self.chart_config = make_chart_card(
            "Configuration des salaires",
            "Employés avec salaire configuré vs en attente"
        )
        self.chart_config_widget = ChartWidget()
        self.chart_config.layout().addWidget(self.chart_config_widget)

        # Bar chart — Brut vs Net
        self.chart_masse = make_chart_card(
            "Répartition masse salariale",
            "Comparaison brut estimé et net calculé"
        )
        self.chart_masse_widget = ChartWidget()
        self.chart_masse.layout().addWidget(self.chart_masse_widget)

        # Line chart — monthly trend (bulletins per month)
        self.chart_trend = make_chart_card(
            "Évolution mensuelle",
            "Nombre de bulletins générés par mois"
        )
        self.chart_trend_widget = ChartWidget()
        self.chart_trend.layout().addWidget(self.chart_trend_widget)

        # Horizontal bar — top salaries
        self.chart_top = make_chart_card(
            "Top 5 salaires nets",
            "Employés avec les salaires nets les plus élevés"
        )
        self.chart_top_widget = ChartWidget()
        self.chart_top.layout().addWidget(self.chart_top_widget)

        self.chart_cards = [
            self.chart_config,
            self.chart_masse,
            self.chart_trend,
            self.chart_top,
        ]
        layout.addLayout(self.charts_grid)
        self._reflow_charts()

        # ── Bottom row: summary card + quick actions ──────────────────────────
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(16)

        # Paie Summary Card
        summary_card = QFrame()
        summary_card.setObjectName("paieSummary")
        c = COLORS
        summary_card.setStyleSheet(f"""
            QFrame#paieSummary {{
                background: {c['bg_secondary']};
                border: 1px solid {c['border']};
                border-radius: 22px;
            }}
            QFrame#paieSummary QLabel {{ background: transparent; border: none; }}
        """)
        shadow = QGraphicsDropShadowEffect(summary_card)
        shadow.setBlurRadius(36)
        shadow.setOffset(0, 8)
        sc = QColor(c["accent_primary"])
        sc.setAlpha(30)
        shadow.setColor(sc)
        summary_card.setGraphicsEffect(shadow)

        summary_lay = QVBoxLayout(summary_card)
        summary_lay.setContentsMargins(24, 22, 24, 22)
        summary_lay.setSpacing(6)

        # Header
        s_header = QHBoxLayout()
        s_header.setSpacing(12)
        s_icon = QLabel()
        s_icon.setFixedSize(44, 44)
        s_icon.setAlignment(Qt.AlignCenter)
        s_icon.setStyleSheet(
            f"background: qlineargradient(x1:0,y1:0,x2:1,y2:1, "
            f"stop:0 {c['accent_primary']}, stop:1 {c['accent_secondary']}); "
            f"border-radius: 14px;"
        )
        si = QLabel(s_icon)
        si.setPixmap(get_pixmap("payslips", 22, "#FFFFFF"))
        si.setAlignment(Qt.AlignCenter)
        si.setGeometry(11, 11, 22, 22)
        s_header.addWidget(s_icon)

        s_title_col = QVBoxLayout()
        s_title_col.setSpacing(2)
        s_title = QLabel("Résumé de paie du mois")
        s_title.setFont(QFont("Segoe UI", 15, QFont.Bold))
        s_title.setStyleSheet(f"color: {c['text_primary']};")
        self._summary_period = QLabel(datetime.now().strftime("%B %Y"))
        self._summary_period.setStyleSheet(f"color: {c['text_muted']}; font-size: 11px;")
        s_title_col.addWidget(s_title)
        s_title_col.addWidget(self._summary_period)
        s_header.addLayout(s_title_col, 1)
        summary_lay.addLayout(s_header)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background: {c['border']}; border: none; margin: 8px 0;")
        summary_lay.addWidget(sep)

        # Rows
        self._sum_bulletins = _SummaryRow("Bulletins générés", "0")
        self._sum_employes = _SummaryRow("Employés actifs", "0")
        self._sum_brut = _SummaryRow("Total brut", "0 MAD")
        self._sum_deductions = _SummaryRow("Total déductions", "0 MAD")
        summary_lay.addWidget(self._sum_bulletins)
        summary_lay.addWidget(self._sum_employes)
        summary_lay.addWidget(self._sum_brut)
        summary_lay.addWidget(self._sum_deductions)

        # Separator
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.HLine)
        sep2.setFixedHeight(1)
        sep2.setStyleSheet(f"background: {c['border']}; border: none; margin: 6px 0;")
        summary_lay.addWidget(sep2)

        # Net total
        self._sum_net = _SummaryRow("NET TOTAL", "0 MAD", COLORS["accent_primary"], bold=True)
        summary_lay.addWidget(self._sum_net)

        bottom_row.addWidget(summary_card, 3)

        # Quick Actions Column
        actions_col = QVBoxLayout()
        actions_col.setSpacing(12)

        actions_title = QLabel("Actions rapides")
        actions_title.setFont(QFont("Segoe UI", 15, QFont.Bold))
        actions_title.setStyleSheet(f"color: {c['text_primary']}; background: transparent;")
        actions_col.addWidget(actions_title)

        qa1 = _QuickActionCard(
            "Configurer les salaires",
            "Définir le salaire de base des employés",
            "salary", COLORS["accent_online"]
        )
        qa1.clicked.connect(lambda: self.navigation_requested.emit("payroll_salaries"))

        qa2 = _QuickActionCard(
            "Gérer la paie mensuelle",
            "Primes, heures sup. et déductions",
            "payroll", COLORS["accent_secondary"]
        )
        qa2.clicked.connect(lambda: self.navigation_requested.emit("payroll_monthly"))

        qa3 = _QuickActionCard(
            "Générer les bulletins",
            "Calculer et exporter les fiches PDF",
            "payslips", COLORS["accent_primary"]
        )
        qa3.clicked.connect(lambda: self.navigation_requested.emit("payroll_payslips"))

        actions_col.addWidget(qa1)
        actions_col.addWidget(qa2)
        actions_col.addWidget(qa3)
        actions_col.addStretch()

        bottom_row.addLayout(actions_col, 2)
        layout.addLayout(bottom_row)

        # ── Alert banner ──────────────────────────────────────────────────────
        self._alert_banner = InfoBanner("", "shield")
        self._alert_banner.setVisible(False)
        layout.addWidget(self._alert_banner)

        # ── Info ──────────────────────────────────────────────────────────────
        layout.addWidget(InfoBanner(
            "Gérez les salaires de base dans « Salaires », ajoutez primes et déductions "
            "dans « Paie Mensuelle », puis générez les fiches PDF dans « Bulletins de Paie »."
        ))
        layout.addStretch()

    # ── Responsive layout helpers ────────────────────────────────────────────

    def _clear_layout(self, grid: QGridLayout):
        while grid.count():
            item = grid.takeAt(0)
            w = item.widget()
            if w is not None:
                w.setParent(None)

    def _reflow_kpis(self):
        if not hasattr(self, "kpi_grid"):
            return
        available = max(1, self.width() - 64)
        cols = max(1, min(3, int((available + 14) / (200 + 14))))
        self._clear_layout(self.kpi_grid)
        for i in range(cols):
            self.kpi_grid.setColumnStretch(i, 1)
        for idx, key in enumerate(self._kpi_keys):
            self.kpi_grid.addWidget(self._stat_cards[key], idx // cols, idx % cols)

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
        self.charts_grid.addWidget(self.chart_config, 0, 0, 1, 1)
        self.charts_grid.addWidget(self.chart_masse, 0, 1, 1, 1)
        self.charts_grid.addWidget(self.chart_trend, 1, 0, 1, 1)
        self.charts_grid.addWidget(self.chart_top, 1, 1, 1, 1)
        for col in range(2):
            self.charts_grid.setColumnStretch(col, 1)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._reflow_kpis()
        self._reflow_charts()

    # ── Refresh data ─────────────────────────────────────────────────────────

    def refresh(self):
        self._update_clock()
        periode = datetime.now().strftime("%Y-%m")
        stats = PayrollService.get_dashboard_stats(periode)

        total = stats["total_employes"]
        avec = stats["avec_salaire"]
        buls = stats["bulletins_mois"]
        masse = stats["masse_salariale"]
        sans = stats["sans_salaire"]

        # Brut estimation
        bulletins = PayrollService.get_bulletins(periode)
        total_brut = sum(b.salaire_brut for b in bulletins)
        total_deductions = sum(b.total_deductions for b in bulletins)

        # Animate KPI cards
        self._stat_cards["employes"].animate_to(total)
        self._stat_cards["salaires"].animate_to(avec)
        self._stat_cards["sans"].animate_to(sans)
        self._stat_cards["bulletins"].animate_to(buls)
        self._stat_cards["masse"].animate_to(int(masse), suffix=" MAD")
        self._stat_cards["brut"].animate_to(int(total_brut), suffix=" MAD")

        # Alert
        if sans > 0:
            self._alert_banner.text_label.setText(
                f"⚠  Action requise : {sans} employé(s) n'ont pas de salaire de base configuré "
                f"pour la période {periode}. Rendez-vous dans « Salaires » pour les configurer."
            )
            self._alert_banner.setVisible(True)
        else:
            self._alert_banner.setVisible(False)

        # Update summary card
        fmt = lambda v: f"{v:,.2f} MAD".replace(",", " ")
        self._sum_bulletins.val_lbl.setText(str(buls))
        self._sum_employes.val_lbl.setText(str(total))
        self._sum_brut.val_lbl.setText(fmt(total_brut))
        self._sum_deductions.val_lbl.setText(fmt(total_deductions))
        self._sum_net.val_lbl.setText(fmt(masse))
        self._summary_period.setText(datetime.now().strftime("%B %Y"))

        # Charts
        self._draw_config_donut(avec, sans)
        self._draw_masse_bars(masse, total_brut)
        self._draw_monthly_trend()
        self._draw_top_salaries(bulletins)

    def _draw_config_donut(self, avec, sans):
        labels = ["Configurés", "En attente"]
        values = [max(avec, 0), max(sans, 0)]
        if sum(values) == 0:
            values = [0, 0]
        self.chart_config_widget.plot_pie(labels, values)

    def _draw_masse_bars(self, net, brut):
        labels = ["Brut", "Net"]
        values = [brut, net]
        self.chart_masse_widget.plot_hbar(
            labels, values,
            color=COLORS["accent_secondary"],
        )

    def _draw_monthly_trend(self):
        """Plot bulletin counts for the last 6 months."""
        now = datetime.now()
        labels = []
        counts = []
        for i in range(5, -1, -1):
            month = now.month - i
            year = now.year
            while month <= 0:
                month += 12
                year -= 1
            p = f"{year}-{month:02d}"
            labels.append(p)
            buls = PayrollService.get_bulletins(p)
            counts.append(len(buls))
        self.chart_trend_widget.plot_line(
            labels, {"Bulletins": counts}
        )

    def _draw_top_salaries(self, bulletins):
        """Show top 5 highest net salaries."""
        sorted_buls = sorted(bulletins, key=lambda b: b.salaire_net, reverse=True)[:5]
        if not sorted_buls:
            self.chart_top_widget.plot_hbar([], [])
            return
        labels = [f"{b.employe_prenom} {b.employe_nom}" for b in sorted_buls]
        values = [b.salaire_net for b in sorted_buls]
        self.chart_top_widget.plot_hbar(
            labels, values,
            color=COLORS["accent_primary"],
        )
