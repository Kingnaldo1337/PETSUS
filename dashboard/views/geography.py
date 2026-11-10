from __future__ import annotations

from .shared import (
    LABELS,
    _cards,
    _plot,
    _ranking,
    _table,
    br_int,
    br_money,
    empty_fig,
    protected_aggregate,
    px,
    section_title,
    semantic_color,
    st,
)


def _render_geography(dff, k):
    _cards([
        ("Municípios", br_int(dff["municipio"].nunique()), "municípios no recorte", "📍", "icon-blue"),
        ("Custo por paciente", br_money(dff["custo_estimado"].sum() / dff["paciente_id"].nunique()), "estimativa ÷ pacientes distintos filtrados; não população municipal", "$", "icon-green"),
    ])
    geo = protected_aggregate(dff, ["municipio", "uf", "regiao", "latitude", "longitude"])
    a, b = st.columns([1.4, 1])
    with a:
        with st.container(border=True, key="manager_panel_municipios_com_dados_publicaveis"):
            section_title("Municípios com dados publicáveis")
            if geo.empty:
                _plot(empty_fig(), key="geography:map")
            else:
                fig = px.scatter_geo(geo, lat="latitude", lon="longitude", size="processos", color="regiao", color_discrete_map={region: semantic_color(region) for region in geo["regiao"].unique()}, hover_name="municipio", hover_data={"uf": True, "processos": True, "pacientes": True, "latitude": False, "longitude": False}, labels=LABELS, height=390)
                fig.update_geos(showcountries=True, countrycolor="#CBD5E1", showland=True, landcolor="#F4F7FB", showocean=True, oceancolor="#E8F2FB", fitbounds="locations")
                fig.update_layout(margin=dict(l=0, r=0, t=0, b=0), legend=dict(orientation="h", y=1.02, x=0))
                _plot(fig, key="geography:map")
    with b:
        _ranking(dff, "regiao", "Processos por região", height=390)
    a, b = st.columns(2)
    with a:
        _ranking(dff, "municipio", "Municípios por processos")
    with b:
        _ranking(dff, "municipio", "Municípios por custo estimado", "custo_estimado", "sum")
    with st.container(border=True, key="manager_panel_tabela_geografica_protegida"):
        section_title("Tabela geográfica protegida")
        _table(geo[["regiao", "uf", "municipio", "processos", "pacientes", "custo_total", "custo_medio"]].sort_values("processos", ascending=False))


def render_geography(dff, base, k, participacao, part_custo, paciente_ids_sel):
    return _render_geography(dff, k)
