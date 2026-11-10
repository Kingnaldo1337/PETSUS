from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo
from io import BytesIO
from typing import Mapping, Sequence
from xml.sax.saxutils import escape

import pandas as pd
from petsus.config import APP_TIMEZONE
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
        return "Não se aplica / não registrado"
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
    styles["BodyText"].fontSize = 10
    styles["BodyText"].leading = 14
    styles.add(ParagraphStyle(
        "ReportTitle", parent=styles["Title"], fontName="Helvetica-Bold",
        fontSize=19, leading=23, textColor=DARK, alignment=TA_CENTER, spaceAfter=5,
    ))
    styles.add(ParagraphStyle(
        "ReportSubtitle", parent=styles["Normal"], fontSize=10, leading=14,
        textColor=MUTED, alignment=TA_CENTER, spaceAfter=12,
    ))
    styles.add(ParagraphStyle(
        "Section", parent=styles["Heading2"], fontName="Helvetica-Bold",
        fontSize=12, leading=15, textColor=DARK, spaceBefore=8, spaceAfter=6,
    ))
    styles.add(ParagraphStyle(
        "Small", parent=styles["BodyText"], fontSize=10, leading=14, textColor=DARK,
    ))

    story = [
        Paragraph("PetSUS", styles["ReportTitle"]),
        Paragraph("Consulta de andamento da judicialização em saúde", styles["ReportSubtitle"]),
    ]

    process_info = [
        ["Processo", _paragraph(process.get("processo_id"), styles["BodyText"]), "Paciente", _paragraph(process.get("paciente"), styles["BodyText"])],
        ["Demanda", _paragraph(process.get("item_demandado"), styles["BodyText"]), "Tipo", _text(process.get("tipo_fluxo_saude"))],
        ["Natureza", _paragraph(process.get("natureza"), styles["BodyText"]), "Consulta gerada", _paragraph(datetime.now(ZoneInfo(APP_TIMEZONE)).strftime("%d/%m/%Y %H:%M") + " (Fortaleza)", styles["BodyText"])],
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
        ["Andamento judicial", _paragraph(process.get("etapa_judicial"), styles["BodyText"]), f"{int(process.get('percentual_judicial', 0))}%"],
        ["Cumprimento na saúde", _paragraph(process.get("etapa_saude"), styles["BodyText"]), f"{int(process.get('percentual_saude', 0))}%"],
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
        ["Referência dos cálculos", _date(process.get("data_referencia_calculo")) + " (America/Fortaleza)"],
        ["Geração da simulação", _date(process.get("geracao_simulacao", process.get("ultima_atualizacao_dados")))],
        ["Ajuizamento", _date(process.get("data_ajuizamento"))],
        ["Desfecho judicial", _text(process.get("desfecho"))],
        ["Pedido urgente", _text(process.get("urgente"))],
        ["Decisão de urgência", _paragraph(process.get("decisao_urgencia"), styles["BodyText"])],
        ["Data da intimação", _date(process.get("data_intimacao"))],
        ["Data limite", _date(process.get("data_limite_cumprimento"))],
        ["Próxima ação judicial", _paragraph(process.get("proxima_acao_judicial"), styles["BodyText"])],
        ["Próxima ação na saúde", _paragraph(process.get("proxima_acao_saude"), styles["BodyText"])],
        ["Responsável pela etapa", _paragraph(process.get("responsavel_etapa"), styles["BodyText"])],
        ["Se o prazo vencer", _paragraph("Procure o órgão de saúde responsável e a Defensoria Pública ou seu representante jurídico. Informe o número do processo e a data limite. Não interrompa ou altere tratamento por conta própria.", styles["BodyText"])],
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
        Paragraph("Sobre esta consulta", styles["Section"]),
        Paragraph(
            "O período no painel filtra o ajuizamento, sem reconstruir a situação histórica. "
            "Os percentuais indicam posição em etapas ilustrativas, não prazo restante ou chance de êxito. "
            "Confirme os eventos e prazos com o tribunal ou órgão de saúde.",
            styles["Small"],
        ),
    ])

    story.extend([
        PageBreak(),
        Paragraph("Trilha A - andamento judicial", styles["Section"]),
        _stage_table(judicial_stages, int(process.get("etapa_judicial_ordem", 0)), BLUE, styles),
        Paragraph(f"Trilha B - cumprimento de {_text(process.get('tipo_fluxo_saude')).lower()}", styles["Section"]),
        _stage_table(health_stages, int(process.get("etapa_saude_ordem", 0)), GREEN, styles),
        Spacer(1, 10),
        KeepTogether([
            Paragraph("Orientações ao Cidadão e Observações Legais", styles["Section"]),
            Paragraph(
                "• <b>Dúvidas sobre o processo ou cumprimento de prazos:</b> Procure a Defensoria Pública do seu Estado "
                "(ou a Defensoria Pública da União em ações na Justiça Federal) ou o seu advogado constituído.<br/>"
                "• <b>Informações sobre o SUS:</b> Ligue gratuitamente para o <b>Disque Saúde 136</b> (Ministério da Saúde).<br/>"
                "• <b>Validade deste documento:</b> Este comprovante reflete os registros integrados ao PetSUS na data de emissão. "
                "Para certidões processuais com fé pública, consulte o portal oficial do respectivo Tribunal de Justiça.",
                styles["Small"],
            ),
        ]),
        Paragraph("Termos em linguagem simples", styles["Section"]),
        Paragraph("Liminar: decisão provisória que pode autorizar uma providência antes do julgamento final. "
                  "Intimação: comunicação formal de uma decisão. Sentença: julgamento do pedido. "
                  "Cumprimento: entrega do medicamento ou realização do serviço. Uma decisão favorável "
                  "não comprova que o atendimento já aconteceu.", styles["BodyText"]),
    ])

    document.build(story, onFirstPage=_footer, onLaterPages=_footer)
    return output.getvalue()
