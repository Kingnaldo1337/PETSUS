from __future__ import annotations

from .shared import (
    _cards,
    _distribution,
    _medication_subset,
    _ranking,
    _rate,
    _table,
    br_float,
    br_int,
    br_money,
    pct,
    pd,
    protected_aggregate,
    section_title,
    st,
)


def _render_medications(dff):
    med = _medication_subset(dff)
    if med is None:
        return
    _cards([
        ("Demandas de medicamentos", br_int(len(med)), "denominador: demandas de medicamentos filtradas", "💊", "icon-blue"),
        ("DCB distintos", br_int(med["medicamento_dcb"].nunique()), "princípios ativos; não apresentações", "🧪", "icon-purple"),
        ("Incorporados à RENAME", _rate(med, med["rename_incorporado"].eq("Sim")), "demandas incorporadas ÷ demandas de medicamentos", "✓", "icon-green"),
        ("Valor anual estimado", br_money(med["valor_anual_tratamento"].sum()), "projeção de 12 meses; não gasto executado", "📈", "icon-green"),
    ])
    st.caption("Os três valores medem conceitos diferentes e não devem ser somados. Nenhum comprova gasto executado. O preço é estimado, não é cotação oficial PMVG. Uma cotação CMED exige apresentação e quantidade de unidades.")
    a, b = st.columns(2)
    with a:
        _distribution(med, "rename_incorporado", "Incorporação à lista RENAME")
    with b:
        _distribution(med, "pcdt_aplicavel", "Existência de protocolo clínico (PCDT)")
    with st.container(border=True, key="manager_panel_assistencia_farmaceutica_e_dispensacao_administrativa"):
        section_title("Assistência farmacêutica e dispensação administrativa")
        st.write("Compare quantos processos solicitam medicamentos da assistência básica, especializada e dos demais componentes. O ente de dispensação é apresentado conforme o cadastro do medicamento.")
        groups = ["componente_sus"]
        if "ente_dispensacao_simulado" in med:
            groups.append("ente_dispensacao_simulado")
        comp = protected_aggregate(med, groups)
        # Zero é ausência de casos, não uma célula pequena: mantém visível a
        # comparação entre assistência básica, especializada e estratégica.
        for component, dispensing in [
            ("Assistência básica (CBAF)", "Município"),
            ("Assistência especializada (CEAF)", "Estado"),
            ("Assistência estratégica (CESAF)", "Compartilhada"),
        ]:
            if not med["componente_sus"].eq(component).any():
                row = {"componente_sus": component, "processos": 0, "pacientes": 0}
                if "ente_dispensacao_simulado" in groups:
                    row["ente_dispensacao_simulado"] = "Não se aplica — sem demandas"
                comp = pd.concat([comp, pd.DataFrame([row])], ignore_index=True)
        comp["% das demandas de medicamentos"] = comp["processos"].map(lambda value: f"{br_float(pct(value, len(med)))}%")
        _table(comp[groups + ["processos", "pacientes", "% das demandas de medicamentos"]])
        st.caption("Assistência básica, especializada e estratégica são componentes distintos. A dispensação administrativa identifica quem organiza o fornecimento e pode envolver pactuação entre entes. Ela não define automaticamente o réu nem a competência judicial.")
        st.caption("O percentual usa todas as demandas de medicamentos dos filtros atuais. Grupos com poucos pacientes são protegidos e, por isso, as linhas visíveis podem não somar 100%.")
    with st.container(border=True, key="manager_panel_classificacao_por_medicamento"):
        section_title("Classificação e dispensação por medicamento")
        groups = ["medicamento_dcb", "rename_incorporado", "componente_sus"]
        if "ente_dispensacao_simulado" in med:
            groups.append("ente_dispensacao_simulado")
        classification = protected_aggregate(med, groups)
        classification["% das demandas de medicamentos"] = classification["processos"].map(lambda value: f"{br_float(pct(value, len(med)))}%")
        _table(classification[groups + ["processos", "pacientes", "% das demandas de medicamentos"]].sort_values("processos", ascending=False), height=460)
        with st.expander("Como interpretar a classificação do medicamento"):
            st.markdown(
                "**RENAME:** Relação Nacional de Medicamentos Essenciais. A coluna mostra a incorporação informada no cadastro.\n\n"
                "**Assistência básica (CBAF):** Componente Básico da Assistência Farmacêutica.\n\n"
                "**Assistência especializada (CEAF):** Componente Especializado da Assistência Farmacêutica.\n\n"
                "**Assistência estratégica (CESAF):** Componente Estratégico da Assistência Farmacêutica.\n\n"
                "**Dispensação administrativa:** ente indicado no cadastro para organizar o fornecimento. "
                "Confirme o fluxo com a rede de saúde, considerando o medicamento, o protocolo e a pactuação local. "
                "Esse campo é separado da competência judicial, que indica qual ramo da Justiça analisa o processo."
            )
    a, b = st.columns(2)
    with a:
        _ranking(med, "medicamento_dcb", "Princípios ativos mais demandados")
    with b:
        _ranking(med, "medicamento_dcb", "Projeção de 12 meses por princípio ativo", "valor_anual_tratamento", "sum")
    with st.container(border=True, key="manager_panel_estimativa_sintetica_de_preco_por_administracao"):
        section_title("Estimativa de preço por administração")
        detail = protected_aggregate(med, ["medicamento_dcb", "apresentacao_padronizada"],
            preco_minimo=("pmvg_referencia", "min"), preco_maximo=("pmvg_referencia", "max"),
            valor_anual=("valor_anual_tratamento", "sum"))
        detail = detail.rename(columns={"preco_minimo": "Menor preço estimado por administração (R$)", "preco_maximo": "Maior preço estimado por administração (R$)"})
        _table(detail[["medicamento_dcb", "apresentacao_padronizada", "processos", "Menor preço estimado por administração (R$)", "Maior preço estimado por administração (R$)", "valor_anual"]])
        st.caption("Cenários agrupados pelo mesmo item e apresentação. Os preços derivam da projeção anual; não são consulta à CMED nem PMVG médio entre medicamentos.")


def render_medications(dff, base, k, participacao, part_custo, paciente_ids_sel):
    return _render_medications(dff)
