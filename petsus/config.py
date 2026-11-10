from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

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

# Atualize após confirmação do próximo ciclo pelo curador da base.
PROXIMA_ATUALIZACAO = "A definir"

# URL do formulário de feedback (substitua pelo link real: Google Forms, Typeform etc.)
FEEDBACK_URL = "mailto:petsus@saude.gov.br?subject=Feedback%20PETSUS"

APP_TIMEZONE = "America/Fortaleza"
# Decretos 11.864/2023, 12.342/2024 e 12.797/2025. Anos fora da
# tabela exigem atualização da fonte; nunca reutilizamos o valor de outro ano.
SALARIO_MINIMO_POR_ANO = {2024: 1412.0, 2025: 1518.0, 2026: 1621.0}


def current_reference_date():
    """Data civil única para a consulta, independente do fuso do servidor."""
    return datetime.now(ZoneInfo(APP_TIMEZONE)).date()


def salario_minimo_no_ano(year: int) -> float | None:
    return SALARIO_MINIMO_POR_ANO.get(int(year))
