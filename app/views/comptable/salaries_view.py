"""
Vue Salaires — consultation et modification des salaires de base.
Design premium avec FilterChips et SalaryProgressBar.
"""
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor
from PySide6.QtWidgets import (
    QButtonGroup,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QFrame,
)

from app.services.payroll_service import PayrollService
from app.utils.theme import COLORS, hex_with_alpha
from app.widgets.ui_primitives import (
    AnimatedStatCard,
    FilterChip,
    GlowButton,
    IconButton,
    PageHeader,
    SalaryProgressBar,
    SearchInput,
    SmallActionButton,
    build_scroll_page,
    build_table_section,
    table_action_bar,
    action_table_row_height,
)


class SalariesView(QWidget):
    """Gestion des salaires de base — design premium."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background-color: {COLORS['bg_primary']};")
        self._stat_cards: dict[str, AnimatedStatCard] = {}
        self._all_rows = []
        self._filter = "all"
        self._build_ui()

    # ── Build UI ────────────────────────────────────────────────────────────────

    def _build_ui(self):
        _, layout = build_scroll_page(self)

        # Header
        header = PageHeader(
            "Gestion des Salaires",
            "Consultez et configurez les salaires de base de chaque employé",
            icon_name="salary",
        )
        refresh_btn = GlowButton("Actualiser", COLORS["accent_secondary"], "refresh")
        refresh_btn.clicked.connect(self.refresh)
        header.add_action(refresh_btn)
        layout.addWidget(header)

        # KPI Cards
        kpi_row = QHBoxLayout()
        kpi_row.setSpacing(14)
        for key, lbl, val, icon, color in [
            ("total",      "Total employés",    "0",        "employees", COLORS["accent_secondary"]),
            ("configured", "Configurés",        "0",        "salary",    COLORS["accent_online"]),
            ("pending",    "Sans salaire",      "0",        "clock_alert", COLORS["accent_warning"]),
            ("avg",        "Salaire moyen",     "0 MAD",    "chart",     COLORS["accent_primary"]),
        ]:
            card = AnimatedStatCard(lbl, val, icon, color)
            self._stat_cards[key] = card
            kpi_row.addWidget(card, 1)
        layout.addLayout(kpi_row)

        # Filter + Search bar
        filter_row = QHBoxLayout()
        filter_row.setSpacing(10)

        self._search = SearchInput("Rechercher par nom, département, poste…")
        self._search.text_changed.connect(lambda _: self._apply_filter())
        filter_row.addWidget(self._search, 1)

        self._chip_grp = QButtonGroup(self)
        self._chip_grp.setExclusive(True)
        for label, fid, icon in [
            ("Tous",           "all",  "employees"),
            ("Configurés",     "conf", "salary"),
            ("Sans salaire",   "pend", "clock_alert"),
        ]:
            chip = FilterChip(label, icon)
            self._chip_grp.addButton(chip)
            chip.setProperty("fid", fid)
            filter_row.addWidget(chip)
        self._chip_grp.buttons()[0].setChecked(True)
        self._chip_grp.buttonClicked.connect(self._on_chip_clicked)

        layout.addLayout(filter_row)

        # Table
        tbl_header, self._count_lbl, self._table_wrap, tbl_lay = build_table_section(
            "Liste des salaires"
        )
        layout.addLayout(tbl_header)

        self._table = QTableWidget()
        self._table.setColumnCount(6)
        self._table.setHorizontalHeaderLabels([
            "ID", "Nom complet", "Département / Poste",
            "Salaire de base", "Taux horaire", "Action",
        ])
        hh = self._table.horizontalHeader()
        hh.setSectionResizeMode(QHeaderView.Stretch)
        hh.setSectionResizeMode(0, QHeaderView.Fixed);  self._table.setColumnWidth(0, 52)
        hh.setSectionResizeMode(3, QHeaderView.Fixed);  self._table.setColumnWidth(3, 280)
        hh.setSectionResizeMode(4, QHeaderView.Fixed);  self._table.setColumnWidth(4, 120)
        hh.setSectionResizeMode(5, QHeaderView.Fixed);  self._table.setColumnWidth(5, 80)
        self._table.setSelectionBehavior(QTableWidget.SelectRows)
        self._table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._table.setAlternatingRowColors(True)
        self._table.verticalHeader().setVisible(False)
        self._table.setShowGrid(False)
        self._table.setStyleSheet("QTableWidget { background: transparent; border: none; }")
        tbl_lay.addWidget(self._table)
        layout.addWidget(self._table_wrap)

    # ── Slots ───────────────────────────────────────────────────────────────────

    def _on_chip_clicked(self, btn):
        self._filter = btn.property("fid")
        self._apply_filter()

    def _apply_filter(self):
        term   = self._search.text().lower()
        result = []
        for s in self._all_rows:
            if term and term not in s.nom_complet.lower() \
               and term not in (s.departement or "").lower() \
               and term not in (s.poste or "").lower():
                continue
            if self._filter == "conf" and s.salaire_base <= 0:
                continue
            if self._filter == "pend" and s.salaire_base > 0:
                continue
            result.append(s)
        self._populate(result)

    def refresh(self):
        self._all_rows = PayrollService.get_all_salaires()
        # Animate KPI cards
        conf = [s for s in self._all_rows if s.salaire_base > 0]
        pend = len(self._all_rows) - len(conf)
        avg  = int(sum(s.salaire_base for s in conf) / len(conf)) if conf else 0
        self._stat_cards["total"].animate_to(len(self._all_rows))
        self._stat_cards["configured"].animate_to(len(conf))
        self._stat_cards["pending"].animate_to(pend)
        self._stat_cards["avg"].animate_to(avg, suffix=" MAD")
        self._apply_filter()

    def _populate(self, rows):
        max_sal = max((s.salaire_base for s in self._all_rows if s.salaire_base > 0), default=1)
        self._count_lbl.setText(f"{len(rows)} employé(s)")
        self._table.setRowCount(len(rows))
        rh = action_table_row_height(36, 1)

        for i, s in enumerate(rows):
            self._table.setRowHeight(i, rh)
            configured = s.salaire_base > 0

            # Col 0 — ID
            id_item = QTableWidgetItem(str(s.employe_id))
            id_item.setTextAlignment(Qt.AlignCenter)
            self._table.setItem(i, 0, id_item)

            # Col 1 — Nom
            nom_item = QTableWidgetItem(s.nom_complet)
            nom_item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
            if not configured:
                nom_item.setForeground(QColor(COLORS["accent_warning"]))
            self._table.setItem(i, 1, nom_item)

            # Col 2 — Département / Poste
            dep_poste = f"{s.departement or '—'}  ·  {s.poste or '—'}"
            dp_item = QTableWidgetItem(dep_poste)
            dp_item.setStyleSheet if False else None  # unused
            dp_item.setForeground(QColor(COLORS["text_secondary"]))
            dp_item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
            self._table.setItem(i, 2, dp_item)

            # Col 3 — Salaire (progress bar or warning label)
            if configured:
                self._table.setCellWidget(i, 3, SalaryProgressBar(s.salaire_base, max_sal))
            else:
                w = QWidget()
                w.setStyleSheet("background: transparent;")
                wl = QHBoxLayout(w)
                wl.setContentsMargins(12, 0, 12, 0)
                lbl = QLabel("⚠  Non configuré")
                lbl.setFont(QFont("Segoe UI", 11))
                lbl.setStyleSheet(
                    f"color: {COLORS['accent_warning']}; background: transparent; border: none;"
                )
                wl.addWidget(lbl)
                self._table.setCellWidget(i, 3, w)

            # Col 4 — Taux horaire
            taux_str = (
                f"{s.taux_horaire:,.2f}".replace(",", " ")
                if s.taux_horaire else "—"
            )
            th_item = QTableWidgetItem(taux_str)
            th_item.setTextAlignment(Qt.AlignCenter)
            self._table.setItem(i, 4, th_item)

            # Col 5 — Edit button
            bar = table_action_bar()
            edit_btn = SmallActionButton("edit", "Modifier le salaire", COLORS["accent_primary"])
            edit_btn.clicked.connect(lambda _, eid=s.employe_id: self._open_edit(eid))
            bar.layout().addWidget(edit_btn)
            self._table.setCellWidget(i, 5, bar)

    # ── Dialog ──────────────────────────────────────────────────────────────────

    def _open_edit(self, employe_id: int):
        salaire = PayrollService.get_salaire(employe_id)
        if not salaire:
            from app.services.employee_service import EmployeeService
            emp = EmployeeService.get_by_id(employe_id)
            if not emp:
                return
            class _Stub:
                pass
            salaire = _Stub()
            salaire.employe_id  = employe_id
            salaire.nom_complet = emp.nom_complet
            salaire.salaire_base = 0.0
            salaire.taux_horaire = 0.0

        dlg = _SalaryDialog(salaire, self)
        if dlg.exec() == QDialog.Accepted:
            data = dlg.get_data()
            ok = PayrollService.set_salaire(employe_id, data["salaire_base"], data["taux_horaire"])
            if ok:
                QMessageBox.information(self, "Enregistré", "Salaire mis à jour avec succès.")
                self.refresh()
            else:
                QMessageBox.warning(self, "Erreur", "Impossible d'enregistrer le salaire.")


class _SalaryDialog(QDialog):
    """Dialog de modification de salaire — design premium."""

    def __init__(self, salaire, parent=None):
        super().__init__(parent)
        self.salaire = salaire
        self.setWindowTitle("Modifier le salaire")
        self.setMinimumWidth(440)
        c = COLORS
        self.setStyleSheet(f"""
            QDialog {{
                background: {c['bg_secondary']};
                border-radius: 20px;
            }}
            QLabel {{ background: transparent; border: none; }}
        """)
        self._build()

    def _build(self):
        c = COLORS
        lay = QVBoxLayout(self)
        lay.setContentsMargins(32, 30, 32, 30)
        lay.setSpacing(22)

        # Header
        hdr = QVBoxLayout()
        hdr.setSpacing(4)
        title = QLabel("Configuration du salaire")
        title.setFont(QFont("Segoe UI", 19, QFont.Bold))
        title.setStyleSheet(f"color: {c['text_primary']};")
        sub = QLabel(self.salaire.nom_complet)
        sub.setFont(QFont("Segoe UI", 13))
        sub.setStyleSheet(f"color: {c['accent_primary']};")
        hdr.addWidget(title)
        hdr.addWidget(sub)
        lay.addLayout(hdr)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"background: {c['border']}; border: none;")
        sep.setFixedHeight(1)
        lay.addWidget(sep)

        # Form
        form = QFormLayout()
        form.setSpacing(16)
        form.setLabelAlignment(Qt.AlignLeft)

        def _lbl(text):
            l = QLabel(text)
            l.setFont(QFont("Segoe UI", 11, QFont.DemiBold))
            l.setStyleSheet(f"color: {c['text_secondary']};")
            return l

        self._base_spin = QDoubleSpinBox()
        self._base_spin.setRange(0, 9_999_999)
        self._base_spin.setDecimals(2)
        self._base_spin.setSuffix("  MAD")
        self._base_spin.setFixedHeight(48)
        self._base_spin.setFont(QFont("Segoe UI", 13))
        self._base_spin.setValue(float(self.salaire.salaire_base or 0))
        self._base_spin.valueChanged.connect(self._auto_taux)

        self._taux_spin = QDoubleSpinBox()
        self._taux_spin.setRange(0, 99_999)
        self._taux_spin.setDecimals(2)
        self._taux_spin.setSuffix("  MAD/h")
        self._taux_spin.setFixedHeight(48)
        self._taux_spin.setFont(QFont("Segoe UI", 13))
        self._taux_spin.setValue(float(self.salaire.taux_horaire or 0))

        form.addRow(_lbl("Salaire de base mensuel *"), self._base_spin)
        form.addRow(_lbl("Taux horaire (auto-calculé)"), self._taux_spin)
        lay.addLayout(form)

        hint = QLabel("Le taux horaire est automatiquement calculé : salaire ÷ 173,33 h")
        hint.setStyleSheet(f"color: {c['text_muted']}; font-size: 11px;")
        hint.setWordWrap(True)
        lay.addWidget(hint)

        # Buttons
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        ok_btn = btns.button(QDialogButtonBox.Ok)
        ok_btn.setText("Enregistrer")
        ok_btn.setCursor(Qt.PointingHandCursor)
        ok_btn.setStyleSheet(f"""
            QPushButton {{
                background: {c['accent_primary']};
                color: white; border: none;
                border-radius: 12px; padding: 10px 24px;
                font-weight: 700; font-size: 13px;
            }}
            QPushButton:hover {{ background: {c['btn_primary_hover']}; }}
        """)
        cancel_btn = btns.button(QDialogButtonBox.Cancel)
        cancel_btn.setText("Annuler")
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background: {c['bg_tertiary']};
                color: {c['text_secondary']}; border: 1px solid {c['border']};
                border-radius: 12px; padding: 10px 24px;
            }}
            QPushButton:hover {{ background: {c['bg_hover']}; color: {c['text_primary']}; }}
        """)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        lay.addWidget(btns)

    def _auto_taux(self):
        base = self._base_spin.value()
        if base > 0:
            self._taux_spin.setValue(round(base / 173.33, 2))

    def get_data(self) -> dict:
        return {
            "salaire_base": self._base_spin.value(),
            "taux_horaire": self._taux_spin.value(),
        }
