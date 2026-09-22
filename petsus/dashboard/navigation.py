from __future__ import annotations

MANAGER_PAGES = (
    "Visão Geral", "Andamento", "Demandas", "Medicamentos", "Competência",
    "Custos", "Geografia", "Pacientes", "Base de Dados", "Gestão interna",
)
USER_PAGE_MAP = {
    "Visão Geral": "Visão Geral",
    "Andamento dos Processos": "Andamento",
    "Demandas": "Demandas",
    "Medicamentos": "Medicamentos",
    "Competência": "Competência",
    "Custos": "Custos",
    "Meu Perfil": "Pacientes",
    "Meus Processos": "Base de Dados",
}

PAGE_SUBTITLES = {
    "Visão Geral": "Indicadores executivos, evolução mensal e principais recortes.",
    "Andamento": "Andamento judicial e cumprimento na saúde acompanhados separadamente.",
    "Demandas": "Análise de tipos de demanda, fase processual, liminares e urgência.",
    "Medicamentos": "Incorporação à RENAME, DCB, componente SUS, PCDT, PMVG e esquema posológico.",
    "Competência": "Competência judicial, réu sugerido e critério de custo anual usados pelo PetSUS.",
    "Custos": "Custos totais, ticket médio, medicamentos/insumos e especialidades mais caras.",
    "Geografia": "Distribuição por região, UF e município.",
    "Pacientes": "Perfil dos pacientes e busca individual.",
    "Base de Dados": "Tabela detalhada, exportação e conferência dos registros filtrados.",
    "Gestão interna": "Cadastro de gestores e manutenção individual de contas por CPF.",
}


def navigation_for(is_manager: bool) -> tuple[list[str], dict[str, str]]:
    if is_manager:
        labels = list(MANAGER_PAGES)
        return labels, {label: label for label in labels}
    return list(USER_PAGE_MAP), dict(USER_PAGE_MAP)


def subtitle_for(page: str, is_manager: bool) -> str:
    if not is_manager and page == "Pacientes":
        return "Seu perfil e os processos vinculados à sua conta."
    if not is_manager and page == "Base de Dados":
        return "Seus processos detalhados e exportação dos seus próprios registros."
    return PAGE_SUBTITLES[page]
