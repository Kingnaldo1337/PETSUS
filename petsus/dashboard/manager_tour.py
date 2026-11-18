"""Conteúdo dos tutoriais de cada página do gestor."""
from __future__ import annotations


PAGE_GUIDES = {
    "Visão Geral": (
        "Acompanhe os principais indicadores e a evolução dos processos no recorte selecionado.",
        ('.st-key-manager_panel_como_interpretar_os_resultados', 'Interprete os indicadores', 'Consulte as definições e os limites dos dados antes de comparar os resultados.'),
        ('.st-key-manager_panel_evolucao_mensal_dos_processos', 'Evolução mensal', 'O gráfico mostra a distribuição dos processos ao longo dos meses de ajuizamento.'),
    ),
    "Processos": (
        "Consulte todos os processos cadastrados, com requerente, município, assunto e andamento.",
        ('.st-key-process_list_search', 'Busque um processo', 'Digite o número, requerente, município, assunto ou andamento para localizar os registros.'),
        ('.st-key-process_list_states', 'Selecione o estado', 'Escolha uma ou mais UFs. Sem seleção, todos os estados são considerados.'),
        ('.st-key-process_list_municipalities', 'Selecione o município', 'As cidades disponíveis correspondem aos estados selecionados. Você pode selecionar mais de uma.'),
        ('[data-testid="stDataFrame"]', 'Confira a listagem', 'Cada linha apresenta um processo. Consulte a fase processual, o andamento judicial, a etapa na saúde e o desfecho.'),
    ),
    "Andamento": (
        "Acompanhe separadamente a tramitação judicial e o cumprimento pela rede de saúde.",
        ('.st-key-manager_panel_etapas_judiciais_no_recorte', 'Etapas judiciais', 'Veja a distribuição dos processos por etapa judicial no recorte selecionado.'),
        ('.st-key-manager_panel_cumprimento_na_rede_de_saude', 'Cumprimento na saúde', 'Confira as etapas da rede de saúde. Uma decisão favorável não confirma que o atendimento foi realizado.'),
        ('.st-key-tracking_process', 'Consulta individual', 'Selecione um processo para consultar a decisão, o prazo e a próxima ação registrada.'),
    ),
    "Demandas": (
        "Analise os tipos de demanda, fases processuais, liminares e urgência.",
        ('.st-key-manager_panel_demandas_por_tipo_e_fase_processual', 'Tipos e fases', 'Compare a distribuição das demandas por tipo e fase processual.'),
        ('.st-key-manager_panel_causas_da_judicializacao_e_oportunidades_de_gestao', 'Causas e oportunidades', 'Explore as causas registradas e as oportunidades de atuação administrativa.'),
    ),
    "Medicamentos": (
        "Explore as demandas de medicamentos, protocolos, dispensação administrativa e custos estimados.",
        ('.st-key-manager_panel_assistencia_farmaceutica_e_dispensacao_administrativa', 'Assistência farmacêutica', 'Consulte os componentes da assistência e a dispensação administrativa indicada.'),
        ('.st-key-manager_panel_classificacao_por_medicamento', 'Classificação dos medicamentos', 'Confira a classificação dos pedidos e as informações disponíveis na base.'),
        ('.st-key-manager_panel_estimativa_sintetica_de_preco_por_administracao', 'Preço estimado', 'As estimativas apoiam a análise e não comprovam valores pagos.'),
    ),
    "Competência": (
        "Responsabilidade administrativa e competência judicial são dimensões distintas. Esta página apoia a revisão dos registros.",
        ('.st-key-manager_panel_responsabilidade_por_processo', 'Responsabilidade por processo', 'Selecione um processo para conferir o ente indicado. A definição das partes exige avaliação jurídica.'),
        ('.st-key-manager_panel_competencia_e_incorporacao_a_rename', 'Competência e RENAME', 'Compare a competência indicada e a incorporação à lista RENAME.'),
    ),
    "Custos": (
        "Analise os custos estimados e sua distribuição. Eles não representam comprovação de gasto executado.",
        ('.st-key-manager_panel_evolucao_mensal_do_custo_estimado', 'Evolução dos custos', 'Observe a evolução mensal do custo estimado no recorte selecionado.'),
        ('.st-key-manager_panel_custo_tipico_e_dispersao_por_natureza', 'Custo típico e dispersão', 'Compare as medidas de custo e sua variação entre as naturezas de demanda.'),
    ),
    "Prevenção": (
        "Identifique causas recorrentes e oportunidades de resolução administrativa das demandas.",
        ('.st-key-manager_panel_oportunidades_de_prevencao_por_causa', 'Oportunidades por causa', 'Consulte as causas e as ações administrativas sugeridas para apoiar o planejamento.'),
        ('.st-key-manager_panel_fluxo_de_prevencao', 'Fluxo de prevenção', 'Use este fluxo como orientação para organizar a análise e os encaminhamentos.'),
    ),
    "Geografia": (
        "Explore a distribuição territorial dos processos por região, estado e município.",
        ('.st-key-manager_panel_municipios_com_dados_publicaveis', 'Distribuição municipal', 'Consulte os municípios com dados publicáveis. Grupos pequenos são protegidos.'),
        ('.st-key-manager_panel_tabela_geografica_protegida', 'Tabela geográfica', 'Confira os valores agregados disponíveis para os grupos do recorte.'),
    ),
    "Pacientes": (
        "Conheça o perfil demográfico e socioassistencial dos pacientes no recorte selecionado.",
        ('.st-key-manager_panel_idade_em_intervalos_de_10_anos', 'Faixas etárias', 'Os intervalos permitem comparar a distribuição por idade entre pacientes distintos.'),
        ('.st-key-manager_panel_perfil_socioassistencial', 'Perfil socioassistencial', 'Confira os indicadores de SUS exclusivo, deficiência, doença rara e renda.'),
        ('.st-key-manager_panel_distribuicao_do_custo_acumulado_por_paciente', 'Faixas de custo por paciente', 'A tabela agrupa pacientes por custo acumulado e protege grupos pequenos.'),
    ),
    "Gestão interna": (
        "Gerencie contas, revise acessos e consulte os eventos de auditoria.",
        ('[data-testid="stTabs"] [role="tablist"]', 'Escolha uma área de gestão', 'Use as abas para acessar as funções disponíveis de cadastro, revisão de acessos e auditoria.'),
        ('[data-testid="stTabs"] [role="tabpanel"]:not([hidden])', 'Revise antes de confirmar', 'Confira a conta selecionada e os dados da operação. Alterações de acesso exigem confirmação no formulário.'),
    ),
    "Ajuda e feedback": (
        "Encontre contatos, acompanhe relatos e consulte as definições e informações sobre os dados.",
        ('.st-key-patient_contacts', 'Contatos de apoio', 'Consulte os contatos disponíveis para suporte e orientação.'),
        ('[data-testid="stTabs"] [role="tablist"]', 'Seções de ajuda', 'Acesse os relatos recebidos, o glossário, as informações sobre os dados e a avaliação de uso.'),
        ('[data-testid="stTabs"] [role="tabpanel"]:not([hidden])', 'Relatos e acompanhamento', 'Consulte as solicitações na seção de relatos. Evite incluir CPF, senhas ou dados clínicos nas mensagens.'),
    ),
}


def manager_tour_steps(page: str) -> list[tuple[str, str, str]]:
    guide = PAGE_GUIDES.get(page)
    if guide is None:
        return []
    description, *specific = guide
    steps = [(".st-key-patient_header", page, description)]
    if page not in {"Processos", "Gestão interna", "Ajuda e feedback"}:
        steps.extend([
            ('.st-key-filter_uf', 'Filtre por estado', 'Selecione uma ou mais UFs para refinar os indicadores. Sem seleção, todos os estados são considerados.'),
            ('.st-key-filter_municipio', 'Filtre por município', 'Selecione as cidades desejadas. A lista acompanha os estados escolhidos.'),
            ('.st-key-manager_filterbar', 'Defina o período', 'Este filtro usa a data de ajuizamento dos processos. A contagem mostra o recorte atual.'),
            ('.metric-card', 'Leia os indicadores', 'Os cartões resumem o recorte. Use o ícone de interrogação para consultar a definição de cada indicador.'),
        ])
    steps.extend(specific)
    steps.append(('.st-key-support_chat_launcher', 'Tire dúvidas sobre o painel', 'O assistente explica como usar a plataforma. Não envie CPF, senhas ou dados de saúde.'))
    return steps
