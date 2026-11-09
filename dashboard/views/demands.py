from __future__ import annotations

from html import escape

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from ..charts import CORES, barh, chart_layout, empty_fig, monthly_line, top_group
from ..ui import br_float, br_int, br_money, citizen_glossary_expander, citizen_legal_contacts_card, display_columns, insight_card, metric_card, pct, section_title, to_excel_bytes
from petsus.reports.process_tracking_pdf import build_process_tracking_pdf

LIMITE_210_SM_2026 = 210 * 1621.0

def render_demands(dff, base, k, participacao, part_custo, paciente_ids_sel):
    cols = st.columns(5)
    demanda_principal = top_group(dff, "tipo_demanda", "processo_id", 1, "count")
    esp_principal = top_group(dff, "especialidade", "processo_id", 1, "count")
    cards = [
        ("Processos Urgentes", br_int(k["urgentes"]), f"{br_float(pct(k['urgentes'], k['total']))}% dos processos", "🔔", "icon-orange"),
        ("Taxa de Liminares", f"{br_float(k['liminar'])}%", "processos com liminar", "⚖️", "icon-purple"),
        ("Demanda Principal", demanda_principal["tipo_demanda"].iloc[0] if not demanda_principal.empty else "-", "maior volume", "📌", "icon-blue"),
        ("Especialidade Líder", esp_principal["especialidade"].iloc[0] if not esp_principal.empty else "-", "maior volume", "🩺", "icon-green"),
        ("Itens Distintos", br_int(dff["item_demandado"].nunique()), "medicamentos/serviços", "💊", "icon-blue"),
    ]
    for col, card in zip(cols, cards):
        with col:
            metric_card(*card)

    a, b = st.columns([1.35, 1.2])
    with a:
        with st.container(border=True):
            section_title("Demandas por tipo e fase processual")
            fase = pd.crosstab(dff["tipo_demanda"], dff["fase_processual"]).reset_index()
            for col in ["Conhecimento", "Execução", "Cumprimento de Sentença"]:
                if col not in fase.columns:
                    fase[col] = 0
            fase = fase.sort_values(["Conhecimento", "Execução", "Cumprimento de Sentença"], ascending=False).head(10)
            fig = go.Figure()
            for col_name, color in [("Conhecimento", "#125CC9"), ("Execução", "#39A74A"), ("Cumprimento de Sentença", "#EAB308")]:
                fig.add_trace(go.Bar(y=fase["tipo_demanda"], x=fase[col_name], orientation="h", name=col_name, marker_color=color, text=fase[col_name], textposition="inside"))
            fig.update_layout(**chart_layout(height=370, showlegend=True, legend=dict(orientation="h", y=1.12, x=0)), barmode="stack")
            fig.update_xaxes(showgrid=True, gridcolor="#E8EDF5", zeroline=False)
            fig.update_yaxes(showgrid=False, autorange="reversed")
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    with b:
        with st.container(border=True):
            section_title("Evolução mensal de liminares e urgências")
            trend = dff.assign(liminar_qtd=(dff["liminar"] == "Sim").astype(int), urgente_qtd=(dff["urgente"] == "Sim").astype(int))
            trend = trend.groupby("ano_mes", as_index=False).agg(liminares=("liminar_qtd", "sum"), urgentes=("urgente_qtd", "sum"))
            trend = trend.sort_values("ano_mes")
            trend["mes"] = pd.to_datetime(trend["ano_mes"] + "-01").dt.strftime("%m/%Y")
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=trend["mes"], y=trend["liminares"], mode="lines+markers", name="Liminares registradas", line=dict(color=CORES["deferido"], width=3)))
            fig.add_trace(go.Scatter(x=trend["mes"], y=trend["urgentes"], mode="lines+markers", name="Demandas urgentes", line=dict(color=CORES["pendente"], width=3)))
            fig.update_layout(**chart_layout(height=370, showlegend=True, legend=dict(orientation="h", y=1.12, x=0)))
            fig.update_yaxes(showgrid=True, gridcolor="#E8EDF5", zeroline=False)
            fig.update_xaxes(showgrid=False)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    with st.container(border=True):
        section_title("Registro de liminares na base")
        com_liminar = int((dff["liminar"] == "Sim").sum())
        sem_liminar = int((dff["liminar"] == "Não").sum())
        liminar_cols = st.columns(2)
        with liminar_cols[0]:
            metric_card("Liminar registrada: Sim", br_int(com_liminar), "conforme o campo liminar", "✅", "icon-green")
        with liminar_cols[1]:
            metric_card("Liminar registrada: Não", br_int(sem_liminar), "conforme o campo liminar", "—", "icon-orange")
        st.info(
            "A base atual não diferencia pedido formulado, liminar deferida ou indeferida e pedido aguardando decisão. "
            "Esses estados não podem ser calculados com segurança a partir do campo Sim/Não."
        )

    c, d, e = st.columns([1.15, 1.15, 1.25])
    with c:
        with st.container(border=True):
            section_title("Tipos de demanda")
            tipo = top_group(dff, "tipo_demanda", "processo_id", 10, "count")
            tipo["texto"] = tipo["valor"].map(br_int)
            st.plotly_chart(barh(tipo, "tipo_demanda", "valor", "texto", height=330), use_container_width=True, config={"displayModeBar": False})
    with d:
        with st.container(border=True):
            section_title("Especialidades mais acionadas")
            esp = top_group(dff, "especialidade", "processo_id", 10, "count")
            esp["texto"] = esp["valor"].map(br_int)
            st.plotly_chart(barh(esp, "especialidade", "valor", "texto", height=330, color="#39A74A"), use_container_width=True, config={"displayModeBar": False})
    with e:
        with st.container(border=True):
            section_title("Tabela de demandas")
            table = dff.groupby(["tipo_demanda", "fase_processual"], as_index=False).agg(
                processos=("processo_id", "count"),
                pacientes=("paciente_id", "nunique"),
                custo_total=("custo_estimado", "sum"),
                tempo_medio=("tempo_tramitacao_dias", "mean"),
            ).sort_values("processos", ascending=False).head(12)
            table["custo_total"] = table["custo_total"].map(lambda x: br_money(x, compact=False))
            table["tempo_medio"] = table["tempo_medio"].map(lambda x: f"{br_int(x)} dias")
            st.dataframe(display_columns(table.rename(columns={"tipo_demanda": "Tipo", "fase_processual": "Fase", "processos": "Processos", "pacientes": "Pacientes", "custo_total": "Custo Total", "tempo_medio": "Tempo Médio"})), hide_index=True, use_container_width=True, height=330)
