DASHBOARD DE JUDICIALIZAÇÃO NA SAÚDE

Como executar no Windows:

1) Abra o PowerShell ou CMD dentro desta pasta.
2) Instale as dependências:
   py -m pip install -r requirements.txt

3) Rode o dashboard:
   py -m streamlit run app.py

ESTRUTURA PARA MANUTENÇÃO

- app.py: composição da aplicação Streamlit e da interface principal.
- criar_gestor.py: comando administrativo para provisionar gestores.
- petsus/config.py: caminhos e constantes globais.
- petsus/access.py: restrição de dados conforme o perfil autenticado.
- petsus/data/: leitura da planilha, filtros e indicadores.
- petsus/auth/: modelos, senhas, verificação de e-mail e envio SMTP.
- petsus/dashboard/: navegação e despacho das páginas.
- dashboard/charts.py: construção dos gráficos Plotly.
- dashboard/ui.py: componentes visuais e formatação.
- dashboard/views.py: conteúdo das páginas existentes.
- tests/: testes de autenticação, dados e responsividade.

A lógica de dados em petsus/data não depende do Streamlit. Isso permite testar
filtros e indicadores separadamente da interface e facilita a futura troca da
planilha por outra fonte de dados.

Se o comando 'streamlit' não funcionar, use sempre:
   py -m streamlit run app.py

O que foi adicionado nesta versão:
- Base detalhada na aba base_processos do arquivo dados_dashboard_saude.xlsx.
- Filtros por período, paciente, CPF completo, número do processo, sexo, faixa etária, condição clínica, município, UF, região, natureza, tipo de demanda, item, especialidade, desfecho, fase, esfera, liminar e urgência.

VERIFICAÇÃO DE E-MAIL NO CADASTRO DE PACIENTES

Antes de iniciar o aplicativo, configure o servidor SMTP por variáveis de ambiente
ou no arquivo local .streamlit/secrets.toml (que não deve ser versionado):

PETSUS_SMTP_HOST = "smtp.exemplo.com"
PETSUS_SMTP_PORT = "587"
PETSUS_SMTP_USERNAME = "usuario_smtp"
PETSUS_SMTP_PASSWORD = "senha_smtp"
PETSUS_SMTP_FROM = "nao-responda@exemplo.com"
PETSUS_SMTP_SECURITY = "starttls"

Use PETSUS_SMTP_SECURITY = "ssl" para conexão SSL direta (normalmente porta 465)
ou "none" apenas se o servidor SMTP interno não oferecer criptografia.
- Página Pacientes, com busca individual e ficha do paciente selecionado.
- Página Base de Dados, com download em CSV e Excel da base filtrada.
- Indicadores e gráficos recalculados automaticamente conforme os filtros.

Como filtrar por paciente:
- Na barra lateral, use o campo "Buscar paciente / CPF / processo".
- Digite parte do nome, código PAC, CPF completo ou número do processo.
- Quando aparecerem pacientes encontrados, selecione o paciente exato no campo logo abaixo.

Observação:
Os dados são fictícios e servem para demonstração acadêmica. Para usar dados reais, substitua as linhas da aba base_processos mantendo os nomes das colunas.

ATUALIZAÇÃO - CAMPOS PETSUS

Foram adicionadas duas novas telas ao dashboard:
- Medicamentos: DCB, CID, incorporação à RENAME, componente/grupo SUS, PCDT, PMVG, apresentação e posologia.
- Competência: competência judicial, réu sugerido, valor anual do tratamento, valor da causa e critério de 210 salários mínimos.
- Andamento: duas trilhas independentes para o andamento judicial e o cumprimento material na rede de saúde.

Na tela Andamento, o gestor acompanha todos os processos do recorte e o paciente visualiza somente os processos vinculados à sua conta. A tela diferencia decisão judicial, intimação, prazo de cumprimento, estoque/regulação, disponibilização e entrega ou realização do procedimento.

Os eventos de andamento da base acadêmica são sintéticos e determinísticos. Em produção, devem ser atualizados por integração com o tribunal, secretaria de saúde, farmácia, unidade hospitalar ou operador autorizado.

Novos filtros na barra lateral:
- DCB / princípio ativo
- CID
- Incorporado à RENAME
- Componente SUS
- Grupo de financiamento
- PCDT aplicável
- PCDT de referência
- Competência PetSUS
- Réu sugerido

Novas variáveis incorporadas à base exibida/exportada:
- medicamento_petsus
- medicamento_dcb
- cid
- rename_incorporado
- componente_sus
- grupo_sus
- apresentacao_padronizada
- pcdt_aplicavel
- pcdt_referencia
- dose_prescrita
- frequencia_administracao
- duracao_meses
- pmvg_referencia
- valor_anual_tratamento
- valor_causa_estimado
- competencia_petsus
- reu_sugerido
- criterio_competencia
- acima_210_salarios_minimos

IMPORTANTE:
A base original do projeto é fictícia. Os novos valores PetSUS são gerados de forma sintética e determinística apenas para fins acadêmicos/demonstração. Eles NÃO representam consulta oficial ao CNJ, à RENAME ou à CMED/Anvisa.

Referências funcionais usadas para modelar os campos:
https://www.cnj.jus.br/ferramenta-publica-facilita-definicao-de-competencia-em-processos-na-saude/
https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2025/decreto/d12797.htm

ATUALIZAÇÃO - LOGIN E PERFIS DE ACESSO

O dashboard agora possui autenticação com dois perfis:
- Gestor: visualiza a base completa e mantém a busca/filtros globais.
- Usuário: visualiza somente os registros vinculados ao seu paciente_id.

Segurança aplicada:
- Senhas não são salvas em texto; são armazenadas com hash scrypt + salt.
- O CPF usado no login não é salvo em texto completo no banco de usuários.
- O filtro por paciente do usuário comum é aplicado antes de KPIs, tabelas, gráficos e exportações.
- O cadastro público cria apenas contas de usuário comum; gestor é criado pela administração.

Como criar o primeiro gestor:
1) Dentro da pasta do projeto, execute:
   py criar_gestor.py
2) Informe CPF, nome e senha do gestor.
3) Depois rode normalmente:
   py -m streamlit run app.py

Também é possível provisionar o primeiro gestor por variáveis de ambiente:
- PETSUS_GESTOR_CPF
- PETSUS_GESTOR_SENHA
- PETSUS_GESTOR_NOME (opcional)
- PETSUS_GESTOR_DATA_NASCIMENTO (opcional, formato AAAA-MM-DD; necessário para recuperação automática da senha do gestor)

RECUPERAÇÃO DE SENHA

Na tela de autenticação, use a aba "Recuperar senha". O sistema confirma CPF, e-mail cadastrado e data de nascimento, envia um código de seis dígitos ao e-mail e permite definir uma nova senha. A data de nascimento é armazenada como hash. Contas criadas antes desta funcionalidade precisam ter essa informação atualizada antes de usar a recuperação automática.

Cadastro de usuário comum:
- O cadastro de usuário comum pede apenas CPF e senha. O CPF precisa existir na base carregada pelo sistema; o paciente_id é identificado automaticamente.
- Se a fonte trouxer `cpf`, `cpf_completo` ou `cpf_paciente`, esse CPF completo é usado diretamente.
- Como a planilha acadêmica original contém apenas `cpf_mascarado`, esta versão cria CPFs completos de demonstração, estáveis e propositalmente não válidos como CPF real. Eles servem apenas para testes.
- Em produção, substitua a base fictícia por uma fonte protegida com CPF completo real e restrinja o acesso conforme a LGPD.

Arquivos locais de autenticação criados na primeira execução:
- usuarios.db: banco SQLite das contas.
- usuarios.secret: segredo local usado na proteção do identificador de CPF.
Mantenha ambos fora de repositórios públicos e faça backup seguro no ambiente de produção.
