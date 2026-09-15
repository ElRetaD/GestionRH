"""
Dataclasses représentant les entités métier de l'application.
Ces modèles sont utilisés pour le transport de données entre les couches.
"""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Utilisateur:
    id: int
    nom_utilisateur: str
    role: str                    # 'admin', 'agent' ou 'comptable'
    nom_complet: str = ""
    email: str = ""
    actif: int = 1
    date_creation: str = ""
    # Le mot de passe n'est JAMAIS inclus dans ce dataclass


@dataclass
class Employe:
    id: int
    nom: str
    prenom: str
    telephone: str = ""
    email: str = ""
    departement: str = ""
    poste: str = ""
    date_embauche: str = ""
    qr_code_path: str = ""
    qr_data: str = ""
    actif: int = 1
    date_creation: str = ""

    @property
    def nom_complet(self) -> str:
        return f"{self.prenom} {self.nom}"


@dataclass
class Presence:
    id: int
    employe_id: int
    date: str
    heure_entree: str = ""
    heure_sortie: str = ""
    heures_travaillees: float = 0.0
    statut: str = "present"
    retard: int = 0
    minutes_retard: int = 0
    enregistre_par: Optional[int] = None
    notes: str = ""
    date_creation: str = ""
    # Champs joints (non stockés directement)
    employe_nom: str = ""
    employe_prenom: str = ""
    departement: str = ""


@dataclass
class Absence:
    id: int
    employe_id: int
    date: str
    type_absence: str            # 'absent', 'conge', 'maladie'
    motif: str = ""
    justifiee: int = 0
    enregistre_par: Optional[int] = None
    date_creation: str = ""
    # Champs joints
    employe_nom: str = ""
    employe_prenom: str = ""
    departement: str = ""


@dataclass
class Retard:
    id: int
    employe_id: int
    date: str
    heure_arrivee: str
    heure_officielle: str
    minutes_retard: int
    date_creation: str = ""
    # Champs joints
    employe_nom: str = ""
    employe_prenom: str = ""
    departement: str = ""


@dataclass
class SalaireEmploye:
    id: int
    employe_id: int
    salaire_base: float = 0.0
    taux_horaire: float = 0.0
    date_modification: str = ""
    employe_nom: str = ""
    employe_prenom: str = ""
    departement: str = ""
    poste: str = ""

    @property
    def nom_complet(self) -> str:
        return f"{self.employe_prenom} {self.employe_nom}"


@dataclass
class ElementPaie:
    id: int
    employe_id: int
    periode: str
    type_element: str          # 'prime', 'heures_sup', 'deduction'
    libelle: str
    montant: float = 0.0
    heures: float = 0.0
    taux: float = 0.0
    notes: str = ""
    date_creation: str = ""
    employe_nom: str = ""
    employe_prenom: str = ""


@dataclass
class BulletinPaie:
    id: int
    employe_id: int
    periode: str
    salaire_base: float = 0.0
    total_primes: float = 0.0
    total_heures_sup: float = 0.0
    total_deductions: float = 0.0
    heures_travaillees: float = 0.0
    salaire_brut: float = 0.0
    salaire_net: float = 0.0
    pdf_path: str = ""
    statut: str = "brouillon"
    genere_par: Optional[int] = None
    date_calcul: str = ""
    employe_nom: str = ""
    employe_prenom: str = ""
    departement: str = ""
    poste: str = ""

    @property
    def nom_complet(self) -> str:
        return f"{self.employe_prenom} {self.employe_nom}"


@dataclass
class StatsDashboard:
    """Agrégation des statistiques pour le tableau de bord."""
    total_employes: int = 0
    presents_aujourd_hui: int = 0
    absents_aujourd_hui: int = 0
    conges_aujourd_hui: int = 0
    retards_aujourd_hui: int = 0
    heures_travaillees_aujourd_hui: float = 0.0
