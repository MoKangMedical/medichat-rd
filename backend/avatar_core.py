"""
MediChat-RD Avatar Core

自有分身核心数据层：
- 分身主档案
- 记忆写入
- 对话记录

SecondMe / Local runtime 都只能作为 provider 绑定在这层之上，
不能再作为分身主数据的唯一来源。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import json
import sqlite3
import uuid


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_AVATAR_DB_PATH = PROJECT_ROOT / "data" / "avatar_core.db"


def _utc_now_iso() -> str:
    return datetime.utcnow().isoformat()


def _json_dumps(payload: Optional[Dict[str, Any]]) -> str:
    return json.dumps(payload or {}, ensure_ascii=False)


def _json_loads(raw: Optional[str]) -> Dict[str, Any]:
    if not raw:
        return {}
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


@dataclass
class PatientAvatar:
    """平台自有分身主档案。"""

    avatar_id: str
    patient_id: str
    nickname: str
    disease_type: str
    bio: str = ""
    memory_summary: str = ""
    personality: str = "温暖、共情、乐于助人"
    provider_key: str = "local"
    provider_avatar_id: Optional[str] = None
    runtime_metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class AvatarMemoryRecord:
    memory_id: str
    avatar_id: str
    memory_type: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class AvatarMessageRecord:
    message_id: str
    avatar_id: str
    role: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)


class AvatarCoreStore:
    """SQLite 持久化的分身主数据层。"""

    def __init__(self, db_path: Path = DEFAULT_AVATAR_DB_PATH):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS avatar_profiles (
                    avatar_id TEXT PRIMARY KEY,
                    patient_id TEXT NOT NULL,
                    nickname TEXT NOT NULL,
                    disease_type TEXT NOT NULL,
                    bio TEXT,
                    memory_summary TEXT,
                    personality TEXT,
                    provider_key TEXT NOT NULL,
                    provider_avatar_id TEXT,
                    runtime_metadata TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS avatar_memories (
                    memory_id TEXT PRIMARY KEY,
                    avatar_id TEXT NOT NULL,
                    memory_type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    metadata TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (avatar_id) REFERENCES avatar_profiles(avatar_id)
                );

                CREATE TABLE IF NOT EXISTS avatar_messages (
                    message_id TEXT PRIMARY KEY,
                    avatar_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    metadata TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (avatar_id) REFERENCES avatar_profiles(avatar_id)
                );

                CREATE INDEX IF NOT EXISTS idx_avatar_memories_avatar_id
                ON avatar_memories(avatar_id, created_at DESC);

                CREATE INDEX IF NOT EXISTS idx_avatar_messages_avatar_id
                ON avatar_messages(avatar_id, created_at DESC);
                """
            )

    def upsert_avatar(self, avatar: PatientAvatar) -> PatientAvatar:
        created_at = avatar.created_at.isoformat()
        updated_at = datetime.utcnow().isoformat()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO avatar_profiles (
                    avatar_id,
                    patient_id,
                    nickname,
                    disease_type,
                    bio,
                    memory_summary,
                    personality,
                    provider_key,
                    provider_avatar_id,
                    runtime_metadata,
                    created_at,
                    updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(avatar_id) DO UPDATE SET
                    patient_id=excluded.patient_id,
                    nickname=excluded.nickname,
                    disease_type=excluded.disease_type,
                    bio=excluded.bio,
                    memory_summary=excluded.memory_summary,
                    personality=excluded.personality,
                    provider_key=excluded.provider_key,
                    provider_avatar_id=excluded.provider_avatar_id,
                    runtime_metadata=excluded.runtime_metadata,
                    updated_at=excluded.updated_at
                """,
                (
                    avatar.avatar_id,
                    avatar.patient_id,
                    avatar.nickname,
                    avatar.disease_type,
                    avatar.bio,
                    avatar.memory_summary,
                    avatar.personality,
                    avatar.provider_key,
                    avatar.provider_avatar_id,
                    _json_dumps(avatar.runtime_metadata),
                    created_at,
                    updated_at,
                ),
            )
        return self.get_avatar(avatar.avatar_id) or avatar

    def get_avatar(self, avatar_id: str) -> Optional[PatientAvatar]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM avatar_profiles WHERE avatar_id = ?",
                (avatar_id,),
            ).fetchone()
        return self._row_to_avatar(row) if row else None

    def list_avatars(self) -> List[PatientAvatar]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM avatar_profiles ORDER BY created_at DESC"
            ).fetchall()
        return [self._row_to_avatar(row) for row in rows]

    def append_memory(
        self,
        avatar_id: str,
        memory_type: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AvatarMemoryRecord:
        record = AvatarMemoryRecord(
            memory_id=f"mem_{uuid.uuid4().hex[:10]}",
            avatar_id=avatar_id,
            memory_type=memory_type,
            content=content,
            metadata=metadata or {},
        )
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO avatar_memories (
                    memory_id, avatar_id, memory_type, content, metadata, created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    record.memory_id,
                    record.avatar_id,
                    record.memory_type,
                    record.content,
                    _json_dumps(record.metadata),
                    record.created_at.isoformat(),
                ),
            )
        return record

    def append_message(
        self,
        avatar_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AvatarMessageRecord:
        record = AvatarMessageRecord(
            message_id=f"msg_{uuid.uuid4().hex[:10]}",
            avatar_id=avatar_id,
            role=role,
            content=content,
            metadata=metadata or {},
        )
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO avatar_messages (
                    message_id, avatar_id, role, content, metadata, created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    record.message_id,
                    record.avatar_id,
                    record.role,
                    record.content,
                    _json_dumps(record.metadata),
                    record.created_at.isoformat(),
                ),
            )
        return record

    def list_memories(self, avatar_id: str, limit: int = 20) -> List[AvatarMemoryRecord]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM avatar_memories
                WHERE avatar_id = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (avatar_id, limit),
            ).fetchall()
        return [
            AvatarMemoryRecord(
                memory_id=row["memory_id"],
                avatar_id=row["avatar_id"],
                memory_type=row["memory_type"],
                content=row["content"],
                metadata=_json_loads(row["metadata"]),
                created_at=datetime.fromisoformat(row["created_at"]),
            )
            for row in rows
        ]

    def list_messages(self, avatar_id: str, limit: int = 50) -> List[AvatarMessageRecord]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM avatar_messages
                WHERE avatar_id = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (avatar_id, limit),
            ).fetchall()
        return [
            AvatarMessageRecord(
                message_id=row["message_id"],
                avatar_id=row["avatar_id"],
                role=row["role"],
                content=row["content"],
                metadata=_json_loads(row["metadata"]),
                created_at=datetime.fromisoformat(row["created_at"]),
            )
            for row in rows
        ]

    def _row_to_avatar(self, row: sqlite3.Row) -> PatientAvatar:
        return PatientAvatar(
            avatar_id=row["avatar_id"],
            patient_id=row["patient_id"],
            nickname=row["nickname"],
            disease_type=row["disease_type"],
            bio=row["bio"] or "",
            memory_summary=row["memory_summary"] or "",
            personality=row["personality"] or "温暖、共情、乐于助人",
            provider_key=row["provider_key"] or "local",
            provider_avatar_id=row["provider_avatar_id"],
            runtime_metadata=_json_loads(row["runtime_metadata"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )
