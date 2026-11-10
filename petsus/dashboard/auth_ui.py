"""Apresentação do acesso: sem sidebar, com controles de leitura no cabeçalho."""
from __future__ import annotations

import streamlit as st

from petsus.dashboard.accessibility import render_accessibility_controls
from petsus.dashboard.patient_ui import icon, render_display_controls
from petsus.dashboard.motion import MOTION_CSS


def render_auth_shell() -> None:
    render_accessibility_controls(show_sidebar=False)
    css = MOTION_CSS + """
    .auth-screen-marker {display:none;}
    @keyframes auth-loading-spin {to {transform:rotate(360deg);}}
    .stApp:has(.auth-screen-marker) [data-testid="stSpinner"] > div > :first-child {
        animation:auth-loading-spin .85s linear infinite!important;
        transform-origin:center;
    }
    .stApp:has(.auth-screen-marker) [data-testid="stSpinner"] > div > :first-child * {
        animation:none!important;
    }
    .stApp:has(.auth-screen-marker) [data-testid="stSidebar"],
    .stApp:has(.auth-screen-marker) [data-testid="stExpandSidebarButton"],
    .stApp:has(.auth-screen-marker) [data-testid="stSidebarCollapsedControl"],
    .stApp:has(.auth-screen-marker) [data-testid="stSidebarCollapseButton"],
    .stApp:has(.auth-screen-marker) [data-testid="stHeader"] {display:none!important;}
    .stApp:has(.auth-screen-marker) [data-testid="stMain"] {background:radial-gradient(ellipse at 85% 5%,#DEEFF7 0%,#F3F7FC 45%,#F6F8FC 100%);}
    .stApp:has(.auth-screen-marker) [data-testid="stMain"] .block-container {max-width:1280px!important;margin-inline:auto;padding:1.25rem 2rem 2rem!important;}
    .st-key-auth_header [data-testid="stHorizontalBlock"] {display:grid!important;grid-template-columns:minmax(0,1fr) auto;align-items:center;gap:1rem;}
    .st-key-auth_header [data-testid="stColumn"] {width:auto!important;min-width:0!important;flex:unset!important;}
    .auth-brand {display:flex;align-items:center;gap:.65rem;color:#122C50;}
    .auth-brand-symbol {display:flex;align-items:center;gap:.05rem;background:#102F56;padding:.6rem;border-radius:12px;color:#E5F2FC;}
    .auth-brand-symbol svg:last-child {color:#35BAC2;}
    .auth-brand-name {font-size:.84rem;font-weight:800;letter-spacing:.08em;}
    .auth-brand-caption {font-size:.69rem;color:#5D7088;line-height:1.5;margin-top:.1rem;}
    .auth-wrap .auth-brand {flex-direction:column;justify-content:center;gap:.8rem;margin-bottom:1.5rem;}
    .auth-wrap .auth-brand-symbol {padding:1rem;border-radius:20px;box-shadow:0 8px 24px #102F561A;}
    .auth-wrap .auth-brand-name {font-size:clamp(1.2rem,4vw,1.65rem);letter-spacing:.1em;}
    .auth-wrap .auth-brand-caption {font-size:.85rem;margin-top:.25rem;}
    .st-key-auth_display_controls [data-testid="stHorizontalBlock"] {display:flex!important;flex-wrap:nowrap!important;gap:.4rem;}
    .st-key-auth_display_controls [data-testid="stColumn"] {flex:0 0 auto!important;width:auto!important;min-width:0!important;}
    .st-key-auth_display_controls button {min-height:38px;border:1px solid #DCE5F0;border-radius:8px;background:#FFFFFFC9;padding:.35rem .65rem;box-shadow:0 2px 5px #1A3E640A;color:#163653;}
    .st-key-auth_display_controls button p {font-size:.75rem!important;font-weight:650;white-space:nowrap;}
    .auth-wrap {width:min(100%,540px);margin:2.4rem auto 1.3rem;text-align:center;}
    .auth-title {font-size:clamp(1.55rem,3vw,2rem)!important;font-weight:800;line-height:1.2;letter-spacing:-.035em;color:#122C50;margin:0;padding:0;}
    .auth-sub {color:#5D7088;font-size:.88rem!important;line-height:1.65;margin:.65rem auto 0;max-width:420px;}
    .st-key-auth_panel {width:100%!important;max-width:510px!important;min-width:0!important;margin-inline:auto;background:#fff;border:1px solid #DFE7F0;border-radius:18px;padding:1.3rem 1.5rem;box-shadow:0 10px 35px #16375509;}
    .st-key-auth_panel [data-testid="stForm"] {padding:.6rem 0 0;border:0!important;border-radius:0;background:transparent;}
    .st-key-auth_panel [data-testid="stTabs"] {width:100%;min-width:0;}
    .st-key-auth_panel [data-baseweb="tab-list"] {gap:1rem;border-bottom:1px solid #E3EAF2;}
    .st-key-auth_panel [data-baseweb="tab"] {color:#5D7088;padding:.4rem .2rem .75rem;font-weight:650;}
    .st-key-auth_panel [aria-selected="true"] {color:#087F8C!important;}
    .st-key-auth_panel [data-baseweb="tab-highlight"] {background:#087F8C;height:3px;border-radius:3px;}
    .st-key-auth_panel [data-testid="stWidgetLabel"] p {font-size:.8rem;font-weight:600;color:#36536F;}
    .st-key-auth_panel [data-baseweb="input"],.st-key-auth_panel [data-baseweb="select"] > div {background:#F9FBFE;border:1px solid #DCE5EF;border-radius:9px;min-height:44px;}
    .st-key-auth_panel [data-baseweb="input"]:focus-within {border-color:#338D9C;box-shadow:0 0 0 3px #087F8C12;}
    .st-key-auth_panel button {border-radius:9px;min-height:42px;}
    .st-key-auth_panel button[kind="primaryFormSubmit"],.st-key-auth_panel button[kind="primary"] {background:#087F8C;border-color:#087F8C;color:#fff;box-shadow:0 3px 8px #087F8C15;}
    .st-key-auth_panel button[kind="primaryFormSubmit"]:hover,.st-key-auth_panel button[kind="primary"]:hover {background:#066B76;border-color:#066B76;}
    body:has(.auth-screen-marker) [role="dialog"] {border:1px solid #DFE7F0;border-radius:18px;background:#fff;color:#122C50;}
    body:has(.auth-screen-marker) [role="dialog"] button[kind="primaryFormSubmit"] {background:#087F8C;border-color:#087F8C;color:#fff;}
    .st-key-auth_panel [data-testid="stCaptionContainer"] {font-size:.76rem;line-height:1.55;color:#5D7088;}
    .forgot-password-link {display:inline-block;color:#17687E!important;font-size:.79rem;font-weight:600;text-decoration:none;margin:.2rem 0 .3rem;}
    .forgot-password-link:hover,.forgot-password-link:focus {text-decoration:underline;}
    .st-key-forgot_password_button button {padding:.2rem 0;min-height:30px;color:#17687E;background:transparent;border:0;}
    .st-key-forgot_password_button button p {font-size:.79rem;font-weight:600;}
    .st-key-forgot_password_button button:hover {text-decoration:underline;background:transparent;}
    .auth-support {width:min(100%,510px);margin:1.15rem auto .3rem;padding:.9rem .4rem;text-align:center;color:#5D7088;font-size:.76rem;line-height:1.7;}
    .auth-support-title {color:#36536F;font-weight:650;margin-bottom:.35rem;}
    .auth-support a {color:#17687E!important;font-weight:600;text-decoration:none;overflow-wrap:anywhere;}
    .auth-support a:hover,.auth-support a:focus {text-decoration:underline;}
    .auth-support-separator {color:#8B9CAE;padding:0 .3rem;}
    .stApp:has(.auth-screen-marker) [data-testid="stMain"] > div {min-width:0;}
    .stApp:has(.auth-screen-marker) [data-testid="stMain"] h1:not(.auth-title),
    .stApp:has(.auth-screen-marker) [data-testid="stMain"] [data-testid="stForm"]:not(.st-key-auth_panel *) {max-width:510px;margin-inline:auto;}
    @media(max-width:640px) {
        .stApp:has(.auth-screen-marker) [data-testid="stMain"] .block-container {padding:1rem .85rem 1.5rem!important;}
        .st-key-auth_header [data-testid="stHorizontalBlock"] {grid-template-columns:1fr;gap:.9rem;}
        .st-key-auth_display_controls [data-testid="stHorizontalBlock"] {display:flex!important;justify-content:flex-end;}
        .auth-wrap {margin:1.5rem auto 1rem;}
        .st-key-auth_panel {padding:1rem;border-radius:14px;}
    }
    """
    if st.session_state.get("a11y_contrast", False):
        css += """
        .stApp:has(.auth-screen-marker) [data-testid="stMain"],.st-key-auth_panel {background:#000!important;color:#fff!important;border-color:#fff!important;box-shadow:none!important;}
        .auth-brand,.auth-brand-name,.auth-brand-caption,.auth-title,.auth-sub,.auth-support,.auth-support-title {color:#fff!important;}
        .auth-brand-symbol {background:#000!important;color:#fff!important;border:1px solid #fff;}
        .st-key-auth_display_controls button {background:#000!important;color:#fff!important;border:2px solid #fff!important;}
        .st-key-auth_display_controls button p {color:#fff!important;}
        .st-key-auth_panel [data-baseweb="input"],.st-key-auth_panel [data-baseweb="select"] > div {background:#000!important;border-color:#fff!important;color:#fff!important;}
        .st-key-auth_panel [data-baseweb="tab"],.st-key-auth_panel [aria-selected="true"] {color:#fff!important;}
        .auth-support a,.forgot-password-link {color:#83D6FF!important;}
        body:has(.auth-screen-marker) [role="dialog"],body:has(.auth-screen-marker) [role="dialog"] [data-testid="stForm"],
        body:has(.auth-screen-marker) [role="dialog"] [data-baseweb="input"] {background:#000!important;color:#fff!important;border-color:#fff!important;}
        body:has(.auth-screen-marker) [role="dialog"] p,body:has(.auth-screen-marker) [role="dialog"] h2,
        body:has(.auth-screen-marker) [role="dialog"] label,body:has(.auth-screen-marker) [role="dialog"] input {color:#fff!important;-webkit-text-fill-color:#fff!important;}
        body:has(.auth-screen-marker) [role="dialog"] button {background:#000!important;color:#fff!important;border:2px solid #fff!important;}
        """
    st.markdown(f'<style>{css}</style><span class="auth-screen-marker" aria-hidden="true"></span>', unsafe_allow_html=True)
    with st.container(key="auth_header"):
        _, controls = st.columns([7, 3], vertical_alignment="center")
        with controls:
            render_display_controls("auth")


def render_auth_intro() -> None:
    st.markdown(
        '<div class="auth-wrap"><div class="auth-brand"><div class="auth-brand-symbol">'
        f'{icon("scales",46)}{icon("medical",38)}</div><div><div class="auth-brand-name">DASHJUS</div>'
        '<div class="auth-brand-caption">Judicialização na Saúde</div></div></div>'
        '<h1 class="auth-title">Bem-vindo ao DASHJUS</h1>'
        '<p class="auth-sub">Entre para acompanhar seus pedidos ou acessar a área de gestão.</p></div>', unsafe_allow_html=True,
    )
