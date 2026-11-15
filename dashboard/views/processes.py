from __future__ import annotations

import pandas as pd
import streamlit as st

from petsus.data.demo import normalize_text


PROCESS_COLUMNS = {
    "processo_id": "Processo",
    "paciente": "Requerente",
    "municipio": "Município",
    "item_demandado": "Assunto do processo",
    "fase_processual": "Fase processual",
    "etapa_judicial": "Andamento judicial",
    "etapa_saude": "Andamento na saúde",
    "desfecho": "Desfecho",
}


def process_list(base: pd.DataFrame, query: str = "") -> pd.DataFrame:
    rows = base.copy()
    if "ultima_movimentacao_data" in rows:
        rows = rows.sort_values("ultima_movimentacao_data", ascending=False, na_position="last")
    rows = rows.drop_duplicates("processo_id")
    view = rows.reindex(columns=list(PROCESS_COLUMNS)).fillna("Não informado")
    query = normalize_text(query)
    if query:
        searchable = view.astype(str).agg(" ".join, axis=1).map(normalize_text)
        view = view.loc[searchable.str.contains(query, regex=False)]
    return view.sort_values("processo_id").rename(columns=PROCESS_COLUMNS).reset_index(drop=True)


def render_processes(base: pd.DataFrame) -> None:
    st.subheader("Todos os processos")
    query = st.text_input(
        "Buscar processo", key="process_list_search",
        placeholder="Número, requerente, município, assunto ou andamento",
    )
    if base.empty:
        st.info("Ainda não há processos cadastrados.")
        return
    view = process_list(base, query)
    st.caption(f"{len(view)} de {base['processo_id'].nunique()} processos cadastrados")
    if view.empty:
        st.info("Nenhum processo encontrado para essa busca.")
        return
    st.dataframe(view, hide_index=True, use_container_width=True, height=600)
