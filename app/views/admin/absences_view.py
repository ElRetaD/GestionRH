"""
Vue des absences — consultation des absences et congés avec design premium.
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

from app.database.connection import db
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


class AbsencesView(QWidget, FadeRefreshMixin):
    """Vue des absences et congés — design moderne."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background-color: {COLORS['bg_primary']};")
        self._stat_cards: dict[str, MiniStatCard] = {}
        self._build_ui()
        self._setup_fade()

    def _build_ui(self):
        _, layout = build_scroll_page(self)

        header = PageHeader(
            "Gestion des Absences & Congés",
            "Suivez les absences, congés et arrêts maladie par période et département",
            icon_name="absences",
        )
        refresh_btn = IconButton("refresh", "Actualiser", COLORS["accent_secondary"])
        refresh_btn.clicked.connect(self.refresh)
        header.add_action(refresh_btn)
        layout.addWidget(header)

        stats_row = QHBoxLayout()
        stats_row.setSpacing(14)
        for key, label, val, icon, color in [
            ("total", "Total", "0", "filter", COLORS["accent_secondary"]),
            ("absent", "Absents", "0", "status", COLORS["accent_danger"]),
            ("conge", "Congés", "0", "calendar", COLORS["accent_warning"]),
            ("maladie", "Maladie", "0", "absences", COLORS["accent_primary"]),
        ]:
            card = MiniStatCard(label, val, icon, color)
            self._stat_cards[key] = card
            stats_row.addWidget(card, 1)
        layout.addLayout(stats_row)

        filter_panel, filter_grid = build_filter_panel("absencesFilters")
        self.date_from = ThemedDateEdit(QDate.currentDate().addDays(-30))
        self.date_to = ThemedDateEdit(QDate.currentDate())

        self.type_combo = QComboBox()
        self.type_combo.addItems(["Tous", "Absent", "Conge", "Maladie"])

        self.dept_combo = QComboBox()
        self.dept_combo.addItem("Tous")
        for department in EmployeeService.get_departments():
            self.dept_combo.addItem(department)

        self.search_input = SearchInput("Nom ou prénom de l'employé...")

        filter_grid.addWidget(FilterField("Date début", "calendar", self.date_from), 0, 0)
        filter_grid.addWidget(FilterField("Date fin", "calendar", self.date_to), 0, 1)
        filter_grid.addWidget(FilterField("Type", "status", self.type_combo), 0, 2)
        filter_grid.addWidget(FilterField("Département", "building", self.dept_combo), 1, 0)
        filter_grid.addWidget(self.search_input, 1, 1, 1, 2)
        layout.addWidget(filter_panel)

        table_header, self.count_lbl, self.table_container, table_lay = build_table_section(
            "Registre des absences"
        )
        layout.addLayout(table_header)

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Employé", "Département", "Date", "Type",
            "Motif", "Justifiée", "Enregistré le"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
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
        self.type_combo.currentIndexChanged.connect(lambda *_: self.refresh())
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
        type_map = {
            "Absent": "absent",
            "Conge": "conge",
            "Maladie": "maladie",
            "Tous": None,
        }
        absence_type = type_map.get(self.type_combo.currentText())
        department = self.dept_combo.currentText()

        query = """
            SELECT a.*, e.nom, e.prenom, e.departement,
                   a.date_creation as enr
            FROM absences a
            JOIN employes e ON e.id = a.employe_id
            WHERE a.date >= ? AND a.date <= ?
        """
        params = [
            self.date_from.date().toString("yyyy-MM-dd"),
            self.date_to.date().toString("yyyy-MM-dd"),
        ]
        if absence_type:
            query += " AND a.type_absence = ?"
            params.append(absence_type)
        if department and department != "Tous":
            query += " AND e.departement = ?"
            params.append(department)
        query += " ORDER BY a.date DESC, e.nom"

        rows = db.fetchall(query, tuple(params))
        search_query = self.search_input.text().strip()
        rows = [row for row in rows if self._matches_search(row, search_query)]

        absent_count = sum(1 for r in rows if r["type_absence"] == "absent")
        conge_count = sum(1 for r in rows if r["type_absence"] == "conge")
        maladie_count = sum(1 for r in rows if r["type_absence"] == "maladie")

        self._stat_cards["total"].set_value(str(len(rows)))
        self._stat_cards["absent"].set_value(str(absent_count))
        self._stat_cards["conge"].set_value(str(conge_count))
        self._stat_cards["maladie"].set_value(str(maladie_count))

        self.table.setRowCount(0)
        for row_data in rows:
            row = self.table.rowCount()
            self.table.insertRow(row)

            name_item = QTableWidgetItem(f"{row_data['prenom']} {row_data['nom']}")
            name_item.setFont(QFont("Segoe UI", 11, QFont.DemiBold))
            self.table.setItem(row, 0, name_item)

            for col, value in enumerate([
                row_data["departement"],
                row_data["date"],
            ], start=1):
                item = QTableWidgetItem(str(value))
                item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row, col, item)

            self.table.setCellWidget(row, 3, badge_cell(row_data["type_absence"]))

            motif_item = QTableWidgetItem(row_data.get("motif") or "—")
            motif_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 4, motif_item)

            just_key = "yes" if row_data.get("justifiee") else "no"
            self.table.setCellWidget(row, 5, badge_cell(just_key))

            enr_item = QTableWidgetItem(row_data.get("enr", "")[:16] or "—")
            enr_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 6, enr_item)
            self.table.setRowHeight(row, 52)

        self.count_lbl.setText(f"{len(rows)} absence(s) trouvée(s)")
