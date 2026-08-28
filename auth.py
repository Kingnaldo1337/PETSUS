from __future__ import annotations

import base64
import hashlib
import hmac
import os
import re
import secrets
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import streamlit as st

ROLE_USER = "usuario"
ROLE_MANAGER = "gestor"


@dataclass(frozen=True)
class AuthUser:
    id: int
    name: str
    role: str
    patient_id: str | None
    cpf_display: str

    @property
    def is_manager(self) -> bool:
        return self.role == ROLE_MANAGER


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
        salt = secrets.token_bytes(16)
        n, r, p = 2**14, 8, 1
        derived = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=n, r=r, p=p, dklen=32)
        return "scrypt${}${}${}${}${}".format(
            n,
            r,
            p,
            base64.urlsafe_b64encode(salt).decode("ascii"),
            base64.urlsafe_b64encode(derived).decode("ascii"),
        )

    @staticmethod
    def _verify_password(password: str, encoded: str) -> bool:
        try:
            algorithm, n, r, p, salt_b64, hash_b64 = encoded.split("$", 5)
            if algorithm != "scrypt":
                return False
            salt = base64.urlsafe_b64decode(salt_b64.encode("ascii"))
            expected = base64.urlsafe_b64decode(hash_b64.encode("ascii"))
            actual = hashlib.scrypt(
                password.encode("utf-8"), salt=salt, n=int(n), r=int(r), p=int(p), dklen=len(expected)
            )
            return hmac.compare_digest(actual, expected)
        except (ValueError, TypeError):
            return False

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

    def create_user(self, cpf: str, password: str, name: str, role: str, patient_id: str | None = None) -> AuthUser:
        normalized = self.normalize_cpf(cpf)
        if len(normalized) != 11:
            raise ValueError("Informe um CPF com 11 dígitos.")
        if len(password) < 8:
            raise ValueError("A senha deve ter pelo menos 8 caracteres.")
        if role not in {ROLE_USER, ROLE_MANAGER}:
            raise ValueError("Perfil de acesso inválido.")
        if role == ROLE_USER and not patient_id:
            raise ValueError("Usuários comuns precisam estar vinculados a um paciente.")
        if role == ROLE_MANAGER:
            patient_id = None

        try:
            with self._connect() as conn:
                cursor = conn.execute(
                    """
                    INSERT INTO users (cpf_lookup, cpf_display, password_hash, role, patient_id, name, active, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, 1, ?)
                    """,
                    (
                        self._lookup_key(normalized),
                        self.mask_cpf(normalized),
                        self._hash_password(password),
                        role,
                        patient_id,
                        name.strip() or "Usuário",
                        datetime.now(timezone.utc).isoformat(),
                    ),
                )
                user_id = int(cursor.lastrowid)
                row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        except sqlite3.IntegrityError as exc:
            message = str(exc).lower()
            if "patient_id" in message:
                raise ValueError("Este paciente já possui uma conta cadastrada.") from exc
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
            width: min(100%, 560px);
            max-width: 560px;
            min-width: 0;
            margin-inline: auto;
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
            .st-key-auth_panel { width: 100%; }
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
            with st.form("register_form", clear_on_submit=False):
                reg_cpf = st.text_input(
                    "CPF",
                    placeholder="000.000.000-00",
                    key="reg_cpf",
                    help="O CPF precisa existir na base de pacientes.",
                )
                reg_password = st.text_input("Crie uma senha", type="password", help="Mínimo de 8 caracteres.")
                reg_submit = st.form_submit_button("Criar conta", use_container_width=True, type="primary")
            if reg_submit:
                resolved_patient_id, name, error = resolve_patient_for_registration(base, reg_cpf)
                if error:
                    st.error(error)
                else:
                    try:
                        store.create_user(reg_cpf, reg_password, name or resolved_patient_id or "Usuário", ROLE_USER, resolved_patient_id)
                    except ValueError as exc:
                        st.error(str(exc))
                    else:
                        st.success("Conta criada. Agora você já pode entrar na aba ‘Entrar’.")

        if not store.has_manager():
            st.warning(
                "Ainda não existe conta de gestor. Crie a primeira conta pelo script `criar_gestor.py` "
                "ou configure PETSUS_GESTOR_CPF e PETSUS_GESTOR_SENHA no ambiente."
            )

    st.stop()


def logout() -> None:
    st.session_state.pop("auth_user", None)
    st.rerun()
