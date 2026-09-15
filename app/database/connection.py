"""
Connexion SQLite — Singleton thread-safe.
Toutes les couches de l'application passent par ce module pour accéder à la BDD.
"""
import sqlite3
import threading
from app.config import DB_PATH


class DatabaseConnection:
    """Gestionnaire de connexion SQLite avec support multi-thread."""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """Initialise la connexion à la base de données."""
        self._local = threading.local()
        self._db_path = DB_PATH

    def get_connection(self) -> sqlite3.Connection:
        """Retourne la connexion SQLite pour le thread courant."""
        if not hasattr(self._local, "connection") or self._local.connection is None:
            self._local.connection = sqlite3.connect(
                self._db_path,
                check_same_thread=False
            )
            self._local.connection.row_factory = sqlite3.Row
            # Activer les clés étrangères
            self._local.connection.execute("PRAGMA foreign_keys = ON")
        return self._local.connection

    def execute(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        """Exécute une requête SQL et retourne le curseur."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        return cursor

    def executemany(self, query: str, params_list: list) -> sqlite3.Cursor:
        """Exécute une requête SQL pour plusieurs jeux de paramètres."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.executemany(query, params_list)
        conn.commit()
        return cursor

    def fetchall(self, query: str, params: tuple = ()) -> list:
        """Retourne tous les résultats d'une requête SELECT."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def fetchone(self, query: str, params: tuple = ()) -> dict | None:
        """Retourne un seul résultat d'une requête SELECT."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        row = cursor.fetchone()
        return dict(row) if row else None

    def close(self):
        """Ferme la connexion du thread courant."""
        if hasattr(self._local, "connection") and self._local.connection:
            self._local.connection.close()
            self._local.connection = None


# Instance globale unique
db = DatabaseConnection()
