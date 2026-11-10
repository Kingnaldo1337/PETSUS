"""Preferências visuais e leitura voluntária do resumo, sem reprodução automática."""
from __future__ import annotations

from html import escape
import json

import streamlit as st
import streamlit.components.v1 as components


def render_accessibility_controls(show_sidebar: bool = True) -> None:
    if show_sidebar:
        with st.sidebar.expander("Acessibilidade", expanded=False):
            st.checkbox("Texto ampliado", key="a11y_large_text")
            st.checkbox("Alto contraste", key="a11y_contrast")
            st.caption("Use Tab para navegar e Enter para acionar botões. O resumo do pedido pode ser ouvido na página de acompanhamento.")
    large = st.session_state.get("a11y_large_text", False)
    contrast = st.session_state.get("a11y_contrast", False)
    css = """
    :focus-visible { outline: 3px solid #D97706 !important; outline-offset: 3px !important; }
    @media(prefers-reduced-motion:reduce){*,*::before,*::after{animation:none!important;transition:none!important;scroll-behavior:auto!important;}}
    .patient-status {background:#fff;border:1px solid #CBD5E1;border-radius:16px;padding:1.1rem;height:100%;}
    .patient-status h3 {font-size:1.15rem;margin:0 0 .55rem;}
    .patient-status p {margin:.3rem 0;}
    .patient-next {background:#E8F5FF;border:1px solid #80BFE8;border-radius:16px;padding:1.2rem;margin:1rem 0;}
    .patient-next h3 {margin:0 0 .5rem;}
    .metric-card {height:auto!important;min-height:185px;overflow:visible!important;}
    .metric-value {white-space:normal;line-height:1.2;font-size:clamp(1.25rem,2.1vw,1.82rem);}
    .metric-sub {overflow-wrap:break-word;}
    .card-help:hover::after,.card-help:focus::after{right:0;max-width:calc(100vw - 3rem);}
    /* O botão de abrir a sidebar pertence a stToolbar nas versões atuais. */
    #MainMenu,[data-testid="stToolbarActions"],[data-testid="stAppDeployButton"],footer:not(.auth-support){display:none!important;}
    [data-testid="stExpandSidebarButton"],
    [data-testid="stSidebarCollapsedControl"] button {
        display:inline-flex!important;align-items:center;gap:.35rem;
        visibility:visible!important;opacity:1!important;
        min-width:44px;min-height:44px;padding:.35rem .65rem!important;
        background:#FFFFFF!important;color:#0B2459!important;
        border:1px solid #B6C4D6!important;border-radius:8px;
    }
    [data-testid="stExpandSidebarButton"]::after,
    [data-testid="stSidebarCollapsedControl"] button::after {
        content:"Menu";font-size:.9rem;font-weight:700;
    }
    [data-testid="stExpandSidebarButton"] [data-testid="stIconMaterial"],
    [data-testid="stSidebarCollapsedControl"] button [data-testid="stIconMaterial"] {
        color:#0B2459!important;
    }
    [data-testid="stSidebarCollapseButton"] {visibility:visible!important;}
    [data-testid="stSidebarCollapseButton"] button,
    [data-testid="stSidebarCollapseButton"] [data-testid="stIconMaterial"] {
        color:#FFFFFF!important;opacity:1!important;
    }
    .stApp [data-testid="stMain"] .block-container {padding-top:3.75rem;}
    """
    if large:
        css += "html{font-size:20px!important}.stApp p,.stApp label,.stApp li,.stApp input{font-size:1.1rem!important}.metric-label,.metric-sub,.small-note{font-size:1rem!important}"
    if contrast:
        css += """
        .stApp,[data-testid="stAppViewContainer"],[data-testid="stMain"],.block-container{background:#000!important;color:#fff!important;}
        [data-testid="stMain"] p,[data-testid="stMain"] label,[data-testid="stMain"] h1,[data-testid="stMain"] h2,[data-testid="stMain"] h3,.title-main,.title-sub,.section-title,.footer-note{color:#fff!important;}
        .patient-status,.patient-next,.metric-card,.insight-card,.patient-box,[data-testid="stVerticalBlockBorderWrapper"]{background:#000!important;border:2px solid #fff!important;color:#fff!important;}
        .metric-label,.metric-value,.metric-sub,.insight-title,.insight-value,.insight-desc,.patient-name,.patient-sub,.small-note{color:#fff!important;}
        [data-testid="stMain"] button{background:#000!important;color:#fff!important;border:2px solid #fff!important;}
        [data-testid="stMain"] [data-testid="stForm"],[data-testid="stMain"] details,[data-testid="stMain"] summary{background:#000!important;color:#fff!important;border-color:#fff!important;}
        [data-testid="stMain"] input,[data-testid="stMain"] textarea{background:#000!important;color:#fff!important;-webkit-text-fill-color:#fff!important;}
        a{color:#83D6FF!important;text-decoration:underline;}
        [data-testid="stMain"] .patient-status a,[data-testid="stMain"] .patient-next a{color:#83D6FF!important;}
        """
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def speech_summary(text: str) -> None:
    """O texto permanece disponível mesmo quando o navegador não oferece voz."""
    payload = json.dumps(str(text), ensure_ascii=True).replace("<", "\\u003c")
    components.html(
        """<style>body{font:16px Arial;margin:0}button{background:white;color:#0B2459;border:2px solid #125CC9;border-radius:8px;padding:10px;margin-right:8px;cursor:pointer}button:focus-visible{outline:3px solid #D97706}#status{font-size:14px}</style>
        <button id="read" type="button">Ouvir resumo</button><button id="stop" type="button">Parar leitura</button>
        <p id="status" role="status" aria-live="polite"></p><script>
        const summary = """ + payload + """;
        const status = document.getElementById('status');
        const available = 'speechSynthesis' in window && 'SpeechSynthesisUtterance' in window;
        if(!available){status.textContent='Leitura por voz indisponível neste navegador.';document.getElementById('read').disabled=true;}
        document.getElementById('read').onclick=()=>{if(!available)return;window.speechSynthesis.cancel();const u=new SpeechSynthesisUtterance(summary);u.lang='pt-BR';u.rate=.9;u.onend=()=>status.textContent='Leitura concluída.';u.onerror=()=>status.textContent='Não foi possível reproduzir. O resumo está disponível em texto.';window.speechSynthesis.speak(u);status.textContent='Lendo o resumo.';};
        document.getElementById('stop').onclick=()=>{if(available)window.speechSynthesis.cancel();status.textContent='Leitura interrompida.';};
        window.addEventListener('pagehide',()=>{if(available)window.speechSynthesis.cancel();});
        </script>""",
        height=100,
    )
