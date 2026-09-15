"""
Fenêtre principale de l'application — Conteneur principal avec routing des vues.
Gère la navigation entre les pages via la sidebar.
"""
from PySide6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QStackedWidget,
                                QPushButton, QLabel, QHBoxLayout, QFrame,
                                QMessageBox, QApplication)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont

from app.models.models import Utilisateur
from app.services.auth_service import AuthService
from app.widgets.sidebar import Sidebar
from app.utils.theme import COLORS


class MainWindow(QMainWindow):
    """Fenêtre principale avec sidebar + zone de contenu stackée."""

    def __init__(self, user: Utilisateur, parent=None):
        super().__init__(parent)
        self.user = user
        self.setWindowTitle(f"GestPrésences - {user.nom_complet}")
        self._setup_responsive_size()
        self._views: dict[str, QWidget] = {}
        self._build_ui()
        self._navigate_to_default()

    def _setup_responsive_size(self):
        """Configure une taille responsive adaptée aux petits et grands écrans."""
        app = QApplication.instance()
        screen = app.primaryScreen()
        if screen:
            screen_rect = screen.availableGeometry()
        else:
            screen_rect = app.desktop().geometry()

        width = int(screen_rect.width() * 0.96)
        height = int(screen_rect.height() * 0.92)

        min_width = max(860, min(960, screen_rect.width() - 40))
        min_height = max(600, min(640, screen_rect.height() - 40))
        self.setMinimumSize(min_width, min_height)

        width = max(width, min_width)
        height = max(height, min_height)
        width = min(width, screen_rect.width())
        height = min(height, screen_rect.height())

        x = int((screen_rect.width() - width) / 2)
        y = int((screen_rect.height() - height) / 2)

        self.setGeometry(x, y, width, height)

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        root_layout = QHBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # ── Sidebar ──
        self.sidebar = Sidebar(self.user.role, self.user.nom_complet)
        self.sidebar.page_changed.connect(self._on_page_change)
        self.sidebar.logout_clicked.connect(self._do_logout)
        self.sidebar.theme_toggle_clicked.connect(self._toggle_theme)
        root_layout.addWidget(self.sidebar)

        # ── Zone de contenu ──
        content_area = QWidget()
        content_area.setStyleSheet(f"background-color: {COLORS['bg_primary']};")
        content_layout = QHBoxLayout(content_area)
        content_layout.setContentsMargins(0, 0, 0, 0)

        # Stack de pages
        self.stack = QStackedWidget()
        self.stack.setStyleSheet("background-color: transparent;")
        content_layout.addWidget(self.stack)

        root_layout.addWidget(content_area)

        # ── Charger les vues selon le rôle ──
        if self.user.role == "admin":
            self._load_admin_views()
        elif self.user.role == "comptable":
            self._load_comptable_views()
        else:
            self._load_agent_views()

    def _load_admin_views(self):
        """Charge toutes les vues administrateur."""
        from app.views.admin.dashboard_view  import DashboardView
        from app.views.admin.employees_view  import EmployeesView
        from app.views.admin.attendance_view import AttendanceView
        from app.views.admin.absences_view   import AbsencesView
        from app.views.admin.stats_view      import StatsView
        from app.views.admin.history_view    import HistoryView
        from app.views.admin.reports_view    import ReportsView
        from app.views.admin.users_view      import UsersView

        views = {
            "dashboard":  DashboardView(),
            "employees":  EmployeesView(),
            "attendance": AttendanceView(),
            "absences":   AbsencesView(),
            "stats":      StatsView(),
            "history":    HistoryView(),
            "reports":    ReportsView(),
            "users":      UsersView(),
        }
        for name, view in views.items():
            self._views[name] = view
            self.stack.addWidget(view)

    def _load_comptable_views(self):
        """Charge les vues du comptable (paie et bulletins)."""
        from app.views.comptable.dashboard_view import ComptableDashboardView
        from app.views.comptable.salaries_view import SalariesView
        from app.views.comptable.payroll_view import PayrollView
        from app.views.comptable.payslips_view import PayslipsView

        dashboard = ComptableDashboardView()
        dashboard.navigation_requested.connect(self._navigate_to_page)

        views = {
            "payroll_dashboard": dashboard,
            "payroll_salaries":  SalariesView(),
            "payroll_monthly":   PayrollView(),
            "payroll_payslips":  PayslipsView(),
        }
        for name, view in views.items():
            self._views[name] = view
            self.stack.addWidget(view)

    def _load_agent_views(self):
        """Charge les vues de l'agent de présence."""
        from app.views.agent.dashboard_view import AgentDashboardView
        from app.views.agent.search_view  import SearchView
        from app.views.agent.record_view  import RecordView
        from app.views.agent.today_view   import TodayView

        dashboard = AgentDashboardView()
        dashboard.navigation_requested.connect(self._navigate_to_page)

        views = {
            "agent_dashboard": dashboard,
            "search":          SearchView(),
            "record":          RecordView(),
            "today":           TodayView(),
        }
        for name, view in views.items():
            self._views[name] = view
            self.stack.addWidget(view)

    def _navigate_to_default(self):
        defaults = {"admin": "dashboard", "comptable": "payroll_dashboard", "agent": "agent_dashboard"}
        default = defaults.get(self.user.role, "agent_dashboard")
        self._on_page_change(default)
        self.sidebar.navigate_to(default)

    def _on_page_change(self, page_id: str):
        """Affiche la page demandée."""
        if page_id not in self._views:
            return
        self._active_page = page_id
        view = self._views[page_id]
        self.stack.setCurrentWidget(view)

        # Rafraîchir la vue si elle a une méthode refresh()
        if hasattr(view, "refresh"):
            view.refresh()

    def _navigate_to_page(self, page_id: str):
        """Navigue vers une page en mettant à jour la sidebar et le stacked widget."""
        self.sidebar.navigate_to(page_id)
        self._on_page_change(page_id)

    def _toggle_theme(self):
        """Bascule le thème entre Clair et Sombre, applique le QSS et recrée la fenêtre."""
        from app.utils.theme import THEME_MODE, set_theme_mode, get_stylesheet
        from PySide6.QtWidgets import QApplication

        # Inverser le thème
        new_theme = "light" if THEME_MODE == "dark" else "dark"
        set_theme_mode(new_theme)

        # Mettre à jour la feuille de style globale
        QApplication.instance().setStyleSheet(get_stylesheet())

        # Conserver la page active avant la reconstruction
        active_page = self._active_page if hasattr(self, "_active_page") else "dashboard"

        # Re-instancier MainWindow pour recréer tous les widgets avec la nouvelle palette
        from app.views.main_window import MainWindow
        new_win = MainWindow(self.user)
        
        # Restaurer la navigation vers la page active
        new_win.sidebar.navigate_to(active_page)
        new_win._on_page_change(active_page)
        new_win.show()

        # Garder la référence pour éviter le garbage collection
        QApplication.instance()._main_win = new_win

        # Fermer la fenêtre actuelle
        self.close()

    def _do_logout(self):
        """Déconnecte l'utilisateur et revient à la fenêtre de login."""
        reply = QMessageBox.question(
            self, "Déconnexion",
            f"Voulez-vous vous déconnecter ?\n\n"
            f"Vous serez redirigé vers la page de connexion.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        AuthService.logout()

        # Ouvrir la fenêtre de login
        from app.views.login_window import LoginWindow
        self._login_win = LoginWindow()

        def on_login(user):
            self._login_win.close()
            new_main = MainWindow(user)
            new_main.show()
            # Garder la référence pour éviter le garbage collection
            self._login_win._main_ref = new_main

        self._login_win.login_success.connect(on_login)
        self._login_win.show()

        # Fermer cette fenêtre
        self.close()

    def closeEvent(self, event):
        """Déconnexion à la fermeture."""
        AuthService.logout()
        event.accept()
