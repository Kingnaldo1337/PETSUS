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

def render_competence(dff, base, k, participacao, part_custo, paciente_ids_sel):
    med = dff[dff["medicamento_petsus"] == "Sim"].copy()
    st.info(
        f"Simulação acadêmica com os campos do PetSUS. Para medicamentos não incorporados, o dashboard usa como referência "
        f"210 salários mínimos de 2026 (R$ {br_float(LIMITE_210_SM_2026, 2)})."
    )
    if med.empty:
        st.warning("Nenhuma demanda de medicamento foi encontrada com os filtros selecionados.")
    else:
        federal = int((med["competencia_petsus"] == "Justiça Federal").sum())
        estadual = int((med["competencia_petsus"] == "Justiça Estadual").sum())
        alto_custo = int((med["acima_210_salarios_minimos"] == "Sim").sum())
        reu_top = top_group(med, "reu_sugerido", "processo_id", 1, "count")
        cols = st.columns(5)
        cards = [
            ("Justiça Federal", f"{br_float(pct(federal, len(med)))}%", f"{br_int(federal)} processos", "🏛️", "icon-blue"),
            ("Justiça Estadual", f"{br_float(pct(estadual, len(med)))}%", f"{br_int(estadual)} processos", "⚖️", "icon-green"),
            ("≥ 210 salários mínimos", br_int(alto_custo), "tratamentos anuais acima do limite de referência", "💰", "icon-orange"),
            ("Réu mais sugerido", reu_top["reu_sugerido"].iloc[0] if not reu_top.empty else "-", "maior frequência no recorte", "👤", "icon-purple"),
            ("Valor da causa estimado", br_money(med["valor_causa_estimado"].sum()), "soma dos valores estimados", "$", "icon-green"),
        ]
        for col, card in zip(cols, cards):
            with col:
                metric_card(*card)

        a, b, c = st.columns([1.0, 1.0, 1.4])
        with a:
            with st.container(border=True):
                section_title("Competência judicial")
                comp = med.groupby("competencia_petsus", as_index=False).size().rename(columns={"size": "processos"})
                st.plotly_chart(donut(comp, "competencia_petsus", "processos", f"{br_int(len(med))}<br>Demandas", height=340), use_container_width=True, config={"displayModeBar": False})
        with b:
            with st.container(border=True):
                section_title("Réu sugerido")
                reu = top_group(med, "reu_sugerido", "processo_id", 5, "count")
                reu["texto"] = reu["valor"].map(br_int)
                st.plotly_chart(barh(reu, "reu_sugerido", "valor", "texto", height=340, color="#7C3AED"), use_container_width=True, config={"displayModeBar": False})
        with c:
            with st.container(border=True):
                section_title("Competência x incorporação à RENAME")
                cross = pd.crosstab(med["rename_incorporado"], med["competencia_petsus"]).reset_index()
                fig = go.Figure()
                for nome, color in [("Justiça Federal", "#125CC9"), ("Justiça Estadual", "#39A74A")]:
                    if nome not in cross.columns:
                        cross[nome] = 0
                    fig.add_trace(go.Bar(x=cross["rename_incorporado"], y=cross[nome], name=nome, marker_color=color, text=cross[nome], textposition="inside"))
                fig.update_layout(**chart_layout(height=340, showlegend=True, legend=dict(orientation="h", y=1.12, x=0)), barmode="stack")
                fig.update_yaxes(showgrid=True, gridcolor="#E8EDF5", zeroline=False)
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

        d, e = st.columns([1.05, 1.6])
        with d:
            with st.container(border=True):
                section_title("Valor anual por componente")
                val_comp = top_group(med, "componente_sus", "valor_anual_tratamento", 8, "sum")
                val_comp["texto"] = val_comp["valor"].map(br_money)
                st.plotly_chart(barh(val_comp, "componente_sus", "valor", "texto", height=360, color="#39A74A"), use_container_width=True, config={"displayModeBar": False})
        with e:
            with st.container(border=True):
                section_title("Casos de maior valor anual")
                tab = med[[
                    "processo_id", "cid", "medicamento_dcb", "rename_incorporado", "componente_sus", "grupo_sus",
                    "valor_anual_tratamento", "acima_210_salarios_minimos", "competencia_petsus", "reu_sugerido"
                ]].sort_values("valor_anual_tratamento", ascending=False).head(15)
                st.dataframe(tab.rename(columns={
                    "processo_id": "Processo", "cid": "CID", "medicamento_dcb": "DCB", "rename_incorporado": "RENAME",
                    "componente_sus": "Componente", "grupo_sus": "Grupo", "valor_anual_tratamento": "Valor anual",
                    "acima_210_salarios_minimos": "≥ 210 SM", "competencia_petsus": "Competência", "reu_sugerido": "Réu sugerido"
                }), hide_index=True, use_container_width=True, height=360, column_config={
                    "Valor anual": st.column_config.NumberColumn("Valor anual", format="R$ %.2f")
                })
