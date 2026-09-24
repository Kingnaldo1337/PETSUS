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
    cpf: str, email: str, password_hash: str, patient_id: str, name: str,
    birth_date: str | None = None,
) -> tuple[dict[str, object], str]:
    return new_registration_challenge(cpf, email, password_hash, patient_id, name, birth_date)


def _new_password_reset_challenge(user_id: int, email: str) -> tuple[dict[str, object], str]:
    code = f"{secrets.randbelow(1_000_000):06d}"
    salt = secrets.token_hex(16)
    challenge: dict[str, object] = {
        "user_id": int(user_id),
        "email": normalize_email(email),
        "code_salt": salt,
        "code_digest": _otp_digest(code, salt),
        "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=OTP_TTL_MINUTES)).isoformat(),
        "attempts": 0,
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
        birth_date: str | None = None,
    ) -> AuthUser:
        normalized = self.normalize_cpf(cpf)
        if len(normalized) != 11:
            raise ValueError("Informe um CPF com 11 dígitos.")
        if len(password) < 8:
            raise ValueError("A senha deve ter pelo menos 8 caracteres.")
        return self.create_user_with_password_hash(
            normalized, self._hash_password(password), name, role, patient_id, email, birth_date
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
    ) -> AuthUser:
        normalized = self.normalize_cpf(cpf)
        normalized_email = normalize_email(email or "") or None
        normalized_birth_date = (birth_date or "").strip()
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
                    INSERT INTO users (cpf_lookup, cpf_display, password_hash, role, patient_id, name, email, birth_date_lookup, active, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
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

    def update_password(self, user_id: int, new_password: str) -> None:
        if len(new_password) < 8:
            raise ValueError("A senha deve ter pelo menos 8 caracteres.")
        with self._connect() as conn:
            cursor = conn.execute(
                "UPDATE users SET password_hash = ? WHERE id = ? AND active = 1",
                (self._hash_password(new_password), int(user_id)),
            )
            updated_rows = cursor.rowcount
            cursor.close()
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
                       birth_date_lookup IS NOT NULL AS has_birth_date, active
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
        if birth_date is not None:
            try:
                date.fromisoformat(birth_date)
            except ValueError as exc:
                raise ValueError("Informe uma data de nascimento válida.") from exc
            updates.append("birth_date_lookup = ?")
            values.append(self._birth_date_key(birth_date))

        if not updates:
            raise ValueError("Nenhuma alteração foi informada.")
        values.extend((int(user_id), expected_role))
        try:
            with self._connect() as conn:
                cursor = conn.execute(
                    f"UPDATE users SET {', '.join(updates)} WHERE id = ? AND role = ? AND active = 1",
                    values,
                )
                updated_rows = cursor.rowcount
                cursor.close()
        except sqlite3.IntegrityError as exc:
            if "email" in str(exc).lower():
                raise ValueError("Este e-mail já possui uma conta cadastrada.") from exc
            raise ValueError("Não foi possível atualizar a conta.") from exc
        if updated_rows != 1:
            raise ValueError("Conta ativa não encontrada para o perfil informado.")

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
        if cpf and password:
            try:
                self.create_user(cpf, password, name, ROLE_MANAGER, birth_date=birth_date)
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
        .forgot-password-link { display:inline-block; color:#125CC9 !important; font-size:.92rem; font-weight:650; text-decoration:none; margin:.05rem 0 .45rem; }
        .forgot-password-link:hover, .forgot-password-link:focus { color:#0B4B93 !important; text-decoration:underline; }
        .auth-support { width:min(100%, 620px); margin:1.15rem auto .25rem; padding:.85rem 1rem; border-top:1px solid #DDE6F2; color:#667085; font-size:.88rem; line-height:1.55; text-align:center; }
        .auth-support-title { color:#0B2459; font-weight:800; margin-bottom:.15rem; }
        .auth-support a { color:#125CC9 !important; font-weight:700; text-decoration:none; white-space:nowrap; }
        .auth-support a:hover, .auth-support a:focus { color:#0B4B93 !important; text-decoration:underline; }
        .auth-support-separator { color:#98A2B3; padding:0 .4rem; }
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
                st.markdown(
                    '<a class="forgot-password-link" href="?recover=1">Esqueceu sua senha?</a>',
                    unsafe_allow_html=True,
                )
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
                        challenge, code = _new_password_reset_challenge(user_id, destination)
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
                            store.update_password(int(reset_pending["user_id"]), new_password)
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


def logout() -> None:
    st.session_state.pop("auth_user", None)
    st.rerun()
