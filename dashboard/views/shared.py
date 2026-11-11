from __future__ import annotations

from html import escape
import re

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from ..charts import barh, chart_layout, distribution_bar, empty_fig, monthly_line, semantic_color, top_group
from ..theme import apply_chart_appearance
from ..ui import br_float, br_int, br_money, insight_card, metric_card, pct, section_title, to_excel_bytes
from petsus.reports.process_tracking_pdf import build_process_tracking_pdf
from petsus.data.prevention import PREVENTION_ACTIONS
from petsus.dashboard.table_layout import compact_column_config, compact_column_width


MIN_PATIENTS = 5


JUDICIAL_TRACK = (
    "Documentação preparada", "Processo protocolado", "Processo distribuído",
    "Análise técnica", "Aguardando decisão", "Decisão judicial",
    "Órgão responsável intimado", "Cumprimento em acompanhamento", "Sentença",
    "Recursos / trânsito em julgado / encerramento",
)


LABELS = {
    "processo_id": "Processo", "paciente_id": "Código do paciente", "paciente": "Paciente", "cpf": "CPF mascarado",
    "municipio": "Município", "uf": "UF", "regiao": "Região", "natureza": "Natureza da ação",
    "tipo_demanda": "Tipo de demanda", "fase_processual": "Fase processual", "desfecho": "Desfecho",
    "especialidade": "Especialidade", "item_demandado": "Item demandado", "condicao_clinica": "Condição clínica",
    "medicamento_dcb": "Princípio ativo (DCB)", "cid": "Código do diagnóstico (CID)",
    "rename_incorporado": "Incorporado à lista RENAME", "componente_sus": "Componente da assistência farmacêutica",
    "grupo_sus": "Grupo de financiamento SUS", "apresentacao_padronizada": "Apresentação do medicamento",
    "pcdt_aplicavel": "Protocolo clínico aplicável", "pcdt_referencia": "Protocolo clínico de referência",
    "dose_prescrita": "Dose prescrita", "frequencia_administracao": "Frequência de administração",
    "duracao_meses": "Duração (meses)", "pmvg_referencia": "Preço estimado por administração (R$)",
    "valor_anual_tratamento": "Tratamento estimado para 12 meses (R$)", "valor_causa_estimado": "Valor estimado da causa (R$)",
    "competencia_petsus": "Competência judicial", "reu_sugerido": "Réu sugerido",
    "ente_responsavel": "Ente responsável", "ente_dispensacao_simulado": "Dispensação administrativa",
    "processos": "Processos", "pacientes": "Pacientes distintos", "custo_total": "Custo estimado dos processos (R$)",
    "custo_medio": "Custo médio por processo (R$)", "tempo_medio": "Tempo médio (dias)",
    "custo_mediano": "Mediana do custo (R$)", "custo_q1": "1º quartil do custo (R$)", "custo_q3": "3º quartil do custo (R$)",
    "valor_anual": "Tratamentos estimados para 12 meses (R$)", "valor_causa": "Valor estimado das causas (R$)",
    "causa_judicializacao": "Causa da judicialização", "motivo_potencialmente_evitavel": "Ação administrativa sugerida",
    "faixa_etaria": "Faixa etária", "sexo": "Sexo", "faixa_custo": "Faixa de custo acumulado por paciente",
    "custo_estimado": "Custo estimado (R$)", "freq": "Frequência", "dcb": "Princípio ativo",
    "data_ajuizamento": "Data de ajuizamento", "salario_minimo_ajuizamento": "Salário mínimo no ajuizamento (R$)",
    "limite_210_sm_ajuizamento": "Limite de 210 salários no ajuizamento (R$)", "ano": "Ano do ajuizamento",
}


def mask_cpf(value: object) -> str:
    digits = re.sub(r"\D", "", str(value))
    return f"{digits[:3]}.***.***-{digits[-2:]}" if len(digits) == 11 else "Não informado"


def mask_personal_data(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()
    for column in result.columns:
        if "cpf" in str(column).lower():
            result[column] = result[column].map(mask_cpf)
    return result


def protected_aggregate(df: pd.DataFrame, groups: list[str], **extra) -> pd.DataFrame:
    """Publica somente células com >=5 pacientes; evita reconstrução de célula única.

    A contagem é de pessoas distintas, nunca de linhas/processos. Quando há uma
    única célula pequena, a menor célula publicável também é suprimida.
    """
    aggregations = dict(processos=("processo_id", "count"), pacientes=("paciente_id", "nunique"))
    for name, column, op in [
        ("custo_total", "custo_estimado", "sum"), ("custo_medio", "custo_estimado", "mean"),
        ("tempo_medio", "tempo_tramitacao_dias", "mean"),
    ]:
        if column in df:
            aggregations[name] = (column, op)
    aggregations.update(extra)
    result = df.groupby(groups, dropna=False, observed=True).agg(**aggregations).reset_index()
    safe = result["pacientes"] >= MIN_PATIENTS
    if (~safe).sum() == 1 and safe.any():
        safe.loc[result.loc[safe, "pacientes"].idxmin()] = False
    suppressed = bool((~safe).any())
    result = result.loc[safe].copy()
    result.attrs["small_cells_suppressed"] = suppressed
    return result


def judgment_summary(df: pd.DataFrame) -> dict:
    counts = df["desfecho"].value_counts()
    full = int(counts.get("Procedente", 0))
    partial = int(counts.get("Parcialmente procedente", 0))
    rejected = int(counts.get("Improcedente", 0))
    judged = full + partial + rejected
    return {
        "julgados": judged, "procedentes": full, "parciais": partial,
        "procedencia": 100 * full / judged if judged else None,
        "procedencia_parcial": 100 * partial / judged if judged else None,
        "pendentes": int(counts.get("Em andamento", 0)),
        "acordos": int(counts.get("Acordo", 0)),
        "outros": len(df) - judged - int(counts.get("Em andamento", 0)) - int(counts.get("Acordo", 0)),
    }


def _publishable_subset(df: pd.DataFrame, mask: pd.Series) -> bool:
    return all(count == 0 or count >= MIN_PATIENTS for count in (
        df.loc[mask, "paciente_id"].nunique(), df.loc[~mask, "paciente_id"].nunique(),
    ))


def _rate(df: pd.DataFrame, mask: pd.Series) -> str:
    if df.empty:
        return "Não se aplica"
    if not _publishable_subset(df, mask):
        return "Suprimido"
    return f"{br_float(pct(mask.sum(), len(df)))}%"


def _count(df: pd.DataFrame, mask: pd.Series) -> str:
    return br_int(mask.sum()) if _publishable_subset(df, mask) else "Suprimido"


def _cards(cards) -> None:
    for column, card in zip(st.columns(len(cards)), cards):
        with column:
            metric_card(*card)


def _plot(fig, *, key: str) -> None:
    apply_chart_appearance(fig, contrast=st.session_state.get("a11y_contrast", False), large_text=st.session_state.get("a11y_large_text", False))
    st.plotly_chart(fig, key=key, use_container_width=True, theme=None, config={"displayModeBar": False, "responsive": True, "scrollZoom": False, "locale": "pt-BR"})


def _table(df: pd.DataFrame, height: int = 350, *, wrap_text: bool = False) -> None:
    view = mask_personal_data(df).rename(columns=LABELS)
    if view.empty:
        st.info("Nenhuma célula publicável neste recorte. Grupos com menos de 5 pacientes distintos são protegidos.")
        return
    view = view.rename(columns={column: str(column).replace("_", " ").capitalize() for column in view if "_" in str(column)})
    if wrap_text:
        # HTML keeps long descriptions readable without truncating cell contents.
        numeric_columns = [index + 1 for index, column in enumerate(view)
                           if pd.api.types.is_numeric_dtype(view[column]) or str(column).startswith("%")]
        compact_rules = "".join(
            f".demands-readable-table th:nth-child({index}),"
            f".demands-readable-table td:nth-child({index})"
            "{width:105px;text-align:right;white-space:nowrap;}"
            for index in numeric_columns
        )
        st.markdown(
            "<style>"
            ".demands-table-scroll{width:100%;overflow-x:auto;margin:.5rem 0 1rem;}"
            ".demands-readable-table{width:100%;border-collapse:collapse;table-layout:fixed;color:inherit;font-size:.95rem;}"
            ".demands-readable-table th,.demands-readable-table td{padding:14px 12px;"
            "text-align:left;vertical-align:top;white-space:normal;overflow-wrap:anywhere;"
            "border-bottom:1px solid #94a3b844;line-height:1.5;}"
            ".demands-readable-table th{font-weight:700;background:#94a3b812;}"
            ".demands-readable-table tbody tr:nth-child(even){background:#94a3b808;}"
            "@media(max-width:700px){.demands-readable-table{min-width:650px;}}"
            + compact_rules + "</style>"
            '<div class="demands-table-scroll" role="region" aria-label="Tabela de demandas" tabindex="0">'
            + view.to_html(index=False, escape=True, border=0, classes="demands-readable-table")
            + "</div>", unsafe_allow_html=True,
        )
        return
    config = compact_column_config(view)
    for column in view:
        if column.endswith("(R$)") or "PMVG" in column:
            config[column] = st.column_config.NumberColumn(column, format="R$ %.2f", width=compact_column_width(view[column], column, money=True), help=column)
        elif pd.api.types.is_numeric_dtype(view[column]):
            config[column] = st.column_config.NumberColumn(column, format="%.1f" if "dias" in column else "%d", width=compact_column_width(view[column], column), help=column)
    st.dataframe(view, hide_index=True, width="content", height=height, row_height=40, column_config=config)


def _distribution(df, column, title, height=340, patients=False):
    with st.container(border=True, key=f"manager_panel_distribution_{column}_{title}"):
        section_title(title)
        agg = protected_aggregate(df, [column])
        value = "pacientes" if patients else "processos"
        denominator = df["paciente_id"].nunique() if patients else len(df)
        _plot(distribution_bar(agg, column, value, denominator=denominator, height=height), key=f"distribution:{column}:{title}")
        st.caption(f"Percentuais sobre {br_int(denominator)} {'pacientes distintos' if patients else 'processos'} no recorte; células protegidas podem não ser exibidas.")


def _ranking(df, column, title, value="processo_id", op="count", height=350, separate=False):
    with st.container(border=True, key=f"manager_panel_ranking_{column}_{op}_{title}"):
        section_title(title)
        grouped = top_group(df, column, value, 10, op)
        grouped["texto"] = grouped["valor"].map(br_money if op in {"sum", "mean"} else br_int)
        _plot(barh(grouped, column, "valor", "texto", height=height, color="#239B56" if op == "sum" else "#125CC9", separate_dominant=separate), key=f"ranking:{column}:{value}:{op}:{title}")


def tracking_bar(title: str, stages, current: int, color: str) -> None:
    help_text = (
        "Andamento do processo no Judiciário, da preparação dos documentos ao encerramento."
        if title.startswith("Trilha A") else
        "Cumprimento prático pela saúde: disponibilidade, aquisição, comunicação e entrega ou realização."
    )
    items = []
    for index, name in enumerate(stages, start=1):
        state = "done" if index < current else "current" if index == current else "pending"
        marker = "✓" if index < current else str(index)
        items.append(f'<div class="flow-step {state}" style="--track-color:{color}"><div class="flow-marker">{marker}</div><div class="flow-label">{escape(str(name))}</div></div>')
    st.markdown(
        f'<div class="flow-title">{escape(title)}<span class="card-help" tabindex="0" role="img" aria-label="Ajuda: {escape(help_text, quote=True)}" data-help="{escape(help_text, quote=True)}">?</span></div><div class="flow-track">' + "".join(items) + "</div>",
        unsafe_allow_html=True,
    )


def _medication_subset(dff):
    med = dff[dff["medicamento_petsus"].eq("Sim")].copy()
    med["componente_sus"] = med["componente_sus"].replace({
        "CBAF": "Assistência básica (CBAF)", "CEAF": "Assistência especializada (CEAF)",
        "CESAF": "Assistência estratégica (CESAF)", "AF Onco": "Assistência oncológica",
    })
    st.info("Consulte medicamentos, protocolos, custos e responsabilidades administrativas. Confirme a disponibilidade com a rede de saúde e as informações jurídicas com o órgão responsável.")
    if med["paciente_id"].nunique() < MIN_PATIENTS:
        st.info("Nenhum grupo de medicamentos publicável com estes filtros. São necessários pelo menos 5 pacientes distintos.")
        return None
    st.caption(f"Denominador desta análise: {br_int(len(med))} demandas de medicamentos, de {br_int(med['paciente_id'].nunique())} pacientes distintos; não é o total de processos de outras naturezas.")
    return med


def _cost_definitions():
    st.caption("Os três valores medem conceitos diferentes e não devem ser somados: custo estimado dos processos = estimativa do atendimento judicializado; tratamento para 12 meses = projeção anual; valor da causa = estimativa processual. Nenhum comprova gasto executado. O preço estimado por administração é valor anual dividido pelo número de administrações anuais; não é cotação oficial PMVG. Uma cotação CMED exige apresentação e quantidade de unidades.")
