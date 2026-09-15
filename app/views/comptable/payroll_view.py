"""
Vue Paie Mensuelle — Split Pane Maître-Détail premium.
Employés à gauche, détails + éléments de paie à droite.
"""
from datetime import datetime

from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont, QColor
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QFrame,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.services.employee_service import EmployeeService
from app.services.payroll_service import PayrollService
from app.utils.theme import COLORS, hex_with_alpha
from app.widgets.ui_primitives import (
    AnimatedStatCard,
    FilterField,
    GlowButton,
    PageHeader,
    SmallActionButton,
    build_table_section,
    table_action_bar,
    action_table_row_height,
)


# ── Helper: styled section title ────────────────────────────────────────────────
def _section_title(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setFont(QFont("Segoe UI", 13, QFont.Bold))
    lbl.setStyleSheet(f"color: {COLORS['text_primary']}; background: transparent; border: none;")
    return lbl


class PayrollView(QWidget):
    """Gestion mensuelle de la paie — Split Pane Maître-Détail."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background-color: {COLORS['bg_primary']};")
        self._employees = []
        self._elements  = []
        self._kpi_cards: dict[str, AnimatedStatCard] = {}
        self._selected_emp_id: int | None = None
        self._build_ui()
        self._load_employees()

    # ── Build ────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        c = COLORS
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 16, 20, 16)
        root.setSpacing(14)

        # Header
        header = PageHeader(
            "Paie Mensuelle",
            "Sélectionnez un employé pour gérer ses éléments de paie du mois",
            icon_name="payroll",
        )
        refresh_btn = GlowButton("Actualiser", c["accent_secondary"], "refresh")
        refresh_btn.clicked.connect(self.refresh)
        calc_all_btn = GlowButton("Calculer tous", c["accent_online"], "check")
        calc_all_btn.clicked.connect(self._calculate_all)
        header.add_action(refresh_btn)
        header.add_action(calc_all_btn)
        root.addWidget(header)

        # ── Splitter ─────────────────────────────────────────────────────────────
        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)
        splitter.setHandleWidth(2)
        splitter.setStyleSheet(f"""
            QSplitter::handle {{ background: {c['border']}; }}
        """)
        root.addWidget(splitter, 1)

        # ════════════════════════════════════════════
        # LEFT PANE — Employés
        # ════════════════════════════════════════════
        left = QWidget()
        left.setStyleSheet("background: transparent;")
        left_lay = QVBoxLayout(left)
        left_lay.setContentsMargins(0, 0, 12, 0)
        left_lay.setSpacing(12)

        # Période combobox
        self._periode_combo = QComboBox()
        self._periode_combo.setFixedHeight(44)
        self._periode_combo.setFont(QFont("Segoe UI", 12))
        now = datetime.now()
        for i in range(12):
            m = (now.month - i - 1) % 12 + 1
            y = now.year - ((now.month - i - 1) // 12)
            label = datetime(y, m, 1).strftime("%B %Y").capitalize()
            val   = f"{y}-{m:02d}"
            self._periode_combo.addItem(label, val)
        self._periode_combo.currentIndexChanged.connect(self._on_period_changed)

        left_lay.addWidget(FilterField("Période de paie", "calendar", self._periode_combo))
        left_lay.addWidget(_section_title("Employés"))

        self._emp_list = QListWidget()
        self._emp_list.setStyleSheet(f"""
            QListWidget {{
                background: {c['bg_secondary']};
                border: 1px solid {c['border']};
                border-radius: 18px;
                outline: none;
                padding: 8px;
            }}
            QListWidget::item {{
                padding: 14px 16px;
                border-radius: 10px;
                margin-bottom: 4px;
                color: {c['text_primary']};
                font-size: 13px;
            }}
            QListWidget::item:hover {{
                background: {c['bg_hover']};
            }}
            QListWidget::item:selected {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 {c['accent_primary']}, stop:1 {c['accent_secondary']});
                color: white;
            }}
        """)
        self._emp_list.itemSelectionChanged.connect(self._on_employee_selected)
        left_lay.addWidget(self._emp_list, 1)

        splitter.addWidget(left)

        # ════════════════════════════════════════════
        # RIGHT PANE — Détail
        # ════════════════════════════════════════════
        right = QWidget()
        right.setStyleSheet("background: transparent;")
        self._right_lay = QVBoxLayout(right)
        self._right_lay.setContentsMargins(12, 0, 0, 0)
        self._right_lay.setSpacing(14)

        # Empty state
        self._empty_lbl = QLabel("← Sélectionnez un employé")
        self._empty_lbl.setAlignment(Qt.AlignCenter)
        self._empty_lbl.setFont(QFont("Segoe UI", 16))
        self._empty_lbl.setStyleSheet(f"color: {c['text_muted']}; background: transparent; border: none;")
        self._right_lay.addWidget(self._empty_lbl, 1, Qt.AlignCenter)

        # Detail container (hidden until selection)
        self._detail_frame = QWidget()
        self._detail_frame.setStyleSheet("background: transparent;")
        detail_lay = QVBoxLayout(self._detail_frame)
        detail_lay.setContentsMargins(0, 0, 0, 0)
        detail_lay.setSpacing(14)

        # Employee name
        self._emp_title = QLabel("—")
        self._emp_title.setFont(QFont("Segoe UI", 22, QFont.Bold))
        self._emp_title.setStyleSheet(f"color: {c['text_primary']}; background: transparent; border: none;")
        detail_lay.addWidget(self._emp_title)

        # KPI cards
        kpi_row = QHBoxLayout()
        kpi_row.setSpacing(12)
        for key, lbl, icon, color in [
            ("base",   "Salaire base",   "salary",      c["accent_secondary"]),
            ("primes", "Primes",         "chart",       c["accent_online"]),
            ("hs",     "Heures sup.",    "clock_alert", c["accent_warning"]),
            ("net",    "Net estimé",     "payslips",    c["accent_primary"]),
        ]:
            card = AnimatedStatCard(lbl, "0", icon, color)
            self._kpi_cards[key] = card
            kpi_row.addWidget(card, 1)
        detail_lay.addLayout(kpi_row)

        # Action buttons
        actions_row = QHBoxLayout()
        actions_row.setSpacing(10)
        for txt, color, icon, handler in [
            ("+ Prime",       c["accent_online"],   "salary",      lambda: self._add_element("prime")),
            ("+ Heures sup.", c["accent_warning"],  "clock_alert", lambda: self._add_element("heures_sup")),
            ("+ Déduction",   c["accent_danger"],   "delete",      lambda: self._add_element("deduction")),
        ]:
            btn = GlowButton(txt, color, icon)
            btn.clicked.connect(handler)
            actions_row.addWidget(btn)
        actions_row.addStretch()
        calc_btn = GlowButton("Calculer la paie", c["accent_primary"], "check")
        calc_btn.clicked.connect(self._calculate_one)
        actions_row.addWidget(calc_btn)
        detail_lay.addLayout(actions_row)

        # Elements table
        tbl_hdr, self._count_lbl, self._tbl_wrap, tbl_lay = build_table_section(
            "Éléments de paie"
        )
        detail_lay.addLayout(tbl_hdr)

        self._table = QTableWidget()
        self._table.setColumnCount(6)
        self._table.setHorizontalHeaderLabels([
            "Type", "Libellé", "Heures", "Taux", "Montant (MAD)", "Actions"
        ])
        hh = self._table.horizontalHeader()
        hh.setSectionResizeMode(QHeaderView.Stretch)
        hh.setSectionResizeMode(5, QHeaderView.Fixed); self._table.setColumnWidth(5, 100)
        self._table.setSelectionBehavior(QTableWidget.SelectRows)
        self._table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._table.setAlternatingRowColors(True)
        self._table.verticalHeader().setVisible(False)
        self._table.setShowGrid(False)
        self._table.setStyleSheet("QTableWidget { background: transparent; border: none; }")
        tbl_lay.addWidget(self._table)
        detail_lay.addWidget(self._tbl_wrap, 1)

        self._right_lay.addWidget(self._detail_frame, 1)
        self._detail_frame.setVisible(False)



        splitter.addWidget(right)
        splitter.setSizes([300, 900])

    # ── Logic ────────────────────────────────────────────────────────────────────

    def _load_employees(self):
        self._employees = EmployeeService.get_all()
        self._populate_list()

    def _populate_list(self):
        periode = self._current_periode()
        self._emp_list.blockSignals(True)
        prev_id = self._selected_emp_id

        self._emp_list.clear()
        for emp in self._employees:
            preview = PayrollService.preview_calculation(emp.id, periode)
            has_base = preview["salaire_base"] > 0
            if has_base:
                net_str = f"{preview['salaire_net']:,.0f} MAD".replace(",", " ")
                icon = "✅"
            else:
                net_str = "Base non configurée"
                icon = "⚠"
            item = QListWidgetItem(f"  {icon}  {emp.nom_complet}\n      {net_str}")
            item.setData(Qt.UserRole, emp.id)
            if not has_base:
                item.setForeground(QColor(COLORS["accent_warning"]))
            self._emp_list.addItem(item)
            if emp.id == prev_id:
                self._emp_list.setCurrentItem(item)

        self._emp_list.blockSignals(False)

    def _on_period_changed(self):
        self._populate_list()
        if self._selected_emp_id:
            self._load_detail(self._selected_emp_id)

    def _on_employee_selected(self):
        items = self._emp_list.selectedItems()
        if not items:
            return
        emp_id = items[0].data(Qt.UserRole)
        if emp_id == self._selected_emp_id:
            return
        self._selected_emp_id = emp_id
        self._show_detail(emp_id)

    def _show_detail(self, emp_id: int):
        self._empty_lbl.setVisible(False)
        self._detail_frame.setVisible(True)
        self._load_detail(emp_id)

    def _load_detail(self, emp_id: int):
        emp = next((e for e in self._employees if e.id == emp_id), None)
        if emp:
            self._emp_title.setText(emp.nom_complet)
        periode = self._current_periode()
        preview = PayrollService.preview_calculation(emp_id, periode)
        self._kpi_cards["base"].animate_to(int(preview["salaire_base"]), suffix=" MAD")
        self._kpi_cards["primes"].animate_to(int(preview["total_primes"]), suffix=" MAD")
        self._kpi_cards["hs"].animate_to(int(preview["total_heures_sup"]), suffix=" MAD")
        self._kpi_cards["net"].animate_to(int(preview["salaire_net"]), suffix=" MAD")
        self._elements = PayrollService.get_elements(emp_id, periode)
        self._populate_elements()

    def _populate_elements(self):
        type_map  = {"prime": "Prime", "heures_sup": "Heures sup.", "deduction": "Déduction"}
        type_cols = {
            "prime":      COLORS["accent_online"],
            "heures_sup": COLORS["accent_warning"],
            "deduction":  COLORS["accent_danger"],
        }
        self._count_lbl.setText(f"{len(self._elements)} élément(s)")
        self._table.setRowCount(len(self._elements))
        rh = action_table_row_height(32, 2)

        for i, el in enumerate(self._elements):
            self._table.setRowHeight(i, rh)
            tc = type_cols.get(el.type_element, COLORS["text_primary"])
            cells = [
                (type_map.get(el.type_element, el.type_element), tc, Qt.AlignCenter),
                (el.libelle, COLORS["text_primary"], Qt.AlignVCenter | Qt.AlignLeft),
                (f"{el.heures:.1f}" if el.heures else "—", COLORS["text_secondary"], Qt.AlignCenter),
                (f"{el.taux:.2f}" if el.taux else "—", COLORS["text_secondary"], Qt.AlignCenter),
                (f"{el.montant:,.2f}".replace(",", " "), COLORS["text_primary"], Qt.AlignCenter),
            ]
            for col, (txt, col_c, align) in enumerate(cells):
                item = QTableWidgetItem(txt)
                item.setTextAlignment(align)
                item.setForeground(QColor(col_c))
                self._table.setItem(i, col, item)

            bar = table_action_bar()
            edit_b = SmallActionButton("edit",   "Modifier",   COLORS["accent_primary"])
            del_b  = SmallActionButton("delete", "Supprimer",  COLORS["accent_danger"])
            edit_b.clicked.connect(lambda _, eid=el.id: self._edit_element(eid))
            del_b.clicked.connect(lambda _,  eid=el.id: self._delete_element(eid))
            bar.layout().addWidget(edit_b)
            bar.layout().addWidget(del_b)
            self._table.setCellWidget(i, 5, bar)

    def _current_periode(self) -> str:
        return self._periode_combo.currentData() or datetime.now().strftime("%Y-%m")

    # ── Element CRUD ─────────────────────────────────────────────────────────────

    def _add_element(self, type_el: str):
        if not self._selected_emp_id:
            return
        dlg = _ElementDialog(type_el, parent=self)
        if dlg.exec() == QDialog.Accepted:
            data = dlg.get_data()
            ok = PayrollService.add_element(
                self._selected_emp_id, self._current_periode(), type_el,
                data["libelle"], data["montant"], data["heures"], data["taux"], data["notes"],
            )
            if ok:
                self._refresh_detail()
            else:
                QMessageBox.warning(self, "Erreur", "Impossible d'ajouter l'élément.")

    def _edit_element(self, element_id: int):
        el = next((e for e in self._elements if e.id == element_id), None)
        if not el:
            return
        dlg = _ElementDialog(el.type_element, el, parent=self)
        if dlg.exec() == QDialog.Accepted:
            data = dlg.get_data()
            if PayrollService.update_element(element_id, data["libelle"], data["montant"],
                                             data["heures"], data["taux"], data["notes"]):
                self._refresh_detail()

    def _delete_element(self, element_id: int):
        if QMessageBox.question(self, "Confirmer", "Supprimer cet élément ?") != QMessageBox.Yes:
            return
        if PayrollService.delete_element(element_id):
            self._refresh_detail()

    def _refresh_detail(self):
        if self._selected_emp_id:
            self._load_detail(self._selected_emp_id)
            self._populate_list()

    # ── Calculations ─────────────────────────────────────────────────────────────

    def _calculate_one(self):
        if not self._selected_emp_id:
            return
        b = PayrollService.calculate_bulletin(self._selected_emp_id, self._current_periode())
        if b:
            QMessageBox.information(
                self, "Bulletin calculé",
                f"✅  Bulletin généré pour {b.nom_complet}.\n"
                f"Brut : {b.salaire_brut:,.2f} MAD\nNet  : {b.salaire_net:,.2f} MAD".replace(",", " ")
            )
            self._refresh_detail()
        else:
            QMessageBox.warning(self, "Erreur",
                                "Impossible de calculer — salaire de base non configuré.")

    def _calculate_all(self):
        ok, fail = PayrollService.calculate_all(self._current_periode())
        QMessageBox.information(
            self, "Calcul terminé",
            f"✅  {ok} bulletin(s) calculé(s).\n⚠  {fail} ignoré(s) (salaire manquant)."
        )
        self._populate_list()

    def refresh(self):
        self._employees = EmployeeService.get_all()
        self._populate_list()
        if self._selected_emp_id:
            self._load_detail(self._selected_emp_id)


# ── Element Dialog ────────────────────────────────────────────────────────────────

class _ElementDialog(QDialog):
    _LABELS = {
        "prime":      ("Prime", COLORS["accent_online"]),
        "heures_sup": ("Heures supplémentaires", COLORS["accent_warning"]),
        "deduction":  ("Déduction", COLORS["accent_danger"]),
    }

    def __init__(self, type_el: str, element=None, parent=None):
        super().__init__(parent)
        self._type_el = type_el
        self._element = element
        lbl, color = self._LABELS.get(type_el, (type_el, COLORS["accent_primary"]))
        self.setWindowTitle(lbl)
        self.setMinimumWidth(450)
        c = COLORS
        self.setStyleSheet(f"QDialog {{ background: {c['bg_secondary']}; }} QLabel {{ background: transparent; border: none; }}")
        self._build(lbl, color)

    def _build(self, lbl_text: str, color: str):
        c = COLORS
        lay = QVBoxLayout(self)
        lay.setContentsMargins(30, 28, 30, 28)
        lay.setSpacing(20)

        title = QLabel(f"{'Modifier' if self._element else 'Ajouter'} — {lbl_text}")
        title.setFont(QFont("Segoe UI", 17, QFont.Bold))
        title.setStyleSheet(f"color: {color};")
        lay.addWidget(title)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"background: {c['border']}; border: none;")
        sep.setFixedHeight(1)
        lay.addWidget(sep)

        form = QFormLayout()
        form.setSpacing(14)

        def _lbl(t):
            l = QLabel(t)
            l.setFont(QFont("Segoe UI", 11, QFont.DemiBold))
            l.setStyleSheet(f"color: {c['text_secondary']};")
            return l

        self._libelle = QLineEdit()
        self._libelle.setFixedHeight(46)
        self._libelle.setFont(QFont("Segoe UI", 12))
        form.addRow(_lbl("Libellé *"), self._libelle)

        self._montant = QDoubleSpinBox()
        self._montant.setRange(0, 9_999_999); self._montant.setDecimals(2)
        self._montant.setSuffix("  MAD"); self._montant.setFixedHeight(46)
        self._montant.setFont(QFont("Segoe UI", 12))

        self._heures = QDoubleSpinBox()
        self._heures.setRange(0, 999); self._heures.setDecimals(1)
        self._heures.setSuffix("  h"); self._heures.setFixedHeight(46)
        self._heures.setFont(QFont("Segoe UI", 12))

        self._taux = QDoubleSpinBox()
        self._taux.setRange(0, 99_999); self._taux.setDecimals(2)
        self._taux.setSuffix("  MAD/h"); self._taux.setFixedHeight(46)
        self._taux.setFont(QFont("Segoe UI", 12))

        self._notes = QLineEdit()
        self._notes.setFixedHeight(46)
        self._notes.setFont(QFont("Segoe UI", 12))

        if self._type_el == "heures_sup":
            form.addRow(_lbl("Nombre d'heures *"), self._heures)
            form.addRow(_lbl("Taux (optionnel)"), self._taux)
        else:
            form.addRow(_lbl("Montant *"), self._montant)
        form.addRow(_lbl("Notes"), self._notes)
        lay.addLayout(form)

        if self._element:
            self._libelle.setText(self._element.libelle)
            self._montant.setValue(self._element.montant)
            self._heures.setValue(self._element.heures)
            self._taux.setValue(self._element.taux)
            self._notes.setText(self._element.notes)

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.button(QDialogButtonBox.Ok).setText("Enregistrer")
        btns.button(QDialogButtonBox.Ok).setCursor(Qt.PointingHandCursor)
        btns.button(QDialogButtonBox.Cancel).setCursor(Qt.PointingHandCursor)
        btns.accepted.connect(self._validate)
        btns.rejected.connect(self.reject)
        lay.addWidget(btns)

    def _validate(self):
        if not self._libelle.text().strip():
            QMessageBox.warning(self, "Requis", "Le libellé est obligatoire.")
            return
        if self._type_el == "heures_sup" and self._heures.value() <= 0:
            QMessageBox.warning(self, "Requis", "Indiquez le nombre d'heures.")
            return
        if self._type_el != "heures_sup" and self._montant.value() <= 0:
            QMessageBox.warning(self, "Requis", "Indiquez le montant.")
            return
        self.accept()

    def get_data(self) -> dict:
        return {
            "libelle": self._libelle.text().strip(),
            "montant": self._montant.value(),
            "heures":  self._heures.value(),
            "taux":    self._taux.value(),
            "notes":   self._notes.text().strip(),
        }
