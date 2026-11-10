from __future__ import annotations

from .shared import (
    _cards,
    _count,
    _ranking,
    _rate,
    _table,
    br_float,
    br_int,
    pct,
    protected_aggregate,
    section_title,
    st,
)


def _render_demands(dff, k):
    _cards([
        ("Processos Urgentes", _count(dff, dff["urgente"].eq("Sim")), "pedidos de análise urgente; não equivale a concessão de liminar", "🔔", "icon-orange"),
        ("Taxa de Liminares", _rate(dff, dff["liminar"].eq("Sim")), "liminares concedidas ÷ processos no recorte", "⚖", "icon-purple"),
        ("Itens Distintos", br_int(dff["item_demandado"].nunique()), "medicamentos, procedimentos e serviços", "💊", "icon-blue"),
    ])
    with st.expander("Como interpretar liminares, urgência e desfecho"):
        st.markdown(
            "**Liminares concedidas:** decisões provisórias favoráveis registradas. "
            "Percentual = processos com liminar concedida ÷ todos os processos do recorte × 100. "
            "A marcação ‘Não’ não permite distinguir pedido indeferido, ainda não analisado ou não apresentado; "
            "por isso, este indicador não é a taxa de deferimento entre pedidos de liminar.\n\n"
            "**Processos urgentes:** quantidade de processos com pedido de análise urgente registrado. "
            "Essa marcação não identifica automaticamente pedido de tutela, classificação processual de prioridade "
            "ou risco assistencial comprovado. Não significa que houve concessão de liminar.\n\n"
            "**Desfecho:** resultado judicial registrado, separado da fase processual e da entrega do tratamento. "
            "Procedente = pedido acolhido integralmente; parcialmente procedente = acolhido em parte; "
            "improcedente = pedido rejeitado; acordo = solução acordada entre as partes; "
            "extinto = processo encerrado conforme o registro, sem presumir vitória ou derrota; "
            "em andamento = sem resultado final registrado. Recurso é uma etapa processual e não um desfecho; "
            "a existência de decisão não comprova trânsito em julgado."
        )
        st.caption("Todos os indicadores consideram os filtros selecionados. Contagens e percentuais que exponham grupos pequenos são protegidos.")
    a, b = st.columns(2)
    with a:
        with st.container(border=True, key="manager_panel_demandas_por_tipo_e_fase_processual"):
            section_title("Demandas por tipo e fase processual")
            phase = protected_aggregate(dff, ["tipo_demanda", "fase_processual"])
            if not phase.empty:
                phase["% do recorte"] = phase["processos"].map(lambda value: f"{br_float(pct(value, len(dff)))}%")
            _table(phase[["tipo_demanda", "fase_processual", "processos", "pacientes", "% do recorte"]] if not phase.empty else phase)
    with b:
        _ranking(dff, "especialidade", "Especialidades mais acionadas", separate=True)
    with st.container(border=True, key="manager_panel_causas_da_judicializacao_e_oportunidades_de_gestao"):
        section_title("Causas da judicialização e oportunidades de gestão")
        if "causa_judicializacao" not in dff:
            st.info("A causa da judicialização ainda não foi informada nesta base.")
        else:
            causes = protected_aggregate(dff, ["causa_judicializacao"])
            causes["% dos processos do recorte"] = causes["processos"].map(lambda value: f"{br_float(pct(value, len(dff)))}%")
            actions = {
                "Falta de oferta": "Avaliar cobertura e capacidade da rede de atendimento.",
                "Falta pontual de medicamento": "Revisar estoque, compra e reposição do medicamento.",
                "Falta de prestador": "Verificar contratação e disponibilidade de prestadores.",
                "Ausência de vaga": "Revisar capacidade, fila e alternativas de atendimento.",
                "Demora na regulação": "Revisar fila, prioridade e prazo de encaminhamento.",
                "Negativa administrativa": "Revisar o motivo da negativa e os critérios de acesso.",
                "Falha de comunicação": "Confirmar orientação e canais de contato com o usuário.",
                "Falta de encaminhamento adequado": "Corrigir o encaminhamento e acompanhar sua aceitação.",
                "Demanda de competência de outro ente": "Articular encaminhamento ao ente responsável e acompanhar retorno.",
                "Serviço disponível, mas não acessado": "Verificar barreiras de agendamento, transporte e informação.",
                "Aguardando fluxo regular": "Informar o prazo e avaliar a necessidade de revisão do atendimento.",
            }
            causes["Ação sugerida à gestão"] = causes["causa_judicializacao"].map(actions).fillna("Revisar a classificação e identificar a barreira de acesso.")
            _table(causes[["causa_judicializacao", "processos", "pacientes", "% dos processos do recorte", "Ação sugerida à gestão"]].sort_values("processos", ascending=False), height=460)
            st.caption("Motivo registrado para o acesso à Justiça, sujeito à conferência da equipe. As ações são sugestões de investigação administrativa, sem presumir causalidade ou dispensar a análise individual. Percentuais usam todos os processos do recorte; grupos protegidos podem não aparecer.")


def render_demands(dff, base, k, participacao, part_custo, paciente_ids_sel):
    return _render_demands(dff, k)
