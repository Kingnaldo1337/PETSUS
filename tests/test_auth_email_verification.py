from datetime import datetime, timezone

from auth import (
    OTP_TTL_MINUTES,
    AuthStore,
    _new_registration_challenge,
    _otp_digest,
    is_valid_email,
    normalize_email,
)


def test_email_normalization_and_validation():
    assert normalize_email(" Paciente@Exemplo.COM ") == "paciente@exemplo.com"
    assert is_valid_email("paciente@exemplo.com")
    assert not is_valid_email("email-invalido")


def test_registration_code_is_six_digits_hashed_and_expires():
    challenge, code = _new_registration_challenge(
        "123.456.789-00", "paciente@example.com", "scrypt$hash", "PAC1", "Paciente"
    )

    assert len(code) == 6
    assert code.isdigit()
    assert code not in str(challenge)
    assert challenge["code_digest"] == _otp_digest(code, str(challenge["code_salt"]))
    expires_at = datetime.fromisoformat(str(challenge["expires_at"]))
    seconds_remaining = (expires_at - datetime.now(timezone.utc)).total_seconds()
    assert 0 < seconds_remaining <= OTP_TTL_MINUTES * 60


def test_database_migration_adds_email_and_enforces_uniqueness(tmp_path):
    store = AuthStore(tmp_path / "users.db")
    first = store.create_user(
        "12345678900", "senha-segura", "Paciente 1", "usuario", "PAC1", "one@example.com"
    )
    assert first.patient_id == "PAC1"

    try:
        store.create_user(
            "98765432100", "outra-senha", "Paciente 2", "usuario", "PAC2", "ONE@example.com"
        )
    except ValueError as exc:
        assert "e-mail" in str(exc)
    else:
        raise AssertionError("E-mail duplicado deveria ser rejeitado")


def test_password_recovery_requires_cpf_email_and_birth_date(tmp_path):
    store = AuthStore(tmp_path / "users.db")
    user = store.create_user(
        "12345678900", "senha-antiga", "Paciente", "usuario", "PAC1",
        "paciente@example.com", "1990-05-20",
    )

    assert store.find_password_reset_account(
        "123.456.789-00", "PACIENTE@example.com", "1990-05-20"
    ) == (user.id, "paciente@example.com")
    assert store.find_password_reset_account(
        "12345678900", "paciente@example.com", "1991-05-20"
    ) is None

    store.update_password(user.id, "senha-nova-segura")
    assert store.authenticate("12345678900", "senha-nova-segura") is not None
    assert store.authenticate("12345678900", "senha-antiga") is None


def test_manager_can_find_and_update_one_account_by_cpf(tmp_path):
    store = AuthStore(tmp_path / "users.db")
    patient = store.create_user(
        "12345678900", "senha-antiga", "Paciente", "usuario", "PAC1",
        "paciente@example.com", "1990-05-20",
    )

    account = store.find_account_by_cpf("123.456.789-00")
    assert account is not None
    assert account["id"] == patient.id
    assert account["role"] == "usuario"
    assert "password_hash" not in account
    assert "birth_date_lookup" not in account

    store.update_account_by_manager(
        patient.id,
        "usuario",
        email="novo@example.com",
        new_password="senha-nova-segura",
        birth_date="1992-07-15",
    )

    assert store.authenticate("12345678900", "senha-nova-segura") is not None
    assert store.find_password_reset_account(
        "12345678900", "novo@example.com", "1992-07-15"
    ) == (patient.id, "novo@example.com")


def test_manager_update_cannot_change_an_account_using_wrong_role(tmp_path):
    store = AuthStore(tmp_path / "users.db")
    patient = store.create_user(
        "12345678900", "senha-antiga", "Paciente", "usuario", "PAC1",
        "paciente@example.com", "1990-05-20",
    )

    try:
        store.update_account_by_manager(
            patient.id, "gestor", email="indevido@example.com"
        )
    except ValueError as exc:
        assert "não encontrada" in str(exc)
    else:
        raise AssertionError("A atualização com um perfil incorreto deveria ser rejeitada")


def test_manager_can_delete_patient_but_not_self(tmp_path):
    store = AuthStore(tmp_path / "users.db")
    manager = store.create_user(
        "98765432100", "senha-gestor", "Gestor", "gestor",
        email="gestor@example.com",
    )
    patient = store.create_user(
        "12345678900", "senha-paciente", "Paciente", "usuario", "PAC1",
        "paciente@example.com", "1990-05-20",
    )

    store.delete_account_by_manager(patient.id, "usuario", manager.id)
    assert store.find_account_by_cpf("12345678900") is None
    assert store.authenticate("12345678900", "senha-paciente") is None

    try:
        store.delete_account_by_manager(manager.id, "gestor", manager.id)
    except ValueError as exc:
        assert "própria conta" in str(exc)
    else:
        raise AssertionError("O gestor não deveria conseguir excluir a própria conta")
