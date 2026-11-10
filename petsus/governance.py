"""Persistência local de feedback, avaliação SUS e uso agregado do painel.

Os registros de navegação e SUS não armazenam CPF, nome, paciente ou conta.
O autor de um relato fica restrito à própria conta e aos gestores.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from petsus.auth.models import AuthUser, ROLE_MANAGER, ROLE_USER

FEEDBACK_CATEGORIES = ("Erro nos dados", "Problema de acesso", "Sugestão", "Acessibilidade", "Outro")
FEEDBACK_STATUSES = ("Recebido", "Em análise", "Resolvido", "Planejado")


class GovernanceStore:
    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS feedback (
                    id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL, role TEXT NOT NULL,
                    category TEXT NOT NULL, description TEXT NOT NULL, process_id TEXT,
                    status TEXT NOT NULL DEFAULT 'Recebido', response TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL, updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS page_views (
                    id INTEGER PRIMARY KEY, role TEXT NOT NULL, page TEXT NOT NULL,
                    visited_on TEXT NOT NULL, visit_key TEXT UNIQUE
                );
                CREATE TABLE IF NOT EXISTS sus_responses (
                    id INTEGER PRIMARY KEY, role TEXT NOT NULL, answers TEXT NOT NULL,
                    score REAL NOT NULL, created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS data_reviews (
                    id INTEGER PRIMARY KEY, fingerprint TEXT NOT NULL, reviewer_id INTEGER NOT NULL,
                    note TEXT NOT NULL, reviewed_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS governance_audit (
                    id INTEGER PRIMARY KEY, actor_id INTEGER NOT NULL, event TEXT NOT NULL,
                    reference TEXT NOT NULL, created_at TEXT NOT NULL
                );
            """)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=15)
        conn.row_factory = sqlite3.Row
        return conn

    @staticmethod
    def _require_manager(user: AuthUser) -> None:
        if not user.is_manager:
            raise ValueError("Esta consulta é restrita aos gestores.")

    def submit_feedback(
        self, user: AuthUser, category: str, description: str, process_id: str | None = None
    ) -> int:
        if category not in FEEDBACK_CATEGORIES:
            raise ValueError("Selecione uma categoria válida.")
        description = description.strip()
        if not 10 <= len(description) <= 4000:
            raise ValueError("Descreva o relato usando entre 10 e 4.000 caracteres.")
        process_id = (process_id or "").strip() or None
        if process_id and len(process_id) > 100:
            raise ValueError("O identificador do processo deve ter até 100 caracteres.")
        timestamp = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            cursor = conn.execute(
                "INSERT INTO feedback(user_id, role, category, description, process_id, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (user.id, user.role, category, description, process_id, timestamp, timestamp),
            )
            return int(cursor.lastrowid)

    def list_feedback(self, user: AuthUser, limit: int = 100) -> list[dict[str, object]]:
        # Sempre filtrar no armazenamento: um paciente nunca recebe relatos alheios.
        restriction = "" if user.is_manager else "WHERE user_id = ?"
        values: list[object] = [] if user.is_manager else [user.id]
        values.append(max(1, min(int(limit), 500)))
        with self._connect() as conn:
            rows = conn.execute(
                f"SELECT id, role, category, description, process_id, status, response, created_at, updated_at "
                f"FROM feedback {restriction} ORDER BY id DESC LIMIT ?", values,
            ).fetchall()
        return [dict(row) for row in rows]

    def update_feedback(self, user: AuthUser, feedback_id: int, status: str, response: str) -> None:
        self._require_manager(user)
        if status not in FEEDBACK_STATUSES:
            raise ValueError("Selecione um status válido.")
        response = response.strip()
        if len(response) > 4000:
            raise ValueError("A resposta deve ter até 4.000 caracteres.")
        with self._connect() as conn:
            cursor = conn.execute(
                "UPDATE feedback SET status = ?, response = ?, updated_at = ? WHERE id = ?",
                (status, response, datetime.now(timezone.utc).isoformat(), int(feedback_id)),
            )
            if cursor.rowcount != 1:
                raise ValueError("Relato não encontrado.")

    def record_page_view(self, role: str, page: str, visit_token: str | None = None) -> None:
        if role not in {ROLE_MANAGER, ROLE_USER}:
            raise ValueError("Perfil inválido.")
        if not page.strip() or len(page) > 100:
            raise ValueError("Página inválida.")
        day = datetime.now(ZoneInfo("America/Fortaleza")).date().isoformat()
        # O token deve ser aleatório e local à sessão, nunca CPF ou paciente_id.
        key = hashlib.sha256(f"{visit_token}:{day}:{role}:{page}".encode()).hexdigest() if visit_token else None
        with self._connect() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO page_views(role, page, visited_on, visit_key) VALUES (?, ?, ?, ?)",
                (role, page, day, key),
            )

    def usage_summary(self, user: AuthUser) -> list[dict[str, object]]:
        self._require_manager(user)
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT visited_on AS date, role, page, COUNT(*) AS views FROM page_views "
                "GROUP BY visited_on, role, page ORDER BY visited_on DESC, views DESC LIMIT 500"
            ).fetchall()
        return [dict(row) for row in rows]

    def submit_sus(self, user: AuthUser, answers: list[int]) -> float:
        if len(answers) != 10 or any(type(value) is not int or not 1 <= value <= 5 for value in answers):
            raise ValueError("Responda às 10 questões da escala SUS, usando valores de 1 a 5.")
        adjusted = sum(value - 1 if index % 2 == 0 else 5 - value for index, value in enumerate(answers))
        score = adjusted * 2.5
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO sus_responses(role, answers, score, created_at) VALUES (?, ?, ?, ?)",
                (user.role, json.dumps(answers), score, datetime.now(timezone.utc).isoformat()),
            )
        return score

    def sus_summary(self, user: AuthUser) -> dict[str, object]:
        self._require_manager(user)
        with self._connect() as conn:
            row = conn.execute("SELECT COUNT(*) AS count, AVG(score) AS average_score FROM sus_responses").fetchone()
        return dict(row)

    def record_data_review(self, user: AuthUser, fingerprint: str, note: str) -> None:
        self._require_manager(user)
        if len(fingerprint) != 64 or any(char not in "0123456789abcdef" for char in fingerprint):
            raise ValueError("Identificador de lote inválido.")
        note = note.strip()
        if not 10 <= len(note) <= 2000:
            raise ValueError("Descreva a conferência usando entre 10 e 2.000 caracteres.")
        timestamp = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO data_reviews(fingerprint, reviewer_id, note, reviewed_at) VALUES (?, ?, ?, ?)",
                (fingerprint, user.id, note, timestamp),
            )
            conn.execute(
                "INSERT INTO governance_audit(actor_id, event, reference, created_at) VALUES (?, ?, ?, ?)",
                (user.id, "data_review", fingerprint, timestamp),
            )

    def latest_data_review(self, user: AuthUser, fingerprint: str) -> dict[str, object] | None:
        self._require_manager(user)
        with self._connect() as conn:
            row = conn.execute(
                "SELECT reviewer_id, note, reviewed_at FROM data_reviews WHERE fingerprint = ? ORDER BY id DESC LIMIT 1",
                (fingerprint,),
            ).fetchone()
        return dict(row) if row is not None else None
