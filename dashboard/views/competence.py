from __future__ import annotations

from .shared import (
    _cards,
    _cost_definitions,
    _distribution,
    _medication_subset,
    _plot,
    _rate,
    _table,
    br_money,
    chart_layout,
    escape,
    go,
    pd,
    protected_aggregate,
    section_title,
    semantic_color,
    st,
)


def _render_responsibility_detail(dff):
    with st.container(border=True, key="manager_panel_responsabilidade_por_processo"):
        section_title("Responsabilidade indicada por processo")
        st.caption("Consulta operacional para apoiar a revisão do ente responsável. A indicação vem do cadastro e precisa de avaliação jurídica antes da definição das partes da ação.")
        rows = dff.drop_duplicates("processo_id").copy()
        ids = rows["processo_id"].astype(str)
        selected = st.selectbox("Consultar responsabilidade do processo", ids.tolist(), index=None,
            placeholder="Selecione ou digite o número do processo", key="competency_process")
        if selected is None:
            return
        process = rows.loc[ids.eq(selected)].iloc[0]
        entity = str(process.get("ente_responsavel", "Não informado"))
        messages = {
            "Município": "Responsabilidade municipal indicada. Conferir as atribuições e o fluxo aplicável ao pedido.",
            "Estado": "Responsabilidade estadual indicada. Revisar o encaminhamento ao Estado, evitando atribuir o atendimento exclusivamente ao Município sem análise do caso.",
            "União": "Responsabilidade da União indicada. Revisar a participação do ente federal e o fluxo de atendimento aplicável.",
            "Compartilhada": "Responsabilidade compartilhada indicada. Identificar os entes envolvidos e pactuar as atribuições; o cadastro não detalha a participação de cada um.",
        }
        st.markdown(f"**Processo:** {escape(str(selected))}")
        st.metric("Ente responsável indicado", entity if entity in messages else "Não informado")
        st.info(messages.get(entity, "Não há classificação suficiente para indicar o ente responsável. Encaminhe o registro para revisão."))
        for label, column in [("Item demandado", "item_demandado"), ("Réu sugerido no cadastro", "reu_sugerido"), ("Dispensação administrativa", "ente_dispensacao_simulado"), ("Competência judicial", "competencia_petsus")]:
            value = process.get(column)
            if pd.notna(value) and str(value).strip():
                st.markdown(f"**{label}:** {escape(str(value))}")
        st.caption("Responsabilidade administrativa, réu sugerido e competência judicial são campos distintos. Esta consulta não determina automaticamente contra quem propor a ação.")


def _render_competency(dff):
    st.info("Responsabilidade administrativa pelo fornecimento e competência judicial são dimensões diferentes.")
    if "ente_responsavel" in dff:
        _cards([
            (ente, _rate(dff, dff["ente_responsavel"].eq(ente)), "percentual de todos os processos filtrados; responsabilidade indicada", "🏛", "icon-blue")
            for ente in ["Município", "Estado", "União", "Compartilhada"]
        ])
        _distribution(dff, "ente_responsavel", "Ente responsável pela demanda", height=290)
        shared = dff["ente_responsavel"].isin(["Estado", "União", "Compartilhada"])
        _cards([("Participação de outros entes", _rate(dff, shared), "Estado, União ou responsabilidade compartilhada ÷ processos filtrados; indica casos para revisão da atribuição exclusiva ao Município", "🏛", "icon-blue")])
        _render_responsibility_detail(dff)
    med = _medication_subset(dff)
    if med is None:
        return
    _cards([
        ("Justiça Federal", _rate(med, med["competencia_petsus"].eq("Justiça Federal")), "percentual das demandas de medicamentos; simulação", "🏛", "icon-blue"),
        ("Justiça Estadual", _rate(med, med["competencia_petsus"].eq("Justiça Estadual")), "percentual das demandas de medicamentos; simulação", "⚖", "icon-green"),
        ("Valor da causa estimado", br_money(med["valor_causa_estimado"].sum()), "estimativa processual, não custo executado", "$", "icon-purple"),
    ])
    _cost_definitions()
    if {"salario_minimo_ajuizamento", "limite_210_sm_ajuizamento"}.issubset(med.columns):
        with st.container(border=True, key="manager_panel_referencia_temporal_da_simulacao"):
            section_title("Referência temporal da simulação")
            temporal = med.assign(ano=pd.to_datetime(med["data_ajuizamento"]).dt.year)
            limits = protected_aggregate(temporal, ["ano"], salario_minimo_ajuizamento=("salario_minimo_ajuizamento", "first"), limite_210_sm_ajuizamento=("limite_210_sm_ajuizamento", "first"))
            _table(limits[["ano", "salario_minimo_ajuizamento", "limite_210_sm_ajuizamento", "processos"]], height=200)
            st.caption("O cálculo compara o valor anual com 210 salários mínimos do ano do ajuizamento de cada processo; não aplica um valor de 2026 a processos de 2024/2025. Critério sujeito a revisão jurídica conforme as normas aplicáveis e o caso concreto.")
    a, b = st.columns(2)
    with a:
        _distribution(med, "competencia_petsus", "Competência judicial")
    with b:
        with st.container(border=True, key="manager_panel_competencia_e_incorporacao_a_rename"):
            section_title("Competência e incorporação à RENAME")
            cross = protected_aggregate(med, ["rename_incorporado", "competencia_petsus"])
            fig = go.Figure()
            for name in ["Justiça Federal", "Justiça Estadual"]:
                values = cross[cross["competencia_petsus"].eq(name)]
                fig.add_trace(go.Bar(x=values["rename_incorporado"], y=values["processos"], name=name, marker_color=semantic_color(name), text=values["processos"], textposition="auto"))
            fig.update_layout(**chart_layout(height=340, showlegend=True, legend=dict(orientation="h", y=1.12, x=0)), barmode="stack")
            fig.update_xaxes(title="Incorporado à lista RENAME")
            fig.update_yaxes(title="Demandas de medicamentos", rangemode="tozero")
            _plot(fig, key="competency:rename_cross")
    with st.container(border=True, key="manager_panel_responsabilidade_administrativa_e_judicial_simuladas"):
        section_title("Responsabilidade administrativa e judicial")
        groups = [column for column in ["componente_sus", "ente_dispensacao_simulado", "ente_responsavel", "competencia_petsus"] if column in med]
        table = protected_aggregate(med, groups)
        _table(table[groups + ["processos", "pacientes"]])


def render_competence(dff, base, k, participacao, part_custo, paciente_ids_sel):
    return _render_competency(dff)
