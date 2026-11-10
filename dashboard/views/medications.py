from __future__ import annotations

from html import escape

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from ..charts import barh, chart_layout, empty_fig, monthly_line, top_group
from ..ui import br_float, br_int, br_money, citizen_glossary_expander, citizen_legal_contacts_card, display_columns, insight_card, metric_card, pct, section_title, to_excel_bytes
from petsus.reports.process_tracking_pdf import build_process_tracking_pdf

LIMITE_210_SM_2026 = 210 * 1621.0

def render_medications(dff, base, k, participacao, part_custo, paciente_ids_sel):
    med = dff[dff["medicamento_petsus"] == "Sim"].copy()
    st.info(
        "Campos de análise de medicamentos do PetSUS. "
        "Nesta base acadêmica, os valores de RENAME, PMVG, PCDT, posologia e competência são sintéticos e servem somente para demonstração do dashboard."
    )
    if med.empty:
        st.warning("Nenhuma demanda de medicamento foi encontrada com os filtros selecionados.")
    else:
        incorporados = int((med["rename_incorporado"] == "Sim").sum())
        cols = st.columns(5)
        cards = [
            ("Demandas de medicamentos", br_int(len(med)), "registros compatíveis com a análise PetSUS", "💊", "icon-blue"),
            ("DCB distintos", br_int(med["medicamento_dcb"].nunique()), "princípios ativos no recorte", "🧪", "icon-purple"),
            ("Incorporados à RENAME", f"{br_float(pct(incorporados, len(med)))}%", f"{br_int(incorporados)} registros", "✅", "icon-green"),
            ("PMVG médio", br_money(med["pmvg_referencia"].mean()), "preço de referência sintético por administração", "$", "icon-orange"),
            ("Valor anual estimado", br_money(med["valor_anual_tratamento"].sum()), "PMVG de referência anualizado; não é gasto efetivo", "📈", "icon-green"),
        ]
        for col, card in zip(cols, cards):
            with col:
                metric_card(*card)

        a, b, c = st.columns([1.0, 1.35, 1.0])
        with a:
            with st.container(border=True):
                section_title("Incorporação à RENAME")
                ren = med.groupby("rename_incorporado", as_index=False).size().rename(columns={"size": "processos"})
                ren["texto"] = ren["processos"].map(br_int)
                st.plotly_chart(barh(ren, "rename_incorporado", "processos", "texto", height=330), use_container_width=True, config={"displayModeBar": False})
        with b:
            with st.container(border=True):
                section_title("Componente de financiamento SUS")
                comp = top_group(med, "componente_sus", "processo_id", 8, "count")
                comp["texto"] = comp["valor"].map(br_int)
                st.plotly_chart(barh(comp, "componente_sus", "valor", "texto", height=330, color="#39A74A"), use_container_width=True, config={"displayModeBar": False})
        with c:
            with st.container(border=True):
                section_title("PCDT aplicável")
                pcdt = med.groupby("pcdt_aplicavel", as_index=False).size().rename(columns={"size": "processos"})
                pcdt["texto"] = pcdt["processos"].map(br_int)
                st.plotly_chart(barh(pcdt, "pcdt_aplicavel", "processos", "texto", height=330), use_container_width=True, config={"displayModeBar": False})

        d, e, f = st.columns([1.2, 1.2, 1.35])
        with d:
            with st.container(border=True):
                section_title("DCB mais demandadas")
                top_dcb = top_group(med, "medicamento_dcb", "processo_id", 10, "count")
                top_dcb["texto"] = top_dcb["valor"].map(br_int)
                st.plotly_chart(barh(top_dcb, "medicamento_dcb", "valor", "texto", height=350), use_container_width=True, config={"displayModeBar": False})
        with e:
            with st.container(border=True):
                section_title("Maior impacto anual por DCB")
                top_val = top_group(med, "medicamento_dcb", "valor_anual_tratamento", 10, "sum")
                top_val["texto"] = top_val["valor"].map(br_money)
                st.plotly_chart(barh(top_val, "medicamento_dcb", "valor", "texto", height=350, color="#7C3AED"), use_container_width=True, config={"displayModeBar": False})
        with f:
            with st.container(border=True):
                section_title("Resumo farmacêutico")
                tab = med.groupby("medicamento_dcb", as_index=False).agg(
                    demandas=("processo_id", "count"),
                    incorporados=("rename_incorporado", lambda s: int((s == "Sim").sum())),
                    pmvg_medio=("pmvg_referencia", "mean"),
                    valor_anual=("valor_anual_tratamento", "sum"),
                ).sort_values("demandas", ascending=False).head(12)
                tab["% RENAME"] = tab.apply(lambda r: f"{br_float(pct(r['incorporados'], r['demandas']))}%", axis=1)
                tab["pmvg_medio"] = tab["pmvg_medio"].map(lambda x: br_money(x, compact=False))
                tab["valor_anual"] = tab["valor_anual"].map(br_money)
                st.dataframe(display_columns(tab[["medicamento_dcb", "demandas", "% RENAME", "pmvg_medio", "valor_anual"]].rename(columns={
                    "demandas": "Demandas", "pmvg_medio": "PMVG médio", "valor_anual": "Valor anual do tratamento (PMVG)"
                })), hide_index=True, use_container_width=True, height=350)

        with st.container(border=True):
            section_title("Detalhamento PetSUS")
            detail_cols = [
                "processo_id", "cid", "medicamento_dcb", "apresentacao_padronizada", "rename_incorporado",
                "componente_sus", "grupo_sus", "pcdt_aplicavel", "pcdt_referencia", "dose_prescrita", "frequencia_administracao",
                "duracao_meses", "pmvg_referencia", "valor_anual_tratamento",
            ]
            det = med[detail_cols].sort_values("valor_anual_tratamento", ascending=False).head(200)
            st.dataframe(display_columns(det), hide_index=True, use_container_width=True, height=360, column_config={
                "PMVG de referência": st.column_config.NumberColumn("PMVG de referência", format="R$ %.2f"),
                "Valor anual do tratamento (PMVG)": st.column_config.NumberColumn("Valor anual do tratamento (PMVG)", format="R$ %.2f"),
            })
