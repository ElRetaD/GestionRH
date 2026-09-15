"""
Vue Recherche Employé (Agent) — Recherche par nom ou QR code.
Lorsqu'un employé est trouvé, affiche sa fiche complète.
Le scan QR via lecteur USB (clavier) est supporté nativement via le champ de recherche QR.
"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                                QPushButton, QLineEdit, QFrame, QScrollArea,
                                QGridLayout, QSizePolicy, QMessageBox,
                                QStackedWidget, QTableWidget, QTableWidgetItem,
                                QHeaderView)
from PySide6.QtCore import Qt, QSize, QTimer, Signal
from PySide6.QtGui import QFont, QPixmap

from app.services.employee_service import EmployeeService
from app.services.attendance_service import AttendanceService
from app.services.auth_service import AuthService
from app.models.models import Employe
from app.utils.theme import COLORS, hex_with_alpha
from app.widgets.ui_primitives import badge_cell


class SearchView(QWidget):
    """Recherche d'employés et affichage de la fiche détaillée."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background-color: {COLORS['bg_primary']};")
        self._selected_emp: Employe | None = None
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(20)

        title = QLabel("👥  Employés")
        title.setFont(QFont("Segoe UI", 22, QFont.Bold))
        title.setStyleSheet(f"color: {COLORS['text_primary']}; background: transparent;")
        layout.addWidget(title)

        # ── Barres de recherche ──
        search_card = QFrame()
        search_card.setObjectName("SearchCard")
        search_card.setStyleSheet(f"""
            QFrame#SearchCard {{
                background: {COLORS['bg_secondary']};
                border-radius: 14px;
                border: 1px solid {COLORS['border']};
            }}
        """)
        sc_layout = QVBoxLayout(search_card)
        sc_layout.setContentsMargins(24, 20, 24, 20)
        sc_layout.setSpacing(16)

        # Recherche par nom
        row1 = QHBoxLayout()
        name_lbl = QLabel("👤 Nom / Prénom / Département :")
        name_lbl.setStyleSheet(f"color: {COLORS['text_secondary']}; background: transparent; font-weight: 600;")
        self.name_search = QLineEdit()
        self.name_search.setPlaceholderText("Rechercher par nom, prénom, département...")
        self.name_search.setFixedHeight(44)
        self.name_search.textChanged.connect(self._search_by_name)

        row1.addWidget(name_lbl)
        row1.addWidget(self.name_search)
        sc_layout.addLayout(row1)

        # Hidden QR input to prevent crashes
        self.qr_input = QLineEdit()

        layout.addWidget(search_card)

        # ── Zone de résultats (stack) ──
        self.stack = QStackedWidget()

        # Page liste de résultats
        self.list_widget = self._build_list_widget()
        self.stack.addWidget(self.list_widget)

        # Page fiche employé
        self.profile_widget = EmployeeProfileWidget()
        self.profile_widget.back_clicked.connect(self._show_list)
        self.stack.addWidget(self.profile_widget)

        layout.addWidget(self.stack)

    def _build_list_widget(self) -> QWidget:
        w = QWidget()
        w.setStyleSheet("background: transparent;")
        l = QVBoxLayout(w)
        l.setContentsMargins(0, 0, 0, 0)

        self.result_table = QTableWidget()
        self.result_table.setColumnCount(6)
        self.result_table.setHorizontalHeaderLabels([
            "ID", "Nom Complet", "Département", "Poste", "Email", ""
        ])
        self.result_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.result_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.result_table.setColumnWidth(0, 60)
        self.result_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Fixed)
        self.result_table.setColumnWidth(5, 100)
        self.result_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.result_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.result_table.setAlternatingRowColors(True)
        self.result_table.verticalHeader().setVisible(False)
        self.result_table.setShowGrid(False)

        l.addWidget(self.result_table)
        return w

    def _search_by_name(self, term: str):
        if not term.strip():
            employees = EmployeeService.get_all()
        else:
            employees = EmployeeService.search(term.strip())
        self._show_results(employees)
        self.stack.setCurrentWidget(self.list_widget)

    def _search_by_qr(self):
        data = self.qr_input.text().strip()
        if not data:
            return
        emp = EmployeeService.get_by_qr_data(data)
        if emp:
            self.qr_input.clear()
            self._show_profile(emp)
        else:
            self.qr_input.setStyleSheet(f"""
                QLineEdit {{
                    border-color: {COLORS['accent_red']};
                    background: {hex_with_alpha(COLORS['accent_red'], 34)};
                }}
            """)
            QTimer.singleShot(2000, lambda: self.qr_input.setStyleSheet(""))

    def _show_results(self, employees: list):
        self.result_table.setRowCount(0)
        for emp in employees:
            row = self.result_table.rowCount()
            self.result_table.insertRow(row)

            vals = [str(emp.id), emp.nom_complet, emp.departement, emp.poste, emp.email]
            for col, val in enumerate(vals):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignCenter)
                self.result_table.setItem(row, col, item)

            btn = QPushButton("👁 Voir")
            btn.setFixedSize(80, 32)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {hex_with_alpha(COLORS['accent_blue'], 40)};
                    color: {COLORS['accent_blue']}; border: 1px solid transparent;
                    border-radius: 12px; font-weight: bold; font-size: 13px;
                    padding: 0;
                }}
                QPushButton:hover {{ background: {COLORS['accent_blue']}; color: white; }}
            """)
            btn.clicked.connect(lambda _, e=emp: self._show_profile(e))
            self.result_table.setCellWidget(row, 5, btn)
            self.result_table.setRowHeight(row, 44)

    def _show_profile(self, emp: Employe):
        self.profile_widget.load_employee(emp)
        self.stack.setCurrentWidget(self.profile_widget)

    def _show_list(self):
        self.stack.setCurrentWidget(self.list_widget)

    def refresh(self):
        self._search_by_name("")


class EmployeeProfileWidget(QWidget):
    """Fiche complète d'un employé — affichée après scan QR ou sélection."""
    back_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: transparent;")
        self._emp: Employe | None = None
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        # Bouton retour
        back_row = QHBoxLayout()
        back_btn = QPushButton("← Retour à la recherche")
        back_btn.setProperty("class", "btn-secondary")
        back_btn.setFixedWidth(200)
        back_btn.clicked.connect(self.back_clicked)
        back_row.addWidget(back_btn)
        back_row.addStretch()
        layout.addLayout(back_row)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: transparent; border: none;")

        container = QWidget()
        container.setStyleSheet("background: transparent;")
        scroll.setWidget(container)
        layout.addWidget(scroll)

        self.profile_layout = QVBoxLayout(container)
        self.profile_layout.setSpacing(20)

    def load_employee(self, emp: Employe):
        """Charge et affiche les informations de l'employé."""
        self._emp = emp

        # Nettoyer
        while self.profile_layout.count():
            item = self.profile_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # ── En-tête profil ──
        header_card = QFrame()
        header_card.setObjectName("HeaderCard")
        header_card.setStyleSheet(f"""
            QFrame#HeaderCard {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {hex_with_alpha(COLORS['accent_primary'], 34)}, stop:1 {COLORS['bg_secondary']});
                border-radius: 16px;
                border: 1px solid {hex_with_alpha(COLORS['accent_primary'], 68)};
            }}
        """)
        hl = QHBoxLayout(header_card)
        hl.setContentsMargins(28, 24, 28, 24)
        hl.setSpacing(24)

        # Avatar
        avatar_lbl = QLabel("👤")
        avatar_lbl.setFont(QFont("Segoe UI Emoji", 48))
        avatar_lbl.setFixedSize(100, 100)
        avatar_lbl.setAlignment(Qt.AlignCenter)
        avatar_lbl.setStyleSheet(f"""
            background: {hex_with_alpha(COLORS['accent_primary'], 34)};
            border-radius: 50px;
            color: {COLORS['accent_primary']};
        """)
        hl.addWidget(avatar_lbl)

        # Infos principales
        info_v = QVBoxLayout()
        info_v.setSpacing(6)

        name_lbl = QLabel(emp.nom_complet)
        name_lbl.setFont(QFont("Segoe UI", 24, QFont.Bold))
        name_lbl.setStyleSheet(f"color: {COLORS['text_primary']}; background: transparent;")

        dept_lbl = QLabel(f"🏢 {emp.departement}  |  💼 {emp.poste}")
        dept_lbl.setStyleSheet(f"color: {COLORS['text_secondary']}; background: transparent; font-size: 14px;")

        id_lbl = QLabel(f"ID Employé : #{emp.id:04d}")
        id_lbl.setStyleSheet(f"""
            color: {COLORS['accent_primary']};
            background: {hex_with_alpha(COLORS['accent_primary'], 24)};
            border-radius: 6px;
            padding: 4px 10px;
            font-size: 12px;
            font-weight: 600;
        """)

        info_v.addWidget(name_lbl)
        info_v.addWidget(dept_lbl)
        info_v.addWidget(id_lbl)
        info_v.addStretch()
        hl.addLayout(info_v)
        hl.addStretch()

        # QR Code miniature removed
        pass

        self.profile_layout.addWidget(header_card)

        # ── Informations détaillées ──
        details_row = QHBoxLayout()
        details_row.setSpacing(16)

        left_card = self._info_card("📋 Informations Personnelles", [
            ("📛 Nom",        emp.nom),
            ("📛 Prénom",     emp.prenom),
            ("📞 Téléphone",  emp.telephone or "—"),
            ("📧 Email",      emp.email or "—"),
            ("📅 Embauche",   emp.date_embauche or "—"),
            ("📅 Profil créé",emp.date_creation[:10] if emp.date_creation else "—"),
        ])
        details_row.addWidget(left_card)

        # ── Présences récentes ──
        recent = AttendanceService.get_presences(employe_id=emp.id)[:10]
        right_card = self._presence_card("📊 Présences Récentes", recent)
        details_row.addWidget(right_card)

        self.profile_layout.addLayout(details_row)
        self.profile_layout.addStretch()

    def _info_card(self, title: str, fields: list) -> QFrame:
        card = QFrame()
        card.setObjectName("InfoCard")
        card.setStyleSheet(f"""
            QFrame#InfoCard {{
                background: {COLORS['bg_secondary']};
                border-radius: 14px;
                border: 1px solid {COLORS['border']};
            }}
        """)
        cl = QVBoxLayout(card)
        cl.setContentsMargins(24, 20, 24, 20)
        cl.setSpacing(12)

        tl = QLabel(title)
        tl.setFont(QFont("Segoe UI", 13, QFont.DemiBold))
        tl.setStyleSheet(f"color: {COLORS['text_primary']}; background: transparent;")
        cl.addWidget(tl)

        for label, value in fields:
            row = QHBoxLayout()
            lbl = QLabel(label)
            lbl.setStyleSheet(f"color: {COLORS['text_secondary']}; background: transparent; font-size: 12px; min-width: 110px;")
            val = QLabel(value)
            val.setStyleSheet(f"color: {COLORS['text_primary']}; background: transparent; font-weight: 600;")
            row.addWidget(lbl)
            row.addWidget(val)
            row.addStretch()
            cl.addLayout(row)

        return card

    def _presence_card(self, title: str, presences: list) -> QFrame:
        card = QFrame()
        card.setObjectName("PresenceCard")
        card.setStyleSheet(f"""
            QFrame#PresenceCard {{
                background: {COLORS['bg_secondary']};
                border-radius: 14px;
                border: 1px solid {COLORS['border']};
            }}
        """)
        cl = QVBoxLayout(card)
        cl.setContentsMargins(24, 20, 24, 20)
        cl.setSpacing(12)

        tl = QLabel(title)
        tl.setFont(QFont("Segoe UI", 13, QFont.DemiBold))
        tl.setStyleSheet(f"color: {COLORS['text_primary']}; background: transparent;")
        cl.addWidget(tl)

        table = QTableWidget(0, 4)
        table.setHorizontalHeaderLabels(["Date", "Entrée", "Sortie", "Statut"])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.verticalHeader().setVisible(False)
        table.setShowGrid(False)
        table.setMaximumHeight(250)

        for p in presences[:8]:
            row = table.rowCount()
            table.insertRow(row)
            
            # Setup columns 0, 1, 2
            for col, val in enumerate([p.date, p.heure_entree or "—", p.heure_sortie or "—"]):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignCenter)
                table.setItem(row, col, item)
                
            # Setup column 3 with badge_cell
            statut = p.statut
            badge_key = "retard" if p.retard else statut
            table.setCellWidget(row, 3, badge_cell(badge_key))
            table.setRowHeight(row, 44)

        cl.addWidget(table)
        return card
