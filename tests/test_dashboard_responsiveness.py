import pandas as pd

from dashboard.charts import barh, chart_layout, donut
from petsus.dashboard.navigation import navigation_for


def test_chart_layout_keeps_layout_responsive():
    layout = chart_layout(height=350)

    assert layout["height"] == 350
    assert layout["autosize"] is True
    assert layout["margin"]["l"] == 10
    assert layout["margin"]["r"] == 20


def test_horizontal_bar_uses_auto_margin_for_long_labels():
    df = pd.DataFrame({
        "item_demandado": ["Medicamento de uso contínuo para tratamento de doenças raras", "Outro item"],
        "valor": [10, 8],
    })

    fig = barh(df, "item_demandado", "valor", height=300)

    assert fig.layout.yaxis.automargin is True
    assert fig.layout.margin.r >= 10


def test_donut_legend_does_not_consume_horizontal_space():
    df = pd.DataFrame({"label": ["Sim", "Não"], "valor": [7, 3]})

    fig = donut(df, "label", "valor", "10 demandas", height=300)

    assert fig.layout.legend.orientation == "h"
    assert fig.layout.legend.xanchor == "center"
    assert fig.layout.margin.b >= 50


def test_internal_management_is_available_only_to_managers():
    manager_pages, _ = navigation_for(True)
    user_pages, _ = navigation_for(False)

    assert "Gestão interna" in manager_pages
    assert "Gestão interna" not in user_pages
