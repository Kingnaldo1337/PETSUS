from html import escape
from io import BytesIO

import pandas as pd
import streamlit as st
from petsus.dashboard.patient_ui import icon as portal_icon


CARD_HELP = {
    "Processos acompanhados": "Quantidade de processos incluídos no recorte e nos filtros selecionados.",
    "Cumprimento iniciado": "Processos em que uma ordem favorável já começou a ser executada pela rede de saúde.",
    "Prazo vencido": "Processos em que o prazo calculado após a intimação terminou e o cumprimento ainda aparece como pendente.",
    "Uso contínuo": "Tratamentos que precisam de entregas ou acompanhamento periódico e não terminam na primeira dispensação.",
    "Total de Processos": "Quantidade total de processos judiciais incluídos no recorte selecionado.",
    "Pacientes Ativos": "Quantidade de pacientes distintos com processos no recorte selecionado.",
    "Custo Total": "Soma dos custos estimados dos processos exibidos.",
    "Tempo Médio": "Soma dos dias de tramitação / processos com tempo válido. Início: ajuizamento. Fim: julgamento de mérito, acordo ou extinção; nos pendentes, data de referência. A data de arquivamento posterior não integra essa duração.",
    "Taxa de Procedência": "100 × processos com desfecho Procedente / processos julgados (Procedente + Parcialmente procedente + Improcedente). Parciais, pendentes e acordos não contam como êxito integral. Sem julgados: não se aplica.",
    "Parcialmente procedentes": "100 × processos Parcialmente procedentes / julgados (Procedente + Parcialmente procedente + Improcedente). É acolhimento parcial e não procedência integral.",
    "Pendentes de julgamento": "Quantidade de processos com desfecho Em andamento. Não significa perda do pedido; não integra o denominador dos julgados.",
    "Processos Urgentes": "Contagem de registros com urgente = Sim: pedido de análise urgente no processo. Não comprova risco clínico nem concessão de liminar.",
    "Taxa de Liminares": "100 × processos com liminar = Sim / total de processos do recorte. Sim indica concessão provisória registrada; Não não distingue ausência de pedido, pendência ou indeferimento.",
    "Ticket Médio": "É o custo estimado médio de cada processo no recorte selecionado: custo total dividido pela quantidade de processos.",
    "Ticket médio": "É o custo estimado médio de cada processo no recorte selecionado: custo total dividido pela quantidade de processos.",
    "Demandas de medicamentos": "Contagem de processos cujo tipo ou natureza é Medicamentos. Esse subconjunto é o denominador das métricas de medicamentos e competência judicial.",
    "Custo Medicamentos": "Soma de custo_estimado apenas das demandas de medicamentos. Estimativa do registro processual, sem comprovação de gasto executado. Não somar ao custo anual do tratamento ou valor da causa: são medidas alternativas.",
    "Valor anual estimado": "Soma do custo estimado de 12 meses de tratamento das demandas de medicamentos. Denominador: demandas de medicamentos do recorte. Não somar ao custo processual nem ao valor da causa.",
    "Valor da causa estimado": "Soma do valor anual estimado × min(duração em meses, 12) / 12. Representa uma base econômica estimada do pedido, sem substituir cálculo jurídico. Não é gasto realizado.",
    "Justiça Federal": "100 × demandas de medicamentos classificadas como Justiça Federal / total de demandas de medicamentos do recorte. Classificação, não parecer jurídico.",
    "Justiça Estadual": "100 × demandas de medicamentos classificadas como Justiça Estadual / total de demandas de medicamentos do recorte. Classificação, não parecer jurídico.",
    "Potencialmente evitáveis": "100 × processos sinalizados como potencialmente evitáveis / total de processos do recorte. A marcação decorre de causas administrativas passíveis de revisão, requer avaliação individual do caso.",
    "Judicialização potencialmente evitável": "100 × processos com sinalização de potencialmente evitável / total de processos filtrados. Classificação por causas administrativas, sujeita a revisão humana.",
    "Demandas potencialmente evitáveis": "Contagem de processos com sinalização de potencialmente evitável no recorte, sem afirmar que a ação judicial era desnecessária.",
    "Acordos": "Contagem de processos com desfecho Acordo no recorte; não integra o denominador dos julgados de mérito.",
    "Itens Distintos": "Contagem de valores distintos de item demandado no recorte, sem somar repetições do mesmo item.",
    "DCB distintos": "Contagem de princípios ativos distintos entre as demandas de medicamentos filtradas, sem distinguir apresentações do mesmo princípio ativo.",
    "Incorporados à RENAME": "100 × demandas de medicamentos com incorporação Sim / total de demandas de medicamentos filtradas. Confirme a incorporação na lista oficial vigente.",
    "Municípios": "Contagem de municípios distintos nos processos filtrados; não é uma taxa por população residente.",
    "Pacientes": "Contagem de pacientes distintos com processo no recorte. Um paciente com vários processos é contado uma vez.",
    "Custo por paciente": "Soma dos custos estimados dos processos / pacientes distintos no recorte. Não é custo per capita da população do município.",
    "Idade Média": "Soma das idades informadas / pacientes distintos com idade válida no recorte. A idade vem do cadastro, sem recalcular a partir de data de nascimento.",
    "% Feminino": "100 × pacientes distintos com sexo Feminino / total de pacientes distintos filtrados.",
    "Município": "100 × processos com ente responsável Município / total de processos filtrados. Responsabilidade administrativa, distinta da competência judicial.",
    "Estado": "100 × processos com ente responsável Estado / total de processos filtrados. Responsabilidade administrativa, distinta da competência judicial.",
    "União": "100 × processos com ente responsável União / total de processos filtrados. Responsabilidade administrativa, distinta da competência judicial.",
    "Compartilhada": "100 × processos com responsabilidade indicada Compartilhada / total de processos filtrados. Hipótese de participação conjunta de entes, sujeita a revisão.",
}


FILTER_HELP = {
    "sexo": "Restringe os resultados ao sexo informado no cadastro do paciente.",
    "faixa_etaria": "Exibe somente pacientes das faixas etárias selecionadas.",
    "condicao_clinica": "Filtra os processos pela condição clínica associada ao paciente.",
    "sus_exclusivo": "Permite separar pacientes que dependem exclusivamente do SUS dos demais.",
    "renda_familiar": "Restringe os resultados pela faixa de renda familiar cadastrada.",
    "regiao": "Exibe somente registros das regiões brasileiras selecionadas.",
    "uf": "Filtra os registros pelo estado (UF) relacionado ao processo.",
    "municipio": "Exibe somente processos dos municípios selecionados.",
    "natureza": "Separa os processos pela natureza da demanda, como medicamentos ou internações.",
    "tipo_demanda": "Filtra pelo tipo específico de pedido feito no processo judicial.",
    "item_demandado": "Localiza processos conforme o medicamento, procedimento, insumo ou serviço solicitado.",
    "especialidade": "Restringe os resultados à especialidade médica relacionada à demanda.",
    "esfera": "Filtra os processos pela esfera judicial responsável.",
    "fase_processual": "Exibe processos que estão nas fases processuais selecionadas.",
    "desfecho": "Filtra pelo resultado ou situação final registrada para o processo.",
    "liminar": "Sim indica liminar concedida. Não não permite distinguir pedido pendente, indeferido ou ausente na planilha.",
    "urgente": "Pedido de análise urgente no processo. Não comprova risco clínico nem concessão de liminar.",
    "causa_judicializacao": "Causa administrativa usada para identificar oportunidades de melhoria de acesso à saúde.",
    "etapa_judicial": "Filtra pela etapa atual da trilha judicial do processo.",
    "etapa_saude": "Filtra pela etapa de cumprimento do medicamento, cirurgia ou tratamento na rede de saúde.",
    "status_andamento": "Separa processos em curso, prioritários, atrasados ou em cumprimento contínuo.",
    "indicador_atraso": "Mostra casos cujo prazo de cumprimento já venceu.",
    "medicamento_dcb": "Filtra pelo princípio ativo do medicamento, usando a Denominação Comum Brasileira (DCB).",
    "cid": "Restringe os registros pelo código da Classificação Internacional de Doenças (CID).",
    "rename_incorporado": "Indica se o medicamento está incorporado à Relação Nacional de Medicamentos Essenciais (RENAME).",
    "componente_sus": "Filtra pelo componente da assistência farmacêutica responsável pelo financiamento no SUS.",
    "grupo_sus": "Restringe pelo grupo de financiamento ou fornecimento do medicamento no SUS.",
    "pcdt_aplicavel": "Separa os casos conforme a existência de Protocolo Clínico e Diretriz Terapêutica aplicável.",
    "pcdt_referencia": "Filtra pelo protocolo clínico ou diretriz terapêutica usado como referência.",
    "competencia_petsus": "Exibe os casos conforme a competência judicial: Justiça Federal ou Estadual.",
    "reu_sugerido": "Filtra pelo ente público indicado na simulação como possível réu: União, Estado ou Município.",
}


def br_int(value: float | int) -> str:
    if pd.isna(value):
        return "0"
    return f"{int(round(float(value))):,}".replace(",", ".")


def br_float(value: float | int, casas: int = 1) -> str:
    if pd.isna(value):
        value = 0
    return f"{float(value):,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def br_money(value: float | int, compact: bool = True) -> str:
    value = 0 if pd.isna(value) else float(value)
    if compact and abs(value) >= 1_000_000:
        return f"R$ {br_float(value / 1_000_000, 1)} Mi"
    if compact and abs(value) >= 1_000:
        return f"R$ {br_float(value / 1_000, 1)} Mil"
    return f"R$ {br_float(value, 2)}"


def pct(part: float, total: float) -> float:
    return 0.0 if total in [0, None] or pd.isna(total) else (float(part) / float(total)) * 100


def fmt_periodo(df: pd.DataFrame) -> str:
    if df.empty:
        return "Sem dados"
    inicio = df["data_ajuizamento"].min().strftime("%d/%m/%Y")
    fim = df["data_ajuizamento"].max().strftime("%d/%m/%Y")
    return f"{inicio} a {fim}"


def section_title(title: str) -> None:
    title_lower = str(title).lower()
    symbol = next((name for word, name in [
        ("custo", "wallet"), ("preço", "wallet"), ("valor", "wallet"),
        ("medicamento", "medical"), ("princípio", "medical"), ("assistência", "medical"),
        ("competência", "scales"), ("responsabilidade", "scales"), ("judicial", "scales"),
        ("mensal", "chart"), ("evolução", "chart"), ("prevenção", "check"),
        ("paciente", "users"), ("idade", "users"), ("sexo", "users"),
        ("município", "location"), ("geogr", "location"),
    ] if word in title_lower), "chart")
    st.markdown(f'<h2 class="section-title"><span class="section-symbol">{portal_icon(symbol, 18)}</span><span>{escape(str(title))}</span></h2>', unsafe_allow_html=True)


def _card_help(label: str, subtitle: str) -> str:
    definition = CARD_HELP.get(str(label), f"{label}: {subtitle}")
    reference = st.session_state.get("metrics_reference")
    return f"{definition} Recorte: filtros selecionados. {subtitle}." + (f" Referência: {reference}." if reference else "")


def metric_card(label: str, value: str, subtitle: str, icon: str, icon_cls: str = "icon-blue") -> None:
    value_text = str(value)
    longest_word = max((len(word) for word in value_text.split()), default=0)
    value_size_cls = " metric-value-long" if longest_word >= 9 else ""
    card_size_cls = " metric-card-long" if longest_word >= 9 else ""
    help_text = _card_help(label, subtitle)
    symbols = {
        "📄": "document", "👥": "users", "$": "wallet", "⏱": "clock",
        "⚖": "scales", "◐": "chart", "⌛": "clock", "🤝": "users",
        "🔔": "alert", "💊": "medical", "🧪": "medical", "✓": "check",
        "📈": "chart", "🏛": "scales", "🧾": "document", "📍": "location",
        "🎂": "person", "♀": "person", "↻": "arrow", "📋": "document",
        "⚕": "medical", "!": "alert",
    }
    symbol = symbols.get(str(icon))
    icon_markup = portal_icon(symbol, 23) if symbol else escape(str(icon))
    st.markdown(
        f"""
        <div class="metric-card{card_size_cls}"><div class="metric-wrap">
            <div class="metric-head">
                <div class="metric-icon {escape(str(icon_cls), quote=True)}">{icon_markup}</div>
                <div class="metric-label">{escape(str(label))}</div>
                <span class="card-help" tabindex="0" role="img" aria-label="Ajuda: {escape(help_text, quote=True)}" data-help="{escape(help_text, quote=True)}">?</span>
            </div>
            <div class="metric-value{value_size_cls}">{escape(value_text)}</div>
            <div class="metric-sub">{escape(str(subtitle))}</div>
        </div></div>
        """,
        unsafe_allow_html=True,
    )


def insight_card(title: str, value: str, desc: str) -> None:
    help_text = _card_help(title, desc)
    st.markdown(
        f"""<div class="insight-card">
            <div class="insight-title">{escape(str(title))}<span class="card-help" tabindex="0" role="img" aria-label="Ajuda: {escape(help_text, quote=True)}" data-help="{escape(help_text, quote=True)}">?</span></div>
            <div class="insight-value">{escape(str(value))}</div>
            <div class="insight-desc">{escape(str(desc))}</div>
        </div>""",
        unsafe_allow_html=True,
    )


def to_excel_bytes(df: pd.DataFrame) -> bytes:
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="dados_filtrados", index=False)
    return output.getvalue()


def multiselect_sidebar(label: str, df: pd.DataFrame, column: str) -> list[str]:
    options = sorted([value for value in df[column].dropna().astype(str).unique().tolist() if value.strip()])
    return st.multiselect(
        label,
        options,
        key=f"filter_{column}",
        placeholder="Todos",
        help=FILTER_HELP.get(column, f"Filtra os resultados pelos valores selecionados em {label}."),
    )
