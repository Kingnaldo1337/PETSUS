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

def render_costs(dff, base, k, participacao, part_custo, paciente_ids_sel):
    cols = st.columns(5)
    med_cost = dff[dff["natureza"] == "Medicamentos"]["custo_estimado"].sum()
    intern_cost = dff[dff["natureza"] == "Internação"]["custo_estimado"].sum()
    cards = [
        ("Custo Total", br_money(k["custo"]), f"{br_float(part_custo)}% do custo da base", "$", "icon-green"),
        ("Ticket Médio", br_money(k["ticket"]), "custo total estimado ÷ número de processos", "🧾", "icon-blue"),
        ("Custo Medicamentos", br_money(med_cost), f"{br_float(pct(med_cost, k['custo']))}% do recorte", "💊", "icon-purple"),
        ("Custo Internações", br_money(intern_cost), f"{br_float(pct(intern_cost, k['custo']))}% do recorte", "🏥", "icon-orange"),
        ("Maior Processo", br_money(dff["custo_estimado"].max()), "maior valor individual", "📈", "icon-green"),
    ]
    for col, card in zip(cols, cards):
        with col:
            metric_card(*card)

    a, b = st.columns([1.55, 1.25])
    with a:
        with st.container(border=True):
            section_title("Evolução mensal do custo total")
            st.plotly_chart(monthly_line(dff, "custo_estimado", "Custo total", money=True, height=350), use_container_width=True, config={"displayModeBar": False})
    with b:
        with st.container(border=True):
            section_title("Custo por esfera")
            esfera = top_group(dff, "esfera", "custo_estimado", 5, "sum")
            esfera["texto"] = esfera["valor"].map(br_money)
            st.plotly_chart(barh(esfera, "esfera", "valor", "texto", height=350, color="#39A74A"), use_container_width=True, config={"displayModeBar": False})

    c, d, e = st.columns([1.2, 1.2, 1.2])
    with c:
        with st.container(border=True):
            section_title("Itens com maior impacto financeiro")
            itens_custo = top_group(dff, "item_demandado", "custo_estimado", 10, "sum")
            itens_custo["texto"] = itens_custo["valor"].map(br_money)
            st.plotly_chart(barh(itens_custo, "item_demandado", "valor", "texto", height=350, color="#125CC9"), use_container_width=True, config={"displayModeBar": False})
    with d:
        with st.container(border=True):
            section_title("Especialidades por custo")
            esp_custo = top_group(dff, "especialidade", "custo_estimado", 10, "sum")
            esp_custo["texto"] = esp_custo["valor"].map(br_money)
            st.plotly_chart(barh(esp_custo, "especialidade", "valor", "texto", height=350, color="#7C3AED"), use_container_width=True, config={"displayModeBar": False})
    with e:
        with st.container(border=True):
            section_title("Custo médio por processo, por natureza")
            sample = dff.copy()
            if len(sample) > 3500:
                sample = sample.sample(3500, random_state=42)
            fig = px.box(sample, x="natureza", y="custo_estimado", points=False)
            fig.update_traces(marker_color="#125CC9")
            fig.update_layout(**chart_layout(height=350))
            fig.update_yaxes(showgrid=True, gridcolor="#E8EDF5", zeroline=False, tickprefix="R$ ")
            fig.update_xaxes(showgrid=False)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
