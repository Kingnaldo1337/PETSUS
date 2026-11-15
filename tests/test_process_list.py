import pandas as pd

from dashboard.views.processes import process_list


def test_process_list_keeps_latest_record_and_searches_without_accents():
    base = pd.DataFrame([
        {"processo_id": "001", "paciente": "João", "municipio": "Fortaleza", "item_demandado": "Consulta", "etapa_judicial": "Distribuído", "ultima_movimentacao_data": "2026-01-01"},
        {"processo_id": "001", "paciente": "João", "municipio": "Fortaleza", "item_demandado": "Consulta", "etapa_judicial": "Decisão", "ultima_movimentacao_data": "2026-02-01"},
        {"processo_id": "002", "paciente": "Maria", "municipio": "Sobral", "item_demandado": "Exame", "ultima_movimentacao_data": "2026-01-01"},
    ])
    view = process_list(base)
    assert len(view) == 2
    assert view.iloc[0]["Andamento judicial"] == "Decisão"
    assert process_list(base, "JOAO")["Processo"].tolist() == ["001"]
    assert process_list(base, "sobral")["Requerente"].tolist() == ["Maria"]
    assert process_list(base, "exame")["Processo"].tolist() == ["002"]
    assert process_list(base, "inexistente").empty
