import pandas as pd
from streamlit.testing.v1 import AppTest

from petsus.data.demo import enrich_judicialization


def test_administrative_delay_is_generated_and_flagged_with_an_action(monkeypatch):
    monkeypatch.setattr("petsus.data.demo.stable_choice", lambda key, choices: "Demora administrativa")
    result = enrich_judicialization(pd.DataFrame({"processo_id": ["P1"], "natureza": ["Outros"]}))
    assert result.iloc[0].judicializacao_potencialmente_evitavel == "Sim"
    assert "prazo de resposta" in result.iloc[0].motivo_potencialmente_evitavel


def prevention_app(groups):
    records = [
        {"processo_id": f"{group}-{index}", "paciente_id": f"{group}-{index}",
         "causa_judicializacao": cause, "judicializacao_potencialmente_evitavel": flag}
        for group, (cause, flag, count) in enumerate(groups)
        for index in range(count)
    ]
    return AppTest.from_string(
        "import pandas as pd\nfrom dashboard.views import _render_prevention\n"
        f"_render_prevention(pd.DataFrame({records!r}))"
    ).run()


def test_prevention_shows_filtered_denominators_coverage_and_administrative_actions():
    app = prevention_app([
        ("Demora administrativa", "Sim", 8),
        ("Falha de comunicação", "Sim", 6),
        ("Ausência de vaga", "Não", 6),
        ("Sem motivo informado", None, 6),
    ])
    assert not app.exception
    cards = " ".join(item.value for item in app.markdown)
    assert "53,8%" in cards  # 14 de 26 processos, incluindo os não classificados no total.
    assert "76,9%" in cards  # 20 de 26 processos com classificação.
    table = app.dataframe[1].value
    assert table["Processos"].tolist() == [8, 6]
    assert table["% de todos os processos filtrados"].tolist() == ["30,8%", "23,1%"]
    assert table["% das demandas potencialmente evitáveis"].tolist() == ["57,1%", "42,9%"]
    assert table["Ação administrativa sugerida"].str.len().gt(0).all()


def test_prevention_distinguishes_no_candidates_from_protected_candidates():
    empty = prevention_app([("Ausência de vaga", "Não", 6)])
    assert not empty.exception
    assert any("Nenhuma demanda está sinalizada" in item.value for item in empty.info)
    protected = prevention_app([("Demora administrativa", "Sim", 2), ("Ausência de vaga", "Não", 6)])
    assert not protected.exception
    assert any("Nenhuma célula publicável" in item.value for item in protected.info)
    assert any("Suprimido" in item.value for item in protected.markdown)
