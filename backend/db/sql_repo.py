"""SQLite-backed implementation of the metrics repository."""

from __future__ import annotations

import asyncio
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from db.base_repo import MetricsRepository


class SQLMetricsRepository(MetricsRepository):
    """Persist mastery and misconception metrics in a local SQLite database."""

    def __init__(self, database_path: str | Path | None = None) -> None:
        self._database_path = Path(database_path or Path(__file__).with_name("metrics.db"))
        self._initialize_database()

    def _initialize_database(self) -> None:
        connection = sqlite3.connect(self._database_path)
        try:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS mastery (
                    user_id TEXT NOT NULL,
                    concept TEXT NOT NULL,
                    score INTEGER NOT NULL,
                    updated_at TEXT NOT NULL,
                    PRIMARY KEY (user_id, concept)
                );

                CREATE TABLE IF NOT EXISTS misconception_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    misconception_id TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    created_at TEXT NOT NULL
                );
                """
            )
        finally:
            connection.close()

    @staticmethod
    def _timestamp() -> str:
        return datetime.now(timezone.utc).isoformat()

    async def update_user_mastery(
        self,
        user_id: str,
        concept: str,
        score: int,
    ) -> None:
        await asyncio.to_thread(self._update_user_mastery, user_id, concept, score)

    def _update_user_mastery(self, user_id: str, concept: str, score: int) -> None:
        connection = sqlite3.connect(self._database_path)
        try:
            connection.execute(
                """
                INSERT INTO mastery (user_id, concept, score, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(user_id, concept) DO UPDATE SET
                    score = excluded.score,
                    updated_at = excluded.updated_at
                """,
                (user_id, concept, score, self._timestamp()),
            )
            connection.commit()
        finally:
            connection.close()

    async def record_misconception(
        self,
        user_id: str,
        misconception_id: str,
        confidence: float,
    ) -> int:
        return await asyncio.to_thread(
            self._record_misconception,
            user_id,
            misconception_id,
            confidence,
        )

    def _record_misconception(
        self,
        user_id: str,
        misconception_id: str,
        confidence: float,
    ) -> int:
        connection = sqlite3.connect(self._database_path)
        try:
            prior_count = connection.execute(
                """
                SELECT COUNT(*)
                FROM misconception_events
                WHERE user_id = ? AND misconception_id = ?
                """,
                (user_id, misconception_id),
            ).fetchone()[0]
            connection.execute(
                """
                INSERT INTO misconception_events
                    (user_id, misconception_id, confidence, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (user_id, misconception_id, confidence, self._timestamp()),
            )
            connection.commit()
            return prior_count
        finally:
            connection.close()

    async def get_recent_attempts(
        self,
        user_id: str,
        misconception_id: str,
        limit: int = 5,
    ) -> list[dict]:
        return await asyncio.to_thread(
            self._get_recent_attempts,
            user_id,
            misconception_id,
            limit,
        )

    def _get_recent_attempts(
        self,
        user_id: str,
        misconception_id: str,
        limit: int,
    ) -> list[dict]:
        connection = sqlite3.connect(self._database_path)
        connection.row_factory = sqlite3.Row
        try:
            rows = connection.execute(
                """
                SELECT id, confidence, created_at
                FROM misconception_events
                WHERE user_id = ? AND misconception_id = ?
                ORDER BY created_at DESC, id DESC
                LIMIT ?
                """,
                (user_id, misconception_id, limit),
            ).fetchall()
            return [dict(row) for row in rows]
        finally:
            connection.close()