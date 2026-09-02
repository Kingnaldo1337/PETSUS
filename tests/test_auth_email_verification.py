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
