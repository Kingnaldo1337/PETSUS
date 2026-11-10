"""Cenários adicionais exclusivos da sessão do paciente de teste."""
from __future__ import annotations

import pandas as pd

from petsus.data.demo import enrich_petsus_fields


def add_test_processes(scoped_base: pd.DataFrame, reference_date) -> pd.DataFrame:
    """Usa apenas o cadastro já autorizado; não busca registros de outros pacientes."""
    if scoped_base.empty:
        return scoped_base.copy()
    reference = pd.Timestamp(reference_date).normalize()
    scenarios = (
        ("Medicamentos", "Medicamento", "Losartana 50 mg", "Hipertensão", 12, "Em andamento", "Não", "Não"),
        ("Medicamentos", "Medicamento", "Insulina glargina", "Diabetes", 35, "Em andamento", "Sim", "Sim"),
        ("Cirurgias", "Cirurgia", "Cirurgia oftalmológica de catarata", "Doenças oftalmológicas", 100, "Procedente", "Não", "Não"),
        ("Tratamentos", "Tratamento", "Fisioterapia", "Doenças osteomusculares", 60, "Parcialmente procedente", "Não", "Não"),
        ("Medicamentos", "Medicamento", "Adalimumabe", "Autoimune", 150, "Improcedente", "Não", "Não"),
        ("Cirurgias", "Cirurgia", "Cirurgia ortopédica: artroplastia de quadril", "Doenças osteomusculares", 3, "Em andamento", "Sim", "Sim"),
    )
    rows = []
    for number, (nature, demand, item, condition, days, outcome, urgent, injunction) in enumerate(scenarios, 1):
        row = scoped_base.iloc[0].copy()
        row["processo_id"] = f"TESTE-{row['paciente_id']}-{number:03d}"
        row["natureza"], row["tipo_demanda"], row["item_demandado"] = nature, demand, item
        row["condicao_clinica"] = condition
        row["data_ajuizamento"] = reference - pd.Timedelta(days=days)
        row["desfecho"], row["urgente"], row["liminar"] = outcome, urgent, injunction
        row["tempo_tramitacao_dias"], row["tempo_liminar_dias"] = 30, 2
        row["custo_estimado"] = [240, 3600, 5200, 1800, 24000, 18000][number - 1]
        rows.append(row)
    examples = enrich_petsus_fields(pd.DataFrame(rows).reset_index(drop=True), reference)
    existing = scoped_base[~scoped_base["processo_id"].astype(str).isin(examples["processo_id"].astype(str))]
    result = pd.concat([existing, examples], ignore_index=True)
    result.attrs.update(scoped_base.attrs)
    return result
