"""Tradução dos rótulos internos do calendário do Streamlit 1.62."""
from __future__ import annotations

import json

import streamlit.components.v1 as components


CALENDAR_TRANSLATIONS = {
    "Date range": "Período",
    "Select...": "Selecionar...",
    "Select…": "Selecionar...",
    "Quick select a date range": "Selecionar um período",
    "Choose date": "Escolher data",
    "Clear date": "Limpar data",
    "Clear dates": "Limpar datas",
    "Today": "Hoje",
    "Yesterday": "Ontem",
    "Past Week": "Última semana",
    "Past Month": "Último mês",
    "Past 3 Months": "Últimos 3 meses",
    "Past 6 Months": "Últimos 6 meses",
    "Past Quarter": "Último trimestre",
    "Past Year": "Último ano",
    "Past 2 Years": "Últimos 2 anos",
    "Last 7 days": "Últimos 7 dias",
    "Last 30 days": "Últimos 30 dias",
    "This week": "Esta semana",
    "This month": "Este mês",
    "This year": "Este ano",
    "Use arrow keys to navigate dates. Enter to select. Escape to close.":
        "Use as setas para navegar pelas datas. Enter para selecionar. Esc para fechar.",
}

TABLE_TRANSLATIONS = {
    "Sort ascending": "Ordenar em ordem crescente",
    "Sort descending": "Ordenar em ordem decrescente",
    "Clear sort": "Limpar ordenação",
    "Statistics": "Estatísticas", "Format": "Formato",
    "Autosize": "Ajustar largura automaticamente",
    "Autosize all columns": "Ajustar largura de todas as colunas",
    "Pin column": "Fixar coluna", "Unpin column": "Desafixar coluna",
    "Hide column": "Ocultar coluna", "Show column": "Mostrar coluna",
    "Show all columns": "Mostrar todas as colunas",
    "Reset": "Redefinir", "Default": "Padrão", "Automatic": "Automático",
    "Number": "Número", "Integer": "Inteiro", "Decimal": "Decimal",
    "Percent": "Porcentagem", "Percentage": "Porcentagem",
    "Scientific": "Notação científica", "Engineering": "Notação de engenharia",
    "Compact": "Compacto", "Currency": "Moeda", "Accounting": "Contábil",
    "Date": "Data", "Time": "Hora", "Datetime": "Data e hora",
    "Duration": "Duração", "Relative": "Relativo", "Localized": "Localizado",
    "Count": "Contagem", "Total": "Total", "Sum": "Soma",
    "Mean": "Média", "Average": "Média", "Median": "Mediana",
    "Min": "Mínimo", "Max": "Máximo", "Minimum": "Mínimo", "Maximum": "Máximo",
    "Std dev": "Desvio padrão", "Standard deviation": "Desvio padrão",
    "Unique": "Valores distintos", "Distinct": "Valores distintos",
    "Missing": "Ausentes", "Empty": "Vazios", "Non-empty": "Preenchidos",
    "True": "Verdadeiro", "False": "Falso", "No data": "Sem dados",
    "Copy": "Copiar", "Copy column name": "Copiar nome da coluna",
    "Column menu": "Menu da coluna", "Button action menu": "Menu de ações",
    "Plain": "Simples", "Dollar": "Dólar", "Euro": "Euro", "Yen": "Iene",
    "Calendar": "Calendário", "Distance": "Tempo relativo",
    "25th percentile": "Percentil 25", "75th percentile": "Percentil 75",
    "Average length": "Comprimento médio", "Maximum length": "Comprimento máximo",
    "Minimum length": "Comprimento mínimo", "Range": "Amplitude",
    "Values": "Valores", "Based on sample": "Com base em uma amostra",
}


def render_calendar_portuguese() -> None:
    """Traduz calendários e menus de tabela, sem alterar valores das células."""
    runtime = """(() => {
        if (window.__dashjusPortugueseMenus) return;
        window.__dashjusPortugueseMenus = true;
        const translations = TRANSLATIONS;
        const dictionary = new Map(Object.entries(translations).map(([a,b]) => [a.toLowerCase(), b]));
        const translate = value => {
            const key = value.trim().toLowerCase();
            return dictionary.has(key) ? value.replace(value.trim(), dictionary.get(key)) : value;
        };
        const refresh = () => {
            document.querySelectorAll('[data-testid^="stDateInput"], [data-testid="stDataFrameColumnMenu"], [data-testid="stDataFrameColumnFormattingMenu"], [data-testid="stDataFrameStatisticsMenu"], [data-testid="stDataFrameButtonActionMenu"]').forEach(root => {
                const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
                let node;
                while ((node = walker.nextNode())) {
                    const next = translate(node.nodeValue);
                    if (next !== node.nodeValue) node.nodeValue = next;
                }
                [root, ...root.querySelectorAll('[aria-label], [title], [placeholder]')].forEach(element => {
                    ['aria-label', 'title', 'placeholder'].forEach(attribute => {
                        const value = element.getAttribute(attribute);
                        if (value === null) return;
                        const next = translate(value);
                        if (next !== value) element.setAttribute(attribute, next);
                    });
                });
            });
        };
        let pending = false;
        const observer = new MutationObserver(() => {
            if (pending) return;
            pending = true;
            requestAnimationFrame(() => { pending = false; refresh(); });
        });
        observer.observe(document.body, {childList:true, subtree:true, characterData:true,
            attributes:true, attributeFilter:['aria-label', 'title', 'placeholder']});
        refresh();
    })();""".replace("TRANSLATIONS", json.dumps(CALENDAR_TRANSLATIONS | TABLE_TRANSLATIONS, ensure_ascii=True))
    # O observador precisa pertencer à página principal, não ao iframe transitório.
    payload = json.dumps(runtime, ensure_ascii=True).replace("<", "\\u003c")
    components.html(
        '<script>try {const doc = window.parent.document;'
        'const script = doc.createElement("script");'
        f'script.textContent = {payload};'
        'doc.body.appendChild(script); script.remove();'
        '} catch (error) {console.warn("Calendário: tradução indisponível.", error);}</script>',
        height=0, scrolling=False,
    )
