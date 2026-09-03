from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

import pandas as pd


@dataclass(frozen=True)
class DashboardFilters:
    """Valores escolhidos na interface, sem dependência do Streamlit."""

    start_date: date | None = None
    end_date: date | None = None
    search: str = ""
    patient_ids: tuple[str, ...] = ()
    fields: dict[str, tuple[str, ...]] = field(default_factory=dict)


def apply_filters(df: pd.DataFrame, filters: DashboardFilters) -> pd.DataFrame:
    filtered = df.copy()
    if filters.start_date is not None:
        filtered = filtered[filtered["data_ajuizamento"].dt.date >= filters.start_date]
    if filters.end_date is not None:
        filtered = filtered[filtered["data_ajuizamento"].dt.date <= filters.end_date]
    if filters.search:
        filtered = filtered[
            filtered["_search"].str.contains(filters.search, regex=False, na=False)
        ]
    if filters.patient_ids:
        filtered = filtered[
            filtered["paciente_id"].astype(str).isin(filters.patient_ids)
        ]
    for column, selected in filters.fields.items():
        if selected:
            filtered = filtered[filtered[column].astype(str).isin(selected)]
    return filtered

