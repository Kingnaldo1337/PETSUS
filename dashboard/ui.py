from html import escape
from io import BytesIO

import pandas as pd
import streamlit as st


def br_int(value: float | int) -> str:
    if pd.isna(value):
        return "0"
    return f"{int(round(float(value))):,}".replace(",", ".")


def br_float(value: float | int, casas: int = 1) -> str:
    if pd.isna(value):
        value = 0
    return f"{float(value):,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def br_money(value: float | int, compact: bool = True) -> str:
    value = 0 if pd.isna(value) else float(value)
    if compact and abs(value) >= 1_000_000:
        return f"R$ {br_float(value / 1_000_000, 1)} Mi"
    if compact and abs(value) >= 1_000:
        return f"R$ {br_float(value / 1_000, 1)} Mil"
    return f"R$ {br_float(value, 2)}"


def pct(part: float, total: float) -> float:
    return 0.0 if total in [0, None] or pd.isna(total) else (float(part) / float(total)) * 100


def fmt_periodo(df: pd.DataFrame) -> str:
    if df.empty:
        return "Sem dados"
    inicio = df["data_ajuizamento"].min().strftime("%d/%m/%Y")
    fim = df["data_ajuizamento"].max().strftime("%d/%m/%Y")
    return f"{inicio} a {fim}"


def section_title(title: str) -> None:
    st.markdown(f'<div class="section-title">{escape(str(title))}</div>', unsafe_allow_html=True)


def metric_card(label: str, value: str, subtitle: str, icon: str, icon_cls: str = "icon-blue") -> None:
    value_text = str(value)
    longest_word = max((len(word) for word in value_text.split()), default=0)
    value_size_cls = " metric-value-long" if longest_word >= 9 else ""
    card_size_cls = " metric-card-long" if longest_word >= 9 else ""
    st.markdown(
        f"""
        <div class="metric-card{card_size_cls}"><div class="metric-wrap">
            <div class="metric-head">
                <div class="metric-icon {escape(str(icon_cls), quote=True)}">{escape(str(icon))}</div>
                <div class="metric-label">{escape(str(label))}</div>
            </div>
            <div class="metric-value{value_size_cls}">{escape(value_text)}</div>
            <div class="metric-sub">{escape(str(subtitle))}</div>
        </div></div>
        """,
        unsafe_allow_html=True,
    )


def insight_card(title: str, value: str, desc: str) -> None:
    st.markdown(
        f"""<div class="insight-card">
            <div class="insight-title">{escape(str(title))}</div>
            <div class="insight-value">{escape(str(value))}</div>
            <div class="insight-desc">{escape(str(desc))}</div>
        </div>""",
        unsafe_allow_html=True,
    )


def to_excel_bytes(df: pd.DataFrame) -> bytes:
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="dados_filtrados", index=False)
    return output.getvalue()


def multiselect_sidebar(label: str, df: pd.DataFrame, column: str) -> list[str]:
    options = sorted([value for value in df[column].dropna().astype(str).unique().tolist() if value.strip()])
    return st.multiselect(label, options, placeholder="Todos")
