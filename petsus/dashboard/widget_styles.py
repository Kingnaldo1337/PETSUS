"""Cores de controles nativos compartilhadas pelo login e pelos dois perfis."""
from __future__ import annotations


def widget_styles(contrast: bool = False) -> str:
    surface, ink, muted, border = ("#000000", "#FFFFFF", "#DCE8F2", "#FFFFFF") if contrast else ("#FFFFFF", "#173653", "#60758C", "#DCE5EF")
    return f"""
    .stApp,[role="dialog"] {{color-scheme:{'dark' if contrast else 'light'};}}
    .stApp [data-testid="stMain"] [data-testid="stWidgetLabel"] p,
    [role="dialog"] [data-testid="stWidgetLabel"] p {{color:{ink}!important;}}
    .stApp [data-testid="stMain"] [data-testid="stCaptionContainer"] p {{color:{muted}!important;}}
    .stApp [data-testid="stTextInputRootElement"],
    .stApp [data-testid="stDateInputField"],
    .stApp [data-testid="stTextInput"] [data-baseweb="input"],
    .stApp [data-testid="stDateInput"] [data-baseweb="input"],
    .stApp [data-testid="stTextArea"] textarea,
    .stApp [data-testid="stNumberInput"] [data-baseweb="input"],
    .stApp [data-baseweb="select"] > div,
    [role="dialog"] [data-testid="stTextInputRootElement"] {{background:{surface}!important;color:{ink}!important;border-color:{border}!important;border-radius:9px;}}
    .stApp input:not([type="checkbox"]):not([type="radio"]):not([type="range"]):not([type="file"]),
    .stApp textarea,
    [role="dialog"] input:not([type="checkbox"]):not([type="radio"]) {{background:{surface}!important;color:{ink}!important;-webkit-text-fill-color:{ink}!important;caret-color:{ink};}}
    .stApp input::placeholder,.stApp textarea::placeholder {{color:{muted}!important;-webkit-text-fill-color:{muted}!important;opacity:1;}}
    .stApp [data-testid="stTextInputRootElement"] button,
    .stApp [data-testid="stDateInputField"] button {{color:{ink}!important;background:transparent!important;}}
    .stApp [data-testid="stMain"] [data-baseweb="select"] span,
    .stApp [data-testid="stMain"] [data-baseweb="select"] input {{color:{ink}!important;-webkit-text-fill-color:{ink}!important;}}
    """
