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
