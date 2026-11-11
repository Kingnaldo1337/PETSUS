"""Integração do widget oficial de Libras na página principal do Streamlit."""
from __future__ import annotations

import streamlit.components.v1 as components


VLIBRAS_SCRIPT_URL = "https://vlibras.gov.br/app/vlibras-plugin.js"


def render_vlibras() -> None:
    """Carrega uma única instância no documento que contém os textos do portal.

    components.html é um iframe: carregar o widget apenas dentro dele impediria
    a seleção dos textos do aplicativo. O script é inserido no documento pai,
    com a mesma origem, e permanece vivo entre as reexecuções do Streamlit.
    A versão atual do script oficial inicializa o widget automaticamente.
    """
    components.html(
        """<!doctype html><html><body><script>
        (() => {
            try {
                const doc = window.parent.document;
                const id = 'dashjus-vlibras-script';
                if (doc.getElementById(id)) return;
                const script = doc.createElement('script');
                script.id = id;
                script.src = '""" + VLIBRAS_SCRIPT_URL + """';
                script.async = true;
                // Permite nova tentativa no próximo rerun se a rede falhar.
                script.onerror = () => {
                    script.remove();
                    console.warn('Não foi possível carregar o VLibras.');
                };
                doc.body.appendChild(script);
            } catch (error) {
                console.warn('VLibras: acesso à página principal indisponível.', error);
            }
        })();
        </script></body></html>""",
        height=0,
        scrolling=False,
    )
