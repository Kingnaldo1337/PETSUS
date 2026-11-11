"""Dimensionamento automático nativo das colunas do Streamlit."""
from __future__ import annotations

import pandas as pd
import streamlit as st


def compact_column_config(frame: pd.DataFrame) -> dict:
    """Deixa o Streamlit calcular a largura a partir do conteúdo das células."""
    return {
        column: st.column_config.Column(
            str(column), width=None,
            help=str(column),
        )
        for column in frame
    }
