from datetime import date
from math import isclose

import pandas as pd

from petsus.data.demo import enrich_petsus_fields, enrich_process_tracking
from petsus.data.filters import DashboardFilters, apply_filters
from petsus.data.metrics import calculate_kpis


def scenario(**overrides):
    row = {
        "processo_id": "P1", "data_ajuizamento": pd.Timestamp("2024-05-01"),
        "paciente_id": "A", "paciente": "Paciente fictício", "idade": 46,
        "sexo": "F", "municipio": "Fortaleza", "uf": "CE", "natureza": "Medicamentos",
        "tipo_demanda": "Medicamentos", "item_demandado": "Insulina Glargina",
        "condicao_clinica": "Transtornos mentais", "especialidade": "Oncologia",
        "fase_processual": "Conhecimento", "desfecho": "Em andamento",
        "tempo_tramitacao_dias": 9, "tempo_liminar_dias": float("nan"),
        "urgente": "Não", "liminar": "Sim", "custo_estimado": 300000,
    }
    row.update(overrides)
    return row


def test_pending_outcome_has_no_success_rate_and_partial_has_own_denominator():
    data = pd.DataFrame([scenario(desfecho=outcome) for outcome in
                         ["Procedente", "Parcialmente procedente", "Improcedente", "Acordo", "Em andamento"]])
    kpi = calculate_kpis(data)
    assert isclose(kpi["procedencia"], 100 / 3)
    assert isclose(kpi["procedencia_parcial"], 100 / 3)
    assert (kpi["julgados"], kpi["pendentes"], kpi["acordos"]) == (3, 1, 1)
    assert calculate_kpis(data.iloc[-1:])["procedencia"] is None


def test_clinical_categories_and_no_urgent_request_are_consistent():
    rows = [scenario(), scenario(processo_id="P2", item_demandado="Terapia multidisciplinar",
                                 condicao_clinica="Diabetes mellitus", tipo_demanda="Órteses, próteses e materiais"),
            scenario(processo_id="P3", item_demandado="Ressonância magnética", natureza="Cirurgia")]
    data = enrich_petsus_fields(pd.DataFrame(rows), "2026-11-09")
    assert data.iloc[0].condicao_clinica == "Diabetes mellitus"
    assert data.iloc[0].especialidade == "Endocrinologia"
    assert data.iloc[1].tipo_demanda == "Consultas e terapias"
    assert data.iloc[1].natureza == "Outros"
    assert data.iloc[2].tipo_fluxo_saude == "Tratamento ou serviço"
    assert data.liminar.eq("Não").all()
    assert data.decisao_urgencia.eq("Não há pedido urgente neste cenário").all()
    assert data.data_intimacao.isna().all()


def test_reference_date_is_independent_of_filing_date_filter():
    reference = pd.Timestamp("2026-11-09")
    data = enrich_petsus_fields(pd.DataFrame([scenario()]), reference)
    data["_search"] = ""
    filtered = apply_filters(data, DashboardFilters(end_date=date(2024, 5, 28)))
    assert len(filtered) == 1
    assert filtered.iloc[0].tempo_tramitacao_dias == (reference - pd.Timestamp("2024-05-01")).days
    assert filtered.iloc[0].data_referencia_calculo == reference
    assert filtered.attrs["data_referencia_calculo"] == "2026-11-09"


def test_historical_salary_and_unknown_year_are_not_replaced_by_2026():
    data = enrich_petsus_fields(pd.DataFrame([
        scenario(processo_id=str(year), item_demandado="Apixabana 5mg", data_ajuizamento=pd.Timestamp(year, 5, 1))
        for year in [2023, 2024, 2025, 2026]
    ]), "2026-11-09")
    assert pd.isna(data.iloc[0].limite_210_sm_ajuizamento)
    assert data.iloc[0].competencia_petsus == "Não classificada"
    assert data.salario_minimo_ajuizamento.iloc[1:].tolist() == [1412, 1518, 1621]
    assert data.limite_210_sm_ajuizamento.iloc[1:].tolist() == [296520, 318780, 340410]


def test_chronology_deadlines_and_negative_outcomes_do_not_start_fulfillment():
    data = enrich_petsus_fields(pd.DataFrame([
        scenario(processo_id="P1", desfecho="Procedente", urgente="Sim"),
        scenario(processo_id="P2", desfecho="Improcedente", urgente="Sim"),
        scenario(processo_id="P3", data_ajuizamento=pd.Timestamp("2026-11-08"), desfecho="Procedente"),
    ]), "2026-11-09")
    positive = data.iloc[0]
    assert positive.data_ajuizamento <= positive.data_decisao <= positive.data_intimacao <= positive.data_limite_cumprimento
    assert positive.data_movimentacao_saude <= positive.ultima_movimentacao_data <= positive.data_referencia_calculo
    negative = data.iloc[1]
    assert negative.etapa_saude_ordem == 0
    assert negative.indicador_atraso == "Não"
    assert "Aguardando" not in negative.decisao_urgencia
    recent = data.iloc[2]
    assert recent.desfecho == "Em andamento"
    assert recent.tempo_tramitacao_dias == 1
    assert recent.indicador_atraso == "Não"


def test_future_filing_is_rejected_instead_of_negative_elapsed():
    try:
        enrich_process_tracking(pd.DataFrame([scenario(data_ajuizamento=pd.Timestamp("2027-01-01"))]), "2026-11-09")
    except ValueError as error:
        assert "posterior" in str(error)
    else:
        raise AssertionError("Ajuizamento futuro não deve produzir duração negativa")


def test_judicial_sphere_has_no_municipal_branch_and_matches_medicine_scenario():
    data = enrich_petsus_fields(pd.DataFrame([
        scenario(processo_id="INS", esfera="Municipal"),
        scenario(processo_id="API", esfera="Federal", item_demandado="Apixabana 5mg", custo_estimado=100),
        scenario(processo_id="CONS", esfera="Municipal", item_demandado="Consulta especializada"),
    ]), "2026-11-09")
    assert set(data.esfera) <= {"Estadual", "Federal"}
    medicines = data[data.medicamento_petsus.eq("Sim")]
    assert ("Justiça " + medicines.esfera).eq(medicines.competencia_petsus).all()


def test_pending_spellings_are_normalized_before_metrics_and_patient_messages():
    data = enrich_petsus_fields(pd.DataFrame([
        scenario(processo_id=str(index), desfecho=outcome)
        for index, outcome in enumerate([None, float("nan"), "", "  ", "Pendente"])
    ]), "2026-11-09")
    assert data.desfecho.eq("Em andamento").all()
    assert data.data_desfecho.isna().all()
    metrics = calculate_kpis(data)
    assert metrics["pendentes"] == 5
    assert metrics["procedencia"] is None
