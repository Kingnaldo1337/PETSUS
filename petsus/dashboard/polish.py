"""Acabamento compartilhado do DASHJUS, independente do tema dos widgets."""
from __future__ import annotations


def polish_styles(contrast: bool = False) -> str:
    # O alto contraste mantém suas superfícies sólidas e bordas bem definidas.
    if contrast:
        return ""
    return """
    @keyframes dashjus-ambient {
        from {background-position:15% 0%;}
        to {background-position:85% 100%;}
    }
    @keyframes dashjus-orbit {
        from {transform:rotate(-35deg);opacity:0;}
        to {transform:rotate(0);opacity:1;}
    }
    @keyframes dashjus-panel-in {
        from {opacity:0;transform:translateY(6px);}
        to {opacity:1;transform:translateY(0);}
    }
    .stApp:has(.patient-portal-marker) {--portal-shadow:0 8px 28px #15355309;--portal-radius:20px;}
    .st-key-patient_header {
        position:relative;background:linear-gradient(115deg,#FFFFFF 48%,#EFF9FA);
        border:1px solid #DCE8F1;border-radius:22px;padding:1.3rem 1.5rem;
        box-shadow:0 8px 28px #15355306;isolation:isolate;
    }
    .patient-page-eyebrow {display:flex;align-items:center;gap:.5rem;}
    .patient-page-eyebrow::before {content:"";width:6px;height:6px;flex:0 0 6px;border-radius:50%;background:#0B919A;box-shadow:0 0 0 4px #0B919A12;}
    .patient-privacy {background:#EAF3F9;border-color:#DCE8F1;margin:.5rem 0 .8rem;}
    .patient-brand-mark {background:linear-gradient(135deg,#FFFFFF14,#FFFFFF04);border:1px solid #FFFFFF1B;border-radius:14px;padding:.65rem;}
    .patient-brand {gap:.7rem;padding-bottom:1.3rem;}
    .patient-avatar {border-radius:12px;background:linear-gradient(135deg,#2C6C8E55,#169CA02A);}
    .st-key-portal_navigation button {transition:background .18s ease,border-color .18s ease,box-shadow .18s ease;}
    .st-key-portal_navigation button[kind="primary"] {box-shadow:inset 3px 0 #65D8E3,0 4px 14px #03192C18!important;}
    .stApp:has(.manager-portal-marker) .metric-card {
        background:linear-gradient(135deg,#FFFFFF 58%,#F5F9FD);border-top-width:2px;
        padding:1.25rem;transition:box-shadow .22s ease,border-color .22s ease,transform .22s ease;
    }
    .stApp:has(.manager-portal-marker) .metric-head {margin-bottom:1.1rem;}
    .stApp:has(.manager-portal-marker) .metric-icon {border:1px solid #17365308;box-shadow:0 3px 9px #17365305;}
    .stApp:has(.manager-portal-marker) .metric-value {letter-spacing:-.045em;margin-bottom:.55rem;}
    .stApp:has(.manager-portal-marker) .metric-sub {line-height:1.65;}
    .stApp:has(.manager-portal-marker) [class*="st-key-manager_panel_"] {border-color:#E0E8F1;}
    .stApp:has(.manager-portal-marker) .section-symbol {background:linear-gradient(135deg,#E3F3F4,#EFF6FC);border:1px solid #DDEEF1;border-radius:11px;}
    .stApp:has(.manager-portal-marker) [data-testid="stExpander"] details {background:#FFFFFF;border-color:#E0E8F1;border-radius:14px;}
    .stApp:has(.patient-portal-marker) [data-testid="stMain"] button[kind="primary"] {
        background:linear-gradient(110deg,#087F8C,#087780);border-color:#087F8C;
        box-shadow:0 4px 10px #087F8C19;transition:box-shadow .18s ease,filter .18s ease;
    }
    .stApp:has(.patient-portal-marker) [data-testid="stMain"] button[kind="primary"]:hover {filter:brightness(1.05);box-shadow:0 6px 16px #087F8C24;}
    .patient-status-card {transition:box-shadow .22s ease,border-color .22s ease;}
    .patient-next-card {background:linear-gradient(115deg,#123C59,#0C626A);border-color:#297A86;box-shadow:0 10px 30px #0C626A16;}
    .patient-next-title {color:#FFFFFF!important;}
    .patient-next-eyebrow,.patient-next-detail-label {color:#B9E8EC!important;}
    .patient-next-detail-value,.patient-next-guidance {color:#EBF7FA!important;}
    .patient-next-detail {color:#94DFE6;}
    .patient-next-detail + .patient-next-detail,.patient-next-guidance {border-color:#FFFFFF26;}
    .patient-next-symbol {background:#FFFFFF15;color:#C1F3F7;border:1px solid #FFFFFF2C;box-shadow:none;}
    .patient-next-card.overdue {border-color:#D7AF65;}
    .stApp:has(.auth-screen-marker) [data-testid="stMain"] {
        background:radial-gradient(ellipse at 15% 10%,#DBEBF8 0%,transparent 48%),radial-gradient(ellipse at 85% 70%,#DDF1EF 0%,transparent 45%),#F5F8FC;
        background-size:125% 125%;animation:dashjus-ambient 4s ease-out both;
    }
    .auth-wrap .auth-brand-symbol {position:relative;background:linear-gradient(135deg,#173F65,#0E2D4B);border:1px solid #2C5575;border-radius:23px;}
    .auth-wrap .auth-brand-symbol::after {content:"";position:absolute;inset:-9px;border:1px dashed #087F8C42;border-radius:30px;pointer-events:none;animation:dashjus-orbit 1.6s ease-out both;}
    .auth-title {letter-spacing:-.045em;}
    .st-key-auth_panel {border-color:#DAE5EF;border-radius:23px;padding:1.5rem 1.65rem;box-shadow:0 18px 50px #1637550D,0 2px 8px #16375504;animation:dashjus-panel-in .5s ease-out both;}
    .st-key-auth_panel button[kind="primaryFormSubmit"],.st-key-auth_panel button[kind="primary"] {background:linear-gradient(110deg,#087F8C,#087780);box-shadow:0 5px 14px #087F8C1F;transition:box-shadow .18s ease,filter .18s ease;}
    .st-key-auth_panel button[kind="primaryFormSubmit"]:hover {filter:brightness(1.06);box-shadow:0 7px 18px #087F8C2B;}
    @media(hover:hover) and (pointer:fine) {
        .stApp:has(.manager-portal-marker) .metric-card:hover {transform:translateY(-2px);border-color:#B8D8E2;box-shadow:0 12px 28px #15355313;}
        .patient-status-card:hover {border-color:#B7D7DE;box-shadow:0 10px 26px #1535530C;}
    }
    @container dashboard (max-width:640px) {
        .st-key-patient_header {padding:1rem;border-radius:16px;}
        .stApp:has(.manager-portal-marker) .metric-card {padding:1rem;}
    }
    @media(max-width:540px) {
        .st-key-auth_panel {padding:1.15rem;border-radius:18px;}
        .auth-wrap .auth-brand-symbol::after {inset:-6px;}
    }
    @media(prefers-reduced-motion:reduce) {
        .stApp:has(.auth-screen-marker) [data-testid="stMain"],.st-key-auth_panel,.auth-wrap .auth-brand-symbol::after {animation:none!important;}
        .stApp:has(.manager-portal-marker) .metric-card:hover {transform:none;}
    }
    """
