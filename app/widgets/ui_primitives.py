"""
Composants UI réutilisables — boutons, en-têtes, filtres, badges.
Design premium avec icônes vectorielles et micro-animations.
"""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve, QSize, QTimer
from PySide6.QtGui import QFont, QCursor, QColor, QFontMetrics
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsDropShadowEffect,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QGridLayout,
    QVBoxLayout,
    QWidget,
)

from app.utils.theme import COLORS, hex_with_alpha
from app.utils.icons import get_pixmap, get_icon


class IconButton(QPushButton):
    """Bouton circulaire avec icône vectorielle et effet hover."""

    def __init__(
        self,
        icon_name: str,
        tooltip: str = "",
        accent: str | None = None,
        size: int = 44,
        parent=None,
    ):
        super().__init__(parent)
        self._icon_name = icon_name
        self._accent = accent or COLORS["accent_primary"]
        self._size = size
        self.setFixedSize(size, size)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setToolTip(tooltip)
        self._icon_lbl = QLabel(self)
        self._icon_lbl.setAlignment(Qt.AlignCenter)
        self._icon_lbl.setAttribute(Qt.WA_TransparentForMouseEvents)
        self._icon_lbl.setGeometry(0, 0, size, size)
        self._apply_icon(False)
        self._apply_style(False)

    def _apply_icon(self, hovered: bool):
        color = "#FFFFFF" if hovered else self._accent
        px = get_pixmap(self._icon_name, size=20, color=color)
        self._icon_lbl.setPixmap(px)

    def _apply_style(self, hovered: bool):
        bg = hex_with_alpha(self._accent, 55 if hovered else 28)
        border = self._accent if hovered else hex_with_alpha(self._accent, 70)
        self.setStyleSheet(f"""
            IconButton {{
                background: {bg};
                border: 1px solid {border};
                border-radius: {self._size // 2}px;
            }}
            IconButton:pressed {{
                background: {hex_with_alpha(self._accent, 80)};
            }}
        """)

    def enterEvent(self, event):
        self._apply_style(True)
        self._apply_icon(True)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._apply_style(False)
        self._apply_icon(False)
        super().leaveEvent(event)


class PrimaryButton(QPushButton):
    """Bouton principal avec icône et gradient."""

    def __init__(self, text: str, icon_name: str | None = None, parent=None):
        super().__init__(parent)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setFixedHeight(44)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 0, 22, 0)
        layout.setSpacing(8)

        if icon_name:
            icon_lbl = QLabel()
            icon_lbl.setFixedSize(18, 18)
            icon_lbl.setPixmap(get_pixmap(icon_name, 18, "#FFFFFF"))
            icon_lbl.setAttribute(Qt.WA_TransparentForMouseEvents)
            layout.addWidget(icon_lbl)

        btn_font = QFont("Segoe UI", 11, QFont.DemiBold)
        text_lbl = QLabel(text)
        text_lbl.setFont(btn_font)
        text_lbl.setStyleSheet("color: white; background: transparent; border: none;")
        text_lbl.setAttribute(Qt.WA_TransparentForMouseEvents)
        layout.addWidget(text_lbl)

        icon_extra = 26 if icon_name else 0
        text_w = QFontMetrics(btn_font).horizontalAdvance(text)
        self.setMinimumWidth(text_w + icon_extra + 64)

        c = COLORS
        self.setStyleSheet(f"""
            PrimaryButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {c['accent_primary']}, stop:1 {c['accent_secondary']});
                border: 1px solid {hex_with_alpha(c['accent_primary'], 90)};
                border-radius: 14px;
            }}
            PrimaryButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {c['btn_primary_hover']}, stop:1 {c['accent_secondary']});
            }}
            PrimaryButton:pressed {{
                background: {c['btn_primary_pressed']};
            }}
        """)


class PageHeader(QFrame):
    """En-tête de page avec titre, sous-titre et zone d'actions."""

    def __init__(
        self,
        title: str,
        subtitle: str = "",
        icon_name: str = "attendance",
        parent=None,
    ):
        super().__init__(parent)
        self.setObjectName("pageHeader")
        c = COLORS
        self.setStyleSheet(f"""
            QFrame#pageHeader {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {hex_with_alpha(c['accent_primary'], 32)},
                    stop:1 {hex_with_alpha(c['accent_secondary'], 14)});
                border: 1px solid {hex_with_alpha(c['accent_primary'], 60)};
                border-radius: 22px;
            }}
            QFrame#pageHeader QLabel {{
                background: transparent;
                border: none;
            }}
        """)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(40)
        shadow.setOffset(0, 12)
        sc = QColor(c["accent_primary"])
        sc.setAlpha(45)
        shadow.setColor(sc)
        self.setGraphicsEffect(shadow)

        root = QHBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(18)

        icon_wrap = QFrame()
        icon_wrap.setFixedSize(52, 52)
        icon_wrap.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {c['accent_primary']}, stop:1 {c['accent_secondary']});
                border-radius: 16px;
                border: none;
            }}
        """)
        icon_lay = QHBoxLayout(icon_wrap)
        icon_lbl = QLabel()
        icon_lbl.setPixmap(get_pixmap(icon_name, 26, "#FFFFFF"))
        icon_lbl.setAlignment(Qt.AlignCenter)
        icon_lay.addWidget(icon_lbl)
        root.addWidget(icon_wrap)

        text_col = QVBoxLayout()
        text_col.setSpacing(4)
        title_lbl = QLabel(title)
        title_lbl.setFont(QFont("Segoe UI", 24, QFont.Bold))
        title_lbl.setStyleSheet(f"color: {c['text_primary']};")
        sub_lbl = QLabel(subtitle)
        sub_lbl.setStyleSheet(f"color: {c['text_secondary']}; font-size: 13px;")
        text_col.addWidget(title_lbl)
        if subtitle:
            text_col.addWidget(sub_lbl)
        root.addLayout(text_col, 1)

        self.actions_layout = QHBoxLayout()
        self.actions_layout.setSpacing(10)
        root.addLayout(self.actions_layout)

    def add_action(self, widget: QWidget):
        self.actions_layout.addWidget(widget)


class FilterField(QFrame):
    """Champ de filtre avec icône, label et widget d'entrée."""

    def __init__(self, label: str, icon_name: str, widget: QWidget, parent=None):
        super().__init__(parent)
        self.setObjectName("filterField")
        c = COLORS
        self.setStyleSheet(f"""
            QFrame#filterField {{
                background: {c['bg_primary']};
                border: 1px solid {c['border']};
                border-radius: 16px;
            }}
            QFrame#filterField QLabel {{
                background: transparent;
                border: none;
            }}
        """)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 12, 14, 12)
        lay.setSpacing(8)

        header = QHBoxLayout()
        header.setSpacing(6)
        icon = QLabel()
        icon.setPixmap(get_pixmap(icon_name, 16, c["accent_secondary"]))
        lbl = QLabel(label)
        lbl.setStyleSheet(
            f"color: {c['text_muted']}; font-size: 11px; font-weight: 700; "
            f"letter-spacing: 0.5px;"
        )
        header.addWidget(icon)
        header.addWidget(lbl)
        header.addStretch()
        lay.addLayout(header)
        lay.addWidget(widget)


class SearchInput(QFrame):
    """Barre de recherche stylisée avec icône intégrée."""

    text_changed = Signal(str)

    def __init__(self, placeholder: str = "Rechercher...", parent=None):
        super().__init__(parent)
        c = COLORS
        self.setObjectName("searchInput")
        self.setStyleSheet(f"""
            QFrame#searchInput {{
                background: {c['input_bg']};
                border: 1px solid {c['input_border']};
                border-radius: 16px;
            }}
            QFrame#searchInput QLineEdit {{
                border: none;
                background: transparent;
                border-radius: 0px;
            }}
        """)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(14, 4, 14, 4)
        lay.setSpacing(10)

        icon = QLabel()
        icon.setPixmap(get_pixmap("search", 18, c["text_muted"]))
        lay.addWidget(icon)

        self.input = QLineEdit()
        self.input.setPlaceholderText(placeholder)
        self.input.setClearButtonEnabled(True)
        self.input.setStyleSheet(
            "border: none; background: transparent; padding: 8px 0; font-size: 13px;"
        )
        self.input.textChanged.connect(self.text_changed.emit)
        lay.addWidget(self.input, 1)

    def text(self) -> str:
        return self.input.text()


class ComboSearchField(QFrame):
    """ComboBox de recherche dans un conteneur arrondi avec icône."""

    def __init__(self, combo: QWidget, parent=None):
        super().__init__(parent)
        c = COLORS
        self.setObjectName("comboSearchField")
        self.setStyleSheet(f"""
            QFrame#comboSearchField {{
                background: {c['input_bg']};
                border: 1px solid {c['input_border']};
                border-radius: 16px;
            }}
            QFrame#comboSearchField QComboBox {{
                border: none;
                background: transparent;
                padding: 6px 4px;
                min-height: 36px;
            }}
            QFrame#comboSearchField QComboBox::drop-down {{
                border: none;
                width: 24px;
            }}
            QFrame#comboSearchField QComboBox::down-arrow {{
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 6px solid {c['text_muted']};
                margin-right: 6px;
            }}
            QFrame#comboSearchField QComboBox QAbstractItemView {{
                background: {c['bg_secondary']};
                border: 1px solid {c['border']};
                selection-background-color: {c['accent_primary']};
                selection-color: white;
            }}
        """)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(14, 4, 10, 4)
        lay.setSpacing(10)
        icon = QLabel()
        icon.setPixmap(get_pixmap("search", 18, c["text_muted"]))
        lay.addWidget(icon)
        lay.addWidget(combo, 1)


class MiniStatCard(QFrame):
    """Petite carte KPI pour les résumés de page."""

    def __init__(
        self,
        label: str,
        value: str,
        icon_name: str,
        color: str,
        parent=None,
    ):
        super().__init__(parent)
        c = COLORS
        self.setObjectName("miniStatCard")
        self.setMinimumHeight(80)
        self.setMinimumWidth(160)
        self.setStyleSheet(f"""
            QFrame#miniStatCard {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {hex_with_alpha(color, 38)},
                    stop:0.12 {c['bg_primary']},
                    stop:1 {c['bg_primary']});
                border: 1px solid {hex_with_alpha(color, 55)};
                border-radius: 16px;
            }}
            QFrame#miniStatCard QLabel {{
                background: transparent;
                border: none;
            }}
        """)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(16, 12, 14, 12)
        lay.setSpacing(12)

        text_col = QVBoxLayout()
        text_col.setSpacing(2)
        lbl = QLabel(label.upper())
        lbl.setStyleSheet(
            f"color: {c['text_muted']}; font-size: 10px; font-weight: 700; "
            f"letter-spacing: 1px;"
        )
        self.value_lbl = QLabel(value)
        self.value_lbl.setFont(QFont("Segoe UI", 26, QFont.Bold))
        self.value_lbl.setStyleSheet(f"color: {color};")
        text_col.addWidget(lbl)
        text_col.addWidget(self.value_lbl)
        lay.addLayout(text_col, 1)

        icon_wrap = QLabel()
        icon_wrap.setFixedSize(40, 40)
        icon_wrap.setAlignment(Qt.AlignCenter)
        icon_wrap.setStyleSheet(
            f"background: {hex_with_alpha(color, 30)}; border-radius: 12px;"
        )
        px = get_pixmap(icon_name, 20, color)
        inner = QLabel(icon_wrap)
        inner.setPixmap(px)
        inner.setAlignment(Qt.AlignCenter)
        inner.setGeometry(10, 10, 20, 20)
        lay.addWidget(icon_wrap)

    def set_value(self, value: str):
        self.value_lbl.setText(str(value))


class SmallActionButton(QPushButton):
    """Bouton d'action compact pour les lignes de tableau."""

    def __init__(self, icon_name: str, tooltip: str, accent: str, size: int = 36, parent=None):
        super().__init__(parent)
        self._icon_name = icon_name
        self._accent = accent
        self._size = size
        self._hovered = False
        self.setFixedSize(size, size)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setToolTip(tooltip)
        self.setProperty("class", "btn-action")
        self.setIconSize(QSize(18, 18))
        self.setFlat(True)
        self._apply_style(False)

    def _apply_style(self, hovered: bool):
        sz = self._size
        if not self.isEnabled():
            self.setIcon(get_icon(self._icon_name, COLORS["text_muted"]))
            self.setStyleSheet(f"""
                SmallActionButton {{
                    background: {COLORS['bg_tertiary']};
                    border: 1px solid {COLORS['border']};
                    border-radius: 10px;
                    padding: 0px;
                    margin: 0px;
                    min-width: {sz}px;
                    max-width: {sz}px;
                    min-height: {sz}px;
                    max-height: {sz}px;
                }}
            """)
            return

        color = "#FFFFFF" if hovered else self._accent
        self.setIcon(get_icon(self._icon_name, color))
        bg = self._accent if hovered else hex_with_alpha(self._accent, 30)
        border = self._accent if hovered else hex_with_alpha(self._accent, 65)
        self.setStyleSheet(f"""
            SmallActionButton {{
                background: {bg};
                border: 1px solid {border};
                border-radius: 10px;
                padding: 0px;
                margin: 0px;
                min-width: {sz}px;
                max-width: {sz}px;
                min-height: {sz}px;
                max-height: {sz}px;
            }}
        """)

    def enterEvent(self, event):
        self._hovered = True
        self._apply_style(True)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hovered = False
        self._apply_style(False)
        super().leaveEvent(event)

    def setEnabled(self, enabled: bool):
        super().setEnabled(enabled)
        self._apply_style(self._hovered and enabled)


def table_action_bar(*buttons: QPushButton) -> QWidget:
    """Barre d'actions centrée pour une cellule de tableau."""
    wrap = QWidget()
    wrap.setStyleSheet("background: transparent;")
    lay = QHBoxLayout(wrap)
    lay.setContentsMargins(6, 4, 6, 4)
    lay.setSpacing(8)
    lay.setAlignment(Qt.AlignCenter)
    for btn in buttons:
        lay.addWidget(btn, 0, Qt.AlignCenter)
    return wrap


def action_table_row_height(button_size: int = 36, button_count: int = 2) -> int:
    """Hauteur de ligne adaptée aux boutons d'action."""
    return button_size + 20


class StatusBadge(QLabel):
    """Badge pill coloré pour statuts."""

    STYLES = {
        "present":   ("Présent",   "accent_online"),
        "absent":    ("Absent",    "accent_danger"),
        "conge":     ("Congé",     "accent_warning"),
        "maladie":   ("Maladie",   "accent_primary"),
        "retard":    ("Retard",    "accent_warning"),
        "ok":        ("A l'heure", "accent_online"),
        "yes":       ("Oui",       "accent_online"),
        "no":        ("Non",       "accent_danger"),
        "entree":    ("Entrée",    "accent_online"),
        "sortie":    ("Sortie",    "accent_secondary"),
        "absence":   ("Absence",   "accent_danger"),
        "connexion": ("Connexion", "accent_teal"),
        "admin":     ("Administrateur", "accent_warning"),
        "agent":     ("Assistant RH",   "accent_secondary"),
        "comptable": ("Comptable",      "accent_teal"),
        "active":    ("Actif",          "accent_online"),
        "inactive":  ("Inactif",        "accent_danger"),
        "teletravail": ("Télétravail",  "accent_secondary"),
    }

    def __init__(self, status_key: str, parent=None):
        super().__init__(parent)
        label, color_key = self.STYLES.get(status_key, (status_key, "text_secondary"))
        color = COLORS.get(color_key, COLORS["text_secondary"])
        self.setText(label)
        self.setAlignment(Qt.AlignCenter)
        self.setFixedHeight(30)
        self.setMinimumWidth(90)
        self.setFont(QFont("Segoe UI", 9, QFont.DemiBold))
        self.setStyleSheet(f"""
            background: {hex_with_alpha(color, 35)};
            color: {color};
            border: 1px solid {hex_with_alpha(color, 70)};
            border-radius: 15px;
            padding: 2px 16px 2px 16px;
        """)


def badge_cell(status_key: str) -> QWidget:
    """Emballe un StatusBadge centré pour une cellule de tableau."""
    wrap = QWidget()
    wrap.setStyleSheet("background: transparent;")
    lay = QHBoxLayout(wrap)
    lay.setContentsMargins(4, 4, 4, 4)
    lay.addWidget(StatusBadge(status_key), 0, Qt.AlignCenter)
    return wrap


def build_scroll_page(parent: QWidget) -> tuple[QScrollArea, QVBoxLayout]:
    """Crée une page scrollable avec layout interne standard."""
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QFrame.NoFrame)
    scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

    container = QWidget()
    container.setStyleSheet("background: transparent;")
    scroll.setWidget(container)

    root = QVBoxLayout(parent)
    root.setContentsMargins(0, 0, 0, 0)
    root.addWidget(scroll)

    layout = QVBoxLayout(container)
    layout.setContentsMargins(28, 24, 28, 28)
    layout.setSpacing(22)
    return scroll, layout


def build_filter_panel(object_name: str = "filterPanel") -> tuple[QFrame, QGridLayout]:
    """Panneau de filtres avec fond arrondi."""
    panel = QFrame()
    panel.setObjectName(object_name)
    panel.setStyleSheet(f"""
        QFrame#{object_name} {{
            background: {COLORS['bg_secondary']};
            border: 1px solid {COLORS['border']};
            border-radius: 20px;
        }}
    """)
    grid = QGridLayout(panel)
    grid.setContentsMargins(18, 18, 18, 18)
    grid.setHorizontalSpacing(14)
    grid.setVerticalSpacing(14)
    return panel, grid


class StatusActionCard(QFrame):
    """Carte cliquable pour enregistrer un statut de présence."""

    clicked = Signal()

    def __init__(
        self,
        title: str,
        subtitle: str,
        icon_name: str,
        color: str,
        parent=None,
    ):
        super().__init__(parent)
        self._color = color
        self._hovered = False
        self.setObjectName("statusActionCard")
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setMinimumSize(130, 120)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 14, 12, 12)
        lay.setSpacing(6)
        lay.setAlignment(Qt.AlignCenter)

        icon_wrap = QLabel()
        icon_wrap.setFixedSize(44, 44)
        icon_wrap.setAlignment(Qt.AlignCenter)
        icon_wrap.setPixmap(get_pixmap(icon_name, 22, color))
        icon_wrap.setStyleSheet(
            f"background: {hex_with_alpha(color, 28)}; border-radius: 12px;"
        )

        title_lbl = QLabel(title)
        title_lbl.setFont(QFont("Segoe UI", 11, QFont.Bold))
        title_lbl.setAlignment(Qt.AlignCenter)
        title_lbl.setStyleSheet(f"color: {color}; background: transparent; border: none;")

        sub_lbl = QLabel(subtitle)
        sub_lbl.setFont(QFont("Segoe UI", 9))
        sub_lbl.setAlignment(Qt.AlignCenter)
        sub_lbl.setWordWrap(True)
        sub_lbl.setStyleSheet(
            f"color: {COLORS['text_muted']}; background: transparent; border: none;"
        )

        lay.addWidget(icon_wrap, 0, Qt.AlignCenter)
        lay.addWidget(title_lbl)
        lay.addWidget(sub_lbl)
        self._apply_style(False)

    def _apply_style(self, hovered: bool):
        color = self._color
        bg = hex_with_alpha(color, 18) if hovered else COLORS["bg_primary"]
        border = color if hovered else COLORS["border"]
        self.setStyleSheet(f"""
            QFrame#statusActionCard {{
                background: {bg};
                border: 1px solid {border};
                border-radius: 16px;
            }}
            QFrame#statusActionCard QLabel {{
                background: transparent;
                border: none;
            }}
        """)

    def enterEvent(self, event):
        self._hovered = True
        self._apply_style(True)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hovered = False
        self._apply_style(False)
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


def make_chart_card(title: str, subtitle: str = "") -> QFrame:
    """Conteneur carte pour graphique matplotlib."""
    card = QFrame()
    card.setObjectName("chartCard")
    card.setStyleSheet(f"""
        QFrame#chartCard {{
            background: {COLORS['bg_secondary']};
            border-radius: 20px;
            border: 1px solid {COLORS['border']};
        }}
        QFrame#chartCard QLabel {{
            background: transparent;
            border: none;
        }}
    """)
    lay = QVBoxLayout(card)
    lay.setContentsMargins(20, 18, 20, 14)
    lay.setSpacing(8)
    title_lbl = QLabel(title)
    title_lbl.setFont(QFont("Segoe UI", 13, QFont.Bold))
    title_lbl.setStyleSheet(f"color: {COLORS['text_primary']};")
    lay.addWidget(title_lbl)
    if subtitle:
        sub_lbl = QLabel(subtitle)
        sub_lbl.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 11px;")
        lay.addWidget(sub_lbl)
    return card


class ExportCard(QFrame):
    """Carte d'export avec icône, description et bouton d'action."""

    def __init__(
        self,
        title: str,
        description: str,
        icon_name: str,
        accent: str,
        button_text: str,
        parent=None,
    ):
        super().__init__(parent)
        self.setObjectName("exportCard")
        self.setStyleSheet(f"""
            QFrame#exportCard {{
                background: {COLORS['bg_secondary']};
                border-radius: 20px;
                border: 1px solid {COLORS['border']};
                border-top: 4px solid {accent};
            }}
            QFrame#exportCard QLabel {{ background: transparent; border: none; }}
        """)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(22, 20, 22, 20)
        lay.setSpacing(14)

        header = QHBoxLayout()
        icon_wrap = QLabel()
        icon_wrap.setFixedSize(44, 44)
        icon_wrap.setAlignment(Qt.AlignCenter)
        icon_wrap.setPixmap(get_pixmap(icon_name, 22, accent))
        icon_wrap.setStyleSheet(
            f"background: {hex_with_alpha(accent, 28)}; border-radius: 14px;"
        )
        header.addWidget(icon_wrap)

        text_col = QVBoxLayout()
        text_col.setSpacing(2)
        title_lbl = QLabel(title)
        title_lbl.setFont(QFont("Segoe UI", 15, QFont.Bold))
        title_lbl.setStyleSheet(f"color: {COLORS['text_primary']};")
        text_col.addWidget(title_lbl)
        header.addLayout(text_col, 1)
        lay.addLayout(header)

        desc_lbl = QLabel(description)
        desc_lbl.setWordWrap(True)
        desc_lbl.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px;")
        lay.addWidget(desc_lbl)

        self.action_btn = QPushButton(button_text)
        self.action_btn.setFixedHeight(44)
        self.action_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.action_btn.setFont(QFont("Segoe UI", 11, QFont.DemiBold))
        self.action_btn.setStyleSheet(f"""
            QPushButton {{
                background: {accent};
                color: white;
                border: none;
                border-radius: 14px;
                font-weight: 700;
            }}
            QPushButton:hover {{
                background: {hex_with_alpha(accent, 200)};
            }}
        """)
        lay.addWidget(self.action_btn)


class InfoBanner(QFrame):
    """Bandeau d'information stylisé."""

    def __init__(self, text: str, icon_name: str = "shield", parent=None):
        super().__init__(parent)
        c = COLORS
        self.setStyleSheet(f"""
            QFrame {{
                background: {hex_with_alpha(c['accent_warning'], 22)};
                border: 1px solid {hex_with_alpha(c['accent_warning'], 55)};
                border-radius: 16px;
            }}
            QFrame QLabel {{ background: transparent; border: none; }}
        """)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(16, 12, 16, 12)
        lay.setSpacing(10)
        icon = QLabel()
        icon.setPixmap(get_pixmap(icon_name, 18, c["accent_warning"]))
        lay.addWidget(icon)
        self.text_label = QLabel(text)
        self.text_label.setWordWrap(True)
        self.text_label.setStyleSheet(f"color: {c['text_secondary']}; font-size: 12px;")
        lay.addWidget(self.text_label, 1)


def build_table_section(title: str) -> tuple[QHBoxLayout, QLabel, QFrame, QVBoxLayout]:
    """En-tête + conteneur de tableau stylisé."""
    header = QHBoxLayout()
    title_lbl = QLabel(title)
    title_lbl.setFont(QFont("Segoe UI", 15, QFont.Bold))
    title_lbl.setStyleSheet(f"color: {COLORS['text_primary']}; background: transparent;")
    count_lbl = QLabel()
    count_lbl.setStyleSheet(
        f"color: {COLORS['text_muted']}; background: transparent; font-size: 12px;"
    )
    header.addWidget(title_lbl)
    header.addStretch()
    header.addWidget(count_lbl)

    container = QFrame()
    container.setObjectName("tableWrap")
    container.setStyleSheet(f"""
        QFrame#tableWrap {{
            background: {COLORS['bg_secondary']};
            border: 1px solid {COLORS['border']};
            border-radius: 20px;
        }}
    """)
    lay = QVBoxLayout(container)
    lay.setContentsMargins(0, 0, 0, 0)
    return header, count_lbl, container, lay


class FadeRefreshMixin:
    """Mixin pour animation fade lors du rafraîchissement de tableau."""

    table_container: QFrame

    def _setup_fade(self):
        self._opacity_effect = QGraphicsOpacityEffect(self.table_container)
        self.table_container.setGraphicsEffect(self._opacity_effect)
        self._opacity_effect.setOpacity(1.0)
        self._fade_anim = QPropertyAnimation(self._opacity_effect, b"opacity")
        self._fade_anim.setDuration(180)
        self._fade_anim.setEasingCurve(QEasingCurve.OutCubic)

    def _run_fade_refresh(self, callback):
        self._fade_anim.stop()
        self._fade_anim.setStartValue(1.0)
        self._fade_anim.setEndValue(0.55)
        self._fade_anim.finished.connect(lambda: self._finish_fade(callback))
        self._fade_anim.start()

    def _finish_fade(self, callback):
        try:
            self._fade_anim.finished.disconnect()
        except RuntimeError:
            pass
        callback()
        self._fade_anim.setStartValue(0.55)
        self._fade_anim.setEndValue(1.0)
        self._fade_anim.start()


# ─── Composants Premium Comptable ─────────────────────────────────────────────

from PySide6.QtCore import QTimer, QPropertyAnimation, QEasingCurve


class AnimatedStatCard(QFrame):
    """Carte KPI avec animation de comptage et effet hover premium."""

    def __init__(
        self,
        label: str,
        value: str,
        icon_name: str,
        color: str,
        is_currency: bool = False,
        parent=None,
    ):
        super().__init__(parent)
        self._color = color
        self._is_currency = is_currency
        self._target_int = 0
        self._current_int = 0
        self._suffix = ""
        self._hovered = False
        self.setObjectName("animStatCard")
        self.setMinimumHeight(100)
        self.setMinimumWidth(180)
        self._apply_style(False)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(20, 16, 16, 16)
        lay.setSpacing(14)

        # Text column
        text_col = QVBoxLayout()
        text_col.setSpacing(4)

        self._label_lbl = QLabel(label.upper())
        self._label_lbl.setStyleSheet(
            f"color: {COLORS['text_muted']}; font-size: 10px; font-weight: 700; "
            f"letter-spacing: 1.2px; background: transparent; border: none;"
        )

        self._value_lbl = QLabel(value)
        self._value_lbl.setFont(QFont("Segoe UI", 24, QFont.Bold))
        self._value_lbl.setStyleSheet(
            f"color: {color}; background: transparent; border: none;"
        )

        text_col.addWidget(self._label_lbl)
        text_col.addWidget(self._value_lbl)
        lay.addLayout(text_col, 1)

        # Icon
        self._icon_wrap = QLabel()
        self._icon_wrap.setFixedSize(48, 48)
        self._icon_wrap.setAlignment(Qt.AlignCenter)
        self._icon_wrap.setStyleSheet(
            f"background: {hex_with_alpha(color, 35)}; border-radius: 14px;"
        )
        px = get_pixmap(icon_name, 22, color)
        inner = QLabel(self._icon_wrap)
        inner.setPixmap(px)
        inner.setAlignment(Qt.AlignCenter)
        inner.setGeometry(13, 13, 22, 22)
        lay.addWidget(self._icon_wrap)

    def _apply_style(self, hovered: bool):
        c = COLORS
        color = self._color
        if hovered:
            bg = f"qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 {hex_with_alpha(color, 55)}, stop:1 {c['bg_secondary']})"
            border = color
        else:
            bg = f"qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 {hex_with_alpha(color, 32)}, stop:0.15 {c['bg_secondary']}, stop:1 {c['bg_secondary']})"
            border = hex_with_alpha(color, 60)
        self.setStyleSheet(f"""
            QFrame#animStatCard {{
                background: {bg};
                border: 1px solid {border};
                border-radius: 18px;
                background-color: {c['bg_secondary']};
            }}
            QFrame#animStatCard QLabel {{ background: transparent; border: none; }}
        """)

    def enterEvent(self, event):
        self._hovered = True
        self._apply_style(True)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hovered = False
        self._apply_style(False)
        super().leaveEvent(event)

    def set_value(self, value: str):
        self._value_lbl.setText(str(value))

    def animate_to(self, target: int, suffix: str = "", prefix: str = ""):
        """Anime la valeur de l'état actuel vers target."""
        self._target_int = target
        self._current_int = 0
        self._suffix = suffix
        self._prefix = prefix
        self._anim_step = max(1, target // 30)
        self._anim_timer = QTimer(self)
        self._anim_timer.timeout.connect(self._tick_anim)
        self._anim_timer.start(16)  # ~60fps

    def _tick_anim(self):
        self._current_int = min(self._current_int + self._anim_step, self._target_int)
        formatted = f"{self._current_int:,}".replace(",", " ")
        self._value_lbl.setText(f"{self._prefix}{formatted}{self._suffix}")
        if self._current_int >= self._target_int:
            self._anim_timer.stop()


class GlowButton(QPushButton):
    """Bouton premium avec glow coloré et animation hover."""

    def __init__(self, text: str, color: str, icon_name: str | None = None, parent=None):
        super().__init__(parent)
        self._color = color
        self.setFixedHeight(46)
        self.setCursor(QCursor(Qt.PointingHandCursor))

        lay = QHBoxLayout(self)
        lay.setContentsMargins(20, 0, 24, 0)
        lay.setSpacing(10)

        if icon_name:
            icon_lbl = QLabel()
            icon_lbl.setFixedSize(20, 20)
            icon_lbl.setPixmap(get_pixmap(icon_name, 20, "#FFFFFF"))
            icon_lbl.setAttribute(Qt.WA_TransparentForMouseEvents)
            lay.addWidget(icon_lbl)

        text_lbl = QLabel(text)
        text_lbl.setFont(QFont("Segoe UI", 12, QFont.DemiBold))
        text_lbl.setStyleSheet("color: white; background: transparent; border: none;")
        text_lbl.setAttribute(Qt.WA_TransparentForMouseEvents)
        lay.addWidget(text_lbl)

        self._apply_style(False)

    def _apply_style(self, hovered: bool):
        c = self._color
        if hovered:
            bg = f"qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 {c}, stop:1 {hex_with_alpha(c, 200)})"
        else:
            bg = f"qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 {hex_with_alpha(c, 220)}, stop:1 {c})"
        self.setStyleSheet(f"""
            GlowButton {{
                background: {bg};
                border: 1px solid {hex_with_alpha(c, 180)};
                border-radius: 14px;
                min-width: 120px;
            }}
            GlowButton:pressed {{ background: {hex_with_alpha(c, 180)}; }}
        """)

    def enterEvent(self, event):
        self._apply_style(True)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._apply_style(False)
        super().leaveEvent(event)


class FilterChip(QPushButton):
    """Bouton-pill toggle pour filtres exclusifs."""

    def __init__(self, text: str, icon_name: str | None = None, parent=None):
        super().__init__(parent)
        self._icon_name = icon_name
        self.setCheckable(True)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setFixedHeight(36)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(14, 0, 18, 0)
        lay.setSpacing(7)

        if icon_name:
            self._icon_lbl = QLabel()
            self._icon_lbl.setFixedSize(16, 16)
            self._icon_lbl.setAttribute(Qt.WA_TransparentForMouseEvents)
            lay.addWidget(self._icon_lbl)
        else:
            self._icon_lbl = None

        self._text_lbl = QLabel(text)
        self._text_lbl.setFont(QFont("Segoe UI", 11, QFont.DemiBold))
        self._text_lbl.setAttribute(Qt.WA_TransparentForMouseEvents)
        lay.addWidget(self._text_lbl)

        self._apply_chip_style()
        self.toggled.connect(self._apply_chip_style)

    def _apply_chip_style(self):
        c = COLORS
        ap = c["accent_primary"]
        if self.isChecked():
            self.setStyleSheet(f"""
                FilterChip {{
                    background: {ap};
                    border: 1px solid {ap};
                    border-radius: 18px;
                }}
            """)
            self._text_lbl.setStyleSheet("color: white; background: transparent; border: none;")
            if self._icon_lbl:
                self._icon_lbl.setPixmap(get_pixmap(self._icon_name, 16, "#FFFFFF"))
        else:
            self.setStyleSheet(f"""
                FilterChip {{
                    background: {c['bg_secondary']};
                    border: 1px solid {c['border']};
                    border-radius: 18px;
                }}
                FilterChip:hover {{
                    background: {c['bg_hover']};
                    border-color: {hex_with_alpha(ap, 120)};
                }}
            """)
            self._text_lbl.setStyleSheet(f"color: {c['text_secondary']}; background: transparent; border: none;")
            if self._icon_lbl:
                self._icon_lbl.setPixmap(get_pixmap(self._icon_name, 16, c["text_muted"]))


class SalaryProgressBar(QWidget):
    """Barre de progression gradient pour afficher un salaire dans un tableau."""

    def __init__(self, value: float, max_val: float, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: transparent;")
        lay = QHBoxLayout(self)
        lay.setContentsMargins(12, 6, 12, 6)
        lay.setSpacing(12)

        from PySide6.QtWidgets import QProgressBar
        bar = QProgressBar()
        bar.setTextVisible(False)
        bar.setFixedHeight(7)
        bar.setMaximum(max(1, int(max_val)))
        bar.setValue(int(value))
        c = COLORS
        bar.setStyleSheet(f"""
            QProgressBar {{
                background: {hex_with_alpha(c['text_muted'], 40)};
                border: none;
                border-radius: 4px;
            }}
            QProgressBar::chunk {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {c['accent_secondary']}, stop:1 {c['accent_primary']});
                border-radius: 4px;
            }}
        """)

        amount_lbl = QLabel(f"{value:,.0f} MAD".replace(",", " "))
        amount_lbl.setFont(QFont("Segoe UI", 12, QFont.DemiBold))
        amount_lbl.setStyleSheet(
            f"color: {COLORS['text_primary']}; background: transparent; border: none;"
        )
        amount_lbl.setMinimumWidth(130)
        amount_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        lay.addWidget(bar, 1)
        lay.addWidget(amount_lbl)


class BulletinPreviewCard(QFrame):
    """Carte de prévisualisation stylisée d'un bulletin de paie."""

    def __init__(self, parent=None):
        super().__init__(parent)
        c = COLORS
        self.setObjectName("bulletinPreview")
        self.setStyleSheet(f"""
            QFrame#bulletinPreview {{
                background: {c['bg_secondary']};
                border: 1px solid {c['border']};
                border-radius: 22px;
            }}
            QFrame#bulletinPreview QLabel {{ background: transparent; border: none; }}
        """)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(40)
        shadow.setOffset(0, 10)
        sc = QColor(c['accent_primary'])
        sc.setAlpha(35)
        shadow.setColor(sc)
        self.setGraphicsEffect(shadow)

        self._main_lay = QVBoxLayout(self)
        self._main_lay.setContentsMargins(28, 24, 28, 24)
        self._main_lay.setSpacing(0)

        # Header gradient band
        header_frame = QFrame()
        header_frame.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {c['accent_primary']}, stop:1 {c['accent_secondary']});
                border-radius: 18px;
            }}
        """)
        
        header_lay = QHBoxLayout(header_frame)
        header_lay.setContentsMargins(24, 20, 24, 20)
        header_lay.setSpacing(16)

        # Left Info Column
        left_col = QVBoxLayout()
        left_col.setSpacing(6)

        # Uppercase badge at the top
        badge_lbl = QLabel("BULLETIN DE PAIE MENSUELE")
        badge_lbl.setFont(QFont("Segoe UI", 9, QFont.Bold))
        badge_lbl.setStyleSheet("""
            color: rgba(255, 255, 255, 0.95);
            letter-spacing: 1.5px;
            background: rgba(255, 255, 255, 0.16);
            border: 1px solid rgba(255, 255, 255, 0.22);
            border-radius: 8px;
            padding: 3px 10px;
        """)
        
        badge_wrap = QHBoxLayout()
        badge_wrap.addWidget(badge_lbl)
        badge_wrap.addStretch()
        left_col.addLayout(badge_wrap)

        self._emp_name_lbl = QLabel("—")
        self._emp_name_lbl.setFont(QFont("Segoe UI", 22, QFont.Bold))
        self._emp_name_lbl.setStyleSheet("color: white; background: transparent; padding-top: 2px;")
        left_col.addWidget(self._emp_name_lbl)

        self._periode_lbl = QLabel("—")
        self._periode_lbl.setFont(QFont("Segoe UI", 11))
        self._periode_lbl.setStyleSheet("color: rgba(255, 255, 255, 0.85); background: transparent;")
        left_col.addWidget(self._periode_lbl)

        header_lay.addLayout(left_col, 1)

        # Right Icon Column
        from app.utils.icons import get_pixmap
        icon_container = QLabel()
        icon_container.setFixedSize(56, 56)
        icon_container.setAlignment(Qt.AlignCenter)
        icon_container.setStyleSheet("""
            background: rgba(255, 255, 255, 0.14);
            border: 1px solid rgba(255, 255, 255, 0.22);
            border-radius: 28px;
        """)
        
        px = get_pixmap("payslips", 24, "#FFFFFF")
        icon_container.setPixmap(px)
        header_lay.addWidget(icon_container, 0, Qt.AlignVCenter | Qt.AlignRight)

        self._main_lay.addWidget(header_frame)
        self._main_lay.addSpacing(20)

        # Lines
        self._rows_lay = QVBoxLayout()
        self._rows_lay.setSpacing(0)
        self._main_lay.addLayout(self._rows_lay)

        # Will be populated by update()
        self._row_widgets: list[tuple[QLabel, QLabel]] = []
        rows_def = [
            ("Salaire de base", "—", False, False),
            ("+ Primes", "—", False, False),
            ("+ Heures supplémentaires", "—", False, False),
            ("sep1", "", True, False),
            ("Salaire Brut", "—", False, False),
            ("− Déductions", "—", False, False),
            ("sep2", "", True, False),
            ("NET À PAYER", "—", False, True),
        ]
        for key, val, is_sep, is_total in rows_def:
            if is_sep:
                sep = QFrame()
                sep.setFrameShape(QFrame.HLine)
                sep.setStyleSheet(f"background: {hex_with_alpha(c['border'], 150)}; border: none; margin: 10px 0;")
                sep.setFixedHeight(1)
                self._rows_lay.addWidget(sep)
            else:
                row = QHBoxLayout()
                row.setContentsMargins(4, 7, 4, 7)
                lbl = QLabel(key)
                lbl.setFont(QFont("Segoe UI", 12 if not is_total else 14,
                                  QFont.Normal if not is_total else QFont.Bold))
                lbl.setStyleSheet(
                    f"color: {c['text_secondary'] if not is_total else c['text_primary']}; "
                    "background: transparent;"
                )
                val_lbl = QLabel(val)
                val_lbl.setFont(QFont("Segoe UI", 12 if not is_total else 15,
                                      QFont.DemiBold if not is_total else QFont.Bold))
                col = c['accent_primary'] if is_total else c['text_primary']
                val_lbl.setStyleSheet(f"color: {col}; background: transparent;")
                val_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
                row.addWidget(lbl, 1)
                row.addWidget(val_lbl)
                self._rows_lay.addLayout(row)
                self._row_widgets.append((lbl, val_lbl))

        self._main_lay.addSpacing(18)

        # Actions
        self._actions_lay = QHBoxLayout()
        self._actions_lay.setSpacing(12)
        self._main_lay.addLayout(self._actions_lay)

    def update_bulletin(self, b):
        """Met à jour la carte avec les données d'un BulletinPaie."""
        c = COLORS
        self._emp_name_lbl.setText(b.nom_complet)
        self._periode_lbl.setText(f"Période : {b.periode}  •  {b.poste or 'Employé'}")

        fmt = lambda v: f"{v:,.2f} MAD".replace(",", " ")
        vals = [
            fmt(b.salaire_base),
            fmt(b.total_primes),
            fmt(b.total_heures_sup),
            fmt(b.salaire_brut),
            fmt(b.total_deductions),
            fmt(b.salaire_net),
        ]
        # Map to row_widgets (skipping separators, order matches rows_def)
        for idx, v in enumerate(vals):
            self._row_widgets[idx][1].setText(v)

    def set_actions(self, widgets: list[QWidget]):
        """Remplace les actions dans la barre du bas."""
        while self._actions_lay.count():
            item = self._actions_lay.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        for w in widgets:
            self._actions_lay.addWidget(w)
        self._actions_lay.addStretch()

