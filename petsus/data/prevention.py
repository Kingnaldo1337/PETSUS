"""Critérios de triagem administrativa; não representam resolução comprovada."""
from __future__ import annotations

PREVENTION_ACTIONS = {
    "Serviço disponível, mas não acessado": "Facilitar agendamento, transporte e orientação de acesso.",
    "Aguardando fluxo regular": "Informar o prazo e revisar a oportunidade do atendimento administrativo.",
    "Falha de comunicação": "Orientar o usuário e confirmar que recebeu a informação sobre acesso.",
    "Demora administrativa": "Identificar a etapa pendente, o responsável e o prazo de resposta administrativa.",
    "Falta pontual de medicamento": "Revisar estoque e reposição antes de interromper o tratamento.",
    "Demora na regulação": "Revisar fila, prioridade e prazo do fluxo administrativo.",
    "Problema de regulação": "Conferir a solicitação na regulação e corrigir pendências de acesso.",
    "Falta de encaminhamento adequado": "Corrigir o encaminhamento e acompanhar sua aceitação.",
}
