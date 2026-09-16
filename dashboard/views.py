from __future__ import annotations

from html import escape

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from .charts import barh, chart_layout, donut, empty_fig, monthly_line, top_group
from .ui import br_float, br_int, br_money, insight_card, metric_card, pct, section_title, to_excel_bytes

LIMITE_210_SM_2026 = 210 * 1621.0

def render_pages(pagina, dff, base, k, participacao, part_custo, paciente_ids_sel):
    auth_state = st.session_state.get("auth_user", {})
    user_role = auth_state.get("role", "gestor") if isinstance(auth_state, dict) else "gestor"
    
    # -----------------------------------------------------------------------------
    # Páginas
    # -----------------------------------------------------------------------------
    if pagina == "Visão Geral":
        cards = [
            ("Total de Processos", br_int(k["total"]), f"{br_float(participacao)}% da base total", "📄", "icon-blue"),
            ("Custo Total", br_money(k["custo"]), f"{br_float(part_custo)}% do custo total", "$", "icon-green"),
            ("Tempo Médio", f"{br_int(k['tempo'])} dias", "tempo médio de tramitação", "⏱", "icon-orange"),
            ("Taxa de Procedência", f"{br_float(k['procedencia'])}%", "procedente + parcialmente", "🛡", "icon-purple"),
        ]
        if user_role != "usuario":
            cards.insert(
                1,
                ("Pacientes Ativos", br_int(k["pacientes"]), f"{br_float(pct(k['pacientes'], base['paciente_id'].nunique()))}% dos pacientes", "👥", "icon-green"),
            )
        cols = st.columns(len(cards))
        for col, card in zip(cols, cards):
            with col:
                metric_card(*card)
    
        a, b, c = st.columns([1.75, 1.2, 1.15])
        with a:
            with st.container(border=True):
                section_title("Evolução mensal dos processos")
                st.plotly_chart(
                    monthly_line(dff.assign(qtd=1), "qtd", "Processos", height=340),
                    use_container_width=True,
                    config={"displayModeBar": True, "scrollZoom": True, "responsive": True, "displaylogo": False},
                )
        with b:
            with st.container(border=True):
                section_title("Natureza da ação")
                nat = dff.groupby("natureza", as_index=False).size().rename(columns={"size": "processos"}).sort_values("processos", ascending=False)
                st.plotly_chart(donut(nat, "natureza", "processos", f"{br_int(k['total'])}<br>Total", height=340), use_container_width=True, config={"displayModeBar": False})
        with c:
            with st.container(border=True):
                section_title("Desfecho processual")
                desf = dff.groupby("desfecho", as_index=False).size().rename(columns={"size": "processos"}).sort_values("processos", ascending=False)
                st.plotly_chart(donut(desf, "desfecho", "processos", f"{br_float(k['procedencia'])}%<br>Proced.", height=340), use_container_width=True, config={"displayModeBar": False})
    
        d, e, f = st.columns([1.35, 1.35, 1.30])
        with d:
            with st.container(border=True):
                section_title("Top 10 itens mais demandados")
                top_itens = top_group(dff, "item_demandado", "processo_id", 10, "count")
                top_itens["texto"] = top_itens["valor"].map(br_int)
                st.plotly_chart(barh(top_itens, "item_demandado", "valor", "texto", height=335), use_container_width=True, config={"displayModeBar": False})
        with e:
            with st.container(border=True):
                section_title("Custo por natureza")
                custo_nat = top_group(dff, "natureza", "custo_estimado", 8, "sum")
                custo_nat["texto"] = custo_nat["valor"].map(br_money)
                st.plotly_chart(barh(custo_nat, "natureza", "valor", "texto", height=335, color="#39A74A"), use_container_width=True, config={"displayModeBar": False})
        with f:
            with st.container(border=True):
                section_title("Alertas executivos")
                p_lim = br_float(k["liminar"])
                item_maior = top_group(dff, "item_demandado", "custo_estimado", 1, "sum")
                ticket_top = dff.groupby("paciente", as_index=False)["custo_estimado"].sum().sort_values("custo_estimado", ascending=False).head(1)
                i1, i2 = st.columns(2)
                with i1:
                    insight_card("Liminares", f"{p_lim}%", "Percentual de processos com decisão liminar no recorte filtrado.")
                with i2:
                    insight_card("Urgentes", br_int(k["urgentes"]), "Total de processos classificados como urgentes.")
                if user_role == "usuario":
                    insight_card("Maior item por custo", item_maior["item_demandado"].iloc[0] if not item_maior.empty else "-", br_money(item_maior["valor"].iloc[0]) if not item_maior.empty else "Sem custo")
                else:
                    cidade_maior = top_group(dff, "municipio", "processo_id", 1, "count")
                    i3, i4 = st.columns(2)
                    with i3:
                        insight_card("Maior item por custo", item_maior["item_demandado"].iloc[0] if not item_maior.empty else "-", br_money(item_maior["valor"].iloc[0]) if not item_maior.empty else "Sem custo")
                    with i4:
                        insight_card("Município destaque", cidade_maior["municipio"].iloc[0] if not cidade_maior.empty else "-", f"{br_int(cidade_maior['valor'].iloc[0])} processos" if not cidade_maior.empty else "Sem registros")
    
    elif pagina == "Demandas":
        cols = st.columns(5)
        demanda_principal = top_group(dff, "tipo_demanda", "processo_id", 1, "count")
        esp_principal = top_group(dff, "especialidade", "processo_id", 1, "count")
        cards = [
            ("Processos Urgentes", br_int(k["urgentes"]), f"{br_float(pct(k['urgentes'], k['total']))}% dos processos", "🔔", "icon-orange"),
            ("Taxa de Liminares", f"{br_float(k['liminar'])}%", "processos com liminar", "⚖️", "icon-purple"),
            ("Demanda Principal", demanda_principal["tipo_demanda"].iloc[0] if not demanda_principal.empty else "-", "maior volume", "📌", "icon-blue"),
            ("Especialidade Líder", esp_principal["especialidade"].iloc[0] if not esp_principal.empty else "-", "maior volume", "🩺", "icon-green"),
            ("Itens Distintos", br_int(dff["item_demandado"].nunique()), "medicamentos/serviços", "💊", "icon-blue"),
        ]
        for col, card in zip(cols, cards):
            with col:
                metric_card(*card)
    
        a, b = st.columns([1.35, 1.2])
        with a:
            with st.container(border=True):
                section_title("Demandas por tipo e fase processual")
                fase = pd.crosstab(dff["tipo_demanda"], dff["fase_processual"]).reset_index()
                for col in ["Conhecimento", "Execução", "Cumprimento de Sentença"]:
                    if col not in fase.columns:
                        fase[col] = 0
                fase = fase.sort_values(["Conhecimento", "Execução", "Cumprimento de Sentença"], ascending=False).head(10)
                fig = go.Figure()
                for col_name, color in [("Conhecimento", "#125CC9"), ("Execução", "#39A74A"), ("Cumprimento de Sentença", "#EAB308")]:
                    fig.add_trace(go.Bar(y=fase["tipo_demanda"], x=fase[col_name], orientation="h", name=col_name, marker_color=color, text=fase[col_name], textposition="inside"))
                fig.update_layout(**chart_layout(height=370, showlegend=True, legend=dict(orientation="h", y=1.12, x=0)), barmode="stack")
                fig.update_xaxes(showgrid=True, gridcolor="#E8EDF5", zeroline=False)
                fig.update_yaxes(showgrid=False, autorange="reversed")
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        with b:
            with st.container(border=True):
                section_title("Evolução mensal de liminares e urgências")
                trend = dff.assign(liminar_qtd=(dff["liminar"] == "Sim").astype(int), urgente_qtd=(dff["urgente"] == "Sim").astype(int))
                trend = trend.groupby("ano_mes", as_index=False).agg(liminares=("liminar_qtd", "sum"), urgentes=("urgente_qtd", "sum"))
                trend = trend.sort_values("ano_mes")
                trend["mes"] = pd.to_datetime(trend["ano_mes"] + "-01").dt.strftime("%m/%Y")
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=trend["mes"], y=trend["liminares"], mode="lines+markers", name="Liminares", line=dict(color="#7C3AED", width=3)))
                fig.add_trace(go.Scatter(x=trend["mes"], y=trend["urgentes"], mode="lines+markers", name="Urgentes", line=dict(color="#F59E0B", width=3)))
                fig.update_layout(**chart_layout(height=370, showlegend=True, legend=dict(orientation="h", y=1.12, x=0)))
                fig.update_yaxes(showgrid=True, gridcolor="#E8EDF5", zeroline=False)
                fig.update_xaxes(showgrid=False)
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    
        c, d, e = st.columns([1.15, 1.15, 1.25])
        with c:
            with st.container(border=True):
                section_title("Tipos de demanda")
                tipo = top_group(dff, "tipo_demanda", "processo_id", 10, "count")
                tipo["texto"] = tipo["valor"].map(br_int)
                st.plotly_chart(barh(tipo, "tipo_demanda", "valor", "texto", height=330), use_container_width=True, config={"displayModeBar": False})
        with d:
            with st.container(border=True):
                section_title("Especialidades mais acionadas")
                esp = top_group(dff, "especialidade", "processo_id", 10, "count")
                esp["texto"] = esp["valor"].map(br_int)
                st.plotly_chart(barh(esp, "especialidade", "valor", "texto", height=330, color="#39A74A"), use_container_width=True, config={"displayModeBar": False})
        with e:
            with st.container(border=True):
                section_title("Tabela de demandas")
                table = dff.groupby(["tipo_demanda", "fase_processual"], as_index=False).agg(
                    processos=("processo_id", "count"),
                    pacientes=("paciente_id", "nunique"),
                    custo_total=("custo_estimado", "sum"),
                    tempo_medio=("tempo_tramitacao_dias", "mean"),
                ).sort_values("processos", ascending=False).head(12)
                table["custo_total"] = table["custo_total"].map(lambda x: br_money(x, compact=False))
                table["tempo_medio"] = table["tempo_medio"].map(lambda x: f"{br_int(x)} dias")
                st.dataframe(table.rename(columns={"tipo_demanda": "Tipo", "fase_processual": "Fase", "processos": "Processos", "pacientes": "Pacientes", "custo_total": "Custo Total", "tempo_medio": "Tempo Médio"}), hide_index=True, use_container_width=True, height=330)
    
    elif pagina == "Medicamentos":
        med = dff[dff["medicamento_petsus"] == "Sim"].copy()
        st.info(
            "Campos de análise de medicamentos do PetSUS. "
            "Nesta base acadêmica, os valores de RENAME, PMVG, PCDT, posologia e competência são sintéticos e servem somente para demonstração do dashboard."
        )
        if med.empty:
            st.warning("Nenhuma demanda de medicamento foi encontrada com os filtros selecionados.")
        else:
            incorporados = int((med["rename_incorporado"] == "Sim").sum())
            cols = st.columns(5)
            cards = [
                ("Demandas de medicamentos", br_int(len(med)), "registros compatíveis com a análise PetSUS", "💊", "icon-blue"),
                ("DCB distintos", br_int(med["medicamento_dcb"].nunique()), "princípios ativos no recorte", "🧪", "icon-purple"),
                ("Incorporados à RENAME", f"{br_float(pct(incorporados, len(med)))}%", f"{br_int(incorporados)} registros", "✅", "icon-green"),
                ("PMVG médio", br_money(med["pmvg_referencia"].mean()), "preço de referência sintético por administração", "$", "icon-orange"),
                ("Valor anual estimado", br_money(med["valor_anual_tratamento"].sum()), "soma anual dos tratamentos", "📈", "icon-green"),
            ]
            for col, card in zip(cols, cards):
                with col:
                    metric_card(*card)
    
            a, b, c = st.columns([1.0, 1.35, 1.0])
            with a:
                with st.container(border=True):
                    section_title("Incorporação à RENAME")
                    ren = med.groupby("rename_incorporado", as_index=False).size().rename(columns={"size": "processos"})
                    st.plotly_chart(donut(ren, "rename_incorporado", "processos", f"{br_int(len(med))}<br>Demandas", height=330), use_container_width=True, config={"displayModeBar": False})
            with b:
                with st.container(border=True):
                    section_title("Componente de financiamento SUS")
                    comp = top_group(med, "componente_sus", "processo_id", 8, "count")
                    comp["texto"] = comp["valor"].map(br_int)
                    st.plotly_chart(barh(comp, "componente_sus", "valor", "texto", height=330, color="#39A74A"), use_container_width=True, config={"displayModeBar": False})
            with c:
                with st.container(border=True):
                    section_title("PCDT aplicável")
                    pcdt = med.groupby("pcdt_aplicavel", as_index=False).size().rename(columns={"size": "processos"})
                    st.plotly_chart(donut(pcdt, "pcdt_aplicavel", "processos", f"{br_float(pct((med['pcdt_aplicavel']=='Sim').sum(), len(med)))}%<br>com PCDT", height=330), use_container_width=True, config={"displayModeBar": False})
    
            d, e, f = st.columns([1.2, 1.2, 1.35])
            with d:
                with st.container(border=True):
                    section_title("DCB mais demandadas")
                    top_dcb = top_group(med, "medicamento_dcb", "processo_id", 10, "count")
                    top_dcb["texto"] = top_dcb["valor"].map(br_int)
                    st.plotly_chart(barh(top_dcb, "medicamento_dcb", "valor", "texto", height=350), use_container_width=True, config={"displayModeBar": False})
            with e:
                with st.container(border=True):
                    section_title("Maior impacto anual por DCB")
                    top_val = top_group(med, "medicamento_dcb", "valor_anual_tratamento", 10, "sum")
                    top_val["texto"] = top_val["valor"].map(br_money)
                    st.plotly_chart(barh(top_val, "medicamento_dcb", "valor", "texto", height=350, color="#7C3AED"), use_container_width=True, config={"displayModeBar": False})
            with f:
                with st.container(border=True):
                    section_title("Resumo farmacêutico")
                    tab = med.groupby("medicamento_dcb", as_index=False).agg(
                        demandas=("processo_id", "count"),
                        incorporados=("rename_incorporado", lambda s: int((s == "Sim").sum())),
                        pmvg_medio=("pmvg_referencia", "mean"),
                        valor_anual=("valor_anual_tratamento", "sum"),
                    ).sort_values("demandas", ascending=False).head(12)
                    tab["% RENAME"] = tab.apply(lambda r: f"{br_float(pct(r['incorporados'], r['demandas']))}%", axis=1)
                    tab["pmvg_medio"] = tab["pmvg_medio"].map(lambda x: br_money(x, compact=False))
                    tab["valor_anual"] = tab["valor_anual"].map(br_money)
                    st.dataframe(tab[["medicamento_dcb", "demandas", "% RENAME", "pmvg_medio", "valor_anual"]].rename(columns={
                        "medicamento_dcb": "DCB", "demandas": "Demandas", "pmvg_medio": "PMVG Médio", "valor_anual": "Valor Anual"
                    }), hide_index=True, use_container_width=True, height=350)
    
            with st.container(border=True):
                section_title("Detalhamento PetSUS")
                detail_cols = [
                    "processo_id", "cid", "medicamento_dcb", "apresentacao_padronizada", "rename_incorporado",
                    "componente_sus", "grupo_sus", "pcdt_aplicavel", "pcdt_referencia", "dose_prescrita", "frequencia_administracao",
                    "duracao_meses", "pmvg_referencia", "valor_anual_tratamento",
                ]
                det = med[detail_cols].sort_values("valor_anual_tratamento", ascending=False).head(200)
                st.dataframe(det, hide_index=True, use_container_width=True, height=360, column_config={
                    "pmvg_referencia": st.column_config.NumberColumn("PMVG Referência", format="R$ %.2f"),
                    "valor_anual_tratamento": st.column_config.NumberColumn("Valor anual", format="R$ %.2f"),
                })
    
    elif pagina == "Competência":
        med = dff[dff["medicamento_petsus"] == "Sim"].copy()
        st.info(
            f"Simulação acadêmica com os campos do PetSUS. Para medicamentos não incorporados, o dashboard usa como referência "
            f"210 salários mínimos de 2026 (R$ {br_float(LIMITE_210_SM_2026, 2)})."
        )
        if med.empty:
            st.warning("Nenhuma demanda de medicamento foi encontrada com os filtros selecionados.")
        else:
            federal = int((med["competencia_petsus"] == "Justiça Federal").sum())
            estadual = int((med["competencia_petsus"] == "Justiça Estadual").sum())
            alto_custo = int((med["acima_210_salarios_minimos"] == "Sim").sum())
            reu_top = top_group(med, "reu_sugerido", "processo_id", 1, "count")
            cols = st.columns(5)
            cards = [
                ("Justiça Federal", f"{br_float(pct(federal, len(med)))}%", f"{br_int(federal)} processos", "🏛️", "icon-blue"),
                ("Justiça Estadual", f"{br_float(pct(estadual, len(med)))}%", f"{br_int(estadual)} processos", "⚖️", "icon-green"),
                ("≥ 210 salários mínimos", br_int(alto_custo), "tratamentos anuais acima do limite de referência", "💰", "icon-orange"),
                ("Réu mais sugerido", reu_top["reu_sugerido"].iloc[0] if not reu_top.empty else "-", "maior frequência no recorte", "👤", "icon-purple"),
                ("Valor da causa estimado", br_money(med["valor_causa_estimado"].sum()), "soma dos valores estimados", "$", "icon-green"),
            ]
            for col, card in zip(cols, cards):
                with col:
                    metric_card(*card)
    
            a, b, c = st.columns([1.0, 1.0, 1.4])
            with a:
                with st.container(border=True):
                    section_title("Competência judicial")
                    comp = med.groupby("competencia_petsus", as_index=False).size().rename(columns={"size": "processos"})
                    st.plotly_chart(donut(comp, "competencia_petsus", "processos", f"{br_int(len(med))}<br>Demandas", height=340), use_container_width=True, config={"displayModeBar": False})
            with b:
                with st.container(border=True):
                    section_title("Réu sugerido")
                    reu = top_group(med, "reu_sugerido", "processo_id", 5, "count")
                    reu["texto"] = reu["valor"].map(br_int)
                    st.plotly_chart(barh(reu, "reu_sugerido", "valor", "texto", height=340, color="#7C3AED"), use_container_width=True, config={"displayModeBar": False})
            with c:
                with st.container(border=True):
                    section_title("Competência x incorporação à RENAME")
                    cross = pd.crosstab(med["rename_incorporado"], med["competencia_petsus"]).reset_index()
                    fig = go.Figure()
                    for nome, color in [("Justiça Federal", "#125CC9"), ("Justiça Estadual", "#39A74A")]:
                        if nome not in cross.columns:
                            cross[nome] = 0
                        fig.add_trace(go.Bar(x=cross["rename_incorporado"], y=cross[nome], name=nome, marker_color=color, text=cross[nome], textposition="inside"))
                    fig.update_layout(**chart_layout(height=340, showlegend=True, legend=dict(orientation="h", y=1.12, x=0)), barmode="stack")
                    fig.update_yaxes(showgrid=True, gridcolor="#E8EDF5", zeroline=False)
                    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    
            d, e = st.columns([1.05, 1.6])
            with d:
                with st.container(border=True):
                    section_title("Valor anual por componente")
                    val_comp = top_group(med, "componente_sus", "valor_anual_tratamento", 8, "sum")
                    val_comp["texto"] = val_comp["valor"].map(br_money)
                    st.plotly_chart(barh(val_comp, "componente_sus", "valor", "texto", height=360, color="#39A74A"), use_container_width=True, config={"displayModeBar": False})
            with e:
                with st.container(border=True):
                    section_title("Casos de maior valor anual")
                    tab = med[[
                        "processo_id", "cid", "medicamento_dcb", "rename_incorporado", "componente_sus", "grupo_sus",
                        "valor_anual_tratamento", "acima_210_salarios_minimos", "competencia_petsus", "reu_sugerido"
                    ]].sort_values("valor_anual_tratamento", ascending=False).head(15)
                    st.dataframe(tab.rename(columns={
                        "processo_id": "Processo", "cid": "CID", "medicamento_dcb": "DCB", "rename_incorporado": "RENAME",
                        "componente_sus": "Componente", "grupo_sus": "Grupo", "valor_anual_tratamento": "Valor anual",
                        "acima_210_salarios_minimos": "≥ 210 SM", "competencia_petsus": "Competência", "reu_sugerido": "Réu sugerido"
                    }), hide_index=True, use_container_width=True, height=360, column_config={
                        "Valor anual": st.column_config.NumberColumn("Valor anual", format="R$ %.2f")
                    })
    
    elif pagina == "Custos":
        cols = st.columns(5)
        med_cost = dff[dff["natureza"] == "Medicamentos"]["custo_estimado"].sum()
        intern_cost = dff[dff["natureza"] == "Internação"]["custo_estimado"].sum()
        cards = [
            ("Custo Total", br_money(k["custo"]), f"{br_float(part_custo)}% do custo da base", "$", "icon-green"),
            ("Ticket Médio", br_money(k["ticket"]), "média por processo", "🧾", "icon-blue"),
            ("Custo Medicamentos", br_money(med_cost), f"{br_float(pct(med_cost, k['custo']))}% do recorte", "💊", "icon-purple"),
            ("Custo Internações", br_money(intern_cost), f"{br_float(pct(intern_cost, k['custo']))}% do recorte", "🏥", "icon-orange"),
            ("Maior Processo", br_money(dff["custo_estimado"].max()), "maior valor individual", "📈", "icon-green"),
        ]
        for col, card in zip(cols, cards):
            with col:
                metric_card(*card)
    
        a, b = st.columns([1.55, 1.25])
        with a:
            with st.container(border=True):
                section_title("Evolução mensal do custo total")
                st.plotly_chart(monthly_line(dff, "custo_estimado", "Custo total", money=True, height=350), use_container_width=True, config={"displayModeBar": False})
        with b:
            with st.container(border=True):
                section_title("Custo por esfera")
                esfera = top_group(dff, "esfera", "custo_estimado", 5, "sum")
                esfera["texto"] = esfera["valor"].map(br_money)
                st.plotly_chart(barh(esfera, "esfera", "valor", "texto", height=350, color="#39A74A"), use_container_width=True, config={"displayModeBar": False})
    
        c, d, e = st.columns([1.2, 1.2, 1.2])
        with c:
            with st.container(border=True):
                section_title("Itens com maior impacto financeiro")
                itens_custo = top_group(dff, "item_demandado", "custo_estimado", 10, "sum")
                itens_custo["texto"] = itens_custo["valor"].map(br_money)
                st.plotly_chart(barh(itens_custo, "item_demandado", "valor", "texto", height=350, color="#125CC9"), use_container_width=True, config={"displayModeBar": False})
        with d:
            with st.container(border=True):
                section_title("Especialidades por custo")
                esp_custo = top_group(dff, "especialidade", "custo_estimado", 10, "sum")
                esp_custo["texto"] = esp_custo["valor"].map(br_money)
                st.plotly_chart(barh(esp_custo, "especialidade", "valor", "texto", height=350, color="#7C3AED"), use_container_width=True, config={"displayModeBar": False})
        with e:
            with st.container(border=True):
                section_title("Distribuição de ticket por natureza")
                sample = dff.copy()
                if len(sample) > 3500:
                    sample = sample.sample(3500, random_state=42)
                fig = px.box(sample, x="natureza", y="custo_estimado", points=False)
                fig.update_traces(marker_color="#125CC9")
                fig.update_layout(**chart_layout(height=350))
                fig.update_yaxes(showgrid=True, gridcolor="#E8EDF5", zeroline=False, tickprefix="R$ ")
                fig.update_xaxes(showgrid=False)
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    
    elif pagina == "Geografia":
        cols = st.columns(5)
        reg_top = top_group(dff, "regiao", "processo_id", 1, "count")
        uf_top = top_group(dff, "uf", "processo_id", 1, "count")
        mun_top = top_group(dff, "municipio", "processo_id", 1, "count")
        cards = [
            ("Municípios", br_int(k["municipios"]), "municípios no recorte", "📍", "icon-blue"),
            ("Região Líder", reg_top["regiao"].iloc[0] if not reg_top.empty else "-", "maior volume", "🗺️", "icon-green"),
            ("UF Líder", uf_top["uf"].iloc[0] if not uf_top.empty else "-", "maior volume", "🏛️", "icon-purple"),
            ("Município Líder", mun_top["municipio"].iloc[0] if not mun_top.empty else "-", "maior volume", "🏙️", "icon-orange"),
            ("Custo per capita", br_money(k["custo"] / max(k["pacientes"], 1)), "por paciente filtrado", "$", "icon-green"),
        ]
        for col, card in zip(cols, cards):
            with col:
                metric_card(*card)
    
        a, b = st.columns([1.45, 1.1])
        with a:
            with st.container(border=True):
                section_title("Mapa dos municípios filtrados")
                geo = dff.groupby(["municipio", "uf", "regiao", "latitude", "longitude"], as_index=False).agg(
                    processos=("processo_id", "count"),
                    pacientes=("paciente_id", "nunique"),
                    custo_total=("custo_estimado", "sum"),
                )
                geo = geo.dropna(subset=["latitude", "longitude"])
                if geo.empty:
                    st.plotly_chart(empty_fig("Sem coordenadas para o recorte", height=390), use_container_width=True, config={"displayModeBar": False})
                else:
                    fig = px.scatter_geo(
                        geo,
                        lat="latitude",
                        lon="longitude",
                        size="processos",
                        color="regiao",
                        hover_name="municipio",
                        hover_data={"uf": True, "processos": True, "pacientes": True, "custo_total": ":,.2f", "latitude": False, "longitude": False},
                        height=390,
                    )
                    fig.update_geos(
                        showcountries=True,
                        countrycolor="#CBD5E1",
                        showland=True,
                        landcolor="#F4F7FB",
                        showocean=True,
                        oceancolor="#E8F2FB",
                        fitbounds="locations",
                    )
                    fig.update_layout(margin=dict(l=0, r=0, t=0, b=0), legend=dict(orientation="h", y=1.02, x=0))
                    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        with b:
            with st.container(border=True):
                section_title("Processos por região")
                reg = top_group(dff, "regiao", "processo_id", 10, "count")
                reg["texto"] = reg["valor"].map(br_int)
                st.plotly_chart(barh(reg, "regiao", "valor", "texto", height=390, color="#39A74A"), use_container_width=True, config={"displayModeBar": False})
    
        c, d, e = st.columns([1.12, 1.12, 1.2])
        with c:
            with st.container(border=True):
                section_title("Top municípios por processos")
                m = top_group(dff, "municipio", "processo_id", 12, "count")
                m["texto"] = m["valor"].map(br_int)
                st.plotly_chart(barh(m, "municipio", "valor", "texto", height=340), use_container_width=True, config={"displayModeBar": False})
        with d:
            with st.container(border=True):
                section_title("Top municípios por custo")
                mc = top_group(dff, "municipio", "custo_estimado", 12, "sum")
                mc["texto"] = mc["valor"].map(br_money)
                st.plotly_chart(barh(mc, "municipio", "valor", "texto", height=340, color="#7C3AED"), use_container_width=True, config={"displayModeBar": False})
        with e:
            with st.container(border=True):
                section_title("Tabela geográfica")
                tab = dff.groupby(["regiao", "uf", "municipio"], as_index=False).agg(
                    processos=("processo_id", "count"),
                    pacientes=("paciente_id", "nunique"),
                    custo_total=("custo_estimado", "sum"),
                    ticket_medio=("custo_estimado", "mean"),
                ).sort_values("processos", ascending=False).head(15)
                tab["custo_total"] = tab["custo_total"].map(lambda x: br_money(x, compact=False))
                tab["ticket_medio"] = tab["ticket_medio"].map(lambda x: br_money(x, compact=False))
                st.dataframe(tab.rename(columns={"regiao": "Região", "uf": "UF", "municipio": "Município", "processos": "Processos", "pacientes": "Pacientes", "custo_total": "Custo Total", "ticket_medio": "Ticket Médio"}), hide_index=True, use_container_width=True, height=340)
    
    elif pagina == "Pacientes":
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
    
    else:  # Base de Dados
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
                "acima_210_salarios_minimos", "esfera", "fase_processual", "desfecho", "liminar", "urgente", "tempo_tramitacao_dias", "custo_estimado"
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
