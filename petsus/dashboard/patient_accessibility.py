"""Recursos de leitura e comunicação exclusivos da área do paciente."""
from __future__ import annotations

import json

import streamlit as st
import streamlit.components.v1 as components


def patient_accessibility_css(reading: bool, reduced_motion: bool) -> str:
    css = """
    .stApp:has(.patient-accessibility-marker) :focus-visible {outline:3px solid #B45309!important;outline-offset:4px!important;}
    .stApp:has(.patient-accessibility-marker) button {min-height:44px;}
    .patient-skip-link {display:inline-block;padding:.65rem .9rem;text-decoration:underline!important;font-weight:700;}
    """
    if reading:
        css += """
        .stApp:has(.patient-accessibility-marker) [data-testid="stMain"] p,
        .stApp:has(.patient-accessibility-marker) [data-testid="stMain"] label,
        .stApp:has(.patient-accessibility-marker) [data-testid="stMain"] li,
        .stApp:has(.patient-accessibility-marker) [data-testid="stMain"] small,
        .stApp:has(.patient-accessibility-marker) [data-testid="stMain"] .patient-process-caption,
        .stApp:has(.patient-accessibility-marker) [data-testid="stMain"] .patient-next-detail-value,
        .stApp:has(.patient-accessibility-marker) [data-testid="stMain"] .patient-badge {font-size:1.2rem!important;line-height:1.8!important;}
        .stApp:has(.patient-accessibility-marker) .patient-status-grid {grid-template-columns:1fr!important;}
        .stApp:has(.patient-accessibility-marker) .care-track-steps {grid-template-columns:1fr!important;}
        .stApp:has(.patient-accessibility-marker) .portal-heading-row > svg {display:none!important;}
        """
    if reduced_motion:
        css += ".stApp:has(.patient-accessibility-marker) *,.stApp:has(.patient-accessibility-marker) *::before,.stApp:has(.patient-accessibility-marker) *::after {animation:none!important;transition:none!important;scroll-behavior:auto!important;}"
    return css


def render_patient_accessibility() -> None:
    with st.container(border=True, key="patient_accessibility"):
        st.subheader("Recursos de acessibilidade")
        st.markdown('<a class="patient-skip-link" href="#patient-main-content" target="_self">Ir para o conteúdo da página</a>', unsafe_allow_html=True)
        st.checkbox("Leitura facilitada: texto maior e cartões em uma coluna", key="patient_reading_mode")
        st.checkbox("Desativar animações", key="patient_reduce_motion")
        st.caption("Use A−, A+ e Contraste no topo para ajustar a tela. Pelo teclado: Tab avança, Shift + Tab volta e Enter aciona os botões. Nas listas, use as setas.")
        st.caption("Você pode usar a página sem ouvir áudio. O resumo falado também aparece por escrito, e as situações são identificadas com palavras. Para pedir ajuda por escrito, use Ajuda e contato → Relatar problema.")
    css = patient_accessibility_css(bool(st.session_state.get("patient_reading_mode")), bool(st.session_state.get("patient_reduce_motion")))
    st.markdown(f'<style>{css}</style><span class="patient-accessibility-marker" aria-hidden="true"></span><div id="patient-main-content" tabindex="-1"></div>', unsafe_allow_html=True)


def patient_speech_html(text: str, contrast: bool = False, large: bool = False) -> str:
    payload = json.dumps(str(text), ensure_ascii=True).replace("<", "\\u003c")
    background, foreground, accent = ("#000", "#FFF", "#83D6FF") if contrast else ("#FFF", "#173653", "#087F8C")
    style = f"body{{margin:0;background:{background};color:{foreground};font:{20 if large else 17}px/1.6 Arial,sans-serif}}button,select{{font:inherit;min-height:44px;border:2px solid {accent};border-radius:8px;background:{background};color:{foreground};padding:.4rem .7rem}}.buttons{{display:flex;gap:.5rem;flex-wrap:wrap;margin-top:.8rem}}:focus-visible{{outline:3px solid {accent};outline-offset:3px}}button:disabled{{opacity:.6}}"
    return '<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><style>' + style + '</style></head><body>' + """
    <label for="speed">Velocidade da leitura</label>
    <select id="speed"><option value="0.7">Mais devagar</option><option value="0.9" selected>Normal</option><option value="1.1">Mais rápida</option></select>
    <div class="buttons"><button id="read" type="button">Ouvir resumo</button><button id="pause" type="button" disabled>Pausar</button><button id="resume" type="button" disabled>Continuar</button><button id="stop" type="button" disabled>Parar</button></div>
    <p id="status" role="status" aria-live="polite" aria-atomic="true">O áudio só começa quando você escolher Ouvir resumo.</p>
    <script>
    const summary = """ + payload + """;
    const el = id => document.getElementById(id);
    const available = 'speechSynthesis' in window && 'SpeechSynthesisUtterance' in window;
    let current = null;
    function state(speaking, paused=false){el('pause').disabled=!speaking||paused;el('resume').disabled=!paused;el('stop').disabled=!speaking;}
    if(!available){el('read').disabled=true;el('speed').disabled=true;el('status').textContent='Este navegador não oferece leitura em voz alta. O resumo completo está escrito logo acima.';}
    el('read').onclick=()=>{
        if(!available)return;
        current=null;window.speechSynthesis.cancel();
        const utterance=new SpeechSynthesisUtterance(summary);current=utterance;
        utterance.lang='pt-BR';utterance.rate=Number(el('speed').value);
        const voice=window.speechSynthesis.getVoices().find(v=>v.lang.toLowerCase().replace('_','-')==='pt-br');
        if(voice)utterance.voice=voice;
        utterance.onend=()=>{if(current!==utterance)return;current=null;state(false);el('status').textContent='Leitura concluída.';};
        utterance.onerror=()=>{if(current!==utterance)return;current=null;state(false);el('status').textContent='Não foi possível reproduzir o áudio. Leia o resumo escrito acima ou tente outro navegador.';};
        state(true);el('status').textContent='Lendo o resumo.';window.speechSynthesis.speak(utterance);
    };
    el('pause').onclick=()=>{if(!available||!current)return;window.speechSynthesis.pause();state(true,true);el('status').textContent='Leitura pausada. Escolha Continuar para retomar.';};
    el('resume').onclick=()=>{if(!available||!current)return;window.speechSynthesis.resume();state(true);el('status').textContent='Leitura retomada.';};
    el('stop').onclick=()=>{if(!available)return;current=null;window.speechSynthesis.cancel();state(false);el('status').textContent='Leitura interrompida.';};
    window.addEventListener('pagehide',()=>{current=null;if(available)window.speechSynthesis.cancel();});
    </script></body></html>"""


def patient_speech_summary(text: str) -> None:
    st.write(text)
    components.html(patient_speech_html(text, contrast=bool(st.session_state.get("a11y_contrast")),
        large=bool(st.session_state.get("a11y_large_text") or st.session_state.get("patient_reading_mode"))), height=280, scrolling=True)
