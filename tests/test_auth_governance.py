from datetime import datetime, timedelta, timezone
import sqlite3

import pytest
from streamlit.testing.v1 import AppTest

from auth import AuthStore
from petsus.auth.models import AuthUser
from petsus.governance import GovernanceStore


def make_accounts(tmp_path):
    store = AuthStore(tmp_path / "users.db")
    manager = store.create_user("98765432100", "senha-gestor", "Gestor", "gestor", email="gestor@example.com")
    patient = store.create_user("12345678900", "senha-paciente", "Paciente", "usuario", "PAC1", "paciente@example.com")
    return store, manager, patient


def test_temporary_password_must_change_and_old_sessions_are_invalidated(tmp_path):
    store, manager, patient = make_accounts(tmp_path)
    assert manager.must_change_password
    assert not patient.must_change_password
    with pytest.raises(ValueError, match="diferente"):
        store.update_password(manager.id, "senha-gestor")
    store.update_password(manager.id, "minha-senha-nova")
    manager_after = store.get_active_user(manager.id)
    assert not manager_after.must_change_password
    assert manager_after.session_version == manager.session_version + 1
    store.update_account_by_manager(patient.id, "usuario", new_password="senha-temporaria", acting_manager_id=manager.id)
    patient_after = store.authenticate("12345678900", "senha-temporaria")
    assert patient_after.must_change_password
    assert patient_after.session_version == patient.session_version + 1


def test_mfa_hashes_codes_is_single_use_and_survives_restarting_store(tmp_path):
    store, manager, _ = make_accounts(tmp_path)
    token, code = store.start_login_challenge(manager)
    with store._connect() as conn:
        row = dict(conn.execute("SELECT * FROM login_challenges").fetchone())
    assert code not in str(row)
    assert token not in str(row)
    restarted = AuthStore(store.db_path)
    assert restarted.verify_login_challenge(token, code).id == manager.id
    with pytest.raises(ValueError, match="inválido"):
        restarted.verify_login_challenge(token, code)
    assert any(event["event"] == "login" for event in store.audit_events(manager.id))


def test_mfa_attempt_limit_expiration_and_revocation(tmp_path):
    store, manager, patient = make_accounts(tmp_path)
    token, code = store.start_login_challenge(patient)
    wrong = "000000" if code != "000000" else "111111"
    for _ in range(5):
        with pytest.raises(ValueError):
            store.verify_login_challenge(token, wrong)
    with pytest.raises(ValueError):
        store.verify_login_challenge(token, code)

    token, code = store.start_login_challenge(patient)
    with store._connect() as conn:
        conn.execute("UPDATE login_challenges SET expires_at = ?", ((datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat(),))
    with pytest.raises(ValueError):
        store.verify_login_challenge(token, code)

    token, code = store.start_login_challenge(patient)
    store.set_account_active(patient.id, False, manager.id)
    assert store.get_active_user(patient.id) is None
    with pytest.raises(ValueError):
        store.verify_login_challenge(token, code)
    store.set_account_active(patient.id, True, manager.id)
    assert store.get_active_user(patient.id).session_version > patient.session_version


def test_access_review_is_minimal_and_patient_cannot_administer_access(tmp_path):
    store, manager, patient = make_accounts(tmp_path)
    rows = store.list_accounts(manager.id)
    assert len(rows) == 2
    assert all(not {"email", "name", "patient_id", "password_hash", "cpf_lookup"}.intersection(row) for row in rows)
    assert "12345678900" not in str(rows)
    with pytest.raises(ValueError, match="gestor"):
        store.list_accounts(patient.id)
    with pytest.raises(ValueError, match="gestor"):
        store.set_account_active(manager.id, False, patient.id)
    with pytest.raises(ValueError, match="própria"):
        store.set_account_active(manager.id, False, manager.id)
    with pytest.raises(ValueError, match="gestor"):
        store.update_account_by_manager(manager.id, "gestor", email="changed@example.com", acting_manager_id=patient.id)


def test_recovery_cannot_override_later_access_changes(tmp_path):
    store, manager, patient = make_accounts(tmp_path)
    store.update_account_by_manager(patient.id, "usuario", email="novo@example.com", acting_manager_id=manager.id)
    with pytest.raises(ValueError, match="conta foi alterada"):
        store.update_password(patient.id, "senha-antigo-email", expected_session_version=patient.session_version)
    assert store.authenticate("12345678900", "senha-paciente") is not None


def test_repeated_password_failures_are_limited_and_audited(tmp_path):
    store, manager, _ = make_accounts(tmp_path)
    for _ in range(10):
        assert store.authenticate("98765432100", "errada") is None
    assert store.authenticate("98765432100", "senha-gestor") is None
    events = store.audit_events(manager.id)
    assert events[0]["outcome"] == "rate_limited"
    assert "senha-gestor" not in str(events)


def test_legacy_managers_are_migrated_to_required_password_change(tmp_path):
    path = tmp_path / "legacy.db"
    with sqlite3.connect(path) as conn:
        conn.execute("CREATE TABLE users(id INTEGER PRIMARY KEY, cpf_lookup TEXT, cpf_display TEXT, password_hash TEXT, role TEXT, patient_id TEXT, name TEXT, active INTEGER, created_at TEXT)")
        conn.execute("INSERT INTO users VALUES(1, 'lookup', '987.***.***-00', 'scrypt$hash', 'gestor', NULL, 'Gestor', 1, '2025-01-01')")
    store = AuthStore(path)
    assert store.get_active_user(1).must_change_password
    assert store.get_active_user(1).session_version == 1


def test_feedback_is_owned_and_only_managers_can_respond(tmp_path):
    store = GovernanceStore(tmp_path / "governance.db")
    manager = AuthUser(1, "Gestor", "gestor", None, "987.***.***-00")
    patient = AuthUser(2, "Paciente", "usuario", "PAC1", "123.***.***-00")
    other = AuthUser(3, "Outra conta", "usuario", "PAC2", "456.***.***-00")
    feedback_id = store.submit_feedback(patient, "Erro nos dados", "O prazo do meu processo precisa de conferência.", "PROC1")
    assert store.list_feedback(other) == []
    assert len(store.list_feedback(patient)) == len(store.list_feedback(manager)) == 1
    with pytest.raises(ValueError, match="restrita"):
        store.update_feedback(other, feedback_id, "Resolvido", "Alterado")
    store.update_feedback(manager, feedback_id, "Em análise", "A equipe está conferindo a fonte.")
    assert store.list_feedback(patient)[0]["response"] == "A equipe está conferindo a fonte."


def test_sus_uses_standard_score_and_usage_is_anonymous(tmp_path):
    store = GovernanceStore(tmp_path / "governance.db")
    manager = AuthUser(1, "Gestor", "gestor", None, "987.***.***-00")
    patient = AuthUser(2, "Paciente", "usuario", "PAC1", "123.***.***-00")
    assert store.submit_sus(patient, [5, 1] * 5) == 100
    assert store.submit_sus(patient, [1, 5] * 5) == 0
    assert store.sus_summary(manager) == {"count": 2, "average_score": 50.0}
    with pytest.raises(ValueError):
        store.submit_sus(patient, [5] * 9)
    store.record_page_view("usuario", "Meu processo", "random-session-token")
    store.record_page_view("usuario", "Meu processo", "random-session-token")
    assert store.usage_summary(manager)[0]["views"] == 1
    with store._connect() as conn:
        sus_columns = {row["name"] for row in conn.execute("PRAGMA table_info(sus_responses)")}
        view_columns = {row["name"] for row in conn.execute("PRAGMA table_info(page_views)")}
    assert not {"user_id", "patient_id", "cpf", "name"}.intersection(sus_columns | view_columns)
    with pytest.raises(ValueError, match="restrita"):
        store.usage_summary(patient)


def test_data_reviews_are_linked_to_file_hash_and_audited(tmp_path):
    store = GovernanceStore(tmp_path / "governance.db")
    manager = AuthUser(1, "Gestor", "gestor", None, "987.***.***-00")
    patient = AuthUser(2, "Paciente", "usuario", "PAC1", "123.***.***-00")
    fingerprint = "a" * 64
    with pytest.raises(ValueError, match="restrita"):
        store.record_data_review(patient, fingerprint, "Dados conferidos.")
    store.record_data_review(manager, fingerprint, "Tipos, datas e quantidade de linhas conferidos.")
    assert store.latest_data_review(manager, fingerprint)["reviewer_id"] == manager.id
    assert store.latest_data_review(manager, "b" * 64) is None
    with store._connect() as conn:
        assert conn.execute("SELECT event FROM governance_audit").fetchone()[0] == "data_review"


def test_auth_gate_blocks_dashboard_until_temporary_password_is_changed(tmp_path, monkeypatch):
    monkeypatch.setattr("auth.mfa_required", lambda: False)
    store, _, _ = make_accounts(tmp_path)
    script = f"""
from pathlib import Path
import pandas as pd
import streamlit as st
from auth import AuthStore, render_auth_gate
store = AuthStore(Path({str(store.db_path)!r}))
user = render_auth_gate(store, pd.DataFrame())
st.success('CONTEUDO PROTEGIDO')
"""
    app = AppTest.from_string(script).run()
    app.text_input[0].set_value("98765432100")
    app.text_input[1].set_value("senha-gestor")
    next(button for button in app.button if button.label == "Entrar").click().run()
    assert not app.exception
    assert app.title[0].value == "Defina sua própria senha"
    assert not any(item.value == "CONTEUDO PROTEGIDO" for item in app.success)
    app.text_input[0].set_value("senha-propria-nova")
    app.text_input[1].set_value("senha-propria-nova")
    next(button for button in app.button if button.label == "Salvar minha senha").click().run()
    assert not app.exception
    assert any(item.value == "CONTEUDO PROTEGIDO" for item in app.success)


def test_auth_gate_requires_real_email_delivery_and_second_factor(tmp_path, monkeypatch):
    store, _, _ = make_accounts(tmp_path)
    monkeypatch.setattr("auth.mfa_required", lambda: True)
    monkeypatch.setattr("auth.smtp_configured", lambda: True)
    delivered = {}

    def send_email(recipient, code):
        delivered["recipient"] = recipient
        delivered["code"] = code

    monkeypatch.setattr("auth.send_verification_code", send_email)
    script = f"""
from pathlib import Path
import pandas as pd
import streamlit as st
from auth import AuthStore, render_auth_gate
store = AuthStore(Path({str(store.db_path)!r}))
user = render_auth_gate(store, pd.DataFrame())
st.success('CONTEUDO PROTEGIDO')
"""
    app = AppTest.from_string(script).run()
    app.text_input[0].set_value("12345678900")
    app.text_input[1].set_value("senha-paciente")
    next(button for button in app.button if button.label == "Entrar").click().run()
    assert not app.exception
    assert delivered["recipient"] == "paciente@example.com"
    assert not any(item.value == "CONTEUDO PROTEGIDO" for item in app.success)
    next(field for field in app.text_input if field.label == "Código de acesso").set_value(delivered["code"])
    next(button for button in app.button if button.label == "Confirmar acesso").click().run()
    assert not app.exception
    assert any(item.value == "CONTEUDO PROTEGIDO" for item in app.success)


def test_enabling_mfa_invalidates_sessions_authenticated_with_password_only(tmp_path, monkeypatch):
    store, _, patient = make_accounts(tmp_path)
    monkeypatch.setattr("auth.mfa_required", lambda: True)
    script = f"""
from pathlib import Path
import pandas as pd
import streamlit as st
from auth import AuthStore, render_auth_gate
store = AuthStore(Path({str(store.db_path)!r}))
user = render_auth_gate(store, pd.DataFrame())
st.success('CONTEUDO PROTEGIDO')
"""
    app = AppTest.from_string(script)
    app.session_state["auth_user"] = patient.__dict__
    app.session_state["auth_mfa_verified"] = False
    app.run()
    assert not app.exception
    assert not any(item.value == "CONTEUDO PROTEGIDO" for item in app.success)
    assert next(button for button in app.button if button.label == "Entrar")


def test_login_has_header_accessibility_without_sidebar_and_keeps_input(tmp_path, monkeypatch):
    monkeypatch.setattr("auth.mfa_required", lambda: False)
    store, _, _ = make_accounts(tmp_path)
    script = f"""
from pathlib import Path
import pandas as pd
from auth import AuthStore, render_auth_gate
render_auth_gate(AuthStore(Path({str(store.db_path)!r})), pd.DataFrame())
"""
    app = AppTest.from_string(script).run()
    assert not app.exception
    assert not app.sidebar.children
    assert app.button(key="auth_text_small")
    app.text_input[0].set_value("12345678900")
    app.button(key="auth_text_large").click().run()
    assert not app.exception
    assert app.session_state["a11y_large_text"] is True
    assert app.text_input[0].value == "12345678900"
    app.button(key="auth_contrast").click().run()
    assert not app.exception
    assert app.session_state["a11y_contrast"] is True
    assert not app.sidebar.children
    app.button(key="auth_text_small").click().run()
    assert not app.exception
    assert app.session_state["a11y_large_text"] is False
