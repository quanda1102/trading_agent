"""
Conversation repository backed by SQLite for persistent chat history.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class ConversationRepository:
    """Simple SQLite-backed repository for storing conversation turns."""

    def __init__(self, db_path: Optional[Path] = None) -> None:
        base_path = Path(__file__).resolve().parents[2]
        default_data_dir = base_path / "data"
        default_data_dir.mkdir(parents=True, exist_ok=True)

        self.db_path = db_path or (default_data_dir / "conversations.db")
        self._initialise()

    # -- Public API -----------------------------------------------------
    def add_interaction(
        self,
        *,
        user_id: str,
        session_id: str,
        question: str,
        answer: str,
        trace: Optional[List[Dict[str, Any]]] = None,
        plan_history: Optional[List[Dict[str, Any]]] = None,
        execution_log: Optional[List[Dict[str, Any]]] = None,
        status: str,
        cycles_used: int,
    ) -> Dict[str, Any]:
        """Persist a completed interaction and return the stored record."""
        created_at = self._utcnow()
        payload = {
            "user_id": user_id,
            "session_id": session_id,
            "question": question,
            "answer": answer,
            "trace": json.dumps(trace or []),
            "plan_history": json.dumps(plan_history or []),
            "execution_log": json.dumps(execution_log or []),
            "status": status,
            "cycles_used": cycles_used,
            "created_at": created_at,
        }

        insert_sql = """
            INSERT INTO conversations (
                user_id,
                session_id,
                question,
                answer,
                trace,
                plan_history,
                execution_log,
                status,
                cycles_used,
                created_at
            )
            VALUES (:user_id, :session_id, :question, :answer, :trace, :plan_history,
                    :execution_log, :status, :cycles_used, :created_at)
        """

        with self._get_connection() as conn:
            cursor = conn.execute(insert_sql, payload)
            interaction_id = cursor.lastrowid

        return self.get_interaction(interaction_id)

    def get_interaction(self, interaction_id: int) -> Dict[str, Any]:
        """Retrieve a single interaction by database identifier."""
        select_sql = """
            SELECT
                id,
                user_id,
                session_id,
                question,
                answer,
                trace,
                plan_history,
                execution_log,
                status,
                cycles_used,
                created_at
            FROM conversations
            WHERE id = ?
        """

        with self._get_connection() as conn:
            row = conn.execute(select_sql, (interaction_id,)).fetchone()

        if row is None:
            raise ValueError(f"Interaction {interaction_id} not found")

        return self._row_to_dict(row)

    def get_history(
        self,
        *,
        user_id: str,
        session_id: str,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Return a paginated set of interactions for a session."""
        if page < 1:
            raise ValueError("page must be >= 1")
        if page_size < 1 or page_size > 100:
            raise ValueError("page_size must be between 1 and 100")

        offset = (page - 1) * page_size

        list_sql = """
            SELECT
                id,
                user_id,
                session_id,
                question,
                answer,
                trace,
                plan_history,
                execution_log,
                status,
                cycles_used,
                created_at
            FROM conversations
            WHERE user_id = ? AND session_id = ?
            ORDER BY datetime(created_at) DESC
            LIMIT ? OFFSET ?
        """

        count_sql = """
            SELECT COUNT(*) FROM conversations
            WHERE user_id = ? AND session_id = ?
        """

        with self._get_connection() as conn:
            rows = conn.execute(
                list_sql,
                (user_id, session_id, page_size, offset),
            ).fetchall()
            total = conn.execute(count_sql, (user_id, session_id)).fetchone()[0]

        return [self._row_to_dict(row) for row in rows], int(total)

    def clear_session(self, *, user_id: str, session_id: str) -> None:
        """Delete all history for a given user session."""
        delete_sql = """
            DELETE FROM conversations
            WHERE user_id = ? AND session_id = ?
        """

        with self._get_connection() as conn:
            conn.execute(delete_sql, (user_id, session_id))

    # -- Internal helpers -----------------------------------------------
    def _initialise(self) -> None:
        """Ensure the SQLite database and schema exist."""
        with self._get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    question TEXT NOT NULL,
                    answer TEXT,
                    trace TEXT,
                    plan_history TEXT,
                    execution_log TEXT,
                    status TEXT NOT NULL,
                    cycles_used INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_conversations_user_session
                ON conversations (user_id, session_id, created_at DESC)
                """
            )

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    @staticmethod
    def _utcnow() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _row_to_dict(row: sqlite3.Row) -> Dict[str, Any]:
        def _load_json(value: Optional[str]) -> Any:
            if value in (None, ""):
                return []
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return []

        status = row["status"]
        answer = row["answer"] or ""

        return {
            "id": row["id"],
            "interaction_id": row["id"],
            "user_id": row["user_id"],
            "session_id": row["session_id"],
            "question": row["question"],
            "answer": row["answer"],
            "final_answer": answer,
            "response": answer,
            "trace": _load_json(row["trace"]),
            "plan_history": _load_json(row["plan_history"]),
            "execution_log": _load_json(row["execution_log"]),
            "agent_results": {},
            "status": status,
            "success": status == "success",
            "timeout": status == "timeout",
            "error": None,
            "cycles_used": row["cycles_used"],
            "created_at": row["created_at"],
        }
