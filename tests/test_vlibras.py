from unittest.mock import patch

from petsus.dashboard.vlibras import VLIBRAS_SCRIPT_URL, render_vlibras


def test_vlibras_targets_app_document_and_guards_reruns():
    with patch("petsus.dashboard.vlibras.components.html") as render:
        render_vlibras()
    markup = render.call_args.args[0]
    assert "window.parent.document" in markup
    assert "if (doc.getElementById(id)) return" in markup
    assert VLIBRAS_SCRIPT_URL in markup
    assert "script.onerror" in markup
    assert "script.remove()" in markup
    assert render.call_args.kwargs == {"height": 0, "scrolling": False}


def test_vlibras_is_loaded_before_authentication():
    import ast
    from pathlib import Path

    tree = ast.parse(Path("app.py").read_text(encoding="utf-8"))
    calls = {
        node.func.id: node.lineno
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        and node.func.id in {"render_vlibras", "render_auth_gate"}
    }
    assert calls["render_vlibras"] < calls["render_auth_gate"]
