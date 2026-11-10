from __future__ import annotations

from .shared import (
    _cards,
    _count,
    _distribution,
    _plot,
    _ranking,
    _rate,
    br_float,
    br_int,
    br_money,
    judgment_summary,
    monthly_line,
    section_title,
    st,
)


def _render_overview(dff, base, k, participacao, part_custo):
    result = judgment_summary(dff)
    judged = dff[dff["desfecho"].isin(["Procedente", "Parcialmente procedente", "Improcedente"])]
    rate = _rate(judged, judged["desfecho"].eq("Procedente")) if result["julgados"] else "Não se aplica"
    _cards([
        ("Total de Processos", br_int(len(dff)), f"{br_float(participacao)}% da base; unidade: processo", "📄", "icon-blue"),
        ("Pacientes Ativos", br_int(dff["paciente_id"].nunique()), "pessoas distintas com processo no recorte", "👥", "icon-green"),
        ("Custo Total", br_money(dff["custo_estimado"].sum()), f"{br_float(part_custo)}% do custo estimado da base", "$", "icon-green"),
        ("Tempo Médio", f"{br_int(dff['tempo_tramitacao_dias'].mean())} dias", "soma dos tempos ÷ processos do recorte", "⏱", "icon-orange"),
        ("Taxa de Procedência", rate, "somente procedentes ÷ julgados de mérito", "⚖", "icon-purple"),
    ])
    st.caption("Tempo de tramitação: do ajuizamento ao julgamento ou desfecho registrado; nos casos em andamento, até a data de referência dos cálculos. A média usa todos os processos do recorte.")
    with st.container(border=True, key="manager_panel_como_interpretar_os_resultados"):
        section_title("Como interpretar os resultados")
        _cards([
            ("Parcialmente procedentes", _rate(judged, judged["desfecho"].eq("Parcialmente procedente")) if result["julgados"] else "Não se aplica", "parcialmente procedentes ÷ julgados de mérito", "◐", "icon-orange"),
            ("Pendentes de julgamento", _count(dff, dff["desfecho"].eq("Em andamento")), "em andamento; fora do denominador de procedência", "⌛", "icon-blue"),
            ("Acordos", _count(dff, dff["desfecho"].eq("Acordo")), "composição entre as partes; fora da taxa", "🤝", "icon-purple"),
        ])
        denominator = _count(dff, dff["desfecho"].isin(["Procedente", "Parcialmente procedente", "Improcedente"]))
        st.caption(f"Denominador dos percentuais de mérito: {denominator} processos julgados no recorte.")
        st.caption("Julgados de mérito = Procedente + Parcialmente procedente + Improcedente. Acordos, extinções, recursos sem julgamento registrado e processos em andamento não entram na taxa. Sem julgados, a taxa não se aplica. Resultado favorável não significa entrega do tratamento.")
    a, b = st.columns([1.4, 1])
    with a:
        with st.container(border=True, key="manager_panel_evolucao_mensal_dos_processos"):
            section_title("Evolução mensal dos processos")
            _plot(monthly_line(dff.assign(qtd=1), "qtd", "Processos"), key="overview:monthly_processes")
    with b:
        _distribution(dff, "desfecho", "Desfecho processual")
    a, b = st.columns(2)
    with a:
        _distribution(dff, "natureza", "Natureza da ação")
    with b:
        _ranking(dff, "item_demandado", "Itens mais demandados", separate=True)


def render_overview(dff, base, k, participacao, part_custo, paciente_ids_sel):
    return _render_overview(dff, base, k, participacao, part_custo)
