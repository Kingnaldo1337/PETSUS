import pandas as pd

from dashboard.charts import distribution_bar, monthly_line, semantic_color, top_group
from dashboard.views import judgment_summary, mask_cpf, mask_personal_data, protected_aggregate


def test_procedencia_keeps_partial_pending_and_agreement_out_of_numerator():
    source = pd.DataFrame({"desfecho": ["Procedente", "Procedente", "Parcialmente procedente", "Improcedente", "Em andamento", "Acordo", "Extinto"]})
    summary = judgment_summary(source)

    assert summary["procedencia"] == 50
    assert summary["procedencia_parcial"] == 25
    assert summary["julgados"] == 4
    assert summary["pendentes"] == 1
    assert summary["acordos"] == 1


def test_processes_without_merit_judgment_do_not_display_zero_success_rate():
    summary = judgment_summary(pd.DataFrame({"desfecho": ["Em andamento", "Acordo"]}))
    assert summary["procedencia"] is None
    assert summary["procedencia_parcial"] is None


def _cohort(sizes):
    records = []
    for category, count in sizes.items():
        for index in range(count):
            records.append({"grupo": category, "paciente_id": f"{category}-{index}", "processo_id": f"{category}-{index}", "custo_estimado": 100})
    return pd.DataFrame(records)


def test_small_cells_use_distinct_people_instead_of_number_of_processes():
    source = _cohort({"pequeno": 4, "publicavel": 7, "outro": 8})
    source = pd.concat([source, source[source.grupo.eq("pequeno")]] * 3, ignore_index=True)
    result = protected_aggregate(source, ["grupo"])
    assert "pequeno" not in result.grupo.tolist()
    assert result.pacientes.ge(5).all()
    # Uma segunda célula é protegida para impedir reconstrução por subtração.
    assert result.grupo.tolist() == ["outro"]


def test_aggregate_export_contains_no_patient_identifiers():
    source = _cohort({"A": 5, "B": 8})
    source["cpf"] = "12345678901"
    source["paciente"] = "Nome completo do paciente"
    exported = protected_aggregate(source, ["grupo"]).to_csv(index=False)
    assert "12345678901" not in exported
    assert "Nome completo" not in exported
    assert "paciente_id" not in exported


def test_cpf_masking_does_not_change_source():
    source = pd.DataFrame({"cpf": ["123.456.789-01", None]})
    assert mask_cpf("12345678901") == "123.***.***-01"
    masked = mask_personal_data(source)
    assert masked.cpf.tolist() == ["123.***.***-01", "Não informado"]
    assert source.cpf.iloc[0] == "123.456.789-01"


def test_same_jurisdiction_keeps_color_across_charts_and_sort_orders():
    source = pd.DataFrame({"competencia": ["Justiça Estadual", "Justiça Federal"], "processos": [20, 10]})
    chart = distribution_bar(source, "competencia", "processos")
    assert chart.data[0].type == "bar"
    for label, color in zip(chart.data[0].y, chart.data[0].marker.color):
        assert color == semantic_color(label)


def test_monthly_chart_has_no_overlapping_text_and_does_not_join_suppressed_months():
    source = _cohort({"2025-01": 7, "2025-02": 2, "2025-03": 8, "2025-04": 2})
    source["ano_mes"] = source.grupo
    source["qtd"] = 1
    chart = monthly_line(source, "qtd", "Processos")
    assert chart.data[0].mode == "lines+markers"
    assert chart.data[0].connectgaps is False
    assert pd.isna(chart.data[0].y[1])


def test_rankings_apply_same_privacy_rule_to_costs_and_counts():
    source = _cohort({"rarissimo": 2, "pequeno_publicavel": 5, "grande": 20})
    result = top_group(source, "grupo", "custo_estimado", op="sum")
    assert result.grupo.tolist() == ["grande"]


def test_age_distribution_preserves_chronological_order_instead_of_ranking_counts():
    source = pd.DataFrame({"faixa": ["0 a 9", "10 a 19", "20 a 29"], "pacientes": [8, 20, 5]})
    chart = distribution_bar(source, "faixa", "pacientes", preserve_order=True)
    assert list(chart.data[0].y)[::-1] == source.faixa.tolist()
    assert chart.layout.xaxis.range[0] == 0


def test_single_month_uses_a_bar_without_suggesting_a_time_trend():
    source = _cohort({"2025-01": 7})
    source["ano_mes"] = source.grupo
    source["qtd"] = 1
    chart = monthly_line(source, "qtd", "Processos")
    assert chart.data[0].type == "bar"
    assert list(chart.data[0].x) == [7]
    assert chart.layout.xaxis.range[0] == 0
    assert "Um único mês" in chart.layout.annotations[0].text


def test_responsibility_consultation_uses_selected_process_and_handles_missing_classification():
    from streamlit.testing.v1 import AppTest

    app = AppTest.from_string('''
import pandas as pd
from dashboard.views import _render_responsibility_detail
_render_responsibility_detail(pd.DataFrame({
    "processo_id": ["P1", "P2", "P3"],
    "ente_responsavel": ["Estado", "Compartilhada", None],
    "item_demandado": ["Item A", "Item B", "Item C"],
}))
''').run()
    assert not app.exception
    assert not app.metric
    app.selectbox(key="competency_process").select("P1").run()
    assert app.metric[0].value == "Estado"
    app.selectbox(key="competency_process").select("P2").run()
    assert app.metric[0].value == "Compartilhada"
    app.selectbox(key="competency_process").select("P3").run()
    assert app.metric[0].value == "Não informado"
    assert not app.exception


def test_empty_distributions_on_same_page_have_distinct_stable_element_keys():
    from streamlit.testing.v1 import AppTest

    script = '''
import pandas as pd
from dashboard.views import _distribution
source = pd.DataFrame({
    "processo_id": ["p1", "p2", "p3", "p4", "p5"],
    "paciente_id": ["a", "b", "c", "d", "e"],
    "rename_incorporado": ["Sim", "Sim", "Não", "Não", "Não"],
    "pcdt_aplicavel": ["Sim", "Sim", "Não", "Não", "Não"],
})
_distribution(source, "rename_incorporado", "Incorporação à RENAME")
_distribution(source, "pcdt_aplicavel", "PCDT aplicável")
'''
    app = AppTest.from_string(script).run()
    assert not app.exception
    assert len(app.get("plotly_chart")) == 2
    app.run()
    assert not app.exception
