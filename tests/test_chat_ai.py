import io
import json
from unittest.mock import patch
from urllib.error import HTTPError, URLError

import pytest

from petsus.dashboard.chat_ai import ChatServiceError, generate_answer


def settings(name, default=""):
    return {"GEMINI_API_KEY": "test-secret"}.get(name, default)


def test_request_has_context_redacts_identifiers_and_keeps_key_in_header():
    result = {"candidates": [{"content": {"parts": [{"text": "Abra Meu acompanhamento."}]}}]}
    with patch("petsus.dashboard.chat_ai.setting", side_effect=settings), patch(
        "petsus.dashboard.chat_ai.urlopen", return_value=io.BytesIO(json.dumps(result).encode())
    ) as request:
        answer = generate_answer("Meu CPF é 123.456.789-00", [
            {"role": "user", "text": "Meu email é pessoa@example.com"},
            {"role": "assistant", "text": "Como posso ajudar?"},
        ], is_manager=False)
    assert answer == "Abra Meu acompanhamento."
    call = request.call_args
    body = json.loads(call.args[0].data)
    assert "test-secret" not in call.args[0].full_url
    assert call.args[0].get_header("X-goog-api-key") == "test-secret"
    assert "123.456.789-00" not in json.dumps(body)
    assert "pessoa@example.com" not in json.dumps(body)
    assert body["contents"][1]["role"] == "model"
    assert "Meu acompanhamento" in body["systemInstruction"]["parts"][0]["text"]
    assert call.kwargs["timeout"] == 20


@pytest.mark.parametrize("failure, expected", [
    (HTTPError("https://example.com", 429, "private", {}, None), "limite de uso"),
    (HTTPError("https://example.com", 400, "test-secret", {}, None), "HTTP 400"),
    (HTTPError("https://example.com", 401, "test-secret", {}, None), "HTTP 401"),
    (HTTPError("https://example.com", 403, "test-secret", {}, None), "HTTP 403"),
    (HTTPError("https://example.com", 404, "test-secret", {}, None), "GEMINI_MODEL"),
    (URLError("test-secret"), "conectar"),
])
def test_errors_are_safe_and_actionable(failure, expected):
    with patch("petsus.dashboard.chat_ai.setting", side_effect=settings), patch(
        "petsus.dashboard.chat_ai.urlopen", side_effect=failure
    ), pytest.raises(ChatServiceError) as error:
        generate_answer("Olá", [], is_manager=False)
    assert expected in str(error.value)
    assert "test-secret" not in str(error.value)


def test_missing_key_does_not_make_network_request():
    with patch("petsus.dashboard.chat_ai.setting", return_value=""), patch(
        "petsus.dashboard.chat_ai.urlopen"
    ) as request, pytest.raises(ChatServiceError):
        generate_answer("Olá", [], is_manager=False)
    request.assert_not_called()
