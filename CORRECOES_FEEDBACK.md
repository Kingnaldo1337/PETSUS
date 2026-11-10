# Correções do feedback — versão 2.0.0, 09/11/2026

## Refinamento visual do perfil do paciente

O portal recebeu uma composição inspirada na imagem da última página do PDF:
menu azul-marinho com identificação do paciente, faixa de privacidade e datas,
cartões de Justiça e saúde, próximo passo em destaque e cartões de movimentação
e ajuda. Meus processos e Meus documentos seguem a mesma identidade visual.
As grades se reorganizam conforme o espaço disponível, sem alturas fixas nos
cartões. Os controles de tamanho de texto e contraste ficam junto ao título.

Os botões Ver contatos e Relatar problema abrem Ajuda e contato; o relato já
recebe o processo selecionado. O seletor diferencia pedidos repetidos pelo
número do processo. Download de PDF, leitura do resumo, trilhas, isolamento de
dados e o botão Menu foram preservados. O layout tem regras para telas pequenas,
texto ampliado e alto contraste. A conferência visual no navegador continua
dependente de um navegador conectado à sessão.

Validação após o refinamento: 67 testes aprovados, incluindo os atalhos de ajuda
e os controles de acessibilidade do cabeçalho.

## Atendimento aos pontos do feedback

### Identidade visual compartilhada com o gestor

O perfil de gestor utiliza os mesmos componentes de cabeçalho, identificação,
menu e acessibilidade do paciente. Os indicadores têm cartões claros com ícones
vetoriais, e os gráficos e tabelas ficam em painéis com bordas, espaçamento e
tipografia padronizados. O período e a contagem ficam numa barra própria, com
reorganização em telas estreitas. O gestor mantém as páginas, filtros, cálculos,
regras de privacidade e exportações. O cabeçalho identifica o ambiente de gestão
e informa as datas de atualização e referência dos cálculos.

O PDF foi usado como lista de problemas e sugestões do produto. A base continua
sendo uma demonstração acadêmica, sem consulta a dados oficiais ou envio de
mensagens a usuários reais durante a implementação.

| Ponto do feedback | Implementação |
| --- | --- |
| Perfil do paciente reaproveitava a análise de gestão | Portal com Meu acompanhamento, Meus processos, Meus documentos e Ajuda e contato. Sem indicadores executivos, gráficos populacionais ou filtros demográficos. |
| Onde está meu pedido, próximo passo e responsável | Duas situações separadas (Justiça e saúde), ação seguinte, responsável, prazo, última movimentação e orientação quando o prazo vence. Trilhas em texto e PDF preservadas. |
| Contato e linguagem técnica | Glossário, diretório oficial das Defensorias e campos configuráveis para o contato específico da equipe e do representante. |
| Data de atualização e referência ambíguas | Data de alteração do arquivo e data de referência dos cálculos visíveis em todas as páginas autenticadas. Período filtra ajuizamento e não simula situação histórica. PDF diferencia geração da simulação e referência. |
| Procedência somava êxito parcial e incluía pendentes | Procedente dividido por julgados de mérito. Parcialmente procedente em indicador separado; pendentes, acordos e ausência de julgamento explícitos. Sem julgados: Não se aplica. |
| Custos semelhantes e denominadores omitidos | Definições nos cartões e nas páginas: custo processual, tratamento para 12 meses e valor da causa não devem ser somados. Percentuais de competência declaram o subconjunto de medicamentos. |
| PMVG médio entre apresentações diferentes | Média global removida; referências por princípio ativo e apresentação. |
| Uso do limite de 2026 em processos anteriores | Salário mínimo do ano de ajuizamento (2024–2026) e limite correspondente. Ano não cadastrado exige revisão, sem reaproveitar valor de outro ano. |
| Inconsistências da base fictícia | Catálogo de cenários coerentes com item, categoria, condição e especialidade; idade pediátrica, urgência, desfecho, decisão, intimação e cronologia verificados. Regras em `petsus/data/demo.py`, separadas da interface. |
| Roscas, cores e rótulos | Distribuições por barras com quantidades e percentuais; paleta semântica fixa, margens e quebra de rótulos. Evolução mensal sem rótulos sobrepostos. |
| Boxplot e categorias dominantes | Mediana e quartis em tabela com explicação. Categoria dominante destacada quando impede a comparação das demais. Faixas etárias com dez anos. |
| Nomes técnicos e tabelas truncadas | Rótulos humanos, configuração de largura e rolagem de tabelas; valores monetários completos disponíveis na tabela e nas exportações. |
| CPF exposto e reidentificação | CPF mascarado em consultas operacionais; análises e exportações agregadas. Supressão por menos de cinco pacientes distintos, incluindo supressão complementar. Rankings nominais substituídos por faixas de custo. |
| Contas frágeis e falta de auditoria | Troca de senha temporária obrigatória, MFA real por e-mail quando configurado, limitação/expiração dos códigos, invalidação de sessões, revisão de contas e revogação, auditoria de acesso e administração. |
| Demandas redundantes e causas da judicialização | Uma matriz por tipo/fase e quadro de causas administrativas. Definições de liminar, urgência e desfecho. |
| Assistência básica/especializada e responsabilidade | Quadro de componentes, quantidades e percentuais, com dispensação administrativa simulada separada da competência judicial. Indicadores Município, Estado, União e Compartilhada. |
| Prevenção de judicialização | Página de causas recorrentes, proporção potencialmente evitável e oportunidades de ação administrativa. Classificação identificada como hipótese sintética. |
| Fontes previstas e transparência | Links DataJud/CNJ, RENAME e CMED/Anvisa, versão e histórico na ajuda e no dicionário. Nenhuma integração inexistente é apresentada como ativa. |
| Atualização e conferência | Recarga detecta mudança na planilha; periodicidade de revisão configurável e próxima revisão planejada explícita. Registro de conferência humana vinculado ao hash do arquivo. |
| Erros e feedback após lançamento | Formulário persistente, protocolo, status e resposta do gestor; paciente acompanha apenas seus relatos. |
| Métricas de uso e avaliação SUS | Visitas por sessão/perfil/página sem identificação pessoal; questionário de dez itens com escore SUS, identificado como adaptação não validada. |
| Acessibilidade visual e sonora | Texto ampliado, alto contraste, foco de teclado, respeito a movimento reduzido e leitura voluntária do resumo em português, com opção de parar. |
| Barra de administração do Streamlit | Modo viewer e controles de infraestrutura ocultos na interface. |

## Configuração e operação

Execute com `python -m streamlit run app.py`. Para validar, instale `pytest` no
ambiente de desenvolvimento e execute `python -m pytest -q`.

Validação desta entrega: 67 testes aprovados, incluindo navegação de todas as
páginas de gestor/paciente, isolamento, relato de erro, ausência de vínculo,
autenticação, MFA, métricas e carga. A planilha original de 24.857 registros
passou pelas validações. PDFs de medicamento e cirurgia foram renderizados e
conferidos visualmente, com duas páginas e sem conteúdo fora da página. A revisão
visual da interface em desktop/mobile e a reprodução de áudio permanecem
pendentes: não havia navegador disponível nas ferramentas da sessão.

O exemplo de configuração está em `.streamlit/secrets.example.toml`. Contatos
específicos precisam ser preenchidos com os canais reais da equipe; não há
números ou endereços fictícios apresentados como atendimento real. Enquanto não
forem cadastrados, a interface mostra essa ausência e o diretório das Defensorias.

Configure SMTP para cadastro, recuperação e segundo fator. `PETSUS_REQUIRE_MFA=true`
impede acesso sem segundo fator e sem infraestrutura de envio funcional.
Credenciais SMTP não devem ser versionadas. Novos gestores e senhas redefinidas
pela gestão exigem troca no primeiro uso. Revogação e alterações de acesso
invalidam sessões anteriores. Gestores legados precisam ter e-mail cadastrado
antes de habilitar MFA obrigatório.

O arquivo `usuarios.db` também contém feedback, registros de auditoria,
conferências e contagens de uso. Preserve esse arquivo e `usuarios.secret` em
armazenamento privado com backup. Uma conferência do arquivo anterior não valida
um arquivo diferente: o registro usa o hash SHA-256 do conteúdo.

`PETSUS_UPDATE_INTERVAL_DAYS` define a frequência **planejada de revisão**;
zero significa sem agendamento. O produto não possui um conector automático para
tribunais ou serviços de saúde. Uma troca do arquivo precisa ser feita pela equipe
após validação, preferencialmente por substituição atômica, preservando a versão
anterior para recuperação. O botão de conferência registra o trabalho humano;
não constitui aprovação automática de dados clínicos.

## Trabalho que depende da equipe e de infraestrutura externa

Não foram realizadas sessões com gestores/pacientes reais. A ferramenta de
avaliação está disponível para a equipe aplicar após tarefas como localizar um
processo, compreender o próximo passo, obter o PDF e relatar uma inconsistência.
Registre dificuldades observadas, dispositivo, perfil e escore, sem inserir
dados pessoais no relato. Para pesquisa formal, escolha uma tradução SUS validada
e o protocolo de consentimento adequado.

O projeto não foi publicado ou migrado de hospedagem. Antes de usar dados reais,
é necessário substituir os enriquecimentos sintéticos por fontes validadas,
configurar os contatos, SMTP e integrações autorizadas, definir responsáveis e
periodicidade, revisar controles de acesso e retenção e implantar em ambiente
privado com TLS, backup e monitoramento. Não basta substituir a planilha
demonstrativa por dados reais: a geração sintética altera os campos para construir
cenários didáticos.

A supressão reduz exposição em células pequenas; filtros sucessivos e consultas
operacionais ainda exigem governança de acesso. Ela não é garantia matemática de
anonimização ou certificação de conformidade com a LGPD.


## Padronização da tela de login

Login com identidade visual do portal, cartão central, cores azul-marinho e verde-petróleo e layout responsivo. A barra lateral e seu botão de expansão ficam ocultos durante o acesso, cadastro e troca obrigatória de senha. Os controles A−, A+ e Contraste ficam no cabeçalho à direita e preservam os dados preenchidos. Cadastro, recuperação de senha e segundo fator foram mantidos.

Validação: 67 testes aprovados, incluindo controles de leitura no login, preservação do CPF e ausência de widgets na barra lateral. A conferência visual em navegador permanece pendente por indisponibilidade de navegador nesta sessão.

## Refinamentos dos dashboards

Identidade visual DASHJUS compartilhada no login e nos dois perfis, navegação com ícones, retirada do CPF da identificação lateral e animações decorativas breves que respeitam a preferência de reduzir movimentos. Gráficos com paleta semântica, legibilidade de rótulos, altura adaptável à quantidade de etapas e preferências de contraste e texto; o acompanhamento de saúde ocupa a largura disponível.

Demandas inclui definições de liminar, urgência e desfecho, além de causas e ações administrativas sugeridas. Medicamentos apresenta componente farmacêutico, incorporação à RENAME e dispensação por medicamento. Competência permite consulta individual do ente indicado. Prevenção detalha os critérios, a cobertura da classificação e as oportunidades de solução administrativa, com proteção de grupos pequenos.

Validação funcional mais recente: 78 testes aprovados. A revisão visual em navegador continua pendente por indisponibilidade de navegador nesta sessão.

## Integração com a estrutura modular da main

As páginas permanecem separadas em `dashboard/views/`, incluindo prevenção e componentes compartilhados. A implementação de autenticação está centralizada em `petsus/auth/application.py`; `auth.py` preserva os imports legados. A carga dos dados fica em `petsus/dashboard/app_services.py`, usando as regras de enriquecimento e a data de referência na chave do cache. APIs de exportação e cores usadas pelos módulos anteriores foram preservadas.

Validação após resolver os conflitos de integração: 87 testes aprovados, incluindo autenticação, navegação de todas as telas, métricas, privacidade, exportações e compatibilidade dos imports.

## Compatibilidade visual no Streamlit Cloud

Corrigida uma seção `[client]` duplicada que tornava o arquivo TOML inválido e impedia a aplicação consistente do tema. A versão do Streamlit está fixada em 1.62.0, igual à usada na validação. A navegação usa botões com ícones nativos em vez de radios e máscaras CSS. Login e perfis compartilham cores de campos, rótulos e placeholders, respeitando o alto contraste. As fontes têm alternativas locais, sem depender de importação de fontes externas.

Validação funcional: 98 testes aprovados, com verificação da configuração TOML e navegação por todas as páginas dos dois perfis. A conferência visual no navegador permanece pendente por indisponibilidade de navegador conectado.
