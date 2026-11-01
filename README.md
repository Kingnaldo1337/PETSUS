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
| **2. Curadoria de Dados** | Boa, mas com métricas de procedência e custos ambíguas | Herda ambiguidades e gera falsas leituras (ex.: taxa de procedência 0% para processo em curso) | **Prioridade Alta:** explicitar denominadores e ajustar base sintética |
| **3. Design das Visualizações** | Robusto nas trilhas; excesso de gráficos de rosca e cores instáveis | Gráficos sem sentido para $n=1$ (roscas 100%, eixos negativos) | **Prioridade Média:** substituir roscas por barras e fixar paleta cromática |
| **4. Hospedagem e LGPD** | Bom isolamento, mas expõe CPFs completos e não suprime células pequenas ($n < 5$) | Bom isolamento dos próprios registros | **Prioridade Máxima:** mascarar CPFs e aplicar regras de supressão |
| **5. Feedback e Revisão** | Ausente (sem canal de erro, sem datas de atualização explícitas) | Ausente | **Prioridade Média:** implementar selo temporal e canal de feedback |

---

## 📋 Checklist Mestre de Tarefas e Melhorias

### Eixo 1: Redesenho Radical do Perfil Paciente (Portal Cidadão)
*Objetivo: Substituir a visão de BI por um serviço cidadão focado em: onde está meu pedido, quem é o responsável agora, qual é o prazo e a quem procurar.*

- [ ] **Desacoplamento de Telas:**
  - [x] Ocultar totalmente da navegação do paciente as abas de gestão: `Demandas`, `Medicamentos`, `Competência`, `Custos` e `Geografia`.
  - [ ] Manter apenas: `Meu Andamento` (Trilhas A e B simplificadas), `Meus Documentos / PDF` e `Orientação e Contatos`.
- [x] **Eliminação de Sobrecarga de Filtros:**
  - [x] Remover a barra lateral com os 30 filtros demográficos, geográficos e processuais na sessão do paciente.
  - [x] Caso o paciente possua mais de 1 processo ativo, disponibilizar apenas um seletor simples de processo no topo da tela.
- [ ] **Reformulação da Interface do Paciente ($n = 1$):**
  - [ ] Eliminar cards populacionais (`Taxa de procedência`, `Ticket médio`, `Taxa de liminares`, `Custo por esfera`).
  - [ ] Eliminar gráficos distorcidos para registro único: roscas de 100%, boxplots colapsados, eixos com números negativos e linhas temporais com um único ponto.
  - [ ] Exibir o status do processo em linguagem cidadã e empática (ex.: *"Seu pedido está em análise judicial"*, *"Medicamento aguardando compra pela Secretaria"*, *"Disponível para retirada"*).
  - [ ] Destacar a **Data Limite para Cumprimento** e alerta amigável de prazo caso haja atraso na entrega.
- [ ] **Suporte, Acolhimento e Orientação Legal:**
  - [ ] Incluir cartão com contatos diretos do órgão defensor do paciente (Defensoria Pública do Estado/União, OAB ou advogado cadastrado).
  - [ ] Criar **Glossário Cidadão** explicando termos jurídicos e farmacêuticos comuns (*tutela de urgência*, *liminar*, *RENAME*, *litisconsórcio*, *polo passivo*).
  - [ ] Preservar e aprimorar o botão de geração de **Relatório de Acompanhamento em PDF**.

---

### Eixo 2: Privacidade, Segurança e Conformidade com a LGPD
*Objetivo: Proteger dados pessoais sensíveis de saúde e eliminar qualquer risco de reidentificação ou vazamento.*

- [ ] **Mascaramento Universal de CPF:**
  - [ ] Mascarar CPFs em **todas** as tabelas analíticas (`***.456.789-**`), em especial nas páginas *Pacientes* (*Pacientes com maior custo acumulado*) e *Base de Dados*.
  - [ ] Permitir visualização do CPF completo apenas para perfis autorizados de assistência direta, com registro obrigatório de auditoria.
- [ ] **Regra de Supressão Estatística de Células Pequenas ($k$-Anonimato / $n < 5$):**
  - [ ] Implementar supressão em cruzamentos analíticos com alto potencial de reidentificação (ex.: combinações de *município pequeno + doença rara + faixa etária*).
  - [ ] Quando o grupo filtrado tiver menos de 5 pacientes, exibir `< 5` ou omitir dados individualizados para preservar a privacidade do paciente do SUS.
- [ ] **Segurança de Exportação e Infraestrutura:**
  - [ ] Sanitizar arquivos gerados em CSV/Excel, removendo colunas com nomes e CPFs desmascarados na exportação padrão.
  - [ ] Ocultar barra de ferramentas e menus de desenvolvimento do Streamlit (*Share*, *GitHub*, *Manage app*) via arquivo de configuração (`.streamlit/config.toml` com `client.toolbarMode = "minimal"`).
  - [ ] Registrar trilha de auditoria (*audit log*) das consultas de CPF e exportações realizadas no módulo de Gestão Interna.

---

### Eixo 3: Curadoria de Dados e Rigor Metodológico das Métricas
*Objetivo: Eliminar ambiguidades conceituais, padronizar fórmulas e garantir coerência temporal dos cálculos.*

- [ ] **Taxa de Procedência:**
  - [ ] Explicitar fórmula no ícone de ajuda `(?)`: $\text{Taxa de Êxito} = \frac{\text{Procedentes}}{\text{Processos com Julgamento de Mérito}}$.
  - [ ] Separar os percentuais de *Procedência Total* e *Procedência Parcial*.
  - [ ] Excluir do denominador processos ainda em andamento, acordos ou extintos sem resolução de mérito, ou rotular como *Taxa Bruta Global*.
- [ ] **Padronização dos Indicadores de Liminar e Urgência:**
  - [ ] Detalhar o indicador de **Liminares**: diferenciar processos com *Pedido de liminar formulado*, *Liminar Deferida*, *Liminar Indeferida* e *Aguardando apreciação*.
  - [ ] Definir o critério de **Urgência**: explicitar se reflete tutela judicial requerida ou gravidade do risco clínico assistencial.
- [ ] **Desambiguação das Métricas de Custo:**
  - [ ] Padronizar e explicar a distinção entre:
    - *Custo Efetivo / Liquidado na Saúde* (gasto real efetuado pelo erário);
    - *Valor Anual Estimado do Tratamento* (posologia anual multiplicada pelo PMVG/CMED);
    - *Valor da Causa Judicial* (fixado na petição inicial).
  - [ ] Evitar exibição concorrente sem legenda explicativa clara.
- [ ] **Sincronismo Temporal e Coerência dos Dados Sintéticos:**
  - [ ] Corrigir anomalias temporais: garantir que a data de corte do dashboard não classifique eventos futuros como "Prazo Vencido".
  - [ ] Alinhar o parâmetro de corte de 210 salários mínimos ao ano base do recorte histórico dos dados (ou justificar o uso do valor de referência de 2026).
  - [ ] Higienizar a coerência clínica dos registros sintéticos de demonstração (ex.: paciente com diabetes recebendo prescrição correlata à sua especialidade).

---

### Eixo 4: Design das Visualizações e Limpeza de Interface (UI/UX)
*Objetivo: Tornar as telas do gestor mais legíveis, ergonômicas e aderentes aos princípios de Gestalt.*

- [ ] **Substituição de Gráficos de Rosca por Barras:**
  - [ ] Substituir gráficos de rosca com muitas categorias (*Desfecho*, *Natureza da Ação*, *PCDT*, *Competência*) por gráficos de barras horizontais ordenadas.
  - [ ] Para variáveis binárias (Sim/Não), priorizar cartões de número único ou barras empilhadas 100%.
- [ ] **Padronização Cromática com Significado Fixo (Gestalt da Similaridade):**
  - [ ] Fixar cores semânticas em todo o dashboard:
    - Justiça Estadual: Sempre Azul Escuro `#083E82`.
    - Justiça Federal: Sempre Azul Celeste `#0284C7`.
    - Deferido / Procedente: Sempre Verde `#16A34A`.
    - Indeferido / Improcedente: Sempre Carmim/Vermelho `#DC2626`.
    - Em Tramitação / Pendente: Sempre Âmbar/Laranja `#D97706`.
- [ ] **Correção de Tipografia e Rótulos Cortados:**
  - [ ] Corrigir quebras indevidas de rótulos numéricos (`R$ 24-`, `R$ 88,4`, `freq`, `Cu`).
  - [ ] Substituir nomes técnicos de banco de dados nos cabeçalhos e tooltips por nomenclaturas em português claro (`faixa_etaria` $\rightarrow$ *"Faixa Etária"*, `medicamento_dcb` $\rightarrow$ *"Princípio Ativo (DCB)"*, `rename_incorporado` $\rightarrow$ *"Incorporado ao SUS"*).
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

- [ ] **Selo de Transparência Temporal:**
  - [ ] Exibir no cabeçalho ou rodapé de todas as páginas:
    - *Data e hora da última extração da base de dados*;
    - *Data de corte dos cálculos e regras de prazo*;
    - *Data prevista para a próxima atualização*.
- [ ] **Canal de Feedback e Ouvidoria Integrado:**
  - [ ] Implementar botão de feedback ou formulário na interface para relatar erros de dados ou sugerir melhorias.
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

