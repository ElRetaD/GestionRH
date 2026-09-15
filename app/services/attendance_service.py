"""
Service de gestion des présences.
Enregistrement entrée/sortie, calcul des heures travaillées, détection des retards.
"""
from datetime import datetime, date, timedelta
from typing import Optional, List
from app.database.connection import db
from app.models.models import Presence, StatsDashboard
from app.config import load_settings


class AttendanceService:
    """Service pour les présences, absences et retards."""

    # ─── Enregistrement ────────────────────────────────────────────────────────

    @staticmethod
    def record_entry(employee_id: int, agent_id: int,
                     entry_time: str = None) -> dict:
        """
        Enregistre l'heure d'entrée d'un employé.
        La sortie est fixée AUTOMATIQUEMENT à l'heure de fin de travail configurée.
        Calcule automatiquement le retard et les heures travaillées.
        """
        settings = load_settings()
        today = date.today().isoformat()
        now = entry_time or datetime.now().strftime("%H:%M")

        # Heure officielle de début et fin de travail
        official_start = settings.get("heure_debut_travail", "08:00")
        official_end   = settings.get("heure_fin_travail",   "18:00")
        tolerance      = settings.get("seuil_retard_minutes", 5)

        # Calcul du retard
        is_late, late_minutes = AttendanceService._calculate_late(
            now, official_start, tolerance
        )

        # Calcul automatique des heures travaillées (entrée réelle → heure fin officielle)
        hours_worked = AttendanceService._calc_hours(now, official_end)

        # Vérifier si une présence existe déjà pour aujourd'hui
        existing = db.fetchone(
            "SELECT * FROM presences WHERE employe_id=? AND date=?",
            (employee_id, today)
        )

        if existing:
            # Mise à jour si déjà existant (re-scan entrée)
            db.execute(
                """UPDATE presences
                   SET heure_entree=?, heure_sortie=?, heures_travaillees=?,
                       statut='present', retard=?, minutes_retard=?, enregistre_par=?
                   WHERE employe_id=? AND date=?""",
                (now, official_end, hours_worked,
                 1 if is_late else 0, late_minutes, agent_id,
                 employee_id, today)
            )
        else:
            db.execute(
                """INSERT INTO presences
                       (employe_id, date, heure_entree, heure_sortie, heures_travaillees,
                        statut, retard, minutes_retard, enregistre_par)
                   VALUES (?, ?, ?, ?, ?, 'present', ?, ?, ?)""",
                (employee_id, today, now, official_end, hours_worked,
                 1 if is_late else 0, late_minutes, agent_id)
            )

        # Enregistrer dans la table retards si retard
        if is_late:
            existing_late = db.fetchone(
                "SELECT id FROM retards WHERE employe_id=? AND date=?",
                (employee_id, today)
            )
            if not existing_late:
                db.execute(
                    """INSERT INTO retards (employe_id, date, heure_arrivee, heure_officielle, minutes_retard)
                       VALUES (?, ?, ?, ?, ?)""",
                    (employee_id, today, now, official_start, late_minutes)
                )

        # Historique avec entrée + sortie automatique
        msg = f"Entrée à {now} | Sortie automatique à {official_end} | {hours_worked:.1f}h travaillées"
        if is_late:
            msg += f" | Retard de {late_minutes} min"
        db.execute(
            "INSERT INTO historique (type_action, employe_id, utilisateur_id, description) VALUES (?,?,?,?)",
            ("entree", employee_id, agent_id, msg)
        )

        return {
            "success":      True,
            "is_late":      is_late,
            "late_minutes": late_minutes,
            "time":         now,
            "exit_time":    official_end,
            "hours_worked": hours_worked,
        }

    @staticmethod
    def record_exit(employee_id: int, agent_id: int, exit_time: str = None) -> dict:
        """Enregistre l'heure de sortie et calcule les heures travaillées."""
        today = date.today().isoformat()
        now = exit_time or datetime.now().strftime("%H:%M")

        presence = db.fetchone(
            "SELECT * FROM presences WHERE employe_id=? AND date=?",
            (employee_id, today)
        )

        hours_worked = 0.0
        if presence and presence.get("heure_entree"):
            hours_worked = AttendanceService._calc_hours(
                presence["heure_entree"], now
            )

        if presence:
            db.execute(
                """UPDATE presences
                   SET heure_sortie=?, heures_travaillees=?, enregistre_par=?
                   WHERE employe_id=? AND date=?""",
                (now, hours_worked, agent_id, employee_id, today)
            )
        else:
            db.execute(
                """INSERT INTO presences
                       (employe_id, date, heure_sortie, heures_travaillees, statut, enregistre_par)
                   VALUES (?, ?, ?, ?, 'present', ?)""",
                (employee_id, today, now, hours_worked, agent_id)
            )

        db.execute(
            "INSERT INTO historique (type_action, employe_id, utilisateur_id, description) VALUES (?,?,?,?)",
            ("sortie", employee_id, agent_id,
             f"Sortie à {now} — {hours_worked:.1f}h travaillées")
        )
        return {"success": True, "hours_worked": hours_worked, "time": now}

    @staticmethod
    def record_absence(employee_id: int, agent_id: int,
                       absence_type: str, motif: str = "", date_str: str = None) -> bool:
        """Enregistre une absence, congé ou maladie."""
        target_date = date_str or date.today().isoformat()
        try:
            # Upsert dans presences
            existing = db.fetchone(
                "SELECT id FROM presences WHERE employe_id=? AND date=?",
                (employee_id, target_date)
            )
            if existing:
                db.execute(
                    "UPDATE presences SET statut=?, enregistre_par=? WHERE employe_id=? AND date=?",
                    (absence_type, agent_id, employee_id, target_date)
                )
            else:
                db.execute(
                    """INSERT INTO presences (employe_id, date, statut, enregistre_par)
                       VALUES (?, ?, ?, ?)""",
                    (employee_id, target_date, absence_type, agent_id)
                )

            # Insérer dans la table absences
            existing_abs = db.fetchone(
                "SELECT id FROM absences WHERE employe_id=? AND date=?",
                (employee_id, target_date)
            )
            if existing_abs:
                db.execute(
                    "UPDATE absences SET type_absence=?, motif=?, enregistre_par=? WHERE employe_id=? AND date=?",
                    (absence_type, motif, agent_id, employee_id, target_date)
                )
            else:
                db.execute(
                    """INSERT INTO absences (employe_id, date, type_absence, motif, enregistre_par)
                       VALUES (?, ?, ?, ?, ?)""",
                    (employee_id, target_date, absence_type, motif, agent_id)
                )

            db.execute(
                "INSERT INTO historique (type_action, employe_id, utilisateur_id, description) VALUES (?,?,?,?)",
                (absence_type, employee_id, agent_id,
                 f"Absence enregistrée : {absence_type} le {target_date}")
            )
            return True
        except Exception as e:
            print(f"[AttendanceService] Erreur absence : {e}")
            return False

    @staticmethod
    def update_record(presence_id: int, statut: str, heure_entree: str, notes: str) -> bool:
        """Met à jour un pointage existant."""
        try:
            db.execute(
                "UPDATE presences SET statut=?, heure_entree=?, notes=? WHERE id=?",
                (statut, heure_entree, notes, presence_id)
            )
            return True
        except Exception as e:
            print(f"[AttendanceService] Erreur update_record : {e}")
            return False

    # ─── Consultation ─────────────────────────────────────────────────────────

    @staticmethod
    def get_today_stats() -> StatsDashboard:
        """Retourne les statistiques du tableau de bord pour aujourd'hui."""
        today = date.today().isoformat()
        total = db.fetchone("SELECT COUNT(*) as c FROM employes WHERE actif=1")
        presents = db.fetchone(
            "SELECT COUNT(*) as c FROM presences WHERE date=? AND statut='present'", (today,)
        )
        absents = db.fetchone(
            "SELECT COUNT(*) as c FROM presences WHERE date=? AND statut='absent'", (today,)
        )
        conges = db.fetchone(
            "SELECT COUNT(*) as c FROM presences WHERE date=? AND statut IN ('conge','maladie')", (today,)
        )
        retards = db.fetchone(
            "SELECT COUNT(*) as c FROM presences WHERE date=? AND retard=1", (today,)
        )
        heures = db.fetchone(
            "SELECT COALESCE(SUM(heures_travaillees),0) as total FROM presences WHERE date=?", (today,)
        )
        return StatsDashboard(
            total_employes=total["c"] if total else 0,
            presents_aujourd_hui=presents["c"] if presents else 0,
            absents_aujourd_hui=absents["c"] if absents else 0,
            conges_aujourd_hui=conges["c"] if conges else 0,
            retards_aujourd_hui=retards["c"] if retards else 0,
            heures_travaillees_aujourd_hui=heures["total"] if heures else 0.0,
        )

    @staticmethod
    def get_presences(date_debut: str = None, date_fin: str = None,
                      employe_id: int = None, departement: str = None,
                      statut: str = None) -> List[Presence]:
        """Retourne les présences avec filtres optionnels."""
        conditions = []
        params = []
        query = """
            SELECT p.*, e.nom, e.prenom, e.departement
            FROM presences p
            JOIN employes e ON e.id = p.employe_id
            WHERE 1=1
        """
        if date_debut:
            conditions.append("p.date >= ?")
            params.append(date_debut)
        if date_fin:
            conditions.append("p.date <= ?")
            params.append(date_fin)
        if employe_id:
            conditions.append("p.employe_id = ?")
            params.append(employe_id)
        if departement:
            conditions.append("e.departement = ?")
            params.append(departement)
        if statut:
            conditions.append("p.statut = ?")
            params.append(statut)

        if conditions:
            query += " AND " + " AND ".join(conditions)
        query += " ORDER BY p.date DESC, e.nom"

        rows = db.fetchall(query, tuple(params))
        result = []
        for r in rows:
            p = Presence(
                id=r["id"], employe_id=r["employe_id"], date=r["date"],
                heure_entree=r.get("heure_entree", ""),
                heure_sortie=r.get("heure_sortie", ""),
                heures_travaillees=r.get("heures_travaillees", 0.0),
                statut=r.get("statut", "present"),
                retard=r.get("retard", 0),
                minutes_retard=r.get("minutes_retard", 0),
                enregistre_par=r.get("enregistre_par"),
                notes=r.get("notes", ""),
                date_creation=r.get("date_creation", ""),
                employe_nom=r.get("nom", ""),
                employe_prenom=r.get("prenom", ""),
                departement=r.get("departement", ""),
            )
            result.append(p)
        return result

    @staticmethod
    def get_monthly_chart_data(year: int = None, month: int = None) -> dict:
        """Retourne les données pour les graphiques mensuels."""
        if not year:
            year = datetime.now().year
        period = f"{year:04d}"

        rows = db.fetchall(
            """
            SELECT
                strftime('%m', date) as mois,
                COUNT(*) FILTER(WHERE statut='present') as presents,
                COUNT(*) FILTER(WHERE statut='absent')  as absents,
                COUNT(*) FILTER(WHERE statut IN ('conge','maladie')) as conges,
                COUNT(*) FILTER(WHERE retard=1)          as retards,
                COALESCE(SUM(heures_travaillees),0)      as heures
            FROM presences
            WHERE strftime('%Y', date)=?
            GROUP BY mois
            ORDER BY mois
            """,
            (str(year),)
        )
        mois_labels = ["Jan", "Fév", "Mar", "Avr", "Mai", "Jun",
                       "Jul", "Aoû", "Sep", "Oct", "Nov", "Déc"]
        presents = [0] * 12
        absents  = [0] * 12
        conges   = [0] * 12
        retards  = [0] * 12
        heures   = [0.0] * 12
        for r in rows:
            idx = int(r["mois"]) - 1
            presents[idx] = r["presents"]
            absents[idx]  = r["absents"]
            conges[idx]   = r["conges"]
            retards[idx]  = r["retards"]
            heures[idx]   = r["heures"]
        return {
            "labels": mois_labels, "presents": presents, "absents": absents,
            "conges": conges, "retards": retards, "heures": heures
        }

    @staticmethod
    def get_department_hours() -> dict:
        """Retourne les heures travaillées par département (30 derniers jours)."""
        rows = db.fetchall(
            """
            SELECT e.departement, COALESCE(SUM(p.heures_travaillees),0) as total_heures
            FROM employes e
            LEFT JOIN presences p ON p.employe_id=e.id
                AND p.date >= date('now', '-30 days')
            WHERE e.actif=1 AND e.departement != ''
            GROUP BY e.departement
            ORDER BY total_heures DESC
            """
        )
        return {
            "labels": [r["departement"] for r in rows],
            "heures": [r["total_heures"] for r in rows]
        }

    @staticmethod
    def get_presences_by_date(target_date: str = None) -> List[dict]:
        """Retourne les présences d'une date donnée avec infos employé."""
        if not target_date:
            target_date = date.today().isoformat()
        return db.fetchall(
            """
            SELECT p.*, e.nom, e.prenom, e.departement, e.poste
            FROM presences p
            JOIN employes e ON e.id=p.employe_id
            WHERE p.date=?
            ORDER BY e.nom
            """,
            (target_date,)
        )

    @staticmethod
    def get_history(date_debut: str = None, date_fin: str = None,
                    employe_id: int = None, departement: str = None) -> List[dict]:
        """Retourne l'historique complet avec filtres."""
        query = """
            SELECT h.*, e.nom, e.prenom, e.departement, u.nom_complet as agent_nom
            FROM historique h
            LEFT JOIN employes e ON e.id=h.employe_id
            LEFT JOIN utilisateurs u ON u.id=h.utilisateur_id
            WHERE 1=1
        """
        params = []
        if date_debut:
            query += " AND h.timestamp >= ?"
            params.append(date_debut)
        if date_fin:
            query += " AND h.timestamp <= ?"
            params.append(date_fin + " 23:59:59")
        if employe_id:
            query += " AND h.employe_id = ?"
            params.append(employe_id)
        if departement:
            query += " AND e.departement = ?"
            params.append(departement)
        query += " ORDER BY h.timestamp DESC LIMIT 500"
        return db.fetchall(query, tuple(params))

    @staticmethod
    def get_live_presence_status() -> List[dict]:
        """Retourne la liste des employés actifs et leur dernier statut de pointage aujourd'hui."""
        return db.fetchall(
            """
            SELECT e.id, e.nom, e.prenom, e.departement, e.poste,
                   p.statut as current_status, p.heure_entree, p.heure_sortie,
                   (SELECT type_action FROM historique 
                    WHERE employe_id = e.id AND date(timestamp) = date('now') 
                    ORDER BY timestamp DESC LIMIT 1) as last_action
            FROM employes e
            LEFT JOIN presences p ON p.employe_id = e.id AND p.date = date('now')
            WHERE e.actif = 1
            ORDER BY e.nom, e.prenom
            """
        )

    # ─── Utilitaires ──────────────────────────────────────────────────────────

    @staticmethod
    def _calculate_late(arrival: str, official: str, tolerance: int) -> tuple:
        """Calcule si un employé est en retard et de combien de minutes."""
        try:
            arr = datetime.strptime(arrival, "%H:%M")
            off = datetime.strptime(official, "%H:%M")
            diff = (arr - off).total_seconds() / 60
            if diff > tolerance:
                return True, int(diff)
        except ValueError:
            pass
        return False, 0

    @staticmethod
    def _calc_hours(entry: str, exit_: str) -> float:
        """Calcule les heures travaillées entre deux horaires HH:MM."""
        try:
            fmt = "%H:%M"
            e = datetime.strptime(entry,  fmt)
            s = datetime.strptime(exit_,  fmt)
            if s < e:
                s += timedelta(days=1)
            return round((s - e).total_seconds() / 3600, 2)
        except ValueError:
            return 0.0
