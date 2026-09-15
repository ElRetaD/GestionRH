"""
Gestion des employés — CRUD complet avec design premium.
Liste, recherche, QR code et actions avec icônes vectorielles.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QDialog,
    QFormLayout, QMessageBox, QDialogButtonBox,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QPixmap, QCursor, QColor

from app.services.employee_service import EmployeeService
from app.models.models import Employe
from app.utils.theme import COLORS
from app.widgets.ui_primitives import (
    FadeRefreshMixin,
    IconButton,
    MiniStatCard,
    PageHeader,
    PrimaryButton,
    SearchInput,
    SmallActionButton,
    build_scroll_page,
    build_table_section,
    table_action_bar,
    action_table_row_height,
)


class EmployeesView(QWidget, FadeRefreshMixin):
    """Vue de gestion complète des employés — design moderne."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background-color: {COLORS['bg_primary']};")
        self._stat_cards: dict[str, MiniStatCard] = {}
        self._employees: list[Employe] = []
        self._build_ui()
        self._setup_fade()

    def _build_ui(self):
        _, layout = build_scroll_page(self)

        header = PageHeader(
            "Gestion des Employés",
            "Ajoutez, modifiez et gérez les profils de votre équipe",
            icon_name="employees",
        )
        refresh_btn = IconButton("refresh", "Actualiser", COLORS["accent_secondary"])
        refresh_btn.clicked.connect(self.refresh)
        add_btn = PrimaryButton("Ajouter", icon_name="add")
        add_btn.clicked.connect(self._add_employee)
        header.add_action(refresh_btn)
        header.add_action(add_btn)
        layout.addWidget(header)

        stats_row = QHBoxLayout()
        stats_row.setSpacing(14)
        for key, label, val, icon, color in [
            ("total", "Total", "0", "employees", COLORS["accent_secondary"]),
            ("depts", "Départements", "0", "building", COLORS["accent_primary"]),
            ("active", "Actifs", "0", "status", COLORS["accent_teal"]),
        ]:
            card = MiniStatCard(label, val, icon, color)
            self._stat_cards[key] = card
            stats_row.addWidget(card, 1)
        layout.addLayout(stats_row)

        self.search_input = SearchInput(
            "Rechercher par nom, email, département..."
        )
        self.search_input.text_changed.connect(self._search)
        layout.addWidget(self.search_input)

        table_header, self.count_lbl, self.table_container, table_lay = build_table_section(
            "Liste des employés"
        )
        layout.addLayout(table_header)

        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "ID", "Nom Complet", "Département", "Poste",
            "Téléphone", "Email", "Date Embauche", "Actions"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.table.setColumnWidth(0, 60)
        self.table.horizontalHeader().setSectionResizeMode(7, QHeaderView.Fixed)
        self.table.setColumnWidth(7, 140)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setStyleSheet("QTableWidget { background: transparent; border: none; border-radius: 20px; }")
        table_lay.addWidget(self.table)
        layout.addWidget(self.table_container, 1)

    def refresh(self):
        self._run_fade_refresh(lambda: self._load_employees(EmployeeService.get_all()))

    def _search(self, term: str):
        self._run_fade_refresh(lambda: self._fetch(term))

    def _fetch(self, term: str):
        employees = (
            EmployeeService.search(term.strip())
            if term.strip()
            else EmployeeService.get_all()
        )
        self._load_employees(employees)

    def _load_employees(self, employees: list[Employe]):
        self._employees = employees
        depts = {e.departement for e in employees if e.departement}
        active = sum(1 for e in employees if e.actif)

        self._stat_cards["total"].set_value(str(len(employees)))
        self._stat_cards["depts"].set_value(str(len(depts)))
        self._stat_cards["active"].set_value(str(active))

        self.table.setRowCount(0)
        for emp in employees:
            row = self.table.rowCount()
            self.table.insertRow(row)

            id_item = QTableWidgetItem(f"#{emp.id:04d}")
            id_item.setTextAlignment(Qt.AlignCenter)
            id_item.setData(Qt.UserRole, emp.id)
            id_item.setForeground(QColor(COLORS["accent_secondary"]))
            self.table.setItem(row, 0, id_item)

            name_item = QTableWidgetItem(emp.nom_complet)
            name_item.setFont(QFont("Segoe UI", 11, QFont.DemiBold))
            name_item.setData(Qt.UserRole, emp.id)
            self.table.setItem(row, 1, name_item)

            for col, text in enumerate(
                [emp.departement, emp.poste, emp.telephone, emp.email, emp.date_embauche],
                start=2,
            ):
                item = QTableWidgetItem(text or "—")
                item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row, col, item)

            edit_btn = SmallActionButton("edit", "Modifier", COLORS["accent_warning"])
            del_btn = SmallActionButton("delete", "Supprimer", COLORS["accent_danger"])
            edit_btn.clicked.connect(lambda _, e=emp: self._edit_employee(e))
            del_btn.clicked.connect(lambda _, e=emp: self._delete_employee(e))

            self.table.setCellWidget(row, 7, table_action_bar(edit_btn, del_btn))
            self.table.setRowHeight(row, action_table_row_height(36, 2))

        self.count_lbl.setText(f"{len(employees)} employé(s) trouvé(s)")

    def _add_employee(self):
        dlg = EmployeeDialog(parent=self)
        if dlg.exec():
            data = dlg.get_data()
            emp = EmployeeService.create(**data)
            if emp:
                QMessageBox.information(
                    self, "Succès",
                    f"Employé {emp.nom_complet} créé avec succès."
                )
                self.refresh()
            else:
                QMessageBox.warning(self, "Erreur", "Impossible de créer l'employé.")

    def _edit_employee(self, emp: Employe):
        dlg = EmployeeDialog(emp, parent=self)
        if dlg.exec():
            data = dlg.get_data()
            if EmployeeService.update(emp.id, **data):
                self.refresh()
            else:
                QMessageBox.warning(self, "Erreur", "Impossible de modifier l'employé.")

    def _delete_employee(self, emp: Employe):
        reply = QMessageBox.question(
            self, "Confirmer la suppression",
            f"Supprimer l'employé {emp.nom_complet} ?\n\n"
            "Cette action est irréversible et supprimera toutes ses données de présence.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            if EmployeeService.delete(emp.id):
                self.refresh()


class EmployeeDialog(QDialog):
    """Dialog d'ajout/modification d'un employé."""

    def __init__(self, employee: Employe = None, parent=None):
        super().__init__(parent)
        self.employee = employee
        self.setWindowTitle("Modifier l'employé" if employee else "Nouvel Employé")
        self.setMinimumWidth(520)
        self.setStyleSheet(f"QDialog {{ background-color: {COLORS['bg_secondary']}; border-radius: 16px; }}")
        self._build_ui()
        if employee:
            self._populate(employee)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(18)

        title = QLabel("Modifier l'employé" if self.employee else "Nouvel Employé")
        title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        title.setStyleSheet(f"color: {COLORS['text_primary']}; background: transparent;")
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(14)
        form.setLabelAlignment(Qt.AlignRight)

        self.fields = {}
        for key, label, placeholder in [
            ("nom", "Nom *", "Nom de famille"),
            ("prenom", "Prénom *", "Prénom"),
            ("telephone", "Téléphone", "+212 XXX XXXXXX"),
            ("email", "Email", "email@exemple.com"),
            ("departement", "Département", "ex: Informatique"),
            ("poste", "Poste", "ex: Développeur"),
            ("date_embauche", "Date d'embauche", "YYYY-MM-DD"),
        ]:
            lbl = QLabel(label)
            lbl.setStyleSheet(
                f"color: {COLORS['text_secondary']}; font-weight: 600; background: transparent;"
            )
            inp = QLineEdit()
            inp.setPlaceholderText(placeholder)
            inp.setFixedHeight(42)
            self.fields[key] = inp
            form.addRow(lbl, inp)

        layout.addLayout(form)

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.button(QDialogButtonBox.Ok).setText("Enregistrer")
        btns.button(QDialogButtonBox.Cancel).setText("Annuler")
        btns.accepted.connect(self._validate)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def _populate(self, emp: Employe):
        self.fields["nom"].setText(emp.nom)
        self.fields["prenom"].setText(emp.prenom)
        self.fields["telephone"].setText(emp.telephone)
        self.fields["email"].setText(emp.email)
        self.fields["departement"].setText(emp.departement)
        self.fields["poste"].setText(emp.poste)
        self.fields["date_embauche"].setText(emp.date_embauche)

    def _validate(self):
        if not self.fields["nom"].text().strip():
            QMessageBox.warning(self, "Champ requis", "Le nom est obligatoire.")
            return
        if not self.fields["prenom"].text().strip():
            QMessageBox.warning(self, "Champ requis", "Le prénom est obligatoire.")
            return
        self.accept()

    def get_data(self) -> dict:
        return {k: v.text().strip() for k, v in self.fields.items()}



