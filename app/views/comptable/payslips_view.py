"""
Vue Bulletins de Paie — Split Pane avec prévisualisation premium du bulletin.
"""
import os
import subprocess
from datetime import datetime

from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont, QColor
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from app.services.payroll_service import PayrollService
from app.services.payslip_pdf_service import PayslipPdfService
from app.utils.theme import COLORS, hex_with_alpha
from app.widgets.ui_primitives import (
    AnimatedStatCard,
    BulletinPreviewCard,
    FilterField,
    GlowButton,
    PageHeader,
    SmallActionButton,
)


class PayslipsView(QWidget):
    """Bulletins de paie — Split Pane + prévisualisation premium."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background-color: {COLORS['bg_primary']};")
        self._bulletins: list = []
        self._kpi_cards: dict[str, AnimatedStatCard] = {}
        self._selected_id: int | None = None
        self._build_ui()

    # ── Build ────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        c = COLORS
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 16, 20, 16)
        root.setSpacing(14)

        # Header
        header = PageHeader(
            "Bulletins de Paie",
            "Consultez et exportez les fiches de paie mensuelles",
            icon_name="payslips",
        )
        refresh_btn = GlowButton("Actualiser",      c["accent_secondary"], "refresh")
        pdf_all_btn = GlowButton("PDF — Tous",      c["accent_danger"],    "pdf")
        refresh_btn.clicked.connect(self.refresh)
        pdf_all_btn.clicked.connect(self._generate_all_pdf)
        header.add_action(refresh_btn)
        header.add_action(pdf_all_btn)
        root.addWidget(header)

        # Splitter
        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)
        splitter.setHandleWidth(2)
        splitter.setStyleSheet(f"QSplitter::handle {{ background: {c['border']}; }}")
        root.addWidget(splitter, 1)

        # ════════════════════════════════════════════
        # LEFT PANE
        # ════════════════════════════════════════════
        left = QWidget()
        left.setStyleSheet("background: transparent;")
        left_lay = QVBoxLayout(left)
        left_lay.setContentsMargins(0, 0, 12, 0)
        left_lay.setSpacing(12)

        # Période combo
        self._periode_combo = QComboBox()
        self._periode_combo.setFixedHeight(44)
        self._periode_combo.setFont(QFont("Segoe UI", 12))
        self._periode_combo.addItem("Toutes les périodes", "")
        now = datetime.now()
        for i in range(12):
            m = (now.month - i - 1) % 12 + 1
            y = now.year - ((now.month - i - 1) // 12)
            label = datetime(y, m, 1).strftime("%B %Y").capitalize()
            self._periode_combo.addItem(label, f"{y}-{m:02d}")
        self._periode_combo.currentIndexChanged.connect(self.refresh)
        left_lay.addWidget(FilterField("Période", "calendar", self._periode_combo))

        # KPI cards (vertical column on left)
        for key, lbl, icon, color in [
            ("count", "Bulletins",    "payslips", c["accent_secondary"]),
            ("brut",  "Total brut",   "salary",   c["accent_primary"]),
            ("net",   "Total net",    "chart",    c["accent_online"]),
            ("pdf",   "Avec PDF",     "pdf",      c["accent_danger"]),
        ]:
            card = AnimatedStatCard(lbl, "0", icon, color)
            card.setMinimumHeight(82)
            self._kpi_cards[key] = card
            left_lay.addWidget(card)

        # List
        lbl_list = QLabel("Bulletins")
        lbl_list.setFont(QFont("Segoe UI", 13, QFont.Bold))
        lbl_list.setStyleSheet(f"color: {c['text_primary']}; background: transparent; border: none;")
        left_lay.addWidget(lbl_list)

        self._bull_list = QListWidget()
        self._bull_list.setStyleSheet(f"""
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
            QListWidget::item:hover {{ background: {c['bg_hover']}; }}
            QListWidget::item:selected {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 {c['accent_primary']}, stop:1 {c['accent_secondary']});
                color: white;
            }}
        """)
        self._bull_list.itemSelectionChanged.connect(self._on_bulletin_selected)
        left_lay.addWidget(self._bull_list, 1)

        splitter.addWidget(left)

        # ════════════════════════════════════════════
        # RIGHT PANE — Preview
        # ════════════════════════════════════════════
        right = QWidget()
        right.setStyleSheet("background: transparent;")
        self._right_lay = QVBoxLayout(right)
        self._right_lay.setContentsMargins(12, 0, 0, 0)
        self._right_lay.setSpacing(0)

        self._empty_lbl = QLabel("← Sélectionnez un bulletin")
        self._empty_lbl.setAlignment(Qt.AlignCenter)
        self._empty_lbl.setFont(QFont("Segoe UI", 16))
        self._empty_lbl.setStyleSheet(f"color: {c['text_muted']}; background: transparent; border: none;")
        self._right_lay.addWidget(self._empty_lbl, 1, Qt.AlignCenter)

        self._preview_card = BulletinPreviewCard()
        self._preview_card.setVisible(False)
        self._right_lay.addWidget(self._preview_card, 1)



        splitter.addWidget(right)
        splitter.setSizes([320, 880])

    # ── Logic ────────────────────────────────────────────────────────────────────

    def refresh(self):
        periode = self._periode_combo.currentData() or None
        if periode == "":
            periode = None
        self._bulletins = PayrollService.get_bulletins(periode)
        self._populate_list()
        if self._selected_id and any(b.id == self._selected_id for b in self._bulletins):
            self._show_preview(self._selected_id)

    def _populate_list(self):
        bulletins = self._bulletins
        total_brut = sum(b.salaire_brut for b in bulletins)
        total_net  = sum(b.salaire_net  for b in bulletins)
        with_pdf   = sum(1 for b in bulletins if b.pdf_path and os.path.exists(b.pdf_path))

        self._kpi_cards["count"].animate_to(len(bulletins))
        self._kpi_cards["brut"].animate_to(int(total_brut), suffix=" MAD")
        self._kpi_cards["net"].animate_to(int(total_net),  suffix=" MAD")
        self._kpi_cards["pdf"].animate_to(with_pdf)

        self._bull_list.blockSignals(True)
        self._bull_list.clear()
        for b in bulletins:
            has_pdf = b.pdf_path and os.path.exists(b.pdf_path)
            icon = "📄" if has_pdf else "⏳"
            item = QListWidgetItem(f"  {icon}  {b.nom_complet}\n      {b.periode}")
            item.setData(Qt.UserRole, b.id)
            if not has_pdf:
                item.setForeground(QColor(COLORS["accent_warning"]))
            self._bull_list.addItem(item)
            if b.id == self._selected_id:
                self._bull_list.setCurrentItem(item)
        self._bull_list.blockSignals(False)

        if not bulletins:
            self._empty_lbl.setVisible(True)
            self._preview_card.setVisible(False)

    def _on_bulletin_selected(self):
        items = self._bull_list.selectedItems()
        if not items:
            return
        bid = items[0].data(Qt.UserRole)
        self._selected_id = bid
        self._show_preview(bid)

    def _show_preview(self, bulletin_id: int):
        b = next((x for x in self._bulletins if x.id == bulletin_id), None)
        if not b:
            return

        self._empty_lbl.setVisible(False)
        self._preview_card.setVisible(True)

        # Update content
        self._preview_card.update_bulletin(b)

        # Action buttons inside the card
        has_pdf = b.pdf_path and os.path.exists(b.pdf_path)
        actions: list = []

        if has_pdf:
            open_btn = GlowButton("Ouvrir PDF", COLORS["accent_online"], "pdf")
            open_btn.clicked.connect(lambda _, p=b.pdf_path: self._open_pdf(p))
            actions.append(open_btn)

        gen_btn = GlowButton(
            "Régénérer PDF" if has_pdf else "Générer PDF",
            COLORS["accent_danger"] if not has_pdf else COLORS["accent_warning"],
            "pdf"
        )
        gen_btn.clicked.connect(lambda _, bid=b.id: self._generate_pdf(bid))
        actions.append(gen_btn)

        self._preview_card.set_actions(actions)

    # ── PDF Actions ──────────────────────────────────────────────────────────────

    def _generate_pdf(self, bulletin_id: int):
        bulletin = PayrollService.get_bulletin_by_id(bulletin_id)
        if not bulletin:
            return
        try:
            path = PayslipPdfService.generate(bulletin)
            msg = QMessageBox(self)
            msg.setWindowTitle("PDF généré")
            msg.setText(f"✅  Fiche de paie enregistrée :\n\n{os.path.basename(path)}")
            msg.setIcon(QMessageBox.Information)
            msg.setStandardButtons(QMessageBox.Ok)
            open_btn = msg.addButton("Ouvrir le dossier", QMessageBox.ActionRole)
            msg.exec()
            if msg.clickedButton() == open_btn:
                subprocess.Popen(f'explorer /select,"{os.path.normpath(path)}"')
            self.refresh()
        except Exception as e:
            QMessageBox.critical(self, "Erreur PDF", str(e))

    def _generate_all_pdf(self):
        if not self._bulletins:
            QMessageBox.information(self, "Info", "Aucun bulletin à exporter.")
            return
        ok = 0
        last_path = None
        for b in self._bulletins:
            try:
                path = PayslipPdfService.generate(b)
                ok += 1
                last_path = path
            except Exception:
                pass
        
        msg = QMessageBox(self)
        msg.setWindowTitle("Terminé")
        msg.setText(f"✅  {ok} fiche(s) PDF générée(s).")
        msg.setIcon(QMessageBox.Information)
        msg.setStandardButtons(QMessageBox.Ok)
        if ok > 0 and last_path:
            open_btn = msg.addButton("Ouvrir le dossier", QMessageBox.ActionRole)
        else:
            open_btn = None
        msg.exec()
        if open_btn and msg.clickedButton() == open_btn:
            from app.config import EXPORT_DIR
            subprocess.Popen(f'explorer "{os.path.normpath(EXPORT_DIR)}"')
        self.refresh()

    def _open_pdf(self, path: str):
        if not path or not os.path.exists(path):
            QMessageBox.warning(self, "Introuvable", "Générez d'abord le PDF.")
            return
        try:
            os.startfile(path)
        except Exception:
            try:
                subprocess.Popen(["xdg-open", path])
            except Exception as e:
                QMessageBox.warning(self, "Erreur", str(e))
