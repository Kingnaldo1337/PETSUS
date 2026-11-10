import pandas as pd

from petsus.dashboard.test_processes import add_test_processes


def test_examples_are_varied_scoped_stable_and_do_not_mutate_source():
    source = pd.DataFrame([dict(processo_id="ORIGINAL", paciente_id="PAC1", paciente="Paciente",
        idade=40, data_ajuizamento=pd.Timestamp("2026-01-01"))])
    original = source.copy(deep=True)
    result = add_test_processes(source, "2026-11-10")
    pd.testing.assert_frame_equal(source, original)
    assert len(result) == 7
    assert result.paciente_id.eq("PAC1").all()
    assert result.processo_id.nunique() == 7
    examples = result[result.processo_id.ne("ORIGINAL")]
    assert examples.tipo_fluxo_saude.nunique() == 3
    assert examples.desfecho.nunique() == 4
    assert examples.etapa_saude_ordem.eq(0).any()
    assert examples.etapa_saude_ordem.gt(0).any()
    assert examples.ultima_movimentacao_data.le(pd.Timestamp("2026-11-10")).all()
    again = add_test_processes(result, "2026-11-10")
    assert len(again) == 7
    assert again.processo_id.tolist() == result.processo_id.tolist()


def test_empty_scope_remains_empty():
    assert add_test_processes(pd.DataFrame(), "2026-11-10").empty
