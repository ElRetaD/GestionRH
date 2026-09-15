"""
Icônes vectorielles via qtawesome (Font Awesome / Material Design).
Centralise la création d'icônes thématisées pour toute l'application.
"""
from __future__ import annotations

import qtawesome as qta
from PySide6.QtGui import QIcon, QPixmap, QPainter
from PySide6.QtCore import Qt

from app.utils.theme import COLORS


# Mapping page_id → icône qtawesome
PAGE_ICONS: dict[str, str] = {
    "dashboard":  "mdi6.view-dashboard-outline",
    "employees":  "mdi6.account-group-outline",
    "attendance": "mdi6.calendar-check-outline",
    "absences":   "mdi6.calendar-remove-outline",
    "stats":      "mdi6.chart-bar",
    "history":    "mdi6.history",
    "reports":    "mdi6.file-chart-outline",
    "ai":         "mdi6.robot-outline",
    "users":      "mdi6.account-cog-outline",
    "record":     "mdi6.qrcode-scan",
    "today":      "mdi6.calendar-today-outline",
    "search":     "mdi6.magnify",
    "payroll_dashboard": "mdi6.view-dashboard-outline",
    "payroll_salaries":  "mdi6.cash-multiple",
    "payroll_monthly":   "mdi6.calculator-variant-outline",
    "payroll_payslips":  "mdi6.file-document-outline",
    "salary":     "mdi6.cash-multiple",
    "payroll":    "mdi6.calculator-variant-outline",
    "payslips":   "mdi6.file-document-outline",
    "agent_dashboard": "mdi6.view-dashboard-outline",
}

ACTION_ICONS: dict[str, str] = {
    "refresh":    "mdi6.refresh",
    "export":     "mdi6.file-export-outline",
    "search":     "mdi6.magnify",
    "calendar":   "mdi6.calendar-outline",
    "building":   "mdi6.domain",
    "filter":     "mdi6.filter-variant",
    "status":     "mdi6.flag-outline",
    "logout":     "mdi6.logout",
    "theme_dark": "mdi6.weather-night",
    "theme_light":"mdi6.white-balance-sunny",
    "chevron":    "mdi6.chevron-right",
    "add":        "mdi6.plus",
    "edit":       "mdi6.pencil-outline",
    "delete":     "mdi6.trash-can-outline",
    "qrcode":     "mdi6.qrcode",
    "history":    "mdi6.history",
    "users":      "mdi6.account-outline",
    "excel":      "mdi6.file-excel-outline",
    "csv":        "mdi6.file-delimited-outline",
    "pdf":        "mdi6.file-pdf-box",
    "chart":      "mdi6.chart-line",
    "shield":     "mdi6.shield-account-outline",
    "check":      "mdi6.check-circle-outline",
    "clock_alert":"mdi6.clock-alert-outline",
    "home":       "mdi6.home-outline",
    "eye":        "mdi6.eye-outline",
    "chevron_left":  "mdi6.chevron-left",
    "chevron_right": "mdi6.chevron-right",
}


def get_icon(name: str, color: str | None = None, scale: float = 1.0) -> QIcon:
    """Retourne une QIcon qtawesome avec la couleur du thème."""
    icon_key = PAGE_ICONS.get(name) or ACTION_ICONS.get(name) or name
    return qta.icon(icon_key, color=color or COLORS["text_secondary"], scale_factor=scale)


def get_pixmap(name: str, size: int = 20, color: str | None = None) -> QPixmap:
    """Pixmap prêt pour QLabel."""
    icon = get_icon(name, color)
    return icon.pixmap(size, size, QIcon.Normal, QIcon.Off)


def tint_pixmap(pixmap: QPixmap, color: str) -> QPixmap:
    """Teinte un pixmap monochrome."""
    tinted = QPixmap(pixmap.size())
    tinted.fill(Qt.transparent)
    painter = QPainter(tinted)
    painter.setCompositionMode(QPainter.CompositionMode_Source)
    painter.drawPixmap(0, 0, pixmap)
    painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
    painter.fillRect(tinted.rect(), color)
    painter.end()
    return tinted
