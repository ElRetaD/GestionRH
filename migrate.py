import sqlite3
import os
from app.config import DB_PATH

def migrate():
    print(f"Connecting to {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("PRAGMA foreign_keys=off;")
    cursor.execute("BEGIN TRANSACTION;")

    # 1. Migrate presences
    print("Migrating presences...")
    cursor.execute("ALTER TABLE presences RENAME TO _presences_old;")
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
    cursor.execute("INSERT INTO presences SELECT * FROM _presences_old;")
    cursor.execute("DROP TABLE _presences_old;")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_presences_employe ON presences(employe_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_presences_date    ON presences(date)")

    # 2. Migrate absences
    print("Migrating absences...")
    cursor.execute("ALTER TABLE absences RENAME TO _absences_old;")
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
    cursor.execute("INSERT INTO absences SELECT * FROM _absences_old;")
    cursor.execute("DROP TABLE _absences_old;")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_absences_employe  ON absences(employe_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_absences_date     ON absences(date)")

    cursor.execute("COMMIT;")
    cursor.execute("PRAGMA foreign_keys=on;")
    conn.close()
    print("Migration complete!")

if __name__ == "__main__":
    migrate()
