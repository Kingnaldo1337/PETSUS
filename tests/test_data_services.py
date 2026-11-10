from datetime import date
from io import BytesIO

import pandas as pd
import pytest

from dashboard.ui import mask_cpf, safe_export_frame, suppress_small_counts, to_csv_bytes, to_excel_bytes
from petsus.access import AccessScopeError, restrict_data_for_user
from petsus.auth.models import AuthUser, ROLE_MANAGER, ROLE_USER
from petsus.dashboard.app_services import enrich_process_tracking
from petsus.data.filters import DashboardFilters, apply_filters
from petsus.data.metrics import calculate_kpis


def sample_data() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "data_ajuizamento": pd.to_datetime(["2026-01-10", "2026-02-10"]),
            "_search": ["ana pac1", "bia pac2"],
            "paciente_id": ["PAC1", "PAC2"],
            "sexo": ["F", "F"],
            "custo_estimado": [100.0, 300.0],
            "tempo_tramitacao_dias": [10, 30],
            "liminar": ["Sim", "Não"],
            "urgente": ["Não", "Sim"],
            "desfecho": ["Procedente", "Improcedente"],
            "idade": [20, 40],
            "municipio": ["A", "B"],
        }
    )


def test_filters_are_explicit_and_independent_from_streamlit():
    result = apply_filters(
        sample_data(),
        DashboardFilters(
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 31),
            search="ana",
            fields={"sexo": ("F",)},
        ),
    )
    assert result["paciente_id"].tolist() == ["PAC1"]


def test_metrics_are_calculated_in_data_layer():
    metrics = calculate_kpis(sample_data())
    assert metrics["total"] == 2
    assert metrics["custo"] == 400.0
    assert metrics["ticket"] == 200.0
    assert metrics["liminar"] == 50.0


def test_procedencia_uses_only_resolved_outcomes():
    data = pd.concat([sample_data().iloc[[0]]] * 5, ignore_index=True)
    data["desfecho"] = [
        "Procedente",
        "Parcialmente procedente",
        "Improcedente",
        "Em andamento",
        "Sem resolução de mérito",
    ]

    assert calculate_kpis(data)["procedencia"] == pytest.approx(200 / 3)


def test_procedencia_is_zero_when_no_outcome_is_resolved():
    data = sample_data()
    data["desfecho"] = ["Em andamento", "Sem resolução de mérito"]

    assert calculate_kpis(data)["procedencia"] == 0


def test_access_scope_is_applied_before_filters():
    manager = AuthUser(1, "Gestor", ROLE_MANAGER, None, "***")
    patient = AuthUser(2, "Ana", ROLE_USER, "PAC1", "***")
    assert len(restrict_data_for_user(sample_data(), manager)) == 2
    assert restrict_data_for_user(sample_data(), patient)["paciente_id"].tolist() == ["PAC1"]

    missing = AuthUser(3, "Sem vínculo", ROLE_USER, None, "***")
    try:
        restrict_data_for_user(sample_data(), missing)
    except AccessScopeError:
        pass
    else:
        raise AssertionError("Conta comum sem vínculo deveria ser rejeitada")


def test_mask_cpf_hides_malformed_values():
    assert mask_cpf("123.456.789-09") == "***.456.789-**"
    assert mask_cpf("CPF irregular 12345") == "***.***.***-**"


def test_safe_exports_remove_direct_patient_identifiers():
    data = pd.DataFrame(
        {
            "processo_id": ["PROC-1"],
            "paciente_id": ["PAC-1"],
            "paciente": ["Nome Sobrenome"],
            "cpf": ["123.456.789-09"],
            "cpf_origem": ["Fonte de dados"],
            "custo_estimado": [100.0],
        }
    )

    safe_frame = safe_export_frame(data)
    csv = pd.read_csv(BytesIO(to_csv_bytes(data)))
    excel = pd.read_excel(BytesIO(to_excel_bytes(data)))

    assert safe_frame.columns.tolist() == ["processo_id", "custo_estimado"]
    assert csv.columns.tolist() == safe_frame.columns.tolist()
    assert excel.columns.tolist() == safe_frame.columns.tolist()
    unsafe_csv = pd.read_csv(BytesIO(to_csv_bytes(data, safe_export=False)))
    assert "cpf" in unsafe_csv.columns


def test_small_counts_are_suppressed():
    result = suppress_small_counts(pd.Series([0, 4, 5, 9]))

    assert result.tolist() == ["< 5", "< 5", 5, 9]


def test_future_deadline_is_not_marked_overdue():
    future_date = pd.Timestamp.today().normalize() + pd.Timedelta(days=90)
    data = pd.DataFrame(
        {
            "processo_id": ["PROC-FUTURO"],
            "data_ajuizamento": [future_date],
            "fase_processual": ["Conhecimento"],
            "desfecho": ["Em andamento"],
            "tempo_tramitacao_dias": [1],
            "urgente": ["Sim"],
            "liminar": ["Sim"],
            "natureza": ["Medicamentos"],
            "tipo_demanda": ["Medicamento"],
        }
    )

    enriched = enrich_process_tracking(data)

    assert enriched.iloc[0]["data_limite_cumprimento"] > pd.Timestamp.today().normalize()
    assert enriched.iloc[0]["indicador_atraso"] == "Não"
