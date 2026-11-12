from __future__ import annotations

import streamlit as st

from .shared import (
    JUDICIAL_TRACK,
    LABELS,
    MIN_PATIENTS,
    _cards,
    _cost_definitions,
    _count,
    _distribution,
    _medication_subset,
    _plot,
    _publishable_subset,
    _ranking,
    _rate,
    _table,
    judgment_summary,
    mask_cpf,
    mask_personal_data,
    protected_aggregate,
    tracking_bar,
)
from .overview import _render_overview, render_overview
from .progress import _render_tracking, render_progress
from .demands import _render_demands, render_demands
from .medications import _render_medications, render_medications
from .competence import _render_responsibility_detail, _render_competency, render_competence
from .costs import _render_costs, render_costs
from .geography import _render_geography, render_geography
from .patients import _render_patients, render_patients
from .prevention import _render_prevention, render_prevention
from .base_data import _render_database, render_base_data


def render_pages(pagina, dff, base, k, participacao, part_custo, paciente_ids_sel, auth_store=None):
    auth_state = st.session_state.get("auth_user", {})
    role = auth_state.get("role") if isinstance(auth_state, dict) else None
    if role != "gestor":
        st.error("Esta visão analítica é restrita a gestores.")
        return
    if pagina == "Gestão interna":
        if not isinstance(auth_state, dict) or auth_state.get("role") != "gestor" or auth_store is None:
            st.error("Esta página é restrita a gestores.")
            return
        from petsus.dashboard.internal_management import render_internal_management
        render_internal_management(auth_store)
        return
    if dff.empty:
        st.info("Nenhum processo encontrado para os filtros selecionados.")
        return
    if pagina == "Andamento":
        _render_tracking(dff)
        return
    if dff["paciente_id"].nunique() < MIN_PATIENTS:
        st.warning("Recorte protegido: são necessários pelo menos 5 pacientes distintos para exibir indicadores, gráficos, tabelas ou exportações. Amplie os filtros.")
        return
    if pagina == "Visão Geral":
        _render_overview(dff, base, k, participacao, part_custo)
    elif pagina == "Demandas":
        _render_demands(dff, k)
    elif pagina == "Medicamentos":
        _render_medications(dff)
    elif pagina == "Competência":
        _render_competency(dff)
    elif pagina == "Custos":
        _render_costs(dff, k, part_custo)
    elif pagina == "Geografia":
        _render_geography(dff, k)
    elif pagina == "Pacientes":
        _render_patients(dff)
    elif pagina in {"Prevenção", "Prevenção de Judicialização", "Prevenção de judicialização"}:
        _render_prevention(dff)
    elif pagina == "Base de Dados":
        _render_database(dff)
