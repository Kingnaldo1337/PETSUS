from __future__ import annotations

import hashlib
import re
import secrets
from datetime import datetime, timedelta, timezone

OTP_TTL_MINUTES = 10
OTP_MAX_ATTEMPTS = 5
EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def normalize_email(value: str) -> str:
    return (value or "").strip().lower()


def is_valid_email(value: str) -> bool:
    return bool(EMAIL_RE.fullmatch(normalize_email(value)))


def otp_digest(code: str, salt: str) -> str:
    return hashlib.sha256(f"{salt}:{code}".encode("utf-8")).hexdigest()


def new_registration_challenge(
    cpf: str, email: str, password_hash: str, patient_id: str, name: str,
    birth_date: str | None = None,
) -> tuple[dict[str, object], str]:
    code = f"{secrets.randbelow(1_000_000):06d}"
    salt = secrets.token_hex(16)
    challenge: dict[str, object] = {
        "cpf": re.sub(r"\D", "", cpf or ""),
        "email": normalize_email(email),
        "password_hash": password_hash,
        "patient_id": patient_id,
        "name": name,
        "birth_date": birth_date or "",
        "code_salt": salt,
        "code_digest": otp_digest(code, salt),
        "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=OTP_TTL_MINUTES)).isoformat(),
        "attempts": 0,
    }
    return challenge, code
