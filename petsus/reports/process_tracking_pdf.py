from __future__ import annotations

from datetime import datetime
from io import BytesIO
from typing import Mapping, Sequence
from xml.sax.saxutils import escape

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


BLUE = colors.HexColor("#0B4B93")
GREEN = colors.HexColor("#239B56")
LIGHT_BLUE = colors.HexColor("#EEF5FF")
LIGHT_GREEN = colors.HexColor("#ECFDF3")
LIGHT_GRAY = colors.HexColor("#F4F7FB")
DARK = colors.HexColor("#0B2459")
MUTED = colors.HexColor("#667085")
BORDER = colors.HexColor("#DDE6F2")


def _text(value: object, fallback: str = "Não informado") -> str:
    if value is None or pd.isna(value):
        return fallback
    value_text = str(value).strip()
    return value_text or fallback


def _paragraph(value: object, style) -> Paragraph:
    return Paragraph(escape(_text(value)), style)


def _date(value: object) -> str:
    if value is None or pd.isna(value):
        return "Não informado"
    return pd.to_datetime(value).strftime("%d/%m/%Y")


def _footer(canvas, document) -> None:
    canvas.saveState()
    canvas.setStrokeColor(BORDER)
    canvas.line(18 * mm, 14 * mm, 192 * mm, 14 * mm)
    canvas.setFillColor(MUTED)
    canvas.setFont("Helvetica", 8)
    canvas.drawString(18 * mm, 9 * mm, "PetSUS - Consulta de andamento processual")
    canvas.drawRightString(192 * mm, 9 * mm, f"Página {document.page}")
    canvas.restoreState()


def _stage_table(
    stages: Sequence[str], current_order: int, accent: colors.Color, styles
) -> Table:
    rows = [["Nº", "Etapa", "Situação"]]
    for index, stage in enumerate(stages, start=1):
        if current_order == 0:
            status = "Não iniciada"
        elif index < current_order:
            status = "Concluída"
        elif index == current_order:
            status = "Etapa atual"
        else:
            status = "Próxima"
        rows.append([
            str(index),
            _paragraph(stage, styles["BodyText"]),
            status,
        ])

    table = Table(rows, colWidths=[14 * mm, 112 * mm, 43 * mm], repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), accent),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
        ("ALIGN", (0, 0), (0, -1), "CENTER"),
        ("ALIGN", (2, 0), (2, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_GRAY]),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    if current_order > 0:
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, current_order), (-1, current_order), colors.HexColor("#FFF4D6")),
            ("FONTNAME", (0, current_order), (-1, current_order), "Helvetica-Bold"),
        ]))
    return table


def build_process_tracking_pdf(
    process: Mapping[str, object],
    judicial_stages: Sequence[str],
    health_stages: Sequence[str],
) -> bytes:
    """Gera o PDF da consulta selecionada inteiramente em memória."""
    output = BytesIO()
    document = SimpleDocTemplate(
        output,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=17 * mm,
        bottomMargin=20 * mm,
        title=f"Andamento do processo {_text(process.get('processo_id'))}",
        author="PetSUS",
    )
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        "ReportTitle", parent=styles["Title"], fontName="Helvetica-Bold",
        fontSize=19, leading=23, textColor=DARK, alignment=TA_CENTER, spaceAfter=5,
    ))
    styles.add(ParagraphStyle(
        "ReportSubtitle", parent=styles["Normal"], fontSize=9.5, leading=13,
        textColor=MUTED, alignment=TA_CENTER, spaceAfter=12,
    ))
    styles.add(ParagraphStyle(
        "Section", parent=styles["Heading2"], fontName="Helvetica-Bold",
        fontSize=12, leading=15, textColor=DARK, spaceBefore=8, spaceAfter=6,
    ))
    styles.add(ParagraphStyle(
        "Small", parent=styles["BodyText"], fontSize=8.5, leading=12, textColor=MUTED,
    ))

    story = [
        Paragraph("PetSUS", styles["ReportTitle"]),
        Paragraph("Consulta de andamento da judicialização em saúde", styles["ReportSubtitle"]),
    ]

    process_info = [
        ["Processo", _text(process.get("processo_id")), "Paciente", _text(process.get("paciente"))],
        ["Demanda", _paragraph(process.get("item_demandado"), styles["BodyText"]), "Tipo", _text(process.get("tipo_fluxo_saude"))],
        ["Natureza", _text(process.get("natureza")), "Consulta gerada", datetime.now().strftime("%d/%m/%Y %H:%M")],
    ]
    info_table = Table(process_info, colWidths=[25 * mm, 62 * mm, 29 * mm, 53 * mm])
    info_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT_BLUE),
        ("TEXTCOLOR", (0, 0), (-1, -1), DARK),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOX", (0, 0), (-1, -1), 0.7, BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.35, BORDER),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    story.extend([info_table, Spacer(1, 10)])

    summary = [
        ["Andamento judicial", _text(process.get("etapa_judicial")), f"{int(process.get('percentual_judicial', 0))}%"],
        ["Cumprimento na saúde", _text(process.get("etapa_saude")), f"{int(process.get('percentual_saude', 0))}%"],
        ["Status geral", _paragraph(process.get("status_andamento"), styles["BodyText"]), ""],
    ]
    summary_table = Table(summary, colWidths=[44 * mm, 106 * mm, 19 * mm])
    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT_GREEN),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (2, 0), (2, 1), "Helvetica-Bold"),
        ("ALIGN", (2, 0), (2, 1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOX", (0, 0), (-1, -1), 0.7, BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.35, BORDER),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    story.extend([summary_table, Spacer(1, 7)])

    details = [
        ["Decisão de urgência", _text(process.get("decisao_urgencia"))],
        ["Data da intimação", _date(process.get("data_intimacao"))],
        ["Data limite", _date(process.get("data_limite_cumprimento"))],
        ["Próxima ação judicial", _paragraph(process.get("proxima_acao_judicial"), styles["BodyText"])],
        ["Próxima ação na saúde", _paragraph(process.get("proxima_acao_saude"), styles["BodyText"])],
        ["Responsável pela etapa", _text(process.get("responsavel_etapa"))],
    ]
    details_table = Table(details, colWidths=[49 * mm, 120 * mm])
    details_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("BACKGROUND", (0, 0), (0, -1), LIGHT_GRAY),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.45, BORDER),
        ("FONTSIZE", (0, 0), (-1, -1), 8.7),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.extend([Paragraph("Resumo da consulta", styles["Section"]), details_table])

    story.extend([
        Paragraph("Trilha A - andamento judicial", styles["Section"]),
        _stage_table(judicial_stages, int(process.get("etapa_judicial_ordem", 0)), BLUE, styles),
        PageBreak(),
        Paragraph(f"Trilha B - cumprimento de {_text(process.get('tipo_fluxo_saude')).lower()}", styles["Section"]),
        _stage_table(health_stages, int(process.get("etapa_saude_ordem", 0)), GREEN, styles),
        Spacer(1, 10),
        KeepTogether([
            Paragraph("Observação", styles["Section"]),
            Paragraph(
                "Este relatório reflete os dados disponíveis no PetSUS no momento da consulta. "
                "Na base acadêmica, os eventos e prazos são demonstrativos e não substituem a "
                "consulta oficial ao processo, ao tribunal ou ao órgão de saúde responsável.",
                styles["Small"],
            ),
        ]),
    ])

    document.build(story, onFirstPage=_footer, onLaterPages=_footer)
    return output.getvalue()
