from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException


class MiniProgramStore:
    def __init__(self, db_path: str | None = None) -> None:
        base = Path(__file__).resolve().parent.parent / "data"
        base.mkdir(parents=True, exist_ok=True)
        self.db_path = Path(db_path) if db_path else base / "mini_program.db"
        self._ensure_schema()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _ensure_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                create table if not exists mp_sessions (
                    access_token text primary key,
                    user_id text not null,
                    patient_id text not null,
                    display_name text not null,
                    wechat_code text not null,
                    created_at text not null
                );

                create table if not exists mp_deeprare_tasks (
                    patient_id text not null,
                    task_id text primary key,
                    payload text not null,
                    created_at text not null
                );

                create table if not exists mp_avatar_bindings (
                    patient_id text primary key,
                    runtime text not null,
                    created_at text not null
                );

                create table if not exists mp_checkins (
                    checkin_id text primary key,
                    patient_id text not null,
                    symptom_score integer not null,
                    mood_score integer not null,
                    note text not null,
                    next_followup_at text not null,
                    created_at text not null
                );
                """
            )

    def create_or_refresh_session(self, wechat_code: str) -> dict:
        access_token = f"mp_{uuid4().hex}"
        user_id = f"user_{wechat_code[-8:]}"
        patient_id = f"patient_{wechat_code[-8:]}"
        display_name = "微信患者"
        created_at = datetime.now(UTC).isoformat()
        with self._connect() as conn:
            conn.execute(
                """
                insert into mp_sessions(access_token, user_id, patient_id, display_name, wechat_code, created_at)
                values (?, ?, ?, ?, ?, ?)
                """,
                (access_token, user_id, patient_id, display_name, wechat_code, created_at),
            )
        return {
            "access_token": access_token,
            "user_id": user_id,
            "patient_id": patient_id,
            "display_name": display_name,
        }

    def require_session(self, access_token: str) -> dict:
        with self._connect() as conn:
            row = conn.execute(
                "select access_token, user_id, patient_id, display_name from mp_sessions where access_token = ?",
                (access_token,),
            ).fetchone()
        if not row:
            raise HTTPException(status_code=401, detail="invalid session")
        return dict(row)

    def save_deeprare_task(self, patient_id: str, task_id: str, payload: dict) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                insert into mp_deeprare_tasks(patient_id, task_id, payload, created_at)
                values (?, ?, ?, ?)
                """,
                (patient_id, task_id, str(payload), datetime.now(UTC).isoformat()),
            )

    def get_deeprare_task(self, patient_id: str, task_id: str) -> dict | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                select payload, created_at from mp_deeprare_tasks
                where patient_id = ? and task_id = ?
                """,
                (patient_id, task_id),
            ).fetchone()
        return dict(row) if row else None

    def bind_avatar(self, patient_id: str, runtime: str) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                insert into mp_avatar_bindings(patient_id, runtime, created_at)
                values (?, ?, ?)
                on conflict(patient_id) do update set runtime = excluded.runtime
                """,
                (patient_id, runtime, datetime.now(UTC).isoformat()),
            )

    def get_avatar_binding(self, patient_id: str) -> dict | None:
        with self._connect() as conn:
            row = conn.execute(
                "select patient_id, runtime, created_at from mp_avatar_bindings where patient_id = ?",
                (patient_id,),
            ).fetchone()
        return dict(row) if row else None

    def save_checkin(self, patient_id: str, payload: dict) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                insert into mp_checkins(checkin_id, patient_id, symptom_score, mood_score, note, next_followup_at, created_at)
                values (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload["checkin_id"],
                    patient_id,
                    payload["symptom_score"],
                    payload["mood_score"],
                    payload["note"],
                    payload["next_followup_at"],
                    datetime.now(UTC).isoformat(),
                ),
            )
