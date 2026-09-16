from __future__ import annotations

import hashlib
import hmac
import os
import re
import secrets
import smtplib
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import streamlit as st

from petsus.auth.email import send_verification_code as _send_verification_email
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

send_verification_code = _send_verification_email


def _otp_digest(code: str, salt: str) -> str:
    return otp_digest(code, salt)


def _new_registration_challenge(
    cpf: str, email: str, password_hash: str, patient_id: str, name: str
) -> tuple[dict[str, object], str]:
    return new_registration_challenge(cpf, email, password_hash, patient_id, name)


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
            conn.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email_unique "
                "ON users(email) WHERE email IS NOT NULL"
            )

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
        )

    def authenticate(self, cpf: str, password: str) -> AuthUser | None:
        normalized = self.normalize_cpf(cpf)
        if len(normalized) != 11 or not password:
            return None
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM users WHERE cpf_lookup = ? AND active = 1",
                (self._lookup_key(normalized),),
            ).fetchone()
        if row is None or not self._verify_password(password, row["password_hash"]):
            return None
        return self._row_to_user(row)

    def create_user(
        self,
        cpf: str,
        password: str,
        name: str,
        role: str,
        patient_id: str | None = None,
        email: str | None = None,
    ) -> AuthUser:
        normalized = self.normalize_cpf(cpf)
        if len(normalized) != 11:
            raise ValueError("Informe um CPF com 11 dígitos.")
        if len(password) < 8:
            raise ValueError("A senha deve ter pelo menos 8 caracteres.")
        return self.create_user_with_password_hash(
            normalized, self._hash_password(password), name, role, patient_id, email
        )

    def create_user_with_password_hash(
        self,
        cpf: str,
        password_hash: str,
        name: str,
        role: str,
        patient_id: str | None = None,
        email: str | None = None,
    ) -> AuthUser:
        normalized = self.normalize_cpf(cpf)
        normalized_email = normalize_email(email or "") or None
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
                cursor = conn.execute(
                    """
                    INSERT INTO users (cpf_lookup, cpf_display, password_hash, role, patient_id, name, email, active, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?)
                    """,
                    (
                        self._lookup_key(normalized),
                        self.mask_cpf(normalized),
                        password_hash,
                        role,
                        patient_id,
                        name.strip() or "Usuário",
                        normalized_email,
                        datetime.now(timezone.utc).isoformat(),
                    ),
                )
                user_id = int(cursor.lastrowid)
                row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        except sqlite3.IntegrityError as exc:
            message = str(exc).lower()
            if "patient_id" in message:
                raise ValueError("Este paciente já possui uma conta cadastrada.") from exc
            if "email" in message:
                raise ValueError("Este e-mail já possui uma conta cadastrada.") from exc
            raise ValueError("Este CPF já possui uma conta cadastrada.") from exc
        return self._row_to_user(row)

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
        if cpf and password:
            try:
                self.create_user(cpf, password, name, ROLE_MANAGER)
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
    current = st.session_state.get("auth_user")
    if isinstance(current, dict) and current.get("id"):
        return AuthUser(**current)

    store.bootstrap_manager_from_env()

    st.markdown(
        """
        <style>
        .auth-wrap { width: min(100%, 560px); max-width: 560px; min-width: 0; margin: 2.5rem auto .5rem; padding-inline: .5rem; box-sizing: border-box; text-align: center; }
        .auth-icon { font-size: 3.2rem; }
        .auth-title { font-size: 2rem; font-weight: 900; color: #0B2459; margin-top: .35rem; }
        .auth-sub { color: #667085; margin: .35rem 0 1.1rem; }
        .st-key-auth_panel {
            width: 100%;
            min-width: 0;
            margin-inline: auto;
        }
        .st-key-auth_panel [data-testid="stTabs"],
        div[data-testid="stTabs"] {
            width: min(100%, 620px) !important;
            max-width: 620px !important;
            min-width: 0;
            margin-inline: auto !important;
        }
        .st-key-auth_panel [data-testid="stForm"],
        div[data-testid="stTabs"] [data-testid="stForm"],
        div[data-testid="stForm"] {
            width: min(100%, 620px) !important;
            max-width: 620px !important;
            margin-inline: auto !important;
        }
        .st-key-auth_panel, .st-key-auth_panel * {
            box-sizing: border-box;
        }
        .st-key-auth_panel p, .st-key-auth_panel label,
        .st-key-auth_panel [data-testid="stMarkdownContainer"] {
            min-width: 0;
            word-break: normal;
            overflow-wrap: break-word;
            white-space: normal;
        }
        @media (max-width: 640px) {
            .auth-wrap { margin-top: 1rem; padding-inline: .25rem; }
            .auth-title { font-size: 1.65rem; line-height: 1.15; }
            .st-key-auth_panel,
            .st-key-auth_panel [data-testid="stTabs"],
            div[data-testid="stTabs"] { width: 100% !important; }
        }
        </style>
        <div class="auth-wrap">
            <div class="auth-icon">⚖️➕</div>
            <div class="auth-title">Acesso ao Dashboard</div>
            <div class="auth-sub">Entre com seu CPF e senha. O conteúdo exibido respeita o perfil da conta.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.container(key="auth_panel"):
        login_tab, register_tab = st.tabs(["Entrar", "Criar conta"])
        with login_tab:
            with st.form("login_form", clear_on_submit=False):
                cpf = st.text_input("CPF", placeholder="000.000.000-00", autocomplete="username")
                password = st.text_input("Senha", type="password", autocomplete="current-password")
                submitted = st.form_submit_button("Entrar", use_container_width=True, type="primary")
            if submitted:
                user = store.authenticate(cpf, password)
                if user is None:
                    st.error("CPF ou senha inválidos.")
                else:
                    st.session_state["auth_user"] = user.__dict__
                    st.rerun()

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
                    reg_password = st.text_input("Crie uma senha", type="password", help="Mínimo de 8 caracteres.")
                    reg_submit = st.form_submit_button("Enviar código", use_container_width=True, type="primary")
                if reg_submit:
                    normalized_email = normalize_email(reg_email)
                    resolved_patient_id, name, error = resolve_patient_for_registration(base, reg_cpf)
                    if error:
                        st.error(error)
                    elif not is_valid_email(normalized_email):
                        st.error("Informe um e-mail válido.")
                    elif len(reg_password) < 8:
                        st.error("A senha deve ter pelo menos 8 caracteres.")
                    else:
                        challenge, code = _new_registration_challenge(
                            reg_cpf,
                            normalized_email,
                            store._hash_password(reg_password),
                            resolved_patient_id or "",
                            name or resolved_patient_id or "Usuário",
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
                            )
                        except ValueError as exc:
                            st.error(str(exc))
                        else:
                            st.session_state.pop("registration_challenge", None)
                            st.success("E-mail confirmado e conta criada. Agora você já pode entrar na aba ‘Entrar’.")

                if st.button("Alterar dados ou solicitar outro código", use_container_width=True):
                    st.session_state.pop("registration_challenge", None)
                    st.rerun()

        if not store.has_manager():
            st.warning(
                "Ainda não existe conta de gestor. Crie a primeira conta pelo script `criar_gestor.py` "
                "ou configure PETSUS_GESTOR_CPF e PETSUS_GESTOR_SENHA no ambiente."
            )

    st.stop()


def logout() -> None:
    st.session_state.pop("auth_user", None)
    st.rerun()
