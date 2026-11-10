from __future__ import annotations

from html import escape

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from ..charts import barh, chart_layout, donut, empty_fig, monthly_line, top_group
from ..ui import br_float, br_int, br_money, citizen_glossary_expander, citizen_legal_contacts_card, insight_card, metric_card, pct, section_title, suppress_small_counts, to_excel_bytes
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
            geo = geo[
                (geo["processos"] >= 5) & (geo["pacientes"] >= 5)
            ].dropna(subset=["latitude", "longitude"])
            if geo.empty:
                st.plotly_chart(empty_fig("Sem municípios elegíveis para o recorte", height=390), use_container_width=True, config={"displayModeBar": False})
            else:
                st.caption("Municípios com menos de 5 processos ou pacientes foram omitidos do mapa.")
                geo["pacientes_exibidos"] = suppress_small_counts(geo["pacientes"])
                fig = px.scatter_geo(
                    geo,
                    lat="latitude",
                    lon="longitude",
                    size="processos",
                    color="regiao",
                    hover_name="municipio",
                    hover_data={
                        "uf": True,
                        "processos": True,
                        "pacientes_exibidos": True,
                        "pacientes": False,
                        "custo_total": ":,.2f",
                        "latitude": False,
                        "longitude": False,
                    },
                    labels={
                        "uf": "UF",
                        "processos": "Processos",
                        "pacientes_exibidos": "Pacientes",
                        "custo_total": "Custo estimado (erário)",
                    },
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
            municipio_resumo = dff.groupby("municipio").agg(
                processos=("processo_id", "count"),
                pacientes=("paciente_id", "nunique"),
            )
            municipios_elegiveis = set(
                municipio_resumo.index[
                    (municipio_resumo["processos"] >= 5)
                    & (municipio_resumo["pacientes"] >= 5)
                ]
            )
            m = m[m["municipio"].isin(municipios_elegiveis)]
            m["texto"] = m["valor"].map(br_int)
            st.caption("Municípios com menos de 5 processos ou pacientes foram omitidos.")
            st.plotly_chart(barh(m, "municipio", "valor", "texto", height=340), use_container_width=True, config={"displayModeBar": False})
    with d:
        with st.container(border=True):
            section_title("Top municípios por custo")
            mc = top_group(dff, "municipio", "custo_estimado", 12, "sum")
            mc = mc[mc["municipio"].isin(municipios_elegiveis)]
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
            small_group = (tab["processos"] < 5) | (tab["pacientes"] < 5)
            tab["processos"] = suppress_small_counts(tab["processos"])
            tab["pacientes"] = suppress_small_counts(tab["pacientes"])
            tab.loc[small_group, ["custo_total", "ticket_medio"]] = pd.NA
            tab["custo_total"] = tab["custo_total"].map(
                lambda value: "Suprimido" if pd.isna(value) else br_money(value, compact=False)
            )
            tab["ticket_medio"] = tab["ticket_medio"].map(
                lambda value: "Suprimido" if pd.isna(value) else br_money(value, compact=False)
            )
            st.caption("Contagens e valores de grupos com menos de 5 pacientes ou processos são suprimidos.")
            st.dataframe(tab.rename(columns={"regiao": "Região", "uf": "UF", "municipio": "Município", "processos": "Processos", "pacientes": "Pacientes", "custo_total": "Custo estimado (erário)", "ticket_medio": "Ticket médio (erário)"}), hide_index=True, use_container_width=True, height=340)
