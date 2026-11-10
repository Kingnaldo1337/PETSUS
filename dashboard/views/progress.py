from __future__ import annotations

from .shared import (
    JUDICIAL_TRACK,
    MIN_PATIENTS,
    _cards,
    _count,
    _plot,
    barh,
    br_int,
    build_process_tracking_pdf,
    escape,
    mask_personal_data,
    pd,
    protected_aggregate,
    section_title,
    st,
    tracking_bar,
)


def _render_tracking(dff, user_role="gestor"):
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

    if dff["paciente_id"].nunique() >= MIN_PATIENTS:
        _cards([
            ("Processos acompanhados", br_int(len(dff)), "processos no recorte", "📋", "icon-blue"),
            ("Cumprimento iniciado", _count(dff, dff["etapa_saude_ordem"].gt(0)), "ordens em execução na saúde", "⚕", "icon-green"),
            ("Prazo vencido", _count(dff, dff["indicador_atraso"].eq("Sim")), "cumprimentos pendentes na data de referência", "!", "icon-orange"),
            ("Uso contínuo", _count(dff, dff["status_andamento"].eq("Tratamento em cumprimento contínuo")), "tratamentos com acompanhamento periódico", "↻", "icon-purple"),
        ])
        with st.container(border=True, key="manager_panel_etapas_judiciais_no_recorte"):
            section_title("Etapas judiciais no recorte")
            judicial_summary = protected_aggregate(dff, ["etapa_judicial"])
            judicial_summary["texto"] = judicial_summary["processos"].map(br_int)
            _plot(barh(judicial_summary, "etapa_judicial", "processos", "texto", height=320, separate_dominant=True), key="tracking:judicial_summary")
        with st.container(border=True, key="manager_panel_cumprimento_na_rede_de_saude"):
            section_title("Cumprimento na rede de saúde")
            st.caption("Processos por etapa registrada na rede de saúde. Os nomes completos aparecem ao passar o mouse sobre cada barra.")
            health_summary = protected_aggregate(dff, ["etapa_saude"])
            health_summary["texto"] = health_summary["processos"].map(br_int)
            _plot(barh(health_summary, "etapa_saude", "processos", "texto", height=380, color="#239B56", separate_dominant=True), key="tracking:health_summary")

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
    if pd.notna(process.get("data_referencia_calculo")):
        st.caption(f"Data de referência dos prazos: {pd.Timestamp(process['data_referencia_calculo']).strftime('%d/%m/%Y')}")
    if pd.notna(process.get("geracao_simulacao")):
        st.caption(f"Simulação gerada para: {pd.Timestamp(process['geracao_simulacao']).strftime('%d/%m/%Y')}")
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
        st.info(f"Cumprimento ainda não iniciado: {process['etapa_saude']}.")
    st.progress(int(process["percentual_saude"]), text=f"Cumprimento na saúde: {int(process['percentual_saude'])}%")
    tracking_bar(f"Trilha B - cumprimento de {str(process['tipo_fluxo_saude']).lower()}", health_track, int(process["etapa_saude_ordem"]), "#239B56")

    c1, c2, c3 = st.columns(3)
    with c1:
        with st.container(border=True, key="manager_panel_decisao_e_comunicacao"):
            section_title("Decisão e comunicação")
            st.write(process["decisao_urgencia"])
            if pd.notna(process["data_intimacao"]):
                st.caption(f"Intimação: {pd.to_datetime(process['data_intimacao']).strftime('%d/%m/%Y')}")
    with c2:
        with st.container(border=True, key="manager_panel_prazo_para_cumprimento"):
            section_title("Prazo para cumprimento")
            if pd.notna(process["data_limite_cumprimento"]):
                st.markdown(f"**{pd.to_datetime(process['data_limite_cumprimento']).strftime('%d/%m/%Y')}**")
                st.caption(f"Prazo informado: {int(process['prazo_cumprimento_dias'])} dias")
            else:
                st.write("Ainda não definido")
    with c3:
        with st.container(border=True, key="manager_panel_proxima_acao"):
            section_title("Próxima ação")
            st.write(process["proxima_etapa"])
            st.caption(f"Responsável: {process['responsavel_etapa']}")

    if user_role == "usuario":
        st.info(process["mensagem_paciente"])

    pdf_data = build_process_tracking_pdf(
        mask_personal_data(pd.DataFrame([process])).iloc[0].to_dict(),
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


def render_progress(dff, base, paciente_ids_sel):
    return _render_tracking(dff)
