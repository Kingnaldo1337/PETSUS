from __future__ import annotations

from collections.abc import Callable
from math import isfinite
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
    """Valida o lote completo antes de preparar qualquer registro.

    Nenhuma linha é descartada nem custo ausente convertido em zero. A tupla
    mantém o contrato da interface: o segundo valor é zero em cargas válidas;
    um lote inválido gera DataLoadError, inclusive quando há datas inválidas.
    """
    if not path.exists():
        raise DataLoadError(f"Arquivo de dados não encontrado: {path}")
    try:
        base = pd.read_excel(path, sheet_name="base_processos")
    except ValueError as exc:
        if "Worksheet named" in str(exc) or "base_processos" in str(exc):
            message = "A aba 'base_processos' não foi encontrada no Excel."
        else:
            message = "Não foi possível interpretar o arquivo Excel."
        raise DataLoadError(message + " Verifique o arquivo e use a versão atualizada da planilha.") from exc
    except Exception as exc:
        # Inclui arquivo bloqueado, removido durante a leitura, ZIP/XLSX
        # corrompido e falha do leitor. A interface não recebe um traceback.
        raise DataLoadError(
            "Não foi possível ler a planilha. Verifique se o arquivo é um Excel válido, "
            "está acessível e não está bloqueado por outro programa."
        ) from exc

    missing = sorted(required_columns - set(base.columns))
    if missing:
        raise DataLoadError(
            "A aba 'base_processos' não possui todas as colunas obrigatórias: "
            + ", ".join(missing)
        )

    if base.empty:
        raise DataLoadError("A aba 'base_processos' está vazia. Nenhum registro foi carregado.")
    base = base.copy(deep=True)
    problems = []
    for column in ("processo_id", "paciente_id"):
        identifiers = base[column].astype("string").str.strip()
        invalid = identifiers.isna() | identifiers.eq("")
        if invalid.any():
            problems.append(f"{int(invalid.sum())} registro(s) com {column} ausente ou vazio")
        base[column] = identifiers
    duplicate_ids = base["processo_id"].notna() & base["processo_id"].ne("") & base["processo_id"].duplicated(keep=False)
    if duplicate_ids.any():
        problems.append(f"{int(duplicate_ids.sum())} registro(s) com processo_id duplicado")
    base["data_ajuizamento"] = pd.to_datetime(base["data_ajuizamento"], errors="coerce")
    invalid_dates = int(base["data_ajuizamento"].isna().sum())
    if invalid_dates:
        problems.append(f"{invalid_dates} registro(s) com data_ajuizamento inválida ou ausente")

    costs = pd.to_numeric(base["custo_estimado"], errors="coerce")
    invalid_costs = ~costs.map(lambda value: pd.notna(value) and isfinite(value) and value >= 0)
    if invalid_costs.any():
        problems.append(f"{int(invalid_costs.sum())} registro(s) com custo_estimado inválido, ausente ou negativo")
    base["custo_estimado"] = costs
    ages = pd.to_numeric(base["idade"], errors="coerce")
    invalid_ages = ~ages.map(lambda value: pd.notna(value) and isfinite(value) and 0 <= value <= 119 and value == int(value))
    if invalid_ages.any():
        problems.append(f"{int(invalid_ages.sum())} registro(s) com idade inválida (use anos completos de 0 a 119)")
    base["idade"] = ages
    for column in ("liminar", "urgente", "sus_exclusivo", "pcd", "doenca_rara"):
        if column in base.columns:
            values = base[column].astype("string").str.strip()
            invalid = ~values.isin(["Sim", "Não"])
            if invalid.any():
                problems.append(f"{int(invalid.sum())} registro(s) com {column} diferente de Sim/Não")
            base[column] = values
    if problems:
        raise DataLoadError("Lote rejeitado: " + "; ".join(problems) + ". Corrija a fonte antes de carregar novamente.")

    for column in ("tempo_tramitacao_dias", "tempo_liminar_dias"):
        base[column] = pd.to_numeric(base[column], errors="coerce")
    base["ano_mes"] = base["data_ajuizamento"].dt.to_period("M").astype(str)
    try:
        prepared = attach_cpf(base)
        prepared = enrich(prepared)
    except ValueError as exc:
        raise DataLoadError(f"A preparação dos dados foi interrompida: {exc} Corrija a fonte e tente novamente.") from exc
    return prepared, 0
