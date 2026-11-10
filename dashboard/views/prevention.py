from __future__ import annotations

from .shared import (
    PREVENTION_ACTIONS,
    _cards,
    _count,
    _rate,
    _table,
    br_float,
    pct,
    pd,
    protected_aggregate,
    section_title,
    st,
)


def _render_prevention(dff):
    needed = {"judicializacao_potencialmente_evitavel", "causa_judicializacao"}
    if not needed.issubset(dff.columns):
        st.info("Esta base ainda não tem classificação de prevenção. Não é possível estimar o indicador sem esses dados.")
        return
    mask = dff["judicializacao_potencialmente_evitavel"].eq("Sim")
    classified = dff["judicializacao_potencialmente_evitavel"].isin(["Sim", "Não"])
    _cards([
        ("Judicialização potencialmente evitável", _rate(dff, mask), "processos classificados como potencialmente evitáveis ÷ processos do recorte", "↻", "icon-green"),
        ("Demandas potencialmente evitáveis", _count(dff, mask), "oportunidades de solução administrativa; hipótese de triagem", "📋", "icon-blue"),
        ("Cobertura da classificação", _rate(dff, classified), "processos com classificação informada ÷ processos do recorte", "✓", "icon-purple"),
    ])
    st.info("O indicador identifica barreiras que podem ser avaliadas para solução administrativa ou mediação. A sinalização é potencial: não comprova que a ação poderia ter sido evitada nem restringe o acesso do paciente à Justiça.")
    with st.expander("Como o indicador é calculado e quais motivos são considerados"):
        st.markdown("**Percentual = processos classificados como potencialmente evitáveis ÷ total de processos dos filtros atuais × 100.** Cada processo entra uma vez na contagem. Registros sem classificação permanecem no total, mas não são contados como potencialmente evitáveis; consulte a cobertura para avaliar a completude do cadastro. ‘Não’ significa ausência de sinalização neste critério, sem afirmar que uma solução administrativa seria impossível.")
        criteria = pd.DataFrame(PREVENTION_ACTIONS.items(), columns=["Motivo para triagem", "Encaminhamento a avaliar"])
        st.dataframe(criteria, hide_index=True, use_container_width=True, column_config={column: st.column_config.TextColumn(column, width="large") for column in criteria})
    if not mask.any():
        st.info("Nenhuma demanda está sinalizada como potencialmente evitável nos filtros atuais. Confira a classificação antes de concluir que não há oportunidades de prevenção.")
        return
    with st.container(border=True, key="manager_panel_oportunidades_de_prevencao_por_causa"):
        section_title("Oportunidades de prevenção por causa")
        opportunities = dff.loc[mask].copy()
        groups = ["causa_judicializacao"]
        if "motivo_potencialmente_evitavel" not in opportunities:
            opportunities["motivo_potencialmente_evitavel"] = opportunities["causa_judicializacao"].map(PREVENTION_ACTIONS).fillna("Validar o motivo e definir o encaminhamento com a equipe responsável.")
        groups.append("motivo_potencialmente_evitavel")
        table = protected_aggregate(opportunities, groups)
        table["% de todos os processos filtrados"] = table["processos"].map(lambda value: f"{br_float(pct(value, len(dff)))}%")
        table["% das demandas potencialmente evitáveis"] = table["processos"].map(lambda value: f"{br_float(pct(value, mask.sum()))}%")
        _table(table[groups + ["processos", "pacientes", "% de todos os processos filtrados", "% das demandas potencialmente evitáveis"]].sort_values("processos", ascending=False), height=460)
        st.caption("Priorize os motivos mais recorrentes. Cada linha mostra seu peso no recorte completo e entre as demandas sinalizadas. Grupos pequenos são protegidos; as linhas publicadas podem não somar 100%.")
    with st.container(border=True, key="manager_panel_fluxo_de_prevencao"):
        section_title("Próximos passos para a gestão")
        st.markdown("1. Conferir a causa e a necessidade atual do paciente.\n2. Identificar o serviço ou ente responsável e a pendência de acesso.\n3. Avaliar encaminhamento administrativo ou mediação, com responsável e prazo.\n4. Confirmar o atendimento e acompanhar a resolução da barreira.")
        st.caption("Os números representam oportunidades identificadas, não casos resolvidos ou redução comprovada de ações judiciais.")


def render_prevention(dff):
    return _render_prevention(dff)
