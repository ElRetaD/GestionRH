"""
Génération des fiches de paie en PDF (ReportLab).
"""
import os
from datetime import datetime

from app.config import EXPORT_DIR
from app.models.models import BulletinPaie, ElementPaie
from app.services.payroll_service import PayrollService


class PayslipPdfService:
    """Génère des bulletins de paie PDF professionnels."""

    @staticmethod
    def generate(bulletin: BulletinPaie) -> str:
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import cm
        from reportlab.platypus import (
            HRFlowable,
            Paragraph,
            SimpleDocTemplate,
            Spacer,
            Table,
            TableStyle,
        )

        os.makedirs(EXPORT_DIR, exist_ok=True)
        safe_name = bulletin.nom_complet.replace(" ", "_")
        filename = f"fiche_paie_{safe_name}_{bulletin.periode}.pdf"
        filepath = os.path.join(EXPORT_DIR, filename)

        doc = SimpleDocTemplate(
            filepath,
            pagesize=A4,
            rightMargin=2 * cm,
            leftMargin=2 * cm,
            topMargin=2 * cm,
            bottomMargin=2 * cm,
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "Title",
            parent=styles["Title"],
            fontSize=20,
            textColor=colors.HexColor("#1a1a2e"),
            alignment=TA_CENTER,
            spaceAfter=4,
        )
        sub_style = ParagraphStyle(
            "Sub",
            parent=styles["Normal"],
            fontSize=10,
            textColor=colors.HexColor("#555555"),
            alignment=TA_CENTER,
            spaceAfter=16,
        )
        section_style = ParagraphStyle(
            "Section",
            parent=styles["Heading2"],
            fontSize=12,
            textColor=colors.HexColor("#2D9CDB"),
            spaceBefore=12,
            spaceAfter=6,
        )
        normal = ParagraphStyle(
            "NormalLeft",
            parent=styles["Normal"],
            fontSize=10,
            alignment=TA_LEFT,
        )

        story = []
        story.append(Paragraph("FICHE DE PAIE", title_style))
        story.append(Paragraph("GestPrésences — Gestion RH", sub_style))
        story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#2D9CDB")))
        story.append(Spacer(1, 0.5 * cm))

        periode_label = PayslipPdfService._format_periode(bulletin.periode)
        info_data = [
            ["Employé", bulletin.nom_complet, "Période", periode_label],
            ["Département", bulletin.departement or "—", "Poste", bulletin.poste or "—"],
            ["Date génération", datetime.now().strftime("%d/%m/%Y %H:%M"), "Statut", bulletin.statut.capitalize()],
        ]
        info_table = Table(info_data, colWidths=[3.5 * cm, 5.5 * cm, 3 * cm, 4 * cm])
        info_table.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
            ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#e2e8f0")),
            ("PADDING", (0, 0), (-1, -1), 8),
        ]))
        story.append(info_table)
        story.append(Spacer(1, 0.6 * cm))

        elements = PayrollService.get_elements(bulletin.employe_id, bulletin.periode)
        gains_rows = [["Libellé", "Type", "Montant (MAD)"]]
        gains_rows.append(["Salaire de base", "Fixe", PayslipPdfService._fmt(bulletin.salaire_base)])

        for el in elements:
            if el.type_element == "prime":
                gains_rows.append([el.libelle, "Prime", PayslipPdfService._fmt(el.montant)])
            elif el.type_element == "heures_sup":
                detail = f"{el.heures}h × {el.taux or 'taux'}"
                gains_rows.append([f"{el.libelle} ({detail})", "Heures sup.", PayslipPdfService._fmt(el.montant)])

        gains_rows.append(["", "TOTAL BRUT", PayslipPdfService._fmt(bulletin.salaire_brut)])

        story.append(Paragraph("Éléments de rémunération", section_style))
        gains_table = Table(gains_rows, colWidths=[8 * cm, 4 * cm, 4 * cm])
        gains_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a1a2e")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
            ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#e8f4fd")),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("ALIGN", (2, 0), (2, -1), "RIGHT"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
            ("PADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(gains_table)
        story.append(Spacer(1, 0.4 * cm))

        ded_rows = [["Libellé", "Montant (MAD)"]]
        ded_elements = [e for e in elements if e.type_element == "deduction"]
        if ded_elements:
            for el in ded_elements:
                ded_rows.append([el.libelle, PayslipPdfService._fmt(el.montant)])
        else:
            ded_rows.append(["Aucune déduction", "0,00"])
        ded_rows.append(["TOTAL DÉDUCTIONS", PayslipPdfService._fmt(bulletin.total_deductions)])

        story.append(Paragraph("Déductions", section_style))
        ded_table = Table(ded_rows, colWidths=[10 * cm, 6 * cm])
        ded_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E74C3C")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
            ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#fff5f5")),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("ALIGN", (1, 0), (1, -1), "RIGHT"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
            ("PADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(ded_table)
        story.append(Spacer(1, 0.6 * cm))

        recap = [
            ["Heures travaillées (présences)", f"{bulletin.heures_travaillees:.1f} h"],
            ["Salaire brut", PayslipPdfService._fmt(bulletin.salaire_brut)],
            ["Total déductions", PayslipPdfService._fmt(bulletin.total_deductions)],
            ["SALAIRE NET À PAYER", PayslipPdfService._fmt(bulletin.salaire_net)],
        ]
        recap_table = Table(recap, colWidths=[10 * cm, 6 * cm])
        recap_table.setStyle(TableStyle([
            ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, -1), (-1, -1), 12),
            ("TEXTCOLOR", (0, -1), (-1, -1), colors.HexColor("#1a1a2e")),
            ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#d4edda")),
            ("FONTSIZE", (0, 0), (-1, -2), 10),
            ("ALIGN", (1, 0), (1, -1), "RIGHT"),
            ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#2D9CDB")),
            ("PADDING", (0, 0), (-1, -1), 10),
        ]))
        story.append(recap_table)
        story.append(Spacer(1, 1 * cm))
        story.append(Paragraph(
            "Document généré automatiquement — à conserver par l'employé.",
            ParagraphStyle("Footer", parent=normal, fontSize=8,
                           textColor=colors.HexColor("#888888"), alignment=TA_CENTER),
        ))

        doc.build(story)
        PayrollService.update_pdf_path(bulletin.id, filepath)
        return filepath

    @staticmethod
    def _fmt(amount: float) -> str:
        return f"{amount:,.2f}".replace(",", " ").replace(".", ",")

    @staticmethod
    def _format_periode(periode: str) -> str:
        months = {
            "01": "Janvier", "02": "Février", "03": "Mars", "04": "Avril",
            "05": "Mai", "06": "Juin", "07": "Juillet", "08": "Août",
            "09": "Septembre", "10": "Octobre", "11": "Novembre", "12": "Décembre",
        }
        year, month = periode.split("-")
        return f"{months.get(month, month)} {year}"
