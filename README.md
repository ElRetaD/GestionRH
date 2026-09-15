# 📊 GestPrésences — Système de Gestion des Présences des Employés

Application desktop professionnelle développée en Python/PySide6 pour la gestion complète des présences des employés.

## 🚀 Lancement rapide

```bash
# 1. Installer les dépendances
pip install -r requirements.txt

# 2. Lancer l'application
python main.py
```

## 🔐 Comptes par défaut

| Rôle          | Nom d'utilisateur | Mot de passe |
|---------------|-------------------|--------------|
| Administrateur | `admin`          | `Admin@2024` |
| Agent          | `agent`          | `Agent@2024` |

> ⚠️ Changez les mots de passe après la première connexion !

## ✨ Fonctionnalités

### 👑 Administrateur
- **Tableau de bord** — KPIs en temps réel + 4 graphiques interactifs
- **Gestion des employés** — CRUD complet avec QR code automatique
- **Présences & Absences** — Consultation avec filtres avancés
- **Statistiques** — Graphiques détaillés par département/mois
- **Historique** — Journal complet de toutes les actions
- **Rapports** — Export Excel, CSV et PDF professionnels
- **IA intégrée** — Assistant conversationnel + détection d'anomalies
- **Gestion utilisateurs** — Création/modification des comptes

### 👤 Agent de Présence
- **Rechercher** un employé par nom ou QR code (lecteur USB)
- **Enregistrer** : Entrée, Sortie, Absence, Congé
- **Consulter** les présences du jour

## 🔲 Système QR Code

Chaque employé reçoit un QR code unique généré automatiquement à sa création.

- QR codes sauvegardés dans `assets/qrcodes/`
- Compatibles avec tous les lecteurs QR USB (fonctionnement clavier)
- Scanner le QR → dirigé vers la fiche complète de l'employé

## 🤖 Intelligence Artificielle (100% locale)

### Assistant conversationnel
Questions supportées :
- "Qui est absent aujourd'hui ?"
- "Qui est en retard cette semaine ?"
- "Quel employé a travaillé le plus d'heures ce mois ?"
- "Statistiques du département Informatique"
- "Bilan général"

### Détection d'anomalies
- Retards fréquents (seuil configurable)
- Absences répétées
- Départements à fort taux d'absence
- Employés inactifs prolongés

## 📁 Structure du projet

```
Gestion/
├── main.py                    # Point d'entrée
├── requirements.txt           # Dépendances
│
├── app/
│   ├── config.py              # Configuration (heure de travail, seuils IA)
│   ├── database/              # SQLite (connexion, schéma, données initiales)
│   ├── models/                # Dataclasses Python
│   ├── services/              # Logique métier
│   │   ├── auth_service.py    # Authentification bcrypt
│   │   ├── employee_service.py
│   │   ├── attendance_service.py
│   │   ├── qr_service.py      # Génération QR codes
│   │   ├── report_service.py  # Export Excel/CSV/PDF
│   │   └── ai_service.py      # IA locale
│   ├── views/admin/           # Vues administrateur
│   ├── views/agent/           # Vues agent
│   ├── widgets/               # Composants réutilisables
│   └── utils/theme.py         # Thème dark professionnel
│
├── assets/qrcodes/            # QR codes générés
├── exports/                   # Fichiers exportés
└── data/presences.db          # Base de données SQLite
```

## ⚙️ Configuration

Les paramètres sont configurables via l'interface admin :
- Heure officielle de début de travail
- Seuil de tolérance pour les retards
- Seuils d'alertes IA

Les paramètres sont sauvegardés dans `data/settings.json`.

## 📦 Dépendances

```
PySide6       — Interface graphique
pandas        — Traitement des données
openpyxl      — Export Excel
reportlab     — Export PDF
qrcode[pil]   — Génération QR codes
Pillow        — Traitement d'images
matplotlib    — Graphiques interactifs
bcrypt        — Hashage sécurisé des mots de passe
```

## 🛡️ Sécurité

- Mots de passe hashés avec **bcrypt** (jamais stockés en clair)
- Système de rôles strict (Admin / Agent)
- Historique complet de toutes les actions

---

Développé avec ❤️ par **RCA Systems** | v1.0.0
