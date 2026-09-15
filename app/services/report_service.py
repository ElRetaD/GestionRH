"""
Service d'export des données : Excel, CSV et PDF.
Génère des rapports professionnels avec mise en forme complète.
"""
import os
import pandas as pd
from datetime import datetime
from app.config import EXPORT_DIR
from app.database.connection import db


class ReportService:
    """Service d'exportation des données en Excel, CSV et PDF."""

    # ─── Préparation des données ───────────────────────────────────────────────

    @staticmethod
    def _get_attendance_data(date_debut: str = None, date_fin: str = None,
                             employe_id: int = None, departement: str = None) -> pd.DataFrame:
        query = """
            SELECT
                e.id as "ID Employé",
                e.prenom || ' ' || e.nom as "Nom Complet",
                e.departement as "Département",
                e.poste as "Poste",
                p.date as "Date",
                p.heure_entree as "Heure Entrée",
                p.heure_sortie as "Heure Sortie",
                ROUND(p.heures_travaillees, 2) as "Heures Travaillées",
                CASE p.statut
                    WHEN 'present' THEN 'Présent'
                    WHEN 'absent'  THEN 'Absent'
                    WHEN 'conge'   THEN 'Congé'
                    WHEN 'maladie' THEN 'Maladie'
                    ELSE p.statut
                END as "Statut",
                CASE p.retard WHEN 1 THEN 'Oui' ELSE 'Non' END as "En Retard",
                p.minutes_retard as "Minutes de Retard"
            FROM presences p
            JOIN employes e ON e.id = p.employe_id
            WHERE 1=1
        """
        params = []
        if date_debut:
            query += " AND p.date >= ?"; params.append(date_debut)
        if date_fin:
            query += " AND p.date <= ?"; params.append(date_fin)
        if employe_id:
            query += " AND p.employe_id = ?"; params.append(employe_id)
        if departement:
            query += " AND e.departement = ?"; params.append(departement)
        query += " ORDER BY p.date DESC, e.nom"

        rows = db.fetchall(query, tuple(params))
        return pd.DataFrame(rows) if rows else pd.DataFrame()

    @staticmethod
    def _get_absences_data(date_debut: str = None, date_fin: str = None) -> pd.DataFrame:
        query = """
            SELECT
                e.prenom || ' ' || e.nom as "Nom Complet",
                e.departement as "Département",
                a.date as "Date",
                CASE a.type_absence
                    WHEN 'absent'  THEN 'Absent'
                    WHEN 'conge'   THEN 'Congé'
                    WHEN 'maladie' THEN 'Maladie'
                    ELSE a.type_absence
                END as "Type",
                a.motif as "Motif",
                CASE a.justifiee WHEN 1 THEN 'Oui' ELSE 'Non' END as "Justifiée"
            FROM absences a
            JOIN employes e ON e.id = a.employe_id
            WHERE 1=1
        """
        params = []
        if date_debut:
            query += " AND a.date >= ?"; params.append(date_debut)
        if date_fin:
            query += " AND a.date <= ?"; params.append(date_fin)
        query += " ORDER BY a.date DESC, e.nom"
        rows = db.fetchall(query, tuple(params))
        return pd.DataFrame(rows) if rows else pd.DataFrame()

    @staticmethod
    def _get_retards_data(date_debut: str = None, date_fin: str = None) -> pd.DataFrame:
        query = """
            SELECT
                e.prenom || ' ' || e.nom as "Nom Complet",
                e.departement as "Département",
                r.date as "Date",
                r.heure_arrivee as "Heure Arrivée",
                r.heure_officielle as "Heure Officielle",
                r.minutes_retard as "Minutes de Retard"
            FROM retards r
            JOIN employes e ON e.id = r.employe_id
            WHERE 1=1
        """
        params = []
        if date_debut:
            query += " AND r.date >= ?"; params.append(date_debut)
        if date_fin:
            query += " AND r.date <= ?"; params.append(date_fin)
        query += " ORDER BY r.date DESC, e.nom"
        rows = db.fetchall(query, tuple(params))
        return pd.DataFrame(rows) if rows else pd.DataFrame()

    # ─── Export Excel ──────────────────────────────────────────────────────────

    @staticmethod
    def export_excel(date_debut: str = None, date_fin: str = None,
                     employe_id: int = None, departement: str = None) -> str:
        """Exporte les données en fichier Excel multi-feuilles."""
        os.makedirs(EXPORT_DIR, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = os.path.join(EXPORT_DIR, f"rapport_presences_{ts}.xlsx")

        df_att = ReportService._get_attendance_data(date_debut, date_fin, employe_id, departement)
        df_abs = ReportService._get_absences_data(date_debut, date_fin)
        df_ret = ReportService._get_retards_data(date_debut, date_fin)

        with pd.ExcelWriter(filepath, engine="openpyxl") as writer:
            if not df_att.empty:
                df_att.to_excel(writer, sheet_name="Présences", index=False)
            if not df_abs.empty:
                df_abs.to_excel(writer, sheet_name="Absences", index=False)
            if not df_ret.empty:
                df_ret.to_excel(writer, sheet_name="Retards", index=False)

            # Mise en forme des colonnes
            for sheet_name in writer.sheets:
                ws = writer.sheets[sheet_name]
                for col in ws.columns:
                    max_len = max(len(str(cell.value or "")) for cell in col)
                    ws.column_dimensions[col[0].column_letter].width = min(max_len + 4, 40)

        return filepath

    # ─── Export CSV ───────────────────────────────────────────────────────────

    @staticmethod
    def export_csv(date_debut: str = None, date_fin: str = None) -> str:
        """Exporte les présences en fichier CSV."""
        os.makedirs(EXPORT_DIR, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = os.path.join(EXPORT_DIR, f"rapport_presences_{ts}.csv")
        df = ReportService._get_attendance_data(date_debut, date_fin)
        df.to_csv(filepath, index=False, encoding="utf-8-sig", sep=";")
        return filepath

    # ─── Export PDF ───────────────────────────────────────────────────────────

    @staticmethod
    def export_pdf(date_debut: str = None, date_fin: str = None,
                   employe_id: int = None) -> str:
        """Génère un rapport PDF professionnel avec ReportLab."""
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.platypus import (SimpleDocTemplate, Table, TableStyle,
                                         Paragraph, Spacer, HRFlowable)
        from reportlab.lib.enums import TA_CENTER, TA_LEFT

        os.makedirs(EXPORT_DIR, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = os.path.join(EXPORT_DIR, f"rapport_presences_{ts}.pdf")

        doc = SimpleDocTemplate(
            filepath, pagesize=landscape(A4),
            rightMargin=1.5*cm, leftMargin=1.5*cm,
            topMargin=2*cm, bottomMargin=1.5*cm
        )

        styles = getSampleStyleSheet()
        title_style  = ParagraphStyle("Title",  parent=styles["Title"],
                                       fontSize=18, textColor=colors.HexColor("#1a1a2e"),
                                       spaceAfter=6, alignment=TA_CENTER)
        sub_style    = ParagraphStyle("Sub",    parent=styles["Normal"],
                                       fontSize=10, textColor=colors.HexColor("#555555"),
                                       alignment=TA_CENTER, spaceAfter=20)
        section_style = ParagraphStyle("Section", parent=styles["Heading2"],
                                        fontSize=13, textColor=colors.HexColor("#2D9CDB"),
                                        spaceBefore=16, spaceAfter=8)

        story = []

        # ── En-tête ──
        story.append(Paragraph("Rapport de Présences des Employés", title_style))
        period = ""
        if date_debut and date_fin:
            period = f"Période : {date_debut} au {date_fin}"
        elif date_debut:
            period = f"À partir du {date_debut}"
        elif date_fin:
            period = f"Jusqu'au {date_fin}"
        else:
            period = f"Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}"
        story.append(Paragraph(period, sub_style))
        story.append(HRFlowable(width="100%", thickness=2,
                                 color=colors.HexColor("#2D9CDB")))
        story.append(Spacer(1, 0.4*cm))

        # ── Section Présences ──
        df_att = ReportService._get_attendance_data(date_debut, date_fin, employe_id)
        if not df_att.empty:
            story.append(Paragraph("📋 Historique des Présences", section_style))
            cols = ["Nom Complet", "Département", "Date", "Heure Entrée",
                    "Heure Sortie", "Heures Travaillées", "Statut", "En Retard"]
            existing_cols = [c for c in cols if c in df_att.columns]
            data = [existing_cols] + df_att[existing_cols].fillna("—").values.tolist()
            table = Table(data, repeatRows=1)
            table.setStyle(TableStyle([
                ("BACKGROUND",  (0,0), (-1,0), colors.HexColor("#1a1a2e")),
                ("TEXTCOLOR",   (0,0), (-1,0), colors.white),
                ("FONTNAME",    (0,0), (-1,0), "Helvetica-Bold"),
                ("FONTSIZE",    (0,0), (-1,0), 9),
                ("FONTSIZE",    (0,1), (-1,-1), 8),
                ("ROWBACKGROUNDS", (0,1), (-1,-1),
                 [colors.white, colors.HexColor("#f0f4f8")]),
                ("GRID",        (0,0), (-1,-1), 0.5, colors.HexColor("#cccccc")),
                ("ALIGN",       (0,0), (-1,-1), "CENTER"),
                ("VALIGN",      (0,0), (-1,-1), "MIDDLE"),
                ("PADDING",     (0,0), (-1,-1), 4),
            ]))
            story.append(table)
            story.append(Spacer(1, 0.5*cm))

        # ── Section Retards ──
        df_ret = ReportService._get_retards_data(date_debut, date_fin)
        if not df_ret.empty:
            story.append(Paragraph("⏰ Historique des Retards", section_style))
            data = [list(df_ret.columns)] + df_ret.fillna("—").values.tolist()
            table = Table(data, repeatRows=1)
            table.setStyle(TableStyle([
                ("BACKGROUND",  (0,0), (-1,0), colors.HexColor("#E74C3C")),
                ("TEXTCOLOR",   (0,0), (-1,0), colors.white),
                ("FONTNAME",    (0,0), (-1,0), "Helvetica-Bold"),
                ("FONTSIZE",    (0,0), (-1,-1), 8),
                ("ROWBACKGROUNDS", (0,1), (-1,-1),
                 [colors.white, colors.HexColor("#fff5f5")]),
                ("GRID",        (0,0), (-1,-1), 0.5, colors.HexColor("#cccccc")),
                ("ALIGN",       (0,0), (-1,-1), "CENTER"),
                ("PADDING",     (0,0), (-1,-1), 4),
            ]))
            story.append(table)

        doc.build(story)
        return filepath
