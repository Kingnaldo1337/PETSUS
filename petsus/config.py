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
JUDSAUDE_FAQ_URL = (
    "https://www.cnj.jus.br/tecnologia-da-informacao-e-comunicacao/"
    "justica-4-0/conheca-o-conecta/judsaude/perguntas-frequentes/"
)

