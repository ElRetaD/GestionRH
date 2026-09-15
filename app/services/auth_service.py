"""
Service d'authentification.
Gère la connexion, la vérification des mots de passe et la session utilisateur.
"""
import bcrypt
from typing import Optional
from app.database.connection import db
from app.models.models import Utilisateur


class AuthService:
    """Service pour l'authentification et la gestion des sessions."""

    _current_user: Optional[Utilisateur] = None

    @classmethod
    def login(cls, nom_utilisateur: str, mot_de_passe: str) -> Optional[Utilisateur]:
        """
        Authentifie un utilisateur.
        Retourne l'objet Utilisateur si succès, None sinon.
        """
        row = db.fetchone(
            "SELECT * FROM utilisateurs WHERE nom_utilisateur = ? AND actif = 1",
            (nom_utilisateur,)
        )
        if not row:
            return None

        # Vérifier le mot de passe avec bcrypt
        if not bcrypt.checkpw(mot_de_passe.encode("utf-8"), row["mot_de_passe"].encode("utf-8")):
            return None

        user = Utilisateur(
            id=row["id"],
            nom_utilisateur=row["nom_utilisateur"],
            role=row["role"],
            nom_complet=row["nom_complet"],
            email=row["email"],
            actif=row["actif"],
            date_creation=row["date_creation"],
        )
        cls._current_user = user

        # Enregistrer dans l'historique
        db.execute(
            "INSERT INTO historique (type_action, utilisateur_id, description) VALUES (?, ?, ?)",
            ("connexion", user.id, f"Connexion de {user.nom_complet} ({user.role})")
        )
        return user

    @classmethod
    def logout(cls):
        """Déconnecte l'utilisateur courant."""
        if cls._current_user:
            db.execute(
                "INSERT INTO historique (type_action, utilisateur_id, description) VALUES (?, ?, ?)",
                ("deconnexion", cls._current_user.id,
                 f"Déconnexion de {cls._current_user.nom_complet}")
            )
        cls._current_user = None

    @classmethod
    def get_current_user(cls) -> Optional[Utilisateur]:
        """Retourne l'utilisateur actuellement connecté."""
        return cls._current_user

    @classmethod
    def is_admin(cls) -> bool:
        """Vérifie si l'utilisateur connecté est administrateur."""
        return cls._current_user is not None and cls._current_user.role == "admin"

    @classmethod
    def is_comptable(cls) -> bool:
        """Vérifie si l'utilisateur connecté est comptable."""
        return cls._current_user is not None and cls._current_user.role == "comptable"

    # ─── Gestion des comptes ───────────────────────────────────────────────────

    @classmethod
    def get_all_users(cls) -> list:
        """Retourne tous les utilisateurs."""
        rows = db.fetchall("SELECT * FROM utilisateurs ORDER BY nom_complet")
        return [Utilisateur(
            id=r["id"], nom_utilisateur=r["nom_utilisateur"], role=r["role"],
            nom_complet=r["nom_complet"], email=r["email"],
            actif=r["actif"], date_creation=r["date_creation"]
        ) for r in rows]

    @classmethod
    def create_user(cls, nom_utilisateur: str, mot_de_passe: str,
                    role: str, nom_complet: str, email: str) -> bool:
        """Crée un nouveau compte utilisateur."""
        try:
            password_hash = bcrypt.hashpw(
                mot_de_passe.encode("utf-8"), bcrypt.gensalt()
            ).decode("utf-8")
            db.execute(
                """INSERT INTO utilisateurs (nom_utilisateur, mot_de_passe, role, nom_complet, email)
                   VALUES (?, ?, ?, ?, ?)""",
                (nom_utilisateur, password_hash, role, nom_complet, email)
            )
            return True
        except Exception:
            return False

    @classmethod
    def update_user(cls, user_id: int, nom_complet: str, email: str,
                    role: str, actif: int, nouveau_mot_de_passe: str = "") -> bool:
        """Met à jour un compte utilisateur."""
        try:
            if nouveau_mot_de_passe:
                password_hash = bcrypt.hashpw(
                    nouveau_mot_de_passe.encode("utf-8"), bcrypt.gensalt()
                ).decode("utf-8")
                db.execute(
                    """UPDATE utilisateurs
                       SET nom_complet=?, email=?, role=?, actif=?, mot_de_passe=?
                       WHERE id=?""",
                    (nom_complet, email, role, actif, password_hash, user_id)
                )
            else:
                db.execute(
                    "UPDATE utilisateurs SET nom_complet=?, email=?, role=?, actif=? WHERE id=?",
                    (nom_complet, email, role, actif, user_id)
                )
            return True
        except Exception:
            return False

    @classmethod
    def delete_user(cls, user_id: int) -> bool:
        """Supprime un compte utilisateur (ne peut pas supprimer son propre compte)."""
        if cls._current_user and cls._current_user.id == user_id:
            return False
        try:
            db.execute("DELETE FROM utilisateurs WHERE id = ?", (user_id,))
            return True
        except Exception:
            return False

    @classmethod
    def change_password(cls, user_id: int, old_password: str, new_password: str) -> bool:
        """Change le mot de passe après vérification de l'ancien."""
        row = db.fetchone("SELECT mot_de_passe FROM utilisateurs WHERE id = ?", (user_id,))
        if not row:
            return False
        if not bcrypt.checkpw(old_password.encode("utf-8"), row["mot_de_passe"].encode("utf-8")):
            return False
        new_hash = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        db.execute("UPDATE utilisateurs SET mot_de_passe = ? WHERE id = ?", (new_hash, user_id))
        return True
