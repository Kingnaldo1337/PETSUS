    # Dicionário de variáveis PetSUS adicionadas

Os campos abaixo compõem a análise de medicamentos do PetSUS. Como a base do projeto é fictícia, os valores incluídos no dashboard são sintéticos/demonstrativos.

| Variável | Significado no dashboard |
|---|---|
| `medicamento_petsus` | Identifica registros elegíveis para a camada de análise de medicamentos. |
| `medicamento_dcb` | Denominação Comum Brasileira / princípio ativo. |
| `cid` | CID relacionado à condição clínica. |
| `rename_incorporado` | Indica se o medicamento está incorporado à RENAME. |
| `componente_sus` | Componente de financiamento/assistência farmacêutica do SUS. |
| `grupo_sus` | Grupo de enquadramento associado ao componente. |
| `apresentacao_padronizada` | Apresentação do medicamento utilizada na análise. |
| `pcdt_aplicavel` | Indica existência/aplicabilidade de PCDT. |
| `pcdt_referencia` | Identifica o protocolo/diretriz de referência usado na demonstração. |
| `dose_prescrita` | Dose utilizada no esquema posológico. |
| `frequencia_administracao` | Frequência do esquema posológico. |
| `duracao_meses` | Duração estimada do tratamento. |
| `pmvg_referencia` | Campo legado: preço sintético por administração (valor anual dividido pelas administrações anuais). Não é cotação oficial PMVG da CMED. |
| `valor_anual_tratamento` | Custo anual estimado do tratamento. |
| `valor_causa_estimado` | Valor estimado da causa no cenário demonstrativo. |
| `competencia_petsus` | Justiça Federal ou Justiça Estadual, conforme simulação. |
| `reu_sugerido` | União, Estado, Município ou Compartilhada, conforme simulação. |
| `criterio_competencia` | Regra que justificou a competência simulada. |
| `acima_210_salarios_minimos` | Compara o custo anual simulado com 210 salários mínimos do ano de ajuizamento; não determina competência legal do caso. |
| `etapa_judicial` | Etapa atual da trilha judicial, independente do cumprimento material. |
| `percentual_judicial` | Progresso demonstrativo da trilha judicial. |
| `etapa_saude` | Etapa de cumprimento na rede de saúde para medicamento, cirurgia ou outro tratamento. |
| `percentual_saude` | Progresso demonstrativo do cumprimento assistencial. |
| `tipo_fluxo_saude` | Define se o fluxo operacional é de medicamento, cirurgia ou tratamento/serviço. |
| `decisao_urgencia` | Situação demonstrativa da tutela de urgência ou liminar. |
| `data_intimacao` | Data em que o responsável teria recebido formalmente a ordem. |
| `prazo_cumprimento_dias` | Prazo demonstrativo fixado para cumprimento. |
| `data_limite_cumprimento` | Data limite calculada a partir da intimação e do prazo. |
| `indicador_atraso` | Indica prazo vencido com cumprimento ainda pendente. |
| `mensagem_paciente` | Explicação simplificada e conjunta das duas trilhas. |
| `origem_informacao` | Origem do evento; nesta base, identifica a simulação PetSUS. |
| `encerramento_judicial` | Encerramento da trilha judicial, independente da assistência. |
| `encerramento_assistencial` | Encerramento do fornecimento ou procedimento, independente do processo. |

## Fontes funcionais

- CNJ — Referência sobre competência em processos de saúde: https://www.cnj.jus.br/ferramenta-publica-facilita-definicao-de-competencia-em-processos-na-saude/
- Planalto — Salário mínimo de 2026 (R$ 1.621,00): https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2025/decreto/d12797.htm

## Referência temporal e atualização

`data_referencia_calculo` é uma única data civil no fuso `America/Fortaleza`,
capturada para a consulta. Todos os prazos e tempos em aberto usam essa data.
O filtro de período seleciona **ajuizamentos**, não recria o estado histórico
dos processos no último dia selecionado.

`geracao_simulacao` e `ultima_atualizacao_dados` indicam a regeneração local da
camada fictícia. Não representam sincronização com tribunal ou serviço de saúde.
Nesta versão não há integração automática semanal ou mensal nem uma próxima
atualização oficial programada. A consulta é recalculada ao abrir o painel em
uma nova data de referência. A planilha permanece uma fonte estática.

## Definições dos indicadores

| Indicador/campo | Definição e denominador |
|---|---|
| Procedência | Número de desfechos `Procedente` / julgados de mérito (`Procedente`, `Parcialmente procedente`, `Improcedente`). Exclui pendentes e acordos; sem julgados, exibe N/A. |
| Procedência parcial | `Parcialmente procedente` / os mesmos julgados de mérito, separada da procedência integral. |
| Pendentes | Desfechos `Em andamento`, `Pendente` ou sem desfecho informado; não são derrotas judiciais. |
| Liminares concedidas | Processos com `liminar=Sim` / total de processos do recorte. Não é a taxa de deferimento dos pedidos. |
| Urgentes | Pedido de análise urgente simulado (`urgente=Sim`); não é uma classificação clínica de risco nem significa que uma liminar foi concedida. |
| `tempo_tramitacao_dias` | Dias corridos do ajuizamento até `data_desfecho` (julgamento de mérito, acordo ou extinção); nos pendentes, até `data_referencia_calculo`. Sua média mistura durações concluídas e tempo em aberto, conforme rótulo do painel. Recursos posteriores não prolongam esse indicador. |
| `tempo_decorrido_dias` | Dias corridos entre ajuizamento e referência para todos os registros. Não é prazo previsto para decisão. |
| `tempo_liminar_dias` | Dias entre ajuizamento e concessão simulada de tutela. Ausente quando não há concessão. |
| `indicador_atraso` | Sim apenas se a referência for posterior à data limite e o cumprimento assistencial não tiver sido concluído. |
| Custo estimado (`custo_estimado`) | Estimativa de custo da demanda na planilha. Não é despesa executada. |
| Valor anual (`valor_anual_tratamento`) | Estimativa demonstrativa de 12 meses de medicamento, independente da duração prevista. |
| Valor da causa (`valor_causa_estimado`) | Valor anual multiplicado por `min(duracao_meses,12)/12`, apenas na demonstração. Não é valor processual real. |
| PMVG de referência | Valor sintético por administração para o cenário; não é cotação oficial CMED. Médias entre fármacos/apresentações não são referência de compra. |
| `salario_minimo_ajuizamento` / `limite_210_sm_ajuizamento` | Salário mínimo do ano de ajuizamento e seu produto por 210. Anos ausentes da tabela ficam sem classificação, sem usar valor de outro ano. |

Os três valores de custo descrevem perspectivas diferentes da mesma demanda;
**não devem ser somados**. Percentuais de competência e de assistência
farmacêutica têm como denominador apenas os registros `medicamento_petsus=Sim`.
Percentuais das trilhas indicam posição na lista ilustrativa de etapas; não
medem probabilidade de êxito, tempo restante ou conclusão de todo o cuidado.

## Gestão da oferta e prevenção

| Campo | Significado |
|---|---|
| `causa_judicializacao` | Causa operacional simulada, compatível com a categoria da demanda. Não foi inferida de processo real. |
| `judicializacao_potencialmente_evitavel` | `Sim` quando o cenário descreve falha administrativa passível de revisão: comunicação, encaminhamento, estoque pontual, acesso ao serviço, regulação ou fluxo regular. `Não` significa evidência insuficiente nesta simulação. |
| `motivo_potencialmente_evitavel` | Explica a oportunidade administrativa ou a insuficiência de evidência; não garante que uma ação poderia ter sido evitada. |
| `disponibilidade_administrativa` | `Sim` apenas nos cenários com serviço disponível não acessado, falha de comunicação ou espera em fluxo regular. |
| `ente_responsavel` | Município, Estado, União ou Compartilhada no cenário. Requer validação do caso e das pactuações reais. |
| `ente_dispensacao_simulado` | Ente ilustrativo do fluxo administrativo do medicamento, distinto de competência judicial. |
| `componente_sus` / `grupo_sus` | Componente e grupo do cenário farmacêutico. Não substituem RENAME, PCDT ou pactuação vigente. Zero registros CBAF/CESAF é mostrado como zero, sem inventar medicamentos ausentes na planilha. |
| `data_movimentacao_saude` | Data simulada da etapa assistencial, não posterior à referência. |

O catálogo de demonstração corrige vínculos impossíveis entre item, natureza,
tipo de demanda, condição clínica, especialidade e CID. Exames não seguem a
trilha cirúrgica; materiais e terapias têm categorias próprias. Solicitações
sem urgência não recebem mensagens de decisão urgente. Sentença improcedente
não inicia cumprimento assistencial. A sentença e o atendimento permanecem
eventos distintos. A esfera judicial é somente Estadual ou Federal e coincide
com a competência simulada dos medicamentos classificados. Município identifica
um ente administrativo, não um ramo judicial. Desfechos vazios, ausentes ou
`Pendente` são normalizados para `Em andamento` antes das métricas.

Faixas etárias usam décadas até 110 a 119. A carga exige idades em anos completos
de 0 a 119; valores ausentes, negativos, fracionários ou fora desse intervalo
rejeitam o lote inteiro, antes da visualização.

## Fontes oficiais previstas e parâmetros históricos

- CNJ/DataJud: metadados e movimentos processuais, sujeitos a integração e validação: https://www.cnj.jus.br/sistemas/datajud/api-publica/
- Ministério da Saúde/RENAME: consulta de medicamentos e componentes: https://www.gov.br/saude/pt-br/composicao/sectics/rename
- Ministério da Saúde/PCDT: protocolos clínicos: https://www.gov.br/saude/pt-br/assuntos/pcdt
- Anvisa/CMED: preços oficiais e apresentações: https://www.gov.br/anvisa/pt-br/assuntos/medicamentos/cmed
- Salário mínimo 2024: R$ 1.412; Decreto 11.864/2023: https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2023/decreto/d11864.htm
- Salário mínimo 2025: R$ 1.518; Decreto 12.342/2024: https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2024/decreto/d12342.htm
- Salário mínimo 2026: R$ 1.621; Decreto 12.797/2025: https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2025/decreto/d12797.htm

Nenhuma dessas bases é consultada automaticamente pelo protótipo. Regras de
competência, réu sugerido, incorporação e componente são **simulações
acadêmicas simplificadas**, sem valor de decisão legal ou orientação de
prescrição. Uma versão operacional deve validar fonte, vigência, indicação,
apresentação, competência e responsabilidade com as equipes responsáveis.
