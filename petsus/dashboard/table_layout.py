"""Larguras de tabela proporcionais ao conteúdo exibido."""
from __future__ import annotations

import pandas as pd
import streamlit as st


def compact_column_width(values: pd.Series, label: str, *, money: bool = False) -> int:
    """Reserva espaço para valores curtos sem alargar por cabeçalhos extensos."""
    numeric = pd.api.types.is_numeric_dtype(values)
    if money and numeric:
        lengths = values.dropna().map(lambda value: len(f"R$ {value:,.2f}"))
    else:
        lengths = values.dropna().astype(str).str.len()
    content = int(lengths.max()) if not lengths.empty else 0
    header = min(len(label), 16 if numeric else 28)
    return min(170 if money else 145 if numeric else 300,
               max(85, max(content, header) * 8 + 24))


def compact_column_config(frame: pd.DataFrame) -> dict:
    return {
        column: st.column_config.Column(
            str(column), width=compact_column_width(frame[column], str(column)),
            help=str(column),
        )
        for column in frame
    }
