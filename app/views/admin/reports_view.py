"""
Vue Rapports — export Excel, CSV et PDF avec design premium.
"""
import subprocess

from PySide6.QtCore import QDate, QThread, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QGridLayout,
    QHBoxLayout,
    QMessageBox,
    QProgressBar,
    QVBoxLayout,
    QWidget,
)

from app.services.employee_service import EmployeeService
from app.services.report_service import ReportService
from app.utils.theme import COLORS
from app.widgets.date_edit import ThemedDateEdit
from app.widgets.ui_primitives import (
    ExportCard,
    FilterField,
    MiniStatCard,
    PageHeader,
    build_filter_panel,
    build_scroll_page,
)


class ExportWorker(QThread):
    """Thread d'export pour ne pas bloquer l'UI."""

    finished = Signal(str)
    error = Signal(str)

    def __init__(self, export_type: str, **kwargs):
        super().__init__()
        self.export_type = export_type
        self.kwargs = kwargs

    def run(self):
        try:
            if self.export_type == "excel":
                path = ReportService.export_excel(**self.kwargs)
            elif self.export_type == "csv":
                path = ReportService.export_csv(**self.kwargs)
            elif self.export_type == "pdf":
                path = ReportService.export_pdf(**self.kwargs)
            else:
                path = ""
            self.finished.emit(path)
        except Exception as e:
            self.error.emit(str(e))


class ReportsView(QWidget):
    """Vue d'export des rapports — design moderne."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background-color: {COLORS['bg_primary']};")
        self._build_ui()

    def _build_ui(self):
        _, layout = build_scroll_page(self)

        header = PageHeader(
            "Rapports & Exportation",
            "Générez et exportez vos données de présence en Excel, CSV ou PDF",
            icon_name="reports",
        )
        layout.addWidget(header)

        stats_row = QHBoxLayout()
        stats_row.setSpacing(14)
        for key, label, val, icon, color in [
            ("excel", "Format Excel", ".xlsx", "excel", COLORS["accent_online"]),
            ("csv", "Format CSV", ".csv", "csv", COLORS["accent_secondary"]),
            ("pdf", "Format PDF", ".pdf", "pdf", COLORS["accent_danger"]),
            ("range", "Période", "30j", "calendar", COLORS["accent_primary"]),
        ]:
            card = MiniStatCard(label, val, icon, color)
            if key == "range":
                self._range_card = card
            stats_row.addWidget(card, 1)
        layout.addLayout(stats_row)

        filter_panel, filter_grid = build_filter_panel("reportsFilters")
        self.date_from = ThemedDateEdit(QDate.currentDate().addDays(-30))
        self.date_to = ThemedDateEdit(QDate.currentDate())
        self.dept_combo = QComboBox()
        self.dept_combo.addItem("Tous")
        for dept in EmployeeService.get_departments():
            self.dept_combo.addItem(dept)

        filter_grid.addWidget(FilterField("Date début", "calendar", self.date_from), 0, 0)
        filter_grid.addWidget(FilterField("Date fin", "calendar", self.date_to), 0, 1)
        filter_grid.addWidget(FilterField("Département", "building", self.dept_combo), 0, 2)
        layout.addWidget(filter_panel)

        export_grid = QGridLayout()
        export_grid.setSpacing(16)

        exports = [
            ("Export Excel", "Fichier multi-feuilles compatible Microsoft Excel", "excel",
             COLORS["accent_online"], "Générer Excel", "excel"),
            ("Export CSV", "Données tabulaires compatibles tous tableurs", "csv",
             COLORS["accent_secondary"], "Générer CSV", "csv"),
            ("Export PDF", "Rapport professionnel formaté et paginé", "pdf",
             COLORS["accent_danger"], "Générer PDF", "pdf"),
        ]
        for col, (title, desc, icon, color, btn_text, etype) in enumerate(exports):
            card = ExportCard(title, desc, icon, color, btn_text)
            card.action_btn.clicked.connect(lambda _, e=etype: self._export(e))
            export_grid.addWidget(card, 0, col)
        layout.addLayout(export_grid)

        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.hide()
        self.progress.setFixedHeight(6)
        self.progress.setStyleSheet(f"""
            QProgressBar {{
                background: {COLORS['bg_tertiary']};
                border-radius: 4px;
                border: none;
            }}
            QProgressBar::chunk {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 {COLORS['accent_primary']}, stop:1 {COLORS['accent_secondary']});
                border-radius: 4px;
            }}
        """)
        layout.addWidget(self.progress)
        layout.addStretch()

        self.date_from.dateChanged.connect(self._update_range_label)
        self.date_to.dateChanged.connect(self._update_range_label)
        self._update_range_label()

    def _update_range_label(self):
        days = self.date_from.date().daysTo(self.date_to.date()) + 1
        self._range_card.set_value(f"{max(days, 1)}j")

    def _export(self, etype: str):
        dept = self.dept_combo.currentText()
        kwargs = {
            "date_debut": self.date_from.date().toString("yyyy-MM-dd"),
            "date_fin": self.date_to.date().toString("yyyy-MM-dd"),
        }
        if dept != "Tous":
            kwargs["departement"] = dept

        self.progress.show()
        self.worker = ExportWorker(etype, **kwargs)
        self.worker.finished.connect(self._on_export_done)
        self.worker.error.connect(self._on_export_error)
        self.worker.start()

    def _on_export_done(self, path: str):
        self.progress.hide()
        msg = QMessageBox(self)
        msg.setWindowTitle("Export réussi")
        msg.setText(f"Fichier exporté avec succès !\n\n{path}")
        msg.setStandardButtons(QMessageBox.Ok)
        open_btn = msg.addButton("Ouvrir le dossier", QMessageBox.ActionRole)
        msg.exec()
        if msg.clickedButton() == open_btn:
            subprocess.Popen(f'explorer /select,"{path}"')

    def _on_export_error(self, err: str):
        self.progress.hide()
        QMessageBox.critical(self, "Erreur d'export", f"Une erreur est survenue :\n{err}")
