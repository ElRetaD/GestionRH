"""
Service de gestion de la paie.
Salaires, primes, heures supplémentaires, déductions et calcul des bulletins.
"""
from __future__ import annotations

from calendar import monthrange
from datetime import datetime
from typing import List, Optional

from app.database.connection import db
from app.models.models import BulletinPaie, ElementPaie, SalaireEmploye
from app.services.auth_service import AuthService

HEURES_STANDARD_MOIS = 173.33
TAUX_HS_MAJORATION = 1.5


class PayrollService:
    """Service métier pour la paie des employés."""

    # ─── Salaires de base ─────────────────────────────────────────────────────

    @staticmethod
    def _default_taux_horaire(salaire_base: float) -> float:
        if salaire_base <= 0:
            return 0.0
        return round(salaire_base / HEURES_STANDARD_MOIS, 2)

    @staticmethod
    def get_salaire(employe_id: int) -> Optional[SalaireEmploye]:
        row = db.fetchone(
            """
            SELECT s.*, e.nom as employe_nom, e.prenom as employe_prenom,
                   e.departement, e.poste
            FROM salaires_employes s
            JOIN employes e ON e.id = s.employe_id
            WHERE s.employe_id = ?
            """,
            (employe_id,),
        )
        return PayrollService._row_to_salaire(row) if row else None

    @staticmethod
    def get_all_salaires() -> List[SalaireEmploye]:
        rows = db.fetchall(
            """
            SELECT e.id as employe_id, s.id, s.salaire_base, s.taux_horaire,
                   s.date_modification, e.nom as employe_nom, e.prenom as employe_prenom,
                   e.departement, e.poste
            FROM employes e
            LEFT JOIN salaires_employes s ON s.employe_id = e.id
            WHERE e.actif = 1
            ORDER BY e.nom, e.prenom
            """
        )
        result = []
        for r in rows:
            if r["id"]:
                result.append(PayrollService._row_to_salaire(r))
            else:
                result.append(SalaireEmploye(
                    id=0,
                    employe_id=r["employe_id"],
                    salaire_base=0.0,
                    taux_horaire=0.0,
                    employe_nom=r["employe_nom"],
                    employe_prenom=r["employe_prenom"],
                    departement=r["departement"] or "",
                    poste=r["poste"] or "",
                ))
        return result

    @staticmethod
    def set_salaire(employe_id: int, salaire_base: float,
                    taux_horaire: float | None = None) -> bool:
        try:
            base = max(0.0, float(salaire_base))
            taux = float(taux_horaire) if taux_horaire is not None else \
                PayrollService._default_taux_horaire(base)
            existing = db.fetchone(
                "SELECT id FROM salaires_employes WHERE employe_id = ?",
                (employe_id,),
            )
            if existing:
                db.execute(
                    """
                    UPDATE salaires_employes
                    SET salaire_base=?, taux_horaire=?,
                        date_modification=datetime('now', 'localtime')
                    WHERE employe_id=?
                    """,
                    (base, taux, employe_id),
                )
            else:
                db.execute(
                    """
                    INSERT INTO salaires_employes (employe_id, salaire_base, taux_horaire)
                    VALUES (?, ?, ?)
                    """,
                    (employe_id, base, taux),
                )
            return True
        except Exception:
            return False

    # ─── Éléments de paie mensuels ───────────────────────────────────────────

    @staticmethod
    def get_elements(employe_id: int, periode: str) -> List[ElementPaie]:
        rows = db.fetchall(
            """
            SELECT el.*, e.nom as employe_nom, e.prenom as employe_prenom
            FROM elements_paie el
            JOIN employes e ON e.id = el.employe_id
            WHERE el.employe_id = ? AND el.periode = ?
            ORDER BY el.type_element, el.libelle
            """,
            (employe_id, periode),
        )
        return [PayrollService._row_to_element(r) for r in rows]

    @staticmethod
    def add_element(employe_id: int, periode: str, type_element: str,
                    libelle: str, montant: float = 0, heures: float = 0,
                    taux: float = 0, notes: str = "") -> bool:
        try:
            montant_calc = PayrollService._calc_element_amount(
                employe_id, type_element, montant, heures, taux
            )
            db.execute(
                """
                INSERT INTO elements_paie
                    (employe_id, periode, type_element, libelle, montant, heures, taux, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (employe_id, periode, type_element, libelle,
                 montant_calc, heures, taux, notes),
            )
            return True
        except Exception:
            return False

    @staticmethod
    def update_element(element_id: int, libelle: str, montant: float = 0,
                       heures: float = 0, taux: float = 0, notes: str = "") -> bool:
        try:
            row = db.fetchone(
                "SELECT employe_id, type_element FROM elements_paie WHERE id = ?",
                (element_id,),
            )
            if not row:
                return False
            montant_calc = PayrollService._calc_element_amount(
                row["employe_id"], row["type_element"], montant, heures, taux
            )
            db.execute(
                """
                UPDATE elements_paie
                SET libelle=?, montant=?, heures=?, taux=?, notes=?
                WHERE id=?
                """,
                (libelle, montant_calc, heures, taux, notes, element_id),
            )
            return True
        except Exception:
            return False

    @staticmethod
    def delete_element(element_id: int) -> bool:
        try:
            db.execute("DELETE FROM elements_paie WHERE id = ?", (element_id,))
            return True
        except Exception:
            return False

    @staticmethod
    def _calc_element_amount(employe_id: int, type_element: str,
                             montant: float, heures: float, taux: float) -> float:
        if type_element == "heures_sup":
            salaire = PayrollService.get_salaire(employe_id)
            base_taux = taux or (salaire.taux_horaire if salaire else 0)
            effective = base_taux * TAUX_HS_MAJORATION if base_taux else 0
            return round(heures * effective, 2)
        return round(max(0.0, float(montant)), 2)

    # ─── Heures travaillées (depuis présences) ────────────────────────────────

    @staticmethod
    def get_heures_travaillees(employe_id: int, periode: str) -> float:
        debut, fin = PayrollService._periode_bounds(periode)
        row = db.fetchone(
            """
            SELECT COALESCE(SUM(heures_travaillees), 0) as total
            FROM presences
            WHERE employe_id = ? AND date >= ? AND date <= ?
              AND statut IN ('present', 'retard', 'teletravail')
            """,
            (employe_id, debut, fin),
        )
        return round(float(row["total"] or 0), 2) if row else 0.0

    # ─── Calcul bulletins ─────────────────────────────────────────────────────

    @staticmethod
    def calculate_bulletin(employe_id: int, periode: str) -> Optional[BulletinPaie]:
        salaire = PayrollService.get_salaire(employe_id)
        if not salaire or salaire.salaire_base <= 0:
            return None

        elements = PayrollService.get_elements(employe_id, periode)
        total_primes = sum(e.montant for e in elements if e.type_element == "prime")
        total_hs = sum(e.montant for e in elements if e.type_element == "heures_sup")
        total_ded = sum(e.montant for e in elements if e.type_element == "deduction")
        heures = PayrollService.get_heures_travaillees(employe_id, periode)

        brut = salaire.salaire_base + total_primes + total_hs
        net = max(0.0, brut - total_ded)

        user = AuthService.get_current_user()
        genere_par = user.id if user else None

        existing = db.fetchone(
            "SELECT id FROM bulletins_paie WHERE employe_id = ? AND periode = ?",
            (employe_id, periode),
        )
        if existing:
            db.execute(
                """
                UPDATE bulletins_paie
                SET salaire_base=?, total_primes=?, total_heures_sup=?,
                    total_deductions=?, heures_travaillees=?, salaire_brut=?,
                    salaire_net=?, genere_par=?, statut='valide',
                    date_calcul=datetime('now', 'localtime')
                WHERE id=?
                """,
                (salaire.salaire_base, total_primes, total_hs, total_ded,
                 heures, brut, net, genere_par, existing["id"]),
            )
            bulletin_id = existing["id"]
        else:
            cursor = db.execute(
                """
                INSERT INTO bulletins_paie
                    (employe_id, periode, salaire_base, total_primes, total_heures_sup,
                     total_deductions, heures_travaillees, salaire_brut, salaire_net,
                     genere_par, statut)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'valide')
                """,
                (employe_id, periode, salaire.salaire_base, total_primes, total_hs,
                 total_ded, heures, brut, net, genere_par),
            )
            bulletin_id = cursor.lastrowid

        return PayrollService.get_bulletin_by_id(bulletin_id)

    @staticmethod
    def calculate_all(periode: str) -> tuple[int, int]:
        """Calcule tous les bulletins. Retourne (succès, échecs)."""
        salaires = PayrollService.get_all_salaires()
        ok, fail = 0, 0
        for s in salaires:
            if s.salaire_base <= 0:
                fail += 1
                continue
            if PayrollService.calculate_bulletin(s.employe_id, periode):
                ok += 1
            else:
                fail += 1
        return ok, fail

    @staticmethod
    def get_bulletin_by_id(bulletin_id: int) -> Optional[BulletinPaie]:
        row = db.fetchone(
            """
            SELECT b.*, e.nom as employe_nom, e.prenom as employe_prenom,
                   e.departement, e.poste
            FROM bulletins_paie b
            JOIN employes e ON e.id = b.employe_id
            WHERE b.id = ?
            """,
            (bulletin_id,),
        )
        return PayrollService._row_to_bulletin(row) if row else None

    @staticmethod
    def get_bulletins(periode: str | None = None) -> List[BulletinPaie]:
        query = """
            SELECT b.*, e.nom as employe_nom, e.prenom as employe_prenom,
                   e.departement, e.poste
            FROM bulletins_paie b
            JOIN employes e ON e.id = b.employe_id
            WHERE 1=1
        """
        params: list = []
        if periode:
            query += " AND b.periode = ?"
            params.append(periode)
        query += " ORDER BY b.periode DESC, e.nom, e.prenom"
        rows = db.fetchall(query, tuple(params))
        return [PayrollService._row_to_bulletin(r) for r in rows]

    @staticmethod
    def update_pdf_path(bulletin_id: int, pdf_path: str):
        db.execute(
            "UPDATE bulletins_paie SET pdf_path = ? WHERE id = ?",
            (pdf_path, bulletin_id),
        )

    @staticmethod
    def get_dashboard_stats(periode: str | None = None) -> dict:
        periode = periode or datetime.now().strftime("%Y-%m")
        salaires = PayrollService.get_all_salaires()
        avec_salaire = sum(1 for s in salaires if s.salaire_base > 0)
        bulletins = PayrollService.get_bulletins(periode)
        masse = sum(b.salaire_net for b in bulletins)
        return {
            "periode": periode,
            "total_employes": len(salaires),
            "avec_salaire": avec_salaire,
            "sans_salaire": len(salaires) - avec_salaire,
            "bulletins_mois": len(bulletins),
            "masse_salariale": round(masse, 2),
        }

    @staticmethod
    def preview_calculation(employe_id: int, periode: str) -> dict:
        salaire = PayrollService.get_salaire(employe_id)
        base = salaire.salaire_base if salaire else 0.0
        elements = PayrollService.get_elements(employe_id, periode)
        total_primes = sum(e.montant for e in elements if e.type_element == "prime")
        total_hs = sum(e.montant for e in elements if e.type_element == "heures_sup")
        total_ded = sum(e.montant for e in elements if e.type_element == "deduction")
        heures = PayrollService.get_heures_travaillees(employe_id, periode)
        brut = base + total_primes + total_hs
        net = max(0.0, brut - total_ded)
        return {
            "salaire_base": base,
            "total_primes": total_primes,
            "total_heures_sup": total_hs,
            "total_deductions": total_ded,
            "heures_travaillees": heures,
            "salaire_brut": round(brut, 2),
            "salaire_net": round(net, 2),
        }

    @staticmethod
    def _periode_bounds(periode: str) -> tuple[str, str]:
        year, month = map(int, periode.split("-"))
        last_day = monthrange(year, month)[1]
        return f"{periode}-01", f"{periode}-{last_day:02d}"

    @staticmethod
    def _row_to_salaire(row) -> SalaireEmploye:
        return SalaireEmploye(
            id=row["id"] or 0,
            employe_id=row["employe_id"],
            salaire_base=float(row["salaire_base"] or 0),
            taux_horaire=float(row["taux_horaire"] or 0),
            date_modification=row.get("date_modification") or "",
            employe_nom=row.get("employe_nom") or "",
            employe_prenom=row.get("employe_prenom") or "",
            departement=row.get("departement") or "",
            poste=row.get("poste") or "",
        )

    @staticmethod
    def _row_to_element(row) -> ElementPaie:
        return ElementPaie(
            id=row["id"],
            employe_id=row["employe_id"],
            periode=row["periode"],
            type_element=row["type_element"],
            libelle=row["libelle"],
            montant=float(row["montant"] or 0),
            heures=float(row["heures"] or 0),
            taux=float(row["taux"] or 0),
            notes=row.get("notes") or "",
            date_creation=row.get("date_creation") or "",
            employe_nom=row.get("employe_nom") or "",
            employe_prenom=row.get("employe_prenom") or "",
        )

    @staticmethod
    def _row_to_bulletin(row) -> BulletinPaie:
        return BulletinPaie(
            id=row["id"],
            employe_id=row["employe_id"],
            periode=row["periode"],
            salaire_base=float(row["salaire_base"] or 0),
            total_primes=float(row["total_primes"] or 0),
            total_heures_sup=float(row["total_heures_sup"] or 0),
            total_deductions=float(row["total_deductions"] or 0),
            heures_travaillees=float(row["heures_travaillees"] or 0),
            salaire_brut=float(row["salaire_brut"] or 0),
            salaire_net=float(row["salaire_net"] or 0),
            pdf_path=row.get("pdf_path") or "",
            statut=row.get("statut") or "brouillon",
            genere_par=row.get("genere_par"),
            date_calcul=row.get("date_calcul") or "",
            employe_nom=row.get("employe_nom") or "",
            employe_prenom=row.get("employe_prenom") or "",
            departement=row.get("departement") or "",
            poste=row.get("poste") or "",
        )
