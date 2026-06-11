from __future__ import annotations

from io import BytesIO
from pathlib import Path
import unicodedata

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(
    page_title="Dashboard de Judicialização na Saúde",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

DATA_FILE = Path(__file__).with_name("dados_dashboard_saude.xlsx")

# -----------------------------------------------------------------------------
# Estilo visual
# -----------------------------------------------------------------------------
st.markdown(
    """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');
        html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
        .stApp, [data-testid="stAppViewContainer"], .main { background: #F4F7FB; color: #0B2459; }
        [data-testid="stHeader"] { background: transparent; }
        .block-container { max-width: 1700px; padding-top: 1.05rem; padding-bottom: 1.2rem; padding-left: 1.2rem; padding-right: 1.2rem; }
        [data-testid="stSidebar"] { background: linear-gradient(180deg, #083E82 0%, #072F66 52%, #061F45 100%); }
        [data-testid="stSidebar"] * { color: white; }
        [data-testid="stSidebar"] input, [data-testid="stSidebar"] textarea { color: #0B2459 !important; }
        [data-testid="stSidebar"] div[data-baseweb="select"] span { color: #0B2459 !important; }
        [data-testid="stSidebar"] div[data-baseweb="select"] div { color: #0B2459 !important; }
        [data-testid="stSidebar"] .stDateInput input { color: #0B2459 !important; }
        .sidebar-logo { padding: 1.0rem 0 .95rem 0; text-align: center; border-bottom: 1px solid rgba(255,255,255,0.18); margin-bottom: .75rem; }
        .sidebar-logo .icon { font-size: 3.25rem; line-height: 1; margin-bottom: .25rem; }
        .sidebar-logo .title { font-size: 1.75rem; font-weight: 900; line-height: 1; letter-spacing: .03em; }
        .sidebar-logo .subtitle { font-size: 1.05rem; font-weight: 500; line-height: 1.3; opacity: .88; }
        .sidebar-hint { font-size: .86rem; opacity: .86; line-height: 1.35; margin-top: -.35rem; margin-bottom: .55rem; }
        .title-main { font-size: 2.45rem; font-weight: 900; color: #0B2459; line-height: 1.04; margin-bottom: .15rem; }
        .title-sub { font-size: 1.05rem; color: #667085; margin-bottom: .4rem; }
        .filter-pill { background: #FFFFFF; border: 1px solid #DDE6F2; border-radius: 16px; padding: .78rem .95rem; color: #0B2459; font-weight: 750; text-align: center; box-shadow: 0 4px 14px rgba(11,36,89,0.05); white-space: nowrap; }
        .metric-card { background: #FFFFFF; border: 1px solid #E1E9F3; border-radius: 20px; padding: 1rem 1rem; min-height: 132px; box-shadow: 0 10px 24px rgba(15, 23, 42, 0.055); }
        .metric-wrap { display: flex; gap: .85rem; align-items: center; }
        .metric-icon { width: 58px; height: 58px; min-width: 58px; border-radius: 17px; display: flex; align-items: center; justify-content: center; color: white; font-size: 1.55rem; font-weight: 900; box-shadow: inset 0 -10px 20px rgba(0,0,0,.08); }
        .icon-blue { background: linear-gradient(135deg, #125CC9, #2682EA); }
        .icon-green { background: linear-gradient(135deg, #239B56, #4CCB75); }
        .icon-orange { background: linear-gradient(135deg, #D97706, #F59E0B); }
        .icon-purple { background: linear-gradient(135deg, #7C3AED, #A78BFA); }
        .metric-label { font-size: .93rem; color: #31456F; font-weight: 800; margin-bottom: .18rem; }
        .metric-value { font-size: 1.82rem; color: #0B2459; font-weight: 900; margin-bottom: .16rem; line-height: 1.08; }
        .metric-sub { font-size: .88rem; color: #667085; line-height: 1.25; }
        .section-title { font-size: 1.13rem; font-weight: 900; color: #0B2459; margin-bottom: .36rem; }
        .small-note { font-size: .88rem; color: #667085; margin-top: .2rem; line-height: 1.35; }
        .insight-card { background: #FFFFFF; border: 1px solid #E1E9F3; border-radius: 18px; padding: .95rem; min-height: 145px; box-shadow: 0 8px 20px rgba(15, 23, 42, 0.045); }
        .insight-title { font-size: .92rem; color: #31456F; font-weight: 800; margin-bottom: .35rem; }
        .insight-value { font-size: 1.35rem; color: #0B2459; font-weight: 900; line-height: 1.15; margin-bottom: .35rem; }
        .insight-desc { font-size: .9rem; color: #667085; line-height: 1.35; }
        .patient-box { background: linear-gradient(135deg, #FFFFFF, #F7FBFF); border: 1px solid #DDE6F2; border-radius: 20px; padding: 1rem; box-shadow: 0 10px 24px rgba(15,23,42,.055); }
        .patient-name { font-size: 1.5rem; color:#0B2459; font-weight: 900; line-height: 1.15; }
        .patient-sub { font-size: .95rem; color:#667085; margin-top:.1rem; }
        .tag { display:inline-block; padding:.25rem .55rem; margin:.25rem .25rem 0 0; border-radius:999px; background:#EEF5FF; color:#0B4B93; font-size:.85rem; font-weight:700; }
        div[data-testid="stVerticalBlockBorderWrapper"] { background: #FFFFFF; border: 1px solid #E1E9F3; border-radius: 18px; box-shadow: 0 8px 20px rgba(15, 23, 42, 0.045); padding: .45rem .6rem; }
        div[data-testid="stDataFrame"] { border: none; }
        .footer-note { font-size: .88rem; color: #667085; margin-top: .4rem; padding-bottom: .5rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------------------------------------------------------------
# Leitura e utilitários
# -----------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def load_data(path: Path) -> tuple[pd.DataFrame, dict[str, pd.DataFrame]]:
    if not path.exists():
        st.error(f"Arquivo de dados não encontrado: {path}")
        st.stop()

    sheets = pd.read_excel(path, sheet_name=None)
    if "base_processos" not in sheets:
        st.error("A aba 'base_processos' não foi encontrada no Excel. Use a versão atualizada do arquivo de dados.")
        st.stop()

    base = sheets["base_processos"].copy()
    base["data_ajuizamento"] = pd.to_datetime(base["data_ajuizamento"], errors="coerce")
    base["custo_estimado"] = pd.to_numeric(base["custo_estimado"], errors="coerce").fillna(0)
    base["idade"] = pd.to_numeric(base["idade"], errors="coerce")
    base["tempo_tramitacao_dias"] = pd.to_numeric(base["tempo_tramitacao_dias"], errors="coerce")
    base["tempo_liminar_dias"] = pd.to_numeric(base["tempo_liminar_dias"], errors="coerce")
    base["ano_mes"] = base["data_ajuizamento"].dt.to_period("M").astype(str)
    base["_search"] = (
        base[["paciente", "paciente_id", "cpf_mascarado", "processo_id"]]
        .fillna("")
        .astype(str)
        .agg(" ".join, axis=1)
        .map(normalize_text)
    )
    return base, sheets


def normalize_text(value: object) -> str:
    txt = str(value).lower().strip()
    txt = unicodedata.normalize("NFKD", txt).encode("ascii", "ignore").decode("ascii")
    return txt


def br_int(n: float | int) -> str:
    if pd.isna(n):
        return "0"
    return f"{int(round(float(n))):,}".replace(",", ".")


def br_float(n: float | int, casas: int = 1) -> str:
    if pd.isna(n):
        n = 0
    return f"{float(n):,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def br_money(n: float | int, compact: bool = True) -> str:
    n = 0 if pd.isna(n) else float(n)
    if compact and abs(n) >= 1_000_000:
        return f"R$ {br_float(n / 1_000_000, 1)} Mi"
    if compact and abs(n) >= 1_000:
        return f"R$ {br_float(n / 1_000, 1)} Mil"
    return f"R$ {br_float(n, 2)}"


def pct(part: float, total: float) -> float:
    return 0.0 if total in [0, None] or pd.isna(total) else (float(part) / float(total)) * 100


def fmt_periodo(df: pd.DataFrame) -> str:
    if df.empty:
        return "Sem dados"
    inicio = df["data_ajuizamento"].min().strftime("%d/%m/%Y")
    fim = df["data_ajuizamento"].max().strftime("%d/%m/%Y")
    return f"{inicio} a {fim}"


def section_title(title: str) -> None:
    st.markdown(f'<div class="section-title">{title}</div>', unsafe_allow_html=True)


def metric_card(label: str, value: str, subtitle: str, icon: str, icon_cls: str = "icon-blue") -> None:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-wrap">
                <div class="metric-icon {icon_cls}">{icon}</div>
                <div>
                    <div class="metric-label">{label}</div>
                    <div class="metric-value">{value}</div>
                    <div class="metric-sub">{subtitle}</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def insight_card(title: str, value: str, desc: str) -> None:
    st.markdown(
        f"""
        <div class="insight-card">
            <div class="insight-title">{title}</div>
            <div class="insight-value">{value}</div>
            <div class="insight-desc">{desc}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def chart_layout(height: int = 310, showlegend: bool = False, legend: dict | None = None) -> dict:
    return dict(
        height=height,
        margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(color="#0B2459", family="Inter"),
        showlegend=showlegend,
        legend=legend or dict(),
    )


def empty_fig(msg: str = "Sem dados para os filtros selecionados", height: int = 300) -> go.Figure:
    fig = go.Figure()
    fig.update_layout(**chart_layout(height=height), annotations=[dict(text=msg, x=0.5, y=0.5, showarrow=False, font=dict(size=16, color="#667085"))])
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    return fig


def barh(df: pd.DataFrame, label_col: str, value_col: str, text_col: str | None = None, height: int = 320, color: str = "#125CC9") -> go.Figure:
    if df.empty:
        return empty_fig(height=height)
    d = df.sort_values(value_col, ascending=True).copy()
    fig = go.Figure(go.Bar(
        x=d[value_col],
        y=d[label_col],
        orientation="h",
        marker_color=color,
        text=d[text_col] if text_col else d[value_col],
        textposition="outside",
        cliponaxis=False,
    ))
    fig.update_layout(**chart_layout(height=height))
    fig.update_xaxes(showgrid=True, gridcolor="#E8EDF5", zeroline=False)
    fig.update_yaxes(showgrid=False)
    return fig


def donut(df: pd.DataFrame, label_col: str, value_col: str, center: str, height: int = 320) -> go.Figure:
    if df.empty or df[value_col].sum() == 0:
        return empty_fig(height=height)
    fig = go.Figure(go.Pie(
        labels=df[label_col],
        values=df[value_col],
        hole=.60,
        textinfo="percent",
        sort=False,
        marker_colors=["#125CC9", "#39A74A", "#2EA8C5", "#EAB308", "#8C67BE", "#94A3B8", "#F97316"],
    ))
    fig.update_layout(
        **chart_layout(height=height, showlegend=True, legend=dict(x=1.02, y=.5)),
        annotations=[dict(text=center, x=.5, y=.5, showarrow=False, font=dict(size=18, color="#0B2459"))],
    )
    return fig


def monthly_line(df: pd.DataFrame, value_col: str, title_name: str, money: bool = False, height: int = 320) -> go.Figure:
    if df.empty:
        return empty_fig(height=height)
    d = df.groupby("ano_mes", as_index=False).agg(valor=(value_col, "sum"))
    d = d.sort_values("ano_mes")
    d["label"] = pd.to_datetime(d["ano_mes"] + "-01").dt.strftime("%m/%Y")
    d["texto"] = d["valor"].map(lambda v: br_money(v) if money else br_int(v))
    fig = go.Figure(go.Scatter(
        x=d["label"],
        y=d["valor"],
        mode="lines+markers+text",
        text=d["texto"],
        textposition="top center",
        name=title_name,
        line=dict(color="#125CC9", width=3),
        marker=dict(size=8, color="#125CC9"),
    ))
    fig.update_layout(**chart_layout(height=height, showlegend=True, legend=dict(orientation="h", y=1.12, x=0)))
    fig.update_yaxes(showgrid=True, gridcolor="#E8EDF5", zeroline=False)
    fig.update_xaxes(showgrid=False)
    return fig


def top_group(df: pd.DataFrame, group_col: str, value_col: str, n: int = 10, op: str = "count") -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=[group_col, "valor"])
    if op == "sum":
        out = df.groupby(group_col, as_index=False)[value_col].sum().rename(columns={value_col: "valor"})
    elif op == "mean":
        out = df.groupby(group_col, as_index=False)[value_col].mean().rename(columns={value_col: "valor"})
    else:
        out = df.groupby(group_col, as_index=False).size().rename(columns={"size": "valor"})
    return out.sort_values("valor", ascending=False).head(n)


def to_excel_bytes(df: pd.DataFrame) -> bytes:
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="dados_filtrados", index=False)
    return output.getvalue()


def multiselect_sidebar(label: str, df: pd.DataFrame, column: str) -> list[str]:
    opts = sorted([x for x in df[column].dropna().astype(str).unique().tolist() if x.strip()])
    return st.multiselect(label, opts, placeholder="Todos")


base, all_sheets = load_data(DATA_FILE)
base_total = len(base)
base_cost_total = float(base["custo_estimado"].sum())

# -----------------------------------------------------------------------------
# Sidebar e filtros
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown(
        '<div class="sidebar-logo"><div class="icon">⚖️➕</div><div class="title">SAÚDE PÚBLICA</div><div class="subtitle">Judicialização na Saúde</div></div>',
        unsafe_allow_html=True,
    )
    pagina = st.radio(
        "Navegação",
        ["Visão Geral", "Demandas", "Custos", "Geografia", "Pacientes", "Base de Dados"],
        label_visibility="collapsed",
    )

    st.markdown("---")
    st.subheader("Filtros")
    st.markdown('<div class="sidebar-hint">Os gráficos e indicadores mudam automaticamente conforme os filtros.</div>', unsafe_allow_html=True)

    min_date = base["data_ajuizamento"].min().date()
    max_date = base["data_ajuizamento"].max().date()
    periodo_sel = st.date_input("Período", value=(min_date, max_date), min_value=min_date, max_value=max_date, format="DD/MM/YYYY")

    busca_paciente = st.text_input(
        "Buscar paciente / CPF / processo",
        placeholder="Ex.: Maria, PAC00042 ou PROC-2025",
        help="Esse campo procura em nome, código do paciente, CPF mascarado e número do processo.",
    )

    paciente_ids_sel: list[str] = []
    if len(normalize_text(busca_paciente)) >= 2:
        matches = base[base["_search"].str.contains(normalize_text(busca_paciente), na=False)].copy()
        pessoas = (
            matches[["paciente_id", "paciente", "cpf_mascarado"]]
            .drop_duplicates("paciente_id")
            .sort_values("paciente")
            .head(150)
        )
        label_to_id = {
            f"{row.paciente} — {row.paciente_id} — {row.cpf_mascarado}": row.paciente_id
            for row in pessoas.itertuples(index=False)
        }
        escolhidos = st.multiselect("Selecionar paciente encontrado", list(label_to_id.keys()), placeholder="Opcional")
        paciente_ids_sel = [label_to_id[x] for x in escolhidos]
        if len(matches["paciente_id"].unique()) > 150:
            st.caption("Mostrando os 150 primeiros pacientes encontrados. Refine a busca para localizar um paciente específico.")

    with st.expander("Filtros demográficos", expanded=False):
        sexo_sel = multiselect_sidebar("Sexo", base, "sexo")
        faixa_sel = multiselect_sidebar("Faixa etária", base, "faixa_etaria")
        condicao_sel = multiselect_sidebar("Condição clínica", base, "condicao_clinica")
        sus_sel = multiselect_sidebar("SUS exclusivo", base, "sus_exclusivo")
        renda_sel = multiselect_sidebar("Renda familiar", base, "renda_familiar")

    with st.expander("Filtros geográficos", expanded=False):
        regiao_sel = multiselect_sidebar("Região", base, "regiao")
        uf_sel = multiselect_sidebar("UF", base, "uf")
        mun_sel = multiselect_sidebar("Município", base, "municipio")

    with st.expander("Filtros processuais", expanded=False):
        natureza_sel = multiselect_sidebar("Natureza", base, "natureza")
        tipo_sel = multiselect_sidebar("Tipo de demanda", base, "tipo_demanda")
        item_sel = multiselect_sidebar("Item demandado", base, "item_demandado")
        esp_sel = multiselect_sidebar("Especialidade", base, "especialidade")
        esfera_sel = multiselect_sidebar("Esfera", base, "esfera")
        fase_sel = multiselect_sidebar("Fase processual", base, "fase_processual")
        desfecho_sel = multiselect_sidebar("Desfecho", base, "desfecho")
        liminar_sel = multiselect_sidebar("Liminar", base, "liminar")
        urgente_sel = multiselect_sidebar("Urgente", base, "urgente")

    st.markdown("---")
    st.caption("Para limpar os filtros, desmarque as seleções ou recarregue a página.")


def apply_filters(df: pd.DataFrame) -> pd.DataFrame:
    d = df.copy()
    if isinstance(periodo_sel, tuple) and len(periodo_sel) == 2:
        inicio, fim = periodo_sel
        d = d[(d["data_ajuizamento"].dt.date >= inicio) & (d["data_ajuizamento"].dt.date <= fim)]

    query = normalize_text(busca_paciente)
    if query:
        d = d[d["_search"].str.contains(query, na=False)]
    if paciente_ids_sel:
        d = d[d["paciente_id"].isin(paciente_ids_sel)]

    field_filters = {
        "sexo": sexo_sel,
        "faixa_etaria": faixa_sel,
        "condicao_clinica": condicao_sel,
        "sus_exclusivo": sus_sel,
        "renda_familiar": renda_sel,
        "regiao": regiao_sel,
        "uf": uf_sel,
        "municipio": mun_sel,
        "natureza": natureza_sel,
        "tipo_demanda": tipo_sel,
        "item_demandado": item_sel,
        "especialidade": esp_sel,
        "esfera": esfera_sel,
        "fase_processual": fase_sel,
        "desfecho": desfecho_sel,
        "liminar": liminar_sel,
        "urgente": urgente_sel,
    }
    for col, selected in field_filters.items():
        if selected:
            d = d[d[col].astype(str).isin(selected)]
    return d


dff = apply_filters(base)

# -----------------------------------------------------------------------------
# Cabeçalho
# -----------------------------------------------------------------------------
subtitles = {
    "Visão Geral": "Indicadores executivos, evolução mensal e principais recortes.",
    "Demandas": "Análise de tipos de demanda, fase processual, liminares e urgência.",
    "Custos": "Custos totais, ticket médio, medicamentos/insumos e especialidades mais caras.",
    "Geografia": "Distribuição por região, UF e município.",
    "Pacientes": "Perfil dos pacientes e busca individual.",
    "Base de Dados": "Tabela detalhada, exportação e conferência dos registros filtrados.",
}

h1, h2, h3 = st.columns([7.7, 2.2, 1.8])
with h1:
    st.markdown('<div class="title-main">Dashboard de Judicialização na Saúde</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="title-sub">{subtitles[pagina]}</div>', unsafe_allow_html=True)
with h2:
    st.markdown(f'<div class="filter-pill">📅&nbsp;&nbsp;{fmt_periodo(dff)}</div>', unsafe_allow_html=True)
with h3:
    st.markdown(f'<div class="filter-pill">🔎&nbsp;&nbsp;{br_int(len(dff))} registros</div>', unsafe_allow_html=True)

if dff.empty:
    st.warning("Nenhum registro foi encontrado com os filtros selecionados. Ajuste ou limpe os filtros na barra lateral.")
    st.stop()

# -----------------------------------------------------------------------------
# KPIs baseados no filtro
# -----------------------------------------------------------------------------
def filtered_kpis(df: pd.DataFrame) -> dict[str, float]:
    total = len(df)
    pacientes = df["paciente_id"].nunique()
    custo = df["custo_estimado"].sum()
    ticket = df["custo_estimado"].mean() if total else 0
    tempo = df["tempo_tramitacao_dias"].mean() if total else 0
    liminar = pct((df["liminar"] == "Sim").sum(), total)
    urg = int((df["urgente"] == "Sim").sum())
    proced = pct(df["desfecho"].isin(["Procedente", "Parcialmente procedente"]).sum(), total)
    idade_media = df.drop_duplicates("paciente_id")["idade"].mean()
    mun = df["municipio"].nunique()
    return {
        "total": total,
        "pacientes": pacientes,
        "custo": custo,
        "ticket": ticket,
        "tempo": tempo,
        "liminar": liminar,
        "urgentes": urg,
        "procedencia": proced,
        "idade_media": idade_media,
        "municipios": mun,
    }

k = filtered_kpis(dff)
participacao = pct(len(dff), base_total)
part_custo = pct(k["custo"], base_cost_total)

# -----------------------------------------------------------------------------
# Páginas
# -----------------------------------------------------------------------------
if pagina == "Visão Geral":
    cols = st.columns(5)
    cards = [
        ("Total de Processos", br_int(k["total"]), f"{br_float(participacao)}% da base total", "📄", "icon-blue"),
        ("Pacientes Ativos", br_int(k["pacientes"]), f"{br_float(pct(k['pacientes'], base['paciente_id'].nunique()))}% dos pacientes", "👥", "icon-green"),
        ("Custo Total", br_money(k["custo"]), f"{br_float(part_custo)}% do custo total", "$", "icon-green"),
        ("Tempo Médio", f"{br_int(k['tempo'])} dias", "tempo médio de tramitação", "⏱", "icon-orange"),
        ("Taxa de Procedência", f"{br_float(k['procedencia'])}%", "procedente + parcialmente", "🛡", "icon-purple"),
    ]
    for col, card in zip(cols, cards):
        with col:
            metric_card(*card)

    a, b, c = st.columns([1.75, 1.2, 1.15])
    with a:
        with st.container(border=True):
            section_title("Evolução mensal dos processos")
            st.plotly_chart(monthly_line(dff.assign(qtd=1), "qtd", "Processos", height=340), use_container_width=True, config={"displayModeBar": False})
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
            cidade_maior = top_group(dff, "municipio", "processo_id", 1, "count")
            ticket_top = dff.groupby("paciente", as_index=False)["custo_estimado"].sum().sort_values("custo_estimado", ascending=False).head(1)
            i1, i2 = st.columns(2)
            with i1:
                insight_card("Liminares", f"{p_lim}%", "Percentual de processos com decisão liminar no recorte filtrado.")
            with i2:
                insight_card("Urgentes", br_int(k["urgentes"]), "Total de processos classificados como urgentes.")
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
                fig = px.scatter_mapbox(
                    geo,
                    lat="latitude",
                    lon="longitude",
                    size="processos",
                    color="regiao",
                    hover_name="municipio",
                    hover_data={"uf": True, "processos": True, "pacientes": True, "custo_total": ":,.2f", "latitude": False, "longitude": False},
                    zoom=3.2,
                    height=390,
                )
                fig.update_layout(mapbox_style="open-street-map", margin=dict(l=0, r=0, t=0, b=0), legend=dict(orientation="h", y=1.02, x=0))
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
        with st.container(border=True):
            st.markdown(
                f"""
                <div class="patient-box">
                    <div class="patient-name">{p['paciente']}</div>
                    <div class="patient-sub">{p['paciente_id']} · CPF {p['cpf_mascarado']} · {p['municipio']}/{p['uf']}</div>
                    <span class="tag">{p['sexo']}</span>
                    <span class="tag">{int(p['idade'])} anos</span>
                    <span class="tag">{p['faixa_etaria']}</span>
                    <span class="tag">{p['condicao_clinica']}</span>
                    <span class="tag">SUS exclusivo: {p['sus_exclusivo']}</span>
                    <span class="tag">Renda: {p['renda_familiar']}</span>
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
            show_cols = ["processo_id", "data_ajuizamento", "natureza", "tipo_demanda", "item_demandado", "especialidade", "fase_processual", "desfecho", "liminar", "urgente", "custo_estimado"]
            tabela_p = p_df[show_cols].copy()
            tabela_p["data_ajuizamento"] = tabela_p["data_ajuizamento"].dt.strftime("%d/%m/%Y")
            tabela_p["custo_estimado"] = tabela_p["custo_estimado"].map(lambda x: br_money(x, compact=False))
            st.dataframe(tabela_p.rename(columns={
                "processo_id": "Processo", "data_ajuizamento": "Data", "natureza": "Natureza", "tipo_demanda": "Tipo", "item_demandado": "Item", "especialidade": "Especialidade", "fase_processual": "Fase", "desfecho": "Desfecho", "liminar": "Liminar", "urgente": "Urgente", "custo_estimado": "Custo"
            }), hide_index=True, use_container_width=True, height=260)

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
            section_title("Pacientes com maior custo acumulado")
            tab = dff.groupby(["paciente_id", "paciente", "cpf_mascarado"], as_index=False).agg(
                processos=("processo_id", "count"),
                custo_total=("custo_estimado", "sum"),
                ultimo_processo=("data_ajuizamento", "max"),
            ).sort_values("custo_total", ascending=False).head(12)
            tab["custo_total"] = tab["custo_total"].map(lambda x: br_money(x, compact=False))
            tab["ultimo_processo"] = tab["ultimo_processo"].dt.strftime("%d/%m/%Y")
            st.dataframe(tab.rename(columns={"paciente_id": "ID", "paciente": "Paciente", "cpf_mascarado": "CPF", "processos": "Processos", "custo_total": "Custo Total", "ultimo_processo": "Último Processo"}), hide_index=True, use_container_width=True, height=310)

else:  # Base de Dados
    cols = st.columns(5)
    cards = [
        ("Registros filtrados", br_int(k["total"]), f"{br_float(participacao)}% da base", "🔎", "icon-blue"),
        ("Pacientes", br_int(k["pacientes"]), "pacientes únicos", "👥", "icon-green"),
        ("Custo total", br_money(k["custo"]), "soma filtrada", "$", "icon-green"),
        ("Municípios", br_int(k["municipios"]), "municípios únicos", "📍", "icon-purple"),
        ("Itens", br_int(dff["item_demandado"].nunique()), "itens distintos", "💊", "icon-orange"),
    ]
    for col, card in zip(cols, cards):
        with col:
            metric_card(*card)

    with st.container(border=True):
        section_title("Base detalhada filtrada")
        st.caption("A tabela abaixo respeita todos os filtros da barra lateral, inclusive o filtro por paciente.")
        show_cols = [
            "processo_id", "data_ajuizamento", "paciente_id", "paciente", "cpf_mascarado", "sexo", "idade", "faixa_etaria",
            "municipio", "uf", "regiao", "condicao_clinica", "natureza", "tipo_demanda", "item_demandado", "especialidade",
            "esfera", "fase_processual", "desfecho", "liminar", "urgente", "tempo_tramitacao_dias", "custo_estimado"
        ]
        table = dff[show_cols].copy().sort_values("data_ajuizamento", ascending=False)
        table["data_ajuizamento"] = table["data_ajuizamento"].dt.strftime("%d/%m/%Y")
        table_view = table.rename(columns={
            "processo_id": "Processo", "data_ajuizamento": "Data", "paciente_id": "ID Paciente", "paciente": "Paciente", "cpf_mascarado": "CPF",
            "sexo": "Sexo", "idade": "Idade", "faixa_etaria": "Faixa", "municipio": "Município", "uf": "UF", "regiao": "Região",
            "condicao_clinica": "Condição", "natureza": "Natureza", "tipo_demanda": "Tipo", "item_demandado": "Item", "especialidade": "Especialidade",
            "esfera": "Esfera", "fase_processual": "Fase", "desfecho": "Desfecho", "liminar": "Liminar", "urgente": "Urgente",
            "tempo_tramitacao_dias": "Tempo (dias)", "custo_estimado": "Custo Estimado"
        })
        st.dataframe(
            table_view,
            hide_index=True,
            use_container_width=True,
            height=520,
            column_config={"Custo Estimado": st.column_config.NumberColumn("Custo Estimado", format="R$ %.2f")},
        )

        csv = table.to_csv(index=False).encode("utf-8-sig")
        xlsx = to_excel_bytes(table)
        c1, c2, c3 = st.columns([1, 1, 4])
        with c1:
            st.download_button("⬇️ Baixar CSV", data=csv, file_name="dados_filtrados_judicializacao_saude.csv", mime="text/csv", use_container_width=True)
        with c2:
            st.download_button("⬇️ Baixar Excel", data=xlsx, file_name="dados_filtrados_judicializacao_saude.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
        with c3:
            st.info("Para filtrar por paciente: use o campo 'Buscar paciente / CPF / processo' na barra lateral. Também dá para selecionar um paciente exato quando a busca encontrar resultados.")

st.markdown(
    '<div class="footer-note">ⓘ Dados fictícios para fins acadêmicos/demonstração. Os indicadores são recalculados dinamicamente conforme o período e os filtros selecionados.</div>',
    unsafe_allow_html=True,
)
