from __future__ import annotations

import pandas as pd


def percentage(part: float, total: float) -> float:
    return (part / total * 100) if total else 0.0


def calculate_kpis(df: pd.DataFrame) -> dict[str, float | int | None]:
    """Procedência usa somente os julgados de mérito; parcial é separada.

    Tempo: ajuizamento até julgamento/acordo/extinção; nos casos em andamento,
    até a data de referência. Liminar: processos com tutela concedida / total.
    """
    total = len(df)
    outcomes = df["desfecho"].astype("string").fillna("").str.strip().str.casefold()
    judged = outcomes.isin(["procedente", "parcialmente procedente", "improcedente"])
    denominator = int(judged.sum())
    return {
        "total": total,
        "pacientes": df["paciente_id"].nunique(),
        "custo": df["custo_estimado"].sum(),
        "ticket": df["custo_estimado"].mean() if total else 0,
        "tempo": df["tempo_tramitacao_dias"].mean() if total else None,
        "liminar": percentage((df["liminar"] == "Sim").sum(), total),
        "urgentes": int((df["urgente"] == "Sim").sum()),
        "procedencia": percentage(int(outcomes.eq("procedente").sum()), denominator) if denominator else None,
        "procedencia_parcial": percentage(int(outcomes.eq("parcialmente procedente").sum()), denominator) if denominator else None,
        "julgados": denominator,
        "pendentes": int(outcomes.isin(["em andamento", "pendente", ""]).sum()),
        "acordos": int(outcomes.eq("acordo").sum()),
        "idade_media": df.drop_duplicates("paciente_id")["idade"].mean(),
        "municipios": df["municipio"].nunique(),
    }
