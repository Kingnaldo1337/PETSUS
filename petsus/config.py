from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = PROJECT_ROOT / "dados_dashboard_saude.xlsx"
DATABASE_FILE = PROJECT_ROOT / "usuarios.db"

REQUIRED_COLUMNS = {
    "processo_id", "data_ajuizamento", "paciente_id", "paciente",
    "sexo", "idade", "faixa_etaria", "municipio", "uf", "regiao", "latitude",
    "longitude", "condicao_clinica", "sus_exclusivo", "renda_familiar", "pcd",
    "doenca_rara", "natureza", "tipo_demanda", "item_demandado", "especialidade",
    "esfera", "fase_processual", "desfecho", "liminar", "urgente",
    "tempo_tramitacao_dias", "tempo_liminar_dias", "custo_estimado",
}

SALARIO_MINIMO_2026 = 1621.0
LIMITE_210_SM_2026 = 210 * SALARIO_MINIMO_2026

# ---------------------------------------------------------------------------
# Governança de Dados — Eixo 6
# ---------------------------------------------------------------------------
# Data de corte usada nos cálculos de prazos e indicadores de atraso.
# Ajuste quando a base for atualizada para uma nova extração real.
DATA_CORTE_CALCULOS = "2025-12-31"

# Descrição do próximo ciclo de atualização previsto da base de dados.
PROXIMA_ATUALIZACAO = "Janeiro / 2026"

# URL do formulário de feedback (substitua pelo link real: Google Forms, Typeform etc.)
FEEDBACK_URL = "mailto:petsus@saude.gov.br?subject=Feedback%20PETSUS"
