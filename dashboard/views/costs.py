from __future__ import annotations

from .shared import (
    _cards,
    _cost_definitions,
    _plot,
    _publishable_subset,
    _ranking,
    _table,
    br_money,
    monthly_line,
    protected_aggregate,
    section_title,
    st,
)


def _render_costs(dff, k, part_custo):
    _cards([
        ("Custo Total", br_money(dff["custo_estimado"].sum()), "estimativa por processo; não gasto executado", "$", "icon-green"),
        ("Ticket Médio", br_money(dff["custo_estimado"].mean()), "soma estimada ÷ processos do recorte", "🧾", "icon-blue"),
        ("Custo Medicamentos", br_money(dff.loc[dff["natureza"].eq("Medicamentos"), "custo_estimado"].sum()) if _publishable_subset(dff, dff["natureza"].eq("Medicamentos")) else "Suprimido", "custo estimado de processos de medicamentos no período", "💊", "icon-purple"),
    ])
    _cost_definitions()
    a, b = st.columns(2)
    with a:
        with st.container(border=True, key="manager_panel_evolucao_mensal_do_custo_estimado"):
            section_title("Evolução mensal do custo estimado")
            _plot(monthly_line(dff, "custo_estimado", "Custo estimado", money=True, height=350), key="costs:monthly_cost")
    with b:
        _ranking(dff, "esfera", "Custo estimado por esfera judicial", "custo_estimado", "sum")
    a, b = st.columns(2)
    with a:
        _ranking(dff, "item_demandado", "Itens com maior impacto financeiro", "custo_estimado", "sum")
    with b:
        _ranking(dff, "especialidade", "Custo estimado por especialidade", "custo_estimado", "sum")
    with st.container(border=True, key="manager_panel_custo_tipico_e_dispersao_por_natureza"):
        section_title("Custo típico e dispersão por natureza")
        summary = protected_aggregate(dff, ["natureza"], custo_mediano=("custo_estimado", "median"), custo_q1=("custo_estimado", lambda values: values.quantile(.25)), custo_q3=("custo_estimado", lambda values: values.quantile(.75)))
        _table(summary[["natureza", "processos", "pacientes", "custo_mediano", "custo_q1", "custo_q3"]])
        st.caption("Mediana: metade dos processos custa até esse valor. Do 1º ao 3º quartil está a metade central dos custos (intervalo interquartil). A tabela usa todos os processos publicáveis, sem amostragem e sem misturar média com distribuição.")


def render_costs(dff, base, k, participacao, part_custo, paciente_ids_sel):
    return _render_costs(dff, k, part_custo)
