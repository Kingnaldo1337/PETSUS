"""Ajuda, transparência de atualização e retorno dos usuários."""
from __future__ import annotations

from petsus.dashboard.table_layout import compact_column_config

from datetime import datetime, timedelta
import hashlib
import os
from pathlib import Path
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st

from petsus.governance import FEEDBACK_CATEGORIES, FEEDBACK_STATUSES

APP_VERSION = "2.0.0"
RELEASE_DATE = "09/11/2026"
TZ = ZoneInfo("America/Fortaleza")
GLOSSARY = {
    "Liminar": "Decisão provisória, que pode ser tomada antes da decisão final. Sim significa concessão registrada.",
    "Procedente / parcialmente procedente": "O pedido foi acolhido por inteiro / em parte. Em andamento significa que não há resultado final registrado.",
    "Competência / esfera": "Indicam qual ramo da Justiça examina o processo. São diferentes do órgão que entrega o tratamento.",
    "RENAME": "Relação Nacional de Medicamentos Essenciais, referência de medicamentos e insumos do SUS.",
    "DCB": "Denominação Comum Brasileira: o nome do princípio ativo do medicamento.",
    "PCDT": "Protocolo Clínico e Diretriz Terapêutica: orientações para diagnóstico e tratamento no SUS.",
    "CMED / PMVG": "Câmara de Regulação do Mercado de Medicamentos / Preço Máximo de Venda ao Governo. Preços variam conforme apresentação e condições da compra.",
    "Intimação": "Comunicação formal de uma decisão à pessoa ou ao órgão responsável.",
    "Regulação": "Organização do acesso a consultas, exames e procedimentos na rede de saúde.",
    "Assistência básica / especializada": "Componentes da assistência farmacêutica com regras próprias de financiamento, acesso e dispensação.",
    "Pedido urgente": "Indica pedido de análise urgente no processo. Não comprova risco clínico nem significa que a liminar foi concedida.",
}
SUS_QUESTIONS = (
    "Eu gostaria de usar este sistema com frequência.",
    "O sistema pareceu mais complexo do que eu precisava.",
    "Foi fácil usar o sistema.",
    "Eu dependeria de alguém com conhecimento técnico para usá-lo.",
    "As funções do sistema funcionam bem em conjunto.",
    "Percebi falta de consistência entre partes do sistema.",
    "Imagino que a maioria das pessoas aprenderia a usá-lo rapidamente.",
    "Achei trabalhoso usar o sistema.",
    "Senti confiança ao usar o sistema.",
    "Precisei aprender muitas coisas antes de conseguir usá-lo.",
)


def setting(name: str, default: str = "") -> str:
    value = os.getenv(name)
    if value is not None:
        return value.strip()
    try:
        return str(st.secrets.get(name, default)).strip()
    except (FileNotFoundError, st.errors.StreamlitSecretNotFoundError):
        return default


def data_metadata(path: Path) -> dict:
    modified = datetime.fromtimestamp(path.stat().st_mtime, TZ)
    try:
        interval = max(0, int(setting("PETSUS_UPDATE_INTERVAL_DAYS", "0")))
    except ValueError:
        interval = 0
    return {
        "modified": modified,
        "fingerprint": hashlib.sha256(path.read_bytes()).hexdigest(),
        "interval": interval,
        "next": modified + timedelta(days=interval) if interval else None,
        "owner": setting("PETSUS_DATA_OWNER", "Equipe gestora do projeto"),
    }


def render_data_freshness(metadata: dict, reference_date) -> None:
    reference = pd.Timestamp(reference_date).strftime("%d/%m/%Y")
    st.session_state["metrics_reference"] = reference
    st.caption(
        f"Arquivo atualizado em {metadata['modified']:%d/%m/%Y às %H:%M} (Fortaleza) · "
        f"Referência dos cálculos e dos prazos: {reference} · Versão {APP_VERSION}"
    )
    st.caption("O período seleciona a data de entrada dos processos. As situações e os prazos usam a data de referência acima; esta tela não reconstrói uma situação histórica.")


def render_contacts() -> None:
    with st.container(border=True):
        st.subheader("Precisa de ajuda?")
        legal = setting("PETSUS_LEGAL_CONTACT")
        support = setting("PETSUS_SUPPORT_CONTACT")
        st.write(legal if legal else "Para orientação sobre seu pedido, procure a Defensoria ou o advogado que já acompanha o processo. O contato específico do responsável ainda não foi cadastrado pela equipe.")
        st.link_button("Encontrar a Defensoria Pública", "https://www.cnj.jus.br/poder-judiciario/defensoria-publica/")
        if support:
            st.write(f"Suporte da plataforma: {support}")
        st.write("Para informar dados incorretos, dificuldade de acesso ou sugestões, use Ajuda e contato no menu. O relato será recebido pela equipe gestora.")
        url = setting("PETSUS_LEGAL_CONTACT_URL")
        parsed = urlparse(url)
        if parsed.scheme in ("https", "http") and parsed.netloc:
            st.link_button("Abrir contato do responsável", url)


def local_timestamp(value) -> str:
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        timestamp = timestamp.tz_localize("UTC")
    return timestamp.tz_convert(TZ).strftime("%d/%m/%Y às %H:%M (Fortaleza)")


def render_patient_faq() -> None:
    st.subheader("Principais dúvidas")
    with st.container(border=True):
        st.markdown("### Como ler as datas e os prazos?")
        st.write("O prazo informado é o prazo registrado para a equipe responsável cumprir a decisão. Ele não é uma data de consulta ou de entrega confirmada.")
        st.write("‘Ainda não informado’ significa que não há uma data registrada. Se aparecer ‘Prazo vencido’, procure os contatos no início desta página.")
        st.write("Os dias mostrados no acompanhamento são corridos: incluem sábados, domingos e feriados.")
        st.write("A última atualização indica quando a informação mais recente foi registrada no acompanhamento.")
    with st.container(border=True):
        st.markdown("### Uma decisão favorável significa que meu atendimento já foi realizado?")
        st.write("A decisão da Justiça e o atendimento na rede de saúde são etapas diferentes. Em ‘Meu acompanhamento’, veja as informações de ‘Na Justiça’ e ‘Na saúde’ para conferir cada uma.")
    with st.container(border=True):
        st.markdown("### Como aviso sobre uma informação incorreta ou um problema?")
        st.write("Use ‘Relatar e acompanhar’, abaixo. Escolha o processo relacionado, descreva o problema e clique em ‘Registrar relato’. A resposta da equipe aparecerá nessa mesma seção.")


def render_support_page(user, store, base: pd.DataFrame, metadata: dict) -> None:
    render_contacts()
    if not user.is_manager:
        render_patient_faq()
    support_intent = st.session_state.pop("patient_support_intent", None)
    if not user.is_manager and support_intent == "report":
        st.info("Conte o que precisa ser conferido em Relatar e acompanhar. O processo selecionado já está vinculado ao formulário abaixo.")
    feedback_tab, glossary_tab, about_tab, survey_tab = st.tabs(["Relatar e acompanhar", "Glossário", "Sobre os dados", "Avaliar uso"])
    with feedback_tab:
        st.subheader("Relatar erro ou sugerir melhoria")
        st.caption("Evite informar CPF, senha ou detalhes clínicos no texto. Relatos ficam visíveis à equipe gestora e a você.")
        with st.form("feedback_form", clear_on_submit=True):
            category = st.selectbox("Tipo de relato", FEEDBACK_CATEGORIES)
            process_ids = [""] + base["processo_id"].drop_duplicates().astype(str).tolist()
            if st.session_state.get("feedback_process", "") not in process_ids:
                st.session_state.pop("feedback_process", None)
            process_id = st.selectbox("Processo relacionado (opcional)", process_ids, format_func=lambda value: value or "Sem processo específico", key="feedback_process")
            description = st.text_area("Descreva o problema ou a sugestão", max_chars=4000)
            submitted = st.form_submit_button("Registrar relato")
        if submitted:
            try:
                number = store.submit_feedback(user, category, description, process_id or None)
                st.success(f"Relato #{number} registrado. Acompanhe a resposta abaixo.")
            except ValueError as exc:
                st.error(str(exc))
        st.subheader("Acompanhar relatos" if not user.is_manager else "Relatos recebidos")
        feedback = store.list_feedback(user)
        if not feedback:
            st.info("Nenhum relato registrado.")
        for item in feedback:
            with st.expander(f"#{item['id']} · {item['category']} · {item['status']}"):
                st.write(item["description"])
                st.caption(f"Registrado em {local_timestamp(item['created_at'])}" + (f" · Processo {item['process_id']}" if item.get("process_id") else ""))
                if item.get("response"):
                    st.write(f"**Resposta da equipe:** {item['response']}")
                if user.is_manager:
                    with st.form(f"review_feedback_{item['id']}"):
                        status = st.selectbox("Situação", FEEDBACK_STATUSES, index=list(FEEDBACK_STATUSES).index(item["status"]))
                        response = st.text_area("Resposta ao usuário", value=item.get("response") or "", max_chars=4000)
                        save = st.form_submit_button("Salvar acompanhamento")
                    if save:
                        try:
                            store.update_feedback(user, item["id"], status, response)
                            st.rerun()
                        except ValueError as exc:
                            st.error(str(exc))
    with glossary_tab:
        for term, meaning in GLOSSARY.items():
            st.write(f"**{term}:** {meaning}")
    with about_tab:
        st.subheader("Atualização e conferência")
        st.write(f"**Responsável pela conferência:** {metadata['owner']}.")
        st.write(f"**Última alteração do arquivo:** {metadata['modified']:%d/%m/%Y às %H:%M} (Fortaleza). Essa data indica alteração do arquivo local, e não sincronização com sistemas oficiais.")
        st.write("**Alimentação atual:** substituição manual da planilha validada. A aplicação verifica alterações do arquivo ao recarregar. Integrações oficiais e agendamento automático ainda não estão conectados.")
        if metadata["next"]:
            st.write(f"**Próxima revisão planejada:** {metadata['next']:%d/%m/%Y} · periodicidade configurada de {metadata['interval']} dias. O planejamento não executa uma importação automática.")
        else:
            st.write("**Próxima atualização:** sem agendamento definido pela equipe.")
        st.write("A leitura verifica campos obrigatórios, datas, valores e duplicidades. Um erro de estrutura interrompe a carga; a equipe deve conferir as informações antes de substituir a planilha. Dados incorretos podem ser comunicados em Relatar e acompanhar.")
        if user.is_manager:
            review = store.latest_data_review(user, metadata["fingerprint"])
            if review:
                st.success(f"Conferência deste arquivo registrada em {local_timestamp(review['reviewed_at'])}: {review['note']}")
            else:
                st.warning("Este arquivo ainda não tem conferência humana registrada.")
            with st.form("data_review"):
                note = st.text_area("Resultado da conferência do arquivo", max_chars=2000)
                confirmed = st.checkbox("Conferi a origem, o período, a quantidade de registros e uma amostra dos dados")
                save = st.form_submit_button("Registrar conferência")
            if save:
                if not confirmed:
                    st.error("Confirme a conferência antes de registrá-la.")
                else:
                    try:
                        store.record_data_review(user, metadata["fingerprint"], note)
                        st.rerun()
                    except ValueError as exc:
                        st.error(str(exc))
        st.subheader("Fontes e limites")
        st.write("Consulte a origem, o período e a metodologia dos indicadores no dicionário de dados do projeto. As integrações com sistemas oficiais ainda não estão ativas.")
        st.markdown("Referências para consulta: [DataJud/CNJ](https://www.cnj.jus.br/sistemas/datajud/api-publica/), [RENAME/Ministério da Saúde](https://www.gov.br/saude/pt-br/composicao/sectics/rename) e [CMED/Anvisa](https://www.gov.br/anvisa/pt-br/assuntos/medicamentos/cmed). Cumprimento assistencial precisa de informação validada da rede de saúde.")
        st.write("Na análise gerencial, CPFs são mascarados e grupos com menos de cinco pacientes distintos são suprimidos. A consulta operacional de um processo exige perfil autorizado. Exportações seguem a proteção da tabela exibida.")
        st.write(f"**Histórico — {APP_VERSION} · {RELEASE_DATE}:** portal próprio do paciente, definições de métricas, gráficos comparáveis, privacidade analítica, revisão de contas, auditoria, feedback e acessibilidade.")
        if user.is_manager:
            st.subheader("Uso da plataforma")
            usage = store.usage_summary(user)
            if usage:
                frame = pd.DataFrame(usage).rename(columns={"date": "Data", "role": "Perfil", "page": "Página", "views": "Visitas"})
                st.dataframe(frame, hide_index=True, width="content", column_config=compact_column_config(frame))
            else:
                st.info("Ainda não há acessos registrados.")
            st.caption("Contagem de visitas por sessão, perfil e página, sem nome, CPF ou identificação do paciente.")
            results = store.sus_summary(user)
            st.write(f"Avaliações de uso: {results['count']}" + (f" · média: {results['average_score']:.1f} / 100" if results["count"] else ""))
    with survey_tab:
        st.subheader("Sua experiência com a plataforma")
        st.write("Depois de consultar um processo ou analisar os dados, responda às dez afirmações. 1 = discordo totalmente; 5 = concordo totalmente.")
        st.caption("Adaptação em português dos itens da System Usability Scale (SUS). Não é uma tradução validada para pesquisa. A avaliação é opcional e não registra sua identidade.")
        with st.form("sus_form"):
            answers = [st.radio(f"{index}. {question}", [1, 2, 3, 4, 5], index=None, horizontal=True, key=f"sus_{index}") for index, question in enumerate(SUS_QUESTIONS, 1)]
            send = st.form_submit_button("Enviar avaliação")
        if send:
            try:
                store.submit_sus(user, answers)
                st.success("Avaliação registrada. Obrigado por ajudar a melhorar a plataforma.")
            except (ValueError, TypeError) as exc:
                st.error(str(exc))
        st.caption("Escore de 0 a 100 = 2,5 × soma de (resposta − 1) nos itens ímpares e (5 − resposta) nos pares. Não representa percentual de satisfação.")
        st.markdown("[Referência sobre adaptação brasileira da SUS](https://aquichan.unisabana.edu.co/index.php/aquichan/article/download/16497/7157?inline=1). A coleta disponível aqui deve ser acompanhada de sessões com gestores e pacientes reais.")
