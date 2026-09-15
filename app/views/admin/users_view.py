"""
Vue Gestion des Utilisateurs — CRUD complet avec design premium.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView, QDialog, QFormLayout,
    QLineEdit, QComboBox, QCheckBox, QMessageBox, QDialogButtonBox,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from app.services.auth_service import AuthService
from app.models.models import Utilisateur
from app.utils.theme import COLORS
from app.widgets.ui_primitives import (
    FadeRefreshMixin,
    IconButton,
    InfoBanner,
    MiniStatCard,
    PageHeader,
    PrimaryButton,
    SmallActionButton,
    badge_cell,
    build_scroll_page,
    build_table_section,
    table_action_bar,
    action_table_row_height,
)


class UsersView(QWidget, FadeRefreshMixin):
    """Gestion des comptes utilisateurs — design moderne."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background-color: {COLORS['bg_primary']};")
        self._stat_cards: dict[str, MiniStatCard] = {}
        self._build_ui()
        self._setup_fade()

    def _build_ui(self):
        _, layout = build_scroll_page(self)

        header = PageHeader(
            "Gestion des Utilisateurs",
            "Créez, modifiez et gérez les comptes administrateurs, assistants RH et comptables",
            icon_name="users",
        )
        refresh_btn = IconButton("refresh", "Actualiser", COLORS["accent_secondary"])
        refresh_btn.clicked.connect(self.refresh)
        add_btn = PrimaryButton("Nouvel utilisateur", icon_name="add")
        add_btn.clicked.connect(self._add_user)
        header.add_action(refresh_btn)
        header.add_action(add_btn)
        layout.addWidget(header)

        stats_row = QHBoxLayout()
        stats_row.setSpacing(14)
        for key, label, val, icon, color in [
            ("total", "Total", "0", "users", COLORS["accent_secondary"]),
            ("admin", "Admins", "0", "shield", COLORS["accent_warning"]),
            ("agent", "Assistants RH", "0", "status", COLORS["accent_primary"]),
            ("active", "Actifs", "0", "filter", COLORS["accent_online"]),
        ]:
            card = MiniStatCard(label, val, icon, color)
            self._stat_cards[key] = card
            stats_row.addWidget(card, 1)
        layout.addLayout(stats_row)

        layout.addWidget(InfoBanner(
            "Seul l'administrateur peut gérer les comptes utilisateurs. "
            "Ne partagez jamais vos identifiants."
        ))

        table_header, self.count_lbl, self.table_container, table_lay = build_table_section(
            "Liste des comptes"
        )
        layout.addLayout(table_header)

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "ID", "Nom d'utilisateur", "Nom Complet", "Email",
            "Rôle", "Statut", "Actions"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.table.setColumnWidth(0, 60)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.Fixed)
        self.table.setColumnWidth(6, 240)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setStyleSheet("QTableWidget { background: transparent; border: none; border-radius: 20px; }")
        table_lay.addWidget(self.table)
        layout.addWidget(self.table_container, 1)

    def refresh(self):
        self._run_fade_refresh(self._populate_table)

    def _populate_table(self):
        users = AuthService.get_all_users()
        current_id = (
            AuthService.get_current_user().id if AuthService.get_current_user() else -1
        )

        admin_count = sum(1 for u in users if u.role == "admin")
        agent_count = sum(1 for u in users if u.role == "agent")
        active_count = sum(1 for u in users if u.actif)

        self._stat_cards["total"].set_value(str(len(users)))
        self._stat_cards["admin"].set_value(str(admin_count))
        self._stat_cards["agent"].set_value(str(agent_count))
        self._stat_cards["active"].set_value(str(active_count))

        self.table.setRowCount(0)
        for user in users:
            row = self.table.rowCount()
            self.table.insertRow(row)

            id_item = QTableWidgetItem(f"#{user.id:03d}")
            id_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 0, id_item)

            user_item = QTableWidgetItem(user.nom_utilisateur)
            user_item.setFont(QFont("Segoe UI", 11, QFont.DemiBold))
            self.table.setItem(row, 1, user_item)

            for col, text in enumerate([user.nom_complet, user.email], start=2):
                item = QTableWidgetItem(text or "—")
                item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row, col, item)

            self.table.setCellWidget(row, 4, badge_cell(user.role))
            status_key = "active" if user.actif else "inactive"
            self.table.setCellWidget(row, 5, badge_cell(status_key))

            edit_btn = SmallActionButton("edit", "Modifier", COLORS["accent_warning"])
            del_btn = SmallActionButton("delete", "Supprimer", COLORS["accent_danger"])
            edit_btn.clicked.connect(lambda _, u=user: self._edit_user(u))
            del_btn.setEnabled(user.id != current_id)
            del_btn.clicked.connect(lambda _, u=user: self._delete_user(u))

            self.table.setCellWidget(row, 6, table_action_bar(edit_btn, del_btn))
            self.table.setRowHeight(row, action_table_row_height(36, 2))

        self.count_lbl.setText(f"{len(users)} utilisateur(s)")

    def _add_user(self):
        dlg = UserDialog(parent=self)
        if dlg.exec():
            d = dlg.get_data()
            if AuthService.create_user(**d):
                QMessageBox.information(self, "Succès", "Utilisateur créé avec succès.")
                self.refresh()
            else:
                QMessageBox.warning(self, "Erreur", "Ce nom d'utilisateur existe déjà.")

    def _edit_user(self, user: Utilisateur):
        dlg = UserDialog(user, parent=self)
        if dlg.exec():
            d = dlg.get_data()
            if AuthService.update_user(
                user.id, d["nom_complet"], d["email"], d["role"],
                d["actif"], d.get("mot_de_passe", ""),
            ):
                self.refresh()

    def _delete_user(self, user: Utilisateur):
        reply = QMessageBox.question(
            self, "Confirmer",
            f"Supprimer le compte de {user.nom_complet} ?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            AuthService.delete_user(user.id)
            self.refresh()


class UserDialog(QDialog):
    """Dialog de création/modification d'un compte utilisateur."""

    def __init__(self, user: Utilisateur = None, parent=None):
        super().__init__(parent)
        self.user = user
        self.setWindowTitle("Modifier l'utilisateur" if user else "Nouvel Utilisateur")
        self.setMinimumWidth(460)
        self.setStyleSheet(f"QDialog {{ background: {COLORS['bg_secondary']}; border-radius: 16px; }}")
        self._build()
        if user:
            self._populate(user)

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(18)

        title = QLabel("Modifier l'utilisateur" if self.user else "Nouvel Utilisateur")
        title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        title.setStyleSheet(f"color: {COLORS['text_primary']}; background: transparent;")
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(12)

        self.username_inp = QLineEdit()
        self.username_inp.setFixedHeight(42)
        self.fullname_inp = QLineEdit()
        self.fullname_inp.setFixedHeight(42)
        self.email_inp = QLineEdit()
        self.email_inp.setFixedHeight(42)
        self.password_inp = QLineEdit()
        self.password_inp.setEchoMode(QLineEdit.Password)
        self.password_inp.setFixedHeight(42)
        self.password_inp.setPlaceholderText(
            "Laisser vide pour ne pas modifier" if self.user else "Mot de passe"
        )
        self.role_combo = QComboBox()
        self.role_combo.addItems(["agent", "admin", "comptable"])
        self.role_combo.setFixedHeight(42)
        self.active_check = QCheckBox("Compte actif")
        self.active_check.setChecked(True)

        def _lbl(text):
            lbl = QLabel(text)
            lbl.setStyleSheet(
                f"color: {COLORS['text_secondary']}; font-weight: 600; background: transparent;"
            )
            return lbl

        form.addRow(_lbl("Nom d'utilisateur *"), self.username_inp)
        form.addRow(_lbl("Nom complet"), self.fullname_inp)
        form.addRow(_lbl("Email"), self.email_inp)
        form.addRow(_lbl("Mot de passe"), self.password_inp)
        form.addRow(_lbl("Rôle"), self.role_combo)
        form.addRow("", self.active_check)

        if self.user:
            self.username_inp.setEnabled(False)

        layout.addLayout(form)

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.button(QDialogButtonBox.Ok).setText("Enregistrer")
        btns.button(QDialogButtonBox.Cancel).setText("Annuler")
        btns.accepted.connect(self._validate)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def _populate(self, u: Utilisateur):
        self.username_inp.setText(u.nom_utilisateur)
        self.fullname_inp.setText(u.nom_complet)
        self.email_inp.setText(u.email)
        self.role_combo.setCurrentText(u.role)
        self.active_check.setChecked(bool(u.actif))

    def _validate(self):
        if not self.username_inp.text().strip() and not self.user:
            QMessageBox.warning(self, "Requis", "Le nom d'utilisateur est obligatoire.")
            return
        if not self.password_inp.text() and not self.user:
            QMessageBox.warning(self, "Requis", "Le mot de passe est obligatoire.")
            return
        self.accept()

    def get_data(self) -> dict:
        return {
            "nom_utilisateur": self.username_inp.text().strip(),
            "mot_de_passe": self.password_inp.text(),
            "nom_complet": self.fullname_inp.text().strip(),
            "email": self.email_inp.text().strip(),
            "role": self.role_combo.currentText(),
            "actif": 1 if self.active_check.isChecked() else 0,
        }
