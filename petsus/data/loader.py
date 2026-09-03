from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pandas as pd


class DataLoadError(ValueError):
    pass


def load_process_data(
    path: Path,
    required_columns: set[str],
    attach_cpf: Callable[[pd.DataFrame], pd.DataFrame],
    enrich: Callable[[pd.DataFrame], pd.DataFrame],
) -> tuple[pd.DataFrame, int]:
    """Lê e prepara a fonte; a camada Streamlit decide como exibir erros."""
    if not path.exists():
        raise DataLoadError(f"Arquivo de dados não encontrado: {path}")
    try:
        base = pd.read_excel(path, sheet_name="base_processos")
    except ValueError as exc:
        raise DataLoadError(
            "A aba 'base_processos' não foi encontrada no Excel. "
            "Use a versão atualizada do arquivo de dados."
        ) from exc

    missing = sorted(required_columns - set(base.columns))
    if missing:
        raise DataLoadError(
            "A aba 'base_processos' não possui todas as colunas obrigatórias: "
            + ", ".join(missing)
        )

    base = attach_cpf(base)
    base["data_ajuizamento"] = pd.to_datetime(base["data_ajuizamento"], errors="coerce")
    invalid_dates = int(base["data_ajuizamento"].isna().sum())
    if invalid_dates == len(base):
        raise DataLoadError("Nenhuma data válida foi encontrada na coluna 'data_ajuizamento'.")
    if invalid_dates:
        base = base.dropna(subset=["data_ajuizamento"]).copy()

    base["custo_estimado"] = pd.to_numeric(base["custo_estimado"], errors="coerce").fillna(0)
    for column in ("idade", "tempo_tramitacao_dias", "tempo_liminar_dias"):
        base[column] = pd.to_numeric(base[column], errors="coerce")
    base["ano_mes"] = base["data_ajuizamento"].dt.to_period("M").astype(str)
    return enrich(base), invalid_dates
