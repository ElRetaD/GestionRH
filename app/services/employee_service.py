"""
Service de gestion des employés.
CRUD complet avec génération automatique du QR code à la création.
"""
from typing import Optional, List
from app.database.connection import db
from app.models.models import Employe


class EmployeeService:
    """Service CRUD pour les employés."""

    @staticmethod
    def get_all(include_inactive: bool = False) -> List[Employe]:
        """Retourne tous les employés actifs (ou tous si include_inactive=True)."""
        query = "SELECT * FROM employes"
        if not include_inactive:
            query += " WHERE actif = 1"
        query += " ORDER BY nom, prenom"
        rows = db.fetchall(query)
        return [EmployeeService._row_to_model(r) for r in rows]

    @staticmethod
    def get_by_id(employee_id: int) -> Optional[Employe]:
        """Retourne un employé par son ID."""
        row = db.fetchone("SELECT * FROM employes WHERE id = ?", (employee_id,))
        return EmployeeService._row_to_model(row) if row else None

    @staticmethod
    def get_by_qr_data(qr_data: str) -> Optional[Employe]:
        """Retourne un employé en cherchant par ses données QR code."""
        row = db.fetchone("SELECT * FROM employes WHERE qr_data = ?", (qr_data,))
        return EmployeeService._row_to_model(row) if row else None

    @staticmethod
    def search(term: str) -> List[Employe]:
        """Recherche des employés par nom, prénom, email ou département."""
        pattern = f"%{term}%"
        rows = db.fetchall(
            """SELECT * FROM employes
               WHERE actif = 1 AND (
                   nom LIKE ? OR prenom LIKE ? OR
                   email LIKE ? OR departement LIKE ? OR poste LIKE ?
               )
               ORDER BY nom, prenom""",
            (pattern, pattern, pattern, pattern, pattern)
        )
        return [EmployeeService._row_to_model(r) for r in rows]

    @staticmethod
    def create(nom: str, prenom: str, telephone: str, email: str,
               departement: str, poste: str, date_embauche: str) -> Optional[Employe]:
        """
        Crée un nouvel employé et génère son QR code automatiquement.
        Retourne l'objet Employe créé ou None en cas d'erreur.
        """
        try:
            cursor = db.execute(
                """INSERT INTO employes
                       (nom, prenom, telephone, email, departement, poste, date_embauche)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (nom, prenom, telephone, email, departement, poste, date_embauche)
            )
            employee_id = cursor.lastrowid

            # Générer un ID unique de données (utilisé comme clé unique d'identification)
            import uuid
            qr_data = f"EMP-{employee_id:04d}-{str(uuid.uuid4()).replace('-', '')[:8].upper()}"

            # Mettre à jour avec l'ID unique
            db.execute(
                "UPDATE employes SET qr_data = ?, qr_code_path = '' WHERE id = ?",
                (qr_data, employee_id)
            )

            # Historique
            db.execute(
                "INSERT INTO historique (type_action, employe_id, description) VALUES (?, ?, ?)",
                ("creation_employe", employee_id, f"Création employé : {prenom} {nom}")
            )
            return EmployeeService.get_by_id(employee_id)
        except Exception as e:
            print(f"[EmployeeService] Erreur création : {e}")
            return None

    @staticmethod
    def update(employee_id: int, nom: str, prenom: str, telephone: str,
               email: str, departement: str, poste: str, date_embauche: str) -> bool:
        """Met à jour les informations d'un employé."""
        try:
            db.execute(
                """UPDATE employes
                   SET nom=?, prenom=?, telephone=?, email=?,
                       departement=?, poste=?, date_embauche=?
                   WHERE id=?""",
                (nom, prenom, telephone, email, departement, poste, date_embauche, employee_id)
            )
            db.execute(
                "INSERT INTO historique (type_action, employe_id, description) VALUES (?, ?, ?)",
                ("modification_employe", employee_id, f"Modification employé ID {employee_id}")
            )
            return True
        except Exception as e:
            print(f"[EmployeeService] Erreur mise à jour : {e}")
            return False

    @staticmethod
    def delete(employee_id: int) -> bool:
        """Suppression logique d'un employé (actif = 0)."""
        try:
            emp = EmployeeService.get_by_id(employee_id)
            db.execute("UPDATE employes SET actif = 0 WHERE id = ?", (employee_id,))
            if emp:
                db.execute(
                    "INSERT INTO historique (type_action, employe_id, description) VALUES (?, ?, ?)",
                    ("suppression_employe", employee_id,
                     f"Suppression employé : {emp.prenom} {emp.nom}")
                )
            return True
        except Exception as e:
            print(f"[EmployeeService] Erreur suppression : {e}")
            return False

    @staticmethod
    def get_departments() -> List[str]:
        """Retourne la liste unique des départements."""
        rows = db.fetchall(
            "SELECT DISTINCT departement FROM employes WHERE actif=1 AND departement != '' ORDER BY departement"
        )
        return [r["departement"] for r in rows]

    @staticmethod
    def count() -> int:
        """Retourne le nombre d'employés actifs."""
        row = db.fetchone("SELECT COUNT(*) as total FROM employes WHERE actif=1")
        return row["total"] if row else 0

    @staticmethod
    def _row_to_model(row: dict) -> Employe:
        """Convertit une ligne de BDD en objet Employe."""
        return Employe(
            id=row["id"], nom=row["nom"], prenom=row["prenom"],
            telephone=row.get("telephone", ""), email=row.get("email", ""),
            departement=row.get("departement", ""), poste=row.get("poste", ""),
            date_embauche=row.get("date_embauche", ""),
            qr_code_path=row.get("qr_code_path", ""),
            qr_data=row.get("qr_data", ""),
            actif=row.get("actif", 1),
            date_creation=row.get("date_creation", "")
        )
