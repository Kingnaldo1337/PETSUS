from __future__ import annotations

import pandas as pd


class AccessScopeError(ValueError):
    """Conta autenticada sem um vínculo de dados utilizável."""


def restrict_data_for_user(base: pd.DataFrame, user) -> pd.DataFrame:
    """Aplica o escopo de autorização antes de filtros, KPIs e exportações."""
    if user.is_manager:
        return base.copy()
    if not user.patient_id:
        raise AccessScopeError(
            "Sua conta não está vinculada a um paciente. Procure a administração do sistema."
        )
    scoped = base[base["paciente_id"].astype(str) == str(user.patient_id)].copy()
    if scoped.empty:
        raise AccessScopeError(
            "Não foram encontrados dados para o paciente vinculado à sua conta."
        )
    return scoped
