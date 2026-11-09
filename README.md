# PETSUS

Dashboard demonstrativo para visualização e acompanhamento de informações relacionadas à judicialização da saúde no SUS, com áreas para gestores e pacientes.

> **Aviso:** os dados e eventos exibidos nesta versão são sintéticos e servem apenas para demonstração. Não representam casos reais e não devem embasar decisões clínicas, administrativas ou judiciais.

## Funcionalidades

- Acesso separado para perfis de gestão e paciente.
- Filtros, indicadores, visualizações e tabelas da base demonstrativa.
- Acompanhamento ilustrativo de processos e geração de relatório em PDF.
- CPF mascarado na interface e exportação padrão sem identificadores diretos do paciente.

## Executar no Windows

Com Python instalado, abra um terminal nesta pasta e execute:

```powershell
py -m pip install -r requirements.txt
py -m streamlit run app.py
```

Para criar uma conta inicial de gestor, se necessário:

```powershell
py criar_gestor.py
```

Consulte [README_EXECUTAR.md](./README_EXECUTAR.md) para detalhes de execução e configuração de e-mail.

## Estrutura

- `app.py`: inicialização e composição da aplicação.
- `dashboard/`: componentes visuais, gráficos e páginas.
- `petsus/auth/`: autenticação e cadastro.
- `petsus/data/`: carregamento, filtros e métricas.
- `petsus/dashboard/`: navegação e serviços do dashboard.
- `petsus/reports/`: geração de relatórios.
- `tests/`: testes automatizados.
- `dados_dashboard_saude.xlsx`: base sintética usada na demonstração.

Consulte [DICIONARIO_PETSUS.md](./DICIONARIO_PETSUS.md) para a descrição dos campos da base.
