"""Assistente de dúvidas frequentes, sem acesso à base ou serviços externos."""
from __future__ import annotations

import re
import unicodedata

import streamlit as st


def _normalize(text: str) -> str:
    return "".join(char for char in unicodedata.normalize("NFKD", text.lower())
                   if not unicodedata.combining(char))


def answer_question(question: str, *, is_manager: bool = False) -> str:
    text = _normalize(question)
    tokens = set(re.findall(r"[a-z0-9]+", text))
    if tokens.intersection({"senha", "login", "entrar", "acesso", "email", "codigo"}):
        return "Para entrar, use seu CPF e sua senha. Se esqueceu a senha, escolha ‘Esqueceu sua senha?’ na tela de entrada. Se houver validação por e-mail, confira também a caixa de spam. Não envie senhas nem códigos nesta conversa."
    if tokens.intersection({"prazo", "prazos", "data", "datas", "atraso", "atrasado", "vencido"}):
        return "O prazo informado é o prazo registrado para cumprir a decisão; não confirma uma consulta ou entrega. ‘Ainda não informado’ indica ausência de data registrada. ‘Prazo vencido’ indica que o prazo registrado passou. Os dias exibidos são corridos. Procure os contatos em ‘Ajuda e contato’ para esclarecer sua situação."
    if tokens.intersection({"liminar", "procedente", "procedencia", "sentenca", "decisao"}):
        return "Liminar é uma decisão provisória. ‘Procedente’ significa que o pedido foi acolhido; ‘parcialmente procedente’, acolhido em parte. Uma decisão favorável não confirma que o atendimento já aconteceu. Confira separadamente as informações da Justiça e da saúde. Para orientação sobre o seu caso, procure quem acompanha seu processo."
    if tokens.intersection({"contato", "contatos", "advogado", "defensoria", "telefone", "equipe"}):
        return "Abra ‘Ajuda e contato’ no menu. Os contatos cadastrados ficam no início da página, incluindo o acesso à Defensoria Pública. Se um contato específico não estiver cadastrado, procure a Defensoria ou o advogado que já acompanha seu processo."
    if tokens.intersection({"erro", "errado", "incorreto", "problema", "relato", "reclamar"}):
        return "Em ‘Ajuda e contato’, abra ‘Relatar e acompanhar’. Escolha o tipo de relato e o processo relacionado, descreva o problema e clique em ‘Registrar relato’. A resposta fica nessa mesma aba. Evite incluir CPF, senha e detalhes clínicos."
    if tokens.intersection({"pdf", "documento", "documentos", "baixar", "resumo"}):
        return ("Os resumos de acompanhamento podem ser baixados em PDF no perfil de paciente. Documentos e decisões oficiais devem ser obtidos com o tribunal ou com o representante do processo."
                if is_manager else "Abra ‘Meus documentos’ para baixar o resumo em PDF. Você também encontra o botão de resumo em ‘Meu acompanhamento’. Documentos e decisões oficiais devem ser obtidos com o tribunal ou com quem acompanha seu processo.")
    if tokens.intersection({"filtro", "filtros", "periodo", "ajuizamento", "indicadores", "custos"}) and is_manager:
        return "O período de ajuizamento filtra a data de entrada dos processos. Os demais filtros refinam o recorte dos indicadores. Os custos apresentados são estimativas e não comprovam gasto executado. Use os ícones de ajuda dos indicadores para conferir suas definições."
    if tokens.intersection({"rename", "pcdt", "dcb", "cmed", "pmvg", "glossario", "palavras"}):
        return ("Consulte a aba ‘Glossário’, em ‘Ajuda e feedback’, para entender as siglas e os termos dos indicadores."
                if is_manager else "Em ‘Ajuda e contato’, abra ‘Significado das palavras’. Lá você encontra explicações de termos como liminar, RENAME, DCB e PCDT.")
    if tokens.intersection({"acompanhar", "acompanhamento", "etapa", "etapas", "processo", "processos", "andamento", "situacao"}):
        return ("Abra ‘Andamento’ para consultar as etapas do acompanhamento. As informações da Justiça e do cumprimento pela saúde representam partes diferentes do processo. Este assistente explica o uso do painel e não consulta registros individuais."
                if is_manager else "Abra ‘Meu acompanhamento’, escolha seu processo e confira ‘Na Justiça’, ‘Na saúde’ e ‘O que você precisa fazer agora’. A seção ‘Etapas de acompanhamento’ destaca a etapa registrada. Não consulto os dados do seu processo nesta conversa.")
    if tokens.intersection({"oi", "ola", "bom", "boa", "obrigado", "obrigada"}):
        return "Olá! Posso ajudar a usar o DASHJUS. Pergunte sobre acompanhamento, datas e prazos, documentos, contatos ou como relatar um problema."
    return "Ainda não tenho uma resposta para essa dúvida. Posso explicar acompanhamento, prazos, documentos, acesso e contatos. Para uma dúvida sobre seu caso, procure os contatos da página de ajuda ou registre um relato."


def render_chatbot(user) -> None:
    owner = (user.id, user.role, user.session_version)
    if st.session_state.get("support_chat_owner") != owner:
        st.session_state["support_chat_owner"] = owner
        st.session_state["support_chat_history"] = []

    def send(question: str | None = None) -> None:
        question = (question or st.session_state.get("support_chat_question", "")).strip()[:500]
        if question:
            history = st.session_state["support_chat_history"]
            history.extend([
                {"role": "user", "text": question},
                {"role": "assistant", "text": answer_question(question, is_manager=user.is_manager)},
            ])
            st.session_state["support_chat_history"] = history[-20:]

    st.markdown("""<style>
    .st-key-support_chat_launcher{position:fixed!important;bottom:1.2rem;right:1.2rem;
        z-index:99990;width:auto!important;max-width:calc(100vw - 2rem)!important;}
    .st-key-support_chat_launcher button{box-shadow:0 6px 24px #102F5626;border-radius:24px;min-height:48px;}
    [data-testid="stPopoverBody"]:has(.st-key-support_chat_body){width:390px!important;
        max-width:calc(100vw - 24px)!important;max-height:calc(100dvh - 100px);overflow-y:auto;}
    .st-key-support_chat_body p{line-height:1.55;}
    .stApp [data-testid="stMain"] .block-container{padding-bottom:5.5rem!important;}
    </style>""", unsafe_allow_html=True)
    with st.container(key="support_chat_launcher"):
        with st.popover("Tirar dúvidas", icon=":material/chat_bubble_outline:"):
            with st.container(key="support_chat_body"):
                st.markdown("**Assistente DASHJUS**")
                st.caption("Respostas automáticas sobre o uso do sistema. Não envie CPF, senhas ou informações de saúde.")
                with st.container(height=260, border=False):
                    if not st.session_state["support_chat_history"]:
                        st.write("Olá! Em que posso ajudar?")
                        for question in ("Como acompanhar um processo?", "Como entender os prazos?", "Como encontrar os contatos?"):
                            st.button(question, key=f"support_chat_suggestion_{question}", on_click=send, args=(question,))
                    for message in st.session_state["support_chat_history"]:
                        with st.chat_message(message["role"]):
                            st.text(message["text"])
                with st.form("support_chat_form", clear_on_submit=True):
                    st.text_input("Sua dúvida", key="support_chat_question", max_chars=500,
                                  placeholder="Escreva sua pergunta...")
                    st.form_submit_button("Enviar", on_click=send, use_container_width=True)
                st.button("Limpar conversa", key="support_chat_clear",
                          on_click=lambda: st.session_state.update(support_chat_history=[]))
