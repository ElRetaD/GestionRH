"""Custom date edit with a lightweight calendar popup.

This avoids native QCalendarWidget rendering issues on some Windows/PySide
setups where a few day numbers are painted with unreadable colors.
"""
from PySide6.QtCore import QDate, QPoint, Qt
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import (
    QAbstractSpinBox,
    QApplication,
    QDateEdit,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QToolButton,
    QVBoxLayout,
)

from app.utils.theme import COLORS


class _CalendarPopup(QFrame):
    def __init__(self, date_edit: "ThemedDateEdit"):
        super().__init__(date_edit, Qt.Popup | Qt.FramelessWindowHint)
        self.date_edit = date_edit
        selected = date_edit.date()
        self.current_month = QDate(selected.year(), selected.month(), 1)
        self.day_buttons = []
        self._build_ui()
        self._render()

    def _build_ui(self):
        c = COLORS
        self.setObjectName("customCalendarPopup")
        self.setStyleSheet(f"""
            QFrame#customCalendarPopup {{
                background-color: {c['bg_secondary']};
                border: 1px solid {c['border']};
                border-radius: 10px;
            }}
            QLabel {{
                color: {c['text_primary']};
                background: transparent;
                border: none;
            }}
            QToolButton {{
                background: transparent;
                color: {c['text_primary']};
                border: none;
                border-radius: 6px;
                font-weight: 700;
                min-width: 28px;
                min-height: 24px;
            }}
            QToolButton:hover {{
                background-color: {c['bg_hover']};
            }}
        """)

        root = QVBoxLayout(self)
        root.setContentsMargins(10, 8, 10, 10)
        root.setSpacing(8)

        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.setSpacing(6)

        self.prev_btn = QToolButton()
        self.prev_btn.setText("<")
        self.prev_btn.clicked.connect(lambda: self._move_month(-1))
        header.addWidget(self.prev_btn)

        self.title = QLabel()
        self.title.setAlignment(Qt.AlignCenter)
        self.title.setStyleSheet(
            f"font-weight: 800; color: {c['text_primary']}; background: transparent;"
        )
        header.addWidget(self.title, 1)

        self.next_btn = QToolButton()
        self.next_btn.setText(">")
        self.next_btn.clicked.connect(lambda: self._move_month(1))
        header.addWidget(self.next_btn)

        root.addLayout(header)

        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(4)
        grid.setVerticalSpacing(4)
        root.addLayout(grid)

        for col, day in enumerate(("Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim")):
            label = QLabel(day)
            label.setAlignment(Qt.AlignCenter)
            label.setFixedSize(32, 20)
            label.setStyleSheet(
                f"color: {c['text_secondary']}; font-size: 11px; font-weight: 700;"
            )
            grid.addWidget(label, 0, col)

        for row in range(6):
            for col in range(7):
                btn = QPushButton()
                btn.setCursor(QCursor(Qt.PointingHandCursor))
                btn.setFixedSize(32, 28)
                btn.clicked.connect(lambda checked=False, b=btn: self._select_button_date(b))
                self.day_buttons.append(btn)
                grid.addWidget(btn, row + 1, col)

    def _move_month(self, offset: int):
        self.current_month = self.current_month.addMonths(offset)
        self._render()

    def _select_button_date(self, button: QPushButton):
        date = QDate.fromString(button.property("date"), "yyyy-MM-dd")
        if date.isValid():
            self.date_edit.setDate(date)
            self.close()

    def _button_style(self, color: str, background: str, border: str) -> str:
        c = COLORS
        return f"""
            QPushButton {{
                color: {color};
                background-color: {background};
                border: 1px solid {border};
                border-radius: 6px;
                padding: 0;
                font-weight: 700;
                font-size: 12px;
            }}
            QPushButton:hover {{
                color: {c['text_primary']};
                background-color: {c['bg_hover']};
                border-color: {c['accent_secondary']};
            }}
        """

    def _render(self):
        c = COLORS
        month_names = (
            "Janvier", "Fevrier", "Mars", "Avril", "Mai", "Juin",
            "Juillet", "Aout", "Septembre", "Octobre", "Novembre", "Decembre",
        )
        self.title.setText(f"{month_names[self.current_month.month() - 1]} {self.current_month.year()}")

        first = self.current_month
        start = first.addDays(-(first.dayOfWeek() - 1))
        selected = self.date_edit.date()
        today = QDate.currentDate()

        for index, button in enumerate(self.day_buttons):
            date = start.addDays(index)
            is_current_month = (
                date.month() == self.current_month.month()
                and date.year() == self.current_month.year()
            )
            is_weekend = date.dayOfWeek() in (6, 7)

            color = c["text_primary"]
            background = c["bg_secondary"]
            border = c["bg_secondary"]

            if not is_current_month:
                color = c["text_secondary"]
            if is_weekend:
                color = c["accent_danger"]
            if date == today:
                background = c["table_selection"]
                border = c["accent_secondary"]
            if date == selected:
                color = "#FFFFFF"
                background = c["accent_primary"]
                border = c["accent_primary"]

            button.setText(str(date.day()))
            button.setProperty("date", date.toString("yyyy-MM-dd"))
            button.setStyleSheet(self._button_style(color, background, border))


class ThemedDateEdit(QDateEdit):
    """QDateEdit replacement that uses a custom calendar popup."""

    def __init__(self, date=None, parent=None):
        super().__init__(parent)
        self.setDate(date or QDate.currentDate())
        self.setCalendarPopup(False)
        self.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.setReadOnly(True)
        self.setCursor(QCursor(Qt.PointingHandCursor))

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.show_calendar_popup()
            event.accept()
            return
        super().mousePressEvent(event)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Space, Qt.Key_Down, Qt.Key_F4):
            self.show_calendar_popup()
            event.accept()
            return
        super().keyPressEvent(event)

    def show_calendar_popup(self):
        popup = _CalendarPopup(self)
        popup.adjustSize()

        pos = self.mapToGlobal(QPoint(0, self.height() + 4))
        screen = QApplication.screenAt(pos) or QApplication.primaryScreen()
        if screen:
            area = screen.availableGeometry()
            if pos.x() + popup.width() > area.right():
                pos.setX(max(area.left(), area.right() - popup.width()))
            if pos.y() + popup.height() > area.bottom():
                pos.setY(self.mapToGlobal(QPoint(0, -popup.height() - 4)).y())

        popup.move(pos)
        popup.show()
