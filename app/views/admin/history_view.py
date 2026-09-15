"""
Vue historique — journal complet des actions avec design premium.
"""
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QHeaderView,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.services.attendance_service import AttendanceService
from app.services.employee_service import EmployeeService
from app.utils.theme import COLORS
from app.widgets.date_edit import ThemedDateEdit
from app.widgets.ui_primitives import (
    FadeRefreshMixin,
    FilterField,
    IconButton,
    MiniStatCard,
    PageHeader,
    SearchInput,
    badge_cell,
    build_filter_panel,
    build_scroll_page,
    build_table_section,
)


class HistoryView(QWidget, FadeRefreshMixin):
    """Vue de l'historique complet — design moderne."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background-color: {COLORS['bg_primary']};")
        self._stat_cards: dict[str, MiniStatCard] = {}
        self._build_ui()
        self._setup_fade()

    def _build_ui(self):
        _, layout = build_scroll_page(self)

        header = PageHeader(
            "Historique Complet",
            "Journal de toutes les actions : entrées, sorties, absences et connexions",
            icon_name="history",
        )
        refresh_btn = IconButton("refresh", "Actualiser", COLORS["accent_secondary"])
        refresh_btn.clicked.connect(self.refresh)
        header.add_action(refresh_btn)
        layout.addWidget(header)

        stats_row = QHBoxLayout()
        stats_row.setSpacing(14)
        for key, label, val, icon, color in [
            ("total", "Total", "0", "history", COLORS["accent_secondary"]),
            ("entree", "Entrées", "0", "status", COLORS["accent_online"]),
            ("sortie", "Sorties", "0", "calendar", COLORS["accent_primary"]),
            ("other", "Autres", "0", "filter", COLORS["accent_teal"]),
        ]:
            card = MiniStatCard(label, val, icon, color)
            self._stat_cards[key] = card
            stats_row.addWidget(card, 1)
        layout.addLayout(stats_row)

        filter_panel, filter_grid = build_filter_panel("historyFilters")
        self.date_from = ThemedDateEdit(QDate.currentDate().addDays(-7))
        self.date_to = ThemedDateEdit(QDate.currentDate())

        self.dept_combo = QComboBox()
        self.dept_combo.addItem("Tous")
        for department in EmployeeService.get_departments():
            self.dept_combo.addItem(department)

        self.search_input = SearchInput("Nom ou prénom de l'employé...")

        filter_grid.addWidget(FilterField("Date début", "calendar", self.date_from), 0, 0)
        filter_grid.addWidget(FilterField("Date fin", "calendar", self.date_to), 0, 1)
        filter_grid.addWidget(FilterField("Département", "building", self.dept_combo), 0, 2)
        filter_grid.addWidget(self.search_input, 1, 0, 1, 3)
        layout.addWidget(filter_panel)

        table_header, self.count_lbl, self.table_container, table_lay = build_table_section(
            "Journal des événements"
        )
        layout.addLayout(table_header)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Date/Heure", "Action", "Employé", "Département",
            "Assistant RH", "Description"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setStyleSheet("QTableWidget { background: transparent; border: none; border-radius: 20px; }")
        table_lay.addWidget(self.table)
        layout.addWidget(self.table_container, 1)

        self._connect_auto_filters()

    def _connect_auto_filters(self):
        self.date_from.dateChanged.connect(lambda *_: self.refresh())
        self.date_to.dateChanged.connect(lambda *_: self.refresh())
        self.dept_combo.currentIndexChanged.connect(lambda *_: self.refresh())
        self.search_input.text_changed.connect(lambda *_: self.refresh())

    def _matches_search(self, row, query: str) -> bool:
        if not query:
            return True
        query = query.strip().casefold()
        first_name = (row.get("prenom") or "").strip()
        last_name = (row.get("nom") or "").strip()
        full_name = f"{first_name} {last_name}".strip()
        return (
            first_name.casefold().startswith(query)
            or last_name.casefold().startswith(query)
            or full_name.casefold().startswith(query)
        )

    def refresh(self):
        self._run_fade_refresh(self._populate_table)

    def _populate_table(self):
        department = self.dept_combo.currentText()
        rows = AttendanceService.get_history(
            date_debut=self.date_from.date().toString("yyyy-MM-dd"),
            date_fin=self.date_to.date().toString("yyyy-MM-dd"),
            departement=department if department != "Tous" else None,
        )

        search_query = self.search_input.text().strip()
        rows = [row for row in rows if self._matches_search(row, search_query)]

        entree_count = sum(1 for r in rows if r.get("type_action") == "entree")
        sortie_count = sum(1 for r in rows if r.get("type_action") == "sortie")
        other_count = len(rows) - entree_count - sortie_count

        self._stat_cards["total"].set_value(str(len(rows)))
        self._stat_cards["entree"].set_value(str(entree_count))
        self._stat_cards["sortie"].set_value(str(sortie_count))
        self._stat_cards["other"].set_value(str(other_count))

        self.table.setRowCount(0)
        for row_data in rows:
            row = self.table.rowCount()
            self.table.insertRow(row)

            action = row_data.get("type_action", "")
            desc_lower = (row_data.get("description") or "").lower()
            if action == "absence":
                if "conge" in desc_lower:
                    action = "conge"
                elif "maladie" in desc_lower:
                    action = "maladie"

            employee_name = ""
            if row_data.get("nom") and row_data.get("prenom"):
                employee_name = f"{row_data['prenom']} {row_data['nom']}"

            ts_item = QTableWidgetItem(row_data.get("timestamp", "")[:16])
            ts_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 0, ts_item)

            badge_key = action if action in ("entree", "sortie", "absence", "connexion", "conge", "maladie") else "connexion"
            self.table.setCellWidget(row, 1, badge_cell(badge_key))

            name_item = QTableWidgetItem(employee_name or "—")
            if employee_name:
                name_item.setFont(QFont("Segoe UI", 11, QFont.DemiBold))
            name_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 2, name_item)

            for col, value in enumerate([
                row_data.get("departement") or "—",
                row_data.get("agent_nom") or "—",
            ], start=3):
                item = QTableWidgetItem(str(value))
                item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row, col, item)

            desc_item = QTableWidgetItem(row_data.get("description") or "—")
            desc_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            self.table.setItem(row, 5, desc_item)
            self.table.setRowHeight(row, 52)

        self.count_lbl.setText(f"{len(rows)} entrée(s) dans l'historique")
