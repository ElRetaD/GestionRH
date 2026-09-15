# 📊 GestRH — Système de Gestion des Ressources Humaines

Application desktop professionnelle développée en **Python / PySide6** pour la gestion intégrée des ressources humaines : employés, présences, absences, paie et rapports.

## 🚀 Lancement rapide

```bash
# 1. Installer les dépendances
pip install -r requirements.txt

# 2. Lancer l'application
python main.py
```

## 🔐 Comptes par défaut

| Rôle           | Nom d'utilisateur | Mot de passe    |
|----------------|-------------------|-----------------|
| Administrateur | `admin`           | `Admin@2024`    |
| Agent          | `agent`           | `Agent@2024`    |
| Comptable      | `comptable`       | `Comptable@2024`|

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

### 💰 Comptable
- **Tableau de bord financier** — Vue d'ensemble des salaires et charges
- **Gestion des salaires** — Configuration des salaires de base et taux horaires
- **Bulletins de paie** — Génération et export des fiches de paie PDF
- **Masse salariale** — Suivi des primes, déductions et heures supplémentaires

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
GestRH/
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
│   │   ├── payroll_service.py # Gestion de la paie
│   │   ├── payslip_pdf_service.py # Génération fiches de paie PDF
│   │   ├── qr_service.py      # Génération QR codes
│   │   ├── report_service.py  # Export Excel/CSV/PDF
│   │   └── ai_service.py      # IA locale
│   ├── views/admin/           # Vues administrateur
│   ├── views/agent/           # Vues agent
│   ├── views/comptable/       # Vues comptable
│   ├── widgets/               # Composants réutilisables
│   └── utils/theme.py         # Thème dark professionnel
│
├── assets/qrcodes/            # QR codes générés
├── exports/                   # Fichiers exportés (rapports, fiches de paie)
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
- Système de rôles strict (Admin / Agent / Comptable)
- Historique complet de toutes les actions

---

Développé avec ❤️ par **RCA Systems** | v1.0.0
