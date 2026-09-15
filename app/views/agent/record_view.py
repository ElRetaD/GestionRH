"""
Vue Enregistrement (Agent) — pointage rapide avec design premium.
"""
from datetime import datetime, date

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QFrame,
    QMessageBox, QLineEdit, QGridLayout, QSizePolicy,
    QTableWidget, QTableWidgetItem, QHeaderView, QDialog, QFormLayout,
    QPushButton, QCompleter, QMenu,
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QCursor, QAction

from app.services.employee_service import EmployeeService
from app.services.attendance_service import AttendanceService
from app.services.auth_service import AuthService
from app.models.models import Employe
from app.utils.theme import COLORS, hex_with_alpha
from app.widgets.ui_primitives import (
    IconButton,
    InfoBanner,
    MiniStatCard,
    PageHeader,
    SearchInput,
    SmallActionButton,
    StatusActionCard,
    badge_cell,
    ComboSearchField,
    build_scroll_page,
    build_table_section,
    table_action_bar,
    action_table_row_height,
)


class RecordView(QWidget):
    """Interface d'enregistrement des présences — design moderne."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background-color: {COLORS['bg_primary']};")
        self._selected_emp: Employe | None = None
        self._stat_cards: dict[str, MiniStatCard] = {}
        self._current_filter_status = "Tous"
        self._current_search_text = ""
        self._build_ui()

        self._clock_timer = QTimer(self)
        self._clock_timer.timeout.connect(self._update_clock)
        self._clock_timer.start(1000)

        self._load_employees()
        self._refresh_dashboard()
        self._update_clock()

    def _build_ui(self):
        _, layout = build_scroll_page(self)

        header = PageHeader(
            "Enregistrer Présence",
            "Recherchez un employé et enregistrez son statut en un clic",
            icon_name="record",
        )
        refresh_btn = IconButton("refresh", "Actualiser", COLORS["accent_secondary"])
        refresh_btn.clicked.connect(self.refresh)
        header.add_action(refresh_btn)
        layout.addWidget(header)

        self.clock_banner_lbl = QLabel()
        self.clock_banner_lbl.setFont(QFont("Segoe UI", 12, QFont.DemiBold))
        self.clock_banner_lbl.setStyleSheet(
            f"color: {COLORS['accent_secondary']}; background: transparent; padding-left: 4px;"
        )
        layout.addWidget(self.clock_banner_lbl)

        top_row = QHBoxLayout()
        top_row.setSpacing(20)

        # ── Panneau gauche ────────────────────────────────────────────────
        left = QVBoxLayout()
        left.setSpacing(18)

        search_panel = QFrame()
        search_panel.setObjectName("agentSearchPanel")
        search_panel.setStyleSheet(f"""
            QFrame#agentSearchPanel {{
                background: {COLORS['bg_secondary']};
                border: 1px solid {COLORS['border']};
                border-radius: 20px;
            }}
        """)
        sp_lay = QVBoxLayout(search_panel)
        sp_lay.setContentsMargins(18, 18, 18, 18)
        sp_lay.setSpacing(12)

        sel_title = QLabel("Sélectionner un employé")
        sel_title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        sel_title.setStyleSheet(f"color: {COLORS['text_primary']};")
        sel_sub = QLabel("Recherchez par nom, prénom ou département")
        sel_sub.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px;")

        self.emp_combo = QComboBox()
        self.emp_combo.setEditable(True)
        line_edit = self.emp_combo.lineEdit()
        line_edit.setPlaceholderText("Tapez pour rechercher un employé...")
        line_edit.setStyleSheet(
            f"background: transparent; border: none; color: {COLORS['text_primary']}; "
            f"font-size: 13px; padding: 4px 0;"
        )
        self.emp_combo.setInsertPolicy(QComboBox.NoInsert)
        completer = self.emp_combo.completer()
        if completer:
            completer.setFilterMode(Qt.MatchContains)
            completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.emp_combo.currentIndexChanged.connect(self._on_employee_selected)

        sp_lay.addWidget(sel_title)
        sp_lay.addWidget(sel_sub)
        sp_lay.addWidget(ComboSearchField(self.emp_combo))
        left.addWidget(search_panel)

        # Fiche employé
        self.emp_card = QFrame()
        self.emp_card.setObjectName("agentEmpCard")
        self.emp_card.setStyleSheet(f"""
            QFrame#agentEmpCard {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 {hex_with_alpha(COLORS['accent_primary'], 28)},
                    stop:1 {hex_with_alpha(COLORS['accent_secondary'], 12)});
                border: 1px solid {hex_with_alpha(COLORS['accent_primary'], 50)};
                border-radius: 20px;
            }}
            QFrame#agentEmpCard QLabel {{ background: transparent; border: none; }}
        """)
        self.emp_card.hide()
        ec = QHBoxLayout(self.emp_card)
        ec.setContentsMargins(20, 18, 20, 18)
        ec.setSpacing(16)

        self.emp_avatar = QLabel()
        self.emp_avatar.setFixedSize(56, 56)
        self.emp_avatar.setAlignment(Qt.AlignCenter)
        self.emp_avatar.setFont(QFont("Segoe UI", 18, QFont.Bold))

        emp_info = QVBoxLayout()
        emp_info.setSpacing(2)
        self.emp_name_lbl = QLabel()
        self.emp_name_lbl.setFont(QFont("Segoe UI", 15, QFont.Bold))
        self.emp_id_lbl = QLabel()
        self.emp_id_lbl.setStyleSheet(f"color: {COLORS['accent_secondary']}; font-size: 12px;")
        self.emp_role_lbl = QLabel()
        self.emp_role_lbl.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px;")
        emp_info.addWidget(self.emp_name_lbl)
        emp_info.addWidget(self.emp_id_lbl)
        emp_info.addWidget(self.emp_role_lbl)

        last_col = QVBoxLayout()
        last_col.setSpacing(2)
        last_title = QLabel("DERNIER POINTAGE")
        last_title.setStyleSheet(
            f"color: {COLORS['text_muted']}; font-size: 10px; font-weight: 700; letter-spacing: 1px;"
        )
        self.emp_last_status = QLabel("—")
        self.emp_last_status.setFont(QFont("Segoe UI", 12, QFont.DemiBold))
        self.emp_last_type = QLabel("—")
        self.emp_last_type.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 11px;")
        last_col.addWidget(last_title)
        last_col.addWidget(self.emp_last_status)
        last_col.addWidget(self.emp_last_type)

        time_col = QVBoxLayout()
        time_col.setSpacing(2)
        time_title = QLabel("HEURE ACTUELLE")
        time_title.setStyleSheet(
            f"color: {COLORS['text_muted']}; font-size: 10px; font-weight: 700; letter-spacing: 1px;"
        )
        self.clock_lbl = QLabel()
        self.clock_lbl.setFont(QFont("Segoe UI", 16, QFont.Bold))
        self.date_lbl = QLabel()
        self.date_lbl.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 11px;")
        time_col.addWidget(time_title)
        time_col.addWidget(self.clock_lbl)
        time_col.addWidget(self.date_lbl)

        ec.addWidget(self.emp_avatar)
        ec.addLayout(emp_info, 2)
        ec.addLayout(last_col, 1)
        ec.addLayout(time_col, 1)
        left.addWidget(self.emp_card)

        # Statuts
        status_panel = QFrame()
        status_panel.setStyleSheet(f"""
            QFrame {{
                background: {COLORS['bg_secondary']};
                border: 1px solid {COLORS['border']};
                border-radius: 20px;
            }}
        """)
        st_lay = QVBoxLayout(status_panel)
        st_lay.setContentsMargins(18, 18, 18, 18)
        st_lay.setSpacing(14)

        st_title = QLabel("Définir le statut")
        st_title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        st_sub = QLabel("Choisissez le statut approprié pour l'employé sélectionné")
        st_sub.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px;")

        btn_grid = QGridLayout()
        btn_grid.setSpacing(12)
        self.btn_present = StatusActionCard(
            "Présent", "Marquer présent", "check", COLORS["accent_online"]
        )
        self.btn_retard = StatusActionCard(
            "Retard", "Arrivée tardive", "clock_alert", COLORS["accent_warning"]
        )
        self.btn_absent = StatusActionCard(
            "Absent", "Non présent", "status", COLORS["accent_danger"]
        )
        self.btn_conge = StatusActionCard(
            "Congé", "Permission", "calendar", COLORS["accent_primary"]
        )
        self.btn_tele = StatusActionCard(
            "Télétravail", "À distance", "home", COLORS["accent_secondary"]
        )
        self.btn_present.clicked.connect(self._record_entry)
        self.btn_retard.clicked.connect(self._record_entry)
        self.btn_absent.clicked.connect(lambda: self._record_absence("absent"))
        self.btn_conge.clicked.connect(lambda: self._record_absence("conge"))
        self.btn_tele.clicked.connect(lambda: self._record_absence("teletravail"))

        status_btns = [
            self.btn_present, self.btn_retard, self.btn_absent,
            self.btn_conge, self.btn_tele,
        ]
        for i, btn in enumerate(status_btns):
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            btn_grid.addWidget(btn, i // 3, i % 3)

        self.info_banner = InfoBanner(
            "Le pointage sera enregistré avec l'heure actuelle.",
            icon_name="clock_alert",
        )

        st_lay.addWidget(st_title)
        st_lay.addWidget(st_sub)
        st_lay.addLayout(btn_grid)
        st_lay.addWidget(self.info_banner)
        left.addWidget(status_panel)

        # ── Panneau droit (stats) ─────────────────────────────────────────
        right = QFrame()
        right.setObjectName("recordSummaryPanel")
        right.setFixedWidth(280)
        right.setStyleSheet(f"""
            QFrame#recordSummaryPanel {{
                background: {COLORS['bg_secondary']};
                border: 1px solid {COLORS['border']};
                border-radius: 20px;
            }}
            QFrame#recordSummaryPanel QLabel {{
                background: transparent;
                border: none;
            }}
        """)
        rp = QVBoxLayout(right)
        rp.setContentsMargins(16, 16, 16, 16)
        rp.setSpacing(10)

        rp_title = QLabel("Résumé du jour")
        rp_title.setFont(QFont("Segoe UI", 15, QFont.Bold))
        rp_title.setStyleSheet(f"color: {COLORS['text_primary']};")
        self.rp_date = QLabel()
        self.rp_date.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px;")
        rp.addWidget(rp_title)
        rp.addWidget(self.rp_date)
        rp.addSpacing(6)

        for key, label, val, icon, color in [
            ("present", "Présents", "0", "check", COLORS["accent_online"]),
            ("retard", "Retards", "0", "clock_alert", COLORS["accent_warning"]),
            ("absent", "Absents", "0", "status", COLORS["accent_danger"]),
            ("conge", "Congés", "0", "calendar", COLORS["accent_primary"]),
            ("total", "Total employés", "0", "employees", COLORS["accent_secondary"]),
        ]:
            card = MiniStatCard(label, val, icon, color)
            self._stat_cards[key] = card
            rp.addWidget(card)
        rp.addStretch()

        top_row.addLayout(left, 3)
        top_row.addWidget(right)
        layout.addLayout(top_row)

        # ── Derniers pointages ────────────────────────────────────────────
        filter_row = QHBoxLayout()
        self.table_search = SearchInput("Rechercher dans les pointages...")
        self.table_search.text_changed.connect(self._apply_table_search)
        filter_row.addWidget(self.table_search, 1)

        self.btn_filter = QPushButton("Filtrer")
        self.btn_filter.setProperty("class", "btn-secondary")
        self.btn_filter.setFixedHeight(44)
        self.btn_filter.setMinimumWidth(120)
        self.btn_filter.setCursor(QCursor(Qt.PointingHandCursor))
        filter_menu = QMenu(self.btn_filter)
        for status in ["Tous", "Présent", "Absent", "Retard", "Congé", "Télétravail"]:
            action = QAction(status, self)
            action.triggered.connect(lambda checked=False, s=status: self._apply_table_filter(s))
            filter_menu.addAction(action)
        self.btn_filter.setMenu(filter_menu)
        filter_row.addWidget(self.btn_filter)
        layout.addLayout(filter_row)

        table_header, self.count_lbl, self.table_container, table_lay = build_table_section(
            "Derniers pointages du jour"
        )
        layout.addLayout(table_header)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Employé", "Matricule", "Statut", "Heure", "Notes", "Actions"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Fixed)
        self.table.setColumnWidth(5, 200)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setMinimumHeight(300)
        self.table.verticalHeader().setDefaultSectionSize(56)
        self.table.setStyleSheet(
            "QTableWidget { background: transparent; border: none; border-radius: 20px; }"
        )
        table_lay.addWidget(self.table)
        self.table_container.setMinimumHeight(320)
        layout.addWidget(self.table_container, 1)

    def _load_employees(self):
        self.emp_combo.clear()
        self._all_employees = EmployeeService.get_all()
        for emp in self._all_employees:
            self.emp_combo.addItem(f"{emp.nom_complet} ({emp.departement})", emp.id)
        self.emp_combo.setCurrentIndex(-1)

    def _on_employee_selected(self, index: int):
        emp_id = self.emp_combo.currentData()
        if not emp_id:
            self.emp_card.hide()
            self._selected_emp = None
            return

        emp = EmployeeService.get_by_id(emp_id)
        if not emp:
            return

        self._selected_emp = emp
        initial = emp.prenom[:1].upper() if emp.prenom else "?"
        self.emp_avatar.setText(initial)
        self.emp_avatar.setStyleSheet(f"""
            color: white;
            background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                stop:0 {COLORS['accent_primary']}, stop:1 {COLORS['accent_secondary']});
            border-radius: 28px;
        """)
        self.emp_name_lbl.setText(emp.nom_complet)
        self.emp_id_lbl.setText(f"EMP{emp.id:03d}")
        self.emp_role_lbl.setText(f"{emp.poste} · {emp.departement}")

        from app.database.connection import db
        today = date.today().isoformat()
        existing = db.fetchone(
            "SELECT * FROM presences WHERE employe_id=? AND date=?",
            (emp.id, today),
        )
        if existing:
            self.emp_last_status.setText(f"Aujourd'hui à {existing.get('heure_entree', '—')}")
            self.emp_last_type.setText(f"Statut : {existing.get('statut', '—').capitalize()}")
        else:
            self.emp_last_status.setText("—")
            self.emp_last_type.setText("Aucun pointage")

        self.emp_card.show()

    def _record_entry(self):
        if not self._selected_emp:
            QMessageBox.warning(self, "Avertissement", "Veuillez sélectionner un employé.")
            return
        now_time = datetime.now().strftime("%H:%M")
        if not ("08:00" <= now_time <= "18:00"):
            QMessageBox.warning(
                self, "Hors horaires",
                "L'enregistrement de présence n'est possible qu'entre 08:00 et 18:00.",
            )
            return
        agent = AuthService.get_current_user()
        agent_id = agent.id if agent else 1
        result = AttendanceService.record_entry(self._selected_emp.id, agent_id)
        if result["success"]:
            self._on_success(f"Pointage enregistré pour {self._selected_emp.nom_complet}")

    def _record_absence(self, absence_type: str):
        if not self._selected_emp:
            QMessageBox.warning(self, "Avertissement", "Veuillez sélectionner un employé.")
            return
        if absence_type != "conge":
            now_time = datetime.now().strftime("%H:%M")
            if not ("08:00" <= now_time <= "18:00"):
                QMessageBox.warning(
                    self, "Hors horaires",
                    f"L'enregistrement du statut '{absence_type}' n'est possible qu'entre 08:00 et 18:00.",
                )
                return
        agent = AuthService.get_current_user()
        agent_id = agent.id if agent else 1
        ok = AttendanceService.record_absence(
            self._selected_emp.id, agent_id, absence_type, "Enregistré via interface rapide"
        )
        if ok:
            self._on_success(f"Statut {absence_type} enregistré pour {self._selected_emp.nom_complet}")

    def _on_success(self, msg: str):
        QMessageBox.information(self, "Succès", msg)
        self.emp_combo.setCurrentIndex(-1)
        self.emp_card.hide()
        self._selected_emp = None
        self._refresh_dashboard()

    def _update_clock(self):
        now = datetime.now()
        time_str = now.strftime("%H:%M:%S")
        self.clock_lbl.setText(time_str)
        date_str = now.strftime("%A %d %B %Y").capitalize()
        self.date_lbl.setText(date_str)
        self.rp_date.setText(date_str)
        self.clock_banner_lbl.setText(f"Heure actuelle : {time_str}  ·  {date_str}")
        self.info_banner.text_label.setText(
            f"Le pointage sera enregistré à {time_str}"
        )

    def _refresh_dashboard(self):
        stats = AttendanceService.get_today_stats()
        self._stat_cards["present"].set_value(f"{stats.presents_aujourd_hui:02d}")
        self._stat_cards["retard"].set_value(f"{stats.retards_aujourd_hui:02d}")
        self._stat_cards["absent"].set_value(f"{stats.absents_aujourd_hui:02d}")
        self._stat_cards["conge"].set_value(f"{stats.conges_aujourd_hui:02d}")
        self._stat_cards["total"].set_value(f"{stats.total_employes:02d}")
        self._load_recent_records()

    def _status_badge_key(self, record) -> str:
        if record.statut == "present" and record.retard:
            return "retard"
        if record.statut == "teletravail":
            return "teletravail"
        return record.statut

    def _load_recent_records(self):
        self.table.setRowCount(0)
        today = date.today().isoformat()
        records = AttendanceService.get_presences(date_debut=today, date_fin=today)
        records.reverse()

        for r in records[:20]:
            row = self.table.rowCount()
            self.table.insertRow(row)

            name_item = QTableWidgetItem(f"{r.employe_prenom} {r.employe_nom}")
            name_item.setFont(QFont("Segoe UI", 11, QFont.DemiBold))
            name_item.setData(Qt.UserRole, r.departement)
            self.table.setItem(row, 0, name_item)

            mat = QTableWidgetItem(f"EMP{r.employe_id:03d}")
            mat.setTextAlignment(Qt.AlignCenter)
            badge_key = self._status_badge_key(r)
            mat.setData(Qt.UserRole, badge_key)
            self.table.setItem(row, 1, mat)

            self.table.setCellWidget(row, 2, badge_cell(badge_key))

            ht = QTableWidgetItem(r.heure_entree or "—")
            ht.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 3, ht)

            notes = "Arrivée en retard" if r.retard else "—"
            if r.statut == "conge":
                notes = "Congé validé"
            elif r.statut == "teletravail":
                notes = "Travail à distance"
            nt = QTableWidgetItem(notes)
            nt.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 4, nt)

            view_btn = SmallActionButton("eye", "Voir", COLORS["accent_secondary"])
            edit_btn = SmallActionButton("edit", "Modifier", COLORS["accent_warning"])
            view_btn.clicked.connect(lambda _, rec=r: self._show_view_dialog(rec))
            edit_btn.clicked.connect(lambda _, rec=r: self._show_edit_dialog(rec))
            self.table.setCellWidget(row, 5, table_action_bar(view_btn, edit_btn))
            self.table.setRowHeight(row, action_table_row_height(36, 2))

        self.count_lbl.setText(f"{len(records[:20])} pointage(s) affiché(s)")
        self._filter_table_rows()

    def refresh(self):
        self._load_employees()
        self._refresh_dashboard()

    def _show_view_dialog(self, record):
        emp = EmployeeService.get_by_id(record.employe_id)
        if emp:
            ViewEmployeeDialog(emp, self).exec()

    def _apply_table_search(self, text: str):
        self._current_search_text = text.lower()
        self._filter_table_rows()

    def _apply_table_filter(self, status: str):
        self._current_filter_status = status
        self.btn_filter.setText("Filtrer" if status == "Tous" else status)
        self._filter_table_rows()

    def _filter_table_rows(self):
        status = self._current_filter_status
        search = self._current_search_text
        status_map = {
            "Présent": "present", "Absent": "absent", "Retard": "retard",
            "Congé": "conge", "Télétravail": "teletravail",
        }
        for row in range(self.table.rowCount()):
            show = True
            if status != "Tous":
                mat_item = self.table.item(row, 1)
                key = mat_item.data(Qt.UserRole) if mat_item else ""
                if status_map.get(status, status.lower()) not in str(key):
                    show = False
            if show and search:
                name = self.table.item(row, 0)
                mat = self.table.item(row, 1)
                match = (
                    (name and search in name.text().lower())
                    or (mat and search in mat.text().lower())
                )
                if not match:
                    show = False
            self.table.setRowHidden(row, not show)

    def _show_edit_dialog(self, record):
        if EditRecordDialog(record, self).exec() == QDialog.Accepted:
            self._refresh_dashboard()


class ViewEmployeeDialog(QDialog):
    def __init__(self, emp: Employe, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Informations — {emp.nom_complet}")
        self.setMinimumWidth(440)
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {COLORS['bg_secondary']};
                border: 1px solid {COLORS['border']};
                border-radius: 20px;
            }}
        """)
        
        # Désactiver le bouton d'aide dans la barre de titre
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        # ── En-tête (Avatar + Nom & Poste) ───────────────────────────────────
        header_layout = QHBoxLayout()
        header_layout.setSpacing(16)

        # Avatar circulaire avec initiales
        avatar = QLabel()
        avatar.setFixedSize(64, 64)
        avatar.setAlignment(Qt.AlignCenter)
        avatar.setFont(QFont("Segoe UI", 20, QFont.Bold))
        
        initials = ""
        if emp.prenom:
            initials += emp.prenom[0].upper()
        if emp.nom:
            initials += emp.nom[0].upper()
        if not initials:
            initials = "?"
            
        avatar.setText(initials)
        avatar.setStyleSheet(f"""
            color: white;
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 {COLORS['accent_primary']}, stop:1 {COLORS['accent_secondary']});
            border-radius: 32px;
            border: 2px solid {COLORS['border']};
        """)
        
        text_layout = QVBoxLayout()
        text_layout.setSpacing(4)
        
        name_lbl = QLabel(emp.nom_complet)
        name_lbl.setFont(QFont("Segoe UI", 16, QFont.Bold))
        name_lbl.setStyleSheet(f"color: {COLORS['text_primary']};")
        
        role_lbl = QLabel(f"{emp.poste} · {emp.departement}")
        role_lbl.setFont(QFont("Segoe UI", 11))
        role_lbl.setStyleSheet(f"color: {COLORS['text_secondary']};")
        
        text_layout.addWidget(name_lbl)
        text_layout.addWidget(role_lbl)
        
        header_layout.addWidget(avatar)
        header_layout.addLayout(text_layout, 1)
        layout.addLayout(header_layout)

        # Séparateur
        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setStyleSheet(f"background-color: {COLORS['border']}; max-height: 1px; border: none;")
        layout.addWidget(divider)

        # ── Cartes d'informations ─────────────────────────────────────────────
        from app.utils.icons import get_pixmap
        
        info_items = [
            ("Matricule", f"EMP{emp.id:03d}", "mdi6.card-account-details-outline"),
            ("Département", emp.departement, "building"),
            ("Poste", emp.poste, "users"),
            ("Téléphone", emp.telephone or "—", "mdi6.phone"),
            ("Email", emp.email or "—", "mdi6.email-outline"),
        ]

        for label, val, icon_name in info_items:
            row_frame = QFrame()
            row_frame.setStyleSheet(f"""
                QFrame {{
                    background: {hex_with_alpha(COLORS['bg_primary'], 140)};
                    border: 1px solid {COLORS['border_light']};
                    border-radius: 12px;
                }}
                QFrame:hover {{
                    background: {hex_with_alpha(COLORS['bg_hover'], 120)};
                    border-color: {hex_with_alpha(COLORS['accent_secondary'], 80)};
                }}
            """)
            row_layout = QHBoxLayout(row_frame)
            row_layout.setContentsMargins(14, 10, 14, 10)
            row_layout.setSpacing(14)

            # Conteneur d'icône
            icon_lbl = QLabel()
            icon_lbl.setFixedSize(32, 32)
            icon_lbl.setAlignment(Qt.AlignCenter)
            icon_lbl.setStyleSheet(f"""
                background: {hex_with_alpha(COLORS['accent_secondary'], 25)};
                border-radius: 8px;
                border: none;
            """)
            px = get_pixmap(icon_name, 16, COLORS["accent_secondary"])
            icon_lbl.setPixmap(px)
            row_layout.addWidget(icon_lbl)

            # Textes
            val_layout = QVBoxLayout()
            val_layout.setSpacing(2)
            
            lbl_key = QLabel(label.upper())
            lbl_key.setFont(QFont("Segoe UI", 9, QFont.Bold))
            lbl_key.setStyleSheet(f"color: {COLORS['text_muted']}; letter-spacing: 0.5px; border: none; background: transparent;")
            
            lbl_val = QLabel(val)
            lbl_val.setFont(QFont("Segoe UI", 11, QFont.DemiBold))
            lbl_val.setStyleSheet(f"color: {COLORS['text_primary']}; border: none; background: transparent;")
            lbl_val.setTextInteractionFlags(Qt.TextSelectableByMouse)
            
            val_layout.addWidget(lbl_key)
            val_layout.addWidget(lbl_val)
            row_layout.addLayout(val_layout, 1)

            layout.addWidget(row_frame)

        layout.addSpacing(6)

        # Bouton Fermer
        btn = QPushButton("Fermer")
        btn.setProperty("class", "btn-secondary")
        btn.setFixedHeight(44)
        btn.setCursor(QCursor(Qt.PointingHandCursor))
        btn.clicked.connect(self.accept)
        layout.addWidget(btn)


class EditRecordDialog(QDialog):
    def __init__(self, record, parent=None):
        super().__init__(parent)
        self.record = record
        self.setWindowTitle("Modifier le pointage")
        self.setMinimumWidth(380)
        self.setStyleSheet(
            f"QDialog {{ background: {COLORS['bg_secondary']}; border-radius: 16px; }}"
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        form = QFormLayout()
        self.statut_combo = QComboBox()
        self.statut_combo.addItems(["present", "absent", "retard", "conge", "teletravail"])
        self.statut_combo.setCurrentText(record.statut if not record.retard else "retard")
        self.heure_input = QLineEdit(record.heure_entree or "")
        self.notes_input = QLineEdit(getattr(record, "notes", "") or "")
        form.addRow("Statut:", self.statut_combo)
        form.addRow("Heure:", self.heure_input)
        form.addRow("Notes:", self.notes_input)
        layout.addLayout(form)
        btns = QHBoxLayout()
        save_btn = QPushButton("Enregistrer")
        save_btn.setProperty("class", "btn-success")
        save_btn.clicked.connect(self._save)
        cancel_btn = QPushButton("Annuler")
        cancel_btn.setProperty("class", "btn-secondary")
        cancel_btn.clicked.connect(self.reject)
        btns.addWidget(save_btn)
        btns.addWidget(cancel_btn)
        layout.addLayout(btns)

    def _save(self):
        AttendanceService.update_record(
            self.record.id,
            self.statut_combo.currentText(),
            self.heure_input.text(),
            self.notes_input.text(),
        )
        self.accept()
