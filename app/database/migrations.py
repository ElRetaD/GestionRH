"""
Migrations incrémentales de la base de données.
Exécutées au démarrage après create_tables().
"""
from app.database.connection import db


def run_migrations():
    """Applique toutes les migrations en attente."""
    _migrate_utilisateurs_comptable_role()
    _create_payroll_tables()
    print("[DB] Migrations appliquées.")


def _migrate_utilisateurs_comptable_role():
    """Étend le rôle utilisateur pour inclure 'comptable'."""
    row = db.fetchone(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='utilisateurs'"
    )
    if not row or not row["sql"]:
        return
    if "comptable" in row["sql"]:
        return

    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys=off")
    cursor.execute("BEGIN")
    cursor.execute("""
        CREATE TABLE utilisateurs_new (
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
    cursor.execute("INSERT INTO utilisateurs_new SELECT * FROM utilisateurs")
    cursor.execute("DROP TABLE utilisateurs")
    cursor.execute("ALTER TABLE utilisateurs_new RENAME TO utilisateurs")
    cursor.execute("COMMIT")
    cursor.execute("PRAGMA foreign_keys=on")
    conn.commit()
    print("[DB] Migration : rôle comptable ajouté.")


def _create_payroll_tables():
    """Crée les tables de paie si elles n'existent pas."""
    conn = db.get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS salaires_employes (
            id                INTEGER PRIMARY KEY AUTOINCREMENT,
            employe_id        INTEGER UNIQUE NOT NULL,
            salaire_base      REAL    NOT NULL DEFAULT 0,
            taux_horaire      REAL    NOT NULL DEFAULT 0,
            date_modification TEXT    DEFAULT (datetime('now', 'localtime')),
            FOREIGN KEY (employe_id) REFERENCES employes(id) ON DELETE CASCADE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS elements_paie (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            employe_id     INTEGER NOT NULL,
            periode        TEXT    NOT NULL,
            type_element   TEXT    NOT NULL
                           CHECK(type_element IN ('prime', 'heures_sup', 'deduction')),
            libelle        TEXT    NOT NULL,
            montant        REAL    DEFAULT 0,
            heures         REAL    DEFAULT 0,
            taux           REAL    DEFAULT 0,
            notes          TEXT    DEFAULT '',
            date_creation  TEXT    DEFAULT (datetime('now', 'localtime')),
            FOREIGN KEY (employe_id) REFERENCES employes(id) ON DELETE CASCADE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bulletins_paie (
            id                INTEGER PRIMARY KEY AUTOINCREMENT,
            employe_id        INTEGER NOT NULL,
            periode           TEXT    NOT NULL,
            salaire_base      REAL    DEFAULT 0,
            total_primes      REAL    DEFAULT 0,
            total_heures_sup  REAL    DEFAULT 0,
            total_deductions  REAL    DEFAULT 0,
            heures_travaillees REAL   DEFAULT 0,
            salaire_brut      REAL    DEFAULT 0,
            salaire_net       REAL    DEFAULT 0,
            pdf_path          TEXT    DEFAULT '',
            statut            TEXT    DEFAULT 'brouillon'
                              CHECK(statut IN ('brouillon', 'valide')),
            genere_par        INTEGER DEFAULT NULL,
            date_calcul       TEXT    DEFAULT (datetime('now', 'localtime')),
            FOREIGN KEY (employe_id) REFERENCES employes(id) ON DELETE CASCADE,
            FOREIGN KEY (genere_par) REFERENCES utilisateurs(id),
            UNIQUE(employe_id, periode)
        )
    """)

    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_elements_paie_periode ON elements_paie(periode)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_elements_paie_employe ON elements_paie(employe_id)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_bulletins_periode ON bulletins_paie(periode)"
    )

    conn.commit()
