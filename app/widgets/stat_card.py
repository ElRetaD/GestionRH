"""
Cartes de statistiques pour le tableau de bord.
Affiche un chiffre clé avec icône, titre et indicateur coloré.
"""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGraphicsDropShadowEffect
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor
from app.utils.theme import COLORS, hex_with_alpha


class StatCard(QWidget):
    """Carte de statistique animée pour le tableau de bord admin."""

    def __init__(self, title: str, value: str, icon: str,
                 color: str = None, subtitle: str = "", parent=None):
        super().__init__(parent)
        self._color  = color or COLORS['accent_primary']
        self._title  = title
        self._icon   = icon
        self.setFixedHeight(152)
        self.setMinimumWidth(215)
        self._build_ui(title, value, icon, self._color, subtitle)
        self._apply_shadow(False)
        self._animate()

    def _apply_shadow(self, hovered: bool):
        shadow = self.graphicsEffect()
        if not isinstance(shadow, QGraphicsDropShadowEffect):
            shadow = QGraphicsDropShadowEffect(self)
            self.setGraphicsEffect(shadow)

        shadow.setBlurRadius(38 if hovered else 28)
        shadow.setOffset(0, 14 if hovered else 10)
        c = QColor(self._color)
        c.setAlpha(110 if hovered else 70)
        shadow.setColor(c)

    def enterEvent(self, event):
        self._apply_shadow(True)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._apply_shadow(False)
        super().leaveEvent(event)

    def _build_ui(self, title, value, icon, color, subtitle):
        self.setStyleSheet(f"""
            StatCard {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {COLORS['bg_secondary']}, stop:1 {COLORS['bg_tertiary']});
                border-radius: 22px;
                border: 1px solid {COLORS['border']};
                border-top: 3px solid {color};
            }}
            StatCard:hover {{
                border: 1px solid {hex_with_alpha(color, 102)};
                border-top: 3px solid {color};
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(16)

        icon_lbl = QLabel(icon)
        icon_lbl.setFont(QFont("Segoe UI", 12, QFont.Bold))
        icon_lbl.setAlignment(Qt.AlignCenter)
        icon_lbl.setFixedSize(42, 42)
        icon_lbl.setStyleSheet(f"""
            background-color: {hex_with_alpha(color, 32)};
            border-radius: 14px;
            color: {color};
        """)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)

        label_badge = QLabel(title.upper())
        label_badge.setStyleSheet(f"""
            color: {COLORS['text_secondary']};
            font-size: 10px;
            font-weight: 700;
            letter-spacing: 1px;
            background: transparent;
        """)

        self.value_lbl = QLabel(str(value))
        font = QFont("Segoe UI", 32, QFont.Bold)
        self.value_lbl.setFont(font)
        self.value_lbl.setStyleSheet(f"color: {color}; background: transparent;")
        title_lbl = QLabel(subtitle or "Indicateur du jour")
        title_lbl.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px; background: transparent;")

        text_layout.addWidget(label_badge)
        text_layout.addWidget(self.value_lbl)
        text_layout.addWidget(title_lbl)
        text_layout.addStretch()
        layout.addLayout(text_layout, 1)
        layout.addWidget(icon_lbl, 0, Qt.AlignTop | Qt.AlignRight)

    def update_value(self, value: str):
        """Met à jour la valeur affichée."""
        self.value_lbl.setText(str(value))

    def _animate(self):
        """Légère animation d'apparition."""
        pass
