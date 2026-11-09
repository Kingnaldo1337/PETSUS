from __future__ import annotations

import pandas as pd


def percentage(part: float, total: float) -> float:
    return (part / total * 100) if total else 0.0


def calculate_kpis(df: pd.DataFrame) -> dict[str, float]:
    total = len(df)
    desfechos = df["desfecho"].astype("string").str.strip().str.casefold()
    desfecho_definido = desfechos.notna() & desfechos.ne("") & ~desfechos.isin(
        {"em andamento", "sem resolução de mérito"}
    )
    procedente = desfechos.isin({"procedente", "parcialmente procedente"})
    return {
        "total": total,
        "pacientes": df["paciente_id"].nunique(),
        "custo": df["custo_estimado"].sum(),
        "ticket": df["custo_estimado"].mean() if total else 0,
        "tempo": df["tempo_tramitacao_dias"].mean() if total else 0,
        "liminar": percentage((df["liminar"] == "Sim").sum(), total),
        "urgentes": int((df["urgente"] == "Sim").sum()),
        "procedencia": percentage(
            (procedente & desfecho_definido).sum(), desfecho_definido.sum()
        ),
        "idade_media": df.drop_duplicates("paciente_id")["idade"].mean(),
        "municipios": df["municipio"].nunique(),
    }
