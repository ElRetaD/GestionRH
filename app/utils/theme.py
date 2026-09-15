"""
Thème visuel de l'application — Support dynamique Mode Clair / Mode Sombre.
Palette de couleurs, polices et feuille de style QSS complète.
"""
import os
import json
from app.config import DATA_DIR


def hex_with_alpha(hex_color: str, alpha: int) -> str:
    """Convertit #RRGGBB en rgba(r,g,b,a) avec alpha 0-255."""
    r = int(hex_color[1:3], 16)
    g = int(hex_color[3:5], 16)
    b = int(hex_color[5:7], 16)
    return f"rgba({r}, {g}, {b}, {alpha})"


SETTINGS_PATH = os.path.join(DATA_DIR, "settings.json")

# ─── Palettes de couleurs ──────────────────────────────────────────────────────

DARK_COLORS = {
    # Fonds
    "bg_primary":         "#081120",
    "bg_secondary":       "#0F1B31",
    "bg_tertiary":        "#16243F",
    "bg_hover":           "#223252",
    "bg_card":            "#111D35",
    "sidebar_bg":         "#09101D",

    # Accents - premium violet/cyan
    "accent_primary":     "#8B5CF6",
    "accent_secondary":   "#38BDF8",
    "accent_success":     "#60A5FA",
    "accent_danger":      "#FB7185",
    "accent_warning":     "#F59E0B",
    "accent_info":        "#22D3EE",
    "accent_online":      "#22C55E",

    # Alias pour compatibilité
    "accent_blue":        "#8B5CF6",
    "accent_green":       "#60A5FA",
    "accent_red":         "#FB7185",
    "accent_orange":      "#FBBF24",
    "accent_purple":      "#8B5CF6",
    "accent_teal":        "#22D3EE",

    # Textes
    "text_primary":       "#F8FAFC",
    "text_secondary":     "#B6C2D9",
    "text_muted":         "#6E7C97",

    # Bordures
    "border":             "#24324E",
    "border_light":       "#18243D",

    # Inputs
    "input_bg":           "#13203A",
    "input_border":       "#2B3D61",
    "input_focus":        "#8B5CF6",
    "input_focus_bg":     "#192846",

    # Tableaux
    "table_alternate":    "#0C1730",
    "table_selection":    "#20355C",

    # Boutons hover/pressed
    "btn_primary_hover":  "#9F78FF",
    "btn_primary_pressed": "#7443F0",
    "btn_success_hover":  "#3B82F6",
    "btn_danger_hover":   "#E11D48",
    "btn_warning_hover":  "#D97706",
    "btn_purple_hover":   "#7443F0",
}

LIGHT_COLORS = {
    # Fonds
    "bg_primary":         "#F4F7FB",
    "bg_secondary":        "#FFFFFF",
    "bg_tertiary":         "#EEF3FA",
    "bg_hover":            "#E0E8F5",
    "bg_card":             "#FFFFFF",
    "sidebar_bg":          "#0F172A",

    # Accents
    "accent_primary":      "#7C3AED",
    "accent_secondary":    "#0EA5E9",
    "accent_success":      "#2563EB",
    "accent_danger":       "#E11D48",
    "accent_warning":      "#D97706",
    "accent_info":         "#0284C7",
    "accent_online":       "#16A34A",

    # Alias pour compatibilité
    "accent_blue":         "#7C3AED",
    "accent_green":        "#2563EB",
    "accent_red":          "#E11D48",
    "accent_orange":       "#D97706",
    "accent_purple":       "#7C3AED",
    "accent_teal":         "#0891B2",

    # Textes
    "text_primary":        "#09090B",
    "text_secondary":      "#475569",
    "text_muted":          "#94A3B8",

    # Bordures
    "border":              "#D7E1F0",
    "border_light":        "#E7EEF8",

    # Inputs
    "input_bg":            "#FFFFFF",
    "input_border":         "#C6D4EA",
    "input_focus":         "#7C3AED",
    "input_focus_bg":      "#F8FBFF",

    # Tableaux
    "table_alternate":     "#F7FAFF",
    "table_selection":     "#E7EEFF",

    # Boutons hover/pressed
    "btn_primary_hover":    "#6D28D9",
    "btn_primary_pressed": "#5B21B6",
    "btn_success_hover":    "#1D4ED8",
    "btn_danger_hover":     "#BE123C",
    "btn_warning_hover":    "#B45309",
    "btn_purple_hover":    "#6D28D9",
}

# ─── Persistance et Chargement du Thème ────────────────────────────────────────

def load_theme_mode() -> str:
    """Charge le mode de thème sauvegardé."""
    try:
        if os.path.exists(SETTINGS_PATH):
            with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
                settings = json.load(f)
                return settings.get("theme", "dark")
    except Exception as e:
        print(f"Error loading theme setting: {e}")
    return "dark"

def save_theme_mode(mode: str):
    """Sauvegarde le mode de thème."""
    try:
        settings = {}
        if os.path.exists(SETTINGS_PATH):
            with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
                settings = json.load(f)
        settings["theme"] = mode
        os.makedirs(os.path.dirname(SETTINGS_PATH), exist_ok=True)
        with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=4)
    except Exception as e:
        print(f"Error saving theme setting: {e}")

# Initialisation à l'import
THEME_MODE = load_theme_mode()
COLORS = LIGHT_COLORS.copy() if THEME_MODE == "light" else DARK_COLORS.copy()

def update_app_palette():
    """Applique la palette du thème actif à l'application."""
    from PySide6.QtWidgets import QApplication
    from PySide6.QtGui import QPalette, QColor
    
    app = QApplication.instance()
    if not app:
        return
        
    c = COLORS
    palette = QPalette()
    
    # Rôles principaux de couleur
    bg_primary = QColor(c["bg_primary"])
    bg_secondary = QColor(c["bg_secondary"])
    bg_tertiary = QColor(c["bg_tertiary"])
    text_primary = QColor(c["text_primary"])
    text_secondary = QColor(c["text_secondary"])
    accent_primary = QColor(c["accent_primary"])
    
    # Configurer la palette
    palette.setColor(QPalette.Window, bg_primary)
    palette.setColor(QPalette.WindowText, text_primary)
    palette.setColor(QPalette.Base, bg_secondary)
    palette.setColor(QPalette.AlternateBase, bg_tertiary)
    palette.setColor(QPalette.ToolTipBase, bg_secondary)
    palette.setColor(QPalette.ToolTipText, text_primary)
    palette.setColor(QPalette.Text, text_primary)
    palette.setColor(QPalette.Button, bg_tertiary)
    palette.setColor(QPalette.ButtonText, text_primary)
    palette.setColor(QPalette.BrightText, QColor("#FFFFFF"))
    palette.setColor(QPalette.Link, accent_primary)
    
    palette.setColor(QPalette.Highlight, accent_primary)
    palette.setColor(QPalette.HighlightedText, QColor("#FFFFFF"))
    
    # Couleurs désactivées
    disabled_text = QColor(c["text_muted"])
    palette.setColor(QPalette.Disabled, QPalette.WindowText, disabled_text)
    palette.setColor(QPalette.Disabled, QPalette.Text, disabled_text)
    palette.setColor(QPalette.Disabled, QPalette.ButtonText, disabled_text)
    
    app.setPalette(palette)


def set_theme_mode(mode: str):
    """Met à jour le thème actif globalement."""
    global THEME_MODE
    THEME_MODE = mode
    COLORS.clear()
    if mode == "light":
        COLORS.update(LIGHT_COLORS)
    else:
        COLORS.update(DARK_COLORS)
    _refresh_chart_colors()
    save_theme_mode(mode)
    update_app_palette()

CHART_COLORS: list[str] = []


def _refresh_chart_colors():
    CHART_COLORS.clear()
    CHART_COLORS.extend([
        COLORS["accent_info"],
        COLORS["accent_danger"],
        COLORS["accent_warning"],
        COLORS["accent_primary"],
        COLORS["accent_secondary"],
        COLORS["accent_success"],
        COLORS["accent_purple"],
    ])


_refresh_chart_colors()


def apply_date_edit_calendar_theme(date_edit):
    """Apply the active theme to a QDateEdit popup calendar."""
    from PySide6.QtCore import Qt, QDate
    from PySide6.QtGui import QColor, QPalette, QTextCharFormat
    from PySide6.QtWidgets import QCalendarWidget

    c = COLORS
    calendar = date_edit.calendarWidget()
    calendar.setGridVisible(False)
    calendar.setVerticalHeaderFormat(QCalendarWidget.NoVerticalHeader)

    palette = calendar.palette()
    palette.setColor(QPalette.Window, QColor(c["bg_secondary"]))
    palette.setColor(QPalette.Base, QColor(c["bg_secondary"]))
    palette.setColor(QPalette.AlternateBase, QColor(c["bg_tertiary"]))
    palette.setColor(QPalette.Text, QColor(c["text_primary"]))
    palette.setColor(QPalette.WindowText, QColor(c["text_primary"]))
    palette.setColor(QPalette.Button, QColor(c["bg_tertiary"]))
    palette.setColor(QPalette.ButtonText, QColor(c["text_primary"]))
    palette.setColor(QPalette.Highlight, QColor(c["accent_primary"]))
    palette.setColor(QPalette.HighlightedText, QColor("#FFFFFF"))
    palette.setColor(QPalette.Disabled, QPalette.Text, QColor(c["text_secondary"]))
    palette.setColor(QPalette.Disabled, QPalette.WindowText, QColor(c["text_secondary"]))
    calendar.setPalette(palette)

    weekday_format = QTextCharFormat()
    weekday_format.setForeground(QColor(c["text_primary"]))
    weekday_format.setBackground(QColor(c["bg_secondary"]))

    weekend_format = QTextCharFormat()
    weekend_format.setForeground(QColor(c["accent_danger"]))
    weekend_format.setBackground(QColor(c["bg_secondary"]))

    for day in (Qt.Monday, Qt.Tuesday, Qt.Wednesday, Qt.Thursday, Qt.Friday):
        calendar.setWeekdayTextFormat(day, weekday_format)
    for day in (Qt.Saturday, Qt.Sunday):
        calendar.setWeekdayTextFormat(day, weekend_format)

    def weekday_number(day):
        return day.value if hasattr(day, "value") else int(day)

    def make_date_format(foreground, background=None):
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(foreground))
        if background:
            fmt.setBackground(QColor(background))
        return fmt

    def apply_visible_date_formats(year=None, month=None):
        if year is None or month is None:
            year = calendar.yearShown()
            month = calendar.monthShown()

        first_of_month = QDate(year, month, 1)
        first_weekday = weekday_number(calendar.firstDayOfWeek())
        offset = (first_of_month.dayOfWeek() - first_weekday) % 7
        first_visible = first_of_month.addDays(-offset)
        selected_date = calendar.selectedDate()
        today = QDate.currentDate()

        for index in range(42):
            day = first_visible.addDays(index)
            in_current_month = day.month() == month and day.year() == year
            is_weekend = day.dayOfWeek() in (6, 7)

            if day == selected_date:
                fmt = make_date_format("#FFFFFF", c["accent_primary"])
            elif day == today:
                fmt = make_date_format(c["text_primary"], c["table_selection"])
            elif is_weekend:
                fmt = make_date_format(c["accent_danger"])
            elif in_current_month:
                fmt = make_date_format(c["text_primary"])
            else:
                fmt = make_date_format(c["text_secondary"])

            calendar.setDateTextFormat(day, fmt)

    calendar.currentPageChanged.connect(apply_visible_date_formats)
    calendar.selectionChanged.connect(apply_visible_date_formats)
    apply_visible_date_formats()


def get_stylesheet() -> str:
    """Retourne la feuille de style QSS complète de l'application."""
    c = COLORS
    primary_soft = hex_with_alpha(c["accent_primary"], 42)
    primary_border = hex_with_alpha(c["accent_primary"], 85)
    secondary_soft = hex_with_alpha(c["accent_secondary"], 30)
    danger_soft = hex_with_alpha(c["accent_danger"], 36)
    hover_bg = hex_with_alpha(c["bg_hover"], 210)
    return f"""
QWidget {{
    background-color: {c['bg_primary']};
    color: {c['text_primary']};
    font-family: "Segoe UI", "Inter", "Arial", sans-serif;
    font-size: 13px;
}}

QMainWindow {{
    background-color: {c['bg_primary']};
}}

QLabel {{
    color: {c['text_primary']};
    background: transparent;
    border: none;
    border-radius: 0px;
}}

QLabel[class="title"] {{
    font-size: 22px;
    font-weight: 700;
    color: {c['text_primary']};
}}

QLabel[class="subtitle"] {{
    font-size: 13px;
    color: {c['text_secondary']};
}}

QLabel[class="section-title"] {{
    font-size: 15px;
    font-weight: 600;
    color: {c['text_primary']};
}}

QLineEdit, QTextEdit, QPlainTextEdit {{
    background-color: {c['input_bg']};
    border: 1px solid {c['input_border']};
    border-radius: 14px;
    padding: 12px 14px;
    color: {c['text_primary']};
    selection-background-color: {c['accent_primary']};
    font-size: 13px;
}}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
    border-color: {c['input_focus']};
    background-color: {c['input_focus_bg']};
    selection-color: white;
}}

QLineEdit:hover {{
    border-color: {c['accent_secondary']};
}}

QComboBox {{
    background-color: {c['input_bg']};
    border: 1px solid {c['input_border']};
    border-radius: 14px;
    padding: 10px 14px;
    color: {c['text_primary']};
    min-width: 120px;
    min-height: 22px;
}}

QComboBox:hover {{
    border-color: {c['accent_secondary']};
}}

QComboBox::drop-down {{
    border: none;
    width: 28px;
}}

QComboBox::down-arrow {{
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 6px solid {c['text_secondary']};
    margin-right: 8px;
}}

QComboBox QAbstractItemView {{
    background-color: {c['bg_secondary']};
    border: 1px solid {c['border']};
    color: {c['text_primary']};
    selection-background-color: {c['accent_primary']};
    selection-color: white;
    outline: none;
}}

QPushButton {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {c['accent_primary']}, stop:1 {c['accent_secondary']});
    color: white;
    border: 1px solid {primary_border};
    border-radius: 14px;
    padding: 11px 20px;
    font-weight: 700;
    font-size: 13px;
    min-height: 18px;
}}

QPushButton:hover {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {c['btn_primary_hover']}, stop:1 {c['accent_secondary']});
    border-color: {c['accent_secondary']};
}}

QPushButton:pressed {{
    background: {c['btn_primary_pressed']};
}}

QPushButton:disabled {{
    background-color: {c['bg_tertiary']};
    color: {c['text_muted']};
    border-color: {c['border']};
}}

QPushButton[class="btn-success"] {{
    background: {c['accent_success']};
    border-color: {hex_with_alpha(c['accent_success'], 110)};
}}
QPushButton[class="btn-success"]:hover {{
    background: {c['btn_success_hover']};
}}

QPushButton[class="btn-danger"] {{
    background: {c['accent_danger']};
    border-color: {hex_with_alpha(c['accent_danger'], 110)};
}}
QPushButton[class="btn-danger"]:hover {{
    background: {c['btn_danger_hover']};
}}

QPushButton[class="btn-warning"] {{
    background: {c['accent_warning']};
    border-color: {hex_with_alpha(c['accent_warning'], 110)};
}}
QPushButton[class="btn-warning"]:hover {{
    background: {c['btn_warning_hover']};
}}

QPushButton[class="btn-secondary"] {{
    background: {hover_bg};
    color: {c['text_primary']};
    border: 1px solid {c['border']};
}}
QPushButton[class="btn-secondary"]:hover {{
    background: {primary_soft};
    color: {c['text_primary']};
    border-color: {primary_border};
}}

QPushButton[class="btn-purple"] {{
    background: {c['accent_purple']};
}}
QPushButton[class="btn-purple"]:hover {{
    background: {c['btn_purple_hover']};
}}

QPushButton[class="btn-ghost"] {{
    background-color: transparent;
    color: {c['text_secondary']};
    border: 1px solid transparent;
    padding: 8px 12px;
}}
QPushButton[class="btn-ghost"]:hover {{
    color: {c['text_primary']};
    background-color: {primary_soft};
    border-color: {hex_with_alpha(c['accent_primary'], 50)};
}}

QTableWidget, QTableView {{
    background-color: {c['bg_secondary']};
    border: 1px solid {c['border']};
    border-radius: 18px;
    gridline-color: {c['bg_tertiary']};
    color: {c['text_primary']};
    alternate-background-color: {c['table_alternate']};
    selection-background-color: {c['table_selection']};
    selection-color: {c['text_primary']};
    outline: none;
}}

QPushButton[class="btn-action"] {{
    padding: 0px;
    margin: 0px;
    min-height: 0px;
    min-width: 0px;
    font-size: 0px;
    border-radius: 10px;
}}

QTableWidget::item, QTableView::item {{
    padding: 10px 14px;
    border: none;
}}

QTableWidget::item:selected, QTableView::item:selected {{
    background-color: {c['table_selection']};
    color: {c['text_primary']};
}}

QHeaderView::section {{
    background-color: {c['bg_tertiary']};
    color: {c['text_secondary']};
    padding: 12px 14px;
    border: none;
    border-bottom: 1px solid {c['border']};
    font-weight: 600;
    font-size: 12px;
}}

QHeaderView::section:first {{
    border-top-left-radius: 18px;
}}

QHeaderView::section:last {{
    border-top-right-radius: 18px;
}}

QScrollBar:vertical {{
    background: transparent;
    width: 10px;
    border-radius: 5px;
    margin: 0;
}}

QScrollBar::handle:vertical {{
    background: {hex_with_alpha(c['accent_secondary'], 110)};
    border-radius: 5px;
    min-height: 30px;
}}

QScrollBar::handle:vertical:hover {{
    background: {c['accent_secondary']};
}}

QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; }}

QScrollBar:horizontal {{
    background: transparent;
    height: 10px;
    border-radius: 5px;
}}

QScrollBar::handle:horizontal {{
    background: {hex_with_alpha(c['accent_secondary'], 110)};
    border-radius: 5px;
    min-width: 30px;
}}

QTabWidget::pane {{
    border: 1px solid {c['border']};
    border-radius: 18px;
    background-color: {c['bg_secondary']};
    top: -1px;
}}

QTabBar::tab {{
    background-color: {c['bg_tertiary']};
    color: {c['text_secondary']};
    padding: 10px 18px;
    margin-right: 6px;
    border-radius: 12px 12px 0 0;
    font-weight: 600;
}}

QTabBar::tab:selected {{
    background-color: {c['accent_primary']};
    color: white;
}}

QTabBar::tab:hover:!selected {{
    background-color: {c['bg_hover']};
    color: {c['text_primary']};
}}

QDialog {{
    background-color: {c['bg_secondary']};
    border-radius: 20px;
}}

QGroupBox {{
    border: 1px solid {c['border']};
    border-radius: 18px;
    margin-top: 12px;
    padding-top: 14px;
    font-weight: 600;
    color: {c['text_secondary']};
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 8px;
    color: {c['accent_primary']};
    font-size: 12px;
}}

QDateEdit, QSpinBox, QTimeEdit {{
    background-color: {c['input_bg']};
    border: 1px solid {c['input_border']};
    border-radius: 14px;
    padding: 10px 12px;
    color: {c['text_primary']};
}}

QDateEdit:focus, QSpinBox:focus, QTimeEdit:focus {{
    border-color: {c['input_focus']};
}}

QDateEdit::drop-down {{
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 28px;
    border: none;
    border-left: 1px solid {c['border']};
    border-top-right-radius: 12px;
    border-bottom-right-radius: 12px;
    background-color: {c['bg_tertiary']};
}}

QDateEdit::down-arrow {{
    image: none;
    width: 0px;
    height: 0px;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 6px solid {c['text_secondary']};
}}

QDateEdit::up-button, QSpinBox::up-button,
QDateEdit::down-button, QSpinBox::down-button {{
    background-color: {c['bg_hover']};
    border-radius: 6px;
    width: 20px;
}}

QCheckBox, QRadioButton {{
    color: {c['text_primary']};
    spacing: 8px;
}}

QCheckBox::indicator, QRadioButton::indicator {{
    width: 18px;
    height: 18px;
    border: 1px solid {c['input_border']};
    border-radius: 6px;
    background: {c['input_bg']};
}}

QCheckBox::indicator:checked {{
    background: {c['accent_primary']};
    border-color: {c['accent_primary']};
}}

QMessageBox {{
    background-color: {c['bg_secondary']};
}}

QToolTip {{
    background-color: {c['bg_tertiary']};
    color: {c['text_primary']};
    border: 1px solid {c['border']};
    border-radius: 8px;
    padding: 6px 10px;
}}

QProgressBar {{
    background-color: {c['bg_tertiary']};
    border-radius: 8px;
    height: 10px;
    text-align: center;
    color: transparent;
}}

QProgressBar::chunk {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {c['accent_primary']}, stop:1 {c['accent_secondary']});
    border-radius: 8px;
}}

QSplitter::handle {{
    background-color: {c['border']};
}}

QCalendarWidget QWidget {{
    alternate-background-color: {c['bg_tertiary']};
    background-color: {c['bg_secondary']};
    color: {c['text_primary']};
}}

QCalendarWidget {{
    background-color: {c['bg_secondary']};
    color: {c['text_primary']};
    border: 1px solid {c['border']};
    border-radius: 10px;
}}

QCalendarWidget QWidget#qt_calendar_navigationbar {{
    background-color: {c['bg_tertiary']};
    border-bottom: 1px solid {c['border']};
    border-top-left-radius: 10px;
    border-top-right-radius: 10px;
}}

QCalendarWidget QAbstractItemView:enabled {{
    color: {c['text_primary']};
    background-color: {c['bg_secondary']};
    selection-background-color: {c['accent_primary']};
    selection-color: white;
    outline: none;
}}

QCalendarWidget QAbstractItemView:disabled {{
    color: {c['text_secondary']};
    background-color: {c['bg_secondary']};
}}

QCalendarWidget QTableView {{
    color: {c['text_primary']};
    background-color: {c['bg_secondary']};
    alternate-background-color: {c['bg_secondary']};
    selection-background-color: {c['accent_primary']};
    selection-color: white;
    border: none;
    gridline-color: {c['border_light']};
}}

QCalendarWidget QTableView::item {{
    color: {c['text_primary']};
    background-color: {c['bg_secondary']};
}}

QCalendarWidget QTableView::item:selected {{
    color: white;
    background-color: {c['accent_primary']};
}}

QCalendarWidget QHeaderView::section {{
    color: {c['text_secondary']};
    background-color: {c['bg_secondary']};
    border: none;
    padding: 4px 0px;
    font-weight: 700;
}}

QCalendarWidget QToolButton {{
    color: {c['text_primary']};
    background-color: transparent;
    border: none;
    border-radius: 6px;
}}

QCalendarWidget QToolButton:hover {{
    background-color: {c['bg_hover']};
}}

QCalendarWidget QMenu {{
    background-color: {c['bg_secondary']};
    color: {c['text_primary']};
    border: 1px solid {c['border']};
}}

QCalendarWidget QMenu::item:selected {{
    background-color: {c['accent_primary']};
    color: white;
}}

QCalendarWidget QSpinBox {{
    background-color: {c['bg_secondary']};
    color: {c['text_primary']};
    selection-background-color: {c['accent_primary']};
    selection-color: white;
    border: 1px solid {c['border']};
    border-radius: 6px;
    padding: 2px 6px;
}}
"""
