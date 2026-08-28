import pandas as pd
import plotly.graph_objects as go

from .ui import br_int, br_money


def chart_layout(height: int = 310, showlegend: bool = False, legend: dict | None = None) -> dict:
    return dict(
        height=height,
        autosize=True,
        margin=dict(l=10, r=20, t=10, b=10),
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(color="#0B2459", family="Inter"),
        showlegend=showlegend,
        legend=legend or dict(),
    )


def empty_fig(msg: str = "Sem dados para os filtros selecionados", height: int = 300) -> go.Figure:
    fig = go.Figure()
    fig.update_layout(**chart_layout(height=height), annotations=[dict(text=msg, x=0.5, y=0.5, showarrow=False, font=dict(size=16, color="#667085"))])
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    return fig


def barh(df: pd.DataFrame, label_col: str, value_col: str, text_col: str | None = None, height: int = 320, color: str = "#125CC9") -> go.Figure:
    if df.empty:
        return empty_fig(height=height)
    data = df.sort_values(value_col, ascending=True).copy()
    fig = go.Figure(go.Bar(x=data[value_col], y=data[label_col], orientation="h", marker_color=color, text=data[text_col] if text_col else data[value_col], textposition="outside", cliponaxis=False))
    fig.update_layout(**chart_layout(height=height))
    fig.update_xaxes(showgrid=True, gridcolor="#E8EDF5", zeroline=False, automargin=True)
    fig.update_yaxes(showgrid=False, automargin=True)
    fig.update_traces(textfont=dict(size=11), insidetextanchor="middle")
    return fig


def donut(df: pd.DataFrame, label_col: str, value_col: str, center: str, height: int = 320) -> go.Figure:
    if df.empty or df[value_col].sum() == 0:
        return empty_fig(height=height)
    fig = go.Figure(go.Pie(labels=df[label_col], values=df[value_col], hole=.60, textinfo="percent", sort=False, marker_colors=["#125CC9", "#39A74A", "#2EA8C5", "#EAB308", "#8C67BE", "#94A3B8", "#F97316"]))
    # A legenda abaixo do gráfico não disputa largura com a rosca quando a
    # sidebar reduz o contêiner do dashboard.
    layout = chart_layout(
        height=height,
        showlegend=True,
        legend=dict(orientation="h", x=.5, xanchor="center", y=-.08, yanchor="top"),
    )
    layout["margin"]["b"] = 58
    fig.update_layout(**layout, annotations=[dict(text=center, x=.5, y=.5, showarrow=False, font=dict(size=18, color="#0B2459"))])
    return fig


def monthly_line(df: pd.DataFrame, value_col: str, title_name: str, money: bool = False, height: int = 320) -> go.Figure:
    if df.empty:
        return empty_fig(height=height)
    data = df.groupby("ano_mes", as_index=False).agg(valor=(value_col, "sum")).sort_values("ano_mes")
    data["label"] = pd.to_datetime(data["ano_mes"] + "-01").dt.strftime("%m/%Y")
    data["texto"] = data["valor"].map(lambda value: br_money(value) if money else br_int(value))
    hover_format = ",.2f" if money else ",.0f"
    hover_prefix = "R$ " if money else ""
    fig = go.Figure(go.Scatter(x=data["label"], y=data["valor"], mode="lines+markers+text", text=data["texto"], textposition="top center", name=title_name, fill="tozeroy", fillcolor="rgba(18, 92, 201, 0.10)", hovertemplate=f"<b>%{{x}}</b><br>{title_name}: {hover_prefix}%{{y:{hover_format}}}<extra></extra>", line=dict(color="#125CC9", width=3), marker=dict(size=8, color="#125CC9")))
    fig.update_layout(**chart_layout(height=height))
    fig.update_yaxes(showgrid=True, gridcolor="#E8EDF5", zeroline=False, tickprefix=hover_prefix)
    fig.update_xaxes(showgrid=False, type="category", tickmode="auto", nticks=6, tickangle=-35, automargin=True)
    return fig


def top_group(df: pd.DataFrame, group_col: str, value_col: str, n: int = 10, op: str = "count") -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=[group_col, "valor"])
    if op == "sum":
        result = df.groupby(group_col, as_index=False)[value_col].sum().rename(columns={value_col: "valor"})
    elif op == "mean":
        result = df.groupby(group_col, as_index=False)[value_col].mean().rename(columns={value_col: "valor"})
    else:
        result = df.groupby(group_col, as_index=False).size().rename(columns={"size": "valor"})
    return result.sort_values("valor", ascending=False).head(n)
