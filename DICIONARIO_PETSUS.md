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
| `pmvg_referencia` | PMVG de referência utilizado no cálculo demonstrativo. |
| `valor_anual_tratamento` | Custo anual estimado do tratamento. |
| `valor_causa_estimado` | Valor estimado da causa no cenário demonstrativo. |
| `competencia_petsus` | Justiça Federal ou Justiça Estadual, conforme simulação. |
| `reu_sugerido` | União, Estado ou Município, conforme simulação. |
| `criterio_competencia` | Regra que justificou a competência simulada. |
| `acima_210_salarios_minimos` | Indica se o custo anual alcança o parâmetro de 210 salários mínimos usado no Tema 1234 para medicamentos não incorporados. |
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
