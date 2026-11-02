from __future__ import annotations

from html import escape

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from ..charts import barh, chart_layout, donut, empty_fig, monthly_line, top_group
from ..ui import br_float, br_int, br_money, citizen_glossary_expander, citizen_legal_contacts_card, insight_card, metric_card, pct, section_title, to_excel_bytes
from petsus.reports.process_tracking_pdf import build_process_tracking_pdf

LIMITE_210_SM_2026 = 210 * 1621.0

def render_geography(dff, base, k, participacao, part_custo, paciente_ids_sel):
    cols = st.columns(5)
    reg_top = top_group(dff, "regiao", "processo_id", 1, "count")
    uf_top = top_group(dff, "uf", "processo_id", 1, "count")
    mun_top = top_group(dff, "municipio", "processo_id", 1, "count")
    cards = [
        ("Municípios", br_int(k["municipios"]), "municípios no recorte", "📍", "icon-blue"),
        ("Região Líder", reg_top["regiao"].iloc[0] if not reg_top.empty else "-", "maior volume", "🗺️", "icon-green"),
        ("UF Líder", uf_top["uf"].iloc[0] if not uf_top.empty else "-", "maior volume", "🏛️", "icon-purple"),
        ("Município Líder", mun_top["municipio"].iloc[0] if not mun_top.empty else "-", "maior volume", "🏙️", "icon-orange"),
        ("Custo per capita", br_money(k["custo"] / max(k["pacientes"], 1)), "por paciente filtrado", "$", "icon-green"),
    ]
    for col, card in zip(cols, cards):
        with col:
            metric_card(*card)

    a, b = st.columns([1.45, 1.1])
    with a:
        with st.container(border=True):
            section_title("Mapa dos municípios filtrados")
            geo = dff.groupby(["municipio", "uf", "regiao", "latitude", "longitude"], as_index=False).agg(
                processos=("processo_id", "count"),
                pacientes=("paciente_id", "nunique"),
                custo_total=("custo_estimado", "sum"),
            )
            geo = geo.dropna(subset=["latitude", "longitude"])
            if geo.empty:
                st.plotly_chart(empty_fig("Sem coordenadas para o recorte", height=390), use_container_width=True, config={"displayModeBar": False})
            else:
                fig = px.scatter_geo(
                    geo,
                    lat="latitude",
                    lon="longitude",
                    size="processos",
                    color="regiao",
                    hover_name="municipio",
                    hover_data={"uf": True, "processos": True, "pacientes": True, "custo_total": ":,.2f", "latitude": False, "longitude": False},
                    height=390,
                )
                fig.update_geos(
                    showcountries=True,
                    countrycolor="#CBD5E1",
                    showland=True,
                    landcolor="#F4F7FB",
                    showocean=True,
                    oceancolor="#E8F2FB",
                    fitbounds="locations",
                )
                fig.update_layout(margin=dict(l=0, r=0, t=0, b=0), legend=dict(orientation="h", y=1.02, x=0))
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    with b:
        with st.container(border=True):
            section_title("Processos por região")
            reg = top_group(dff, "regiao", "processo_id", 10, "count")
            reg["texto"] = reg["valor"].map(br_int)
            st.plotly_chart(barh(reg, "regiao", "valor", "texto", height=390, color="#39A74A"), use_container_width=True, config={"displayModeBar": False})

    c, d, e = st.columns([1.12, 1.12, 1.2])
    with c:
        with st.container(border=True):
            section_title("Top municípios por processos")
            m = top_group(dff, "municipio", "processo_id", 12, "count")
            m["texto"] = m["valor"].map(br_int)
            st.plotly_chart(barh(m, "municipio", "valor", "texto", height=340), use_container_width=True, config={"displayModeBar": False})
    with d:
        with st.container(border=True):
            section_title("Top municípios por custo")
            mc = top_group(dff, "municipio", "custo_estimado", 12, "sum")
            mc["texto"] = mc["valor"].map(br_money)
            st.plotly_chart(barh(mc, "municipio", "valor", "texto", height=340, color="#7C3AED"), use_container_width=True, config={"displayModeBar": False})
    with e:
        with st.container(border=True):
            section_title("Tabela geográfica")
            tab = dff.groupby(["regiao", "uf", "municipio"], as_index=False).agg(
                processos=("processo_id", "count"),
                pacientes=("paciente_id", "nunique"),
                custo_total=("custo_estimado", "sum"),
                ticket_medio=("custo_estimado", "mean"),
            ).sort_values("processos", ascending=False).head(15)
            tab["custo_total"] = tab["custo_total"].map(lambda x: br_money(x, compact=False))
            tab["ticket_medio"] = tab["ticket_medio"].map(lambda x: br_money(x, compact=False))
            st.dataframe(tab.rename(columns={"regiao": "Região", "uf": "UF", "municipio": "Município", "processos": "Processos", "pacientes": "Pacientes", "custo_total": "Custo Total", "ticket_medio": "Ticket Médio"}), hide_index=True, use_container_width=True, height=340)
