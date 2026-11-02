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

def render_patients(dff, base, k, participacao, part_custo, paciente_ids_sel):
    auth_state = st.session_state.get("auth_user", {})
    user_role = auth_state.get("role", "gestor") if isinstance(auth_state, dict) else "gestor"
    pacientes_unicos = dff.drop_duplicates("paciente_id")

    if user_role == "usuario":
        # Na visão individual não faz sentido exibir métricas populacionais
        # (percentual por sexo, condição líder, quantidade de pacientes etc.).
        idade_paciente = pd.to_numeric(pacientes_unicos["idade"], errors="coerce").dropna()
        idade_texto = "Não informada" if idade_paciente.empty else f"{br_int(idade_paciente.iloc[0])} anos"
        idade_col, _ = st.columns([1, 4])
        with idade_col:
            metric_card("Idade", idade_texto, "idade do paciente", "🎂", "icon-blue")
    else:
        cols = st.columns(5)
        fem = pct((pacientes_unicos["sexo"] == "Feminino").sum(), len(pacientes_unicos))
        masc = pct((pacientes_unicos["sexo"] == "Masculino").sum(), len(pacientes_unicos))
        maior_cond = top_group(pacientes_unicos, "condicao_clinica", "paciente_id", 1, "count")
        cards = [
            ("Pacientes", br_int(k["pacientes"]), "pacientes únicos", "👥", "icon-green"),
            ("Idade Média", f"{br_float(k['idade_media'])} anos", "média dos pacientes", "🎂", "icon-blue"),
            ("% Feminino", f"{br_float(fem)}%", "distribuição por sexo", "♀", "icon-purple"),
            ("% Masculino", f"{br_float(masc)}%", "distribuição por sexo", "♂", "icon-blue"),
            ("Condição Líder", maior_cond["condicao_clinica"].iloc[0] if not maior_cond.empty else "-", "maior frequência", "🫀", "icon-orange"),
        ]
        for col, card in zip(cols, cards):
            with col:
                metric_card(*card)

    selected_patient_id = None
    if paciente_ids_sel and len(paciente_ids_sel) == 1:
        selected_patient_id = paciente_ids_sel[0]
    elif len(dff["paciente_id"].unique()) == 1:
        selected_patient_id = dff["paciente_id"].iloc[0]

    if selected_patient_id:
        p_df = dff[dff["paciente_id"] == selected_patient_id].sort_values("data_ajuizamento", ascending=False)
        p = p_df.iloc[0]
        idade = "Não informada" if pd.isna(p["idade"]) else f"{int(p['idade'])} anos"
        with st.container(border=True):
            st.markdown(
                f"""
                <div class="patient-box">
                    <div class="patient-name">{escape(str(p['paciente']))}</div>
                    <div class="patient-sub">{escape(str(p['paciente_id']))} · CPF {escape(str(p['cpf']))} · {escape(str(p['municipio']))}/{escape(str(p['uf']))}</div>
                    <span class="tag">{escape(str(p['sexo']))}</span>
                    <span class="tag">{escape(idade)}</span>
                    <span class="tag">{escape(str(p['faixa_etaria']))}</span>
                    <span class="tag">{escape(str(p['condicao_clinica']))}</span>
                    <span class="tag">SUS exclusivo: {escape(str(p['sus_exclusivo']))}</span>
                    <span class="tag">Renda: {escape(str(p['renda_familiar']))}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
            p_cols = st.columns(5)
            vals = [
                ("Processos", br_int(len(p_df)), "no recorte", "📄", "icon-blue"),
                ("Custo acumulado", br_money(p_df["custo_estimado"].sum()), "soma dos processos", "$", "icon-green"),
                ("Ticket médio", br_money(p_df["custo_estimado"].mean()), "por processo", "🧾", "icon-purple"),
                ("Liminares", br_int((p_df["liminar"] == "Sim").sum()), "processos com liminar", "⚖️", "icon-orange"),
                ("Tempo médio", f"{br_int(p_df['tempo_tramitacao_dias'].mean())} dias", "tramitação", "⏱", "icon-blue"),
            ]
            for col, card in zip(p_cols, vals):
                with col:
                    metric_card(*card)
            section_title("Processos do paciente selecionado")
            show_cols = ["processo_id", "data_ajuizamento", "natureza", "tipo_demanda", "item_demandado", "medicamento_dcb", "cid", "rename_incorporado", "competencia_petsus", "especialidade", "fase_processual", "desfecho", "liminar", "urgente", "custo_estimado"]
            tabela_p = p_df[show_cols].copy()
            tabela_p["data_ajuizamento"] = tabela_p["data_ajuizamento"].dt.strftime("%d/%m/%Y")
            tabela_p["custo_estimado"] = tabela_p["custo_estimado"].map(lambda x: br_money(x, compact=False))
            st.dataframe(tabela_p.rename(columns={
                "processo_id": "Processo", "data_ajuizamento": "Data", "natureza": "Natureza", "tipo_demanda": "Tipo", "item_demandado": "Item", "medicamento_dcb": "DCB", "cid": "CID", "rename_incorporado": "RENAME", "competencia_petsus": "Competência", "especialidade": "Especialidade", "fase_processual": "Fase", "desfecho": "Desfecho", "liminar": "Liminar", "urgente": "Urgente", "custo_estimado": "Custo"
            }), hide_index=True, use_container_width=True, height=260)

    if user_role != "usuario":
        a, b, c = st.columns([1.2, 1.0, 1.25])
        with a:
            with st.container(border=True):
                section_title("Faixa etária dos pacientes")
                faixa = pacientes_unicos.groupby("faixa_etaria", as_index=False).size().rename(columns={"size": "pacientes"})
                order = ["0 a 18", "19 a 30", "31 a 40", "41 a 50", "51 a 60", "61 a 70", "71+"]
                faixa["ordem"] = faixa["faixa_etaria"].map({v: i for i, v in enumerate(order)})
                faixa = faixa.sort_values("ordem")
                fig = px.bar(faixa, x="faixa_etaria", y="pacientes", text=faixa["pacientes"].map(br_int))
                fig.update_traces(marker_color="#125CC9")
                fig.update_layout(**chart_layout(height=330))
                fig.update_yaxes(showgrid=True, gridcolor="#E8EDF5", zeroline=False)
                fig.update_xaxes(showgrid=False)
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        with b:
            with st.container(border=True):
                section_title("Distribuição por sexo")
                sexo = pacientes_unicos.groupby("sexo", as_index=False).size().rename(columns={"size": "pacientes"})
                st.plotly_chart(donut(sexo, "sexo", "pacientes", f"{br_int(k['pacientes'])}<br>Pacientes", height=330), use_container_width=True, config={"displayModeBar": False})
        with c:
            with st.container(border=True):
                section_title("Condições clínicas mais frequentes")
                cond = top_group(pacientes_unicos, "condicao_clinica", "paciente_id", 10, "count")
                cond["texto"] = cond["valor"].map(br_int)
                st.plotly_chart(barh(cond, "condicao_clinica", "valor", "texto", height=330, color="#39A74A"), use_container_width=True, config={"displayModeBar": False})

    d, e = st.columns([1.05, 1.5])
    with d:
        with st.container(border=True):
            section_title("Perfil socioassistencial")
            socio = pd.DataFrame({
                "Indicador": ["SUS exclusivo", "PCD", "Doença rara", "Renda até 1 SM"],
                "Pacientes": [
                    int((pacientes_unicos["sus_exclusivo"] == "Sim").sum()),
                    int((pacientes_unicos["pcd"] == "Sim").sum()),
                    int((pacientes_unicos["doenca_rara"] == "Sim").sum()),
                    int((pacientes_unicos["renda_familiar"] == "Até 1 salário mínimo").sum()),
                ],
            })
            socio["% do total"] = socio["Pacientes"].map(lambda x: f"{br_float(pct(x, len(pacientes_unicos)))}%")
            socio["Pacientes"] = socio["Pacientes"].map(br_int)
            st.dataframe(socio, hide_index=True, use_container_width=True, height=260)
    with e:
        with st.container(border=True):
            section_title("Custo acumulado dos meus processos" if user_role == "usuario" else "Pacientes com maior custo acumulado")
            tab = dff.groupby(["paciente_id", "paciente", "cpf"], as_index=False).agg(
                processos=("processo_id", "count"),
                custo_total=("custo_estimado", "sum"),
                ultimo_processo=("data_ajuizamento", "max"),
            ).sort_values("custo_total", ascending=False).head(12)
            tab["custo_total"] = tab["custo_total"].map(lambda x: br_money(x, compact=False))
            tab["ultimo_processo"] = tab["ultimo_processo"].dt.strftime("%d/%m/%Y")
            st.dataframe(tab.rename(columns={"paciente_id": "ID", "paciente": "Paciente", "cpf": "CPF", "processos": "Processos", "custo_total": "Custo Total", "ultimo_processo": "Último Processo"}), hide_index=True, use_container_width=True, height=310)
