from __future__ import annotations

import hashlib
import hmac
import os
import re
import secrets
import smtplib
import sqlite3
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import streamlit as st

from petsus.auth.email import send_verification_code as _send_verification_email
from petsus.auth.email import mfa_required, smtp_configured, setting
from petsus.auth.models import AuthUser, ROLE_MANAGER, ROLE_USER
from petsus.auth.registration import (
    OTP_MAX_ATTEMPTS,
    OTP_TTL_MINUTES,
    is_valid_email,
    new_registration_challenge,
    normalize_email,
    otp_digest,
)
from petsus.auth.security import hash_password, verify_password
from petsus.dashboard.auth_ui import render_auth_intro, render_auth_shell

send_verification_code = _send_verification_email


def _otp_digest(code: str, salt: str) -> str:
    return otp_digest(code, salt)


def _new_registration_challenge(
    cpf: str, email: str, password_hash: str, patient_id: str, name: str,
    birth_date: str | None = None,
) -> tuple[dict[str, object], str]:
    return new_registration_challenge(cpf, email, password_hash, patient_id, name, birth_date)


def _new_password_reset_challenge(
    user_id: int, email: str, session_version: int | None = None
) -> tuple[dict[str, object], str]:
    code = f"{secrets.randbelow(1_000_000):06d}"
    salt = secrets.token_hex(16)
    challenge: dict[str, object] = {
        "user_id": int(user_id),
        "email": normalize_email(email),
        "code_salt": salt,
        "code_digest": _otp_digest(code, salt),
        "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=OTP_TTL_MINUTES)).isoformat(),
        "attempts": 0,
        "session_version": session_version,
    }
    return challenge, code


class AuthStore:
    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self.secret_path = self.db_path.with_suffix(".secret")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._pepper = self._load_or_create_pepper()
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=15)
        conn.row_factory = sqlite3.Row
        return conn

    def _load_or_create_pepper(self) -> bytes:
        env_secret = os.getenv("PETSUS_CPF_PEPPER", "").strip()
        if env_secret:
            return env_secret.encode("utf-8")
        if self.secret_path.exists():
            return self.secret_path.read_bytes()
        secret = secrets.token_bytes(32)
        self.secret_path.write_bytes(secret)
        try:
            os.chmod(self.secret_path, 0o600)
        except OSError:
            pass
        return secret

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cpf_lookup TEXT NOT NULL UNIQUE,
                    cpf_display TEXT NOT NULL,
                    password_hash TEXT NOT NULL,
                    role TEXT NOT NULL CHECK(role IN ('usuario', 'gestor')),
                    patient_id TEXT,
                    name TEXT NOT NULL,
                    active INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL,
                    UNIQUE(patient_id)
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_users_role ON users(role)")
            columns = {row["name"] for row in conn.execute("PRAGMA table_info(users)")}
            if "email" not in columns:
                conn.execute("ALTER TABLE users ADD COLUMN email TEXT")
            if "birth_date_lookup" not in columns:
                conn.execute("ALTER TABLE users ADD COLUMN birth_date_lookup TEXT")
            if "must_change_password" not in columns:
                conn.execute("ALTER TABLE users ADD COLUMN must_change_password INTEGER NOT NULL DEFAULT 0")
                conn.execute("UPDATE users SET must_change_password = 1 WHERE role = 'gestor'")
            if "session_version" not in columns:
                conn.execute("ALTER TABLE users ADD COLUMN session_version INTEGER NOT NULL DEFAULT 1")
            conn.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email_unique "
                "ON users(email) WHERE email IS NOT NULL"
            )
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS auth_audit (
                    id INTEGER PRIMARY KEY, actor_id INTEGER, subject_id INTEGER,
                    event TEXT NOT NULL, outcome TEXT NOT NULL, detail TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS login_failures (
                    id INTEGER PRIMARY KEY, account_key TEXT NOT NULL, created_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_login_failures_key_time ON login_failures(account_key, created_at);
                CREATE INDEX IF NOT EXISTS idx_auth_audit_subject_event_time ON auth_audit(subject_id, event, created_at);
                CREATE TABLE IF NOT EXISTS login_challenges (
                    token_digest TEXT PRIMARY KEY, user_id INTEGER NOT NULL, code_salt TEXT NOT NULL,
                    code_digest TEXT NOT NULL, expires_at TEXT NOT NULL, attempts INTEGER NOT NULL DEFAULT 0,
                    session_version INTEGER NOT NULL
                );
            """)

    @staticmethod
    def normalize_cpf(value: str) -> str:
        return re.sub(r"\D", "", value or "")

    @classmethod
    def format_cpf(cls, value: str) -> str:
        cpf = cls.normalize_cpf(value)
        if len(cpf) != 11:
            return value
        return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"

    @classmethod
    def mask_cpf(cls, value: str) -> str:
        cpf = cls.normalize_cpf(value)
        if len(cpf) != 11:
            return "CPF não informado"
        return f"{cpf[:3]}.***.***-{cpf[-2:]}"

    def _lookup_key(self, cpf: str) -> str:
        normalized = self.normalize_cpf(cpf)
        return hmac.new(self._pepper, normalized.encode("utf-8"), hashlib.sha256).hexdigest()

    def _birth_date_key(self, birth_date: str) -> str:
        return hmac.new(
            self._pepper, f"birth-date:{birth_date}".encode("utf-8"), hashlib.sha256
        ).hexdigest()

    @staticmethod
    def _hash_password(password: str) -> str:
        return hash_password(password)

    @staticmethod
    def _verify_password(password: str, encoded: str) -> bool:
        return verify_password(password, encoded)

    @staticmethod
    def _row_to_user(row: sqlite3.Row) -> AuthUser:
        return AuthUser(
            id=int(row["id"]),
            name=str(row["name"]),
            role=str(row["role"]),
            patient_id=row["patient_id"],
            cpf_display=str(row["cpf_display"]),
            must_change_password=bool(row["must_change_password"]),
            session_version=int(row["session_version"]),
        )

    @staticmethod
    def _audit(
        conn: sqlite3.Connection, event: str, *, actor_id: int | None = None,
        subject_id: int | None = None, outcome: str = "success", detail: str = "",
    ) -> None:
        conn.execute(
            "INSERT INTO auth_audit(actor_id, subject_id, event, outcome, detail, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (actor_id, subject_id, event, outcome, detail, datetime.now(timezone.utc).isoformat()),
        )

    def record_auth_event(self, user_id: int, event: str) -> None:
        if event not in {"login", "logout", "mfa_delivery_failed"}:
            raise ValueError("Evento de autenticação inválido.")
        with self._connect() as conn:
            self._audit(conn, event, actor_id=int(user_id), subject_id=int(user_id),
                        outcome="failed" if event == "mfa_delivery_failed" else "success")

    def authenticate(self, cpf: str, password: str) -> AuthUser | None:
        normalized = self.normalize_cpf(cpf)
        if len(normalized) != 11 or not password:
            with self._connect() as conn:
                self._audit(conn, "password_check", outcome="failed")
            return None
        lookup = self._lookup_key(normalized)
        cutoff = (datetime.now(timezone.utc) - timedelta(minutes=15)).isoformat()
        with self._connect() as conn:
            failures = conn.execute(
                "SELECT COUNT(*) FROM login_failures WHERE account_key = ? AND created_at >= ?",
                (lookup, cutoff),
            ).fetchone()[0]
            if failures >= 10:
                self._audit(conn, "password_check", outcome="rate_limited")
                return None
            row = conn.execute(
                "SELECT * FROM users WHERE cpf_lookup = ? AND active = 1",
                (lookup,),
            ).fetchone()
            valid = row is not None and self._verify_password(password, row["password_hash"])
            subject_id = int(row["id"]) if row is not None else None
            self._audit(conn, "password_check", subject_id=subject_id, outcome="success" if valid else "failed")
            if not valid:
                conn.execute(
                    "INSERT INTO login_failures(account_key, created_at) VALUES (?, ?)",
                    (lookup, datetime.now(timezone.utc).isoformat()),
                )
                return None
            conn.execute("DELETE FROM login_failures WHERE account_key = ?", (lookup,))
            row = self._restore_legacy_manager_email(conn, row, normalized)
        return self._row_to_user(row)

    def _restore_legacy_manager_email(self, conn: sqlite3.Connection, row: sqlite3.Row, cpf: str) -> sqlite3.Row:
        """Reparo opt-in após senha válida, restrito ao único gestor sem e-mail."""
        if (row["role"] != ROLE_MANAGER or is_valid_email(str(row["email"] or ""))
                or setting("PETSUS_RECUPERAR_EMAIL_GESTOR").lower() not in {"true", "1", "yes", "sim"}):
            return row
        configured_cpf = self.normalize_cpf(setting("PETSUS_GESTOR_CPF"))
        email = normalize_email(setting("PETSUS_GESTOR_EMAIL"))
        if len(configured_cpf) != 11 or configured_cpf != cpf or not is_valid_email(email):
            return row
        managers = conn.execute("SELECT COUNT(*) FROM users WHERE role = ? AND active = 1", (ROLE_MANAGER,)).fetchone()[0]
        if managers != 1 or conn.execute("SELECT 1 FROM users WHERE email = ? AND id != ?", (email, row["id"])).fetchone():
            return row
        conn.execute("UPDATE users SET email = ?, session_version = session_version + 1 WHERE id = ?", (email, row["id"]))
        conn.execute("DELETE FROM login_challenges WHERE user_id = ?", (row["id"],))
        self._audit(conn, "manager_email_restored", actor_id=int(row["id"]), subject_id=int(row["id"]), detail="private_configuration_after_password_check")
        return conn.execute("SELECT * FROM users WHERE id = ?", (row["id"],)).fetchone()

    def get_active_user(self, user_id: int) -> AuthUser | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM users WHERE id = ? AND active = 1",
                (int(user_id),),
            ).fetchone()
        return self._row_to_user(row) if row is not None else None

    @staticmethod
    def _require_active_manager(conn: sqlite3.Connection, manager_id: int) -> None:
        manager = conn.execute(
            "SELECT 1 FROM users WHERE id = ? AND role = ? AND active = 1",
            (int(manager_id), ROLE_MANAGER),
        ).fetchone()
        if manager is None:
            raise ValueError("O gestor responsável pela operação não está ativo.")

    def login_email(self, user_id: int) -> str | None:
        with self._connect() as conn:
            row = conn.execute("SELECT email FROM users WHERE id = ? AND active = 1", (int(user_id),)).fetchone()
        return str(row["email"]) if row is not None and row["email"] else None

    def start_login_challenge(self, user: AuthUser) -> tuple[str, str]:
        """Cria um código de uso único. O chamador só anuncia envio após SMTP confirmar."""
        token = secrets.token_urlsafe(32)
        code = f"{secrets.randbelow(1_000_000):06d}"
        salt = secrets.token_hex(16)
        expires = (datetime.now(timezone.utc) + timedelta(minutes=OTP_TTL_MINUTES)).isoformat()
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM users WHERE id = ? AND active = 1", (user.id,)).fetchone()
            if row is None or int(row["session_version"]) != user.session_version:
                raise ValueError("A conta foi alterada. Entre novamente.")
            if not is_valid_email(str(row["email"] or "")):
                raise ValueError("A conta precisa de e-mail válido. Procure a administração para atualizá-la.")
            # Tentativas persistem mesmo ao reiniciar o navegador.
            since = (datetime.now(timezone.utc) - timedelta(minutes=15)).isoformat()
            issues = conn.execute(
                "SELECT COUNT(*) FROM auth_audit WHERE subject_id = ? AND event = 'mfa_issued' AND created_at >= ?",
                (user.id, since),
            ).fetchone()[0]
            if issues >= 5:
                raise ValueError("Limite de códigos atingido. Aguarde 15 minutos para tentar novamente.")
            conn.execute("DELETE FROM login_challenges WHERE user_id = ? OR expires_at < ?", (user.id, datetime.now(timezone.utc).isoformat()))
            conn.execute(
                "INSERT INTO login_challenges(token_digest, user_id, code_salt, code_digest, expires_at, session_version) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (hashlib.sha256(token.encode()).hexdigest(), user.id, salt, _otp_digest(code, salt), expires, user.session_version),
            )
            self._audit(conn, "mfa_issued", subject_id=user.id)
        return token, code

    def cancel_login_challenge(self, token: str) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM login_challenges WHERE token_digest = ?", (hashlib.sha256(token.encode()).hexdigest(),))

    def verify_login_challenge(self, token: str, code: str) -> AuthUser:
        token_digest = hashlib.sha256(token.encode()).hexdigest()
        error = "Código inválido ou expirado. Inicie o acesso novamente."
        result = None
        with self._connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            pending = conn.execute("SELECT * FROM login_challenges WHERE token_digest = ?", (token_digest,)).fetchone()
            if pending is not None:
                user = conn.execute("SELECT * FROM users WHERE id = ? AND active = 1", (pending["user_id"],)).fetchone()
                expired = datetime.now(timezone.utc) > datetime.fromisoformat(pending["expires_at"])
                account_changed = user is None or int(user["session_version"]) != int(pending["session_version"])
                attempts = int(pending["attempts"]) + 1
                correct = len(code.strip()) == 6 and code.strip().isdigit() and hmac.compare_digest(
                    _otp_digest(code.strip(), pending["code_salt"]), pending["code_digest"]
                )
                if correct and not expired and not account_changed and attempts <= OTP_MAX_ATTEMPTS:
                    result = self._row_to_user(user)
                    conn.execute("DELETE FROM login_challenges WHERE token_digest = ?", (token_digest,))
                    self._audit(conn, "login", actor_id=result.id, subject_id=result.id, detail="email_second_factor")
                else:
                    self._audit(conn, "mfa_check", subject_id=int(pending["user_id"]), outcome="failed")
                    if expired or account_changed or attempts >= OTP_MAX_ATTEMPTS:
                        conn.execute("DELETE FROM login_challenges WHERE token_digest = ?", (token_digest,))
                    else:
                        conn.execute("UPDATE login_challenges SET attempts = ? WHERE token_digest = ?", (attempts, token_digest))
                        error = f"Código inválido. Restam {OTP_MAX_ATTEMPTS - attempts} tentativas."
        if result is None:
            raise ValueError(error)
        return result

    def list_accounts(self, acting_manager_id: int, limit: int = 500) -> list[dict[str, object]]:
        """Revisão mínima: não inclui nome, e-mail, CPF completo ou vínculo de paciente."""
        with self._connect() as conn:
            self._require_active_manager(conn, acting_manager_id)
            rows = conn.execute(
                "SELECT id, cpf_display, role, active, must_change_password, created_at, "
                "(SELECT MAX(created_at) FROM auth_audit WHERE subject_id = users.id AND event = 'login') AS last_login "
                "FROM users ORDER BY active DESC, id LIMIT ?", (max(1, min(int(limit), 500)),),
            ).fetchall()
            self._audit(conn, "account_access_review", actor_id=acting_manager_id)
        return [dict(row) for row in rows]

    def set_account_active(self, user_id: int, active: bool, acting_manager_id: int) -> None:
        if int(user_id) == int(acting_manager_id) and not active:
            raise ValueError("Você não pode revogar a própria conta enquanto está conectado.")
        with self._connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            self._require_active_manager(conn, acting_manager_id)
            target = conn.execute("SELECT role, active FROM users WHERE id = ?", (int(user_id),)).fetchone()
            if target is None:
                raise ValueError("Conta não encontrada.")
            if not active and target["role"] == ROLE_MANAGER and target["active"]:
                count = conn.execute("SELECT COUNT(*) FROM users WHERE role = ? AND active = 1", (ROLE_MANAGER,)).fetchone()[0]
                if count <= 1:
                    raise ValueError("O último gestor ativo não pode ter o acesso revogado.")
            conn.execute("UPDATE users SET active = ?, session_version = session_version + 1 WHERE id = ?", (int(active), int(user_id)))
            conn.execute("DELETE FROM login_challenges WHERE user_id = ?", (int(user_id),))
            self._audit(conn, "access_activated" if active else "access_revoked", actor_id=acting_manager_id, subject_id=int(user_id))

    def audit_events(self, acting_manager_id: int, limit: int = 200) -> list[dict[str, object]]:
        with self._connect() as conn:
            self._require_active_manager(conn, acting_manager_id)
            rows = conn.execute(
                "SELECT id, actor_id, subject_id, event, outcome, detail, created_at FROM auth_audit ORDER BY id DESC LIMIT ?",
                (max(1, min(int(limit), 500)),),
            ).fetchall()
        return [dict(row) for row in rows]

    def create_user(
        self,
        cpf: str,
        password: str,
        name: str,
        role: str,
        patient_id: str | None = None,
        email: str | None = None,
        birth_date: str | None = None,
        *,
        must_change_password: bool | None = None,
        acting_manager_id: int | None = None,
    ) -> AuthUser:
        normalized = self.normalize_cpf(cpf)
        if len(normalized) != 11:
            raise ValueError("Informe um CPF com 11 dígitos.")
        if len(password) < 8:
            raise ValueError("A senha deve ter pelo menos 8 caracteres.")
        return self.create_user_with_password_hash(
            normalized, self._hash_password(password), name, role, patient_id, email, birth_date,
            must_change_password=must_change_password, acting_manager_id=acting_manager_id,
        )

    def create_user_with_password_hash(
        self,
        cpf: str,
        password_hash: str,
        name: str,
        role: str,
        patient_id: str | None = None,
        email: str | None = None,
        birth_date: str | None = None,
        *,
        must_change_password: bool | None = None,
        acting_manager_id: int | None = None,
    ) -> AuthUser:
        normalized = self.normalize_cpf(cpf)
        normalized_email = normalize_email(email or "") or None
        normalized_birth_date = (birth_date or "").strip()
        if must_change_password is None:
            must_change_password = role == ROLE_MANAGER or acting_manager_id is not None
        if len(normalized) != 11:
            raise ValueError("Informe um CPF com 11 dígitos.")
        if not password_hash.startswith("scrypt$"):
            raise ValueError("Senha inválida.")
        if role not in {ROLE_USER, ROLE_MANAGER}:
            raise ValueError("Perfil de acesso inválido.")
        if role == ROLE_USER and not patient_id:
            raise ValueError("Usuários comuns precisam estar vinculados a um paciente.")
        if role == ROLE_USER and not is_valid_email(normalized_email or ""):
            raise ValueError("Informe um e-mail válido.")
        if role == ROLE_MANAGER:
            patient_id = None

        try:
            with self._connect() as conn:
                if acting_manager_id is not None:
                    self._require_active_manager(conn, acting_manager_id)
                cursor = conn.execute(
                    """
                    INSERT INTO users (cpf_lookup, cpf_display, password_hash, role, patient_id, name, email, birth_date_lookup, active, created_at, must_change_password)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
                    """,
                    (
                        self._lookup_key(normalized),
                        self.mask_cpf(normalized),
                        password_hash,
                        role,
                        patient_id,
                        name.strip() or "Usuário",
                        normalized_email,
                        self._birth_date_key(normalized_birth_date) if normalized_birth_date else None,
                        datetime.now(timezone.utc).isoformat(),
                        int(must_change_password),
                    ),
                )
                user_id = int(cursor.lastrowid)
                row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
                self._audit(conn, "account_created", actor_id=acting_manager_id, subject_id=user_id, detail=role)
        except sqlite3.IntegrityError as exc:
            message = str(exc).lower()
            if "patient_id" in message:
                raise ValueError("Este paciente já possui uma conta cadastrada.") from exc
            if "email" in message:
                raise ValueError("Este e-mail já possui uma conta cadastrada.") from exc
            raise ValueError("Este CPF já possui uma conta cadastrada.") from exc
        return self._row_to_user(row)

    def find_password_reset_account(
        self, cpf: str, email: str, birth_date: str
    ) -> tuple[int, str] | None:
        normalized_cpf = self.normalize_cpf(cpf)
        normalized_email = normalize_email(email)
        if len(normalized_cpf) != 11 or not is_valid_email(normalized_email) or not birth_date:
            return None
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT id, email, birth_date_lookup FROM users
                WHERE cpf_lookup = ? AND email = ? AND active = 1
                """,
                (self._lookup_key(normalized_cpf), normalized_email),
            ).fetchone()
        if row is None or not row["birth_date_lookup"]:
            return None
        if not hmac.compare_digest(str(row["birth_date_lookup"]), self._birth_date_key(birth_date)):
            return None
        return int(row["id"]), str(row["email"])

    def update_password(
        self, user_id: int, new_password: str, *, expected_session_version: int | None = None
    ) -> None:
        if len(new_password) < 8:
            raise ValueError("A senha deve ter pelo menos 8 caracteres.")
        with self._connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            account = conn.execute("SELECT password_hash, session_version FROM users WHERE id = ? AND active = 1", (int(user_id),)).fetchone()
            if expected_session_version is not None and (account is None or int(account["session_version"]) != expected_session_version):
                raise ValueError("A conta foi alterada. Inicie o acesso ou a recuperação novamente.")
            if account is not None and self._verify_password(new_password, account["password_hash"]):
                raise ValueError("Escolha uma senha diferente da senha atual.")
            cursor = conn.execute(
                "UPDATE users SET password_hash = ?, must_change_password = 0, session_version = session_version + 1 WHERE id = ? AND active = 1",
                (self._hash_password(new_password), int(user_id)),
            )
            updated_rows = cursor.rowcount
            cursor.close()
            if updated_rows == 1:
                conn.execute("DELETE FROM login_challenges WHERE user_id = ?", (int(user_id),))
                self._audit(conn, "password_changed", actor_id=int(user_id), subject_id=int(user_id))
        if updated_rows != 1:
            raise ValueError("Não foi possível atualizar a senha.")

    def find_account_by_cpf(self, cpf: str) -> dict[str, object] | None:
        """Consulta uma única conta pelo CPF, sem expor dados de autenticação."""
        normalized = self.normalize_cpf(cpf)
        if len(normalized) != 11:
            raise ValueError("Informe um CPF com 11 dígitos.")
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT id, cpf_display, role, patient_id, name, email,
                       birth_date_lookup IS NOT NULL AS has_birth_date, active, must_change_password
                FROM users
                WHERE cpf_lookup = ?
                LIMIT 1
                """,
                (self._lookup_key(normalized),),
            ).fetchone()
        return dict(row) if row is not None else None

    def update_account_by_manager(
        self,
        user_id: int,
        expected_role: str,
        *,
        email: str | None = None,
        new_password: str | None = None,
        birth_date: str | None = None,
        acting_manager_id: int | None = None,
    ) -> None:
        """Atualiza somente os campos administrativos permitidos para uma conta."""
        if expected_role not in {ROLE_USER, ROLE_MANAGER}:
            raise ValueError("Perfil de acesso inválido.")

        updates: list[str] = []
        values: list[object] = []
        if email is not None:
            normalized_email = normalize_email(email)
            if not is_valid_email(normalized_email):
                raise ValueError("Informe um e-mail válido.")
            updates.append("email = ?")
            values.append(normalized_email)
        if new_password:
            if len(new_password) < 8:
                raise ValueError("A senha deve ter pelo menos 8 caracteres.")
            updates.append("password_hash = ?")
            values.append(self._hash_password(new_password))
            updates.append("must_change_password = 1")
        if birth_date is not None:
            try:
                date.fromisoformat(birth_date)
            except ValueError as exc:
                raise ValueError("Informe uma data de nascimento válida.") from exc
            updates.append("birth_date_lookup = ?")
            values.append(self._birth_date_key(birth_date))

        if not updates:
            raise ValueError("Nenhuma alteração foi informada.")
        changes = [update.split(" =")[0] for update in updates if "password_hash" not in update]
        if new_password:
            changes.append("temporary_password")
        updates.append("session_version = session_version + 1")
        values.extend((int(user_id), expected_role))
        try:
            with self._connect() as conn:
                if acting_manager_id is not None:
                    self._require_active_manager(conn, acting_manager_id)
                cursor = conn.execute(
                    f"UPDATE users SET {', '.join(updates)} WHERE id = ? AND role = ? AND active = 1",
                    values,
                )
                updated_rows = cursor.rowcount
                cursor.close()
                if updated_rows == 1:
                    conn.execute("DELETE FROM login_challenges WHERE user_id = ?", (int(user_id),))
                    self._audit(conn, "account_updated", actor_id=acting_manager_id, subject_id=int(user_id), detail=",".join(changes))
        except sqlite3.IntegrityError as exc:
            if "email" in str(exc).lower():
                raise ValueError("Este e-mail já possui uma conta cadastrada.") from exc
            raise ValueError("Não foi possível atualizar a conta.") from exc
        if updated_rows != 1:
            raise ValueError("Conta ativa não encontrada para o perfil informado.")

    def delete_account_by_manager(
        self, user_id: int, expected_role: str, acting_manager_id: int
    ) -> None:
        """Exclui uma conta, protegendo o gestor atual e o último gestor ativo."""
        if expected_role not in {ROLE_USER, ROLE_MANAGER}:
            raise ValueError("Perfil de acesso inválido.")
        if int(user_id) == int(acting_manager_id):
            raise ValueError("Você não pode excluir a própria conta enquanto está conectado.")

        with self._connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            acting_manager = conn.execute(
                "SELECT 1 FROM users WHERE id = ? AND role = ? AND active = 1",
                (int(acting_manager_id), ROLE_MANAGER),
            ).fetchone()
            if acting_manager is None:
                raise ValueError("O gestor responsável pela operação não está ativo.")
            account = conn.execute(
                "SELECT role FROM users WHERE id = ? AND role = ? AND active = 1",
                (int(user_id), expected_role),
            ).fetchone()
            if account is None:
                raise ValueError("Conta ativa não encontrada para o perfil informado.")
            if expected_role == ROLE_MANAGER:
                manager_count = conn.execute(
                    "SELECT COUNT(*) FROM users WHERE role = ? AND active = 1",
                    (ROLE_MANAGER,),
                ).fetchone()[0]
                if int(manager_count) <= 1:
                    raise ValueError("O último gestor ativo não pode ser excluído.")
            cursor = conn.execute(
                "DELETE FROM users WHERE id = ? AND role = ? AND active = 1",
                (int(user_id), expected_role),
            )
            deleted_rows = cursor.rowcount
            cursor.close()
            if deleted_rows == 1:
                conn.execute("DELETE FROM login_challenges WHERE user_id = ?", (int(user_id),))
                self._audit(conn, "account_deleted", actor_id=int(acting_manager_id), subject_id=int(user_id))
        if deleted_rows != 1:
            raise ValueError("Não foi possível excluir a conta.")

    def has_manager(self) -> bool:
        with self._connect() as conn:
            row = conn.execute("SELECT 1 FROM users WHERE role = 'gestor' AND active = 1 LIMIT 1").fetchone()
        return row is not None

    def bootstrap_manager_from_env(self) -> None:
        if self.has_manager():
            return
        cpf = os.getenv("PETSUS_GESTOR_CPF", "").strip()
        password = os.getenv("PETSUS_GESTOR_SENHA", "").strip()
        name = os.getenv("PETSUS_GESTOR_NOME", "Gestor").strip() or "Gestor"
        birth_date = os.getenv("PETSUS_GESTOR_DATA_NASCIMENTO", "").strip() or None
        email = os.getenv("PETSUS_GESTOR_EMAIL", "").strip() or None
        if cpf and password:
            try:
                self.create_user(cpf, password, name, ROLE_MANAGER, email=email, birth_date=birth_date, must_change_password=True)
            except ValueError:
                pass


def _candidate_cpf_column(base: pd.DataFrame) -> str | None:
    for col in ("cpf", "cpf_completo", "cpf_paciente"):
        if col in base.columns:
            return col
    return None


def _normalize_data_cpf(value: object) -> str:
    if pd.isna(value):
        return ""
    if isinstance(value, int):
        return str(value).zfill(11)
    if isinstance(value, float) and value.is_integer():
        return str(int(value)).zfill(11)
    return AuthStore.normalize_cpf(str(value))


def resolve_patient_for_registration(
    base: pd.DataFrame, cpf: str
) -> tuple[str | None, str | None, str | None]:
    """Localiza automaticamente o paciente pelo CPF completo da base."""
    normalized = AuthStore.normalize_cpf(cpf)
    if len(normalized) != 11:
        return None, None, "Informe um CPF com 11 dígitos."

    cpf_col = _candidate_cpf_column(base)
    if cpf_col is None:
        return None, None, "A base não possui uma coluna de CPF completo para realizar o cadastro."

    cpf_values = base[cpf_col].map(_normalize_data_cpf)
    matches = base[cpf_values == normalized].copy()
    if matches.empty:
        return None, None, "O CPF informado não foi localizado na base de pacientes."

    patient_ids = matches["paciente_id"].astype(str).dropna().unique().tolist()
    if len(patient_ids) != 1:
        return None, None, "O CPF está associado a mais de um cadastro. Procure a administração do sistema."

    resolved_id = patient_ids[0]
    row = matches.iloc[0]
    return resolved_id, str(row.get("paciente", resolved_id)), None


def render_auth_gate(store: AuthStore, base: pd.DataFrame) -> AuthUser:
    """Render login/register screen and stop execution until authenticated."""
    st.session_state["_auth_store_path"] = str(store.db_path)
    current = st.session_state.get("auth_user")
    if isinstance(current, dict) and current.get("id"):
        active_user = store.get_active_user(int(current["id"]))
        assurance_ok = not mfa_required() or st.session_state.get("auth_mfa_verified") is True
        if active_user is not None and current.get("session_version") == active_user.session_version and assurance_ok:
            st.session_state["auth_user"] = active_user.__dict__
            if active_user.must_change_password:
                render_auth_shell()
                with st.container(key="auth_panel"):
                    _render_required_password_change(store, active_user)
                st.stop()
            return active_user
        st.session_state.pop("auth_user", None)
        st.session_state.pop("auth_mfa_verified", None)

    store.bootstrap_manager_from_env()

    render_auth_shell()
    render_auth_intro()

    with st.container(key="auth_panel"):
        login_tab, register_tab = st.tabs(["Entrar", "Criar conta"])
        with login_tab:
            _render_login(store)

        with register_tab:
            st.caption("Cadastro destinado a usuários comuns. Contas de gestor são criadas pela administração.")
            pending = st.session_state.get("registration_challenge")
            if not isinstance(pending, dict):
                with st.form("register_form", clear_on_submit=False):
                    reg_cpf = st.text_input(
                        "CPF",
                        placeholder="000.000.000-00",
                        key="reg_cpf",
                        help="O CPF precisa existir na base de pacientes.",
                    )
                    reg_email = st.text_input(
                        "E-mail",
                        placeholder="paciente@exemplo.com",
                        autocomplete="email",
                        help="Enviaremos um código de verificação para este endereço.",
                    )
                    reg_birth_date = st.date_input(
                        "Data de nascimento",
                        value=None,
                        min_value=date(1900, 1, 1),
                        max_value=date.today(),
                        format="DD/MM/YYYY",
                        help="Será usada, junto com CPF e e-mail, em uma futura recuperação de senha.",
                    )
                    reg_password = st.text_input("Crie uma senha", type="password", help="Mínimo de 8 caracteres.")
                    reg_submit = st.form_submit_button("Enviar código", use_container_width=True, type="primary")
                if reg_submit:
                    normalized_email = normalize_email(reg_email)
                    resolved_patient_id, name, error = resolve_patient_for_registration(base, reg_cpf)
                    if error:
                        st.error(error)
                    elif not is_valid_email(normalized_email):
                        st.error("Informe um e-mail válido.")
                    elif reg_birth_date is None:
                        st.error("Informe a data de nascimento.")
                    elif len(reg_password) < 8:
                        st.error("A senha deve ter pelo menos 8 caracteres.")
                    else:
                        challenge, code = _new_registration_challenge(
                            reg_cpf,
                            normalized_email,
                            store._hash_password(reg_password),
                            resolved_patient_id or "",
                            name or resolved_patient_id or "Usuário",
                            reg_birth_date.isoformat(),
                        )
                        try:
                            send_verification_code(normalized_email, code)
                        except (OSError, smtplib.SMTPException, RuntimeError) as exc:
                            st.error(f"Não foi possível enviar o código. {exc}")
                        else:
                            st.session_state["registration_challenge"] = challenge
                            st.rerun()
            else:
                masked_email = str(pending["email"])
                st.info(f"Enviamos um código de 6 dígitos para {masked_email}.")
                with st.form("verification_form", clear_on_submit=False):
                    verification_code = st.text_input(
                        "Código de verificação",
                        max_chars=6,
                        placeholder="000000",
                        autocomplete="one-time-code",
                    )
                    verify_submit = st.form_submit_button("Verificar e criar conta", use_container_width=True, type="primary")

                if verify_submit:
                    expires_at = datetime.fromisoformat(str(pending["expires_at"]))
                    supplied_digest = _otp_digest(verification_code.strip(), str(pending["code_salt"]))
                    code_is_valid = (
                        len(verification_code.strip()) == 6
                        and verification_code.strip().isdigit()
                        and datetime.now(timezone.utc) <= expires_at
                        and hmac.compare_digest(supplied_digest, str(pending["code_digest"]))
                    )
                    if not code_is_valid:
                        pending["attempts"] = int(pending.get("attempts", 0)) + 1
                        if int(pending["attempts"]) >= OTP_MAX_ATTEMPTS:
                            st.session_state.pop("registration_challenge", None)
                            st.error("Código inválido. Limite de tentativas atingido; solicite um novo código.")
                        elif datetime.now(timezone.utc) > expires_at:
                            st.error("Código inválido ou expirado. Solicite um novo código.")
                        else:
                            st.error("Código inválido.")
                    else:
                        try:
                            store.create_user_with_password_hash(
                                str(pending["cpf"]),
                                str(pending["password_hash"]),
                                str(pending["name"]),
                                ROLE_USER,
                                str(pending["patient_id"]),
                                str(pending["email"]),
                                str(pending["birth_date"]),
                            )
                        except ValueError as exc:
                            st.error(str(exc))
                        else:
                            st.session_state.pop("registration_challenge", None)
                            st.success("E-mail confirmado e conta criada. Agora você já pode entrar na aba ‘Entrar’.")

                if st.button("Alterar dados ou solicitar outro código", use_container_width=True):
                    st.session_state.pop("registration_challenge", None)
                    st.rerun()

        @st.dialog("Recuperar senha")
        def recovery_dialog() -> None:
            st.caption(
                "Confirme CPF, e-mail e data de nascimento. Depois enviaremos um código para o e-mail cadastrado."
            )
            reset_pending = st.session_state.get("password_reset_challenge")
            if not isinstance(reset_pending, dict):
                with st.form("password_recovery_form", clear_on_submit=False):
                    reset_cpf = st.text_input(
                        "CPF",
                        placeholder="000.000.000-00",
                        key="reset_cpf",
                        autocomplete="username",
                    )
                    reset_email = st.text_input(
                        "E-mail cadastrado",
                        placeholder="paciente@exemplo.com",
                        key="reset_email",
                        autocomplete="email",
                    )
                    reset_birth_date = st.date_input(
                        "Data de nascimento",
                        value=None,
                        min_value=date(1900, 1, 1),
                        max_value=date.today(),
                        format="DD/MM/YYYY",
                        key="reset_birth_date",
                    )
                    reset_submit = st.form_submit_button(
                        "Confirmar identidade", use_container_width=True, type="primary"
                    )

                if reset_submit:
                    birth_date_text = reset_birth_date.isoformat() if reset_birth_date else ""
                    account = store.find_password_reset_account(
                        reset_cpf, reset_email, birth_date_text
                    )
                    if account is None:
                        st.error(
                            "Os dados informados não conferem com uma conta habilitada para recuperação. "
                            "Contas antigas podem precisar de atualização pela administração."
                        )
                    else:
                        user_id, destination = account
                        reset_user = store.get_active_user(user_id)
                        challenge, code = _new_password_reset_challenge(user_id, destination, reset_user.session_version if reset_user else -1)
                        try:
                            send_verification_code(destination, code)
                        except (OSError, smtplib.SMTPException, RuntimeError) as exc:
                            st.error(f"Não foi possível enviar o código. {exc}")
                        else:
                            st.session_state["password_reset_challenge"] = challenge
                            st.rerun(scope="fragment")
            else:
                st.info(f"Enviamos um código de 6 dígitos para {reset_pending['email']}.")
                with st.form("password_reset_confirmation_form", clear_on_submit=False):
                    reset_code = st.text_input(
                        "Código de verificação",
                        max_chars=6,
                        placeholder="000000",
                        autocomplete="one-time-code",
                    )
                    new_password = st.text_input(
                        "Nova senha", type="password", autocomplete="new-password",
                        help="Use pelo menos 8 caracteres.",
                    )
                    confirm_password = st.text_input(
                        "Confirmar nova senha", type="password", autocomplete="new-password"
                    )
                    change_submit = st.form_submit_button(
                        "Alterar senha", use_container_width=True, type="primary"
                    )

                if change_submit:
                    expires_at = datetime.fromisoformat(str(reset_pending["expires_at"]))
                    supplied_digest = _otp_digest(reset_code.strip(), str(reset_pending["code_salt"]))
                    code_is_valid = (
                        len(reset_code.strip()) == 6
                        and reset_code.strip().isdigit()
                        and datetime.now(timezone.utc) <= expires_at
                        and hmac.compare_digest(supplied_digest, str(reset_pending["code_digest"]))
                    )
                    if not code_is_valid:
                        reset_pending["attempts"] = int(reset_pending.get("attempts", 0)) + 1
                        if int(reset_pending["attempts"]) >= OTP_MAX_ATTEMPTS:
                            st.session_state.pop("password_reset_challenge", None)
                            st.error("Limite de tentativas atingido. Inicie a recuperação novamente.")
                        elif datetime.now(timezone.utc) > expires_at:
                            st.error("Código expirado. Inicie a recuperação novamente.")
                        else:
                            st.error("Código de verificação inválido.")
                    elif len(new_password) < 8:
                        st.error("A nova senha deve ter pelo menos 8 caracteres.")
                    elif new_password != confirm_password:
                        st.error("A confirmação da senha não corresponde à nova senha.")
                    else:
                        try:
                            store.update_password(
                                int(reset_pending["user_id"]), new_password,
                                expected_session_version=int(reset_pending.get("session_version") or -1),
                            )
                        except ValueError as exc:
                            st.error(str(exc))
                        else:
                            st.session_state.pop("password_reset_challenge", None)
                            st.success("Senha alterada com sucesso. Você já pode entrar com a nova senha.")

                if st.button("Cancelar e começar novamente", use_container_width=True):
                    st.session_state.pop("password_reset_challenge", None)
                    st.query_params.pop("recover", None)
                    st.rerun()

        if st.query_params.get("recover") == "1":
            recovery_dialog()

        if not store.has_manager():
            st.warning(
                "Ainda não existe conta de gestor. Crie a primeira conta pelo script `criar_gestor.py` "
                "ou configure PETSUS_GESTOR_CPF e PETSUS_GESTOR_SENHA no ambiente."
            )

    st.markdown(
        """
        <footer class="auth-support">
            <div class="auth-support-title">Precisa de ajuda? Fale com o suporte</div>
            <a href="https://wa.me/5584998344139" target="_blank" rel="noopener noreferrer"
               aria-label="Abrir conversa com o suporte no WhatsApp">WhatsApp: (84) 99834-4139</a>
            <span class="auth-support-separator">•</span>
            <a href="mailto:reinaldo20jr@gmail.com">reinaldo20jr@gmail.com</a>
        </footer>
        """,
        unsafe_allow_html=True,
    )

    st.stop()


def _render_required_password_change(store: AuthStore, user: AuthUser) -> None:
    st.title("Defina sua própria senha")
    st.info("A senha inicial foi definida pela administração. Troque-a para acessar o painel.")
    with st.form("required_password_change"):
        password = st.text_input("Nova senha", type="password", autocomplete="new-password", help="Use ao menos 8 caracteres e escolha uma senha diferente da inicial.")
        confirmation = st.text_input("Confirmar nova senha", type="password", autocomplete="new-password")
        submitted = st.form_submit_button("Salvar minha senha", type="primary")
    if submitted:
        if password != confirmation:
            st.error("A confirmação não corresponde à nova senha.")
        else:
            try:
                store.update_password(user.id, password, expected_session_version=user.session_version)
            except ValueError as exc:
                st.error(str(exc))
            else:
                refreshed = store.get_active_user(user.id)
                if refreshed:
                    st.session_state["auth_user"] = refreshed.__dict__
                st.rerun()
    if st.button("Sair", key="required_password_logout"):
        logout(store)


def _render_login(store: AuthStore) -> None:
    pending = st.session_state.get("login_challenge")
    if isinstance(pending, dict):
        st.info("Enviamos um código de 6 dígitos para o e-mail cadastrado. Ele expira em 10 minutos.")
        with st.form("login_second_factor"):
            code = st.text_input("Código de acesso", max_chars=6, autocomplete="one-time-code", placeholder="000000")
            submitted = st.form_submit_button("Confirmar acesso", use_container_width=True, type="primary")
        if submitted:
            try:
                with st.spinner("Validando código de acesso…"):
                    user = store.verify_login_challenge(str(pending["token"]), code)
            except ValueError as exc:
                st.error(str(exc))
            else:
                st.session_state.pop("login_challenge", None)
                st.session_state["auth_user"] = user.__dict__
                st.session_state["auth_mfa_verified"] = True
                st.rerun()
        if st.button("Voltar ou solicitar novo código", use_container_width=True):
            store.cancel_login_challenge(str(pending["token"]))
            st.session_state.pop("login_challenge", None)
            st.rerun()
        return

    with st.form("login_form", clear_on_submit=False):
        cpf = st.text_input("CPF", placeholder="000.000.000-00", autocomplete="username")
        password = st.text_input("Senha", type="password", autocomplete="current-password")
        st.markdown('<a class="forgot-password-link" href="?recover=1">Esqueceu sua senha?</a>', unsafe_allow_html=True)
        submitted = st.form_submit_button("Entrar", use_container_width=True, type="primary")
    if not submitted:
        return
    with st.spinner("Validando CPF e senha…"):
        user = store.authenticate(cpf, password)
    if user is None:
        st.error("CPF ou senha inválidos, ou limite de tentativas atingido. Após tentativas repetidas, aguarde 15 minutos.")
        return
    if not mfa_required():
        store.record_auth_event(user.id, "login")
        st.session_state["auth_user"] = user.__dict__
        st.session_state["auth_mfa_verified"] = False
        st.rerun()
        return
    if not smtp_configured():
        st.error("O segundo fator é obrigatório, mas o envio de e-mail ainda não foi configurado. Procure a administração.")
        return
    token = None
    try:
        with st.spinner("Enviando o código de acesso para seu e-mail. Aguarde…"):
            token, code = store.start_login_challenge(user)
            send_verification_code(store.login_email(user.id) or "", code)
    except (OSError, smtplib.SMTPException, RuntimeError, ValueError) as exc:
        if token:
            store.cancel_login_challenge(token)
        store.record_auth_event(user.id, "mfa_delivery_failed")
        st.error(f"Não foi possível concluir o segundo fator. {exc}")
    else:
        st.session_state["login_challenge"] = {"token": token}
        st.rerun()


def logout(store: AuthStore | None = None) -> None:
    current = st.session_state.get("auth_user")
    if store is None and st.session_state.get("_auth_store_path"):
        store = AuthStore(Path(st.session_state["_auth_store_path"]))
    if store is not None and isinstance(current, dict) and current.get("id"):
        store.record_auth_event(int(current["id"]), "logout")
    pending = st.session_state.get("login_challenge")
    if store is not None and isinstance(pending, dict) and pending.get("token"):
        store.cancel_login_challenge(str(pending["token"]))
    st.session_state.pop("auth_user", None)
    st.session_state.pop("auth_mfa_verified", None)
    st.session_state.pop("login_challenge", None)
    st.session_state.pop("internal_management_account", None)
    st.session_state.pop("registration_challenge", None)
    st.session_state.pop("password_reset_challenge", None)
    st.rerun()
