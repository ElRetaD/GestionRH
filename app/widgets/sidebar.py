"""
Sidebar premium de l'application.
Navigation moderne avec icônes vectorielles, indicateur animé et profil utilisateur.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel, QHBoxLayout,
    QFrame, QGraphicsDropShadowEffect,
)
from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve, Property
from PySide6.QtGui import QFont, QCursor, QColor

from app.utils.theme import COLORS, hex_with_alpha, THEME_MODE
from app.utils.icons import get_pixmap


class _ActiveIndicator(QFrame):
    """Barre latérale animée derrière le bouton actif."""

    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.setFixedWidth(4)
        self.setStyleSheet(f"""
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {COLORS['accent_primary']}, stop:1 {COLORS['accent_secondary']});
            border-radius: 2px;
        """)
        self._y = 0.0
        self.hide()

    def get_y(self):
        return self._y

    def set_y(self, value):
        self._y = value
        self.move(6, int(value))
        self.show()

    y_pos = Property(float, get_y, set_y)


class SidebarButton(QPushButton):
    """Bouton de navigation avec icône MDI et états hover/actif."""

    def __init__(self, page_id: str, text: str, parent=None):
        super().__init__(parent)
        self._page_id = page_id
        self._text = text
        self._active = False
        self.setFixedHeight(48)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setCheckable(True)
        self._build()

    def _build(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 12, 0)
        layout.setSpacing(12)

        self.icon_lbl = QLabel()
        self.icon_lbl.setFixedSize(34, 34)
        self.icon_lbl.setAlignment(Qt.AlignCenter)
        self.icon_lbl.setAttribute(Qt.WA_TransparentForMouseEvents)

        self.text_lbl = QLabel(self._text)
        self.text_lbl.setFont(QFont("Segoe UI", 12, QFont.DemiBold))
        self.text_lbl.setAttribute(Qt.WA_TransparentForMouseEvents)

        self.chevron = QLabel()
        self.chevron.setFixedSize(16, 16)
        self.chevron.setAttribute(Qt.WA_TransparentForMouseEvents)

        layout.addWidget(self.icon_lbl)
        layout.addWidget(self.text_lbl, 1)
        layout.addWidget(self.chevron)

        self._update_style(False)

    def _update_style(self, active: bool):
        c = COLORS
        icon_color = "#FFFFFF" if active else c["text_secondary"]
        text_color = c["text_primary"] if active else c["text_secondary"]

        self.icon_lbl.setPixmap(get_pixmap(self._page_id, 18, icon_color))
        icon_bg = (
            f"qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 {c['accent_primary']},"
            f"stop:1 {c['accent_secondary']})"
            if active else hex_with_alpha(c["bg_hover"], 160)
        )
        self.icon_lbl.setStyleSheet(
            f"background: {icon_bg}; border-radius: 11px; border: none;"
        )

        self.text_lbl.setStyleSheet(
            f"color: {text_color}; background: transparent; border: none;"
            f"{' font-weight: 700;' if active else ''}"
        )

        chevron_color = c["accent_secondary"] if active else "transparent"
        self.chevron.setPixmap(get_pixmap("chevron", 14, chevron_color))

        if active:
            self.setStyleSheet(f"""
                SidebarButton {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 {hex_with_alpha(c['accent_primary'], 50)},
                        stop:1 {hex_with_alpha(c['accent_secondary'], 12)});
                    border: 1px solid {hex_with_alpha(c['accent_primary'], 45)};
                    border-radius: 14px;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                SidebarButton {{
                    background: transparent;
                    border: 1px solid transparent;
                    border-radius: 14px;
                }}
                SidebarButton:hover {{
                    background: {hex_with_alpha(c['accent_primary'], 16)};
                    border-color: {hex_with_alpha(c['accent_primary'], 35)};
                }}
            """)

    def set_active(self, active: bool):
        self._active = active
        self.setChecked(active)
        self._update_style(active)


class Sidebar(QWidget):
    """Barre latérale premium — icônes vectorielles et navigation fluide."""

    page_changed = Signal(str)
    logout_clicked = Signal()
    theme_toggle_clicked = Signal()

    ADMIN_MENU = [
        ("Tableau de Bord",   "dashboard"),
        ("Employés",          "employees"),
        ("Présences",         "attendance"),
        ("Absences",          "absences"),
        ("Statistiques",      "stats"),
        ("Historique",        "history"),
        ("Rapports",          "reports"),
        ("Utilisateurs",      "users"),
    ]

    AGENT_MENU = [
        ("Tableau de Bord",    "agent_dashboard"),
        ("Enregistrer",        "record"),
        ("Collaborateurs",     "search"),
        ("Présences du Jour",  "today"),
    ]

    COMPTABLE_MENU = [
        ("Tableau de Bord",    "payroll_dashboard"),
        ("Salaires",           "payroll_salaries"),
        ("Paie Mensuelle",     "payroll_monthly"),
        ("Bulletins de Paie",  "payroll_payslips"),
    ]

    def __init__(self, role: str = "admin", user_name: str = "", parent=None):
        super().__init__(parent)
        self._role = role
        self._buttons: dict[str, SidebarButton] = {}
        self._active_page = ""
        self.setFixedWidth(272)
        self.setStyleSheet(f"""
            Sidebar {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {COLORS['sidebar_bg']}, stop:1 {hex_with_alpha(COLORS['bg_primary'], 200)});
                border-right: 1px solid {COLORS['border']};
            }}
        """)
        self._build_ui(user_name)

    def _build_ui(self, user_name: str):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 18, 14, 16)
        layout.setSpacing(12)

        # ── Brand ─────────────────────────────────────────────────────────
        brand = QFrame()
        brand.setObjectName("sidebarBrand")
        brand.setStyleSheet(f"""
            QFrame#sidebarBrand {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {hex_with_alpha(COLORS['accent_primary'], 38)},
                    stop:1 {hex_with_alpha(COLORS['accent_secondary'], 16)});
                border: 1px solid {hex_with_alpha(COLORS['accent_primary'], 55)};
                border-radius: 20px;
            }}
            QFrame#sidebarBrand QLabel {{ border: none; background: transparent; }}
        """)
        shadow = QGraphicsDropShadowEffect(brand)
        shadow.setBlurRadius(28)
        shadow.setOffset(0, 6)
        sc = QColor(COLORS["accent_primary"])
        sc.setAlpha(55)
        shadow.setColor(sc)
        brand.setGraphicsEffect(shadow)

        bl = QHBoxLayout(brand)
        bl.setContentsMargins(14, 14, 14, 14)
        bl.setSpacing(12)

        logo = QLabel()
        logo.setFixedSize(44, 44)
        logo.setAlignment(Qt.AlignCenter)
        logo.setPixmap(get_pixmap("attendance", 24, "#FFFFFF"))
        logo.setStyleSheet(f"""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 {COLORS['accent_primary']}, stop:1 {COLORS['accent_secondary']});
            border-radius: 14px;
        """)

        brand_text = QVBoxLayout()
        brand_text.setSpacing(1)
        app_name = QLabel("GestRH")
        app_name.setFont(QFont("Segoe UI", 14, QFont.Bold))
        app_name.setStyleSheet(f"color: {COLORS['text_primary']};")
        app_sub = QLabel("Gestion RH")
        app_sub.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 11px;")
        brand_text.addWidget(app_name)
        brand_text.addWidget(app_sub)

        bl.addWidget(logo)
        bl.addLayout(brand_text, 1)
        layout.addWidget(brand)

        # ── Navigation ────────────────────────────────────────────────────
        section = QLabel("MENU PRINCIPAL")
        section.setStyleSheet(
            f"color: {COLORS['text_muted']}; font-size: 10px; font-weight: 700; "
            f"letter-spacing: 2px; padding-left: 6px; border: none; background: transparent;"
        )
        layout.addWidget(section)

        nav_container = QFrame()
        nav_container.setObjectName("navContainer")
        nav_container.setStyleSheet(f"""
            QFrame#navContainer {{
                background: {hex_with_alpha(COLORS['bg_secondary'], 180)};
                border: 1px solid {COLORS['border']};
                border-radius: 18px;
            }}
        """)
        nav_outer = QVBoxLayout(nav_container)
        nav_outer.setContentsMargins(6, 6, 6, 6)
        nav_outer.setSpacing(0)
        nav_outer.setAlignment(Qt.AlignTop)

        self._indicator = _ActiveIndicator(nav_container)
        self._indicator.setFixedHeight(48)

        nav_layout = QVBoxLayout()
        nav_layout.setContentsMargins(0, 0, 0, 0)
        nav_layout.setSpacing(3)

        menu = self._get_menu()
        for text, page_id in menu:
            btn = SidebarButton(page_id, text)
            btn.clicked.connect(lambda checked, pid=page_id: self._on_click(pid))
            self._buttons[page_id] = btn
            nav_layout.addWidget(btn)

        nav_outer.addLayout(nav_layout)
        layout.addWidget(nav_container)

        layout.addStretch(1)

        self._indicator_anim = QPropertyAnimation(self._indicator, b"y_pos")
        self._indicator_anim.setDuration(220)
        self._indicator_anim.setEasingCurve(QEasingCurve.OutCubic)

        # ── Profile ───────────────────────────────────────────────────────
        profile = QFrame()
        profile.setObjectName("sidebarProfile")
        profile.setStyleSheet(f"""
            QFrame#sidebarProfile {{
                background: {COLORS['bg_tertiary']};
                border-radius: 16px;
                border: 1px solid {COLORS['border']};
            }}
            QFrame#sidebarProfile QLabel {{ border: none; background: transparent; }}
        """)
        pl = QHBoxLayout(profile)
        pl.setContentsMargins(12, 10, 12, 10)
        pl.setSpacing(10)

        initial = (user_name[:1] if user_name else "U").upper()
        avatar = QLabel(initial)
        avatar.setFont(QFont("Segoe UI", 13, QFont.Bold))
        avatar.setFixedSize(38, 38)
        avatar.setAlignment(Qt.AlignCenter)
        avatar.setStyleSheet(f"""
            color: white;
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 {COLORS['accent_primary']}, stop:1 {COLORS['accent_secondary']});
            border-radius: 19px;
        """)

        info = QVBoxLayout()
        info.setSpacing(0)
        name_lbl = QLabel(user_name[:20] if user_name else "Utilisateur")
        name_lbl.setStyleSheet(
            f"color: {COLORS['text_primary']}; font-weight: 700; font-size: 12px;"
        )
        role_labels = {
            "admin": "Administrateur",
            "agent": "Assistant RH",
            "comptable": "Comptable",
        }
        role_lbl = QLabel(role_labels.get(self._role, self._role))
        role_lbl.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 10px;")
        info.addWidget(name_lbl)
        info.addWidget(role_lbl)

        pl.addWidget(avatar)
        pl.addLayout(info, 1)
        layout.addWidget(profile)

        # ── Footer actions ────────────────────────────────────────────────
        footer = QHBoxLayout()
        footer.setSpacing(8)

        theme_icon = "theme_light" if THEME_MODE == "dark" else "theme_dark"
        theme_label = "Clair" if THEME_MODE == "dark" else "Sombre"
        theme_btn = self._footer_btn(theme_icon, theme_label, "btn-secondary")
        theme_btn.clicked.connect(self.theme_toggle_clicked)

        logout_btn = self._footer_btn("logout", "Quitter", "btn-danger")
        logout_btn.clicked.connect(self.logout_clicked)

        footer.addWidget(theme_btn, 1)
        footer.addWidget(logout_btn, 1)
        layout.addLayout(footer)

    def _footer_btn(self, icon_name: str, text: str, css_class: str) -> QPushButton:
        btn = QPushButton()
        btn.setFixedHeight(40)
        btn.setCursor(QCursor(Qt.PointingHandCursor))
        btn.setProperty("class", css_class)

        lay = QHBoxLayout(btn)
        lay.setContentsMargins(10, 0, 10, 0)
        lay.setSpacing(6)
        icon = QLabel()
        icon_color = COLORS["text_primary"] if css_class == "btn-secondary" else "#FFFFFF"
        icon.setPixmap(get_pixmap(icon_name, 16, icon_color))
        icon.setAttribute(Qt.WA_TransparentForMouseEvents)
        lbl = QLabel(text)
        lbl.setFont(QFont("Segoe UI", 10, QFont.DemiBold))
        lbl.setAttribute(Qt.WA_TransparentForMouseEvents)
        lbl.setStyleSheet(
            f"color: {'#FFFFFF' if css_class == 'btn-danger' else COLORS['text_primary']}; "
            f"background: transparent; border: none;"
        )
        lay.addWidget(icon)
        lay.addWidget(lbl)
        lay.addStretch()
        btn.setStyleSheet("border-radius: 12px; text-align: left;")
        return btn

    def _animate_indicator(self, btn: SidebarButton):
        target_y = btn.y() + 6
        self._indicator.setFixedHeight(btn.height() - 12)
        self._indicator_anim.stop()
        self._indicator_anim.setStartValue(self._indicator.y_pos if self._indicator.isVisible() else target_y)
        self._indicator_anim.setEndValue(target_y)
        self._indicator_anim.start()

    def _on_click(self, page_id: str):
        self.navigate_to(page_id)
        self.page_changed.emit(page_id)

    def navigate_to(self, page_id: str):
        for pid, btn in self._buttons.items():
            btn.set_active(pid == page_id)
        if page_id in self._buttons:
            self._animate_indicator(self._buttons[page_id])
        self._active_page = page_id

    def _get_menu(self) -> list[tuple[str, str]]:
        if self._role == "admin":
            return self.ADMIN_MENU
        if self._role == "comptable":
            return self.COMPTABLE_MENU
        return self.AGENT_MENU

    def get_first_page(self) -> str:
        menu = self._get_menu()
        return menu[0][1] if menu else ""

    def showEvent(self, event):
        super().showEvent(event)
        if self._active_page and self._active_page in self._buttons:
            self._animate_indicator(self._buttons[self._active_page])
