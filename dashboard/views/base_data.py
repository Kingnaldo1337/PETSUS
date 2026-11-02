from __future__ import annotations

from html import escape

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from ..charts import barh, chart_layout, donut, empty_fig, monthly_line, top_group
from ..ui import br_float, br_int, br_money, citizen_glossary_expander, citizen_legal_contacts_card, insight_card, metric_card, pct, section_title, to_excel_bytes
from petsus.reports.process_tracking_pdf import build_process_tracking_pdf

LIMITE_210_SM_2026 = 210 * 1621.0

def render_base_data(dff, base, k, participacao, part_custo, paciente_ids_sel):
    auth_state = st.session_state.get("auth_user", {})
    user_role = auth_state.get("role", "gestor") if isinstance(auth_state, dict) else "gestor"
    if user_role == "usuario":
        cards = [
            ("Meus processos", br_int(k["total"]), "processos vinculados", "🔎", "icon-blue"),
            ("Custo total", br_money(k["custo"]), "soma dos processos", "$", "icon-green"),
            ("Itens", br_int(dff["item_demandado"].nunique()), "itens distintos", "💊", "icon-orange"),
        ]
    else:
        cards = [
            ("Registros filtrados", br_int(k["total"]), f"{br_float(participacao)}% da base", "🔎", "icon-blue"),
            ("Pacientes", br_int(k["pacientes"]), "pacientes únicos", "👥", "icon-green"),
            ("Custo total", br_money(k["custo"]), "soma filtrada", "$", "icon-green"),
            ("Municípios", br_int(k["municipios"]), "municípios únicos", "📍", "icon-purple"),
            ("Itens", br_int(dff["item_demandado"].nunique()), "itens distintos", "💊", "icon-orange"),
        ]
    cols = st.columns(len(cards))
    for col, card in zip(cols, cards):
        with col:
            metric_card(*card)

    with st.container(border=True):
        section_title("Base detalhada filtrada")
        st.caption("A tabela abaixo contém somente os seus registros." if user_role == "usuario" else "A tabela abaixo respeita todos os filtros da barra lateral, inclusive o filtro por paciente.")
        show_cols = [
            "processo_id", "data_ajuizamento", "paciente_id", "paciente", "cpf", "sexo", "idade", "faixa_etaria",
            "municipio", "uf", "regiao", "condicao_clinica", "natureza", "tipo_demanda", "item_demandado", "especialidade",
            "medicamento_dcb", "cid", "rename_incorporado", "componente_sus", "grupo_sus", "apresentacao_padronizada",
            "pcdt_aplicavel", "pcdt_referencia", "dose_prescrita", "frequencia_administracao", "duracao_meses", "pmvg_referencia",
            "valor_anual_tratamento", "valor_causa_estimado", "competencia_petsus", "reu_sugerido", "criterio_competencia",
            "acima_210_salarios_minimos", "etapa_judicial", "percentual_judicial", "etapa_saude", "percentual_saude",
            "status_andamento", "decisao_urgencia", "data_intimacao", "prazo_cumprimento_dias",
            "data_limite_cumprimento", "indicador_atraso", "proxima_acao_judicial", "proxima_acao_saude",
            "origem_informacao", "esfera", "fase_processual", "desfecho", "liminar", "urgente", "tempo_tramitacao_dias", "custo_estimado"
        ]
        table = dff[show_cols].copy().sort_values("data_ajuizamento", ascending=False)
        table["data_ajuizamento"] = table["data_ajuizamento"].dt.strftime("%d/%m/%Y")
        table_view = table.rename(columns={
            "processo_id": "Processo", "data_ajuizamento": "Data", "paciente_id": "ID Paciente", "paciente": "Paciente", "cpf": "CPF",
            "sexo": "Sexo", "idade": "Idade", "faixa_etaria": "Faixa", "municipio": "Município", "uf": "UF", "regiao": "Região",
            "condicao_clinica": "Condição", "natureza": "Natureza", "tipo_demanda": "Tipo", "item_demandado": "Item", "especialidade": "Especialidade",
            "medicamento_dcb": "DCB", "cid": "CID", "rename_incorporado": "RENAME", "componente_sus": "Componente SUS", "grupo_sus": "Grupo SUS",
            "apresentacao_padronizada": "Apresentação", "pcdt_aplicavel": "PCDT", "pcdt_referencia": "PCDT de Referência", "dose_prescrita": "Dose", "frequencia_administracao": "Frequência",
            "duracao_meses": "Duração (meses)", "pmvg_referencia": "PMVG Referência", "valor_anual_tratamento": "Valor Anual Tratamento",
            "valor_causa_estimado": "Valor da Causa", "competencia_petsus": "Competência PetSUS", "reu_sugerido": "Réu Sugerido",
            "criterio_competencia": "Critério de Competência", "acima_210_salarios_minimos": "≥ 210 SM",
            "etapa_judicial": "Etapa Judicial", "percentual_judicial": "Andamento Judicial (%)",
            "etapa_saude": "Cumprimento na Saúde", "percentual_saude": "Cumprimento na Saúde (%)",
            "status_andamento": "Status do Acompanhamento", "decisao_urgencia": "Decisão de Urgência",
            "data_intimacao": "Data da Intimação", "prazo_cumprimento_dias": "Prazo (dias)",
            "data_limite_cumprimento": "Data Limite", "indicador_atraso": "Prazo Vencido",
            "proxima_acao_judicial": "Próxima Ação Judicial", "proxima_acao_saude": "Próxima Ação na Saúde",
            "origem_informacao": "Origem da Informação",
            "esfera": "Esfera", "fase_processual": "Fase", "desfecho": "Desfecho", "liminar": "Liminar", "urgente": "Urgente",
            "tempo_tramitacao_dias": "Tempo (dias)", "custo_estimado": "Custo Estimado"
        })
        st.dataframe(
            table_view,
            hide_index=True,
            use_container_width=True,
            height=520,
            column_config={
                "Custo Estimado": st.column_config.NumberColumn("Custo Estimado", format="R$ %.2f"),
                "PMVG Referência": st.column_config.NumberColumn("PMVG Referência", format="R$ %.2f"),
                "Valor Anual Tratamento": st.column_config.NumberColumn("Valor Anual Tratamento", format="R$ %.2f"),
                "Valor da Causa": st.column_config.NumberColumn("Valor da Causa", format="R$ %.2f"),
            },
        )

        csv = table.to_csv(index=False).encode("utf-8-sig")
        c1, c2, c3 = st.columns([1, 1.35, 3.65])
