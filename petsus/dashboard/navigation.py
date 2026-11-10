from __future__ import annotations

import re
import unicodedata

MANAGER_PAGES = (
    "Visão Geral", "Andamento", "Demandas", "Medicamentos", "Competência",
    "Custos", "Prevenção", "Geografia", "Pacientes", "Base de Dados", "Gestão interna", "Ajuda e feedback",
)
USER_PAGE_MAP = {
    "Meu acompanhamento": "Meu acompanhamento",
    "Meus processos": "Meus processos",
    "Meus documentos": "Meus documentos",
    "Ajuda e contato": "Ajuda e feedback",
}

PAGE_ICONS = {
    "Visão Geral": "chart", "Andamento": "clock", "Demandas": "document",
    "Medicamentos": "medical", "Competência": "scales", "Custos": "wallet",
    "Prevenção": "check", "Geografia": "location", "Pacientes": "users",
    "Base de Dados": "document", "Gestão interna": "lock", "Ajuda e feedback": "chat",
    "Meu acompanhamento": "clock", "Meus processos": "document",
    "Meus documentos": "download", "Ajuda e contato": "chat",
}

MATERIAL_ICONS = {
    "chart": "dashboard", "clock": "pending_actions", "document": "description",
    "medical": "medication", "scales": "balance", "wallet": "payments",
    "check": "verified_user", "location": "location_on", "users": "groups",
    "lock": "admin_panel_settings", "chat": "help_outline", "download": "download",
}


def navigation_key(page: str) -> str:
    normalized = unicodedata.normalize("NFKD", page).encode("ascii", "ignore").decode("ascii").lower()
    return "nav_" + re.sub(r"[^a-z0-9]+", "_", normalized).strip("_")

PAGE_SUBTITLES = {
    "Visão Geral": "Indicadores executivos, evolução mensal e principais recortes.",
    "Andamento": "Andamento judicial e cumprimento na saúde acompanhados separadamente.",
    "Demandas": "Análise de tipos de demanda, fase processual, liminares e urgência.",
    "Medicamentos": "Assistência farmacêutica, protocolos e custos dos pedidos.",
    "Competência": "Competência judicial, réu sugerido e critério de custo anual usados pelo PetSUS.",
    "Custos": "Custos totais, ticket médio, medicamentos/insumos e especialidades mais caras.",
    "Geografia": "Distribuição por região, UF e município.",
    "Pacientes": "Perfil demográfico e socioassistencial dos pacientes, com proteção de grupos pequenos.",
    "Base de Dados": "Tabela agregada, exportação protegida e conferência dos grupos filtrados.",
    "Gestão interna": "Cadastro de gestores, revisão de acessos e trilha de auditoria.",
    "Prevenção": "Causas recorrentes e oportunidades de resolução administrativa.",
    "Ajuda e feedback": "Ajuda, relato de erros, avaliação de uso e informações sobre os dados.",
    "Meu acompanhamento": "Veja a situação do seu processo, os próximos passos e quem procurar.",
    "Meus processos": "Consulte os processos vinculados à sua conta.",
    "Meus documentos": "Baixe o resumo de acompanhamento de cada processo.",
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
