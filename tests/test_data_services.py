from datetime import date

import pandas as pd

from petsus.access import AccessScopeError, restrict_data_for_user
from petsus.auth.models import AuthUser, ROLE_MANAGER, ROLE_USER
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
