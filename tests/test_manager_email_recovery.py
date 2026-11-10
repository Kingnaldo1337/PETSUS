import pytest

from auth import AuthStore


@pytest.fixture
def recovery(tmp_path, monkeypatch):
    store = AuthStore(tmp_path / "users.db")
    manager = store.create_user("98765432100", "senha-gestor", "Gestor", "gestor")
    config = {
        "PETSUS_RECUPERAR_EMAIL_GESTOR": "true",
        "PETSUS_GESTOR_CPF": "987.654.321-00",
        "PETSUS_GESTOR_EMAIL": "gestor@example.com",
    }
    monkeypatch.setattr("auth.setting", lambda name, default="": config.get(name, default))
    return store, manager, config


def test_recovery_repairs_email_once_invalidates_old_sessions_and_still_requires_code(recovery):
    store, original, config = recovery
    user = store.authenticate("98765432100", "senha-gestor")
    assert store.login_email(user.id) == "gestor@example.com"
    assert user.session_version == original.session_version + 1
    assert user.must_change_password  # Reparo não remove a troca obrigatória.
    token, code = store.start_login_challenge(user)
    with pytest.raises(ValueError, match="inválido"):
        store.verify_login_challenge(token, "invalid")
    assert store.verify_login_challenge(token, code).id == user.id
    config["PETSUS_GESTOR_EMAIL"] = "outro@example.com"
    again = store.authenticate("98765432100", "senha-gestor")
    assert store.login_email(user.id) == "gestor@example.com"
    assert again.session_version == user.session_version
    with store._connect() as conn:
        assert conn.execute("SELECT COUNT(*) FROM auth_audit WHERE event = 'manager_email_restored'").fetchone()[0] == 1


@pytest.mark.parametrize("name,value", [
    ("PETSUS_RECUPERAR_EMAIL_GESTOR", "false"),
    ("PETSUS_GESTOR_CPF", "12345678900"),
    ("PETSUS_GESTOR_EMAIL", "email-invalido"),
    ("PETSUS_GESTOR_EMAIL", ""),
])
def test_recovery_requires_explicit_private_configuration(recovery, name, value):
    store, manager, config = recovery
    config[name] = value
    store.authenticate("98765432100", "senha-gestor")
    assert store.login_email(manager.id) is None


def test_wrong_password_does_not_repair_email(recovery):
    store, manager, _ = recovery
    assert store.authenticate("98765432100", "senha-incorreta") is None
    assert store.login_email(manager.id) is None


def test_recovery_refuses_multiple_managers(recovery):
    store, manager, _ = recovery
    store.create_user("11122233344", "senha-segura", "Outro gestor", "gestor", email="outro@example.com")
    store.authenticate("98765432100", "senha-gestor")
    assert store.login_email(manager.id) is None


def test_recovery_refuses_email_owned_by_another_account(recovery):
    store, manager, _ = recovery
    store.create_user("12345678900", "senha-paciente", "Paciente", "usuario", "PAC1", email="gestor@example.com")
    store.authenticate("98765432100", "senha-gestor")
    assert store.login_email(manager.id) is None


def test_recovery_does_not_modify_patient_accounts(recovery):
    store, _, config = recovery
    patient = store.create_user("12345678900", "senha-paciente", "Paciente", "usuario", "PAC1", email="paciente@example.com")
    config["PETSUS_GESTOR_CPF"] = "12345678900"
    store.authenticate("12345678900", "senha-paciente")
    assert store.login_email(patient.id) == "paciente@example.com"
