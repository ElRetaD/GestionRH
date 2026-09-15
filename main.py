"""
Point d'entrée principal de l'application.
Initialise la BDD, applique le thème et lance la fenêtre de connexion.
"""
import sys
import os

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QIcon

# ── Initialisation de la base de données ──────────────────────────────────────
from app.database.models import create_tables
from app.database.migrations import run_migrations
from app.database.seed import seed_database
from app.utils.theme import get_stylesheet, load_theme_mode, set_theme_mode
from app.views.login_window import LoginWindow
from app.views.main_window import MainWindow


def main():
    # Activer le scaling HiDPI
    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"

    # Fixer l'icône de la barre des tâches sous Windows
    if sys.platform == "win32":
        import ctypes
        try:
            # Assigne un ID d'application unique pour que Windows affiche notre icône personnalisée sur la barre des tâches
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("sbzs.hr.gestpresences.1.0")
        except Exception:
            pass

    app = QApplication(sys.argv)
    app.setApplicationName("GestPrésences")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("RCA Systems")
    app.setStyle("Fusion")

    # Police par défaut
    font = QFont("Segoe UI", 10)
    app.setFont(font)

    # Définir l'icône globale de l'application
    logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "logo.png")
    if os.path.exists(logo_path):
        app.setWindowIcon(QIcon(logo_path))

    # Initialiser et appliquer le thème
    set_theme_mode(load_theme_mode())
    app.setStyleSheet(get_stylesheet())

    # Initialiser la BDD
    create_tables()
    run_migrations()
    seed_database()

    # ── Fenêtre de connexion ──
    login_win = LoginWindow()

    def on_login(user):
        """Appelé après connexion réussie."""
        login_win.close()
        main_win = MainWindow(user)
        main_win.show()
        # Garder une référence pour éviter le garbage collection
        app._main_win = main_win

    login_win.login_success.connect(on_login)
    login_win.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
