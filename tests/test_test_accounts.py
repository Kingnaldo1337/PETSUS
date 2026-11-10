import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from auth import AuthStore
from petsus.auth.testing import bootstrap_test_accounts


@pytest.fixture
def test_setup(tmp_path, monkeypatch):
    config = {
        "PETSUS_TEST_MODE": "true",
        "PETSUS_TEST_GESTOR_CPF": "11111111111",
        "PETSUS_TEST_GESTOR_SENHA": "senha-gestor-teste",
        "PETSUS_TEST_PACIENTE_CPF": "22222222222",
        "PETSUS_TEST_PACIENTE_SENHA": "senha-paciente-teste",
    }
    for key, value in config.items():
        monkeypatch.setenv(key, value)
    monkeypatch.delenv("PETSUS_TEST_PACIENTE_ID", raising=False)
    monkeypatch.setattr("auth.mfa_required", lambda: True)
    store = AuthStore(tmp_path / "users.db")
    base = pd.DataFrame({"paciente_id": ["PAC1", "PAC2"]})
    return store, base


def test_only_marked_test_accounts_skip_mfa_and_still_require_correct_password(test_setup):
    store, base = test_setup
    bootstrap_test_accounts(store, base)
    manager = store.authenticate("11111111111", "senha-gestor-teste")
    patient = store.authenticate("22222222222", "senha-paciente-teste")
    assert manager.is_manager and not patient.is_manager
    assert patient.patient_id == "PAC1"
    assert not manager.must_change_password
    assert not store.requires_second_factor(manager)
    assert not store.requires_second_factor(patient)
    assert store.authenticate("11111111111", "senha-errada") is None
    regular = store.create_user("33333333333", "senha-normal", "Gestor normal", "gestor", email="normal@example.com")
    assert store.requires_second_factor(regular)
    with store._connect() as conn:
        assert conn.execute("SELECT COUNT(*) FROM users WHERE is_test_account = 1").fetchone()[0] == 2


@pytest.mark.parametrize("cpf,password,role", [
    ("11111111111", "senha-gestor-teste", "gestor"),
    ("22222222222", "senha-paciente-teste", "usuario"),
])
def test_test_login_does_not_send_email_and_session_is_blocked_when_disabled(test_setup, monkeypatch, cpf, password, role):
    store, base = test_setup
    bootstrap_test_accounts(store, base)
    def refuse_email(*args):
        raise AssertionError("Login de teste não deve enviar e-mail")
    monkeypatch.setattr("auth.send_verification_code", refuse_email)
    script = f'''
from pathlib import Path
import pandas as pd
import streamlit as st
from auth import AuthStore, render_auth_gate
user = render_auth_gate(AuthStore(Path({str(store.db_path)!r})), pd.DataFrame({{"paciente_id": ["PAC1", "PAC2"]}}))
st.success("PROTEGIDO:" + user.role)
'''
    app = AppTest.from_string(script).run()
    app.text_input[0].input(cpf)
    app.text_input[1].input(password)
    next(button for button in app.button if button.label == "Entrar").click().run()
    assert not app.exception
    assert any(item.value == "PROTEGIDO:" + role for item in app.success)
    assert app.session_state["auth_mfa_verified"] is False
    monkeypatch.setenv("PETSUS_TEST_MODE", "false")
    app.run()
    assert not app.exception
    assert not any(item.value.startswith("PROTEGIDO:") for item in app.success)
    assert store.authenticate(cpf, password) is None


def test_bootstrap_does_not_convert_existing_accounts_or_reset_test_passwords(test_setup, monkeypatch):
    store, base = test_setup
    regular = store.create_user("11111111111", "senha-original", "Gestor normal", "gestor", email="normal@example.com")
    with pytest.raises(ValueError, match="conta normal"):
        bootstrap_test_accounts(store, base)
    assert store.requires_second_factor(regular)
    assert store.authenticate("11111111111", "senha-original") is not None


def test_bootstrap_is_idempotent_and_does_not_overwrite_password_or_patient(test_setup, monkeypatch):
    store, base = test_setup
    monkeypatch.setenv("PETSUS_TEST_PACIENTE_ID", "PAC2")
    bootstrap_test_accounts(store, base)
    monkeypatch.setenv("PETSUS_TEST_GESTOR_SENHA", "outra-senha-configurada")
    bootstrap_test_accounts(store, base)
    assert store.authenticate("11111111111", "senha-gestor-teste") is not None
    assert store.authenticate("11111111111", "outra-senha-configurada") is None
    assert store.authenticate("22222222222", "senha-paciente-teste").patient_id == "PAC2"


def test_disabled_mode_blocks_test_accounts_even_when_global_mfa_is_not_required(test_setup, monkeypatch):
    store, base = test_setup
    bootstrap_test_accounts(store, base)
    user = store.authenticate("11111111111", "senha-gestor-teste")
    monkeypatch.setenv("PETSUS_TEST_MODE", "false")
    monkeypatch.setattr("auth.mfa_required", lambda: False)
    assert store.authenticate("11111111111", "senha-gestor-teste") is None
    assert store.get_active_user(user.id) is None


def test_test_creation_requires_private_authorization_and_a_free_patient(test_setup, monkeypatch):
    store, base = test_setup
    with pytest.raises(ValueError, match="autorizada"):
        store.create_user("33333333333", "senha-teste", "Outro", "gestor", is_test_account=True)
    store.create_user("44444444444", "senha-normal", "Paciente normal", "usuario", "PAC1", email="p1@example.com")
    store.create_user("55555555555", "senha-normal", "Outro paciente", "usuario", "PAC2", email="p2@example.com")
    with pytest.raises(ValueError, match="paciente livre"):
        bootstrap_test_accounts(store, base)


def test_test_manager_does_not_remove_protection_of_last_regular_manager(test_setup):
    store, base = test_setup
    bootstrap_test_accounts(store, base)
    assert not store.has_manager()
    test_manager = store.authenticate("11111111111", "senha-gestor-teste")
    regular = store.create_user("33333333333", "senha-normal", "Gestor normal", "gestor", email="normal@example.com")
    assert store.has_manager()
    with pytest.raises(ValueError, match="último gestor"):
        store.set_account_active(regular.id, False, test_manager.id)
    with pytest.raises(ValueError, match="último gestor"):
        store.delete_account_by_manager(regular.id, "gestor", test_manager.id)
