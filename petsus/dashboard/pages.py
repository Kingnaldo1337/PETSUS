"""Ponto único de despacho das páginas.

Mantém a assinatura de renderização estável enquanto cada tela pode evoluir
independentemente dos serviços de dados e autenticação.
"""

from dashboard.views import render_pages


def render_dashboard_page(page, filtered, base, metrics, participation, cost_share, patient_ids):
    return render_pages(page, filtered, base, metrics, participation, cost_share, patient_ids)
