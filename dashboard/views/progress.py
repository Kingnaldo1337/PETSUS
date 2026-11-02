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

JUDICIAL_TRACK = (
    "Documentação preparada", "Processo protocolado", "Processo distribuído",
    "Análise técnica", "Aguardando decisão", "Decisão sobre urgência",
    "Órgão responsável intimado", "Cumprimento em acompanhamento", "Sentença",
    "Recursos / encerramento",
)


def tracking_bar(title: str, stages, current: int, color: str) -> None:
    help_text = (
        "A Trilha A mostra o andamento do processo dentro do Judiciário."
        if title.startswith("Trilha A")
        else "A Trilha B mostra o cumprimento prático da decisão pela rede de saúde."
    )
    items = []
    for index, name in enumerate(stages, start=1):
        state = "done" if index < current else "current" if index == current else "pending"
        marker = "✓" if index < current else str(index)
        items.append(
            f'<div class="flow-step {state}" style="--track-color:{color}">'
            f'<div class="flow-marker">{marker}</div><div class="flow-label">{escape(str(name))}</div></div>'
        )
    st.markdown(
        f'<div class="flow-title">{escape(title)}'
        f'<span class="card-help" tabindex="0" role="img" aria-label="Ajuda: {escape(help_text, quote=True)}" '
        f'data-help="{escape(help_text, quote=True)}">?</span></div>'
        f'<div class="flow-track">' + "".join(items) + "</div>",
        unsafe_allow_html=True,
    )


def render_progress(dff, base, paciente_ids_sel):
    auth_state = st.session_state.get("auth_user", {})
    user_role = auth_state.get("role", "gestor") if isinstance(auth_state, dict) else "gestor"
    st.markdown(
        """
        <style>
        .flow-title { display:flex; align-items:center; gap:.5rem; font-size:1.05rem; font-weight:900; color:#0B2459; margin:.7rem 0 .5rem; }
        .flow-title .card-help { margin-left:0; }
        .flow-track { display:grid; grid-template-columns:repeat(5,minmax(0,1fr)); gap:.6rem; margin-bottom:1rem; }
        .flow-step { min-width:0; padding:.65rem .4rem; border:1px solid #DDE6F2; border-radius:13px; background:#F8FAFD; text-align:center; }
        .flow-marker { width:28px; height:28px; border-radius:50%; margin:0 auto .4rem; display:flex; align-items:center; justify-content:center; background:#E5EAF1; color:#667085; font-weight:900; }
        .flow-label { font-size:.74rem; line-height:1.18; color:#667085; font-weight:750; overflow-wrap:anywhere; }
        .flow-step.done { background:#ECFDF3; border-color:#A7E3BC; }
        .flow-step.done .flow-marker { background:#239B56; color:white; }
        .flow-step.current { background:#EEF5FF; border:2px solid var(--track-color); box-shadow:0 4px 12px rgba(18,92,201,.12); }
        .flow-step.current .flow-marker { background:var(--track-color); color:white; }
        .flow-step.current .flow-label { color:#0B2459; }
        [data-testid="stMetricValue"],
        [data-testid="stMetricValue"] > div,
        [data-testid="stMetricValue"] * {
            font-size: clamp(1.05rem, 1.65vw, 1.6rem) !important;
            line-height: 1.15 !important;
            white-space: normal !important;
            overflow: visible !important;
            text-overflow: clip !important;
            overflow-wrap: anywhere !important;
        }
        @media(max-width:900px){.flow-track{grid-template-columns:repeat(2,minmax(0,1fr));}}
        @media(max-width:520px){.flow-track{grid-template-columns:1fr;}}
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.info(
        "Esta demonstração separa o andamento no Judiciário do cumprimento material na saúde. "
        "Uma decisão favorável não significa, por si só, que o medicamento foi entregue ou que a cirurgia foi realizada."
    )

    overdue_count = int((dff["indicador_atraso"] == "Sim").sum())
    health_active = int((dff["etapa_saude_ordem"] > 0).sum())
    continuous = int((dff["status_andamento"] == "Tratamento em cumprimento contínuo").sum())
    cols = st.columns(4)
    cards = [
        ("Processos acompanhados", br_int(len(dff)), "processos no recorte", "📋", "icon-blue"),
        ("Cumprimento iniciado", br_int(health_active), "ordens em execução na saúde", "⚕", "icon-green"),
        ("Prazo vencido", br_int(overdue_count), "cumprimentos pendentes", "!", "icon-orange"),
        ("Uso contínuo", br_int(continuous), "tratamentos com acompanhamento periódico", "↻", "icon-purple"),
    ]
    for col, card in zip(cols, cards):
        with col:
            metric_card(*card)

    if user_role != "usuario":
        a, b = st.columns(2)
        with a:
            with st.container(border=True):
                section_title("Etapas judiciais no recorte")
                judicial_summary = dff.groupby("etapa_judicial", as_index=False).size().rename(columns={"size": "processos"})
                judicial_summary["texto"] = judicial_summary["processos"].map(br_int)
                st.plotly_chart(barh(judicial_summary, "etapa_judicial", "processos", "texto", height=320), use_container_width=True, config={"displayModeBar": False})
        with b:
            with st.container(border=True):
                section_title("Cumprimento na rede de saúde")
                health_summary = dff.groupby("etapa_saude", as_index=False).size().rename(columns={"size": "processos"})
                health_summary["texto"] = health_summary["processos"].map(br_int)
                st.plotly_chart(barh(health_summary, "etapa_saude", "processos", "texto", height=320, color="#239B56"), use_container_width=True, config={"displayModeBar": False})

    section_title("Consultar um processo")
    process_rows = dff.sort_values("ultima_movimentacao_data", ascending=False).drop_duplicates("processo_id")
    labels = {}
    for row in process_rows.itertuples(index=False):
        patient = f" · {row.paciente}" if user_role != "usuario" else ""
        labels[f"{row.processo_id}{patient} · {row.item_demandado}"] = row.processo_id
    selected_label = st.selectbox("Processo", list(labels), help="Selecione o processo que deseja acompanhar.")
    process = process_rows[process_rows["processo_id"] == labels[selected_label]].iloc[0]

    st.markdown(f"### {escape(str(process['item_demandado']))}")
    st.caption(f"Processo {process['processo_id']} · Fluxo de {process['tipo_fluxo_saude']}")
    if process["status_andamento"] == "Tratamento em cumprimento contínuo":
        st.success("O medicamento foi entregue, mas o acompanhamento continua por se tratar de uso contínuo.")

    j1, j2, j3 = st.columns(3)
    j1.metric("Situação judicial", process["etapa_judicial"])
    j2.metric("Cumprimento na saúde", process["etapa_saude"])
    j3.metric("Status geral", process["status_andamento"])

    st.progress(int(process["percentual_judicial"]), text=f"Andamento judicial: {int(process['percentual_judicial'])}%")
    tracking_bar("Trilha A - andamento judicial", JUDICIAL_TRACK, int(process["etapa_judicial_ordem"]), "#125CC9")

    health_tracks = {
        "Medicamento": ("Ordem recebida", "Análise do cumprimento", "Estoque verificado", "Aquisição", "Produto recebido", "Disponível", "Paciente comunicado", "Medicamento entregue"),
        "Cirurgia": ("Ordem recebida", "Regulação", "Hospital definido", "Pré-operatório", "Autorizada", "Agendada", "Paciente convocado", "Realizada", "Pós-operatório"),
        "Tratamento ou serviço": ("Ordem recebida", "Análise", "Disponibilidade", "Providência administrativa", "Disponibilizado", "Paciente comunicado", "Realizado"),
    }
    health_track = health_tracks[process["tipo_fluxo_saude"]]
    if int(process["etapa_saude_ordem"]) == 0:
        st.warning("A trilha de cumprimento ainda não começou porque não há ordem favorável registrada.")
    st.progress(int(process["percentual_saude"]), text=f"Cumprimento na saúde: {int(process['percentual_saude'])}%")
    tracking_bar(f"Trilha B - cumprimento de {str(process['tipo_fluxo_saude']).lower()}", health_track, int(process["etapa_saude_ordem"]), "#239B56")

    c1, c2, c3 = st.columns(3)
    with c1:
        with st.container(border=True):
            section_title("Decisão e comunicação")
            st.write(process["decisao_urgencia"])
            if pd.notna(process["data_intimacao"]):
                st.caption(f"Intimação: {pd.to_datetime(process['data_intimacao']).strftime('%d/%m/%Y')}")
    with c2:
        with st.container(border=True):
            section_title("Prazo para cumprimento")
            if pd.notna(process["data_limite_cumprimento"]):
                st.markdown(f"**{pd.to_datetime(process['data_limite_cumprimento']).strftime('%d/%m/%Y')}**")
                st.caption(f"Prazo demonstrativo: {int(process['prazo_cumprimento_dias'])} dias")
            else:
                st.write("Ainda não definido")
    with c3:
        with st.container(border=True):
            section_title("Próxima ação")
            st.write(process["proxima_etapa"])
            st.caption(f"Responsável: {process['responsavel_etapa']}")

    if user_role == "usuario":
        st.info(process["mensagem_paciente"])

    pdf_data = build_process_tracking_pdf(
        process.to_dict(),
        JUDICIAL_TRACK,
        health_track,
    )
    st.download_button(
        "Baixar consulta em PDF",
        data=pdf_data,
        file_name=f"andamento_{process['processo_id']}.pdf",
        mime="application/pdf",
        help="Baixa um relatório com o resumo e as etapas do processo selecionado.",
        type="primary",
    )

    if user_role == "usuario":
        st.markdown("---")
        citizen_legal_contacts_card()
        citizen_glossary_expander()
