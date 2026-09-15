"""
Vue Présences du Jour (Agent) — liste premium avec navigation par date.
"""
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QWidget,
)

from app.services.attendance_service import AttendanceService
from app.utils.theme import COLORS
from app.widgets.ui_primitives import (
    FadeRefreshMixin,
    IconButton,
    MiniStatCard,
    PageHeader,
    SearchInput,
    badge_cell,
    build_scroll_page,
    build_table_section,
)


class TodayView(QWidget, FadeRefreshMixin):
    """Vue des présences du jour pour l'agent — design moderne."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background-color: {COLORS['bg_primary']};")
        self.current_date = QDate.currentDate()
        self._stat_cards: dict[str, MiniStatCard] = {}
        self._build_ui()
        self._setup_fade()

    def _build_ui(self):
        _, layout = build_scroll_page(self)

        header = PageHeader(
            "Présences du Jour",
            "Consultez les pointages enregistrés pour la date sélectionnée",
            icon_name="today",
        )
        self.btn_prev = IconButton("chevron_left", "Jour précédent", COLORS["accent_secondary"], size=40)
        self.btn_prev.clicked.connect(self._prev_date)
        self.btn_next = IconButton("chevron_right", "Jour suivant", COLORS["accent_secondary"], size=40)
        self.btn_next.clicked.connect(self._next_date)
        self.btn_pdf = IconButton("pdf", "Exporter PDF", COLORS["accent_danger"], size=40)
        self.btn_pdf.clicked.connect(self._export_pdf)
        self.btn_excel = IconButton("excel", "Exporter Excel", COLORS["accent_success"], size=40)
        self.btn_excel.clicked.connect(self._export_excel)
        refresh_btn = IconButton("refresh", "Actualiser", COLORS["accent_primary"])
        refresh_btn.clicked.connect(self.refresh)
        header.add_action(self.btn_prev)
        header.add_action(self.btn_next)
        header.add_action(self.btn_pdf)
        header.add_action(self.btn_excel)
        header.add_action(refresh_btn)
        layout.addWidget(header)

        date_row = QHBoxLayout()
        self.date_lbl = QLabel()
        self.date_lbl.setFont(QFont("Segoe UI", 14, QFont.Bold))
        self.date_lbl.setStyleSheet(
            f"color: {COLORS['accent_secondary']}; background: transparent; padding-left: 4px;"
        )
        date_row.addWidget(self.date_lbl)
        date_row.addStretch()
        layout.addLayout(date_row)

        stats_row = QHBoxLayout()
        stats_row.setSpacing(14)
        for key, label, val, icon, color in [
            ("total", "Total", "0", "filter", COLORS["accent_secondary"]),
            ("present", "Présents", "0", "check", COLORS["accent_online"]),
            ("absent", "Absents", "0", "status", COLORS["accent_danger"]),
            ("retard", "Retards", "0", "clock_alert", COLORS["accent_warning"]),
        ]:
            card = MiniStatCard(label, val, icon, color)
            self._stat_cards[key] = card
            stats_row.addWidget(card, 1)
        layout.addLayout(stats_row)

        self.search_input = SearchInput("Rechercher un employé...")
        self.search_input.text_changed.connect(lambda *_: self.refresh())
        layout.addWidget(self.search_input)

        table_header, self.count_lbl, self.table_container, table_lay = build_table_section(
            "Liste des pointages"
        )
        layout.addLayout(table_header)

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Employé", "Département", "Poste", "Entrée",
            "Sortie", "Statut", "Retard"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setStyleSheet(
            "QTableWidget { background: transparent; border: none; border-radius: 20px; }"
        )
        table_lay.addWidget(self.table)
        layout.addWidget(self.table_container, 1)

    def _prev_date(self):
        self.current_date = self.current_date.addDays(-1)
        self.refresh()

    def _next_date(self):
        self.current_date = self.current_date.addDays(1)
        self.refresh()

    def refresh(self):
        self._run_fade_refresh(self._populate_table)

    def _populate_table(self):
        selected_date = self.current_date.toString(Qt.ISODate)
        self.date_lbl.setText(self.current_date.toString("dddd dd MMMM yyyy"))

        rows = AttendanceService.get_presences_by_date(selected_date)
        query = self.search_input.text().strip().casefold()
        if query:
            rows = [
                r for r in rows
                if query in f"{r.get('prenom', '')} {r.get('nom', '')}".casefold()
                or query in (r.get("departement") or "").casefold()
            ]

        present = sum(1 for r in rows if r.get("statut") == "present")
        absent = sum(1 for r in rows if r.get("statut") == "absent")
        retard = sum(1 for r in rows if r.get("retard"))

        self._stat_cards["total"].set_value(str(len(rows)))
        self._stat_cards["present"].set_value(str(present))
        self._stat_cards["absent"].set_value(str(absent))
        self._stat_cards["retard"].set_value(str(retard))

        self.table.setRowCount(0)
        for r in rows:
            row = self.table.rowCount()
            self.table.insertRow(row)

            name_item = QTableWidgetItem(f"{r.get('prenom', '')} {r.get('nom', '')}")
            name_item.setFont(QFont("Segoe UI", 11, QFont.DemiBold))
            self.table.setItem(row, 0, name_item)

            for col, val in enumerate([
                r.get("departement") or "—",
                r.get("poste") or "—",
                r.get("heure_entree") or "—",
                r.get("heure_sortie") or "—",
            ], start=1):
                item = QTableWidgetItem(str(val))
                item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row, col, item)

            statut = r.get("statut", "")
            badge_key = "retard" if r.get("retard") else statut
            if statut == "teletravail":
                badge_key = "teletravail"
            self.table.setCellWidget(row, 5, badge_cell(badge_key))

            if statut in ["conge", "absent", "maladie", "teletravail"]:
                item = QTableWidgetItem("—")
                item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row, 6, item)
            else:
                retard_key = "retard" if r.get("retard") else "ok"
                self.table.setCellWidget(row, 6, badge_cell(retard_key))
            self.table.setRowHeight(row, 52)

        label = "aujourd'hui" if self.current_date == QDate.currentDate() else "pour cette date"
        self.count_lbl.setText(f"{len(rows)} enregistrement(s) {label}")

    def _export_pdf(self):
        from app.services.report_service import ReportService
        from PySide6.QtWidgets import QMessageBox
        import os
        import subprocess
        selected_date = self.current_date.toString(Qt.ISODate)
        try:
            filepath = ReportService.export_pdf(date_debut=selected_date, date_fin=selected_date)
            msg = QMessageBox(self)
            msg.setWindowTitle("Export Réussi")
            msg.setText(f"Le rapport PDF a été exporté avec succès :\n\n{os.path.basename(filepath)}")
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
        from PySide6.QtWidgets import QMessageBox
        import os
        import subprocess
        selected_date = self.current_date.toString(Qt.ISODate)
        try:
            filepath = ReportService.export_excel(date_debut=selected_date, date_fin=selected_date)
            msg = QMessageBox(self)
            msg.setWindowTitle("Export Réussi")
            msg.setText(f"Le rapport Excel a été exporté avec succès :\n\n{os.path.basename(filepath)}")
            msg.setIcon(QMessageBox.Information)
            msg.setStandardButtons(QMessageBox.Ok)
            open_btn = msg.addButton("Ouvrir le dossier", QMessageBox.ActionRole)
            msg.exec()
            if msg.clickedButton() == open_btn:
                subprocess.Popen(f'explorer /select,"{os.path.normpath(filepath)}"')
        except Exception as e:
            QMessageBox.critical(self, "Erreur d'export", f"Erreur lors de l'export Excel : {e}")
