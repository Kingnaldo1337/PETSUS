"""Portal do paciente: consulta individual, próximos passos e documentos."""
from __future__ import annotations

from html import escape

import pandas as pd
import streamlit as st

from petsus.dashboard.accessibility import speech_summary
from petsus.dashboard.patient_ui import icon, open_patient_help, open_patient_process
from petsus.dashboard.patient_timeline import TIMELINE_CSS, timeline_html
from petsus.reports.process_tracking_pdf import build_process_tracking_pdf

JUDICIAL_STAGES = (
    "Documentação preparada", "Processo protocolado", "Processo distribuído",
    "Análise técnica", "Aguardando decisão", "Decisão sobre o pedido",
    "Órgão responsável intimado", "Cumprimento em acompanhamento", "Sentença",
    "Recursos / encerramento",
)
HEALTH_STAGES = {
    "Medicamento": ("Ordem recebida", "Análise do cumprimento", "Estoque verificado", "Aquisição, se necessária", "Produto recebido", "Disponível para dispensação", "Paciente comunicado", "Medicamento entregue"),
    "Cirurgia": ("Ordem recebida", "Regulação", "Hospital definido", "Pré-operatório", "Cirurgia autorizada", "Cirurgia agendada", "Paciente convocado", "Cirurgia realizada", "Acompanhamento pós-operatório"),
    "Tratamento ou serviço": ("Ordem recebida", "Análise do cumprimento", "Disponibilidade verificada", "Providência administrativa", "Serviço disponibilizado", "Paciente comunicado", "Tratamento ou procedimento realizado"),
}


def date_label(value) -> str:
    return pd.to_datetime(value).strftime("%d/%m/%Y") if pd.notna(value) else "Ainda não informado"


def patient_guidance(process) -> str:
    if process["indicador_atraso"] == "Sim":
        return "O prazo registrado venceu e a entrega ou o atendimento continua pendente. Procure a Defensoria ou o advogado que acompanha seu processo e informe o número do pedido e a data do prazo."
    if int(process["etapa_saude_ordem"]) == 0:
        if process["desfecho"] == "Improcedente":
            return "Há uma decisão desfavorável registrada. Procure seu advogado ou a Defensoria para entender a decisão e os próximos passos."
        if process["desfecho"] in ("Extinto sem julgamento", "Extinto"):
            return "O processo foi encerrado sem julgamento do pedido. Procure seu advogado ou a Defensoria para entender o motivo do encerramento e verificar os próximos passos."
        return "Acompanhe a análise do pedido. Ainda não há ordem favorável registrada para iniciar o atendimento. Se precisar de orientação, procure a equipe que acompanha seu processo."
    if process["encerramento_assistencial"] == "Sim":
        return "O atendimento foi registrado como realizado. Mantenha os comprovantes e siga as orientações da equipe de saúde."
    if process["status_andamento"] == "Tratamento em cumprimento contínuo":
        return "A primeira entrega foi registrada. Confirme com a farmácia responsável quando será a próxima retirada."
    return "A rede de saúde está preparando o atendimento. Confira o próximo passo abaixo e aguarde a comunicação da equipe responsável."


def download_summary(process, key: str, compact: bool = False) -> None:
    st.download_button(
        "↓  Baixar resumo do acompanhamento",
        data=build_process_tracking_pdf(process.to_dict(), JUDICIAL_STAGES, HEALTH_STAGES[process["tipo_fluxo_saude"]]),
        file_name=f"acompanhamento_{process['processo_id']}.pdf", mime="application/pdf", key=key,
        use_container_width=not compact,
    )


def court_status(process) -> tuple[str, str, str]:
    outcome = str(process["desfecho"])
    if outcome == "Improcedente":
        return "Decisão desfavorável", "red", "Há uma decisão registrada. Sua equipe jurídica pode explicar o resultado e os próximos passos."
    if outcome in ("Extinto", "Extinto sem julgamento"):
        return "Processo encerrado", "gray", "O pedido foi encerrado sem julgamento. Consulte seu representante para entender o motivo."
    if outcome in ("Procedente", "Parcialmente procedente", "Acordo"):
        return "Decisão registrada", "green", f"Resultado do pedido: {outcome.lower()}. O atendimento é acompanhado separadamente na saúde."
    if process["liminar"] == "Sim":
        return "Decisão provisória favorável", "teal", "Uma decisão provisória foi concedida. O processo continua em acompanhamento."
    return "Aguardando decisão", "amber", "Seu pedido foi registrado e aguarda análise. Acompanhe aqui as próximas movimentações."


def health_status(process) -> tuple[str, str, str]:
    if int(process["etapa_saude_ordem"]) == 0:
        return "Atendimento ainda não iniciado", "gray", "Ainda não há atendimento registrado para este pedido."
    if process["status_andamento"] == "Tratamento em cumprimento contínuo":
        return "Entrega registrada", "green", "O medicamento foi entregue. O acompanhamento continua para as próximas retiradas."
    if process["encerramento_assistencial"] == "Sim":
        return "Atendimento realizado", "green", "A realização do atendimento foi registrada pela rede de saúde."
    if process["indicador_atraso"] == "Sim":
        return "Cumprimento pendente", "amber", "O atendimento segue pendente após o prazo registrado. Confira abaixo quem procurar."
    return "Atendimento em preparação", "teal", f"Etapa atual: {process['etapa_saude']}."


def status_cards(process) -> str:
    cards = []
    for kind, title, symbol, state, footer in (
        ("justice", "Na Justiça", "scales", court_status(process), '<strong>Responsável:</strong> Poder Judiciário'),
        ("health", "Na saúde", "medical", health_status(process), 'Uma decisão favorável não significa que o atendimento já foi realizado.'),
    ):
        label, tone, description = state
        state_symbol = "check" if tone in ("green", "teal") else "alert" if tone == "red" else "clock"
        cards.append(
            f'<section class="patient-status-card {kind}" aria-label="{title}">'
            f'<div class="patient-status-main"><div class="patient-status-symbol">{icon(symbol,36)}</div>'
            f'<div class="patient-status-copy"><h2 class="patient-status-title">{title}</h2>'
            f'<span class="patient-badge {tone}">{icon(state_symbol,13)}{escape(label)}</span>'
            f'<p class="patient-status-description">{escape(description)}</p></div></div>'
            f'<div class="patient-status-footer">{footer}</div></section>'
        )
    return '<div class="patient-status-grid">' + "".join(cards) + "</div>"


def _render_records(rows: pd.DataFrame) -> None:
    for index, process in rows.iterrows():
        with st.container(border=True, key=f"patient_record_{index}"):
            label, tone, _ = court_status(process)
            st.markdown(
                f'<div class="patient-record-label">Processo {escape(str(process["processo_id"]))} · Registrado em {date_label(process["data_ajuizamento"])}</div>'
                f'<h2 class="patient-record-title">{escape(str(process["item_demandado"]))}</h2>'
                f'<span class="patient-badge {tone}">{icon("clock",13)}{escape(label)}</span>'
                '<div class="patient-record-details">'
                f'<div><strong>NA JUSTIÇA</strong>{escape(str(process["etapa_judicial"]))}</div>'
                f'<div><strong>NA SAÚDE</strong>{escape(str(process["etapa_saude"]))}</div></div>', unsafe_allow_html=True,
            )
            st.button("Acompanhar este pedido →", key=f"patient_open_{index}", on_click=open_patient_process, args=(str(process["processo_id"]),))


def _render_documents(rows: pd.DataFrame) -> None:
    st.markdown('<p class="patient-discreet-note">Seus resumos de acompanhamento, reunidos em um só lugar. Documentos e decisões oficiais devem ser obtidos com o tribunal ou seu representante.</p>', unsafe_allow_html=True)
    for index, process in rows.iterrows():
        with st.container(border=True, key=f"patient_document_{index}"):
            st.markdown(
                '<div class="patient-panel-heading"><div class="patient-panel-icon">'
                f'{icon("document",29)}</div><div><div class="patient-record-label">RESUMO DO ACOMPANHAMENTO</div>'
                f'<h2 class="patient-panel-title">{escape(str(process["item_demandado"]))}</h2>'
                f'<p class="patient-panel-sub">{escape(str(process["processo_id"]))} · Última movimentação: {date_label(process["ultima_movimentacao_data"])}</p></div></div>', unsafe_allow_html=True,
            )
            download_summary(process, f"document_pdf_{index}")


def _render_help(process_id: str) -> None:
    with st.container(border=True, key="patient_help"):
        st.markdown(
            '<div class="patient-panel-heading"><div class="patient-panel-icon">'
            f'{icon("chat",28)}</div><div><h2 class="patient-panel-title">Precisa de ajuda?</h2>'
            '<p class="patient-panel-sub">Encontre os contatos ou informe um problema com seu pedido.</p></div></div>', unsafe_allow_html=True,
        )
        contact, report = st.columns(2)
        with contact:
            st.button("Ver contatos", key="patient_contact_button", use_container_width=True, on_click=open_patient_help, args=("contact",process_id))
        with report:
            st.button("Relatar problema", key="patient_report_button", use_container_width=True, on_click=open_patient_help, args=("report",process_id))


def render_patient_page(page: str, base: pd.DataFrame) -> None:
    if base.empty:
        st.markdown(
            f'<div class="patient-empty">{icon("document",38)}<h2>Nenhum pedido para acompanhar</h2>'
            '<p>Ainda não há processos vinculados à sua conta.<br>Se precisar, a equipe pode ajudar a conferir seu cadastro.</p></div>', unsafe_allow_html=True,
        )
        st.button("Encontrar ajuda", key="patient_empty_help", on_click=open_patient_help)
        return
    rows = base.sort_values("ultima_movimentacao_data", ascending=False).drop_duplicates("processo_id")
    if page == "Meus processos":
        _render_records(rows)
        return
    if page == "Meus documentos":
        _render_documents(rows)
        return

    st.markdown('<div class="patient-order-heading"><span class="patient-order-label">Pedido selecionado</span></div>', unsafe_allow_html=True)
    process_ids = rows["processo_id"].astype(str).tolist()
    if st.session_state.get("patient_process") not in process_ids:
        st.session_state.pop("patient_process", None)
    labels = rows.assign(processo_id=rows["processo_id"].astype(str)).set_index("processo_id")["item_demandado"].astype(str).to_dict()
    repeated_items = rows["item_demandado"].duplicated(keep=False)
    duplicate_ids = set(rows.loc[repeated_items, "processo_id"].astype(str))
    selected = st.selectbox(
        "Pedido que deseja acompanhar", process_ids,
        format_func=lambda value: f"{labels[value]} · {value}" if value in duplicate_ids else labels[value], key="patient_process", label_visibility="collapsed",
    )
    process = rows[rows["processo_id"].astype(str) == selected].iloc[0]
    long_item = f'{escape(str(process["item_demandado"]))} · ' if len(str(process["item_demandado"])) > 45 else ""
    st.markdown(f'<div class="patient-process-caption">{long_item}Processo {escape(str(process["processo_id"]))} · Pedido registrado em {date_label(process["data_ajuizamento"])}</div>', unsafe_allow_html=True)
    st.markdown(status_cards(process), unsafe_allow_html=True)
    guidance = patient_guidance(process)
    overdue = process["indicador_atraso"] == "Sim"
    deadline = date_label(process["data_limite_cumprimento"])
    if overdue:
        deadline += " · Prazo vencido"
    st.markdown(
        f'<section class="patient-next-card{" overdue" if overdue else ""}" aria-label="Próximo passo">'
        f'<div class="patient-next-main"><div class="patient-next-symbol">{icon("arrow",24)}</div>'
        '<div class="patient-next-body"><div class="patient-next-eyebrow">Qual é o próximo passo?</div>'
        f'<h2 class="patient-next-title">{escape(str(process["proxima_etapa"]))}</h2>'
        '<div class="patient-next-details"><div class="patient-next-detail">'
        f'{icon("person",21)}<div><div class="patient-next-detail-label">Quem acompanha</div>'
        f'<div class="patient-next-detail-value">{escape(str(process["responsavel_etapa"]))}</div></div></div>'
        f'<div class="patient-next-detail">{icon("calendar",21)}<div><div class="patient-next-detail-label">Prazo informado</div>'
        f'<div class="patient-next-detail-value">{escape(deadline)}</div></div></div></div></div></div>'
        f'<div class="patient-next-guidance">{icon("alert" if overdue else "info",16)}<span>{escape(guidance)}</span></div></section>', unsafe_allow_html=True,
    )
    with st.container(key="patient_bottom"):
        movement, help_column = st.columns(2)
        with movement:
            with st.container(border=True, key="patient_movement"):
                st.markdown(
                    '<div class="patient-panel-heading"><div class="patient-panel-icon">'
                    f'{icon("document",28)}</div><div><h2 class="patient-panel-title">Última movimentação</h2>'
                    f'<div class="patient-movement-date">{date_label(process["ultima_movimentacao_data"])}</div>'
                    f'<p class="patient-movement-text">{escape(str(process["ultima_movimentacao"]))}</p></div></div>', unsafe_allow_html=True,
                )
        with help_column:
            _render_help(str(process["processo_id"]))
    with st.container(key="patient_actions"):
        action, note = st.columns([3,2])
        with action:
            download_summary(process, "patient_pdf", compact=True)
        with note:
            st.markdown('<div class="patient-discreet-note">Resumo em PDF · Guarde ou compartilhe com quem acompanha seu pedido.</div>', unsafe_allow_html=True)
    with st.container(border=True):
        st.subheader("Ouvir o resumo do meu pedido")
        speech_summary(f"Pedido {process['item_demandado']}. Na Justiça: {process['etapa_judicial']}. Na saúde: {process['etapa_saude']}. Próximo passo: {process['proxima_etapa']}. Responsável: {process['responsavel_etapa']}. Prazo: {date_label(process['data_limite_cumprimento'])}. {guidance}")
    with st.container(border=True):
        st.subheader("Etapas de acompanhamento")
        st.markdown(TIMELINE_CSS, unsafe_allow_html=True)
        for title, stages, current, status, health in (
            ("Na Justiça", JUDICIAL_STAGES, int(process["etapa_judicial_ordem"]), str(process["etapa_judicial"]), False),
            ("Na rede de saúde", HEALTH_STAGES[process["tipo_fluxo_saude"]], int(process["etapa_saude_ordem"]), str(process["etapa_saude"]), True),
        ):
            st.markdown(timeline_html(title, stages, current, status, health=health,
                                     contrast=bool(st.session_state.get("a11y_contrast", False))), unsafe_allow_html=True)
        st.caption("As etapas são marcos de acompanhamento e não medem a chance de ganhar o processo.")
    with st.container(border=True):
        st.subheader("Como ler as datas e os prazos")
        st.write("Os prazos são apresentados em dias corridos após a intimação. A referência dos cálculos está na faixa de privacidade no topo. Uma decisão favorável e a realização do atendimento são acontecimentos diferentes.")
