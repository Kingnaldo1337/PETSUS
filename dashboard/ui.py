from __future__ import annotations

from datetime import datetime
from html import escape
from io import BytesIO
from pathlib import Path

import pandas as pd
import streamlit as st


CARD_HELP = {
    "Processos acompanhados": "Quantidade de processos incluídos no recorte e nos filtros selecionados.",
    "Cumprimento iniciado": "Processos em que uma ordem favorável já começou a ser executada pela rede de saúde.",
    "Prazo vencido": "Processos em que o prazo calculado após a intimação terminou e o cumprimento ainda aparece como pendente.",
    "Uso contínuo": "Tratamentos que precisam de entregas ou acompanhamento periódico e não terminam na primeira dispensação.",
    "Total de Processos": "Quantidade total de processos judiciais incluídos no recorte selecionado.",
    "Pacientes Ativos": "Quantidade de pacientes distintos com processos no recorte selecionado.",
    "Custo Total": "Soma dos custos estimados dos processos exibidos.",
    "Tempo Médio": "Média de dias de tramitação dos processos exibidos.",
    "Taxa de Procedência": "Percentual de processos com resultado procedente ou parcialmente procedente.",
    "Processos Urgentes": "Quantidade de processos classificados como urgentes.",
    "Taxa de Liminares": "Percentual de processos que possuem decisão liminar registrada.",
    "Ticket Médio": "É o custo estimado médio de cada processo no recorte selecionado: custo total dividido pela quantidade de processos.",
    "Ticket médio": "É o custo estimado médio de cada processo no recorte selecionado: custo total dividido pela quantidade de processos.",
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
    "liminar": "Permite visualizar processos conforme a existência ou concessão de medida liminar.",
    "urgente": "Separa as demandas classificadas como urgentes das não urgentes.",
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
    "competencia_petsus": "Exibe os casos conforme a competência judicial simulada: Justiça Federal ou Estadual.",
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
    st.markdown(f'<div class="section-title">{escape(str(title))}</div>', unsafe_allow_html=True)


def metric_card(label: str, value: str, subtitle: str, icon: str, icon_cls: str = "icon-blue") -> None:
    value_text = str(value)
    longest_word = max((len(word) for word in value_text.split()), default=0)
    value_size_cls = " metric-value-long" if longest_word >= 9 else ""
    card_size_cls = " metric-card-long" if longest_word >= 9 else ""
    help_text = CARD_HELP.get(str(label), f"{label}: {subtitle}")
    st.markdown(
        f"""
        <div class="metric-card{card_size_cls}"><div class="metric-wrap">
            <div class="metric-head">
                <div class="metric-icon {escape(str(icon_cls), quote=True)}">{escape(str(icon))}</div>
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
    help_text = CARD_HELP.get(str(title), f"{title}: {desc}")
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


def citizen_glossary_expander() -> None:
    with st.expander("📖 Glossário Cidadão — Entenda os termos do seu processo", expanded=False):
        st.markdown(
            """
            Para facilitar a compreensão do andamento do seu processo, veja o significado dos termos jurídicos e da saúde mais utilizados:

            - **Tutela de Urgência / Liminar:** Decisão provisória concedida pelo juiz logo no início do processo, determinando que o SUS forneça o medicamento ou realize o procedimento imediatamente, antes da sentença final, devido ao risco à saúde ou perigo de dano irreparável.
            - **RENAME (Relação Nacional de Medicamentos Essenciais):** Lista oficial do Ministério da Saúde com todos os medicamentos padronizados e garantidos para entrega pelo SUS.
            - **PCDT (Protocolo Clínico e Diretrizes Terapêuticas):** Documento oficial que estabelece os critérios de diagnóstico, tratamento recomendado, remédios e doses para cada doença na rede pública.
            - **Polo Passivo / Réu:** É contra quem a ação judicial foi proposta — geralmente o Município (prefeitura), o Estado (governo estadual) ou a União (governo federal). Eles são os responsáveis por cumprir o que o juiz ordenar.
            - **Litisconsórcio (Responsabilidade Compartilhada):** Quando mais de um ente público (ex.: Município e Estado juntos) respondem solidariamente pela entrega do tratamento.
            - **Intimação:** Notificação formal da Justiça para o setor de saúde informando a ordem judicial e iniciando a contagem do prazo limite para cumprimento.
            - **Prazo de Cumprimento:** Período fixado pelo juiz (geralmente em dias úteis ou corridos) para que o medicamento seja entregue ou o procedimento seja agendado/realizado.
            - **Princípio Ativo / DCB (Denominação Comum Brasileira):** O nome químico oficial do medicamento, independente do fabricante ou marca comercial.
            - **Cumprimento de Sentença:** Fase da ação em que a decisão já é definitiva (não cabe mais recurso ordinário) e o poder público tem a obrigação jurídica de prestar o tratamento.
            """
        )


def citizen_legal_contacts_card() -> None:
    with st.container(border=True):
        section_title("🏛️ Onde buscar orientação e assistência jurídica")
        st.markdown(
            """
            Se você tiver dúvidas sobre o seu processo, prazos vencidos ou descumprimento de ordem judicial, procure os canais de assistência:

            - **Defensoria Pública do Estado (DPE):** Assistência jurídica integral e gratuita aos cidadãos que não possuem condições financeiras de contratar advogado. Atua em processos na Justiça Estadual (contra Município ou Estado).
            - **Defensoria Pública da União (DPU):** Atua gratuitamente em causas que tramitam na Justiça Federal (processos que envolvem a União, o Ministério da Saúde ou o INSS).
            - **Ouvidoria do SUS — Disque Saúde 136:** Central telefônica gratuita do Ministério da Saúde para informações, reclamações e denúncias sobre falta de medicamentos e regulação.
            - **Advogado Constituído ou OAB:** Se você contratou um advogado particular ou conta com defensor dativo indicado pela OAB, faça contato direto com o escritório responsável.
            """
        )


def transparency_footer(data_file: Path, data_corte: str, proxima_atualizacao: str) -> None:
    """Rodapé de transparência temporal — exibe data de extração, corte e próxima atualização.

    Deve ser chamado no final de cada renderização de página (após o conteúdo principal).
    """
    try:
        mtime = datetime.fromtimestamp(data_file.stat().st_mtime)
        ultima_extracao = mtime.strftime("%d/%m/%Y às %H:%M")
    except (FileNotFoundError, OSError):
        ultima_extracao = "Não disponível"

    st.markdown(
        f"""
        <div style="
            margin-top: 2rem;
            padding: .85rem 1.1rem;
            background: #F0F4FB;
            border: 1px solid #DDE6F2;
            border-radius: 14px;
            display: flex;
            flex-wrap: wrap;
            gap: .6rem 2rem;
            align-items: center;
        ">
            <span style="font-size:.82rem;color:#667085;font-weight:700;letter-spacing:.02em;">ℹ️ TRANSPARÊNCIA DOS DADOS</span>
            <span style="font-size:.82rem;color:#31456F;">
                📥 <b>Última extração da base:</b> {escape(ultima_extracao)}
            </span>
            <span style="font-size:.82rem;color:#31456F;">
                📅 <b>Data de corte dos cálculos:</b> {escape(data_corte)}
            </span>
            <span style="font-size:.82rem;color:#31456F;">
                🔄 <b>Próxima atualização prevista:</b> {escape(proxima_atualizacao)}
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def feedback_widget(feedback_url: str) -> None:
    """Widget flutuante de feedback no canto inferior direito da tela."""
    st.markdown(
        f"""
        <style>
        .petsus-feedback-btn {{
            position: fixed;
            bottom: 1.5rem;
            right: 1.5rem;
            z-index: 9999;
            background: linear-gradient(135deg, #083E82 0%, #125CC9 100%);
            color: #FFFFFF !important;
            border: none;
            border-radius: 50px;
            padding: .65rem 1.2rem;
            font-size: .88rem;
            font-weight: 800;
            font-family: 'Inter', sans-serif;
            cursor: pointer;
            box-shadow: 0 6px 20px rgba(8, 62, 130, 0.35);
            text-decoration: none;
            display: flex;
            align-items: center;
            gap: .45rem;
            transition: transform .15s ease, box-shadow .15s ease;
        }}
        .petsus-feedback-btn:hover {{
            transform: translateY(-2px);
            box-shadow: 0 10px 28px rgba(8, 62, 130, 0.45);
            color: #FFFFFF !important;
        }}
        </style>
        <a class="petsus-feedback-btn" href="{escape(feedback_url, quote=True)}" target="_blank" rel="noopener noreferrer"
           title="Clique para reportar uma inconsistência ou sugerir uma melhoria">
            💬 Reportar inconsistência
        </a>
        """,
        unsafe_allow_html=True,
    )
