"""
Données initiales de la base de données.
Crée le compte administrateur par défaut et des données de démonstration.
"""
import bcrypt
from app.database.connection import db


def seed_database():
    """Initialise la base de données avec les données de démarrage."""
    _ensure_default_users()
    _create_sample_data()
    _seed_sample_salaries()
    print("[DB] Données initiales chargées.")


def _ensure_user(username: str, password: str, role: str, nom_complet: str, email: str):
    """Crée un compte par défaut s'il n'existe pas encore."""
    existing = db.fetchone(
        "SELECT id FROM utilisateurs WHERE nom_utilisateur = ?",
        (username,),
    )
    if existing:
        return
    password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    db.execute(
        """
        INSERT INTO utilisateurs (nom_utilisateur, mot_de_passe, role, nom_complet, email)
        VALUES (?, ?, ?, ?, ?)
        """,
        (username, password_hash, role, nom_complet, email),
    )


def _ensure_default_users():
    """Crée les comptes de démonstration (admin, agent, comptable)."""
    _ensure_user(
        "admin", "Admin@2024", "admin",
        "Administrateur Système", "admin@entreprise.com",
    )
    _ensure_user(
        "agent", "Agent@2024", "agent",
        "Assistant RH", "agent@entreprise.com",
    )
    _ensure_user(
        "comptable", "Comptable@2024", "comptable",
        "Comptable Principal", "comptable@entreprise.com",
    )


def _create_sample_data():
    """Crée quelques employés de démonstration si la table est vide."""
    count = db.fetchone("SELECT COUNT(*) as total FROM employes")
    if count and count["total"] > 0:
        return

    from app.services.employee_service import EmployeeService

    sample_employees = [
        ("Hamdi", "Imrane",  "+212 661 112233", "imrane.hamdi@entreprise.ma",  "Informatique",        "Développeur Fullstack", "2024-01-15"),
        ("Sabah", "Zakaria", "+212 661 445566", "zakaria.sabah@entreprise.ma", "Ressources Humaines", "Responsable RH",        "2023-09-01"),
        ("Alla",  "Adam",    "+212 661 778899", "adam.alla@entreprise.ma",    "Commercial",          "Responsable Ventes",    "2024-03-10"),
    ]

    for nom, prenom, tel, email, dept, poste, date_emb in sample_employees:
        EmployeeService.create(nom, prenom, tel, email, dept, poste, date_emb)

    print(f"[DB] {len(sample_employees)} employés de démonstration créés.")


def _seed_sample_salaries():
    """Configure des salaires de démonstration pour les employés actifs."""
    count = db.fetchone("SELECT COUNT(*) as total FROM salaires_employes")
    if count and count["total"] > 0:
        return

    base_salaries = [9500, 11000, 8500]
    employees = db.fetchall(
        "SELECT id FROM employes WHERE actif = 1 ORDER BY id LIMIT ?",
        (len(base_salaries),),
    )
    for emp, base in zip(employees, base_salaries):
        taux = round(base / 173.33, 2)
        db.execute(
            """
            INSERT OR IGNORE INTO salaires_employes (employe_id, salaire_base, taux_horaire)
            VALUES (?, ?, ?)
            """,
            (emp["id"], base, taux),
        )
    if employees:
        print(f"[DB] {len(employees)} salaires de démonstration configurés.")
