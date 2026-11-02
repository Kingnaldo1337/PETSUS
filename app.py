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
from petsus.auth.application import AuthStore, logout, render_auth_gate
from petsus.access import AccessScopeError, restrict_data_for_user
from petsus.config import (
    DATA_FILE,
    DATABASE_FILE,
    LIMITE_210_SM_2026,
    REQUIRED_COLUMNS,
)
from petsus.data.filters import DashboardFilters, apply_filters as filter_data
from petsus.data.loader import DataLoadError, load_process_data
from petsus.data.metrics import calculate_kpis
from petsus.dashboard.navigation import navigation_for, subtitle_for
from petsus.dashboard.app_services import (_attach_full_cpf, _cpf_digits, _cpf_checksum_valid, _format_cpf, enrich_petsus_fields, enrich_process_tracking, extract_dcb, load_data, stable_choice, stable_int, normalize_text)
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
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');
        html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
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
FILTER_WIDGET_KEYS = (
    "filter_search", "filter_patients", "header_periodo",
    "filter_sexo", "filter_faixa_etaria", "filter_condicao_clinica",
    "filter_sus_exclusivo", "filter_renda_familiar", "filter_regiao",
    "filter_uf", "filter_municipio", "filter_natureza",
    "filter_tipo_demanda", "filter_item_demandado", "filter_especialidade",
    "filter_esfera", "filter_fase_processual", "filter_desfecho",
    "filter_liminar", "filter_urgente", "filter_etapa_judicial",
    "filter_etapa_saude", "filter_status_andamento", "filter_indicador_atraso",
    "filter_medicamento_dcb", "filter_cid", "filter_rename_incorporado",
    "filter_componente_sus", "filter_grupo_sus", "filter_pcdt_aplicavel",
    "filter_pcdt_referencia", "filter_competencia_petsus", "filter_reu_sugerido",
)


def clear_dashboard_filters() -> None:
    for widget_key in FILTER_WIDGET_KEYS:
        st.session_state.pop(widget_key, None)


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

    page_labels, page_map = navigation_for(auth_user.is_manager)
    page_label = st.radio("Navegação", page_labels, label_visibility="collapsed")
    pagina = page_map[page_label]

    busca_paciente = ""
    paciente_ids_sel: list[str] = []
    processo_paciente_sel: list[str] = []

    if auth_user.is_manager:
        st.markdown("---")
        st.subheader("Filtros")
        st.markdown('<div class="sidebar-hint">Os gráficos e indicadores mudam automaticamente conforme os filtros.</div>', unsafe_allow_html=True)
        st.button(
            "Limpar todos os filtros",
            key="clear_filters_button",
            on_click=clear_dashboard_filters,
            use_container_width=True,
            help="Restaura a busca, o período e todas as seleções de filtros.",
        )

        busca_paciente = st.text_input(
            "Buscar paciente / CPF / processo",
            key="filter_search",
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
            escolhidos = st.multiselect(
                "Selecionar paciente encontrado",
                list(label_to_id.keys()),
                key="filter_patients",
                placeholder="Opcional",
                help="Seleciona um ou mais pacientes encontrados para limitar todos os indicadores e tabelas aos seus processos.",
            )
            paciente_ids_sel = [label_to_id[x] for x in escolhidos]
            if len(matches["paciente_id"].unique()) > 150:
                st.caption("Mostrando os 150 primeiros pacientes encontrados. Refine a busca para localizar um paciente específico.")

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

        with st.expander("Filtros de andamento", expanded=False):
            etapa_judicial_sel = multiselect_sidebar("Etapa judicial", base, "etapa_judicial")
            etapa_saude_sel = multiselect_sidebar("Cumprimento na saúde", base, "etapa_saude")
            status_andamento_sel = multiselect_sidebar("Status do acompanhamento", base, "status_andamento")
            atraso_sel = multiselect_sidebar("Prazo vencido", base, "indicador_atraso")

        med_ref = base[base["medicamento_petsus"] == "Sim"]
        with st.expander("Filtros PetSUS", expanded=False):
            dcb_sel = multiselect_sidebar("DCB / princípio ativo", med_ref, "medicamento_dcb")
            cid_sel = multiselect_sidebar("CID", med_ref, "cid")
            rename_sel = multiselect_sidebar("Incorporado à RENAME", med_ref, "rename_incorporado")
            componente_sel = multiselect_sidebar("Componente SUS", med_ref, "componente_sus")
            grupo_sel = multiselect_sidebar("Grupo de financiamento", med_ref, "grupo_sus")
            pcdt_sel = multiselect_sidebar("PCDT aplicável", med_ref, "pcdt_aplicavel")
            pcdt_ref_sel = multiselect_sidebar("PCDT de referência", med_ref, "pcdt_referencia")
            competencia_sel = multiselect_sidebar("Competência PetSUS", med_ref, "competencia_petsus")
            reu_sel = multiselect_sidebar("Réu sugerido", med_ref, "reu_sugerido")

        st.markdown("---")
        st.caption("Use o botão acima para restaurar todos os filtros.")
    else:
        paciente_ids_sel = [str(auth_user.patient_id)]
        st.markdown("---")
        st.caption("🔒 **Área do Paciente**")
        st.markdown(
            '<div class="sidebar-hint">Seus dados e processos estão protegidos e restritos ao seu perfil pessoal.</div>',
            unsafe_allow_html=True,
        )
        processos_paciente = sorted(base["processo_id"].dropna().unique().tolist())
        if len(processos_paciente) > 1:
            escolha = st.selectbox(
                "Filtrar por processo",
                ["Todos os meus processos"] + processos_paciente,
                key="filtro_processo_paciente",
                help="Selecione um processo específico para visualizar.",
            )
            if escolha != "Todos os meus processos":
                processo_paciente_sel = [escolha]

        sexo_sel = []
        faixa_sel = []
        condicao_sel = []
        sus_sel = []
        renda_sel = []
        regiao_sel = []
        uf_sel = []
        mun_sel = []
        natureza_sel = []
        tipo_sel = []
        item_sel = []
        esp_sel = []
        esfera_sel = []
        fase_sel = []
        desfecho_sel = []
        liminar_sel = []
        urgente_sel = []
        etapa_judicial_sel = []
        etapa_saude_sel = []
        status_andamento_sel = []
        atraso_sel = []
        dcb_sel = []
        cid_sel = []
        rename_sel = []
        componente_sel = []
        grupo_sel = []
        pcdt_sel = []
        pcdt_ref_sel = []
        competencia_sel = []
        reu_sel = []


# -----------------------------------------------------------------------------
# Cabeçalho
# -----------------------------------------------------------------------------
h1, h2, h3 = st.columns([7.7, 2.2, 1.8])
with h1:
    dashboard_title = "Dashboard de Judicialização na Saúde" if auth_user.is_manager else "Meus Dados — Judicialização na Saúde"
    st.markdown(f'<div class="title-main">{dashboard_title}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="title-sub">{subtitle_for(pagina, auth_user.is_manager)}</div>', unsafe_allow_html=True)
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

period_start, period_end = (
    periodo_sel if isinstance(periodo_sel, tuple) else (periodo_sel, periodo_sel)
)
active_filters = DashboardFilters(
    start_date=period_start,
    end_date=period_end,
    search=normalize_text(busca_paciente),
    patient_ids=tuple(str(value) for value in paciente_ids_sel),
    fields={
        "processo_id": tuple(processo_paciente_sel),
        "sexo": tuple(sexo_sel), "faixa_etaria": tuple(faixa_sel),
        "condicao_clinica": tuple(condicao_sel), "sus_exclusivo": tuple(sus_sel),
        "renda_familiar": tuple(renda_sel), "regiao": tuple(regiao_sel),
        "uf": tuple(uf_sel), "municipio": tuple(mun_sel),
        "natureza": tuple(natureza_sel), "tipo_demanda": tuple(tipo_sel),
        "item_demandado": tuple(item_sel), "especialidade": tuple(esp_sel),
        "esfera": tuple(esfera_sel), "fase_processual": tuple(fase_sel),
        "desfecho": tuple(desfecho_sel), "liminar": tuple(liminar_sel),
        "urgente": tuple(urgente_sel), "etapa_judicial": tuple(etapa_judicial_sel),
        "etapa_saude": tuple(etapa_saude_sel), "status_andamento": tuple(status_andamento_sel),
        "indicador_atraso": tuple(atraso_sel), "medicamento_dcb": tuple(dcb_sel),
        "cid": tuple(cid_sel), "rename_incorporado": tuple(rename_sel),
        "componente_sus": tuple(componente_sel), "grupo_sus": tuple(grupo_sel),
        "pcdt_aplicavel": tuple(pcdt_sel), "pcdt_referencia": tuple(pcdt_ref_sel),
        "competencia_petsus": tuple(competencia_sel), "reu_sugerido": tuple(reu_sel),
    },
)
dff = filter_data(base, active_filters)
registros_header.markdown(f'<div class="filter-pill">🔎&nbsp;&nbsp;{br_int(len(dff))} registros</div>', unsafe_allow_html=True)

if dff.empty:
    st.warning("Nenhum registro foi encontrado com os filtros selecionados. Ajuste ou limpe os filtros na barra lateral.")
    st.stop()

# -----------------------------------------------------------------------------
# KPIs baseados no filtro
# -----------------------------------------------------------------------------
k = calculate_kpis(dff)
participacao = pct(len(dff), base_total)
part_custo = pct(k["custo"], base_cost_total)
render_dashboard_page(
    pagina, dff, base, k, participacao, part_custo, paciente_ids_sel,
    auth_store=auth_store,
)

st.markdown(
    '<div class="footer-note">ⓘ Dados fictícios para fins acadêmicos/demonstração. Os campos PetSUS adicionados nesta versão são sintéticos e não substituem consulta oficial ao CNJ, RENAME ou CMED/Anvisa.</div>',
    unsafe_allow_html=True,
)
