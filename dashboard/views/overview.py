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

def render_overview(dff, base, k, participacao, part_custo, paciente_ids_sel):
    auth_state = st.session_state.get("auth_user", {})
    user_role = auth_state.get("role", "gestor") if isinstance(auth_state, dict) else "gestor"
    if user_role == "usuario":
        # -------------------------------------------------------------------------
        # Visão Cidadã / Paciente (foco no seu pedido, situação, prazos e orientações)
        # -------------------------------------------------------------------------
        st.markdown(
            """
            <style>
            .patient-welcome-card {
                background: linear-gradient(135deg, #083E82 0%, #125CC9 100%);
                color: white;
                border-radius: 18px;
                padding: 1.3rem 1.6rem;
                margin-bottom: 1.2rem;
                box-shadow: 0 8px 24px rgba(8, 62, 130, 0.15);
            }
            .patient-welcome-title { font-size: 1.45rem; font-weight: 900; margin-bottom: .25rem; }
            .patient-welcome-sub { font-size: 0.95rem; opacity: 0.92; line-height: 1.4; }
            .guide-item {
                display: flex;
                gap: 0.75rem;
                align-items: flex-start;
                margin-bottom: 0.85rem;
            }
            .guide-step-num {
                background: #EEF5FF;
                color: #083E82;
                font-weight: 800;
                width: 28px;
                height: 28px;
                min-width: 28px;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 0.85rem;
            }
            .guide-text-title { font-weight: 800; font-size: 0.93rem; color: #0B2459; margin-bottom: 0.15rem; }
            .guide-text-desc { font-size: 0.86rem; color: #667085; line-height: 1.35; }
            </style>
            """,
            unsafe_allow_html=True,
        )

        paciente_nome = dff["paciente"].iloc[0] if "paciente" in dff.columns and not dff.empty else "Paciente"
        total_proc = len(dff)

        st.markdown(
            f"""
            <div class="patient-welcome-card">
                <div class="patient-welcome-title">Olá, {escape(str(paciente_nome))}</div>
                <div class="patient-welcome-sub">
                    Você tem <b>{total_proc} processo(s)</b> vinculado(s) à sua conta.
                    Aqui você acompanha a situação do seu pedido judicial e da liberação do seu tratamento pelo SUS em linguagem simples.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Processo em foco (primeiro registro da seleção)
        proc = dff.iloc[0]
        proc_id = str(proc.get("processo_id", "-"))
        item_desc = str(proc.get("item_demandado", proc.get("medicamento_dcb", "-")))
        etapa_jud = str(proc.get("etapa_judicial", "Em análise"))
        etapa_sau = str(proc.get("etapa_saude", "Aguardando"))
        urgente_val = str(proc.get("decisao_urgencia", proc.get("urgente", "Não")))
        prazo_vencido = str(proc.get("indicador_atraso", "Não")) == "Sim"
        dt_limite = proc.get("data_limite_cumprimento")
        if pd.notnull(dt_limite) and hasattr(dt_limite, "strftime"):
            dt_limite_str = dt_limite.strftime("%d/%m/%Y")
        elif pd.notnull(dt_limite):
            dt_limite_str = str(dt_limite)
        else:
            dt_limite_str = "Aguardando prazo"

        # 4 Cards Cidadãos (substituem métricas estatísticas inapropriadas para n=1)
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            metric_card(
                "Processo",
                proc_id,
                f"Item: {item_desc[:26]}..." if len(item_desc) > 26 else f"Item: {item_desc}",
                "📄",
                "icon-blue",
            )
        with c2:
            metric_card(
                "Situação na Justiça",
                etapa_jud,
                "andamento judicial da ação",
                "⚖️",
                "icon-purple",
            )
        with c3:
            metric_card(
                "Situação no SUS",
                etapa_sau,
                "fornecimento na rede de saúde",
                "🏥",
                "icon-green",
            )
        with c4:
            if prazo_vencido:
                metric_card(
                    "Prazo de Entrega",
                    "Prazo Vencido",
                    f"Data limite era {dt_limite_str}",
                    "⚠️",
                    "icon-orange",
                )
            else:
                metric_card(
                    "Prazo de Entrega",
                    dt_limite_str,
                    "data fixada para cumprimento",
                    "⏱",
                    "icon-green",
                )

        col_esq, col_dir = st.columns([1.35, 1.0])
        with col_esq:
            with st.container(border=True):
                section_title("📌 O que está acontecendo com o seu pedido?")
                msg_paciente = proc.get("mensagem_paciente")
                if pd.notnull(msg_paciente) and str(msg_paciente).strip():
                    st.info(f"**Situação resumida:** {msg_paciente}")

                prox_jud = proc.get("proxima_acao_judicial")
                prox_jud_txt = f"<b>Próxima ação judicial:</b> {escape(str(prox_jud))}" if pd.notnull(prox_jud) else "Aguardando próxima movimentação no processo."

                prox_sau = proc.get("proxima_acao_saude")
                prox_sau_txt = f"<b>Ação na rede de saúde:</b> {escape(str(prox_sau))}" if pd.notnull(prox_sau) else "Em tramitação administrativa no órgão de saúde."

                st.markdown(
                    f"""
                    <div style="margin-top:0.75rem;">
                        <div class="guide-item">
                            <div class="guide-step-num">1</div>
                            <div>
                                <div class="guide-text-title">Trilha Judicial</div>
                                <div class="guide-text-desc"><b>Status atual:</b> {escape(etapa_jud)}.<br>{prox_jud_txt}</div>
                            </div>
                        </div>
                        <div class="guide-item">
                            <div class="guide-step-num">2</div>
                            <div>
                                <div class="guide-text-title">Cumprimento na Saúde</div>
                                <div class="guide-text-desc"><b>Status atual:</b> {escape(etapa_sau)}.<br>{prox_sau_txt}</div>
                            </div>
                        </div>
                        <div class="guide-item">
                            <div class="guide-step-num">3</div>
                            <div>
                                <div class="guide-text-title">Pedido Urgente / Liminar</div>
                                <div class="guide-text-desc"><b>Situação:</b> {escape(urgente_val)}. Pedidos urgentes têm prioridade legal na análise judicial.</div>
                            </div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        with col_dir:
            citizen_legal_contacts_card()

        citizen_glossary_expander()

        if len(dff) > 1:
            with st.container(border=True):
                section_title("Todos os seus processos")
                p_table = dff[[
                    "processo_id", "data_ajuizamento", "item_demandado",
                    "especialidade", "etapa_judicial", "etapa_saude", "data_limite_cumprimento", "indicador_atraso"
                ]].copy()
                p_table["data_ajuizamento"] = p_table["data_ajuizamento"].dt.strftime("%d/%m/%Y")
                if p_table["data_limite_cumprimento"].dtype == "object" or hasattr(p_table["data_limite_cumprimento"].iloc[0], "strftime"):
                    p_table["data_limite_cumprimento"] = pd.to_datetime(p_table["data_limite_cumprimento"], errors="coerce").dt.strftime("%d/%m/%Y").fillna("A definir")
                st.dataframe(
                    display_columns(p_table.rename(columns={
                        "processo_id": "Processo",
                        "data_ajuizamento": "Data",
                        "item_demandado": "Item / Medicamento",
                        "especialidade": "Especialidade",
                        "etapa_judicial": "Etapa Judicial",
                        "etapa_saude": "Situação no SUS",
                        "data_limite_cumprimento": "Data Limite",
                        "indicador_atraso": "Prazo Vencido",
                    })),
                    hide_index=True,
                    use_container_width=True,
                )
    else:
        # -------------------------------------------------------------------------
        # Visão Executiva do Gestor (indicadores agregados, BI e evolução)
        # -------------------------------------------------------------------------
        cards = [
            ("Total de Processos", br_int(k["total"]), f"{br_float(participacao)}% da base total", "📄", "icon-blue"),
            ("Pacientes Ativos", br_int(k["pacientes"]), f"{br_float(pct(k['pacientes'], base['paciente_id'].nunique()))}% dos pacientes", "👥", "icon-green"),
            ("Custo Total", br_money(k["custo"]), f"{br_float(part_custo)}% da base · estimativa para o erário", "$", "icon-green"),
            ("Tempo Médio", f"{br_int(k['tempo'])} dias", "tempo médio de tramitação", "⏱", "icon-orange"),
            ("Taxa de Procedência", f"{br_float(k['procedencia'])}%", "sobre processos com resolução de mérito", "🛡", "icon-purple"),
        ]
        cols = st.columns(len(cards))
        for col, card in zip(cols, cards):
            with col:
                metric_card(*card)

        a, b, c = st.columns([1.75, 1.2, 1.15])
        with a:
            with st.container(border=True):
                section_title("Evolução mensal dos processos")
                st.plotly_chart(
                    monthly_line(dff.assign(qtd=1), "qtd", "Processos", height=340),
                    use_container_width=True,
                    config={"displayModeBar": True, "scrollZoom": True, "responsive": True, "displaylogo": False},
                )
        with b:
            with st.container(border=True):
                section_title("Natureza da ação")
                nat = dff.groupby("natureza", as_index=False).size().rename(columns={"size": "processos"}).sort_values("processos", ascending=False)
                nat["texto"] = nat["processos"].map(br_int)
                st.plotly_chart(barh(nat, "natureza", "processos", "texto", height=340), use_container_width=True, config={"displayModeBar": False})
        with c:
            with st.container(border=True):
                section_title("Desfecho processual")
                desf = dff.groupby("desfecho", as_index=False).size().rename(columns={"size": "processos"}).sort_values("processos", ascending=False)
                desf["texto"] = desf["processos"].map(br_int)
                cores_desfecho = {
                    "Procedente": CORES["deferido"],
                    "Parcialmente procedente": CORES["deferido"],
                    "Improcedente": CORES["indeferido"],
                    "Em andamento": CORES["pendente"],
                    "Sem resolução de mérito": CORES["pendente"],
                    "Acordo": CORES["justica_federal"],
                }
                st.plotly_chart(barh(desf, "desfecho", "processos", "texto", height=340, color=cores_desfecho), use_container_width=True, config={"displayModeBar": False})

        d, e, f = st.columns([1.35, 1.35, 1.30])
        with d:
            with st.container(border=True):
                section_title("Top 10 itens mais demandados")
                top_itens = top_group(dff, "item_demandado", "processo_id", 10, "count")
                top_itens["texto"] = top_itens["valor"].map(br_int)
                st.plotly_chart(barh(top_itens, "item_demandado", "valor", "texto", height=335), use_container_width=True, config={"displayModeBar": False})
        with e:
            with st.container(border=True):
                section_title("Custo por natureza")
                custo_nat = top_group(dff, "natureza", "custo_estimado", 8, "sum")
                custo_nat["texto"] = custo_nat["valor"].map(br_money)
                st.plotly_chart(barh(custo_nat, "natureza", "valor", "texto", height=335, color="#39A74A"), use_container_width=True, config={"displayModeBar": False})
        with f:
            with st.container(border=True):
                section_title("Alertas executivos")
                p_lim = br_float(k["liminar"])
                item_maior = top_group(dff, "item_demandado", "custo_estimado", 1, "sum")
                cidade_maior = top_group(dff, "municipio", "processo_id", 1, "count")
                i1, i2 = st.columns(2)
                with i1:
                    insight_card("Liminares", f"{p_lim}%", "Percentual de processos com decisão liminar no recorte filtrado.")
                with i2:
                    insight_card("Urgentes", br_int(k["urgentes"]), "Total de processos classificados como urgentes.")
                i3, i4 = st.columns(2)
                with i3:
                    insight_card("Maior item por custo", item_maior["item_demandado"].iloc[0] if not item_maior.empty else "-", br_money(item_maior["valor"].iloc[0]) if not item_maior.empty else "Sem custo")
                with i4:
                    insight_card("Município destaque", cidade_maior["municipio"].iloc[0] if not cidade_maior.empty else "-", f"{br_int(cidade_maior['valor'].iloc[0])} processos" if not cidade_maior.empty else "Sem registros")
