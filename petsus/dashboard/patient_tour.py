"""Tutorial do paciente com preferência local por conta e navegador."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import streamlit.components.v1 as components


def render_patient_tour(user, restart: int = 0, page: str = "Meu acompanhamento") -> None:
    owner = hashlib.sha256(str(user.id).encode()).hexdigest()[:24]
    runtime = Path(__file__).with_suffix(".js").read_text(encoding="utf-8")
    runtime = runtime.replace("__TOUR_CONFIG__", json.dumps({"owner": owner, "restart": restart, "page": page}))
    payload = json.dumps(runtime, ensure_ascii=True).replace("<", "\\u003c")
    components.html(
        '<script>try {const doc=window.parent.document;const script=doc.createElement("script");'
        f'script.textContent={payload};doc.body.appendChild(script);script.remove();'
        '} catch (_) {console.warn("Tutorial indisponível neste navegador.");}</script>',
        height=0, scrolling=False,
    )
