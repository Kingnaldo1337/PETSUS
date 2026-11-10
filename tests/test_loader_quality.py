from pathlib import Path

import pandas as pd
import pytest

from petsus.config import REQUIRED_COLUMNS
from petsus.data.loader import DataLoadError, load_process_data


def source_frame():
    row = {column: "Exemplo" for column in REQUIRED_COLUMNS}
    row.update(processo_id="P1", paciente_id="A1", data_ajuizamento="2024-05-01",
               custo_estimado=100.0, idade=30, tempo_tramitacao_dias=10,
               tempo_liminar_dias=None, liminar="Não", urgente="Não",
               sus_exclusivo="Sim", pcd="Não", doenca_rara="Não")
    return pd.DataFrame([row])


def read(monkeypatch, tmp_path, frame, attach=lambda d: d, enrich=lambda d: d):
    path = tmp_path / "source.xlsx"
    path.touch()
    monkeypatch.setattr(pd, "read_excel", lambda *a, **kw: frame)
    return load_process_data(path, REQUIRED_COLUMNS, attach, enrich)


@pytest.mark.parametrize("column,value,reason", [
    ("paciente_id", None, "paciente_id ausente"),
    ("processo_id", "  ", "processo_id ausente"),
    ("custo_estimado", "desconhecido", "custo_estimado inválido"),
    ("custo_estimado", -0.01, "custo_estimado inválido"),
    ("custo_estimado", float("inf"), "custo_estimado inválido"),
    ("idade", -1, "idade inválida"),
    ("idade", 120, "idade inválida"),
    ("idade", 2.5, "idade inválida"),
    ("data_ajuizamento", "31/02/2025", "data_ajuizamento inválida"),
    ("urgente", "Talvez", "urgente diferente de Sim/Não"),
    ("pcd", None, "pcd diferente de Sim/Não"),
])
def test_invalid_batch_is_rejected_with_count(monkeypatch, tmp_path, column, value, reason):
    frame = source_frame().astype(object)
    frame.loc[0, column] = value
    calls = []
    with pytest.raises(DataLoadError, match=reason) as caught:
        read(monkeypatch, tmp_path, frame, enrich=lambda d: calls.append(d))
    assert "1 registro(s)" in str(caught.value)
    assert not calls


def test_duplicate_processes_are_rejected_even_after_trimming(monkeypatch, tmp_path):
    frame = pd.concat([source_frame(), source_frame()], ignore_index=True)
    frame.loc[1, "processo_id"] = " P1 "
    with pytest.raises(DataLoadError, match="2 registro\\(s\\) com processo_id duplicado"):
        read(monkeypatch, tmp_path, frame)


def test_success_does_not_mutate_original_frame(monkeypatch, tmp_path):
    frame = source_frame()
    original = frame.copy(deep=True)

    def mutate_copy(data):
        data["sentinel"] = "changed"
        return data

    result, discarded = read(monkeypatch, tmp_path, frame, attach=mutate_copy)
    assert discarded == 0
    assert result.iloc[0].ano_mes == "2024-05"
    assert result.iloc[0].custo_estimado == 100
    pd.testing.assert_frame_equal(frame, original)


def test_preparation_errors_have_data_load_contract(monkeypatch, tmp_path):
    def broken(data):
        raise ValueError("Ajuizamento posterior à referência.")

    with pytest.raises(DataLoadError, match="preparação.*Ajuizamento"):
        read(monkeypatch, tmp_path, source_frame(), enrich=broken)


def test_unreadable_workbook_has_actionable_error(monkeypatch, tmp_path):
    path = tmp_path / "broken.xlsx"
    path.touch()

    def broken(*args, **kwargs):
        raise PermissionError("internal OS detail")

    monkeypatch.setattr(pd, "read_excel", broken)
    with pytest.raises(DataLoadError, match="Verifique se o arquivo é um Excel válido") as caught:
        load_process_data(path, REQUIRED_COLUMNS, lambda d: d, lambda d: d)
    assert "internal OS detail" not in str(caught.value)


def test_real_xlsx_validates_without_data_loss(tmp_path):
    path = tmp_path / "real.xlsx"
    source_frame().to_excel(path, sheet_name="base_processos", index=False)
    result, discarded = load_process_data(path, REQUIRED_COLUMNS, lambda d: d, lambda d: d)
    assert len(result) == 1
    assert discarded == 0
