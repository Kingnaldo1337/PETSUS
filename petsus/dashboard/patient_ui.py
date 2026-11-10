"""Identidade visual e componentes compartilhados pelos perfis do portal."""
from __future__ import annotations

from html import escape

import pandas as pd
import streamlit as st

from petsus.dashboard.navigation import MATERIAL_ICONS, PAGE_ICONS, navigation_key
from petsus.dashboard.motion import MOTION_CSS, header_art


_ICONS = {
    "scales": '<path d="M12 3v17m-5 1h10M4 7h16M6 7l-4 7h8L6 7Zm12 0-4 7h8l-4-7Z"/><path d="M2 14a4 4 0 0 0 8 0m4 0a4 4 0 0 0 8 0"/>',
    "medical": '<path fill="currentColor" stroke="none" d="M9 2h6a1 1 0 0 1 1 1v5h5a1 1 0 0 1 1 1v6a1 1 0 0 1-1 1h-5v5a1 1 0 0 1-1 1H9a1 1 0 0 1-1-1v-5H3a1 1 0 0 1-1-1V9a1 1 0 0 1 1-1h5V3a1 1 0 0 1 1-1Z"/>',
    "lock": '<rect x="5" y="10" width="14" height="11" rx="3"/><path d="M8 10V7a4 4 0 0 1 8 0v3m-4 5v2"/>',
    "arrow": '<path d="M4 12h15m-6-6 6 6-6 6"/>',
    "calendar": '<rect x="3" y="5" width="18" height="16" rx="3"/><path d="M7 3v4m10-4v4M3 11h18m-13 4h1m6 0h1"/>',
    "clock": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    "document": '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6Z"/><path d="M14 2v6h6M8 12h8m-8 4h6"/>',
    "chat": '<path d="M21 11a8 8 0 0 1-8 8H8l-5 3 1-6a8 8 0 1 1 17-5Z"/><path d="M8 10h8m-8 4h5"/>',
    "person": '<circle cx="12" cy="7" r="4"/><path d="M4 21v-2a8 8 0 0 1 16 0v2"/>',
    "info": '<circle cx="12" cy="12" r="9"/><path d="M12 11v6m0-10v.1"/>',
    "check": '<path d="m5 12 4 4L19 6"/>',
    "alert": '<path d="m10 4-8 14a2 2 0 0 0 2 3h16a2 2 0 0 0 2-3L14 4a2 2 0 0 0-4 0Z"/><path d="M12 9v5m0 3v.1"/>',
    "download": '<path d="M12 3v12m-5-5 5 5 5-5M4 16v4a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-4"/>',
    "users": '<circle cx="9" cy="8" r="3"/><path d="M3 21v-3a6 6 0 0 1 12 0v3m1-16a3 3 0 0 1 0 6m3 10v-3a6 6 0 0 0-3-5"/>',
    "wallet": '<rect x="3" y="5" width="18" height="15" rx="3"/><path d="M3 8V5a2 2 0 0 1 2-2h12m4 8h-6v5h6m-3-2.5h.1"/>',
    "chart": '<path d="M4 3v17h17M8 15v-4m5 4V7m5 8v-6"/>',
    "location": '<path d="M20 10c0 6-8 12-8 12S4 16 4 10a8 8 0 0 1 16 0Z"/><circle cx="12" cy="10" r="3"/>',
}


def icon(name: str, size: int = 24) -> str:
    return (
        f'<svg class="patient-icon" width="{size}" height="{size}" viewBox="0 0 24 24" '
        'fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" '
        f'stroke-linejoin="round" aria-hidden="true" focusable="false">{_ICONS[name]}</svg>'
    )


def set_text_size(large: bool) -> None:
    st.session_state["a11y_large_text"] = large


def toggle_contrast() -> None:
    st.session_state["a11y_contrast"] = not st.session_state.get("a11y_contrast", False)


def render_display_controls(prefix: str = "patient") -> None:
    """Os mesmos controles de leitura no login e nos dois perfis."""
    with st.container(key=f"{prefix}_display_controls"):
        smaller, larger, contrast = st.columns([1, 1, 2])
        with smaller:
            st.button("A−", key=f"{prefix}_text_small", help="Usar tamanho de texto padrão", on_click=set_text_size, args=(False,))
        with larger:
            st.button("A+", key=f"{prefix}_text_large", help="Ampliar o tamanho do texto", on_click=set_text_size, args=(True,))
        with contrast:
            st.button("◐ Contraste", key=f"{prefix}_contrast", help="Ativar ou desativar alto contraste", on_click=toggle_contrast)


def open_patient_help(intent: str = "contact", process_id: str | None = None) -> None:
    st.session_state["dashboard_navigation"] = "Ajuda e contato"
    st.session_state["patient_support_intent"] = intent
    st.session_state["feedback_process"] = str(process_id) if process_id else ""


def open_patient_process(process_id: str) -> None:
    st.session_state["patient_process"] = str(process_id)
    st.session_state["dashboard_navigation"] = "Meu acompanhamento"


def render_portal_styles(is_manager: bool = False) -> None:
    css = MOTION_CSS + """
    .patient-portal-marker {display:none;}
    .stApp:has(.patient-portal-marker) {--patient-ink:#122C50;--patient-muted:#5D7088;--patient-border:#E0E8F2;--patient-teal:#087F8C;--portal-shadow:0 6px 24px #16375508;--portal-radius:18px;}
    .stApp:has(.patient-portal-marker) [data-testid="stMain"] {background:radial-gradient(ellipse at 90% 0%,#EAF4FA 0%,#F3F7FC 42%,#F6F8FC 100%);}
    .stApp:has(.patient-portal-marker) [data-testid="stMain"] .block-container {max-width:1240px!important;margin-inline:auto;padding:3.9rem 2rem 1.3rem;}
    .stApp:has(.patient-portal-marker) [data-testid="stMain"] [data-testid="stVerticalBlock"] {gap:.8rem;}
    .stApp:has(.patient-portal-marker) [data-testid="stSidebar"] {background:linear-gradient(165deg,#102F56 0%,#0C294C 65%,#0B2545 100%);border-right:1px solid #173F63;}
    .stApp:has(.patient-portal-marker) [data-testid="stSidebarUserContent"] {padding-top:.35rem;}
    .patient-brand {display:flex;align-items:center;gap:.8rem;padding:.5rem 0 1.2rem;border-bottom:1px solid #FFFFFF21;}
    .patient-brand-mark {position:relative;display:flex;align-items:center;gap:.08rem;color:#DCEBFB;}
    .patient-brand-mark .patient-icon:last-child {color:#2FB7BE;}
    .patient-brand-name {font-size:.95rem;font-weight:800;letter-spacing:.065em;color:#fff;}
    .patient-brand-sub {font-size:.72rem;line-height:1.4;color:#B8CBE0;}
    .patient-account {display:flex;gap:.65rem;align-items:center;margin:.65rem 0 .7rem;}
    .patient-avatar {display:flex;align-items:center;justify-content:center;width:36px;height:36px;flex-shrink:0;border-radius:50%;background:#FFFFFF12;border:1px solid #FFFFFF27;color:#DDEFFC;font-size:.78rem;font-weight:700;}
    .patient-account-name {font-size:.85rem;font-weight:650;color:#EDF5FF;overflow-wrap:anywhere;}
    .patient-account-caption {font-size:.72rem;color:#A9C1D8;}
    .patient-sidebar-label {font-size:.66rem;letter-spacing:.14em;font-weight:700;color:#9FBDD8;margin:.55rem 0 .35rem;}
    .patient-sidebar-note {font-size:.73rem;line-height:1.5;color:#A9C1D8;border-top:1px solid #FFFFFF1C;padding-top:1rem;margin-top:.7rem;}
    .stApp:has(.patient-portal-marker) [data-testid="stSidebar"] .st-key-logout_button {margin-top:1rem;}
    .stApp:has(.patient-portal-marker) [data-testid="stSidebar"] .st-key-logout_button button {background:transparent!important;border-color:#FFFFFF28!important;min-height:40px;font-weight:500;}
    .st-key-patient_header [data-testid="stHorizontalBlock"] {display:grid!important;grid-template-columns:minmax(0,1fr) auto;align-items:center;gap:1rem;}
    .st-key-patient_header [data-testid="stColumn"] {width:auto!important;min-width:0!important;flex:unset!important;}
    .patient-page-eyebrow {font-size:.68rem;letter-spacing:.14em;font-weight:750;color:#087F8C;text-transform:uppercase;margin:0 0 .5rem;}
    .patient-page-title {font-size:clamp(1.65rem,3vw,2.25rem)!important;letter-spacing:-.045em;line-height:1.13!important;font-weight:800!important;color:var(--patient-ink)!important;margin:0!important;padding:0!important;}
    .patient-page-subtitle {font-size:.88rem!important;color:var(--patient-muted)!important;line-height:1.5!important;margin:.4rem 0 0!important;}
    .st-key-patient_display_controls [data-testid="stHorizontalBlock"] {display:flex!important;flex-wrap:nowrap!important;gap:.4rem;}
    .st-key-patient_display_controls [data-testid="stColumn"] {flex:0 0 auto!important;min-width:0!important;width:auto!important;}
    .st-key-patient_display_controls button {min-height:37px;padding:.3rem .65rem;border:1px solid #DCE5F0;border-radius:8px;background:#FFFFFFB8;box-shadow:0 2px 5px #1A3E6410;}
    .st-key-patient_display_controls button p {font-size:.74rem!important;font-weight:650;white-space:nowrap;}
    .patient-privacy {display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:.5rem 1rem;background:#EDF5FB;border:1px solid #DCEAF5;border-radius:12px;padding:.75rem 1rem;margin:.35rem 0 .55rem;}
    .patient-privacy-message {display:flex;align-items:center;gap:.45rem;color:#205F8F;font-size:.76rem;font-weight:600;}
    .patient-privacy-meta {color:#4A6683;font-size:.69rem;line-height:1.5;}
    .patient-privacy-meta span {white-space:nowrap;}
    .patient-order-heading {display:flex;justify-content:space-between;gap:.8rem;align-items:center;margin-top:.25rem;}
    .patient-order-label {font-size:.72rem;font-weight:700;letter-spacing:.08em;color:#607B95;text-transform:uppercase;}
    .patient-demo-badge {font-size:.64rem;font-weight:650;color:#6A7F99;background:#E9EFF7;border:1px solid #DFE7F1;border-radius:6px;padding:.25rem .5rem;white-space:nowrap;}
    .st-key-patient_process [data-baseweb="select"] > div {min-height:48px;background:#fff;border:1px solid #DCE5EF;border-radius:10px;box-shadow:0 2px 5px #173B6110;}
    .patient-process-caption {font-size:.71rem;color:#6D829A;margin:.2rem 0 0;overflow-wrap:anywhere;}
    .patient-status-grid {display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:1rem;margin:.3rem 0 .1rem;}
    .patient-status-card {display:flex;flex-direction:column;padding:1.3rem 1.35rem 0;min-width:0;background:#fff;border:1px solid var(--patient-border);border-radius:var(--portal-radius);box-shadow:var(--portal-shadow);}
    .patient-status-card.justice {background:linear-gradient(115deg,#FFFCF5,#FFFDF8);border-color:#EEE5D3;}
    .patient-status-main {display:flex;gap:.85rem;align-items:flex-start;flex:1;}
    .patient-status-symbol {color:#DFA415;flex-shrink:0;padding-top:.1rem;}
    .patient-status-card.health .patient-status-symbol {color:var(--patient-teal);}
    .patient-status-copy {min-width:0;}
    .patient-status-title {font-size:1rem!important;font-weight:750!important;line-height:1.3!important;margin:0 0 .45rem!important;padding:0!important;color:var(--patient-ink)!important;}
    .patient-badge {display:inline-flex;align-items:center;gap:.3rem;border-radius:999px;padding:.28rem .55rem;font-size:.68rem;font-weight:650;line-height:1.25;max-width:100%;}
    .patient-badge.amber {background:#FFF0C2;color:#865B00;}
    .patient-badge.teal {background:#DFF4F2;color:#08716F;}
    .patient-badge.green {background:#E2F2E7;color:#23673E;}
    .patient-badge.gray {background:#EDF0F5;color:#566881;}
    .patient-badge.red {background:#FCE9E6;color:#A1392C;}
    .patient-status-description {font-size:.78rem!important;line-height:1.6!important;color:var(--patient-muted)!important;margin:.65rem 0 .85rem!important;}
    .patient-status-footer {border-top:1px solid #D7E0EB90;padding:.65rem 0;font-size:.67rem;line-height:1.5;color:#637B95;margin-top:.2rem;}
    .patient-status-footer strong {font-weight:650;color:#36556F;}
    .patient-next-card {background:linear-gradient(115deg,#E0F4FF 0%,#E8F6FF 55%,#E1F2FD 100%);border:1px solid #BBDFF2;box-shadow:0 4px 15px #1F739009;border-radius:14px;padding:1.2rem 1.3rem;margin:.2rem 0 .1rem;}
    .patient-next-main {display:flex;gap:1rem;align-items:flex-start;}
    .patient-next-symbol {display:flex;align-items:center;justify-content:center;width:42px;height:42px;flex-shrink:0;border-radius:50%;background:#088A99;color:#fff;box-shadow:0 3px 8px #007A8D21;}
    .patient-next-body {min-width:0;flex:1;}
    .patient-next-eyebrow {font-size:.74rem;font-weight:650;color:#226A91;margin-bottom:.3rem;}
    .patient-next-title {font-size:clamp(1.15rem,2.1vw,1.4rem)!important;line-height:1.35!important;font-weight:750!important;letter-spacing:-.025em;margin:0!important;padding:0!important;color:#12365A!important;overflow-wrap:anywhere;}
    .patient-next-details {display:grid;grid-template-columns:repeat(2,minmax(0,1fr));margin-top:1rem;gap:1rem;}
    .patient-next-detail {display:flex;gap:.6rem;align-items:flex-start;min-width:0;color:#4B93B4;}
    .patient-next-detail + .patient-next-detail {border-left:1px solid #B7D7EA;padding-left:1rem;}
    .patient-next-detail-label {font-size:.67rem;font-weight:700;color:#316B8B;margin-bottom:.2rem;}
    .patient-next-detail-value {font-size:.77rem;line-height:1.5;color:#365A77;overflow-wrap:anywhere;}
    .patient-next-guidance {display:flex;align-items:flex-start;gap:.5rem;border-top:1px solid #BBDCEE;padding-top:.75rem;margin-top:.9rem;color:#285F80;font-size:.75rem;line-height:1.65;}
    .patient-next-guidance > svg {flex-shrink:0;margin-top:.1rem;}
    .patient-next-card.overdue {border-color:#E6C994;}
    .st-key-patient_bottom [data-testid="stHorizontalBlock"] {display:grid!important;grid-template-columns:repeat(2,minmax(0,1fr));gap:1rem;}
    .st-key-patient_bottom [data-testid="stColumn"] {flex:unset!important;width:auto!important;min-width:0!important;}
    .st-key-patient_movement,.st-key-patient_help,[class*="st-key-patient_record_"],[class*="st-key-patient_document_"] {background:#fff;border:1px solid var(--patient-border);border-radius:var(--portal-radius);padding:1.2rem 1.3rem;box-shadow:var(--portal-shadow);height:100%;}
    .patient-panel-heading {display:flex;gap:.7rem;align-items:flex-start;}
    .patient-panel-icon {color:#3B84B3;flex-shrink:0;}
    .patient-panel-title {font-size:.9rem!important;font-weight:750!important;line-height:1.4!important;color:var(--patient-ink)!important;margin:0!important;padding:0!important;}
    .patient-panel-sub {color:var(--patient-muted)!important;font-size:.75rem!important;line-height:1.5!important;margin:.15rem 0 .4rem!important;}
    .patient-movement-date {font-size:.68rem;font-weight:600;color:#7890A5;margin:.15rem 0 .45rem;}
    .patient-movement-text {font-size:.76rem!important;line-height:1.6!important;color:#526A83!important;margin:.1rem 0 0!important;}
    .st-key-patient_help [data-testid="stHorizontalBlock"] {gap:.5rem;}
    .st-key-patient_help button {min-height:38px;border-radius:7px;padding:.3rem .65rem;border-color:#A8CCD3;}
    .st-key-patient_help button p {font-size:.73rem!important;font-weight:650;}
    .st-key-patient_contact_button button {background:#087F8C!important;border-color:#087F8C!important;color:#fff!important;}
    .st-key-patient_contact_button button p {color:#fff!important;}
    .st-key-patient_report_button button {color:#8A651E;background:#fffdf7;border-color:#E7DCC3;}
    .st-key-patient_actions [data-testid="stHorizontalBlock"] {display:flex!important;flex-wrap:wrap!important;align-items:center;justify-content:space-between;gap:.6rem;}
    .st-key-patient_actions [data-testid="stColumn"] {min-width:0!important;flex:0 1 auto!important;width:auto!important;}
    .st-key-patient_actions [data-testid="stDownloadButton"] button {min-height:39px;font-size:.76rem;border:1px solid #99BBD9;color:#245C8A;border-radius:8px;background:#FFFFFFC9;box-shadow:0 2px 5px #173B6108;}
    .st-key-patient_actions [data-testid="stDownloadButton"] button p {font-size:.76rem!important;font-weight:600;}
    .patient-record-label {font-size:.69rem;color:#7189A1;font-weight:600;margin-bottom:.4rem;}
    .patient-record-title {font-size:1.15rem!important;color:var(--patient-ink)!important;font-weight:750!important;line-height:1.4!important;margin:.2rem 0 .6rem!important;padding:0!important;}
    .patient-record-details {display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:1rem;padding-top:.75rem;border-top:1px solid #E7EDF4;margin-top:.85rem;color:#5B738C;font-size:.78rem;line-height:1.6;}
    .patient-record-details strong {display:block;font-size:.68rem;color:#7B8EA4;margin-bottom:.15rem;}
    .patient-empty {text-align:center;border:1px solid var(--patient-border);border-radius:16px;padding:2.5rem 1.5rem;background:#FFFFFFC9;color:#4B84A3;}
    .patient-empty h2 {font-size:1.3rem!important;color:var(--patient-ink)!important;}
    .patient-empty p {font-size:.88rem!important;color:var(--patient-muted)!important;}
    .patient-discreet-note {font-size:.69rem;color:#7B8EA3;line-height:1.6;}
    .patient-footer {display:flex;gap:.4rem;align-items:center;justify-content:center;font-size:.67rem;color:#7D90A6;margin:1.3rem 0 .3rem;text-align:center;}
    .patient-process-caption,.patient-movement-date,.patient-record-label,.patient-record-details strong,.patient-discreet-note,.patient-footer {color:#5D7088;}
    .patient-demo-badge {color:#53677F;font-size:.7rem;}
    .patient-badge {font-size:.73rem;}
    .patient-status-footer,.patient-movement-date {font-size:.72rem;}
    .stApp:has(.patient-portal-marker) [data-testid="stExpander"] details {background:#FFFFFF80;border:1px solid #DFE7F0;border-radius:11px;box-shadow:none;}
    .stApp:has(.patient-portal-marker) [data-testid="stExpander"] summary {font-size:.8rem;}
    .stApp:has(.patient-portal-marker) .patient-icon {display:inline-block;vertical-align:middle;flex-shrink:0;}
    @media(max-width:900px) {
        .stApp:has(.patient-portal-marker) [data-testid="stMain"] .block-container {padding-inline:1.1rem;}
        .st-key-patient_header [data-testid="stHorizontalBlock"] {grid-template-columns:1fr;gap:.8rem;}
        .st-key-patient_display_controls [data-testid="stHorizontalBlock"] {display:flex!important;}
    }
    @container dashboard (max-width:600px) {
        .patient-status-grid {grid-template-columns:1fr;gap:.75rem;}
        .st-key-patient_bottom [data-testid="stHorizontalBlock"] {grid-template-columns:1fr;gap:.75rem;}
        .st-key-patient_help [data-testid="stHorizontalBlock"] {grid-template-columns:repeat(2,minmax(0,1fr));}
        .patient-next-details {grid-template-columns:1fr;gap:.7rem;}
        .patient-next-detail + .patient-next-detail {border-left:0;padding-left:0;}
        .patient-next-card {padding:1rem;}
        .patient-next-main {gap:.7rem;}
        .patient-next-symbol {width:34px;height:34px;}
        .patient-record-details {grid-template-columns:1fr;gap:.6rem;}
    }
    @media(max-width:540px) {
        .stApp:has(.patient-portal-marker) [data-testid="stMain"] .block-container {padding-inline:.8rem;}
        .patient-status-grid {grid-template-columns:1fr;}
        .st-key-patient_bottom [data-testid="stHorizontalBlock"] {grid-template-columns:1fr;}
        .st-key-patient_help [data-testid="stHorizontalBlock"] {grid-template-columns:repeat(2,minmax(0,1fr));}
        .patient-privacy-meta span {white-space:normal;}
    }
    """
    if st.session_state.get("a11y_contrast", False):
        css += """
        .stApp:has(.patient-portal-marker) {--patient-ink:#fff;--patient-muted:#E2EAF2;--patient-border:#fff;--patient-teal:#8DE5EF;}
        .stApp:has(.patient-portal-marker) [data-testid="stMain"],
        .patient-status-card,.patient-status-card.justice,.patient-next-card,.patient-privacy,.patient-empty,
        .st-key-patient_movement,.st-key-patient_help,[class*="st-key-patient_record_"],[class*="st-key-patient_document_"] {background:#000!important;color:#fff!important;border-color:#fff!important;box-shadow:none!important;}
        .patient-privacy-message,.patient-privacy-meta,.patient-next-eyebrow,.patient-next-title,.patient-next-detail-label,.patient-next-detail-value,.patient-next-guidance,
        .patient-status-description,.patient-status-footer,.patient-status-footer strong,.patient-panel-sub,.patient-movement-date,.patient-movement-text,
        .patient-order-label,.patient-process-caption,.patient-record-label,.patient-record-details,.patient-record-details strong,.patient-page-eyebrow,.patient-discreet-note,.patient-footer {color:#E5F4FF!important;}
        .patient-badge,.patient-demo-badge {background:#000!important;color:#fff!important;border:1px solid #fff!important;}
        .patient-status-symbol,.patient-status-card.health .patient-status-symbol,.patient-panel-icon {color:#8DE5EF!important;}
        .patient-next-symbol {background:#fff!important;color:#000!important;}
        .st-key-patient_display_controls button,.st-key-patient_help button,.st-key-patient_actions button {background:#000!important;color:#fff!important;border:2px solid #fff!important;}
        .st-key-patient_display_controls button p,.st-key-patient_help button p,.st-key-patient_actions button p {color:#fff!important;}
        .st-key-patient_process [data-baseweb="select"] > div {background:#000!important;border:2px solid #fff!important;color:#fff!important;}
        .st-key-patient_process [data-baseweb="select"] span,.st-key-patient_process [data-baseweb="select"] input {color:#fff!important;-webkit-text-fill-color:#fff!important;}
        """
    if is_manager:
        css += _manager_styles()
    marker = "patient-portal-marker manager-portal-marker" if is_manager else "patient-portal-marker"
    st.markdown(f'<style>{css}</style><span class="{marker}" aria-hidden="true"></span>', unsafe_allow_html=True)


def render_portal_sidebar(user) -> None:
    st.markdown(
        '<div class="patient-brand"><div class="patient-brand-mark">'
        f'{icon("scales", 29)}{icon("medical", 25)}</div><div><div class="patient-brand-name">DASHJUS</div>'
        '<div class="patient-brand-sub">Judicialização na Saúde</div></div></div>',
        unsafe_allow_html=True,
    )
    parts = str(user.name).split()
    initials = "".join(word[0] for word in (parts[:1] + parts[-1:] if len(parts) > 1 else parts)).upper()
    st.markdown(
        f'<div class="patient-account"><div class="patient-avatar">{escape(initials)}</div>'
        f'<div><div class="patient-account-name">{escape(str(user.name))}</div>'
        '</div></div>'
        f'<div class="patient-sidebar-label">{"ÁREA DO GESTOR" if user.is_manager else "ÁREA DO PACIENTE"}</div>', unsafe_allow_html=True,
    )


def render_portal_navigation(page_labels: list[str]) -> str:
    """Navegação com botões e ícones nativos, sem máscaras CSS ou radios ocultos."""
    if st.session_state.get("dashboard_navigation") not in page_labels:
        st.session_state["dashboard_navigation"] = page_labels[0]
    scope = '.stApp [data-testid="stSidebar"] .st-key-portal_navigation'
    css = f"""
    {scope} [data-testid="stVerticalBlock"] {{gap:.25rem;}}
    {scope} [data-testid="stElementContainer"],{scope} [data-testid="stButton"] {{width:100%!important;align-self:stretch;}}
    {scope} button {{display:flex;justify-content:flex-start;gap:.7rem;min-height:42px;width:100%;text-align:left;border:1px solid transparent!important;border-radius:9px;background:transparent!important;color:#D6E8F8!important;padding:.6rem .7rem;box-shadow:none;font-family:inherit;}}
    {scope} button p {{font-size:.82rem;font-weight:550;color:inherit!important;text-align:left;}}
    {scope} button [data-testid="stMarkdownContainer"] {{text-align:left;}}
    {scope} button > div {{width:100%;}}
    {scope} button [data-has-shortcut] {{display:grid!important;grid-template-columns:22px minmax(0,1fr);align-items:center;justify-content:start;column-gap:.7rem;width:100%;}}
    {scope} button [data-has-shortcut] > :first-child {{width:22px;min-width:22px;justify-self:center;}}
    {scope} button:hover {{background:#FFFFFF0D!important;border-color:#FFFFFF1A!important;}}
    {scope} button[kind="primary"] {{background:linear-gradient(90deg,#208EA42E,#2586AE18)!important;border-color:#57BBD140!important;box-shadow:inset 3px 0 #39BBD2;color:#ECFAFF!important;}}
    {scope} button[kind="primary"] p {{font-weight:750;}}
    {scope} button:focus-visible {{outline:2px solid #72DFEB;outline-offset:2px;}}
    """
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
    with st.container(key="portal_navigation"):
        for label in page_labels:
            symbol = MATERIAL_ICONS[PAGE_ICONS.get(label, "document")]
            st.button(label, icon=f":material/{symbol}:", key=navigation_key(label),
                type="primary" if st.session_state["dashboard_navigation"] == label else "secondary",
                use_container_width=True, wrap=False, on_click=_select_portal_page, args=(label,))
    return st.session_state["dashboard_navigation"]


def _select_portal_page(page: str) -> None:
    st.session_state["dashboard_navigation"] = page


def render_portal_header(page: str, subtitle: str, metadata: dict, reference_date, is_manager: bool = False) -> None:
    with st.container(key="patient_header"):
        heading, controls = st.columns([7, 3], vertical_alignment="center")
        with heading:
            st.markdown(
                '<div class="portal-heading-row"><div class="portal-heading-copy">'
                f'<div class="patient-page-eyebrow">{"Saúde pública · Gestão" if is_manager else "Seu espaço de cuidado"}</div>'
                f'<h1 class="patient-page-title">{escape(page)}</h1>'
                f'<p class="patient-page-subtitle">{escape(subtitle)}</p></div>'
                f'{header_art(contrast=st.session_state.get("a11y_contrast", False))}</div>', unsafe_allow_html=True,
            )
        with controls:
            render_display_controls()
    reference = pd.Timestamp(reference_date).strftime("%d/%m/%Y")
    st.session_state["metrics_reference"] = reference
    modified = metadata["modified"].strftime("%d/%m/%Y às %H:%M")
    message = "Ambiente de gestão · Acesso restrito" if is_manager else "Você visualiza apenas os seus dados."
    reference_label = "Referência dos cálculos" if is_manager else "Referência dos prazos"
    st.markdown(
        '<div class="patient-privacy"><div class="patient-privacy-message">'
        f'{icon("lock",16)}<span>{message}</span></div>'
        f'<div class="patient-privacy-meta"><span>Arquivo atualizado: {modified}</span> · <span>{reference_label}: {reference}</span></div></div>',
        unsafe_allow_html=True,
    )


def _manager_styles() -> str:
    css = """
    .manager-portal-marker {display:none;}
    .stApp:has(.manager-portal-marker) [data-testid="stMain"] .block-container {max-width:1540px!important;}
    .stApp:has(.manager-portal-marker) [data-testid="stSidebar"] [data-testid="stWidgetLabel"] p {font-size:.75rem;line-height:1.5;}
    .stApp:has(.manager-portal-marker) [data-testid="stSidebar"] [data-testid="stExpander"] details {background:#FFFFFF07;border:1px solid #FFFFFF26;border-radius:9px;box-shadow:none;}
    .stApp:has(.manager-portal-marker) [data-testid="stSidebar"] [data-testid="stExpander"] summary {background:#FFFFFF07!important;border-radius:8px!important;padding:.6rem .65rem;}
    .stApp:has(.manager-portal-marker) [data-testid="stSidebar"] [data-testid="stExpander"] summary p {font-size:.74rem;font-weight:600;}
    .stApp:has(.manager-portal-marker) [data-testid="stSidebar"] .st-key-clear_filters_button button {min-height:36px;background:#FFFFFF09!important;border-color:#FFFFFF35!important;border-radius:8px;}
    .stApp:has(.manager-portal-marker) [data-testid="stSidebar"] .st-key-clear_filters_button button p {font-size:.76rem;}
    .manager-filter-caption {color:#A9C1D8;font-size:.72rem;line-height:1.6;margin:.1rem 0 .6rem;}
    .stApp:has(.manager-portal-marker) [data-testid="stHorizontalBlock"]:has(> [data-testid="stColumn"] .metric-card) {display:grid!important;grid-template-columns:repeat(auto-fit,minmax(min(100%,175px),1fr));gap:1rem;}
    .stApp:has(.manager-portal-marker) [data-testid="stHorizontalBlock"]:has(> [data-testid="stColumn"] .metric-card) > [data-testid="stColumn"] {width:auto!important;min-width:0!important;flex:unset!important;}
    .stApp:has(.manager-portal-marker) .metric-card {background:linear-gradient(145deg,#FFFFFF 65%,#F7FAFD);border:1px solid var(--patient-border);border-top:3px solid #D1E4F4;border-radius:var(--portal-radius);padding:1.15rem 1.2rem;min-height:178px;height:100%!important;box-shadow:var(--portal-shadow);transition:border-color .18s ease,box-shadow .18s ease;}
    .stApp:has(.manager-portal-marker) .metric-card:has(.icon-green) {border-top-color:#8BD0C7;}
    .stApp:has(.manager-portal-marker) .metric-card:has(.icon-orange) {border-top-color:#E8C886;}
    .stApp:has(.manager-portal-marker) .metric-card:has(.icon-purple) {border-top-color:#BDAEE8;}
    .stApp:has(.manager-portal-marker) .metric-card:hover {border-color:#AFCDD9;box-shadow:0 9px 28px #1637550E;}
    .stApp:has(.manager-portal-marker) .metric-head {gap:.6rem;align-items:flex-start;margin-bottom:.9rem;}
    .stApp:has(.manager-portal-marker) .metric-icon {width:38px;height:38px;min-width:38px;border-radius:12px;font-size:1.05rem;box-shadow:none;}
    .stApp:has(.manager-portal-marker) .icon-blue {background:#E6F0FB;color:#2D6B9F;}
    .stApp:has(.manager-portal-marker) .icon-green {background:#E2F3EF;color:#087F79;}
    .stApp:has(.manager-portal-marker) .icon-orange {background:#FFF1D8;color:#A27312;}
    .stApp:has(.manager-portal-marker) .icon-purple {background:#EDEAF8;color:#7057A3;}
    .stApp:has(.manager-portal-marker) .metric-label {font-size:.77rem;font-weight:700;color:#506985;line-height:1.45;padding-top:.05rem;}
    .stApp:has(.manager-portal-marker) .metric-value {font-size:clamp(1.5rem,2.15vw,2.05rem);font-weight:800;font-variant-numeric:tabular-nums;letter-spacing:-.045em;color:#122C50;line-height:1.2;margin-bottom:.45rem;}
    .stApp:has(.manager-portal-marker) .metric-value-long {font-size:1.35rem!important;letter-spacing:-.025em;}
    .stApp:has(.manager-portal-marker) .metric-sub {font-size:.74rem;line-height:1.55;color:#5D7088;}
    .stApp:has(.manager-portal-marker) .card-help {border-color:#9AB6CA;color:#487491!important;min-width:18px;width:18px;height:18px;font-size:.65rem;background:transparent;}
    .stApp:has(.manager-portal-marker) [class*="st-key-manager_panel_"] {background:#fff;border:1px solid var(--patient-border);border-radius:var(--portal-radius);padding:1.3rem 1.35rem;box-shadow:var(--portal-shadow);}
    .stApp:has(.manager-portal-marker) .section-title {display:flex;align-items:center;gap:.65rem;font-size:.95rem!important;line-height:1.45!important;font-weight:750;letter-spacing:-.02em;color:#163653;margin:0 0 1rem!important;padding:0!important;}
    .stApp:has(.manager-portal-marker) .section-symbol {display:flex;align-items:center;justify-content:center;flex:0 0 32px;width:32px;height:32px;border-radius:10px;background:#EDF6F8;color:#087F8C;}
    .stApp:has(.manager-portal-marker) [data-testid="stPlotlyChart"] {border-radius:12px;}
    .stApp:has(.manager-portal-marker) .insight-card {border:1px solid #DFE7F0;border-radius:13px;box-shadow:0 3px 12px #16375505;padding:1.05rem;}
    .stApp:has(.manager-portal-marker) .insight-title {font-size:.79rem;font-weight:650;}
    .stApp:has(.manager-portal-marker) .insight-value {font-size:1.25rem;font-weight:750;color:#122C50;}
    .stApp:has(.manager-portal-marker) .insight-desc {font-size:.77rem;line-height:1.55;color:#5D7088;}
    .stApp:has(.manager-portal-marker) [data-testid="stDataFrame"] {border:1px solid #E1E8F0;border-radius:12px;overflow:hidden;}
    .stApp:has(.manager-portal-marker) [data-testid="stMain"] [data-baseweb="input"],
    .stApp:has(.manager-portal-marker) [data-testid="stMain"] [data-baseweb="select"] > div {background:#fff;border-color:#DCE5EF;border-radius:9px;}
    .stApp:has(.manager-portal-marker) [data-testid="stMain"] [data-testid="stForm"] {border-color:#DFE7F0;border-radius:13px;background:#FFFFFFA8;}
    .stApp:has(.manager-portal-marker) [data-testid="stMain"] button {border-radius:8px;font-size:.8rem;}
    .stApp:has(.manager-portal-marker) [data-testid="stMain"] button[kind="primary"] {background:#087F8C;border-color:#087F8C;color:#fff;}
    .stApp:has(.manager-portal-marker) [data-testid="stMain"] [data-testid="stDownloadButton"] button {border:1px solid #99BBD9;background:#FFFFFFC9;color:#245C8A;}
    .st-key-manager_filterbar {background:#FFFFFFE8;border:1px solid var(--patient-border);border-radius:var(--portal-radius);padding:.85rem 1.1rem;box-shadow:var(--portal-shadow);}
    .st-key-manager_filterbar [data-testid="stHorizontalBlock"] {display:grid!important;grid-template-columns:minmax(0,1fr) auto;align-items:center;gap:1rem;}
    .st-key-manager_filterbar [data-testid="stColumn"] {width:auto!important;min-width:0!important;flex:unset!important;}
    .st-key-manager_filterbar .filter-pill {background:#EAF3FA;color:#2C648A;border:1px solid #D7E6F1;box-shadow:none;border-radius:8px;font-size:.8rem;padding:.65rem .85rem;}
    .stApp:has(.manager-portal-marker) .flow-step {border-radius:10px;box-shadow:none;}
    .stApp:has(.manager-portal-marker) .flow-title {font-size:.95rem;}
    .stApp:has(.manager-portal-marker) [data-testid="stCaptionContainer"] {color:#5D7088;font-size:.75rem;line-height:1.6;}
    @container dashboard (max-width:540px) {
        .st-key-manager_filterbar [data-testid="stHorizontalBlock"] {grid-template-columns:1fr;gap:.5rem;}
        .stApp:has(.manager-portal-marker) [class*="st-key-manager_panel_"] {padding:.85rem;}
    }
    """
    if st.session_state.get("a11y_contrast", False):
        css += """
        .stApp:has(.manager-portal-marker) .metric-card,.stApp:has(.manager-portal-marker) .insight-card,
        .stApp:has(.manager-portal-marker) [class*="st-key-manager_panel_"],.st-key-manager_filterbar {background:#000!important;border-color:#fff!important;box-shadow:none!important;}
        .stApp:has(.manager-portal-marker) .metric-label,.stApp:has(.manager-portal-marker) .metric-value,
        .stApp:has(.manager-portal-marker) .metric-sub,.stApp:has(.manager-portal-marker) .section-title,
        .stApp:has(.manager-portal-marker) .insight-value,.stApp:has(.manager-portal-marker) .insight-desc {color:#fff!important;}
        .stApp:has(.manager-portal-marker) .metric-icon,.st-key-manager_filterbar .filter-pill {background:#000!important;border:1px solid #fff!important;color:#fff!important;}
        .stApp:has(.manager-portal-marker) .section-symbol {background:#000!important;color:#fff!important;border:1px solid #fff;}
        .stApp:has(.manager-portal-marker) .card-help {border-color:#fff!important;color:#fff!important;}
        .stApp:has(.manager-portal-marker) [data-testid="stMain"] [data-baseweb="select"] > div,
        .stApp:has(.manager-portal-marker) [data-testid="stMain"] [data-baseweb="input"] {background:#000!important;color:#fff!important;border-color:#fff!important;}
        .stApp:has(.manager-portal-marker) [data-testid="stMain"] [data-baseweb="select"] span {color:#fff!important;}
        """
    return css


# Compatibilidade com as chamadas do portal do paciente.
render_patient_styles = render_portal_styles
render_patient_sidebar = render_portal_sidebar
render_patient_header = render_portal_header
