from __future__ import annotations

from html import escape
from textwrap import wrap

import pandas as pd
import plotly.graph_objects as go

from .ui import br_float, br_int, br_money


# Paleta compartilhada com os cartões e a navegação do portal.
CHART_BLUE = "#287BB5"
CHART_TEAL = "#0D8A7A"
CHART_INK = "#163653"
CHART_MUTED = "#60788F"
CHART_GRID = "#E8EFF5"
CHART_FONT = "Inter, Source Sans Pro, Arial, sans-serif"
_LEGACY_COLORS = {"#125CC9": CHART_BLUE, "#239B56": CHART_TEAL}

# Os mesmos valores têm as mesmas cores em todas as páginas e ordenações.
SEMANTIC_COLORS = {
    "Norte": CHART_BLUE, "Nordeste": "#7865AD", "Sudeste": CHART_TEAL,
    "Sul": "#B5822B", "Centro-Oeste": "#348D9B",
    "Justiça Federal": CHART_BLUE, "Justiça Estadual": CHART_TEAL,
    "Federal": CHART_BLUE, "Estadual": CHART_TEAL,
    "Município": "#7865AD", "Estado": CHART_TEAL, "União": CHART_BLUE,
    "Compartilhada": "#B5822B", "Sim": CHART_TEAL, "Não": "#7B8C9E",
    "Procedente": CHART_TEAL, "Parcialmente procedente": "#B5822B",
    "Improcedente": "#BF5B56", "Em andamento": CHART_BLUE,
    "Acordo": "#7865AD", "Extinto": "#7B8C9E",
    "Feminino": "#7865AD", "Masculino": CHART_BLUE,
    "Não informado": "#7B8C9E",
}

# API pública mantida para consumidores anteriores à padronização visual.
CORES = {
    "justica_estadual": SEMANTIC_COLORS["Justiça Estadual"],
    "justica_federal": SEMANTIC_COLORS["Justiça Federal"],
    "deferido": SEMANTIC_COLORS["Procedente"],
    "indeferido": SEMANTIC_COLORS["Improcedente"],
    "pendente": SEMANTIC_COLORS["Parcialmente procedente"],
}


def semantic_color(label: object, default: str = "#125CC9") -> str:
    return SEMANTIC_COLORS.get(str(label), _LEGACY_COLORS.get(default, default))


def chart_layout(height: int = 310, showlegend: bool = False, legend: dict | None = None) -> dict:
    legend_style = dict(
        font=dict(size=12, color=CHART_MUTED), bgcolor="rgba(0,0,0,0)",
        borderwidth=0, itemsizing="constant", tracegroupgap=10,
    )
    legend_style.update(legend or {})
    axis_style = dict(
        tickfont=dict(size=12, color=CHART_MUTED), showline=False,
        zeroline=False, ticks="", automargin=True, gridcolor=CHART_GRID,
        gridwidth=1, title=None, fixedrange=True,
    )
    return dict(
        height=height, autosize=True, margin=dict(l=10, r=40, t=10, b=10),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=CHART_INK, family=CHART_FONT, size=12),
        colorway=[CHART_BLUE, CHART_TEAL, "#7865AD", "#B5822B", "#348D9B"],
        showlegend=showlegend, legend=legend_style, separators=",.",
        xaxis=dict(axis_style), yaxis=dict(axis_style),
        hoverlabel=dict(bgcolor=CHART_INK, bordercolor=CHART_INK,
                        font=dict(family=CHART_FONT, size=13, color="#FFFFFF"), align="left"),
        hovermode="closest", bargap=.34, dragmode=False,
    )


def empty_fig(msg: str = "Sem dados publicáveis para os filtros selecionados", height: int = 300) -> go.Figure:
    fig = go.Figure()
    fig.update_layout(**chart_layout(height=height), annotations=[dict(text=msg, x=.5, y=.5, showarrow=False, font=dict(size=14, color=CHART_MUTED))])
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    return fig


def _label(value: object) -> str:
    return "<br>".join(escape(part) for part in wrap(str(value), 28))


def barh(df: pd.DataFrame, label_col: str, value_col: str, text_col: str | None = None, height: int = 320, color: str | dict[str, str] = "#125CC9", separate_dominant: bool = False, preserve_order: bool = False) -> go.Figure:
    if df.empty:
        return empty_fig(height=height)
    data = df.iloc[::-1].copy() if preserve_order else df.sort_values(value_col, ascending=True).copy()
    dominant = None
    if separate_dominant and len(data) > 1 and data[value_col].iloc[-1] > 4 * max(data[value_col].iloc[-2], 1):
        dominant = data.iloc[-1]
        data = data.iloc[:-1]
    texts = data[text_col] if text_col else data[value_col].map(br_int)
    fig = go.Figure(go.Bar(
        x=data[value_col], y=data[label_col].astype(str), orientation="h",
        marker_color=[color.get(str(label), semantic_color(label)) if isinstance(color, dict) else semantic_color(label, color) for label in data[label_col]],
        text=texts, textposition="outside", cliponaxis=False,
        customdata=data[label_col].astype(str),
        hovertemplate="<b>%{customdata}</b><br>%{text}<extra></extra>",
    ))
    # Plotly 5.18 continua aceito pelo projeto; versões recentes arredondam as pontas.
    marker_style = dict(line=dict(width=0))
    if "cornerradius" in go.bar.Marker()._valid_props:
        marker_style["cornerradius"] = 5
    fig.update_traces(marker=marker_style)
    layout = chart_layout(height=height)
    # O eixo categórico divide a área igualmente entre as barras. Reserva
    # espaço também para os nomes quebrados em duas ou mais linhas.
    tick_labels = [_label(label) for label in data[label_col]]
    label_lines = max(label.count("<br>") + 1 for label in tick_labels)
    row_height = max(34, label_lines * 18 + 12)
    layout["margin"]["b"] = 42
    layout["margin"]["r"] = min(180, max(90, max(len(str(text)) for text in texts) * 7))
    if dominant is not None:
        amount = str(dominant[text_col]) if text_col else br_int(dominant[value_col])
        layout["margin"]["t"] = 90
        layout["annotations"] = [dict(
            text=f"<b>{_label(dominant[label_col])}: {escape(amount)}</b><br>Categoria líder destacada; barras abaixo comparam as demais.",
            x=0, y=1.06, xref="paper", yref="paper", xanchor="left", yanchor="bottom", showarrow=False, align="left", font=dict(size=12, color=CHART_INK),
        )]
    layout["height"] = max(height, len(data) * row_height + layout["margin"]["t"] + layout["margin"]["b"])
    layout["bargap"] = .4
    fig.update_layout(**layout)
    maximum = max(float(data[value_col].max()), 1)
    fig.update_xaxes(title=None, range=[0, maximum * 1.38], showgrid=True, gridcolor=CHART_GRID, zeroline=False, automargin=True, rangemode="tozero", nticks=5)
    fig.update_yaxes(title=None, showgrid=False, automargin=True, tickmode="array", tickvals=data[label_col].astype(str).tolist(), ticktext=tick_labels)
    fig.update_traces(textfont=dict(size=12, color=CHART_INK), insidetextanchor="middle")
    return fig


def distribution_bar(df: pd.DataFrame, label_col: str, value_col: str, height: int = 320, denominator: float | None = None, preserve_order: bool = False) -> go.Figure:
    """Comparação por barras, com quantidade e percentual do denominador declarado."""
    if df.empty or df[value_col].sum() == 0:
        return empty_fig(height=height)
    data = df.copy()
    total = float(data[value_col].sum()) if denominator is None else float(denominator)
    data["texto"] = data[value_col].map(lambda value: f"{br_int(value)} · {br_float(100 * value / total) if total else '0,0'}%")
    return barh(data, label_col, value_col, "texto", height=height, preserve_order=preserve_order)


def donut(df: pd.DataFrame, label_col: str, value_col: str, center: str, height: int = 320) -> go.Figure:
    """Compatibilidade com chamadas antigas; a distribuição agora usa barras."""
    fig = distribution_bar(df, label_col, value_col, height=height)
    fig.update_layout(legend=dict(orientation="h", x=.5, xanchor="center", y=-.08, yanchor="top"), margin_b=58)
    return fig


def monthly_line(df: pd.DataFrame, value_col: str, title_name: str, money: bool = False, height: int = 320) -> go.Figure:
    if df.empty:
        return empty_fig(height=height)
    grouped = df.groupby("ano_mes", dropna=False)
    data = grouped.agg(valor=(value_col, "sum")).reset_index().sort_values("ano_mes")
    if "paciente_id" in df:
        counts = grouped["paciente_id"].nunique()
        suppressed = counts[counts < 5].index.tolist()
        if len(suppressed) == 1 and len(counts[counts >= 5]):
            suppressed.append(counts[counts >= 5].idxmin())
        data.loc[data["ano_mes"].isin(suppressed), "valor"] = float("nan")
    if data["valor"].notna().sum() == 0:
        return empty_fig(height=height)
    data["label"] = pd.to_datetime(data["ano_mes"] + "-01").dt.strftime("%m/%Y")
    data["texto"] = data["valor"].map(lambda value: br_money(value) if money else br_int(value))
    if data["valor"].notna().sum() == 1:
        available = data.loc[data["valor"].notna()]
        fig = barh(available, "label", "valor", "texto", height=height)
        fig.update_layout(margin_t=50, annotations=[dict(
            text="Um único mês disponível; não há série suficiente para indicar tendência.",
            x=0, y=1.1, xref="paper", yref="paper", showarrow=False, xanchor="left", font=dict(size=12, color=CHART_MUTED),
        )])
        return fig
    hover_prefix = "R$ " if money else ""
    series_color = CHART_TEAL if money else CHART_BLUE
    series_fill = "rgba(13,138,122,.08)" if money else "rgba(40,123,181,.08)"
    fig = go.Figure(go.Scatter(
        x=data["label"], y=data["valor"], mode="lines+markers", connectgaps=False,
        text=data["texto"], name=title_name, fill="tozeroy", fillcolor=series_fill,
        hovertemplate=f"<b>%{{x}}</b><br>{title_name}: %{{text}}<extra></extra>",
        line=dict(color=series_color, width=3, shape="linear"),
        marker=dict(size=7, color=series_color, line=dict(color="#FFFFFF", width=2)),
    ))
    fig.update_layout(**chart_layout(height=height))
    fig.update_layout(hovermode="x unified", margin_t=18, margin_b=24)
    fig.update_yaxes(title=None, showgrid=True, gridcolor=CHART_GRID, zeroline=False, tickprefix=hover_prefix, rangemode="tozero", nticks=5)
    fig.update_xaxes(title=None, showgrid=False, type="category", tickmode="auto", nticks=6, tickangle=-30, automargin=True,
                     showspikes=True, spikemode="across", spikesnap="cursor", spikecolor="#B7CAD9", spikethickness=1, spikedash="dot")
    return fig


def top_group(df: pd.DataFrame, group_col: str, value_col: str, n: int = 10, op: str = "count") -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=[group_col, "valor"])
    grouped = df.groupby(group_col, dropna=False)
    if op in {"sum", "mean"}:
        result = grouped[value_col].agg(op).reset_index(name="valor")
    else:
        result = grouped.size().reset_index(name="valor")
    if "paciente_id" in df:
        counts = grouped["paciente_id"].nunique()
        safe = counts >= 5
        if (~safe).sum() == 1 and safe.any():
            safe.loc[counts[safe].idxmin()] = False
        result = result[result[group_col].isin(counts[safe].index)]
    return result.sort_values("valor", ascending=False).head(n)
