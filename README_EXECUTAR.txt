DASHBOARD DE JUDICIALIZAÇÃO NA SAÚDE

Como executar no Windows:

1) Abra o PowerShell ou CMD dentro desta pasta.
2) Instale as dependências:
   py -m pip install -r requirements.txt

3) Rode o dashboard:
   py -m streamlit run app.py

Se o comando 'streamlit' não funcionar, use sempre:
   py -m streamlit run app.py

O que foi adicionado nesta versão:
- Base detalhada na aba base_processos do arquivo dados_dashboard_saude.xlsx.
- Filtros por período, paciente, CPF mascarado, número do processo, sexo, faixa etária, condição clínica, município, UF, região, natureza, tipo de demanda, item, especialidade, desfecho, fase, esfera, liminar e urgência.
- Página Pacientes, com busca individual e ficha do paciente selecionado.
- Página Base de Dados, com download em CSV e Excel da base filtrada.
- Indicadores e gráficos recalculados automaticamente conforme os filtros.

Como filtrar por paciente:
- Na barra lateral, use o campo "Buscar paciente / CPF / processo".
- Digite parte do nome, código PAC, CPF mascarado ou número do processo.
- Quando aparecerem pacientes encontrados, selecione o paciente exato no campo logo abaixo.

Observação:
Os dados são fictícios e servem para demonstração acadêmica. Para usar dados reais, substitua as linhas da aba base_processos mantendo os nomes das colunas.

ATUALIZAÇÃO - CAMPOS JUDSAÚDE

Foram adicionadas duas novas telas ao dashboard:
- Medicamentos: DCB, CID, incorporação à RENAME, componente/grupo SUS, PCDT, PMVG, apresentação e posologia.
- Competência: competência judicial, réu sugerido, valor anual do tratamento, valor da causa e critério de 210 salários mínimos.

Novos filtros na barra lateral:
- DCB / princípio ativo
- CID
- Incorporado à RENAME
- Componente SUS
- Grupo de financiamento
- PCDT aplicável
- PCDT de referência
- Competência JudSaúde
- Réu sugerido

Novas variáveis incorporadas à base exibida/exportada:
- medicamento_judsaude
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
- competencia_judsaude
- reu_sugerido
- criterio_competencia
- acima_210_salarios_minimos

IMPORTANTE:
A base original do projeto é fictícia. Os novos valores JudSaúde são gerados de forma sintética e determinística apenas para fins acadêmicos/demonstração. Eles NÃO representam consulta oficial ao CNJ, à RENAME ou à CMED/Anvisa.

Referências funcionais usadas para modelar os campos:
https://www.cnj.jus.br/tecnologia-da-informacao-e-comunicacao/justica-4-0/conheca-o-conecta/judsaude/perguntas-frequentes/
https://www.cnj.jus.br/ferramenta-publica-facilita-definicao-de-competencia-em-processos-na-saude/
https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2025/decreto/d12797.htm
