"""
Vue des présences — consultation et gestion avec design premium.
Filtres live, KPIs, badges de statut et export Excel.
"""
from PySide6.QtCore import Qt, QDate, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QGraphicsOpacityEffect,
)

from app.services.attendance_service import AttendanceService
from app.services.employee_service import EmployeeService
from app.services.report_service import ReportService
from app.utils.theme import COLORS
from app.widgets.date_edit import ThemedDateEdit
from app.widgets.ui_primitives import (
    FilterField,
    IconButton,
    MiniStatCard,
    PageHeader,
    SearchInput,
    StatusBadge,
)


class AttendanceView(QWidget):
    """Vue de consultation des présences — design moderne."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background-color: {COLORS['bg_primary']};")
        self._stat_cards: dict[str, MiniStatCard] = {}
        self._build_ui()
        self._setup_fade()

    def _setup_fade(self):
        self._opacity_effect = QGraphicsOpacityEffect(self.table_container)
        self.table_container.setGraphicsEffect(self._opacity_effect)
        self._opacity_effect.setOpacity(1.0)
        self._fade_anim = QPropertyAnimation(self._opacity_effect, b"opacity")
        self._fade_anim.setDuration(180)
        self._fade_anim.setEasingCurve(QEasingCurve.OutCubic)

    def _build_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        container = QWidget()
        container.setStyleSheet("background: transparent;")
        scroll.setWidget(container)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(scroll)

        layout = QVBoxLayout(container)
        layout.setContentsMargins(28, 24, 28, 28)
        layout.setSpacing(22)

        # ── En-tête ───────────────────────────────────────────────────────
        header = PageHeader(
            "Gestion des Présences",
            "Consultez, filtrez et exportez les enregistrements de présence",
            icon_name="attendance",
        )
        refresh_btn = IconButton("refresh", "Actualiser", COLORS["accent_secondary"])
        refresh_btn.clicked.connect(self.refresh)
        export_btn = IconButton("export", "Exporter Excel", COLORS["accent_online"])
        export_btn.clicked.connect(self._export_excel)
        header.add_action(refresh_btn)
        header.add_action(export_btn)
        layout.addWidget(header)

        # ── KPIs ──────────────────────────────────────────────────────────
        stats_row = QHBoxLayout()
        stats_row.setSpacing(14)
        stat_defs = [
            ("total",   "Total",      "0", "filter",       COLORS["accent_secondary"]),
            ("present", "Présents",   "0", "status",       COLORS["accent_online"]),
            ("absent",  "Absents",    "0", "calendar",     COLORS["accent_danger"]),
            ("retard",  "Retards",    "0", "calendar",     COLORS["accent_warning"]),
        ]
        for key, label, val, icon, color in stat_defs:
            card = MiniStatCard(label, val, icon, color)
            self._stat_cards[key] = card
            stats_row.addWidget(card, 1)
        layout.addLayout(stats_row)

        # ── Filtres ───────────────────────────────────────────────────────
        filter_panel = QFrame()
        filter_panel.setObjectName("attendanceFilters")
        filter_panel.setStyleSheet(f"""
            QFrame#attendanceFilters {{
                background: {COLORS['bg_secondary']};
                border: 1px solid {COLORS['border']};
                border-radius: 20px;
            }}
        """)
        filter_grid = QGridLayout(filter_panel)
        filter_grid.setContentsMargins(18, 18, 18, 18)
        filter_grid.setHorizontalSpacing(14)
        filter_grid.setVerticalSpacing(14)

        self.date_from = ThemedDateEdit(QDate.currentDate().addDays(-30))
        self.date_to = ThemedDateEdit(QDate.currentDate())

        self.dept_combo = QComboBox()
        self.dept_combo.addItem("Tous")
        for department in EmployeeService.get_departments():
            self.dept_combo.addItem(department)

        self.status_combo = QComboBox()
        self.status_combo.addItems(["Tous", "Present", "Absent", "Conge", "Maladie"])

        self.search_input = SearchInput("Nom ou prénom de l'employé...")

        filter_grid.addWidget(FilterField("Date début", "calendar", self.date_from), 0, 0)
        filter_grid.addWidget(FilterField("Date fin", "calendar", self.date_to), 0, 1)
        filter_grid.addWidget(FilterField("Département", "building", self.dept_combo), 0, 2)
        filter_grid.addWidget(FilterField("Statut", "status", self.status_combo), 1, 0)
        filter_grid.addWidget(self.search_input, 1, 1, 1, 2)
        layout.addWidget(filter_panel)

        # ── Table ─────────────────────────────────────────────────────────
        table_header = QHBoxLayout()
        table_title = QLabel("Liste des enregistrements")
        table_title.setFont(QFont("Segoe UI", 15, QFont.Bold))
        table_title.setStyleSheet(f"color: {COLORS['text_primary']}; background: transparent;")
        self.count_lbl = QLabel()
        self.count_lbl.setStyleSheet(
            f"color: {COLORS['text_muted']}; background: transparent; font-size: 12px;"
        )
        table_header.addWidget(table_title)
        table_header.addStretch()
        table_header.addWidget(self.count_lbl)
        layout.addLayout(table_header)

        self.table_container = QFrame()
        self.table_container.setObjectName("tableWrap")
        self.table_container.setStyleSheet(f"""
            QFrame#tableWrap {{
                background: {COLORS['bg_secondary']};
                border: 1px solid {COLORS['border']};
                border-radius: 20px;
            }}
        """)
        table_lay = QVBoxLayout(self.table_container)
        table_lay.setContentsMargins(0, 0, 0, 0)

        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            "Employé", "Département", "Date", "Entrée",
            "Sortie", "Heures", "Statut", "Retard", "Min. Retard"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setStyleSheet(f"""
            QTableWidget {{
                background: transparent;
                border: none;
                border-radius: 20px;
            }}
        """)
        table_lay.addWidget(self.table)
        layout.addWidget(self.table_container, 1)

        self._connect_auto_filters()

    def _connect_auto_filters(self):
        self.date_from.dateChanged.connect(lambda *_: self.refresh())
        self.date_to.dateChanged.connect(lambda *_: self.refresh())
        self.dept_combo.currentIndexChanged.connect(lambda *_: self.refresh())
        self.status_combo.currentIndexChanged.connect(lambda *_: self.refresh())
        self.search_input.text_changed.connect(lambda *_: self.refresh())

    def _run_fade_refresh(self, callback):
        self._fade_anim.stop()
        self._fade_anim.setStartValue(1.0)
        self._fade_anim.setEndValue(0.55)
        self._fade_anim.finished.connect(lambda: self._finish_fade(callback))
        self._fade_anim.start()

    def _finish_fade(self, callback):
        try:
            self._fade_anim.finished.disconnect()
        except RuntimeError:
            pass
        callback()
        self._fade_anim.setStartValue(0.55)
        self._fade_anim.setEndValue(1.0)
        self._fade_anim.start()

    def _matches_search(self, presence, query: str) -> bool:
        if not query:
            return True
        query = query.strip().casefold()
        first_name = (presence.employe_prenom or "").strip()
        last_name = (presence.employe_nom or "").strip()
        full_name = f"{first_name} {last_name}".strip()
        return (
            first_name.casefold().startswith(query)
            or last_name.casefold().startswith(query)
            or full_name.casefold().startswith(query)
        )

    def refresh(self):
        self._run_fade_refresh(self._populate_table)

    def _populate_table(self):
        status_map = {
            "Present": "present",
            "Absent": "absent",
            "Conge": "conge",
            "Maladie": "maladie",
            "Tous": None,
        }
        status = status_map.get(self.status_combo.currentText())
        department = self.dept_combo.currentText()
        if department == "Tous":
            department = None

        presences = AttendanceService.get_presences(
            date_debut=self.date_from.date().toString("yyyy-MM-dd"),
            date_fin=self.date_to.date().toString("yyyy-MM-dd"),
            departement=department,
            statut=status,
        )

        search_query = self.search_input.text().strip()
        presences = [p for p in presences if self._matches_search(p, search_query)]

        present_count = sum(1 for p in presences if p.statut == "present")
        absent_count = sum(1 for p in presences if p.statut == "absent")
        retard_count = sum(1 for p in presences if p.retard)

        self._stat_cards["total"].set_value(str(len(presences)))
        self._stat_cards["present"].set_value(str(present_count))
        self._stat_cards["absent"].set_value(str(absent_count))
        self._stat_cards["retard"].set_value(str(retard_count))

        self.table.setRowCount(0)

        for presence in presences:
            row = self.table.rowCount()
            self.table.insertRow(row)

            name_item = QTableWidgetItem(
                f"{presence.employe_prenom} {presence.employe_nom}"
            )
            name_item.setFont(QFont("Segoe UI", 11, QFont.DemiBold))
            self.table.setItem(row, 0, name_item)

            plain_values = [
                presence.departement,
                presence.date,
                presence.heure_entree or "—",
                presence.heure_sortie or "—",
                f"{presence.heures_travaillees:.1f}h" if presence.heures_travaillees else "—",
            ]
            for col, value in enumerate(plain_values, start=1):
                item = QTableWidgetItem(str(value))
                item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row, col, item)

            status_widget = StatusBadge(presence.statut)
            status_wrap = QWidget()
            status_wrap.setStyleSheet("background: transparent;")
            sw_lay = QHBoxLayout(status_wrap)
            sw_lay.setContentsMargins(4, 4, 4, 4)
            sw_lay.addWidget(status_widget, 0, Qt.AlignCenter)
            self.table.setCellWidget(row, 6, status_wrap)

            if presence.statut in ["conge", "absent", "maladie", "teletravail"]:
                delay_item_cell = QTableWidgetItem("—")
                delay_item_cell.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row, 7, delay_item_cell)
            else:
                retard_key = "retard" if presence.retard else "ok"
                retard_widget = StatusBadge(retard_key)
                retard_wrap = QWidget()
                retard_wrap.setStyleSheet("background: transparent;")
                rw_lay = QHBoxLayout(retard_wrap)
                rw_lay.setContentsMargins(4, 4, 4, 4)
                rw_lay.addWidget(retard_widget, 0, Qt.AlignCenter)
                self.table.setCellWidget(row, 7, retard_wrap)

            delay_item = QTableWidgetItem(
                f"{presence.minutes_retard} min" if presence.minutes_retard else "—"
            )
            delay_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 8, delay_item)

            self.table.setRowHeight(row, 52)

        self.count_lbl.setText(f"{len(presences)} entrée(s) trouvée(s)")

    def _export_excel(self):
        import subprocess
        import os
        try:
            path = ReportService.export_excel(
                date_debut=self.date_from.date().toString("yyyy-MM-dd"),
                date_fin=self.date_to.date().toString("yyyy-MM-dd"),
            )
            msg = QMessageBox(self)
            msg.setWindowTitle("Export réussi")
            msg.setText(f"Le rapport Excel a été exporté avec succès :\n\n{os.path.basename(path)}")
            msg.setIcon(QMessageBox.Information)
            msg.setStandardButtons(QMessageBox.Ok)
            open_btn = msg.addButton("Ouvrir le dossier", QMessageBox.ActionRole)
            msg.exec()
            if msg.clickedButton() == open_btn:
                subprocess.Popen(f'explorer /select,"{os.path.normpath(path)}"')
        except Exception as e:
            QMessageBox.warning(self, "Erreur d'export", str(e))
