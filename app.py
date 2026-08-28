from __future__ import annotations

from pathlib import Path
from html import escape
import re
import zlib
import unicodedata

import pandas as pd
import streamlit as st

from dashboard.charts import barh, chart_layout, donut, empty_fig, monthly_line, top_group
from dashboard.ui import br_float, br_int, br_money, fmt_periodo, insight_card, metric_card, multiselect_sidebar, pct, section_title, to_excel_bytes
from auth import AuthStore, logout, render_auth_gate

st.set_page_config(
    page_title="Dashboard de Judicialização na Saúde",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

DATA_FILE = Path(__file__).with_name("dados_dashboard_saude.xlsx")
REQUIRED_COLUMNS = {
    "processo_id", "data_ajuizamento", "paciente_id", "paciente",
    "sexo", "idade", "faixa_etaria", "municipio", "uf", "regiao", "latitude",
    "longitude", "condicao_clinica", "sus_exclusivo", "renda_familiar", "pcd",
    "doenca_rara", "natureza", "tipo_demanda", "item_demandado", "especialidade",
    "esfera", "fase_processual", "desfecho", "liminar", "urgente",
    "tempo_tramitacao_dias", "tempo_liminar_dias", "custo_estimado",
}

# -----------------------------------------------------------------------------
# Estilo visual
# -----------------------------------------------------------------------------
st.markdown(
    """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');
        html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
        .stApp, [data-testid="stAppViewContainer"], .main { background: #F4F7FB; color: #0B2459; }
        [data-testid="stHeader"] { background: transparent; }
        .block-container { max-width: 1700px; padding-top: 1.05rem; padding-bottom: 1.2rem; padding-left: 1.2rem; padding-right: 1.2rem; container-type: inline-size; container-name: dashboard; }
        [data-testid="stSidebar"] { background: linear-gradient(180deg, #083E82 0%, #072F66 52%, #061F45 100%); }
        [data-testid="stSidebar"] * { color: white; }
        [data-testid="stSidebar"] input, [data-testid="stSidebar"] textarea,
        [data-testid="stSidebar"] [role="combobox"] { color: #0B2459 !important; -webkit-text-fill-color: #0B2459 !important; }
        [data-testid="stSidebar"] div[data-baseweb="select"],
        [data-testid="stSidebar"] div[data-baseweb="select"] > div { background: #FFFFFF !important; }
        [data-testid="stMain"] { min-width: 0; }
        [data-testid="stHorizontalBlock"], [data-testid="stVerticalBlock"], [data-testid="stColumn"], [data-testid="stContainer"], div[data-testid="stPlotlyChart"] { min-width: 0; max-width: 100% !important; }
        [data-testid="stHorizontalBlock"], [data-testid="stVerticalBlock"], [data-testid="stContainer"], div[data-testid="stPlotlyChart"] { width: 100% !important; }
        div[data-testid="stPlotlyChart"] > div, div[data-testid="stPlotlyChart"] .js-plotly-plot, div[data-testid="stPlotlyChart"] .plot-container, div[data-testid="stPlotlyChart"] .svg-container { max-width: 100% !important; }
        .stApp [data-testid="stMain"] .block-container {
            width: 100% !important;
            max-width: none;
            min-width: 0;
            box-sizing: border-box;
        }
        .metric-card, .insight-card, .patient-box, .section-title, .insight-title, .insight-value, .insight-desc, .patient-name, .patient-sub { overflow-wrap: anywhere; word-break: break-word; }
        [data-testid="stSidebar"] div[data-baseweb="select"] span,
        [data-testid="stSidebar"] div[data-baseweb="select"] div,
        [data-testid="stSidebar"] div[data-baseweb="select"] input { color: #0B2459 !important; -webkit-text-fill-color: #0B2459 !important; }
        [data-testid="stSidebar"] div[data-baseweb="tag"] { background: #DDEBFF !important; }
        [data-testid="stSidebar"] div[data-baseweb="tag"] span { color: #0B2459 !important; }
        [data-testid="stSidebar"] .stDateInput input { color: #0B2459 !important; -webkit-text-fill-color: #0B2459 !important; }
        [data-baseweb="popover"] [role="option"], [data-baseweb="popover"] [role="option"] * { color: #0B2459 !important; }
        [data-testid="stSidebar"] .st-key-logout_button button {
            background: rgba(255, 255, 255, .14) !important;
            border: 1px solid rgba(255, 255, 255, .55) !important;
            color: #FFFFFF !important;
            font-weight: 800;
        }
        [data-testid="stSidebar"] .st-key-logout_button button p,
        [data-testid="stSidebar"] .st-key-logout_button button span {
            color: #FFFFFF !important;
        }
        [data-testid="stSidebar"] .st-key-logout_button button:hover,
        [data-testid="stSidebar"] .st-key-logout_button button:focus {
            background: rgba(255, 255, 255, .24) !important;
            border-color: #FFFFFF !important;
        }
        .sidebar-logo { padding: 1.0rem 0 .95rem 0; text-align: center; border-bottom: 1px solid rgba(255,255,255,0.18); margin-bottom: .75rem; }
        .sidebar-logo .icon { font-size: 3.25rem; line-height: 1; margin-bottom: .25rem; }
        .sidebar-logo .title { font-size: 1.75rem; font-weight: 900; line-height: 1; letter-spacing: .03em; }
        .sidebar-logo .subtitle { font-size: 1.05rem; font-weight: 500; line-height: 1.3; opacity: .88; }
        .sidebar-hint { font-size: .86rem; opacity: .86; line-height: 1.35; margin-top: -.35rem; margin-bottom: .55rem; }
        .title-main { font-size: 2.45rem; font-weight: 900; color: #0B2459; line-height: 1.04; margin-bottom: .15rem; }
        .title-sub { font-size: 1.05rem; color: #667085; margin-bottom: .4rem; }
        .filter-pill { background: #FFFFFF; border: 1px solid #DDE6F2; border-radius: 16px; padding: .78rem .95rem; color: #0B2459; font-weight: 750; text-align: center; box-shadow: 0 4px 14px rgba(11,36,89,0.05); white-space: nowrap; }
        .st-key-header_periodo [data-baseweb="input"] { min-height: 52px; background: #FFFFFF; border: 1px solid #DDE6F2; border-radius: 16px; box-shadow: 0 4px 14px rgba(11,36,89,0.05); }
        .st-key-header_periodo input { color: #0B2459 !important; font-weight: 750; text-align: center; }
        .metric-card { background: #FFFFFF; border: 1px solid #E1E9F3; border-radius: 20px; padding: .9rem 1rem; height: 185px; min-height: 185px; max-width: 100%; box-sizing: border-box; box-shadow: 0 10px 24px rgba(15, 23, 42, 0.055); }
        .metric-wrap { display: block; min-width: 0; width: 100%; height: 100%; }
        .metric-head { display: flex; gap: .7rem; align-items: center; min-width: 0; margin-bottom: .65rem; }
        .metric-icon { width: 58px; height: 58px; min-width: 58px; border-radius: 17px; display: flex; align-items: center; justify-content: center; color: white; font-size: 1.55rem; font-weight: 900; box-shadow: inset 0 -10px 20px rgba(0,0,0,.08); }
        .icon-blue { background: linear-gradient(135deg, #125CC9, #2682EA); }
        .icon-green { background: linear-gradient(135deg, #239B56, #4CCB75); }
        .icon-orange { background: linear-gradient(135deg, #D97706, #F59E0B); }
        .icon-purple { background: linear-gradient(135deg, #7C3AED, #A78BFA); }
        .metric-label { min-width: 0; font-size: .93rem; color: #31456F; font-weight: 800; line-height: 1.2; }
        .metric-value { font-size: 1.82rem; color: #0B2459; font-weight: 900; margin-bottom: .16rem; line-height: 1.08; }
        .metric-sub { font-size: .88rem; color: #667085; line-height: 1.25; }
        .metric-label, .metric-value, .metric-sub {
            word-break: normal;
            overflow-wrap: break-word;
            hyphens: none;
            max-width: 100%;
        }
        .metric-value-long { font-size: 1.35rem !important; letter-spacing: -.015em; line-height: 1.18; }
        .metric-card-long .metric-icon { width: 48px; height: 48px; min-width: 48px; border-radius: 14px; font-size: 1.3rem; }
        .section-title { font-size: 1.13rem; font-weight: 900; color: #0B2459; margin-bottom: .36rem; }
        .small-note { font-size: .88rem; color: #667085; margin-top: .2rem; line-height: 1.35; }
        .insight-card { background: #FFFFFF; border: 1px solid #E1E9F3; border-radius: 18px; padding: .95rem; min-height: 145px; max-width: 100%; box-sizing: border-box; box-shadow: 0 8px 20px rgba(15, 23, 42, 0.045); }
        .insight-title { font-size: .92rem; color: #31456F; font-weight: 800; margin-bottom: .35rem; }
        .insight-value { font-size: 1.35rem; color: #0B2459; font-weight: 900; line-height: 1.15; margin-bottom: .35rem; }
        .insight-desc { font-size: .9rem; color: #667085; line-height: 1.35; }
        .patient-box { background: linear-gradient(135deg, #FFFFFF, #F7FBFF); border: 1px solid #DDE6F2; border-radius: 20px; padding: 1rem; box-shadow: 0 10px 24px rgba(15,23,42,.055); }
        .patient-name { font-size: 1.5rem; color:#0B2459; font-weight: 900; line-height: 1.15; }
        .patient-sub { font-size: .95rem; color:#667085; margin-top:.1rem; }
        .tag { display:inline-block; padding:.25rem .55rem; margin:.25rem .25rem 0 0; border-radius:999px; background:#EEF5FF; color:#0B4B93; font-size:.85rem; font-weight:700; }
        div[data-testid="stVerticalBlockBorderWrapper"] { background: #FFFFFF; border: 1px solid #E1E9F3; border-radius: 18px; box-shadow: 0 8px 20px rgba(15, 23, 42, 0.045); padding: .45rem .6rem; }
        div[data-testid="stDataFrame"] { border: none; }
        .footer-note { font-size: .88rem; color: #667085; margin-top: .4rem; padding-bottom: .5rem; }
        /* Reage ao espaço útil do dashboard, inclusive quando a sidebar abre. */
        @container dashboard (max-width: 1120px) {
            [data-testid="stHorizontalBlock"] { flex-wrap: wrap; gap: .75rem; }
            [data-testid="stColumn"] { flex: 1 1 300px !important; width: auto !important; min-width: min(300px, 100%) !important; }
            .metric-card { height: 172px; min-height: 172px; }
            .metric-head { margin-bottom: .5rem; }
            .metric-icon { width: 50px; height: 50px; min-width: 50px; border-radius: 14px; font-size: 1.3rem; }
            .metric-value { font-size: clamp(1.35rem, 3cqi, 1.72rem); }
            .metric-value-long { font-size: 1.3rem !important; }
            div[data-testid="stPlotlyChart"] { overflow: hidden; }
        }
        @container dashboard (max-width: 680px) {
            [data-testid="stHorizontalBlock"] { gap: .65rem; }
            [data-testid="stColumn"] { flex: 1 1 100% !important; min-width: 100% !important; width: 100% !important; }
            .title-main { font-size: 1.75rem; line-height: 1.08; }
            .title-sub { font-size: .95rem; line-height: 1.3; }
            .filter-pill { white-space: normal; padding: .6rem .7rem; border-radius: 12px; }
            .metric-card { height: auto; min-height: 0; padding: .8rem; border-radius: 14px; }
            .metric-value { font-size: 1.5rem; }
            .metric-value-long { font-size: 1.3rem !important; }
            .insight-card, .patient-box { border-radius: 14px; }
            [data-testid="stDataFrame"] { max-width: 100%; overflow-x: auto; }
        }
        @media (max-width: 768px) {
            .block-container { padding: .7rem .65rem 1rem; }
            [data-testid="stHorizontalBlock"] { flex-wrap: wrap; gap: .65rem; }
            [data-testid="stColumn"] { flex: 1 1 100% !important; min-width: 100% !important; width: 100% !important; }
            .title-main { font-size: 1.75rem; line-height: 1.08; }
            .title-sub { font-size: .95rem; line-height: 1.3; }
            .filter-pill { white-space: normal; padding: .6rem .7rem; border-radius: 12px; }
            .metric-card { height: auto; min-height: 0; padding: .8rem; border-radius: 14px; }
            .metric-icon { width: 48px; height: 48px; min-width: 48px; border-radius: 14px; font-size: 1.25rem; }
            .metric-value { font-size: 1.5rem; overflow-wrap: normal; word-break: normal; }
            .metric-value-long { font-size: 1.3rem !important; }
            .insight-card, .patient-box { border-radius: 14px; }
            [data-testid="stDataFrame"] { max-width: 100%; overflow-x: auto; }
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------------------------------------------------------------
# Leitura e utilitários
# -----------------------------------------------------------------------------
def _cpf_digits(value: object) -> str:
    if pd.isna(value):
        return ""
    if isinstance(value, int):
        return str(value).zfill(11)
    if isinstance(value, float) and value.is_integer():
        return str(int(value)).zfill(11)
    return re.sub(r"\D", "", str(value))


def _format_cpf(value: object) -> str:
    digits = _cpf_digits(value)
    if len(digits) != 11:
        return str(value)
    return f"{digits[:3]}.{digits[3:6]}.{digits[6:9]}-{digits[9:]}"


def _cpf_checksum_valid(digits: str) -> bool:
    """Usado só para evitar que um CPF fictício gerado coincida com um CPF real válido."""
    if len(digits) != 11 or len(set(digits)) == 1:
        return False
    nums = [int(x) for x in digits]
    total = sum(nums[i] * (10 - i) for i in range(9))
    d1 = (total * 10 % 11) % 10
    total = sum(nums[i] * (11 - i) for i in range(10))
    d2 = (total * 10 % 11) % 10
    return nums[9] == d1 and nums[10] == d2


def _attach_full_cpf(base: pd.DataFrame) -> pd.DataFrame:
    """Garante uma coluna `cpf` completa.

    Em produção, se a planilha já trouxer `cpf`, `cpf_completo` ou `cpf_paciente`,
    o valor real da fonte é usado. Na base fictícia atual, os dígitos ocultos não
    existem; por isso é criado um CPF de demonstração estável por paciente,
    preservando o prefixo e o sufixo visíveis e evitando CPFs válidos reais.
    """
    d = base.copy()
    for source in ("cpf", "cpf_completo", "cpf_paciente"):
        if source in d.columns:
            values = d[source].map(_cpf_digits)
            invalid = values.str.len().ne(11)
            if invalid.any():
                st.error(f"A coluna '{source}' possui CPF(s) incompleto(s). Corrija a fonte de dados antes de continuar.")
                st.stop()
            d["cpf"] = values.map(_format_cpf)
            d["cpf_origem"] = "Fonte de dados"
            return d

    if "cpf_mascarado" not in d.columns:
        st.error("A base precisa conter uma coluna de CPF completo (`cpf`) ou, para demonstração, `cpf_mascarado`.")
        st.stop()

    patient_rows = (
        d[["paciente_id", "cpf_mascarado"]]
        .drop_duplicates("paciente_id")
        .sort_values("paciente_id")
    )
    mapping: dict[str, str] = {}
    used: set[str] = set()
    for row in patient_rows.itertuples(index=False):
        patient_id = str(row.paciente_id)
        masked_digits = re.sub(r"\D", "", str(row.cpf_mascarado))
        if len(masked_digits) < 5:
            st.error(f"CPF mascarado inválido para o paciente {patient_id}.")
            st.stop()
        prefix, suffix = masked_digits[:3], masked_digits[-2:]
        pid_digits = re.sub(r"\D", "", patient_id)
        base_middle = int(pid_digits or "0") % 1_000_000

        # Usa o ID do paciente como semente. Se, por coincidência, resultar em um
        # CPF matematicamente válido, desloca a parte central para mantê-lo fictício.
        for offset in (0, 500_000, 600_000, 700_000, 800_000, 900_000, 400_000, 300_000, 200_000, 100_000):
            middle = (base_middle + offset) % 1_000_000
            candidate = f"{prefix}{middle:06d}{suffix}"
            if candidate not in used and not _cpf_checksum_valid(candidate):
                used.add(candidate)
                mapping[patient_id] = _format_cpf(candidate)
                break
        else:
            st.error(f"Não foi possível gerar um CPF de demonstração para {patient_id}.")
            st.stop()

    d["cpf"] = d["paciente_id"].astype(str).map(mapping)
    d["cpf_origem"] = "Demonstração"
    return d


@st.cache_data(show_spinner=False)
def load_data(path: Path, modified_at: int) -> pd.DataFrame:
    if not path.exists():
        st.error(f"Arquivo de dados não encontrado: {path}")
        st.stop()

    try:
        base = pd.read_excel(path, sheet_name="base_processos")
    except ValueError:
        st.error("A aba 'base_processos' não foi encontrada no Excel. Use a versão atualizada do arquivo de dados.")
        st.stop()

    missing = sorted(REQUIRED_COLUMNS - set(base.columns))
    if missing:
        st.error("A aba 'base_processos' não possui todas as colunas obrigatórias.")
        st.code(", ".join(missing))
        st.stop()

    base = _attach_full_cpf(base)
    base["data_ajuizamento"] = pd.to_datetime(base["data_ajuizamento"], errors="coerce")
    invalid_dates = int(base["data_ajuizamento"].isna().sum())
    if invalid_dates == len(base):
        st.error("Nenhuma data válida foi encontrada na coluna 'data_ajuizamento'.")
        st.stop()
    if invalid_dates:
        st.warning(f"{invalid_dates} registro(s) com data inválida foram ignorados.")
        base = base.dropna(subset=["data_ajuizamento"]).copy()
    base["custo_estimado"] = pd.to_numeric(base["custo_estimado"], errors="coerce").fillna(0)
    base["idade"] = pd.to_numeric(base["idade"], errors="coerce")
    base["tempo_tramitacao_dias"] = pd.to_numeric(base["tempo_tramitacao_dias"], errors="coerce")
    base["tempo_liminar_dias"] = pd.to_numeric(base["tempo_liminar_dias"], errors="coerce")
    base["ano_mes"] = base["data_ajuizamento"].dt.to_period("M").astype(str)
    base = enrich_judsaude_fields(base)
    base["_search"] = (
        base[["paciente", "paciente_id", "cpf", "processo_id", "medicamento_dcb", "cid"]]
        .fillna("")
        .astype(str)
        .agg(" ".join, axis=1)
        .map(normalize_text)
    )
    return base


def normalize_text(value: object) -> str:
    txt = str(value).lower().strip()
    txt = unicodedata.normalize("NFKD", txt).encode("ascii", "ignore").decode("ascii")
    return txt


SALARIO_MINIMO_2026 = 1621.0
LIMITE_210_SM_2026 = 210 * SALARIO_MINIMO_2026
JUDSAUDE_FAQ_URL = "https://www.cnj.jus.br/tecnologia-da-informacao-e-comunicacao/justica-4-0/conheca-o-conecta/judsaude/perguntas-frequentes/"


def stable_int(key: object, modulo: int) -> int:
    return zlib.crc32(str(key).encode("utf-8")) % modulo


def stable_choice(key: object, choices: list):
    return choices[stable_int(key, len(choices))]


def extract_dcb(item: object) -> str:
    txt = str(item).strip()
    txt = re.sub(r"\s+\d.*$", "", txt).strip()
    return txt or str(item).strip()


def enrich_judsaude_fields(base: pd.DataFrame) -> pd.DataFrame:
    """Adiciona campos inspirados nas funcionalidades públicas do JudSaúde.

    A base deste projeto é fictícia. Portanto, os valores abaixo são sintéticos e
    determinísticos, criados apenas para permitir a demonstração dos novos filtros,
    indicadores e dashboards sem representar consulta oficial ao CNJ/CMED/RENAME.
    """
    d = base.copy()
    item_norm = d["item_demandado"].fillna("").map(normalize_text)
    nao_medicamento = item_norm.str.contains(r"dieta|cadeira|oxigenio|curativo|fralda", regex=True)
    med_mask = d["natureza"].eq("Medicamentos") & ~nao_medicamento

    text_fields = [
        "medicamento_judsaude", "medicamento_dcb", "cid", "rename_incorporado",
        "componente_sus", "grupo_sus", "apresentacao_padronizada", "pcdt_aplicavel", "pcdt_referencia",
        "dose_prescrita", "frequencia_administracao", "competencia_judsaude",
        "reu_sugerido", "criterio_competencia", "acima_210_salarios_minimos",
    ]
    for col in text_fields:
        d[col] = "Não se aplica"
    d["duracao_meses"] = pd.NA
    d["pmvg_referencia"] = pd.NA
    d["valor_anual_tratamento"] = pd.NA
    d["valor_causa_estimado"] = pd.NA
    d.loc[med_mask, "medicamento_judsaude"] = "Sim"
    d.loc[~med_mask, "medicamento_judsaude"] = "Não"

    cid_map = {
        "Doenças cardiovasculares": ["I10", "I48.9", "I50.9"],
        "Diabetes mellitus": ["E10.9", "E11.9"],
        "Transtornos mentais": ["F32.2", "F41.1", "F31.9"],
        "Neoplasias": ["C50.9", "C34.9", "C18.9", "C61"],
        "Doenças respiratórias crônicas": ["J45.9", "J44.9"],
        "Doenças raras": ["G12.0", "E75.2", "E76.0"],
        "Doenças autoimunes": ["M06.9", "K50.9", "L40.9"],
        "Outras": ["G89.4", "R69"],
    }
    pcdt_map = {
        "Doenças cardiovasculares": "PCDT cardiovascular relacionado à condição",
        "Diabetes mellitus": "PCDT de Diabetes Mellitus",
        "Transtornos mentais": "PCDT relacionado ao transtorno mental",
        "Neoplasias": "Diretriz/PCDT oncológico correspondente",
        "Doenças respiratórias crônicas": "PCDT de Asma/DPOC",
        "Doenças raras": "PCDT da doença rara correspondente",
        "Doenças autoimunes": "PCDT da condição autoimune",
        "Outras": "PCDT relacionado à condição",
    }
    freq_options = [
        ("1x ao dia", 365),
        ("1x por semana", 52),
        ("A cada 14 dias", 26),
        ("A cada 28 dias", 13),
        ("1x ao mês", 12),
    ]
    rows = []
    med_cols = ["processo_id", "item_demandado", "condicao_clinica", "custo_estimado", "uf"]
    for row in d.loc[med_mask, med_cols].itertuples():
        key = row.processo_id
        dcb = extract_dcb(row.item_demandado)
        cid = stable_choice(f"{key}-cid", cid_map.get(row.condicao_clinica, ["R69"]))
        incorporado = "Sim" if stable_int(f"{key}-rename", 100) < 58 else "Não"

        if incorporado == "Sim":
            if row.condicao_clinica == "Neoplasias":
                componente = stable_choice(f"{key}-comp", ["AF Onco", "AF Onco", "CEAF"])
            else:
                componente = stable_choice(f"{key}-comp", ["CEAF", "CEAF", "CEAF", "CBAF", "CBAF", "CESAF"])
            if componente == "CEAF":
                grupo = stable_choice(f"{key}-grupo", ["1A", "1A", "1B", "2", "3"])
            elif componente == "AF Onco":
                grupo = "Oncologia"
            else:
                grupo = componente
        else:
            componente = "Não incorporado"
            grupo = "Não incorporado"

        pcdt = "Sim" if stable_int(f"{key}-pcdt", 100) < (82 if incorporado == "Sim" else 28) else "Não"
        pcdt_ref = pcdt_map.get(row.condicao_clinica, "PCDT relacionado à condição") if pcdt == "Sim" else "Sem PCDT aplicável"
        apresentacao = str(row.item_demandado)
        dose = stable_choice(f"{key}-dose", ["1 unidade por administração", "2 unidades por administração", "Dose conforme prescrição"])
        frequencia, adm_ano = stable_choice(f"{key}-freq", freq_options)
        duracao = stable_choice(f"{key}-dur", [6, 12, 12, 12, 24])

        custo = float(row.custo_estimado or 0)
        fator_anual = 0.80 + stable_int(f"{key}-anual", 51) / 100
        valor_anual = max(custo * fator_anual, 0.0)
        fator_uf = 0.95 + stable_int(f"{row.uf}-pmvg", 11) / 100
        pmvg = (valor_anual / max(adm_ano, 1)) * fator_uf
        valor_causa = valor_anual * min(duracao, 12) / 12
        acima = "Sim" if valor_anual >= LIMITE_210_SM_2026 else "Não"

        if incorporado == "Sim":
            if componente == "AF Onco" or componente == "CESAF" or (componente == "CEAF" and grupo == "1A"):
                competencia = "Justiça Federal"
                reu = "União"
                criterio = f"Medicamento incorporado — {componente} / grupo {grupo}"
            else:
                competencia = "Justiça Estadual"
                reu = "Município" if componente == "CBAF" else "Estado"
                criterio = f"Medicamento incorporado — {componente} / grupo {grupo}"
        else:
            competencia = "Justiça Federal" if acima == "Sim" else "Justiça Estadual"
            reu = "União" if competencia == "Justiça Federal" else stable_choice(f"{key}-reu", ["Estado", "Estado", "Município"])
            criterio = "Não incorporado — custo anual ≥ 210 salários mínimos" if acima == "Sim" else "Não incorporado — custo anual < 210 salários mínimos"

        rows.append({
            "index": row.Index,
            "medicamento_dcb": dcb,
            "cid": cid,
            "rename_incorporado": incorporado,
            "componente_sus": componente,
            "grupo_sus": grupo,
            "apresentacao_padronizada": apresentacao,
            "pcdt_aplicavel": pcdt,
            "pcdt_referencia": pcdt_ref,
            "dose_prescrita": dose,
            "frequencia_administracao": frequencia,
            "duracao_meses": int(duracao),
            "pmvg_referencia": round(pmvg, 2),
            "valor_anual_tratamento": round(valor_anual, 2),
            "valor_causa_estimado": round(valor_causa, 2),
            "competencia_judsaude": competencia,
            "reu_sugerido": reu,
            "criterio_competencia": criterio,
            "acima_210_salarios_minimos": acima,
        })

    if rows:
        jud = pd.DataFrame(rows).set_index("index")
        for col in jud.columns:
            d.loc[jud.index, col] = jud[col]

    for col in ["duracao_meses", "pmvg_referencia", "valor_anual_tratamento", "valor_causa_estimado"]:
        d[col] = pd.to_numeric(d[col], errors="coerce")
    return d


base_all = load_data(DATA_FILE, DATA_FILE.stat().st_mtime_ns if DATA_FILE.exists() else 0)
auth_store = AuthStore(Path(__file__).with_name("usuarios.db"))
auth_user = render_auth_gate(auth_store, base_all)

# O escopo de acesso é aplicado antes de filtros, KPIs, tabelas ou exportações.
# Assim, um usuário comum nunca recebe registros de outros pacientes no restante do app.
if auth_user.is_manager:
    base = base_all.copy()
else:
    if not auth_user.patient_id:
        st.error("Sua conta não está vinculada a um paciente. Procure a administração do sistema.")
        st.stop()
    base = base_all[base_all["paciente_id"].astype(str) == str(auth_user.patient_id)].copy()
    if base.empty:
        st.error("Não foram encontrados dados para o paciente vinculado à sua conta.")
        st.stop()

base_total = len(base)
base_cost_total = float(base["custo_estimado"].sum())
min_date = base["data_ajuizamento"].min().date()
max_date = base["data_ajuizamento"].max().date()

# -----------------------------------------------------------------------------
# Sidebar e filtros
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown(
        '<div class="sidebar-logo"><div class="icon">⚖️➕</div><div class="title">SAÚDE PÚBLICA</div><div class="subtitle">Judicialização na Saúde</div></div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<div style='padding:.15rem 0 .55rem'><b>{escape(auth_user.name)}</b><br>"
        f"<span style='opacity:.82;font-size:.86rem'>{'Gestor' if auth_user.is_manager else 'Usuário'} · {escape(auth_user.cpf_display)}</span></div>",
        unsafe_allow_html=True,
    )
    if st.button("Sair", use_container_width=True, key="logout_button"):
        logout()

    if auth_user.is_manager:
        page_labels = ["Visão Geral", "Demandas", "Medicamentos", "Competência", "Custos", "Geografia", "Pacientes", "Base de Dados"]
        page_map = {label: label for label in page_labels}
    else:
        page_labels = ["Visão Geral", "Demandas", "Medicamentos", "Competência", "Custos", "Meu Perfil", "Meus Processos"]
        page_map = {
            "Visão Geral": "Visão Geral",
            "Demandas": "Demandas",
            "Medicamentos": "Medicamentos",
            "Competência": "Competência",
            "Custos": "Custos",
            "Meu Perfil": "Pacientes",
            "Meus Processos": "Base de Dados",
        }
    page_label = st.radio("Navegação", page_labels, label_visibility="collapsed")
    pagina = page_map[page_label]

    st.markdown("---")
    st.subheader("Filtros")
    st.markdown('<div class="sidebar-hint">Os gráficos e indicadores mudam automaticamente conforme os filtros.</div>', unsafe_allow_html=True)

    busca_paciente = ""
    paciente_ids_sel: list[str] = []
    if auth_user.is_manager:
        busca_paciente = st.text_input(
            "Buscar paciente / CPF / processo",
            placeholder="Ex.: Maria, PAC00042 ou PROC-2025",
            help="Esse campo procura em nome, código do paciente, CPF completo e número do processo.",
        )
        if len(normalize_text(busca_paciente)) >= 2:
            matches = base[base["_search"].str.contains(normalize_text(busca_paciente), regex=False, na=False)].copy()
            pessoas = (
                matches[["paciente_id", "paciente", "cpf"]]
                .drop_duplicates("paciente_id")
                .sort_values("paciente")
                .head(150)
            )
            label_to_id = {
                f"{row.paciente} — {row.paciente_id} — {row.cpf}": row.paciente_id
                for row in pessoas.itertuples(index=False)
            }
            escolhidos = st.multiselect("Selecionar paciente encontrado", list(label_to_id.keys()), placeholder="Opcional")
            paciente_ids_sel = [label_to_id[x] for x in escolhidos]
            if len(matches["paciente_id"].unique()) > 150:
                st.caption("Mostrando os 150 primeiros pacientes encontrados. Refine a busca para localizar um paciente específico.")
    else:
        paciente_ids_sel = [str(auth_user.patient_id)]
        st.caption("🔒 Seus dados estão limitados ao paciente vinculado à sua conta.")

    with st.expander("Filtros demográficos", expanded=False):
        sexo_sel = multiselect_sidebar("Sexo", base, "sexo")
        faixa_sel = multiselect_sidebar("Faixa etária", base, "faixa_etaria")
        condicao_sel = multiselect_sidebar("Condição clínica", base, "condicao_clinica")
        sus_sel = multiselect_sidebar("SUS exclusivo", base, "sus_exclusivo")
        renda_sel = multiselect_sidebar("Renda familiar", base, "renda_familiar")

    with st.expander("Filtros geográficos", expanded=False):
        regiao_sel = multiselect_sidebar("Região", base, "regiao")
        uf_sel = multiselect_sidebar("UF", base, "uf")
        mun_sel = multiselect_sidebar("Município", base, "municipio")

    with st.expander("Filtros processuais", expanded=False):
        natureza_sel = multiselect_sidebar("Natureza", base, "natureza")
        tipo_sel = multiselect_sidebar("Tipo de demanda", base, "tipo_demanda")
        item_sel = multiselect_sidebar("Item demandado", base, "item_demandado")
        esp_sel = multiselect_sidebar("Especialidade", base, "especialidade")
        esfera_sel = multiselect_sidebar("Esfera", base, "esfera")
        fase_sel = multiselect_sidebar("Fase processual", base, "fase_processual")
        desfecho_sel = multiselect_sidebar("Desfecho", base, "desfecho")
        liminar_sel = multiselect_sidebar("Liminar", base, "liminar")
        urgente_sel = multiselect_sidebar("Urgente", base, "urgente")

    med_ref = base[base["medicamento_judsaude"] == "Sim"]
    with st.expander("Filtros JudSaúde", expanded=False):
        dcb_sel = multiselect_sidebar("DCB / princípio ativo", med_ref, "medicamento_dcb")
        cid_sel = multiselect_sidebar("CID", med_ref, "cid")
        rename_sel = multiselect_sidebar("Incorporado à RENAME", med_ref, "rename_incorporado")
        componente_sel = multiselect_sidebar("Componente SUS", med_ref, "componente_sus")
        grupo_sel = multiselect_sidebar("Grupo de financiamento", med_ref, "grupo_sus")
        pcdt_sel = multiselect_sidebar("PCDT aplicável", med_ref, "pcdt_aplicavel")
        pcdt_ref_sel = multiselect_sidebar("PCDT de referência", med_ref, "pcdt_referencia")
        competencia_sel = multiselect_sidebar("Competência JudSaúde", med_ref, "competencia_judsaude")
        reu_sel = multiselect_sidebar("Réu sugerido", med_ref, "reu_sugerido")

    st.markdown("---")
    st.caption("Para limpar os filtros, desmarque as seleções ou recarregue a página.")


def apply_filters(df: pd.DataFrame) -> pd.DataFrame:
    d = df.copy()
    if isinstance(periodo_sel, tuple) and len(periodo_sel) == 2:
        inicio, fim = periodo_sel
        d = d[(d["data_ajuizamento"].dt.date >= inicio) & (d["data_ajuizamento"].dt.date <= fim)]

    query = normalize_text(busca_paciente)
    if query:
        d = d[d["_search"].str.contains(query, regex=False, na=False)]
    if paciente_ids_sel:
        d = d[d["paciente_id"].isin(paciente_ids_sel)]

    field_filters = {
        "sexo": sexo_sel,
        "faixa_etaria": faixa_sel,
        "condicao_clinica": condicao_sel,
        "sus_exclusivo": sus_sel,
        "renda_familiar": renda_sel,
        "regiao": regiao_sel,
        "uf": uf_sel,
        "municipio": mun_sel,
        "natureza": natureza_sel,
        "tipo_demanda": tipo_sel,
        "item_demandado": item_sel,
        "especialidade": esp_sel,
        "esfera": esfera_sel,
        "fase_processual": fase_sel,
        "desfecho": desfecho_sel,
        "liminar": liminar_sel,
        "urgente": urgente_sel,
        "medicamento_dcb": dcb_sel,
        "cid": cid_sel,
        "rename_incorporado": rename_sel,
        "componente_sus": componente_sel,
        "grupo_sus": grupo_sel,
        "pcdt_aplicavel": pcdt_sel,
        "pcdt_referencia": pcdt_ref_sel,
        "competencia_judsaude": competencia_sel,
        "reu_sugerido": reu_sel,
    }
    for col, selected in field_filters.items():
        if selected:
            d = d[d[col].astype(str).isin(selected)]
    return d


# -----------------------------------------------------------------------------
# Cabeçalho
# -----------------------------------------------------------------------------
subtitles = {
    "Visão Geral": "Indicadores executivos, evolução mensal e principais recortes.",
    "Demandas": "Análise de tipos de demanda, fase processual, liminares e urgência.",
    "Medicamentos": "Incorporação à RENAME, DCB, componente SUS, PCDT, PMVG e esquema posológico.",
    "Competência": "Competência judicial, réu sugerido e critério de custo anual alinhados ao JudSaúde.",
    "Custos": "Custos totais, ticket médio, medicamentos/insumos e especialidades mais caras.",
    "Geografia": "Distribuição por região, UF e município.",
    "Pacientes": "Perfil dos pacientes e busca individual.",
    "Base de Dados": "Tabela detalhada, exportação e conferência dos registros filtrados.",
}
if not auth_user.is_manager:
    subtitles["Pacientes"] = "Seu perfil e os processos vinculados à sua conta."
    subtitles["Base de Dados"] = "Seus processos detalhados e exportação dos seus próprios registros."

h1, h2, h3 = st.columns([7.7, 2.2, 1.8])
with h1:
    dashboard_title = "Dashboard de Judicialização na Saúde" if auth_user.is_manager else "Meus Dados — Judicialização na Saúde"
    st.markdown(f'<div class="title-main">{dashboard_title}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="title-sub">{subtitles[pagina]}</div>', unsafe_allow_html=True)
with h2:
    periodo_sel = st.date_input(
        "Período",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
        format="DD/MM/YYYY",
        label_visibility="collapsed",
        key="header_periodo",
    )
with h3:
    registros_header = st.empty()

dff = apply_filters(base)
registros_header.markdown(f'<div class="filter-pill">🔎&nbsp;&nbsp;{br_int(len(dff))} registros</div>', unsafe_allow_html=True)

if dff.empty:
    st.warning("Nenhum registro foi encontrado com os filtros selecionados. Ajuste ou limpe os filtros na barra lateral.")
    st.stop()

# -----------------------------------------------------------------------------
# KPIs baseados no filtro
# -----------------------------------------------------------------------------
def filtered_kpis(df: pd.DataFrame) -> dict[str, float]:
    total = len(df)
    pacientes = df["paciente_id"].nunique()
    custo = df["custo_estimado"].sum()
    ticket = df["custo_estimado"].mean() if total else 0
    tempo = df["tempo_tramitacao_dias"].mean() if total else 0
    liminar = pct((df["liminar"] == "Sim").sum(), total)
    urg = int((df["urgente"] == "Sim").sum())
    proced = pct(df["desfecho"].isin(["Procedente", "Parcialmente procedente"]).sum(), total)
    idade_media = df.drop_duplicates("paciente_id")["idade"].mean()
    mun = df["municipio"].nunique()
    return {
        "total": total,
        "pacientes": pacientes,
        "custo": custo,
        "ticket": ticket,
        "tempo": tempo,
        "liminar": liminar,
        "urgentes": urg,
        "procedencia": proced,
        "idade_media": idade_media,
        "municipios": mun,
    }

k = filtered_kpis(dff)
participacao = pct(len(dff), base_total)
part_custo = pct(k["custo"], base_cost_total)
from dashboard.views import render_pages

render_pages(
    pagina, dff, base, k, participacao, part_custo, paciente_ids_sel, auth_user.role,
)

st.markdown(
    '<div class="footer-note">ⓘ Dados fictícios para fins acadêmicos/demonstração. Os campos JudSaúde adicionados nesta versão são sintéticos e não substituem consulta oficial ao CNJ, RENAME ou CMED/Anvisa.</div>',
    unsafe_allow_html=True,
)
