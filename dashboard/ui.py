from html import escape
from io import BytesIO

import pandas as pd
import streamlit as st


FILTER_HELP = {
    "sexo": "Restringe os resultados ao sexo informado no cadastro do paciente.",
    "faixa_etaria": "Exibe somente pacientes das faixas etárias selecionadas.",
    "condicao_clinica": "Filtra os processos pela condição clínica associada ao paciente.",
    "sus_exclusivo": "Permite separar pacientes que dependem exclusivamente do SUS dos demais.",
    "renda_familiar": "Restringe os resultados pela faixa de renda familiar cadastrada.",
    "regiao": "Exibe somente registros das regiões brasileiras selecionadas.",
    "uf": "Filtra os registros pelo estado (UF) relacionado ao processo.",
    "municipio": "Exibe somente processos dos municípios selecionados.",
    "natureza": "Separa os processos pela natureza da demanda, como medicamentos ou internações.",
    "tipo_demanda": "Filtra pelo tipo específico de pedido feito no processo judicial.",
    "item_demandado": "Localiza processos conforme o medicamento, procedimento, insumo ou serviço solicitado.",
    "especialidade": "Restringe os resultados à especialidade médica relacionada à demanda.",
    "esfera": "Filtra os processos pela esfera judicial responsável.",
    "fase_processual": "Exibe processos que estão nas fases processuais selecionadas.",
    "desfecho": "Filtra pelo resultado ou situação final registrada para o processo.",
    "liminar": "Permite visualizar processos conforme a existência ou concessão de medida liminar.",
    "urgente": "Separa as demandas classificadas como urgentes das não urgentes.",
    "medicamento_dcb": "Filtra pelo princípio ativo do medicamento, usando a Denominação Comum Brasileira (DCB).",
    "cid": "Restringe os registros pelo código da Classificação Internacional de Doenças (CID).",
    "rename_incorporado": "Indica se o medicamento está incorporado à Relação Nacional de Medicamentos Essenciais (RENAME).",
    "componente_sus": "Filtra pelo componente da assistência farmacêutica responsável pelo financiamento no SUS.",
    "grupo_sus": "Restringe pelo grupo de financiamento ou fornecimento do medicamento no SUS.",
    "pcdt_aplicavel": "Separa os casos conforme a existência de Protocolo Clínico e Diretriz Terapêutica aplicável.",
    "pcdt_referencia": "Filtra pelo protocolo clínico ou diretriz terapêutica usado como referência.",
    "competencia_petsus": "Exibe os casos conforme a competência judicial simulada: Justiça Federal ou Estadual.",
    "reu_sugerido": "Filtra pelo ente público indicado na simulação como possível réu: União, Estado ou Município.",
}


def br_int(value: float | int) -> str:
    if pd.isna(value):
        return "0"
    return f"{int(round(float(value))):,}".replace(",", ".")


def br_float(value: float | int, casas: int = 1) -> str:
    if pd.isna(value):
        value = 0
    return f"{float(value):,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def br_money(value: float | int, compact: bool = True) -> str:
    value = 0 if pd.isna(value) else float(value)
    if compact and abs(value) >= 1_000_000:
        return f"R$ {br_float(value / 1_000_000, 1)} Mi"
    if compact and abs(value) >= 1_000:
        return f"R$ {br_float(value / 1_000, 1)} Mil"
    return f"R$ {br_float(value, 2)}"


def pct(part: float, total: float) -> float:
    return 0.0 if total in [0, None] or pd.isna(total) else (float(part) / float(total)) * 100


def fmt_periodo(df: pd.DataFrame) -> str:
    if df.empty:
        return "Sem dados"
    inicio = df["data_ajuizamento"].min().strftime("%d/%m/%Y")
    fim = df["data_ajuizamento"].max().strftime("%d/%m/%Y")
    return f"{inicio} a {fim}"


def section_title(title: str) -> None:
    st.markdown(f'<div class="section-title">{escape(str(title))}</div>', unsafe_allow_html=True)


def metric_card(label: str, value: str, subtitle: str, icon: str, icon_cls: str = "icon-blue") -> None:
    value_text = str(value)
    longest_word = max((len(word) for word in value_text.split()), default=0)
    value_size_cls = " metric-value-long" if longest_word >= 9 else ""
    card_size_cls = " metric-card-long" if longest_word >= 9 else ""
    st.markdown(
        f"""
        <div class="metric-card{card_size_cls}"><div class="metric-wrap">
            <div class="metric-head">
                <div class="metric-icon {escape(str(icon_cls), quote=True)}">{escape(str(icon))}</div>
                <div class="metric-label">{escape(str(label))}</div>
            </div>
            <div class="metric-value{value_size_cls}">{escape(value_text)}</div>
            <div class="metric-sub">{escape(str(subtitle))}</div>
        </div></div>
        """,
        unsafe_allow_html=True,
    )


def insight_card(title: str, value: str, desc: str) -> None:
    st.markdown(
        f"""<div class="insight-card">
            <div class="insight-title">{escape(str(title))}</div>
            <div class="insight-value">{escape(str(value))}</div>
            <div class="insight-desc">{escape(str(desc))}</div>
        </div>""",
        unsafe_allow_html=True,
    )


def to_excel_bytes(df: pd.DataFrame) -> bytes:
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="dados_filtrados", index=False)
    return output.getvalue()


def multiselect_sidebar(label: str, df: pd.DataFrame, column: str) -> list[str]:
    options = sorted([value for value in df[column].dropna().astype(str).unique().tolist() if value.strip()])
    return st.multiselect(
        label,
        options,
        placeholder="Todos",
        help=FILTER_HELP.get(column, f"Filtra os resultados pelos valores selecionados em {label}."),
    )
