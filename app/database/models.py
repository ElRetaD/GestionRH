"""
Schéma de la base de données — Création de toutes les tables.
Ce module est exécuté au démarrage pour s'assurer que le schéma est à jour.
"""
from app.database.connection import db


def create_tables():
    """Crée toutes les tables de la base de données si elles n'existent pas."""
    conn = db.get_connection()
    cursor = conn.cursor()

    # ─── Table : utilisateurs ──────────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS utilisateurs (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            nom_utilisateur  TEXT    UNIQUE NOT NULL,
            mot_de_passe     TEXT    NOT NULL,
            role             TEXT    NOT NULL CHECK(role IN ('admin', 'agent', 'comptable')),
            nom_complet      TEXT    DEFAULT '',
            email            TEXT    DEFAULT '',
            actif            INTEGER DEFAULT 1,
            date_creation    TEXT    DEFAULT (datetime('now', 'localtime'))
        )
    """)

    # ─── Table : employes ──────────────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS employes (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            nom             TEXT    NOT NULL,
            prenom          TEXT    NOT NULL,
            telephone       TEXT    DEFAULT '',
            email           TEXT    DEFAULT '',
            departement     TEXT    DEFAULT '',
            poste           TEXT    DEFAULT '',
            date_embauche   TEXT    DEFAULT '',
            qr_code_path    TEXT    DEFAULT '',
            qr_data         TEXT    UNIQUE DEFAULT '',
            actif           INTEGER DEFAULT 1,
            date_creation   TEXT    DEFAULT (datetime('now', 'localtime'))
        )
    """)

    # ─── Table : presences ─────────────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS presences (
            id                INTEGER PRIMARY KEY AUTOINCREMENT,
            employe_id        INTEGER NOT NULL,
            date              TEXT    NOT NULL,
            heure_entree      TEXT    DEFAULT '',
            heure_sortie      TEXT    DEFAULT '',
            heures_travaillees REAL   DEFAULT 0.0,
            statut            TEXT    DEFAULT 'present'
                              CHECK(statut IN ('present', 'absent', 'conge', 'maladie', 'teletravail', 'retard')),
            retard            INTEGER DEFAULT 0,
            minutes_retard    INTEGER DEFAULT 0,
            enregistre_par    INTEGER DEFAULT NULL,
            notes             TEXT    DEFAULT '',
            date_creation     TEXT    DEFAULT (datetime('now', 'localtime')),
            FOREIGN KEY (employe_id)    REFERENCES employes(id)    ON DELETE CASCADE,
            FOREIGN KEY (enregistre_par) REFERENCES utilisateurs(id),
            UNIQUE(employe_id, date)
        )
    """)

    # ─── Table : absences ──────────────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS absences (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            employe_id      INTEGER NOT NULL,
            date            TEXT    NOT NULL,
            type_absence    TEXT    NOT NULL
                            CHECK(type_absence IN ('absent', 'conge', 'maladie', 'teletravail')),
            motif           TEXT    DEFAULT '',
            justifiee       INTEGER DEFAULT 0,
            enregistre_par  INTEGER DEFAULT NULL,
            date_creation   TEXT    DEFAULT (datetime('now', 'localtime')),
            FOREIGN KEY (employe_id)    REFERENCES employes(id)   ON DELETE CASCADE,
            FOREIGN KEY (enregistre_par) REFERENCES utilisateurs(id)
        )
    """)

    # ─── Table : retards ───────────────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS retards (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            employe_id       INTEGER NOT NULL,
            date             TEXT    NOT NULL,
            heure_arrivee    TEXT    NOT NULL,
            heure_officielle TEXT    NOT NULL,
            minutes_retard   INTEGER NOT NULL,
            date_creation    TEXT    DEFAULT (datetime('now', 'localtime')),
            FOREIGN KEY (employe_id) REFERENCES employes(id) ON DELETE CASCADE
        )
    """)

    # ─── Table : historique ────────────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS historique (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            type_action     TEXT    NOT NULL,
            employe_id      INTEGER DEFAULT NULL,
            utilisateur_id  INTEGER DEFAULT NULL,
            description     TEXT    DEFAULT '',
            donnees_json    TEXT    DEFAULT '{}',
            timestamp       TEXT    DEFAULT (datetime('now', 'localtime')),
            FOREIGN KEY (employe_id)    REFERENCES employes(id),
            FOREIGN KEY (utilisateur_id) REFERENCES utilisateurs(id)
        )
    """)

    # ─── Index pour améliorer les performances ─────────────────────────────────
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_presences_employe ON presences(employe_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_presences_date    ON presences(date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_absences_employe  ON absences(employe_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_absences_date     ON absences(date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_retards_employe   ON retards(employe_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_historique_ts     ON historique(timestamp)")

    conn.commit()
    print("[DB] Tables créées avec succès.")
