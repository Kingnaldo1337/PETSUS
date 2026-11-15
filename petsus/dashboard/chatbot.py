"""Assistente de dúvidas frequentes, sem acesso à base ou serviços externos."""
from __future__ import annotations

import re
import unicodedata
import time

import streamlit as st
from petsus.dashboard.chat_ai import ChatServiceError, generate_answer
from petsus.dashboard.support import setting


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
        st.session_state["support_chat_last_send"] = 0.0

    def send(question: str | None = None) -> None:
        question = (question or st.session_state.get("support_chat_question", "")).strip()[:500]
        if question:
            now = time.monotonic()
            if now - st.session_state.get("support_chat_last_send", 0.0) < 5:
                st.session_state["support_chat_notice"] = "Aguarde alguns segundos antes de enviar outra pergunta."
                return
            st.session_state["support_chat_last_send"] = now
            history = st.session_state["support_chat_history"]
            if setting("GEMINI_API_KEY"):
                try:
                    with st.spinner("Preparando resposta..."):
                        answer = generate_answer(question, history, is_manager=user.is_manager)
                except ChatServiceError as error:
                    answer = str(error)
            else:
                answer = "A IA ainda não está configurada. Orientação automática: " + answer_question(question, is_manager=user.is_manager)
            history.extend([
                {"role": "user", "text": question},
                {"role": "assistant", "text": answer},
            ])
            st.session_state["support_chat_history"] = history[-20:]

    st.markdown("""<style>
    .st-key-support_chat_launcher{position:fixed!important;bottom:1.2rem;right:1.2rem;
        z-index:99990;width:auto!important;max-width:calc(100vw - 2rem)!important;}
    .st-key-support_chat_launcher [data-testid="stPopoverButton"]{box-shadow:0 8px 28px #102F5633;
        border-radius:28px;min-height:50px;background:#087F8C;color:white;border:1px solid #087F8C;padding:.65rem 1.1rem;}
    [data-testid="stPopoverBody"]:has(.st-key-support_chat_body){width:410px!important;
        max-width:calc(100vw - 24px)!important;max-height:calc(100dvh - 100px);overflow-y:auto;
        border:1px solid #DCE7EF;border-radius:22px;box-shadow:0 20px 65px #102F5626;padding:1.1rem;}
    .st-key-support_chat_body p{line-height:1.6;font-size:.95rem;}
    .support-chat-heading{display:flex;align-items:center;gap:12px;padding:0 0 15px;border-bottom:1px solid #94A3B833;}
    .support-chat-symbol{display:grid;place-items:center;width:43px;height:43px;border-radius:14px;
        background:linear-gradient(135deg,#102F56,#087F8C);color:#fff;font-size:25px;}
    .support-chat-title{font-size:1rem;font-weight:750;margin:0;}
    .support-chat-subtitle{font-size:.8rem;opacity:.7;margin-top:2px;}
    .support-chat-welcome{display:flex;flex-direction:column;align-items:center;justify-content:center;
        min-height:235px;text-align:center;padding:1.25rem .8rem;animation:chat-welcome-in .3s ease-out;}
    .support-chat-welcome-symbol{display:grid;place-items:center;width:64px;height:64px;border-radius:22px;
        background:#087F8C12;color:#087F8C;font-size:32px;margin-bottom:16px;}
    .support-chat-welcome h3{font-size:1.2rem;margin:0 0 8px;padding:0;}
    .support-chat-welcome p{max-width:270px;margin:0;opacity:.75;}
    .st-key-support_chat_body [data-testid="stChatMessage"]{border-radius:16px;border:1px solid #94A3B826;padding:12px;}
    .st-key-support_chat_body [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]){background:#087F8C0D;}
    .st-key-support_chat_body [data-testid="stForm"]{padding:12px!important;border:1px solid #94A3B840;border-radius:16px;}
    .st-key-support_chat_body [data-testid="stFormSubmitButton"] button{border-radius:10px;}
    .st-key-support_chat_body [data-testid="stCaptionContainer"] p{font-size:.75rem;line-height:1.5;}
    @keyframes chat-welcome-in{from{opacity:0;transform:translateY(6px);}to{opacity:1;transform:translateY(0);}}
    @media(prefers-reduced-motion:reduce){.support-chat-welcome{animation:none;}}
    @media(max-height:650px){.st-key-support_chat_messages{height:180px!important;}.support-chat-welcome{min-height:145px;}}
    .stApp [data-testid="stMain"] .block-container{padding-bottom:5.5rem!important;}
    </style>""", unsafe_allow_html=True)
    with st.container(key="support_chat_launcher"):
        with st.popover("Tirar dúvidas", icon=":material/chat_bubble_outline:"):
            with st.container(key="support_chat_body"):
                st.markdown(
                    '<div class="support-chat-heading"><span class="support-chat-symbol" aria-hidden="true">✦</span>'
                    '<div><div class="support-chat-title">Assistente DASHJUS</div>'
                    '<div class="support-chat-subtitle">Uma ajuda para usar o portal</div></div></div>',
                    unsafe_allow_html=True,
                )
                if notice := st.session_state.pop("support_chat_notice", None):
                    st.info(notice)
                with st.container(height=280, border=False, key="support_chat_messages"):
                    if not st.session_state["support_chat_history"]:
                        st.markdown(
                            '<div class="support-chat-welcome"><span class="support-chat-welcome-symbol" aria-hidden="true">✦</span>'
                            '<h3>Olá! Como posso ajudar?</h3>'
                            '<p>Escreva sua dúvida abaixo para começar nossa conversa.</p></div>',
                            unsafe_allow_html=True,
                        )
                    for message in st.session_state["support_chat_history"]:
                        with st.chat_message(message["role"]):
                            st.text(message["text"])
                with st.form("support_chat_form", clear_on_submit=True):
                    st.text_input("Sua dúvida", key="support_chat_question", max_chars=500,
                                  placeholder="Digite sua dúvida aqui...", label_visibility="collapsed")
                    st.form_submit_button("Enviar mensagem", on_click=send, use_container_width=True, type="primary")
                st.caption("Suas mensagens são enviadas à IA do Google. Não informe CPF, senhas ou dados de saúde. A IA pode errar.")
                st.button("Limpar conversa", key="support_chat_clear",
                          on_click=lambda: st.session_state.update(support_chat_history=[]))
