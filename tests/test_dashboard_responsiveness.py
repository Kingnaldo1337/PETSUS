import pandas as pd

from dashboard.charts import CORES, barh, chart_layout, donut
from petsus.dashboard.navigation import navigation_for


def test_chart_layout_keeps_layout_responsive():
    layout = chart_layout(height=350)

    assert layout["height"] == 350
    assert layout["autosize"] is True
    assert layout["margin"]["l"] == 10
    assert layout["margin"]["r"] == 40


def test_horizontal_bar_uses_auto_margin_for_long_labels():
    df = pd.DataFrame({
        "item_demandado": ["Medicamento de uso contínuo para tratamento de doenças raras", "Outro item"],
        "valor": [10, 8],
    })

    fig = barh(df, "item_demandado", "valor", height=300)

    assert fig.layout.yaxis.automargin is True
    assert fig.layout.margin.r >= 10


def test_bar_uses_fixed_semantic_colors():
    df = pd.DataFrame(
        {
            "competencia": ["Justiça Federal", "Justiça Estadual"],
            "processos": [3, 5],
        }
    )

    fig = barh(
        df,
        "competencia",
        "processos",
        color={
            "Justiça Estadual": CORES["justica_estadual"],
            "Justiça Federal": CORES["justica_federal"],
        },
    )

    assert list(fig.data[0].marker.color) == [
        CORES["justica_federal"],
        CORES["justica_estadual"],
    ]


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


def test_manager_specific_pages_hidden_from_patients():
    manager_pages, _ = navigation_for(True)
    user_pages, _ = navigation_for(False)

    for hidden in ("Demandas", "Medicamentos", "Competência", "Custos", "Geografia", "Gestão interna"):
        assert hidden in manager_pages
        assert hidden not in user_pages


def test_dense_tracking_chart_reserves_space_for_every_multiline_label():
    df = pd.DataFrame({
        "etapa": [f"Etapa de cumprimento na rede de saúde número {index}" for index in range(24)],
        "processos": list(range(1, 25)),
    })
    fig = barh(df, "etapa", "processos", height=320)
    available_height = fig.layout.height - fig.layout.margin.t - fig.layout.margin.b
    max_lines = max(label.count("<br>") + 1 for label in fig.layout.yaxis.ticktext)
    assert available_height / len(df) >= max_lines * 18 + 12
    assert len(fig.data[0].y) == len(df)
    assert list(fig.data[0].x) == df.processos.tolist()


def test_dominant_annotation_does_not_take_space_reserved_for_category_labels():
    df = pd.DataFrame({"etapa": [f"Etapa {index}" for index in range(12)], "processos": list(range(1, 12)) + [1000]})
    fig = barh(df, "etapa", "processos", height=320, separate_dominant=True)
    available_height = fig.layout.height - fig.layout.margin.t - fig.layout.margin.b
    assert available_height / len(fig.data[0].y) >= 34
    assert "1.000" in fig.layout.annotations[0].text
