from __future__ import annotations

from html import escape
import re

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from .charts import barh, chart_layout, distribution_bar, empty_fig, monthly_line, semantic_color, top_group
from .theme import apply_chart_appearance
from .ui import br_float, br_int, br_money, insight_card, metric_card, pct, section_title, to_excel_bytes
from petsus.reports.process_tracking_pdf import build_process_tracking_pdf
from petsus.data.prevention import PREVENTION_ACTIONS

MIN_PATIENTS = 5
JUDICIAL_TRACK = (
    "Documentação preparada", "Processo protocolado", "Processo distribuído",
    "Análise técnica", "Aguardando decisão", "Decisão judicial",
    "Órgão responsável intimado", "Cumprimento em acompanhamento", "Sentença",
    "Recursos / trânsito em julgado / encerramento",
)

LABELS = {
    "processo_id": "Processo", "paciente_id": "Código do paciente", "paciente": "Paciente", "cpf": "CPF mascarado",
    "municipio": "Município", "uf": "UF", "regiao": "Região", "natureza": "Natureza da ação",
    "tipo_demanda": "Tipo de demanda", "fase_processual": "Fase processual", "desfecho": "Desfecho",
    "especialidade": "Especialidade", "item_demandado": "Item demandado", "condicao_clinica": "Condição clínica",
    "medicamento_dcb": "Princípio ativo (DCB)", "cid": "Código do diagnóstico (CID)",
    "rename_incorporado": "Incorporado à lista RENAME", "componente_sus": "Componente da assistência farmacêutica",
    "grupo_sus": "Grupo de financiamento SUS", "apresentacao_padronizada": "Apresentação do medicamento",
    "pcdt_aplicavel": "Protocolo clínico aplicável", "pcdt_referencia": "Protocolo clínico de referência",
    "dose_prescrita": "Dose prescrita", "frequencia_administracao": "Frequência de administração",
    "duracao_meses": "Duração (meses)", "pmvg_referencia": "Preço estimado por administração (R$)",
    "valor_anual_tratamento": "Tratamento estimado para 12 meses (R$)", "valor_causa_estimado": "Valor estimado da causa (R$)",
    "competencia_petsus": "Competência judicial", "reu_sugerido": "Réu sugerido",
    "ente_responsavel": "Ente responsável", "ente_dispensacao_simulado": "Dispensação administrativa",
    "processos": "Processos", "pacientes": "Pacientes distintos", "custo_total": "Custo estimado dos processos (R$)",
    "custo_medio": "Custo médio por processo (R$)", "tempo_medio": "Tempo médio (dias)",
    "custo_mediano": "Mediana do custo (R$)", "custo_q1": "1º quartil do custo (R$)", "custo_q3": "3º quartil do custo (R$)",
    "valor_anual": "Tratamentos estimados para 12 meses (R$)", "valor_causa": "Valor estimado das causas (R$)",
    "causa_judicializacao": "Causa da judicialização", "motivo_potencialmente_evitavel": "Ação administrativa sugerida",
    "faixa_etaria": "Faixa etária", "sexo": "Sexo", "faixa_custo": "Faixa de custo acumulado por paciente",
    "custo_estimado": "Custo estimado (R$)", "freq": "Frequência", "dcb": "Princípio ativo",
    "data_ajuizamento": "Data de ajuizamento", "salario_minimo_ajuizamento": "Salário mínimo no ajuizamento (R$)",
    "limite_210_sm_ajuizamento": "Limite de 210 salários no ajuizamento (R$)", "ano": "Ano do ajuizamento",
}


def mask_cpf(value: object) -> str:
    digits = re.sub(r"\D", "", str(value))
    return f"{digits[:3]}.***.***-{digits[-2:]}" if len(digits) == 11 else "Não informado"


def mask_personal_data(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()
    for column in result.columns:
        if "cpf" in str(column).lower():
            result[column] = result[column].map(mask_cpf)
    return result


def protected_aggregate(df: pd.DataFrame, groups: list[str], **extra) -> pd.DataFrame:
    """Publica somente células com >=5 pacientes; evita reconstrução de célula única.

    A contagem é de pessoas distintas, nunca de linhas/processos. Quando há uma
    única célula pequena, a menor célula publicável também é suprimida.
    """
    aggregations = dict(processos=("processo_id", "count"), pacientes=("paciente_id", "nunique"))
    for name, column, op in [
        ("custo_total", "custo_estimado", "sum"), ("custo_medio", "custo_estimado", "mean"),
        ("tempo_medio", "tempo_tramitacao_dias", "mean"),
    ]:
        if column in df:
            aggregations[name] = (column, op)
    aggregations.update(extra)
    result = df.groupby(groups, dropna=False, observed=True).agg(**aggregations).reset_index()
    safe = result["pacientes"] >= MIN_PATIENTS
    if (~safe).sum() == 1 and safe.any():
        safe.loc[result.loc[safe, "pacientes"].idxmin()] = False
    suppressed = bool((~safe).any())
    result = result.loc[safe].copy()
    result.attrs["small_cells_suppressed"] = suppressed
    return result


def judgment_summary(df: pd.DataFrame) -> dict:
    counts = df["desfecho"].value_counts()
    full = int(counts.get("Procedente", 0))
    partial = int(counts.get("Parcialmente procedente", 0))
    rejected = int(counts.get("Improcedente", 0))
    judged = full + partial + rejected
    return {
        "julgados": judged, "procedentes": full, "parciais": partial,
        "procedencia": 100 * full / judged if judged else None,
        "procedencia_parcial": 100 * partial / judged if judged else None,
        "pendentes": int(counts.get("Em andamento", 0)),
        "acordos": int(counts.get("Acordo", 0)),
        "outros": len(df) - judged - int(counts.get("Em andamento", 0)) - int(counts.get("Acordo", 0)),
    }


def _publishable_subset(df: pd.DataFrame, mask: pd.Series) -> bool:
    return all(count == 0 or count >= MIN_PATIENTS for count in (
        df.loc[mask, "paciente_id"].nunique(), df.loc[~mask, "paciente_id"].nunique(),
    ))


def _rate(df: pd.DataFrame, mask: pd.Series) -> str:
    if df.empty:
        return "Não se aplica"
    if not _publishable_subset(df, mask):
        return "Suprimido"
    return f"{br_float(pct(mask.sum(), len(df)))}%"


def _count(df: pd.DataFrame, mask: pd.Series) -> str:
    return br_int(mask.sum()) if _publishable_subset(df, mask) else "Suprimido"


def _cards(cards) -> None:
    for column, card in zip(st.columns(len(cards)), cards):
        with column:
            metric_card(*card)


def _plot(fig, *, key: str) -> None:
    apply_chart_appearance(fig, contrast=st.session_state.get("a11y_contrast", False), large_text=st.session_state.get("a11y_large_text", False))
    st.plotly_chart(fig, key=key, use_container_width=True, theme=None, config={"displayModeBar": False, "responsive": True, "scrollZoom": False, "locale": "pt-BR"})


def _table(df: pd.DataFrame, height: int = 350) -> None:
    view = mask_personal_data(df).rename(columns=LABELS)
    if view.empty:
        st.info("Nenhuma célula publicável neste recorte. Grupos com menos de 5 pacientes distintos são protegidos.")
        return
    view = view.rename(columns={column: str(column).replace("_", " ").capitalize() for column in view if "_" in str(column)})
    config = {column: st.column_config.Column(column, width="large") for column in view}
    for column in view:
        if column.endswith("(R$)") or "PMVG" in column:
            config[column] = st.column_config.NumberColumn(column, format="R$ %.2f", width="large")
        elif pd.api.types.is_numeric_dtype(view[column]):
            config[column] = st.column_config.NumberColumn(column, format="%.1f" if "dias" in column else "%d", width="medium")
    st.dataframe(view, hide_index=True, use_container_width=True, height=height, row_height=40, column_config=config)


def _distribution(df, column, title, height=340, patients=False):
    with st.container(border=True, key=f"manager_panel_distribution_{column}_{title}"):
        section_title(title)
        agg = protected_aggregate(df, [column])
        value = "pacientes" if patients else "processos"
        denominator = df["paciente_id"].nunique() if patients else len(df)
        _plot(distribution_bar(agg, column, value, denominator=denominator, height=height), key=f"distribution:{column}:{title}")
        st.caption(f"Percentuais sobre {br_int(denominator)} {'pacientes distintos' if patients else 'processos'} no recorte; células protegidas podem não ser exibidas.")


def _ranking(df, column, title, value="processo_id", op="count", height=350, separate=False):
    with st.container(border=True, key=f"manager_panel_ranking_{column}_{op}_{title}"):
        section_title(title)
        grouped = top_group(df, column, value, 10, op)
        grouped["texto"] = grouped["valor"].map(br_money if op in {"sum", "mean"} else br_int)
        _plot(barh(grouped, column, "valor", "texto", height=height, color="#239B56" if op == "sum" else "#125CC9", separate_dominant=separate), key=f"ranking:{column}:{value}:{op}:{title}")


def tracking_bar(title: str, stages, current: int, color: str) -> None:
    help_text = (
        "Andamento do processo no Judiciário, da preparação dos documentos ao encerramento."
        if title.startswith("Trilha A") else
        "Cumprimento prático pela saúde: disponibilidade, aquisição, comunicação e entrega ou realização."
    )
    items = []
    for index, name in enumerate(stages, start=1):
        state = "done" if index < current else "current" if index == current else "pending"
        marker = "✓" if index < current else str(index)
        items.append(f'<div class="flow-step {state}" style="--track-color:{color}"><div class="flow-marker">{marker}</div><div class="flow-label">{escape(str(name))}</div></div>')
    st.markdown(
        f'<div class="flow-title">{escape(title)}<span class="card-help" tabindex="0" role="img" aria-label="Ajuda: {escape(help_text, quote=True)}" data-help="{escape(help_text, quote=True)}">?</span></div><div class="flow-track">' + "".join(items) + "</div>",
        unsafe_allow_html=True,
    )


def render_pages(pagina, dff, base, k, participacao, part_custo, paciente_ids_sel, auth_store=None):
    auth_state = st.session_state.get("auth_user", {})
    role = auth_state.get("role") if isinstance(auth_state, dict) else None
    if role != "gestor":
        st.error("Esta visão analítica é restrita a gestores.")
        return
    if pagina == "Gestão interna":
        if not isinstance(auth_state, dict) or auth_state.get("role") != "gestor" or auth_store is None:
            st.error("Esta página é restrita a gestores.")
            return
        from petsus.dashboard.internal_management import render_internal_management
        render_internal_management(auth_store)
        return
    if dff.empty:
        st.info("Nenhum processo encontrado para os filtros selecionados.")
        return
    if pagina == "Andamento":
        _render_tracking(dff)
        return
    if dff["paciente_id"].nunique() < MIN_PATIENTS:
        st.warning("Recorte protegido: são necessários pelo menos 5 pacientes distintos para exibir indicadores, gráficos, tabelas ou exportações. Amplie os filtros.")
        return
    st.caption("Privacidade: células com menos de 5 pacientes distintos são suprimidas; uma segunda célula pode ser protegida para impedir reconstrução por subtração. As exportações seguem a mesma regra.")
    if pagina == "Visão Geral":
        _render_overview(dff, base, k, participacao, part_custo)
    elif pagina == "Demandas":
        _render_demands(dff, k)
    elif pagina == "Medicamentos":
        _render_medications(dff)
    elif pagina == "Competência":
        _render_competency(dff)
    elif pagina == "Custos":
        _render_costs(dff, k, part_custo)
    elif pagina == "Geografia":
        _render_geography(dff, k)
    elif pagina == "Pacientes":
        _render_patients(dff)
    elif pagina in {"Prevenção", "Prevenção de Judicialização", "Prevenção de judicialização"}:
        _render_prevention(dff)
    elif pagina == "Base de Dados":
        _render_database(dff)


def _render_overview(dff, base, k, participacao, part_custo):
    result = judgment_summary(dff)
    judged = dff[dff["desfecho"].isin(["Procedente", "Parcialmente procedente", "Improcedente"])]
    rate = _rate(judged, judged["desfecho"].eq("Procedente")) if result["julgados"] else "Não se aplica"
    _cards([
        ("Total de Processos", br_int(len(dff)), f"{br_float(participacao)}% da base; unidade: processo", "📄", "icon-blue"),
        ("Pacientes Ativos", br_int(dff["paciente_id"].nunique()), "pessoas distintas com processo no recorte", "👥", "icon-green"),
        ("Custo Total", br_money(dff["custo_estimado"].sum()), f"{br_float(part_custo)}% do custo estimado da base", "$", "icon-green"),
        ("Tempo Médio", f"{br_int(dff['tempo_tramitacao_dias'].mean())} dias", "soma dos tempos ÷ processos do recorte", "⏱", "icon-orange"),
        ("Taxa de Procedência", rate, "somente procedentes ÷ julgados de mérito", "⚖", "icon-purple"),
    ])
    st.caption("Tempo de tramitação: do ajuizamento ao julgamento ou desfecho registrado; nos casos em andamento, até a data de referência dos cálculos. A média usa todos os processos do recorte.")
    with st.container(border=True, key="manager_panel_como_interpretar_os_resultados"):
        section_title("Como interpretar os resultados")
        _cards([
            ("Parcialmente procedentes", _rate(judged, judged["desfecho"].eq("Parcialmente procedente")) if result["julgados"] else "Não se aplica", "parcialmente procedentes ÷ julgados de mérito", "◐", "icon-orange"),
            ("Pendentes de julgamento", _count(dff, dff["desfecho"].eq("Em andamento")), "em andamento; fora do denominador de procedência", "⌛", "icon-blue"),
            ("Acordos", _count(dff, dff["desfecho"].eq("Acordo")), "composição entre as partes; fora da taxa", "🤝", "icon-purple"),
        ])
        denominator = _count(dff, dff["desfecho"].isin(["Procedente", "Parcialmente procedente", "Improcedente"]))
        st.caption(f"Denominador dos percentuais de mérito: {denominator} processos julgados no recorte.")
        st.caption("Julgados de mérito = Procedente + Parcialmente procedente + Improcedente. Acordos, extinções, recursos sem julgamento registrado e processos em andamento não entram na taxa. Sem julgados, a taxa não se aplica. Resultado favorável não significa entrega do tratamento.")
    a, b = st.columns([1.4, 1])
    with a:
        with st.container(border=True, key="manager_panel_evolucao_mensal_dos_processos"):
            section_title("Evolução mensal dos processos")
            _plot(monthly_line(dff.assign(qtd=1), "qtd", "Processos"), key="overview:monthly_processes")
    with b:
        _distribution(dff, "desfecho", "Desfecho processual")
    a, b = st.columns(2)
    with a:
        _distribution(dff, "natureza", "Natureza da ação")
    with b:
        _ranking(dff, "item_demandado", "Itens mais demandados", separate=True)


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


def _medication_subset(dff):
    med = dff[dff["medicamento_petsus"].eq("Sim")].copy()
    med["componente_sus"] = med["componente_sus"].replace({
        "CBAF": "Assistência básica (CBAF)", "CEAF": "Assistência especializada (CEAF)",
        "CESAF": "Assistência estratégica (CESAF)", "AF Onco": "Assistência oncológica",
    })
    st.info("Consulte medicamentos, protocolos, custos e responsabilidades administrativas. Confirme a disponibilidade com a rede de saúde e as informações jurídicas com o órgão responsável.")
    if med["paciente_id"].nunique() < MIN_PATIENTS:
        st.info("Nenhum grupo de medicamentos publicável com estes filtros. São necessários pelo menos 5 pacientes distintos.")
        return None
    st.caption(f"Denominador desta análise: {br_int(len(med))} demandas de medicamentos, de {br_int(med['paciente_id'].nunique())} pacientes distintos; não é o total de processos de outras naturezas.")
    return med


def _cost_definitions():
    st.caption("Os três valores medem conceitos diferentes e não devem ser somados: custo estimado dos processos = estimativa do atendimento judicializado; tratamento para 12 meses = projeção anual; valor da causa = estimativa processual. Nenhum comprova gasto executado. O preço estimado por administração é valor anual dividido pelo número de administrações anuais; não é cotação oficial PMVG. Uma cotação CMED exige apresentação e quantidade de unidades.")


def _render_medications(dff):
    med = _medication_subset(dff)
    if med is None:
        return
    _cards([
        ("Demandas de medicamentos", br_int(len(med)), "denominador: demandas de medicamentos filtradas", "💊", "icon-blue"),
        ("DCB distintos", br_int(med["medicamento_dcb"].nunique()), "princípios ativos; não apresentações", "🧪", "icon-purple"),
        ("Incorporados à RENAME", _rate(med, med["rename_incorporado"].eq("Sim")), "demandas incorporadas ÷ demandas de medicamentos", "✓", "icon-green"),
        ("Valor anual estimado", br_money(med["valor_anual_tratamento"].sum()), "projeção de 12 meses; não gasto executado", "📈", "icon-green"),
    ])
    _cost_definitions()
    a, b = st.columns(2)
    with a:
        _distribution(med, "rename_incorporado", "Incorporação à lista RENAME")
    with b:
        _distribution(med, "pcdt_aplicavel", "Existência de protocolo clínico (PCDT)")
    with st.container(border=True, key="manager_panel_assistencia_farmaceutica_e_dispensacao_administrativa"):
        section_title("Assistência farmacêutica e dispensação administrativa")
        st.write("Compare quantos processos solicitam medicamentos da assistência básica, especializada e dos demais componentes. O ente de dispensação é apresentado conforme o cadastro do medicamento.")
        groups = ["componente_sus"]
        if "ente_dispensacao_simulado" in med:
            groups.append("ente_dispensacao_simulado")
        comp = protected_aggregate(med, groups)
        # Zero é ausência de casos, não uma célula pequena: mantém visível a
        # comparação entre assistência básica, especializada e estratégica.
        for component, dispensing in [
            ("Assistência básica (CBAF)", "Município"),
            ("Assistência especializada (CEAF)", "Estado"),
            ("Assistência estratégica (CESAF)", "Compartilhada"),
        ]:
            if not med["componente_sus"].eq(component).any():
                row = {"componente_sus": component, "processos": 0, "pacientes": 0}
                if "ente_dispensacao_simulado" in groups:
                    row["ente_dispensacao_simulado"] = "Não se aplica — sem demandas"
                comp = pd.concat([comp, pd.DataFrame([row])], ignore_index=True)
        comp["% das demandas de medicamentos"] = comp["processos"].map(lambda value: f"{br_float(pct(value, len(med)))}%")
        _table(comp[groups + ["processos", "pacientes", "% das demandas de medicamentos"]])
        st.caption("Assistência básica, especializada e estratégica são componentes distintos. A dispensação administrativa identifica quem organiza o fornecimento e pode envolver pactuação entre entes. Ela não define automaticamente o réu nem a competência judicial.")
        st.caption("O percentual usa todas as demandas de medicamentos dos filtros atuais. Grupos com poucos pacientes são protegidos e, por isso, as linhas visíveis podem não somar 100%.")
    with st.container(border=True, key="manager_panel_classificacao_por_medicamento"):
        section_title("Classificação e dispensação por medicamento")
        groups = ["medicamento_dcb", "rename_incorporado", "componente_sus"]
        if "ente_dispensacao_simulado" in med:
            groups.append("ente_dispensacao_simulado")
        classification = protected_aggregate(med, groups)
        classification["% das demandas de medicamentos"] = classification["processos"].map(lambda value: f"{br_float(pct(value, len(med)))}%")
        _table(classification[groups + ["processos", "pacientes", "% das demandas de medicamentos"]].sort_values("processos", ascending=False), height=460)
        with st.expander("Como interpretar a classificação do medicamento"):
            st.markdown(
                "**RENAME:** Relação Nacional de Medicamentos Essenciais. A coluna mostra a incorporação informada no cadastro.\n\n"
                "**Assistência básica (CBAF):** Componente Básico da Assistência Farmacêutica.\n\n"
                "**Assistência especializada (CEAF):** Componente Especializado da Assistência Farmacêutica.\n\n"
                "**Assistência estratégica (CESAF):** Componente Estratégico da Assistência Farmacêutica.\n\n"
                "**Dispensação administrativa:** ente indicado no cadastro para organizar o fornecimento. "
                "Confirme o fluxo com a rede de saúde, considerando o medicamento, o protocolo e a pactuação local. "
                "Esse campo é separado da competência judicial, que indica qual ramo da Justiça analisa o processo."
            )
    a, b = st.columns(2)
    with a:
        _ranking(med, "medicamento_dcb", "Princípios ativos mais demandados")
    with b:
        _ranking(med, "medicamento_dcb", "Projeção de 12 meses por princípio ativo", "valor_anual_tratamento", "sum")
    with st.container(border=True, key="manager_panel_estimativa_sintetica_de_preco_por_administracao"):
        section_title("Estimativa de preço por administração")
        detail = protected_aggregate(med, ["medicamento_dcb", "apresentacao_padronizada"],
            preco_minimo=("pmvg_referencia", "min"), preco_maximo=("pmvg_referencia", "max"),
            valor_anual=("valor_anual_tratamento", "sum"))
        detail = detail.rename(columns={"preco_minimo": "Menor preço estimado por administração (R$)", "preco_maximo": "Maior preço estimado por administração (R$)"})
        _table(detail[["medicamento_dcb", "apresentacao_padronizada", "processos", "Menor preço estimado por administração (R$)", "Maior preço estimado por administração (R$)", "valor_anual"]])
        st.caption("Cenários agrupados pelo mesmo item e apresentação. Os preços derivam da projeção anual; não são consulta à CMED nem PMVG médio entre medicamentos.")


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


def _render_costs(dff, k, part_custo):
    _cards([
        ("Custo Total", br_money(dff["custo_estimado"].sum()), "estimativa por processo; não gasto executado", "$", "icon-green"),
        ("Ticket Médio", br_money(dff["custo_estimado"].mean()), "soma estimada ÷ processos do recorte", "🧾", "icon-blue"),
        ("Custo Medicamentos", br_money(dff.loc[dff["natureza"].eq("Medicamentos"), "custo_estimado"].sum()) if _publishable_subset(dff, dff["natureza"].eq("Medicamentos")) else "Suprimido", "custo estimado de processos de medicamentos no período", "💊", "icon-purple"),
    ])
    _cost_definitions()
    a, b = st.columns(2)
    with a:
        with st.container(border=True, key="manager_panel_evolucao_mensal_do_custo_estimado"):
            section_title("Evolução mensal do custo estimado")
            _plot(monthly_line(dff, "custo_estimado", "Custo estimado", money=True, height=350), key="costs:monthly_cost")
    with b:
        _ranking(dff, "esfera", "Custo estimado por esfera judicial", "custo_estimado", "sum")
    a, b = st.columns(2)
    with a:
        _ranking(dff, "item_demandado", "Itens com maior impacto financeiro", "custo_estimado", "sum")
    with b:
        _ranking(dff, "especialidade", "Custo estimado por especialidade", "custo_estimado", "sum")
    with st.container(border=True, key="manager_panel_custo_tipico_e_dispersao_por_natureza"):
        section_title("Custo típico e dispersão por natureza")
        summary = protected_aggregate(dff, ["natureza"], custo_mediano=("custo_estimado", "median"), custo_q1=("custo_estimado", lambda values: values.quantile(.25)), custo_q3=("custo_estimado", lambda values: values.quantile(.75)))
        _table(summary[["natureza", "processos", "pacientes", "custo_mediano", "custo_q1", "custo_q3"]])
        st.caption("Mediana: metade dos processos custa até esse valor. Do 1º ao 3º quartil está a metade central dos custos (intervalo interquartil). A tabela usa todos os processos publicáveis, sem amostragem e sem misturar média com distribuição.")


def _render_geography(dff, k):
    _cards([
        ("Municípios", br_int(dff["municipio"].nunique()), "municípios no recorte", "📍", "icon-blue"),
        ("Custo por paciente", br_money(dff["custo_estimado"].sum() / dff["paciente_id"].nunique()), "estimativa ÷ pacientes distintos filtrados; não população municipal", "$", "icon-green"),
    ])
    geo = protected_aggregate(dff, ["municipio", "uf", "regiao", "latitude", "longitude"])
    a, b = st.columns([1.4, 1])
    with a:
        with st.container(border=True, key="manager_panel_municipios_com_dados_publicaveis"):
            section_title("Municípios com dados publicáveis")
            if geo.empty:
                _plot(empty_fig(), key="geography:map")
            else:
                fig = px.scatter_geo(geo, lat="latitude", lon="longitude", size="processos", color="regiao", color_discrete_map={region: semantic_color(region) for region in geo["regiao"].unique()}, hover_name="municipio", hover_data={"uf": True, "processos": True, "pacientes": True, "latitude": False, "longitude": False}, labels=LABELS, height=390)
                fig.update_geos(showcountries=True, countrycolor="#CBD5E1", showland=True, landcolor="#F4F7FB", showocean=True, oceancolor="#E8F2FB", fitbounds="locations")
                fig.update_layout(margin=dict(l=0, r=0, t=0, b=0), legend=dict(orientation="h", y=1.02, x=0))
                _plot(fig, key="geography:map")
    with b:
        _ranking(dff, "regiao", "Processos por região", height=390)
    a, b = st.columns(2)
    with a:
        _ranking(dff, "municipio", "Municípios por processos")
    with b:
        _ranking(dff, "municipio", "Municípios por custo estimado", "custo_estimado", "sum")
    with st.container(border=True, key="manager_panel_tabela_geografica_protegida"):
        section_title("Tabela geográfica protegida")
        _table(geo[["regiao", "uf", "municipio", "processos", "pacientes", "custo_total", "custo_medio"]].sort_values("processos", ascending=False))


def _render_patients(dff):
    patients = dff.drop_duplicates("paciente_id").copy()
    _cards([
        ("Pacientes", br_int(len(patients)), "pessoas distintas no recorte", "👥", "icon-green"),
        ("Idade Média", f"{br_float(patients['idade'].mean())} anos", "soma das idades informadas ÷ pacientes com idade", "🎂", "icon-blue"),
        ("% Feminino", _rate(patients, patients["sexo"].eq("Feminino")), "pacientes femininas ÷ pacientes distintos", "♀", "icon-purple"),
    ])
    a, b = st.columns(2)
    with a:
        with st.container(border=True, key="manager_panel_idade_em_intervalos_de_10_anos"):
            section_title("Idade em intervalos de 10 anos")
            ages = pd.to_numeric(patients["idade"], errors="coerce")
            labels = [f"{start} a {start+9}" for start in range(0, 120, 10)]
            patients["faixa_etaria"] = pd.cut(ages, bins=list(range(0, 121, 10)), labels=labels, right=False).astype("string").fillna("Idade não informada")
            patients.loc[ages.ge(120), "faixa_etaria"] = "120 ou mais (intervalo aberto)"
            age_table = protected_aggregate(patients, ["faixa_etaria"])
            age_order = labels + ["120 ou mais (intervalo aberto)", "Idade não informada"]
            age_table = age_table.sort_values("faixa_etaria", key=lambda values: values.map({label: index for index, label in enumerate(age_order)}))
            _plot(distribution_bar(age_table, "faixa_etaria", "pacientes", denominator=len(patients), height=430, preserve_order=True), key="patients:age")
            st.caption("Todos os intervalos fechados cobrem 10 anos completos; eventual categoria de 120 anos ou mais é aberta. Pacientes sem idade válida aparecem em categoria própria. Unidade: paciente distinto.")
    with b:
        _distribution(patients, "sexo", "Distribuição por sexo", height=380, patients=True)
    _ranking(patients, "condicao_clinica", "Condições clínicas mais frequentes")
    with st.container(border=True, key="manager_panel_perfil_socioassistencial"):
        section_title("Perfil socioassistencial")
        rows = []
        for title, column, value in [("SUS exclusivo", "sus_exclusivo", "Sim"), ("Pessoa com deficiência", "pcd", "Sim"), ("Doença rara", "doenca_rara", "Sim"), ("Renda até 1 salário mínimo", "renda_familiar", "Até 1 salário mínimo")]:
            mask = patients[column].eq(value)
            rows.append({"Indicador": title, "Pacientes distintos": _count(patients, mask), "% dos pacientes distintos": _rate(patients, mask)})
        _table(pd.DataFrame(rows), height=220)
    with st.container(border=True, key="manager_panel_distribuicao_do_custo_acumulado_por_paciente"):
        section_title("Distribuição do custo acumulado por paciente")
        totals = dff.groupby("paciente_id", as_index=False)["custo_estimado"].sum()
        totals["processo_id"] = totals["paciente_id"]
        totals["faixa_custo"] = pd.cut(totals["custo_estimado"], bins=[-1, 1000, 10000, 100000, float("inf")], labels=["Até R$ 1 mil", "Mais de R$ 1 mil até R$ 10 mil", "Mais de R$ 10 mil até R$ 100 mil", "Mais de R$ 100 mil"])
        grouped = protected_aggregate(totals, ["faixa_custo"])
        _table(grouped[["faixa_custo", "pacientes", "custo_total"]])
        st.caption("A análise usa faixas com pelo menos 5 pacientes distintos. Nomes, CPFs e rankings individuais não são necessários nesta visão analítica. Para uma consulta operacional autorizada, use Andamento.")


def _render_prevention(dff):
    needed = {"judicializacao_potencialmente_evitavel", "causa_judicializacao"}
    if not needed.issubset(dff.columns):
        st.info("Esta base ainda não tem classificação de prevenção. Não é possível estimar o indicador sem esses dados.")
        return
    mask = dff["judicializacao_potencialmente_evitavel"].eq("Sim")
    classified = dff["judicializacao_potencialmente_evitavel"].isin(["Sim", "Não"])
    _cards([
        ("Judicialização potencialmente evitável", _rate(dff, mask), "processos classificados como potencialmente evitáveis ÷ processos do recorte", "↻", "icon-green"),
        ("Demandas potencialmente evitáveis", _count(dff, mask), "oportunidades de solução administrativa; hipótese de triagem", "📋", "icon-blue"),
        ("Cobertura da classificação", _rate(dff, classified), "processos com classificação informada ÷ processos do recorte", "✓", "icon-purple"),
    ])
    st.info("O indicador identifica barreiras que podem ser avaliadas para solução administrativa ou mediação. A sinalização é potencial: não comprova que a ação poderia ter sido evitada nem restringe o acesso do paciente à Justiça.")
    with st.expander("Como o indicador é calculado e quais motivos são considerados"):
        st.markdown("**Percentual = processos classificados como potencialmente evitáveis ÷ total de processos dos filtros atuais × 100.** Cada processo entra uma vez na contagem. Registros sem classificação permanecem no total, mas não são contados como potencialmente evitáveis; consulte a cobertura para avaliar a completude do cadastro. ‘Não’ significa ausência de sinalização neste critério, sem afirmar que uma solução administrativa seria impossível.")
        criteria = pd.DataFrame(PREVENTION_ACTIONS.items(), columns=["Motivo para triagem", "Encaminhamento a avaliar"])
        st.dataframe(criteria, hide_index=True, use_container_width=True, column_config={column: st.column_config.TextColumn(column, width="large") for column in criteria})
    if not mask.any():
        st.info("Nenhuma demanda está sinalizada como potencialmente evitável nos filtros atuais. Confira a classificação antes de concluir que não há oportunidades de prevenção.")
        return
    with st.container(border=True, key="manager_panel_oportunidades_de_prevencao_por_causa"):
        section_title("Oportunidades de prevenção por causa")
        opportunities = dff.loc[mask].copy()
        groups = ["causa_judicializacao"]
        if "motivo_potencialmente_evitavel" not in opportunities:
            opportunities["motivo_potencialmente_evitavel"] = opportunities["causa_judicializacao"].map(PREVENTION_ACTIONS).fillna("Validar o motivo e definir o encaminhamento com a equipe responsável.")
        groups.append("motivo_potencialmente_evitavel")
        table = protected_aggregate(opportunities, groups)
        table["% de todos os processos filtrados"] = table["processos"].map(lambda value: f"{br_float(pct(value, len(dff)))}%")
        table["% das demandas potencialmente evitáveis"] = table["processos"].map(lambda value: f"{br_float(pct(value, mask.sum()))}%")
        _table(table[groups + ["processos", "pacientes", "% de todos os processos filtrados", "% das demandas potencialmente evitáveis"]].sort_values("processos", ascending=False), height=460)
        st.caption("Priorize os motivos mais recorrentes. Cada linha mostra seu peso no recorte completo e entre as demandas sinalizadas. Grupos pequenos são protegidos; as linhas publicadas podem não somar 100%.")
    with st.container(border=True, key="manager_panel_fluxo_de_prevencao"):
        section_title("Próximos passos para a gestão")
        st.markdown("1. Conferir a causa e a necessidade atual do paciente.\n2. Identificar o serviço ou ente responsável e a pendência de acesso.\n3. Avaliar encaminhamento administrativo ou mediação, com responsável e prazo.\n4. Confirmar o atendimento e acompanhar a resolução da barreira.")
        st.caption("Os números representam oportunidades identificadas, não casos resolvidos ou redução comprovada de ações judiciais.")


def _render_database(dff):
    section_title("Base analítica protegida")
    st.caption("A tabela e os arquivos agrupam os processos por município, natureza e tipo de demanda. Identificadores pessoais e processuais foram retirados desta visão; células pequenas seguem a mesma regra de supressão dos gráficos.")
    table = protected_aggregate(dff, ["municipio", "uf", "natureza", "tipo_demanda"])
    table = table[["municipio", "uf", "natureza", "tipo_demanda", "processos", "pacientes", "custo_total", "custo_medio", "tempo_medio"]].sort_values("processos", ascending=False)
    _table(table, height=520)
    if table.empty:
        return
    exported = mask_personal_data(table).rename(columns=LABELS)
    a, b = st.columns(2)
    with a:
        st.download_button("Baixar CSV protegido", data=exported.to_csv(index=False).encode("utf-8-sig"), file_name="petsus_base_analitica_protegida.csv", mime="text/csv", key="protected_csv")
    with b:
        st.download_button("Baixar Excel protegido", data=to_excel_bytes(exported), file_name="petsus_base_analitica_protegida.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key="protected_excel")


def _render_tracking(dff, user_role="gestor"):
    st.markdown(
        """
        <style>
        .flow-title { display:flex; align-items:center; gap:.5rem; font-size:1.05rem; font-weight:900; color:#0B2459; margin:.7rem 0 .5rem; }
        .flow-title .card-help { margin-left:0; }
        .flow-track { display:grid; grid-template-columns:repeat(5,minmax(0,1fr)); gap:.6rem; margin-bottom:1rem; }
        .flow-step { min-width:0; padding:.65rem .4rem; border:1px solid #DDE6F2; border-radius:13px; background:#F8FAFD; text-align:center; }
        .flow-marker { width:28px; height:28px; border-radius:50%; margin:0 auto .4rem; display:flex; align-items:center; justify-content:center; background:#E5EAF1; color:#667085; font-weight:900; }
        .flow-label { font-size:.74rem; line-height:1.18; color:#667085; font-weight:750; overflow-wrap:anywhere; }
        .flow-step.done { background:#ECFDF3; border-color:#A7E3BC; }
        .flow-step.done .flow-marker { background:#239B56; color:white; }
        .flow-step.current { background:#EEF5FF; border:2px solid var(--track-color); box-shadow:0 4px 12px rgba(18,92,201,.12); }
        .flow-step.current .flow-marker { background:var(--track-color); color:white; }
        .flow-step.current .flow-label { color:#0B2459; }
        [data-testid="stMetricValue"],
        [data-testid="stMetricValue"] > div,
        [data-testid="stMetricValue"] * {
            font-size: clamp(1.05rem, 1.65vw, 1.6rem) !important;
            line-height: 1.15 !important;
            white-space: normal !important;
            overflow: visible !important;
            text-overflow: clip !important;
            overflow-wrap: anywhere !important;
        }
        @media(max-width:900px){.flow-track{grid-template-columns:repeat(2,minmax(0,1fr));}}
        @media(max-width:520px){.flow-track{grid-template-columns:1fr;}}
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.info(
        "Esta demonstração separa o andamento no Judiciário do cumprimento material na saúde. "
        "Uma decisão favorável não significa, por si só, que o medicamento foi entregue ou que a cirurgia foi realizada."
    )

    if dff["paciente_id"].nunique() >= MIN_PATIENTS:
        _cards([
            ("Processos acompanhados", br_int(len(dff)), "processos no recorte", "📋", "icon-blue"),
            ("Cumprimento iniciado", _count(dff, dff["etapa_saude_ordem"].gt(0)), "ordens em execução na saúde", "⚕", "icon-green"),
            ("Prazo vencido", _count(dff, dff["indicador_atraso"].eq("Sim")), "cumprimentos pendentes na data de referência", "!", "icon-orange"),
            ("Uso contínuo", _count(dff, dff["status_andamento"].eq("Tratamento em cumprimento contínuo")), "tratamentos com acompanhamento periódico", "↻", "icon-purple"),
        ])
        with st.container(border=True, key="manager_panel_etapas_judiciais_no_recorte"):
            section_title("Etapas judiciais no recorte")
            judicial_summary = protected_aggregate(dff, ["etapa_judicial"])
            judicial_summary["texto"] = judicial_summary["processos"].map(br_int)
            _plot(barh(judicial_summary, "etapa_judicial", "processos", "texto", height=320, separate_dominant=True), key="tracking:judicial_summary")
        with st.container(border=True, key="manager_panel_cumprimento_na_rede_de_saude"):
            section_title("Cumprimento na rede de saúde")
            st.caption("Processos por etapa registrada na rede de saúde. Os nomes completos aparecem ao passar o mouse sobre cada barra.")
            health_summary = protected_aggregate(dff, ["etapa_saude"])
            health_summary["texto"] = health_summary["processos"].map(br_int)
            _plot(barh(health_summary, "etapa_saude", "processos", "texto", height=380, color="#239B56", separate_dominant=True), key="tracking:health_summary")

    section_title("Consultar um processo")
    process_rows = dff.sort_values("ultima_movimentacao_data", ascending=False).drop_duplicates("processo_id")
    labels = {}
    for row in process_rows.itertuples(index=False):
        patient = f" · {row.paciente}" if user_role != "usuario" else ""
        labels[f"{row.processo_id}{patient} · {row.item_demandado}"] = row.processo_id
    selected_label = st.selectbox("Processo", list(labels), help="Selecione o processo que deseja acompanhar.")
    process = process_rows[process_rows["processo_id"] == labels[selected_label]].iloc[0]

    st.markdown(f"### {escape(str(process['item_demandado']))}")
    st.caption(f"Processo {process['processo_id']} · Fluxo de {process['tipo_fluxo_saude']}")
    if pd.notna(process.get("data_referencia_calculo")):
        st.caption(f"Data de referência dos prazos: {pd.Timestamp(process['data_referencia_calculo']).strftime('%d/%m/%Y')}")
    if pd.notna(process.get("geracao_simulacao")):
        st.caption(f"Simulação gerada para: {pd.Timestamp(process['geracao_simulacao']).strftime('%d/%m/%Y')}")
    if process["status_andamento"] == "Tratamento em cumprimento contínuo":
        st.success("O medicamento foi entregue, mas o acompanhamento continua por se tratar de uso contínuo.")

    j1, j2, j3 = st.columns(3)
    j1.metric("Situação judicial", process["etapa_judicial"])
    j2.metric("Cumprimento na saúde", process["etapa_saude"])
    j3.metric("Status geral", process["status_andamento"])

    st.progress(int(process["percentual_judicial"]), text=f"Andamento judicial: {int(process['percentual_judicial'])}%")
    tracking_bar("Trilha A - andamento judicial", JUDICIAL_TRACK, int(process["etapa_judicial_ordem"]), "#125CC9")

    health_tracks = {
        "Medicamento": ("Ordem recebida", "Análise do cumprimento", "Estoque verificado", "Aquisição", "Produto recebido", "Disponível", "Paciente comunicado", "Medicamento entregue"),
        "Cirurgia": ("Ordem recebida", "Regulação", "Hospital definido", "Pré-operatório", "Autorizada", "Agendada", "Paciente convocado", "Realizada", "Pós-operatório"),
        "Tratamento ou serviço": ("Ordem recebida", "Análise", "Disponibilidade", "Providência administrativa", "Disponibilizado", "Paciente comunicado", "Realizado"),
    }
    health_track = health_tracks[process["tipo_fluxo_saude"]]
    if int(process["etapa_saude_ordem"]) == 0:
        st.info(f"Cumprimento ainda não iniciado: {process['etapa_saude']}.")
    st.progress(int(process["percentual_saude"]), text=f"Cumprimento na saúde: {int(process['percentual_saude'])}%")
    tracking_bar(f"Trilha B - cumprimento de {str(process['tipo_fluxo_saude']).lower()}", health_track, int(process["etapa_saude_ordem"]), "#239B56")

    c1, c2, c3 = st.columns(3)
    with c1:
        with st.container(border=True, key="manager_panel_decisao_e_comunicacao"):
            section_title("Decisão e comunicação")
            st.write(process["decisao_urgencia"])
            if pd.notna(process["data_intimacao"]):
                st.caption(f"Intimação: {pd.to_datetime(process['data_intimacao']).strftime('%d/%m/%Y')}")
    with c2:
        with st.container(border=True, key="manager_panel_prazo_para_cumprimento"):
            section_title("Prazo para cumprimento")
            if pd.notna(process["data_limite_cumprimento"]):
                st.markdown(f"**{pd.to_datetime(process['data_limite_cumprimento']).strftime('%d/%m/%Y')}**")
                st.caption(f"Prazo informado: {int(process['prazo_cumprimento_dias'])} dias")
            else:
                st.write("Ainda não definido")
    with c3:
        with st.container(border=True, key="manager_panel_proxima_acao"):
            section_title("Próxima ação")
            st.write(process["proxima_etapa"])
            st.caption(f"Responsável: {process['responsavel_etapa']}")

    if user_role == "usuario":
        st.info(process["mensagem_paciente"])

    pdf_data = build_process_tracking_pdf(
        mask_personal_data(pd.DataFrame([process])).iloc[0].to_dict(),
        JUDICIAL_TRACK,
        health_track,
    )
    st.download_button(
        "Baixar consulta em PDF",
        data=pdf_data,
        file_name=f"andamento_{process['processo_id']}.pdf",
        mime="application/pdf",
        help="Baixa um relatório com o resumo e as etapas do processo selecionado.",
        type="primary",
    )
