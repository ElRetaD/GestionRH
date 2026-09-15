"""
Configuration globale de l'application.
Toutes les constantes et paramètres par défaut sont définis ici.
"""
import os
import json

# ─── Chemins de base ───────────────────────────────────────────────────────────
BASE_DIR    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR    = os.path.join(BASE_DIR, "data")
DB_PATH     = os.path.join(DATA_DIR, "presences.db")
QR_DIR      = os.path.join(BASE_DIR, "assets", "qrcodes")
EXPORT_DIR  = os.path.join(BASE_DIR, "exports")
ASSETS_DIR  = os.path.join(BASE_DIR, "assets")
SETTINGS_PATH = os.path.join(DATA_DIR, "settings.json")

# Créer les répertoires s'ils n'existent pas
for directory in [DATA_DIR, QR_DIR, EXPORT_DIR, ASSETS_DIR]:
    os.makedirs(directory, exist_ok=True)

# ─── Informations de l'application ─────────────────────────────────────────────
APP_NAME    = "GestRH — Gestion des Ressources Humaines"
APP_VERSION = "1.0.0"
APP_AUTHOR  = "RCA Systems"

# ─── Paramètres par défaut (écrasables via l'interface admin) ──────────────────
DEFAULT_SETTINGS = {
    "heure_debut_travail":    "08:00",
    "heure_fin_travail":      "17:00",
    "nom_entreprise":         "Mon Entreprise",
    "seuil_retard_minutes":   5,      # tolérance avant de marquer retard
    "seuil_alertes_retards":  5,      # nb retards/mois → alerte
    "seuil_alertes_absences": 3,      # nb absences/mois → alerte
    "langue":                 "fr",
}


def load_settings() -> dict:
    """Charge les paramètres depuis le fichier JSON (ou retourne les défauts)."""
    if os.path.exists(SETTINGS_PATH):
        try:
            with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
                saved = json.load(f)
                # Fusionner avec les défauts pour les clés manquantes
                merged = DEFAULT_SETTINGS.copy()
                merged.update(saved)
                return merged
        except (json.JSONDecodeError, IOError):
            pass
    return DEFAULT_SETTINGS.copy()


def save_settings(settings: dict) -> None:
    """Sauvegarde les paramètres dans le fichier JSON."""
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)


# Charger les paramètres au démarrage
SETTINGS = load_settings()
