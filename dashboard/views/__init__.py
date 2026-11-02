from __future__ import annotations

import streamlit as st

from .views.overview import render_overview
from .views.progress import render_progress
from .views.demands import render_demands
from .views.medications import render_medications
from .views.competence import render_competence
from .views.costs import render_costs
from .views.geography import render_geography
from .views.patients import render_patients

def render_pages(pagina, dff, base, k, participacao, part_custo, paciente_ids_sel, auth_store=None):
    auth_state = st.session_state.get("auth_user", {})
    user_role = auth_state.get("role", "gestor") if isinstance(auth_state, dict) else "gestor"
    if user_role == "usuario" and pagina in ("Demandas", "Medicamentos", "Competencia", "Competência", "Custos", "Geografia", "Gestão interna", "Pacientes"):
        st.warning("Esta página é de acesso exclusivo para gestores da saúde.")
        return
    if pagina == "Gestão interna":
        manager_session = isinstance(auth_state, dict) and auth_state.get("role") == "gestor"
        if not manager_session or auth_store is None:
            st.error("Esta página é restrita a gestores.")
            return
        from petsus.dashboard.internal_management import render_internal_management
        render_internal_management(auth_store)
        return
    if pagina == "Visão Geral":
        render_overview(dff, base, k, participacao, part_custo, paciente_ids_sel)
    elif pagina == "Andamento":
        render_progress(dff, base, paciente_ids_sel)
    elif pagina == "Demandas":
        render_demands(dff, base, k, participacao, part_custo, paciente_ids_sel)
    elif pagina == "Medicamentos":
        render_medications(dff, base, k, participacao, part_custo, paciente_ids_sel)
    elif pagina == "Competência":
        render_competence(dff, base, k, participacao, part_custo, paciente_ids_sel)
    elif pagina == "Custos":
        render_costs(dff, base, k, participacao, part_custo, paciente_ids_sel)
    elif pagina == "Geografia":
        render_geography(dff, base, k, participacao, part_custo, paciente_ids_sel)
    elif pagina == "Pacientes":
        render_patients(dff, base, k, participacao, part_custo, paciente_ids_sel)
    else:
        from .views.base_data import render_base_data
        render_base_data(dff, base, k, participacao, part_custo, paciente_ids_sel)
