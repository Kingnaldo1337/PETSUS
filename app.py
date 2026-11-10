from __future__ import annotations

import secrets

import pandas as pd
import streamlit as st

from dashboard.ui import br_int, multiselect_sidebar, pct
from petsus.auth.application import AuthStore, logout, render_auth_gate
from petsus.access import AccessScopeError, restrict_data_for_user
from petsus.config import (
    DATA_FILE,
    DATABASE_FILE,
    current_reference_date,
)
from petsus.data.filters import DashboardFilters, apply_filters as filter_data
from petsus.data.metrics import calculate_kpis
from petsus.dashboard.app_services import load_data, normalize_text
from petsus.governance import GovernanceStore
from petsus.dashboard.accessibility import render_accessibility_controls
from petsus.dashboard.patient import render_patient_page
from petsus.dashboard.patient_ui import icon, render_portal_header, render_portal_navigation, render_portal_sidebar, render_portal_styles
from petsus.dashboard.support import data_metadata, render_support_page
from petsus.dashboard.navigation import navigation_for, subtitle_for
from dashboard.views import render_pages as render_dashboard_page

st.set_page_config(
    page_title="Dashboard de Judicialização na Saúde",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -----------------------------------------------------------------------------
# Estilo visual
# -----------------------------------------------------------------------------
st.markdown(
    """
    <style>
        html, body, .stApp { font-family: 'Inter', 'Segoe UI', Arial, sans-serif; }
        .stApp input,.stApp textarea,.stApp button {font-family:inherit;}
        .stApp, [data-testid="stAppViewContainer"], .main { background: #F4F7FB; color: #0B2459; }
        [data-testid="stHeader"] { background: transparent; }
        .block-container { max-width: 1700px; padding-top: 1.05rem; padding-bottom: 1.2rem; padding-left: 1.2rem; padding-right: 1.2rem; container-type: inline-size; container-name: dashboard; }
        [data-testid="stSidebar"] { background: linear-gradient(180deg, #083E82 0%, #072F66 52%, #061F45 100%); }
        [data-testid="stSidebar"] * { color: white; }
        /* Mantém os ícones de ajuda legíveis sobre o fundo azul da barra lateral. */
        [data-testid="stSidebar"] [data-testid="stTooltipIcon"],
        [data-testid="stSidebar"] [data-testid="stTooltipIcon"] button {
            color: #FFFFFF !important;
            opacity: 1 !important;
        }
        [data-testid="stSidebar"] [data-testid="stTooltipIcon"] svg {
            color: #FFFFFF !important;
            fill: none !important;
            stroke: #FFFFFF !important;
            opacity: 1 !important;
            filter: drop-shadow(0 1px 2px rgba(0, 0, 0, .28));
        }
        [data-testid="stSidebar"] [data-testid="stTooltipIcon"] svg path {
            fill: none !important;
            stroke: #FFFFFF !important;
            stroke-width: 2 !important;
            stroke-linecap: round !important;
            stroke-linejoin: round !important;
        }
        [data-testid="stSidebar"] [data-testid="stTooltipIcon"] svg circle {
            fill: none !important;
            stroke: #FFFFFF !important;
        }
        /* Expansores dos grupos de filtros: mantém contraste abertos e fechados. */
        [data-testid="stSidebar"] [data-testid="stExpander"] details,
        [data-testid="stSidebar"] [data-testid="stExpander"] details[open] {
            background: transparent !important;
            border-color: rgba(255, 255, 255, .34) !important;
        }
        [data-testid="stSidebar"] [data-testid="stExpander"] summary,
        [data-testid="stSidebar"] [data-testid="stExpander"] details[open] summary {
            background: rgba(255, 255, 255, .12) !important;
            color: #FFFFFF !important;
            border-radius: .5rem !important;
        }
        [data-testid="stSidebar"] [data-testid="stExpander"] summary:hover {
            background: rgba(255, 255, 255, .20) !important;
        }
        [data-testid="stSidebar"] [data-testid="stExpander"] summary *,
        [data-testid="stSidebar"] [data-testid="stExpander"] summary svg,
        [data-testid="stSidebar"] [data-testid="stExpander"] summary svg path {
            color: #FFFFFF !important;
            fill: #FFFFFF !important;
            stroke: #FFFFFF !important;
            opacity: 1 !important;
        }
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
        [data-testid="stSidebar"] .st-key-clear_filters_button button {
            background: rgba(255, 255, 255, .14) !important;
            border: 1px solid rgba(255, 255, 255, .55) !important;
            color: #FFFFFF !important;
            font-weight: 800;
        }
        [data-testid="stSidebar"] .st-key-clear_filters_button button p,
        [data-testid="stSidebar"] .st-key-clear_filters_button button span {
            color: #FFFFFF !important;
        }
        [data-testid="stSidebar"] .st-key-clear_filters_button button:hover,
        [data-testid="stSidebar"] .st-key-clear_filters_button button:focus {
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
        .card-help { position: relative; margin-left: auto; width: 22px; height: 22px; min-width: 22px; border: 1.5px solid #125CC9; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; color: #125CC9 !important; background: #FFFFFF; font-size: .78rem; font-weight: 900; line-height: 1; cursor: help; }
        .card-help:hover::after, .card-help:focus::after { content: attr(data-help); position: absolute; z-index: 9999; top: calc(100% + 8px); right: 0; width: min(260px, 70vw); padding: .65rem .75rem; border-radius: 10px; background: #0B2459; color: #FFFFFF; font-size: .78rem; font-weight: 500; line-height: 1.35; text-align: left; white-space: normal; box-shadow: 0 8px 22px rgba(11,36,89,.22); }
        .card-help:focus { outline: 2px solid #93C5FD; outline-offset: 2px; }
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
        .insight-title { display:flex; align-items:center; gap:.45rem; font-size: .92rem; color: #31456F; font-weight: 800; margin-bottom: .35rem; }
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
DATA_SCHEMA_VERSION = "feedback-v4"
REFERENCE_DATE = current_reference_date().isoformat()
base_all = load_data(
    DATA_FILE, DATA_FILE.stat().st_mtime_ns if DATA_FILE.exists() else 0,
    DATA_SCHEMA_VERSION, REFERENCE_DATE,
)
auth_store = AuthStore(DATABASE_FILE)
auth_user = render_auth_gate(auth_store, base_all)
render_accessibility_controls(show_sidebar=False)
try:
    base = restrict_data_for_user(base_all, auth_user)
except AccessScopeError as exc:
    st.error(str(exc))
    # Uma falha no vínculo mantém ajuda e saída disponíveis, sem liberar dados.
    base = base_all.iloc[0:0].copy()

governance = GovernanceStore(DATABASE_FILE)
metadata = data_metadata(DATA_FILE)
render_portal_styles(is_manager=auth_user.is_manager)

FILTER_GROUPS = {
    "Filtros demográficos": (
        ("Sexo", "sexo"), ("Faixa etária", "faixa_etaria"),
        ("Condição clínica", "condicao_clinica"), ("SUS exclusivo", "sus_exclusivo"),
        ("Renda familiar", "renda_familiar"),
    ),
    "Filtros geográficos": (("Região", "regiao"), ("UF", "uf"), ("Município", "municipio")),
    "Filtros processuais": (
        ("Natureza", "natureza"), ("Tipo de demanda", "tipo_demanda"),
        ("Item demandado", "item_demandado"), ("Especialidade", "especialidade"),
        ("Esfera judicial", "esfera"), ("Fase processual", "fase_processual"),
        ("Desfecho", "desfecho"), ("Liminar concedida", "liminar"), ("Pedido urgente", "urgente"),
        ("Causa da judicialização", "causa_judicializacao"),
    ),
    "Filtros de andamento": (
        ("Etapa judicial", "etapa_judicial"), ("Cumprimento na saúde", "etapa_saude"),
        ("Status do acompanhamento", "status_andamento"), ("Prazo vencido", "indicador_atraso"),
    ),
    "Filtros de medicamentos": (
        ("Princípio ativo (DCB)", "medicamento_dcb"), ("Código da doença (CID)", "cid"),
        ("Incorporado à RENAME", "rename_incorporado"), ("Componente SUS", "componente_sus"),
        ("Grupo de financiamento", "grupo_sus"), ("Protocolo aplicável (PCDT)", "pcdt_aplicavel"),
        ("Protocolo de referência", "pcdt_referencia"), ("Competência judicial", "competencia_petsus"),
        ("Réu sugerido", "reu_sugerido"),
    ),
}
FILTER_WIDGET_KEYS = (
    "filter_search", "filter_patients", "header_periodo",
    *(f"filter_{column}" for fields in FILTER_GROUPS.values() for _, column in fields),
)


def clear_dashboard_filters() -> None:
    for key in FILTER_WIDGET_KEYS:
        st.session_state.pop(key, None)


selected_fields = {}
selected_patient_ids = []
search = ""
with st.sidebar:
    render_portal_sidebar(auth_user)
    page_labels, page_map = navigation_for(auth_user.is_manager)
    page_label = render_portal_navigation(page_labels)
    pagina = page_map[page_label]
    if not auth_user.is_manager:
        st.markdown(f'<div class="patient-sidebar-note">{icon("lock",13)} Um espaço seguro para acompanhar os seus pedidos.</div>', unsafe_allow_html=True)
    if auth_user.is_manager and pagina not in ("Gestão interna", "Ajuda e feedback"):
        st.divider()
        st.markdown('<div class="patient-sidebar-label">REFINAR ANÁLISE</div><div class="manager-filter-caption">Ajuste os filtros para explorar os indicadores.</div>', unsafe_allow_html=True)
        st.button("Limpar todos os filtros", key="clear_filters_button", on_click=clear_dashboard_filters, use_container_width=True)
        search = st.text_input("Buscar paciente / CPF / processo", key="filter_search", placeholder="Nome, código ou número do processo")
        if len(normalize_text(search)) >= 2:
            matches = base[base["_search"].str.contains(normalize_text(search), regex=False, na=False)]
            people = matches[["paciente_id", "paciente", "cpf"]].drop_duplicates("paciente_id").sort_values("paciente").head(150)
            labels = {f"{row.paciente} · {row.paciente_id} · {AuthStore.mask_cpf(row.cpf)}": str(row.paciente_id) for row in people.itertuples(index=False)}
            chosen = st.multiselect("Selecionar paciente encontrado", list(labels), key="filter_patients", placeholder="Opcional")
            selected_patient_ids = [labels[value] for value in chosen]
            st.caption("Resultados analíticos de grupos com menos de cinco pacientes são protegidos. Use Andamento para a consulta operacional de um processo.")
        for group, fields in FILTER_GROUPS.items():
            page_groups = {
                "Visão Geral": {"Filtros processuais"},
                "Andamento": {"Filtros processuais", "Filtros de andamento"},
                "Demandas": {"Filtros processuais"},
                "Medicamentos": {"Filtros de medicamentos"},
                "Competência": {"Filtros de medicamentos", "Filtros geográficos"},
                "Custos": {"Filtros processuais", "Filtros de medicamentos"},
                "Prevenção": {"Filtros processuais", "Filtros geográficos"},
                "Geografia": {"Filtros geográficos"},
                "Pacientes": {"Filtros demográficos", "Filtros geográficos"},
            }
            if group not in page_groups.get(pagina, set(FILTER_GROUPS)):
                continue
            with st.expander(group):
                source = base[base["medicamento_petsus"] == "Sim"] if group == "Filtros de medicamentos" else base
                for label, column in fields:
                    if column in source.columns:
                        selected_fields[column] = tuple(multiselect_sidebar(label, source, column))
    if st.button("Sair", use_container_width=True, key="logout_button"):
        logout()

render_portal_header(page_label, subtitle_for(pagina, auth_user.is_manager), metadata, REFERENCE_DATE, is_manager=auth_user.is_manager)
visit_token = st.session_state.setdefault("usage_visit_token", secrets.token_urlsafe(24))
governance.record_page_view(auth_user.role, pagina, visit_token)

if pagina == "Ajuda e feedback":
    render_support_page(auth_user, governance, base, metadata)
elif not auth_user.is_manager:
    render_patient_page(pagina, base)
else:
    dff = base
    if pagina != "Gestão interna":
        if base.empty:
            st.info("Não há registros disponíveis.")
            st.stop()
        min_date = base["data_ajuizamento"].min().date()
        max_date = base["data_ajuizamento"].max().date()
        with st.container(key="manager_filterbar"):
            period_column, count_column = st.columns([3, 1], vertical_alignment="bottom")
            with period_column:
                dates = st.date_input("Período de ajuizamento", value=(min_date, max_date), min_value=min_date, max_value=max_date, format="DD/MM/YYYY", key="header_periodo", help="Seleciona a data de entrada dos processos. Os cálculos usam a referência indicada no cabeçalho, sem reconstruir uma situação histórica.")
        if isinstance(dates, (tuple, list)):
            start, end = (dates[0], dates[-1]) if dates else (min_date, max_date)
        else:
            start = end = dates
        dff = filter_data(base, DashboardFilters(start_date=start, end_date=end, search=normalize_text(search), patient_ids=tuple(selected_patient_ids), fields=selected_fields))
        with count_column:
            protected = pagina != "Andamento" and dff["paciente_id"].nunique() < 5
            count_label = "Contagem protegida" if protected and not dff.empty else f"{br_int(len(dff))} registros"
            st.markdown(f'<div class="filter-pill">{count_label}</div>', unsafe_allow_html=True)
        if dff.empty:
            st.warning("Nenhum registro encontrado. Ajuste ou limpe os filtros.")
            st.stop()
    k = calculate_kpis(dff)
    render_dashboard_page(pagina, dff, base, k, pct(len(dff), len(base)), pct(k["custo"], base["custo_estimado"].sum()), selected_patient_ids, auth_store=auth_store)

st.markdown(f'<div class="patient-footer">{icon("lock",12)} DASHJUS · Judicialização na Saúde</div>', unsafe_allow_html=True)
