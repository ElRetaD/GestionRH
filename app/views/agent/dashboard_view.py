"""
Tableau de bord de l'agent — Design premium avec KPIs animés, graphique
de répartition du jour, flux d'activité en temps réel, grille de présence "Qui est au bureau"
et actions d'export rapide.
"""
import os
from datetime import datetime, date

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QFont, QColor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QMessageBox,
    QGridLayout, QGraphicsDropShadowEffect, QTableWidget, QTableWidgetItem, QHeaderView, QScrollArea
)

from app.services.attendance_service import AttendanceService
from app.utils.theme import COLORS, hex_with_alpha
from app.utils.icons import get_pixmap
from app.widgets.chart_widget import ChartWidget
from app.widgets.ui_primitives import (
    AnimatedStatCard,
    GlowButton,
    PageHeader,
    build_scroll_page,
    make_chart_card,
)


# ─── Employee Presence Card ───────────────────────────────────────────────────

class _EmployeePresenceCard(QFrame):
    """Petite carte pour visualiser la présence d'un employé dans la grille."""

    def __init__(self, name, dept, status, parent=None):
        super().__init__(parent)
        self.setObjectName("empPresenceCard")
        c = COLORS
        
        # Déterminer la couleur et le texte selon l'état
        if status == "entree":
            dot_color = c["accent_online"]
            bg_alpha = 20
            border_alpha = 50
            status_text = "Présent"
        elif status == "sortie":
            dot_color = c["accent_secondary"]
            bg_alpha = 15
            border_alpha = 30
            status_text = "Parti"
        elif status == "conge":
            dot_color = c["accent_warning"]
            bg_alpha = 15
            border_alpha = 35
            status_text = "En Congé"
        elif status == "maladie":
            dot_color = c["accent_danger"]
            bg_alpha = 15
            border_alpha = 35
            status_text = "Maladie"
        elif status == "teletravail":
            dot_color = c["accent_info"]
            bg_alpha = 15
            border_alpha = 35
            status_text = "Télétravail"
        else:
            dot_color = c["text_muted"]
            bg_alpha = 8
            border_alpha = 20
            status_text = "Absent"
            
        self.setStyleSheet(f"""
            QFrame#empPresenceCard {{
                background: {hex_with_alpha(dot_color, bg_alpha)};
                border: 1px solid {hex_with_alpha(dot_color, border_alpha)};
                border-radius: 14px;
            }}
        """)
        
        lay = QHBoxLayout(self)
        lay.setContentsMargins(14, 10, 14, 10)
        lay.setSpacing(10)
        
        # Status Dot
        dot = QLabel()
        dot.setFixedSize(10, 10)
        dot.setStyleSheet(f"background: {dot_color}; border-radius: 5px; border: none;")
        lay.addWidget(dot, 0, Qt.AlignVCenter)
        
        # Info col
        info = QVBoxLayout()
        info.setSpacing(2)
        
        name_lbl = QLabel(name)
        name_lbl.setFont(QFont("Segoe UI", 10, QFont.Bold))
        name_lbl.setStyleSheet(f"color: {c['text_primary']}; background: transparent; border: none;")
        
        sub_lbl = QLabel(f"{dept} · {status_text}")
        sub_lbl.setFont(QFont("Segoe UI", 8))
        sub_lbl.setStyleSheet(f"color: {c['text_secondary']}; background: transparent; border: none;")
        
        info.addWidget(name_lbl)
        info.addWidget(sub_lbl)
        lay.addLayout(info, 1)


# ─── Quick-action card ────────────────────────────────────────────────────────

class _QuickActionCard(QFrame):
    """Carte cliquable pour une action rapide dans le dashboard agent."""
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


# ─── Main Dashboard ──────────────────────────────────────────────────────────

class AgentDashboardView(QWidget):
    """Vue d'accueil premium pour l'agent."""
    navigation_requested = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background-color: {COLORS['bg_primary']};")
        self._stat_cards: dict[str, AnimatedStatCard] = {}
        self._build_ui()

        # Auto-refresh every 30s
        self._data_timer = QTimer(self)
        self._data_timer.timeout.connect(self.refresh)
        self._data_timer.start(30_000)

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
            "Portail Agent",
            f"Suivi et enregistrement des présences — {datetime.now().strftime('%d %B %Y')}",
            icon_name="dashboard",
        )
        refresh_btn = GlowButton("Actualiser", COLORS["accent_secondary"], "refresh")
        refresh_btn.clicked.connect(self.refresh)
        header.add_action(refresh_btn)

        # Exports
        pdf_btn = GlowButton("Exporter PDF", COLORS["accent_danger"], "pdf")
        pdf_btn.clicked.connect(self._export_pdf)
        excel_btn = GlowButton("Exporter Excel", COLORS["accent_success"], "excel")
        excel_btn.clicked.connect(self._export_excel)
        header.add_action(pdf_btn)
        header.add_action(excel_btn)

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
            ("total",    "Total Employés", "0", "employees", COLORS["accent_primary"], False),
            ("present",  "Présents",       "0", "check",     COLORS["accent_online"],    False),
            ("retard",   "En Retard",      "0", "clock_alert",COLORS["accent_danger"],    False),
            ("absent",   "Absents",        "0", "status",    COLORS["accent_warning"],   False),
        ]
        self._kpi_keys = []
        for key, label, val, icon, color, is_cur in kpi_defs:
            card = AnimatedStatCard(label, val, icon, color, is_cur)
            self._stat_cards[key] = card
            self._kpi_keys.append(key)
        layout.addLayout(self.kpi_grid)
        self._reflow_kpis()

        # ── Charts & Activity Row ─────────────────────────────────────────────
        self.mid_layout = QHBoxLayout()
        self.mid_layout.setSpacing(16)

        # Distribution Chart
        self.chart_card = make_chart_card(
            "Répartition des présences",
            "Statut de l'effectif pour la journée en cours"
        )
        self.chart_widget = ChartWidget()
        self.chart_card.layout().addWidget(self.chart_widget)
        self.mid_layout.addWidget(self.chart_card, 4)

        # Live Activity Log
        self.activity_card = make_chart_card(
            "Pointages récents du jour",
            "Historique en temps réel des entrées, sorties et absences enregistrées"
        )
        
        self.activity_table = QTableWidget()
        self.activity_table.setColumnCount(4)
        self.activity_table.setHorizontalHeaderLabels(["Heure", "Collaborateur", "Action", "Détails"])
        self.activity_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.activity_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.activity_table.setColumnWidth(0, 65)
        self.activity_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)
        self.activity_table.setColumnWidth(2, 80)
        self.activity_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.activity_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.activity_table.setAlternatingRowColors(True)
        self.activity_table.verticalHeader().setVisible(False)
        self.activity_table.setShowGrid(False)
        self.activity_table.setStyleSheet("QTableWidget { background: transparent; border: none; border-radius: 12px; }")
        
        self.activity_card.layout().addWidget(self.activity_table)
        self.mid_layout.addWidget(self.activity_card, 6)

        layout.addLayout(self.mid_layout)

        # ── Qui est au bureau ? (Grille en direct) ────────────────────────────
        self.presence_card = make_chart_card(
            "Qui est au bureau ? (En direct)",
            "Visualisation en temps réel de l'état de présence de chaque membre de l'équipe"
        )
        self.presence_scroll = QScrollArea()
        self.presence_scroll.setWidgetResizable(True)
        self.presence_scroll.setMinimumHeight(200)
        self.presence_scroll.setMaximumHeight(350)
        self.presence_scroll.setStyleSheet("background: transparent; border: none;")
        
        self.presence_container = QWidget()
        self.presence_container.setStyleSheet("background: transparent;")
        self.presence_grid = QGridLayout(self.presence_container)
        self.presence_grid.setSpacing(12)
        self.presence_grid.setContentsMargins(4, 4, 4, 4)
        
        self.presence_scroll.setWidget(self.presence_container)
        self.presence_card.layout().addWidget(self.presence_scroll)
        layout.addWidget(self.presence_card)

        # ── Actions Rapides ───────────────────────────────────────────────────
        c = COLORS
        actions_title = QLabel("Actions rapides")
        actions_title.setFont(QFont("Segoe UI", 15, QFont.Bold))
        actions_title.setStyleSheet(f"color: {c['text_primary']}; background: transparent; margin-top: 10px;")
        layout.addWidget(actions_title)

        actions_row = QHBoxLayout()
        actions_row.setSpacing(14)

        qa1 = _QuickActionCard(
            "Enregistrer les pointages",
            "Pointer une entrée ou une sortie",
            "record", COLORS["accent_online"]
        )
        qa1.clicked.connect(lambda: self.navigation_requested.emit("record"))

        qa2 = _QuickActionCard(
            "Fiches Collaborateurs",
            "Rechercher un profil ou consulter un dossier",
            "employees", COLORS["accent_secondary"]
        )
        qa2.clicked.connect(lambda: self.navigation_requested.emit("search"))

        qa3 = _QuickActionCard(
            "Présences du jour",
            "Voir la liste détaillée des pointages",
            "today", COLORS["accent_primary"]
        )
        qa3.clicked.connect(lambda: self.navigation_requested.emit("today"))

        actions_row.addWidget(qa1)
        actions_row.addWidget(qa2)
        actions_row.addWidget(qa3)
        layout.addLayout(actions_row)

        layout.addStretch()

    # ── Responsive layout helpers ────────────────────────────────────────────

    def _clear_layout(self, grid: QGridLayout):
        while grid.count():
            item = grid.takeAt(0)
            w = item.widget()
            if w is not None:
                w.setParent(None)

    def _clear_grid_layout(self, grid: QGridLayout):
        while grid.count():
            item = grid.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()

    def _reflow_kpis(self):
        if not hasattr(self, "kpi_grid"):
            return
        available = max(1, self.width() - 64)
        cols = max(1, min(4, int((available + 14) / (200 + 14))))
        self._clear_layout(self.kpi_grid)
        for i in range(cols):
            self.kpi_grid.setColumnStretch(i, 1)
        for idx, key in enumerate(self._kpi_keys):
            self.kpi_grid.addWidget(self._stat_cards[key], idx // cols, idx % cols)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._reflow_kpis()
        self._reflow_presence_grid()

    def _reflow_presence_grid(self):
        if not hasattr(self, "presence_grid") or self.presence_grid.count() == 0:
            return
        # Dynamically change column numbers based on screen width
        available = max(1, self.width() - 80)
        cols = max(2, min(6, int((available + 12) / (180 + 12))))
        
        # Temporarily detach widgets
        widgets = []
        for i in range(self.presence_grid.count()):
            item = self.presence_grid.itemAt(i)
            if item and item.widget():
                widgets.append(item.widget())
                
        # Re-add in new grid dimensions
        for w in widgets:
            self.presence_grid.removeWidget(w)
            
        for i in range(self.presence_grid.columnCount()):
            self.presence_grid.setColumnStretch(i, 0)
            
        for i in range(cols):
            self.presence_grid.setColumnStretch(i, 1)
            
        for idx, w in enumerate(widgets):
            self.presence_grid.addWidget(w, idx // cols, idx % cols)

    # ── Refresh data ─────────────────────────────────────────────────────────

    def refresh(self):
        self._update_clock()
        
        # 1. Fetch statistics
        stats = AttendanceService.get_today_stats()
        self._stat_cards["total"].animate_to(stats.total_employes)
        self._stat_cards["present"].animate_to(stats.presents_aujourd_hui)
        self._stat_cards["retard"].animate_to(stats.retards_aujourd_hui)
        self._stat_cards["absent"].animate_to(stats.absents_aujourd_hui)

        # 2. Draw chart
        labels = ["Présents", "Absents", "Congés/Maladie"]
        values = [
            stats.presents_aujourd_hui,
            stats.absents_aujourd_hui,
            stats.conges_aujourd_hui
        ]
        if sum(values) == 0:
            self.chart_widget.plot_pie(labels, [0, 0, 0])
        else:
            self.chart_widget.plot_pie(labels, values)

        # 3. Fetch recent activities for today (filter only entree, sortie, absence, conge, maladie)
        today_str = date.today().isoformat()
        all_logs = AttendanceService.get_history(date_debut=today_str)
        logs = [log for log in all_logs if log.get("employe_id") is not None and log.get("type_action") in ["entree", "sortie", "absence", "conge", "maladie"]]
        
        self.activity_table.setRowCount(0)
        # Limit to last 8 logs for display
        for log in logs[:8]:
            row = self.activity_table.rowCount()
            self.activity_table.insertRow(row)

            # Format timestamp to show HH:MM
            time_str = "—"
            if log.get("timestamp"):
                try:
                    time_str = datetime.strptime(log["timestamp"], "%Y-%m-%d %H:%M:%S").strftime("%H:%M")
                except ValueError:
                    time_str = log["timestamp"]

            time_item = QTableWidgetItem(time_str)
            time_item.setTextAlignment(Qt.AlignCenter)
            self.activity_table.setItem(row, 0, time_item)

            name_str = f"{log.get('prenom', '')} {log.get('nom', '')}"
            name_item = QTableWidgetItem(name_str)
            name_item.setFont(QFont("Segoe UI", 11, QFont.DemiBold))
            self.activity_table.setItem(row, 1, name_item)

            action_type = log.get("type_action", "")
            desc_lower = log.get("description", "").lower()
            if action_type == "absence":
                if "conge" in desc_lower:
                    action_type = "conge"
                elif "maladie" in desc_lower:
                    action_type = "maladie"

            action_map = {
                "entree": "Entrée",
                "sortie": "Sortie",
                "absence": "Absence",
                "conge": "Congé",
                "maladie": "Maladie",
            }
            action_str = action_map.get(action_type, action_type.capitalize())
            action_item = QTableWidgetItem(action_str)
            action_item.setTextAlignment(Qt.AlignCenter)
            
            # Apply color indicator
            if action_type == "entree":
                action_item.setForeground(QColor(COLORS["accent_online"]))
            elif action_type == "sortie":
                action_item.setForeground(QColor(COLORS["accent_secondary"]))
            elif action_type in ["conge", "maladie"]:
                action_item.setForeground(QColor(COLORS["accent_warning"]))
            else:
                action_item.setForeground(QColor(COLORS["accent_danger"]))
            self.activity_table.setItem(row, 2, action_item)

            # Details
            desc = log.get("description", "")
            desc_item = QTableWidgetItem(desc)
            desc_item.setFont(QFont("Segoe UI", 9))
            self.activity_table.setItem(row, 3, desc_item)
            
            self.activity_table.setRowHeight(row, 40)

        # 4. Qui est au bureau ?
        self._clear_grid_layout(self.presence_grid)
        employees = AttendanceService.get_live_presence_status()
        
        # Calculate columns based on width
        available = max(1, self.width() - 80)
        cols = max(2, min(6, int((available + 12) / (180 + 12))))
        
        for idx, emp in enumerate(employees):
            name = f"{emp.get('prenom', '')} {emp.get('nom', '')}"
            dept = emp.get("departement") or "—"
            
            current = emp.get("current_status")
            h_entree = emp.get("heure_entree")
            h_sortie = emp.get("heure_sortie")
            last_act = emp.get("last_action")
            
            if current == "conge":
                status = "conge"
            elif current == "maladie":
                status = "maladie"
            elif current == "teletravail":
                status = "teletravail"
            elif current == "present" or last_act in ["entree", "present"]:
                if h_sortie or last_act == "sortie":
                    status = "sortie"
                else:
                    status = "entree"
            elif current == "absent" or last_act == "absent":
                status = "absent"
            else:
                status = "absent"
            
            card = _EmployeePresenceCard(name, dept, status)
            self.presence_grid.addWidget(card, idx // cols, idx % cols)
            
        for i in range(cols):
            self.presence_grid.setColumnStretch(i, 1)

    # ── Export Handlers ───────────────────────────────────────────────────────

    def _export_pdf(self):
        from app.services.report_service import ReportService
        import subprocess
        selected_date = date.today().isoformat()
        try:
            filepath = ReportService.export_pdf(date_debut=selected_date, date_fin=selected_date)
            msg = QMessageBox(self)
            msg.setWindowTitle("Export Réussi")
            msg.setText(f"Le rapport PDF du jour a été généré avec succès :\n\n{os.path.basename(filepath)}")
            msg.setIcon(QMessageBox.Information)
            msg.setStandardButtons(QMessageBox.Ok)
            open_btn = msg.addButton("Ouvrir le dossier", QMessageBox.ActionRole)
            msg.exec()
            if msg.clickedButton() == open_btn:
                subprocess.Popen(f'explorer /select,"{os.path.normpath(filepath)}"')
        except Exception as e:
            QMessageBox.critical(self, "Erreur d'export", f"Erreur lors de l'export PDF : {e}")

    def _export_excel(self):
        from app.services.report_service import ReportService
        import subprocess
        selected_date = date.today().isoformat()
        try:
            filepath = ReportService.export_excel(date_debut=selected_date, date_fin=selected_date)
            msg = QMessageBox(self)
            msg.setWindowTitle("Export Réussi")
            msg.setText(f"Le rapport Excel du jour a été généré avec succès :\n\n{os.path.basename(filepath)}")
            msg.setIcon(QMessageBox.Information)
            msg.setStandardButtons(QMessageBox.Ok)
            open_btn = msg.addButton("Ouvrir le dossier", QMessageBox.ActionRole)
            msg.exec()
            if msg.clickedButton() == open_btn:
                subprocess.Popen(f'explorer /select,"{os.path.normpath(filepath)}"')
        except Exception as e:
            QMessageBox.critical(self, "Erreur d'export", f"Erreur lors de l'export Excel : {e}")
