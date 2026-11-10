import plotly.graph_objects as go
import pandas as pd

from dashboard.charts import distribution_bar
from dashboard.theme import apply_chart_appearance


def test_high_contrast_preserves_chart_values_order_labels_and_axis_range():
    source = pd.DataFrame({"ente": ["Justiça Federal", "Justiça Estadual"], "processos": [10, 20]})
    fig = distribution_bar(source, "ente", "processos")
    values, labels, texts = list(fig.data[0].x), list(fig.data[0].y), list(fig.data[0].text)
    axis_range = fig.layout.xaxis.range
    apply_chart_appearance(fig, contrast=True, large_text=True)
    assert list(fig.data[0].x) == values
    assert list(fig.data[0].y) == labels
    assert list(fig.data[0].text) == texts
    assert fig.layout.xaxis.range == axis_range
    assert fig.layout.paper_bgcolor == "#000000"
    assert fig.layout.font.color == "#FFFFFF"
    assert fig.layout.font.size == 15
    assert len(set(fig.data[0].marker.color)) == 2


def test_map_uses_same_high_contrast_surface_without_changing_locations():
    fig = go.Figure(go.Scattergeo(lat=[-3.7], lon=[-38.5], marker=dict(color="#287BB5")))
    apply_chart_appearance(fig, contrast=True)
    assert list(fig.data[0].lat) == [-3.7]
    assert list(fig.data[0].lon) == [-38.5]
    assert fig.layout.geo.landcolor == "#111827"
    assert fig.layout.geo.oceancolor == "#000000"


def test_regular_chart_has_brazilian_separators_and_transparent_surface():
    fig = go.Figure(go.Bar(x=[1], y=[10]))
    apply_chart_appearance(fig)
    assert fig.layout.separators == ",."
    assert fig.layout.paper_bgcolor == "rgba(0,0,0,0)"
    assert fig.layout.hoverlabel.font.color == "#FFFFFF"
