"""Carga compartilhada e API compatível dos serviços do dashboard."""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd
import streamlit as st

from petsus.config import REQUIRED_COLUMNS, current_reference_date
from petsus.data.loader import DataLoadError, load_process_data
from petsus.data.demo import (
    GENERAL_HEALTH_STAGES, JUDICIAL_STAGES, MEDICINE_STAGES, SURGERY_STAGES,
    enrich_petsus_fields, enrich_process_tracking, extract_dcb,
    normalize_text, stable_choice, stable_int,
)


def _cpf_digits(value: object) -> str:
    if pd.isna(value):
        return ""
    if isinstance(value, int):
        return str(value).zfill(11)
    if isinstance(value, float) and value.is_integer():
        return str(int(value)).zfill(11)
    return re.sub(r"\D", "", str(value))

def _format_cpf(value: object) -> str:
    digits = _cpf_digits(value)
    if len(digits) != 11:
        return str(value)
    return f"{digits[:3]}.{digits[3:6]}.{digits[6:9]}-{digits[9:]}"

def _cpf_checksum_valid(digits: str) -> bool:
    """Usado só para evitar que um CPF fictício gerado coincida com um CPF real válido."""
    if len(digits) != 11 or len(set(digits)) == 1:
        return False
    nums = [int(x) for x in digits]
    total = sum(nums[i] * (10 - i) for i in range(9))
    d1 = (total * 10 % 11) % 10
    total = sum(nums[i] * (11 - i) for i in range(10))
    d2 = (total * 10 % 11) % 10
    return nums[9] == d1 and nums[10] == d2

def _attach_full_cpf(base: pd.DataFrame) -> pd.DataFrame:
    """Garante uma coluna `cpf` completa.

    Em produção, se a planilha já trouxer `cpf`, `cpf_completo` ou `cpf_paciente`,
    o valor real da fonte é usado. Na base fictícia atual, os dígitos ocultos não
    existem; por isso é criado um CPF de demonstração estável por paciente,
    preservando o prefixo e o sufixo visíveis e evitando CPFs válidos reais.
    """
    d = base.copy()
    for source in ("cpf", "cpf_completo", "cpf_paciente"):
        if source in d.columns:
            values = d[source].map(_cpf_digits)
            invalid = values.str.len().ne(11)
            if invalid.any():
                st.error(f"A coluna '{source}' possui CPF(s) incompleto(s). Corrija a fonte de dados antes de continuar.")
                st.stop()
            d["cpf"] = values.map(_format_cpf)
            d["cpf_origem"] = "Fonte de dados"
            return d

    if "cpf_mascarado" not in d.columns:
        st.error("A base precisa conter uma coluna de CPF completo (`cpf`) ou, para demonstração, `cpf_mascarado`.")
        st.stop()

    patient_rows = (
        d[["paciente_id", "cpf_mascarado"]]
        .drop_duplicates("paciente_id")
        .sort_values("paciente_id")
    )
    mapping: dict[str, str] = {}
    used: set[str] = set()
    for row in patient_rows.itertuples(index=False):
        patient_id = str(row.paciente_id)
        masked_digits = re.sub(r"\D", "", str(row.cpf_mascarado))
        if len(masked_digits) < 5:
            st.error(f"CPF mascarado inválido para o paciente {patient_id}.")
            st.stop()
        prefix, suffix = masked_digits[:3], masked_digits[-2:]
        pid_digits = re.sub(r"\D", "", patient_id)
        base_middle = int(pid_digits or "0") % 1_000_000

        # Usa o ID do paciente como semente. Se, por coincidência, resultar em um
        # CPF matematicamente válido, desloca a parte central para mantê-lo fictício.
        for offset in (0, 500_000, 600_000, 700_000, 800_000, 900_000, 400_000, 300_000, 200_000, 100_000):
            middle = (base_middle + offset) % 1_000_000
            candidate = f"{prefix}{middle:06d}{suffix}"
            if candidate not in used and not _cpf_checksum_valid(candidate):
                used.add(candidate)
                mapping[patient_id] = _format_cpf(candidate)
                break
        else:
            st.error(f"Não foi possível gerar um CPF de demonstração para {patient_id}.")
            st.stop()

    d["cpf"] = d["paciente_id"].astype(str).map(mapping)
    d["cpf_origem"] = "Demonstração"
    return d

def load_data(path: Path, modified_at: int, schema_version: str, reference_date: str | None = None) -> pd.DataFrame:
    """Inclui a referência civil na chave de cache, inclusive para chamadas legadas."""
    return _load_data_cached(path, modified_at, schema_version, reference_date or current_reference_date().isoformat())


@st.cache_data(show_spinner=False)
def _load_data_cached(path: Path, modified_at: int, schema_version: str, reference_date: str) -> pd.DataFrame:
    # schema_version participa da chave do cache. Ele deve mudar quando novas
    # colunas calculadas forem adicionadas, mesmo que o Excel não seja alterado.
    del schema_version
    try:
        base, invalid_dates = load_process_data(
            path, REQUIRED_COLUMNS, _attach_full_cpf,
            lambda data: enrich_petsus_fields(data, reference_date=reference_date)
        )
    except DataLoadError as exc:
        st.error(str(exc))
        st.stop()
    base["_search"] = (
        base[["paciente", "paciente_id", "cpf", "processo_id", "medicamento_dcb", "cid"]]
        .fillna("")
        .astype(str)
        .agg(" ".join, axis=1)
        .map(normalize_text)
    )
    return base
