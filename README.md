# PETSUS — Plataforma de Monitoramento, Gestão e Prevenção da Judicialização na Saúde

Plataforma analítica e operacional para monitoramento de processos judiciais de saúde pública no âmbito do Sistema Único de Saúde (SUS), combinando visão estratégica para gestores públicos e um portal de acompanhamento para pacientes e cidadãos.

A evolução desta plataforma é orientada pelo framework de maturidade em dashboards de saúde pública de **Wu et al. (2025, JMIR Preprints)**: *Building Public Health Data Dashboards: A Tutorial Playbook* (5W1H, Curadoria de Dados, Design de Visualizações, Hospedagem/LGPD e Feedback/Revisão Contínua).

---

## 📌 Sumário
1. [Visão Geral e Arquitetura de Perfis](#-visão-geral-e-arquitetura-de-perfis)
2. [Diagnóstico Crítico da Versão Atual](#-diagnóstico-crítico-da-versão-atual)
3. [Checklist Mestre de Tarefas e Melhorias](#-checklist-mestre-de-tarefas-e-melhorias)
   - [Eixo 1: Redesenho Radical do Perfil Paciente (Portal Cidadão)](#eixo-1-redesenho-radical-do-perfil-paciente-portal-cidadão)
   - [Eixo 2: Privacidade, Segurança e Conformidade com a LGPD](#eixo-2-privacidade-segurança-e-conformidade-com-a-lgpd)
   - [Eixo 3: Curadoria de Dados e Rigor Metodológico das Métricas](#eixo-3-curadoria-de-dados-e-rigor-metodológico-das-métricas)
   - [Eixo 4: Design das Visualizações e Limpeza de Interface (UI/UX)](#eixo-4-design-das-visualizações-e-limpeza-de-interface-uiux)
   - [Eixo 5: Enriquecimento Estratégico da Gestão Pública](#eixo-5-enriquecimento-estratégico-da-gestão-pública)
   - [Eixo 6: Governança, Sustentação e Feedback Pós-Lançamento](#eixo-6-governança-sustentação-e-feedback-pós-lançamento)
4. [Governança de Dados, Rotinas de Carga e Escalonamento](#-governança-de-dados-rotinas-de-carga-e-escalonamento)
5. [Como Executar a Aplicação](#-como-executar-a-aplicação)
6. [Estrutura do Código-Fonte](#-estrutura-do-código-fonte)

Para instruções operacionais detalhadas, consulte o [guia de execução](README_EXECUTAR.md).

---

## 🩺 Visão Geral e Arquitetura de Perfis

O PETSUS estrutura a judicialização da saúde a partir de duas trilhas independentes:
* **Trilha A (Andamento Judicial):** Fases do processo, intimações, concessão de liminares, recursos e decisões de mérito.
* **Trilha B (Cumprimento na Saúde):** Tramitação administrativa, regulação de vagas, aquisição extraordinária, dispensação em farmácia ou agendamento de procedimentos.

### Os Dois Perfis de Usuário
1. **Perfil Gestor (Secretarias Municipais, Estaduais e Órgãos de Controle):** Visão macro e micro de demandas, custos, competência federativa (Tema 1234/STF), conformidade com RENAME/PCDT e prevenção de litígios.
2. **Perfil Paciente / Cidadão:** Acompanhamento do andamento real da sua demanda de forma simples, transparente e acolhedora, sem ruídos ou métricas executivas que causem desinformação.

---

## 🔍 Diagnóstico Crítico da Versão Atual

Baseado na matriz de avaliação de *Wu et al. (2025)*:

| Dimensão | Perfil Gestor | Perfil Paciente | Status / Diretriz de Correção |
|---|---|---|---|
| **1. Considerações Centrais (5W1H)** | Bem alinhado aos objetivos de gestão | **Desalinhado:** cópia filtrada do gestor com indicadores inadequados para $n=1$ | **Prioridade Alta:** redesenhar a experiência do paciente |
| **2. Curadoria de Dados** | Denominador da procedência explícito; custos estimados diferenciados; classificação detalhada de liminares depende de novos dados | Herda limites da fonte sintética | **Em andamento:** validar semântica e completar campos com o curador |
| **3. Design das Visualizações** | Roscas de gestão substituídas por barras nos indicadores priorizados; paleta semântica e margens ajustadas | Gráficos do perfil individual preservados conforme contexto | **Em andamento:** revisar escalas e demais visualizações |
| **4. Hospedagem e LGPD** | CPF mascarado na interface e exportações padrão sem identificadores diretos; contagens pequenas suprimidas nas análises geográficas existentes | Isolamento dos próprios registros | **Em andamento:** auditar acessos e definir campos para cruzamentos sensíveis |
| **5. Feedback e Revisão** | Rodapé temporal e canal de feedback implementados | Disponíveis nas páginas renderizadas | **Implementado no MVP** |

---

## 📋 Checklist Mestre de Tarefas e Melhorias

### Eixo 1: Redesenho Radical do Perfil Paciente (Portal Cidadão)
*Objetivo: Substituir a visão de BI por um serviço cidadão focado em: onde está meu pedido, quem é o responsável agora, qual é o prazo e a quem procurar.*

- [x] **Desacoplamento de Telas:**
  - [x] Ocultar totalmente da navegação do paciente as abas de gestão: `Demandas`, `Medicamentos`, `Competência`, `Custos` e `Geografia`.
  - [x] Manter apenas: `Visão Geral` (painel cidadão), `Meu Andamento` (Trilhas A e B + PDF + glossário) e `Meus Documentos` (tabela dos próprios registros + exportação).
- [x] **Eliminação de Sobrecarga de Filtros:**
  - [x] Remover a barra lateral com os 30 filtros demográficos, geográficos e processuais na sessão do paciente.
  - [x] Caso o paciente possua mais de 1 processo ativo, disponibilizar apenas um seletor simples de processo no topo da tela.
- [x] **Reformulação da Interface do Paciente ($n = 1$):**
  - [x] Eliminar cards populacionais (`Taxa de procedência`, `Ticket médio`, `Taxa de liminares`, `Custo por esfera`).
  - [x] Eliminar gráficos distorcidos para registro único: roscas de 100%, boxplots colapsados, eixos com números negativos e linhas temporais com um único ponto.
  - [x] Exibir o status do processo em linguagem cidadã e empática (ex.: *"Seu pedido está em análise judicial"*, *"Medicamento aguardando compra pela Secretaria"*, *"Disponível para retirada"*).
  - [x] Destacar a **Data Limite para Cumprimento** e alerta amigável de prazo caso haja atraso na entrega.
- [x] **Suporte, Acolhimento e Orientação Legal:**
  - [x] Incluir cartão com contatos diretos do órgão defensor do paciente (Defensoria Pública do Estado/União, OAB ou advogado cadastrado).
  - [x] Criar **Glossário Cidadão** explicando termos jurídicos e farmacêuticos comuns (*tutela de urgência*, *liminar*, *RENAME*, *litisconsórcio*, *polo passivo*).
  - [x] Preservar e aprimorar o botão de geração de **Relatório de Acompanhamento em PDF**.

---

### Eixo 2: Privacidade, Segurança e Conformidade com a LGPD
*Objetivo: Proteger dados pessoais sensíveis de saúde e eliminar qualquer risco de reidentificação ou vazamento.*

- [ ] **Mascaramento Universal de CPF:**
  - [x] Mascarar CPFs em tabelas, cartões de paciente e resultados de busca.
  - [ ] Criar fluxo autorizado e auditado para acesso excepcional ao CPF completo; atualmente ele não é exibido na interface.
- [ ] **Regra de Supressão Estatística de Células Pequenas ($k$-Anonimato / $n < 5$):**
  - [x] Suprimir contagens pequenas nas tabelas geográficas e omitir grupos com menos de 5 processos nos gráficos e mapas municipais existentes.
  - [ ] Aplicar a regra a cruzamentos de município, doença rara e faixa etária caso esses cruzamentos sejam adicionados.
- [ ] **Segurança de Exportação e Infraestrutura:**
  - [x] Sanitizar CSV/Excel padrão, removendo nome, ID do paciente e colunas de CPF.
  - [x] Ocultar barra de ferramentas e menus de desenvolvimento do Streamlit (*Share*, *GitHub*, *Manage app*) via arquivo de configuração (`.streamlit/config.toml` com `client.toolbarMode = "minimal"`).
  - [ ] Registrar trilha de auditoria (*audit log*) das consultas de CPF e exportações realizadas no módulo de Gestão Interna.

---

### Eixo 3: Curadoria de Dados e Rigor Metodológico das Métricas
*Objetivo: Eliminar ambiguidades conceituais, padronizar fórmulas e garantir coerência temporal dos cálculos.*

- [ ] **Taxa de Procedência:**
  - [x] Explicar a fórmula no ícone de ajuda: procedentes e parcialmente procedentes sobre processos com desfecho definido.
  - [ ] Separar os percentuais de *Procedência Total* e *Procedência Parcial*.
  - [x] Excluir do denominador processos *Em andamento* e *Sem resolução de mérito*.
- [ ] **Padronização dos Indicadores de Liminar e Urgência:**
  - [ ] A base atual informa apenas `liminar` como Sim/Não; a interface explicita esse limite e não inventa os estados formulada/deferida/indeferida/aguardando.
  - [ ] Definir o critério de **Urgência**: explicitar se reflete tutela judicial requerida ou gravidade do risco clínico assistencial.
- [ ] **Desambiguação das Métricas de Custo:**
  - [x] Distinguir `custo_estimado` (estimativa para o erário), `valor_anual_tratamento` (estimativa baseada no PMVG) e `valor_causa_estimado` (estimativa do pedido na petição).
  - [x] Explicitar essas diferenças nos cartões e cabeçalhos das tabelas.
- [ ] **Sincronismo Temporal e Coerência dos Dados Sintéticos:**
  - [x] O indicador de atraso compara o prazo limite com a data atual real; há teste cobrindo datas futuras.
  - [ ] Alinhar o parâmetro de corte de 210 salários mínimos ao ano base do recorte histórico dos dados (ou justificar o uso do valor de referência de 2026).
  - [ ] Higienizar a coerência clínica dos registros sintéticos de demonstração (ex.: paciente com diabetes recebendo prescrição correlata à sua especialidade).

---

### Eixo 4: Design das Visualizações e Limpeza de Interface (UI/UX)
*Objetivo: Tornar as telas do gestor mais legíveis, ergonômicas e aderentes aos princípios de Gestalt.*

- [ ] **Substituição de Gráficos de Rosca por Barras:**
  - [x] Substituir *Desfecho*, *Natureza da Ação*, *PCDT*, *RENAME* e *Competência* por barras horizontais ordenadas.
  - [x] Usar barras horizontais para as variáveis binárias de RENAME e PCDT.
- [ ] **Padronização Cromática com Significado Fixo (Gestalt da Similaridade):**
  - [x] Definir cores semânticas e aplicá-las nos gráficos de competência, desfecho e liminares:
    - Justiça Estadual: Sempre Azul Escuro `#083E82`.
    - Justiça Federal: Sempre Azul Celeste `#0284C7`.
    - Deferido / Procedente: Sempre Verde `#16A34A`.
    - Indeferido / Improcedente: Sempre Carmim/Vermelho `#DC2626`.
    - Em Tramitação / Pendente: Sempre Âmbar/Laranja `#D97706`.
- [ ] **Correção de Tipografia e Rótulos Cortados:**
  - [x] Aumentar margens e habilitar ajuste automático dos eixos para reduzir cortes.
  - [x] Substituir nomes técnicos nos cabeçalhos das tabelas por nomenclaturas em português claro.
- [ ] **Equalização de Escalas e Faixas Etárias:**
  - [ ] Tratar categorias desproporcionais (ex.: fase *Sentença* ou natureza *Medicamentos* que esmagam visualmente as demais categorias) com escalas relativas, quebras ou filtros de detalhamento.
  - [ ] Padronizar intervalos de faixas etárias para evitar amplitudes desiguais que distorçam as comparações estatísticas.

---

### Eixo 5: Enriquecimento Estratégico da Gestão Pública
*Objetivo: Transformar o painel em instrumento de inteligência ativa para redução de custos e resolutividade administrativa.*

- [ ] **Aba Demandas — Análise de Causa-Raiz:**
  - [ ] Remover a tabela redundante de tipos de demanda, mantendo apenas a tabela de demandas por tipo e fase processual.
  - [ ] Adicionar tabela/gráfico com a **Classificação da Causa da Judicialização**:
    - Falta pontual de medicamento no estoque;
    - Falta de prestador credenciado na região;
    - Ausência de vaga hospitalar / leito especializado;
    - Demora no sistema de regulação;
    - Negativa administrativa prévia;
    - Demanda de competência originária de outro ente federativo;
    - Serviço disponível na rede, mas não acessado pelo usuário por falha de informação.
- [ ] **Aba Medicamentos — Enquadramento na RENAME:**
  - [ ] Criar levantamento estratificado por **Componente da Assistência Farmacêutica**:
    - **CBAF (Componente Básico):** Financiamento tripartite e dispensação obrigatória pelo Município;
    - **CEAF (Componente Especializado):** Fármacos de alto custo sob responsabilidade primária do Estado;
    - **CESAF (Componente Estratégico):** Controle de endemias e programas específicos do Ministério da Saúde;
    - **Não Incorporado:** Medicamentos fora da lista oficial do SUS.
  - [ ] Disponibilizar indicador de processos e custos que pleiteiam fármacos de competência estadual/federal para apoiar a Procuradoria Municipal no pedido de ressarcimento.
- [ ] **Aba Competências — Polo Passivo e Solidariedade Federativa:**
  - [ ] Criar indicador para distinguir as ações quanto ao réu judicial:
    - Ação ajuizada exclusivamente contra o Município;
    - Ação contra Município e Estado (Litisconsórcio);
    - Ação com inclusão da União (Justiça Federal / parâmetro do Tema 1234 do STF).
- [ ] **Módulo de Prevenção de Judicialização (SUS Mediado):**
  - [ ] Criar o indicador de **Judicialização Potencialmente Evitável**: mapear demandas que poderiam ter sido resolvidas administrativamente em câmaras de mediação de saúde, evitando custas processuais e bloqueios judiciais de verbas públicas.

---

### Eixo 6: Governança, Sustentação e Feedback Pós-Lançamento
*Objetivo: Garantir confiabilidade contínua dos dados, rastreabilidade de erros e escuta dos usuários.*

- [x] **Selo de Transparência Temporal:**
  - [x] Exibir no rodapé de todas as páginas:
    - *Data e hora da última modificação do arquivo da base* (via `mtime` do Excel);
    - *Data de corte dos cálculos e regras de prazo* (configurável em `petsus/config.py` → `DATA_CORTE_CALCULOS`);
    - *Data prevista para a próxima atualização* (configurável em `petsus/config.py` → `PROXIMA_ATUALIZACAO`; está como “A definir” até confirmação do curador).
- [x] **Canal de Feedback e Ouvidoria Integrado:**
  - [x] Botão flutuante fixo no canto inferior direito da tela ("💬 Reportar inconsistência"), configurável via `FEEDBACK_URL` em `petsus/config.py`.
- [ ] **Homologação e Teste de Usabilidade (Soft Launch):**
  - [ ] Realizar piloto com 5 gestores de saúde e 10 pacientes antes do lançamento oficial.
  - [ ] Aplicar a escala internacional **SUS (*System Usability Scale*)** para mensurar ergonomia e facilidade de uso da plataforma.

---

## ⚙️ Governança de Dados, Rotinas de Carga e Escalonamento

### 1. Periodicidade de Alimentação do Sistema
| Camada de Dados | Frequência Recomendada | Fonte Primária | Justificativa |
|---|---|---|---|
| **Prazos e Cumprimento Assistencial (Trilha B)** | **Semanal** (ou Near-Real-Time) | Sistema de Regulação, Almoxarifado da Farmácia Municipal e SEI | Prazos de tutelas de urgência variam de 24 horas a 5 dias. Atualização mensal causaria atrasos críticos. |
| **Movimentações Processuais (Trilha A)** | **Semanal** | API Pública do CNJ (**DataJud**) / Diários de Justiça | Acompanhamento de liminares deferidas e prazos para manifestação da Procuradoria. |
| **Custos Consolidados e Orçamento** | **Mensal** | Sistema de Contabilidade / Fundo Municipal de Saúde | O fechamento contábil e a liquidação de despesas empenhadas ocorrem em ciclo mensal. |

---

### 2. Controle de Qualidade e Risco de Dados Equivocados
Para prevenir subida de dados errôneos (ex.: valores de causa com zeros extras, duplicidade de registros, incongruências clínicas):
1. **Pipeline Automatizado de Validação (*Data Quality Gates*):** A carga de novas planilhas ou bancos é submetida a checagens automáticas de schema antes da publicação:
   - Validação de formato de datas, CPF e números de processo;
   - Bloqueio de valores de causa acima de limites plausíveis sem confirmação manual;
   - Teste de consistência temporal ($Data_{Intimação} \le Data_{Limite}$).
2. **Papel do Curador de Dados (*Data Steward*):** Um profissional designado na Secretaria de Saúde ou no projeto atua como homologador responsável antes da publicação final da base no painel.

---

### 3. Matriz de Escalonamento: A Quem Procurar?
| Tipo de Ocorrência | Responsável pelo Atendimento | Prazo Típico |
|---|---|---|
| **Erro em Processo Específico** (status defasado, medicamento incorreto, valor digitado errado) | **Setor de Judicialização da Secretaria de Saúde / NATJUS** | Até 2 dias úteis |
| **Falha Sistêmica na Plataforma** (gráficos quebrados, erro de cálculo, lentidão) | **Equipe Técnica de TI / Engenharia de Software** | Até 24 horas |
| **Incidente de Dados Sensíveis ou Privacidade** (exposição indevida de CPF ou prontuário) | **Encarregado de Dados / DPO da Instituição (LGPD)** | Imediato |

---

### 4. Comunicação e Feedback Contínuo dos Usuários
A plataforma deve contar com dois mecanismos permanentes de escuta:
* **Mecanismo Ativo (Widget na Plataforma):** Um botão discreto no canto da tela (*"Reportar Inconsistência ou Sugestão"*), permitindo ao gestor ou ao paciente relatar qualquer discrepância de forma simples.
* **Mecanismo Periódico (Pesquisa de Usabilidade SUS):** Aplicação semestral da escala padronizada de usabilidade (10 questões) para coletar percepções e priorizar melhorias contínuas no roadmap do software.

---

## 🚀 Como Executar a Aplicação

### Pré-requisitos
* Python 3.10 ou superior instalado.
* Dependências listadas no `requirements.txt`.

### Passo a Passo

1. **Clonar o repositório e abrir o terminal na pasta:**
   ```bash
   cd c:\Users\natha\OneDrive\Documentos\GitHub\PETSUS
   ```

2. **Instalar as dependências:**
   ```bash
   py -m pip install -r requirements.txt
   ```

3. **Executar a aplicação Streamlit:**
   ```bash
   py -m streamlit run app.py
   ```

4. **Criar uma conta inicial de Gestor (caso necessário):**
   ```bash
   py criar_gestor.py
   ```

### Configuração de Envio de E-mails (SMTP)
Para habilitar o envio de links de verificação cadastral para novos pacientes, configure as credenciais no arquivo `.streamlit/secrets.toml`:
```toml
PETSUS_SMTP_HOST = "smtp.seu-servidor.com"
PETSUS_SMTP_PORT = "587"
PETSUS_SMTP_USERNAME = "usuario_smtp"
PETSUS_SMTP_PASSWORD = "senha_smtp"
PETSUS_SMTP_FROM = "nao-responda@petsus.saude.gov.br"
PETSUS_SMTP_SECURITY = "starttls"
```

---

## 📂 Estrutura do Código-Fonte

```text
PETSUS/
├── app.py                      # Aplicação principal Streamlit, barra lateral e montagem de layout
├── auth.py                     # Controle de sessão, autenticação e telas de login
├── criar_gestor.py             # Script CLI para provisionamento manual de gestores
├── dados_dashboard_saude.xlsx  # Base de dados acadêmica e demonstrativa
├── DICIONARIO_PETSUS.md        # Dicionário de variáveis e fundamentação legal (Tema 1234, CMED, RENAME)
├── README_EXECUTAR.txt         # Instruções operacionais rápidas de execução
├── README.md                   # Este documento (visão geral, checklist mestre e governança)
├── requirements.txt            # Dependências do projeto (Streamlit, Plotly, Pandas, ReportLab, etc.)
├── dashboard/
│   ├── charts.py               # Funções de construção de gráficos Plotly
│   ├── ui.py                   # Componentes visuais HTML/CSS, cards de métricas e formatação
│   └── views.py                # Implementação das páginas e relatórios do dashboard
├── petsus/
│   ├── access.py               # Camada de controle de acesso e isolamento de escopo por perfil
│   ├── config.py               # Constantes globais, caminhos e parâmetros legais (ex.: teto 210 SM)
│   ├── auth/                   # Módulos de segurança, hashing, modelos e verificação SMTP
│   ├── dashboard/              # Navegação, despacho de páginas e gestão interna de usuários
│   ├── data/                   # Carregamento de dados, filtros desacoplados e cálculo de KPIs
│   └── reports/                # Gerador do relatório de acompanhamento de processos em PDF
└── tests/                      # Bateria de testes automatizados (segurança, filtros e layout)
```
