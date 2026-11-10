from __future__ import annotations

from .shared import (
    _cards,
    _count,
    _distribution,
    _plot,
    _ranking,
    _rate,
    _table,
    br_float,
    br_int,
    distribution_bar,
    pd,
    protected_aggregate,
    section_title,
    st,
)


def _render_patients(dff):
    patients = dff.drop_duplicates("paciente_id").copy()
    _cards([
        ("Pacientes", br_int(len(patients)), "pessoas distintas no recorte", "👥", "icon-green"),
        ("Idade Média", f"{br_float(patients['idade'].mean())} anos", "soma das idades informadas ÷ pacientes com idade", "🎂", "icon-blue"),
        ("% Feminino", _rate(patients, patients["sexo"].eq("Feminino")), "pacientes femininas ÷ pacientes distintos", "♀", "icon-purple"),
    ])
    a, b = st.columns(2)
    with a:
        with st.container(border=True, key="manager_panel_idade_em_intervalos_de_10_anos"):
            section_title("Idade em intervalos de 10 anos")
            ages = pd.to_numeric(patients["idade"], errors="coerce")
            labels = [f"{start} a {start+9}" for start in range(0, 120, 10)]
            patients["faixa_etaria"] = pd.cut(ages, bins=list(range(0, 121, 10)), labels=labels, right=False).astype("string").fillna("Idade não informada")
            patients.loc[ages.ge(120), "faixa_etaria"] = "120 ou mais (intervalo aberto)"
            age_table = protected_aggregate(patients, ["faixa_etaria"])
            age_order = labels + ["120 ou mais (intervalo aberto)", "Idade não informada"]
            age_table = age_table.sort_values("faixa_etaria", key=lambda values: values.map({label: index for index, label in enumerate(age_order)}))
            _plot(distribution_bar(age_table, "faixa_etaria", "pacientes", denominator=len(patients), height=430, preserve_order=True), key="patients:age")
            st.caption("Todos os intervalos fechados cobrem 10 anos completos; eventual categoria de 120 anos ou mais é aberta. Pacientes sem idade válida aparecem em categoria própria. Unidade: paciente distinto.")
    with b:
        _distribution(patients, "sexo", "Distribuição por sexo", height=380, patients=True)
    _ranking(patients, "condicao_clinica", "Condições clínicas mais frequentes")
    with st.container(border=True, key="manager_panel_perfil_socioassistencial"):
        section_title("Perfil socioassistencial")
        rows = []
        for title, column, value in [("SUS exclusivo", "sus_exclusivo", "Sim"), ("Pessoa com deficiência", "pcd", "Sim"), ("Doença rara", "doenca_rara", "Sim"), ("Renda até 1 salário mínimo", "renda_familiar", "Até 1 salário mínimo")]:
            mask = patients[column].eq(value)
            rows.append({"Indicador": title, "Pacientes distintos": _count(patients, mask), "% dos pacientes distintos": _rate(patients, mask)})
        _table(pd.DataFrame(rows), height=220)
    with st.container(border=True, key="manager_panel_distribuicao_do_custo_acumulado_por_paciente"):
        section_title("Distribuição do custo acumulado por paciente")
        totals = dff.groupby("paciente_id", as_index=False)["custo_estimado"].sum()
        totals["processo_id"] = totals["paciente_id"]
        totals["faixa_custo"] = pd.cut(totals["custo_estimado"], bins=[-1, 1000, 10000, 100000, float("inf")], labels=["Até R$ 1 mil", "Mais de R$ 1 mil até R$ 10 mil", "Mais de R$ 10 mil até R$ 100 mil", "Mais de R$ 100 mil"])
        grouped = protected_aggregate(totals, ["faixa_custo"])
        _table(grouped[["faixa_custo", "pacientes", "custo_total"]])
        st.caption("A análise usa faixas com pelo menos 5 pacientes distintos. Nomes, CPFs e rankings individuais não são necessários nesta visão analítica. Para uma consulta operacional autorizada, use Andamento.")


def render_patients(dff, base, k, participacao, part_custo, paciente_ids_sel):
    return _render_patients(dff)
