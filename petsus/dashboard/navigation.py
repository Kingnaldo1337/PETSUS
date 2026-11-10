from __future__ import annotations

MANAGER_PAGES = (
    "Visão Geral", "Andamento", "Demandas", "Medicamentos", "Competência",
    "Custos", "Geografia", "Pacientes", "Base de Dados", "Gestão interna",
)
USER_PAGE_MAP = {
    "Visão Geral": "Visão Geral",
    "Meu Andamento": "Andamento",
    "Meus Documentos": "Base de Dados",
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
    if not is_manager:
        if page == "Visão Geral":
            return "Resumo do acompanhamento dos seus processos."
        if page == "Meu Andamento" or page == "Andamento":
            return "Acompanhamento detalhado do andamento judicial e do cumprimento na saúde."
        if page == "Meus Documentos" or page == "Base de Dados":
            return "Seus processos detalhados, relatório em PDF e exportação dos seus registros."
    return PAGE_SUBTITLES.get(page, "")
