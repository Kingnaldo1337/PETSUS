"""Acabamento visual comum aos gráficos, incluindo as preferências de leitura."""
from __future__ import annotations

import colorsys
import re

import plotly.graph_objects as go

FONT_FAMILY = "Inter, Segoe UI, Arial, sans-serif"


def _contrast_color(color):
    if not isinstance(color, str) or not re.fullmatch(r"#[0-9a-fA-F]{6}", color):
        return color
    rgb = tuple(int(color[index:index + 2], 16) / 255 for index in (1, 3, 5))
    hue, light, saturation = colorsys.rgb_to_hls(*rgb)
    brighter = colorsys.hls_to_rgb(hue, max(light, .72), saturation)
    return "#" + "".join(f"{round(channel * 255):02x}" for channel in brighter)


def apply_chart_appearance(fig: go.Figure, *, contrast: bool = False, large_text: bool = False) -> go.Figure:
    """Estiliza sem modificar valores, rótulos, intervalos ou regras de privacidade."""
    ink, muted, surface, grid = ("#FFFFFF", "#E2E8F0", "#000000", "#475569") if contrast else ("#173653", "#60758C", "rgba(0,0,0,0)", "#ECF1F7")
    size = 15 if large_text else 12
    fig.update_layout(
        paper_bgcolor=surface, plot_bgcolor=surface,
        font=dict(family=FONT_FAMILY, size=size, color=ink),
        separators=",.",
        hoverlabel=dict(bgcolor="#FFFFFF" if contrast else "#102F56", bordercolor="#FFFFFF" if contrast else "#102F56", font=dict(family=FONT_FAMILY, size=size + 1, color="#000000" if contrast else "#FFFFFF"), align="left"),
        legend=dict(font=dict(size=size, color=muted), bgcolor="rgba(0,0,0,0)", borderwidth=0),
    )
    fig.update_xaxes(tickfont=dict(size=size, color=muted), title_font=dict(size=size, color=muted), gridcolor=grid, zeroline=False, showline=False)
    fig.update_yaxes(tickfont=dict(size=size, color=muted), title_font=dict(size=size, color=muted), gridcolor=grid, zeroline=False, showline=False)
    for annotation in fig.layout.annotations or ():
        annotation.font.update(color=ink, size=size)
    for trace in fig.data:
        if trace.type in {"bar", "scatter"}:
            trace.textfont.update(color=ink, size=size)
        if contrast:
            if hasattr(trace, "marker"):
                colors = trace.marker.color
                if isinstance(colors, str):
                    trace.marker.color = _contrast_color(colors)
                elif colors is not None and not isinstance(colors, (int, float)):
                    trace.marker.color = [_contrast_color(color) for color in colors]
            if trace.type == "scatter":
                trace.line.color = _contrast_color(trace.line.color)
                if trace.fill and trace.fill != "none":
                    trace.fillcolor = "rgba(125,211,252,.12)"
    if fig.layout.geo:
        fig.update_geos(bgcolor=surface, landcolor="#111827" if contrast else "#F1F5FA", oceancolor="#000000" if contrast else "#E8F1F8", countrycolor="#94A3B8" if contrast else "#CBD5E1")
    return fig
