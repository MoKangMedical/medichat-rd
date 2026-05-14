"""
OpenRD bridge API.

This module maps the public OpenRD collaboration pattern into MediChat-RD:
patient/community needs, volunteer contribution, project progress, anonymous
rooms, consent events, and virtual cohort planning.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
import uuid
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field


router = APIRouter(prefix="/api/v1/openrd", tags=["OpenRD 共建协作"])

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "openrd_bridge.db"

PROJECT_PROFILE: Dict[str, Any] = {
    "name": "MediChat-RD-AI 驱动的罕见病患者连接、诊疗协作与药物研发平台",
    "short_name": "MediChat-RD OpenRD Bridge",
    "slogan": "让罕见被看见，让患者、医生、科研和药企在同一张协作桌上行动。",
    "summary": (
        "MediChat-RD 以 AI 为核心，连接罕见病患者、医生、科研机构与制药企业，"
        "围绕患者孤立、诊疗分散和药物研发困难三个痛点，提供可追溯诊断、"
        "患者互助、跨机构协作、虚拟队列和临床试验招募能力。"
    ),
    "source_references": [
        {
            "name": "Khub-OpenRD/OpenRD",
            "url": "https://github.com/Khub-OpenRD/OpenRD",
            "mapped_capability": "志愿者需求池、项目进度、贡献者加入、社区介绍。",
            "integration_policy": "无显式开源许可证；仅做产品模式和数据模型兼容，不复制源码。",
        },
        {
            "name": "Alex-Yanggg/OpenRD-web-server",
            "url": "https://github.com/Alex-Yanggg/OpenRD-web-server",
            "mapped_capability": "用户、聊天组、消息和 API 版本化后端结构。",
            "integration_policy": "无显式开源许可证；用 FastAPI + SQLite 重新实现兼容能力。",
        },
    ],
    "core_modules": [
        {
            "id": "patient-community",
            "title": "智能患者社区与精准匹配",
            "outcome": "把患者叙述、表型、基因线索和病程阶段转成匿名画像，用于病友互助和陪伴。",
            "capabilities": ["7x24 AI 问答", "患者画像", "相似患者匹配", "匿名论坛/聊天室"],
        },
        {
            "id": "mdt-collaboration",
            "title": "跨机构诊疗协作平台",
            "outcome": "把 EMR、影像、HPO、基因和授权事件组织成可审计 MDT 工作流。",
            "capabilities": ["EMR/影像入口", "分布式 MDT", "授权台账", "数据可用不可见"],
        },
        {
            "id": "drug-rd-engine",
            "title": "药物研发加速引擎",
            "outcome": "把文献、临床试验、RWD、虚拟队列和患者招募连接到转化研究路径。",
            "capabilities": ["靶点发现", "药物重定位", "虚拟患者队列", "试验匹配"],
        },
    ],
    "technology": [
        {"name": "多模态 AI 融合", "status": "active", "description": "文本、HPO、基因、临床记录和影像入口统一到患者对象。"},
        {"name": "联邦学习框架", "status": "roadmap", "description": "先建立站点级 consent + cohort contract，后续接入跨机构训练。"},
        {"name": "可解释性 AI", "status": "active", "description": "DeepRare 推理链、ACMG 矩阵和证据缺口可视化。"},
        {"name": "隐私保护授权台账", "status": "active", "description": "以 hash-chain 记录授权事件，支持审计，不暴露原始身份。"},
    ],
}

SEED_REQUIREMENTS: List[Dict[str, Any]] = [
    {
        "id": "req_patient_qa",
        "title": "多语言患者问答与心理支持",
        "description": "为患者和家属提供 7x24 医学信息解释、就诊前问题整理和情绪支持入口。",
        "status": "in-progress",
        "priority": "high",
        "created_by": "RareDBridge 团队",
        "tags": ["AI问答", "心理支持", "多语言"],
        "track": "patient-community",
        "disease_area": "全病种",
        "progress": 72,
    },
    {
        "id": "req_patient_matching",
        "title": "HPO/基因/病程患者画像与相似患者匹配",
        "description": "基于症状自评、HPO、授权基因线索和脱敏病程阶段匹配相似患者。",
        "status": "in-progress",
        "priority": "high",
        "created_by": "OpenRD 共建",
        "tags": ["HPO", "患者画像", "病友匹配"],
        "track": "patient-community",
        "disease_area": "神经肌肉/溶酶体病优先",
        "progress": 64,
    },
    {
        "id": "req_mdt_ledger",
        "title": "跨机构 MDT 病例协作与患者授权台账",
        "description": "将患者授权、专家会诊、数据共享范围和审计证据形成可追溯协作记录。",
        "status": "unclaimed",
        "priority": "high",
        "created_by": "临床协作组",
        "tags": ["MDT", "授权", "合规审计"],
        "track": "mdt-collaboration",
        "disease_area": "未诊断病例",
        "progress": 28,
    },
    {
        "id": "req_multimodal_triage",
        "title": "EMR/影像/基因组多模态诊断工作流",
        "description": "把 EMR 摘要、影像提示、HPO 和基因变异统一进入 DeepRare / ACMG 分析面板。",
        "status": "unclaimed",
        "priority": "medium",
        "created_by": "医生工作台",
        "tags": ["EMR", "医学影像", "基因组"],
        "track": "mdt-collaboration",
        "disease_area": "多系统受累病例",
        "progress": 18,
    },
    {
        "id": "req_virtual_cohort",
        "title": "虚拟患者队列与 RWD 研究包",
        "description": "按疾病、HPO、基因和用药线索形成匿名虚拟队列，用于自然史和早期研发评估。",
        "status": "in-progress",
        "priority": "high",
        "created_by": "转化研究组",
        "tags": ["RWD", "虚拟队列", "自然史"],
        "track": "drug-rd-engine",
        "disease_area": "可治疗罕见病",
        "progress": 52,
    },
    {
        "id": "req_trial_channel",
        "title": "患者-药企临床试验合作通道",
        "description": "将患者意愿、入排标准、试验地点和响应率预测转成可协作招募漏斗。",
        "status": "unclaimed",
        "priority": "medium",
        "created_by": "药物研发组",
        "tags": ["临床试验", "药企合作", "招募"],
        "track": "drug-rd-engine",
        "disease_area": "有在研疗法疾病",
        "progress": 24,
    },
]

SEED_PROJECTS: List[Dict[str, Any]] = [
    {
        "id": "proj_patient_qa",
        "requirement_id": "req_patient_qa",
        "name": "AI 陪诊 + 心理支持工作台",
        "description": "把现有 AI 陪诊、SecondMe 和患者社群内容连接成患者入口。",
        "progress": 72,
        "start_date": "2026-04-24",
        "target_date": "2026-06-30",
        "github_url": "https://github.com/MoKangMedical/medichat-rd",
        "contribution_guide": "优先补充多语言提示词、患者风险边界和心理支持模板。",
    },
    {
        "id": "proj_virtual_cohort",
        "requirement_id": "req_virtual_cohort",
        "name": "RareDBridge 虚拟队列 MVP",
        "description": "用 Phenopacket-lite、HPO 和患者登记库构建匿名队列。",
        "progress": 52,
        "start_date": "2026-04-26",
        "target_date": "2026-07-15",
        "github_url": "https://github.com/MoKangMedical/medichat-rd",
        "contribution_guide": "需要疾病自然史、真实世界数据字段和隐私分级设计。",
    },
]


class RequirementCreate(BaseModel):
    title: str = Field(..., min_length=2, max_length=140)
    description: str = Field(..., min_length=5, max_length=2000)
    priority: str = Field("medium", pattern="^(high|medium|low)$")
    tags: List[str] = Field(default_factory=list, max_length=12)
    created_by: str = Field("OpenRD 共建者", max_length=80)
    track: str = Field("patient-community", max_length=80)
    disease_area: str = Field("全病种", max_length=120)


class JoinRequirementInput(BaseModel):
    name: str = Field(..., min_length=1, max_length=80)
    role: str = Field(..., min_length=1, max_length=80)
    affiliation: str = Field("", max_length=120)
    github: str = Field("", max_length=120)
    contact: str = Field("", max_length=160)
    participant_type: str = Field("volunteer", max_length=40)
    message: str = Field("", max_length=500)


class ProgressInput(BaseModel):
    progress: int = Field(..., ge=0, le=100)
    content: str = Field(..., min_length=2, max_length=1000)
    author: str = Field("OpenRD 共建者", max_length=80)
    status: Optional[str] = Field(None, pattern="^(unclaimed|in-progress|completed)$")


class MessageInput(BaseModel):
    room: str = Field("general", max_length=80)
    author_alias: str = Field("匿名共建者", max_length=80)
    role: str = Field("volunteer", max_length=40)
    content: str = Field(..., min_length=1, max_length=1200)


class ConsentEventInput(BaseModel):
    subject_alias: str = Field(..., min_length=1, max_length=120)
    scope: str = Field(..., min_length=2, max_length=200)
    action: str = Field(..., pattern="^(grant|revoke|review|share)$")
    actor: str = Field("MediChat-RD", max_length=120)
    note: str = Field("", max_length=500)


class CohortInput(BaseModel):
    name: str = Field(..., min_length=2, max_length=140)
    disease_area: str = Field(..., min_length=2, max_length=140)
    criteria: str = Field(..., min_length=2, max_length=1000)
    data_sources: List[str] = Field(default_factory=list, max_length=12)
    target_size: int = Field(20, ge=1, le=100000)
    owner: str = Field("转化研究组", max_length=100)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _json_loads(value: str, default: Any) -> Any:
    try:
        return json.loads(value or "")
    except (json.JSONDecodeError, TypeError):
        return default


def _hash_text(value: str) -> str:
    if not value.strip():
        return ""
    return hashlib.sha256(value.strip().encode("utf-8")).hexdigest()[:20]


def _ensure_db() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(DB_PATH)) as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS requirements (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                status TEXT NOT NULL,
                priority TEXT NOT NULL,
                created_at TEXT NOT NULL,
                created_by TEXT NOT NULL,
                tags_json TEXT NOT NULL,
                track TEXT NOT NULL,
                disease_area TEXT NOT NULL,
                progress INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS contributors (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                role TEXT NOT NULL,
                affiliation TEXT NOT NULL,
                github TEXT NOT NULL,
                contact_hash TEXT NOT NULL,
                participant_type TEXT NOT NULL,
                joined_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS requirement_contributors (
                id TEXT PRIMARY KEY,
                requirement_id TEXT NOT NULL,
                contributor_id TEXT NOT NULL,
                role TEXT NOT NULL,
                message TEXT NOT NULL,
                status TEXT NOT NULL,
                requested_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS progress_updates (
                id TEXT PRIMARY KEY,
                requirement_id TEXT NOT NULL,
                content TEXT NOT NULL,
                author TEXT NOT NULL,
                progress INTEGER NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY,
                requirement_id TEXT NOT NULL,
                name TEXT NOT NULL,
                description TEXT NOT NULL,
                progress INTEGER NOT NULL,
                start_date TEXT NOT NULL,
                target_date TEXT NOT NULL,
                github_url TEXT NOT NULL,
                contribution_guide TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS room_messages (
                id TEXT PRIMARY KEY,
                room TEXT NOT NULL,
                author_alias TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS consent_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id TEXT NOT NULL UNIQUE,
                subject_alias_hash TEXT NOT NULL,
                scope TEXT NOT NULL,
                action TEXT NOT NULL,
                actor TEXT NOT NULL,
                note TEXT NOT NULL,
                previous_hash TEXT NOT NULL,
                event_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS virtual_cohorts (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                disease_area TEXT NOT NULL,
                criteria TEXT NOT NULL,
                data_sources_json TEXT NOT NULL,
                target_size INTEGER NOT NULL,
                owner TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            """
        )
        count = connection.execute("SELECT COUNT(*) FROM requirements").fetchone()[0]
        if count == 0:
            for item in SEED_REQUIREMENTS:
                connection.execute(
                    """
                    INSERT INTO requirements (
                        id, title, description, status, priority, created_at, created_by,
                        tags_json, track, disease_area, progress
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        item["id"],
                        item["title"],
                        item["description"],
                        item["status"],
                        item["priority"],
                        _now(),
                        item["created_by"],
                        json.dumps(item["tags"], ensure_ascii=False),
                        item["track"],
                        item["disease_area"],
                        item["progress"],
                    ),
                )
            for project in SEED_PROJECTS:
                connection.execute(
                    """
                    INSERT INTO projects (
                        id, requirement_id, name, description, progress, start_date,
                        target_date, github_url, contribution_guide
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        project["id"],
                        project["requirement_id"],
                        project["name"],
                        project["description"],
                        project["progress"],
                        project["start_date"],
                        project["target_date"],
                        project["github_url"],
                        project["contribution_guide"],
                    ),
                )
        connection.commit()


def _get_connection() -> sqlite3.Connection:
    _ensure_db()
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def _serialize_requirement(row: sqlite3.Row, connection: sqlite3.Connection) -> Dict[str, Any]:
    req_id = row["id"]
    team_rows = connection.execute(
        """
        SELECT c.id, c.name, c.role, c.affiliation, c.github, c.participant_type, rc.status, rc.requested_at
        FROM requirement_contributors rc
        JOIN contributors c ON c.id = rc.contributor_id
        WHERE rc.requirement_id = ?
        ORDER BY rc.requested_at DESC
        """,
        (req_id,),
    ).fetchall()
    update_rows = connection.execute(
        "SELECT id, content, author, progress, status, created_at FROM progress_updates WHERE requirement_id = ? ORDER BY created_at DESC LIMIT 8",
        (req_id,),
    ).fetchall()
    return {
        "id": req_id,
        "title": row["title"],
        "description": row["description"],
        "status": row["status"],
        "priority": row["priority"],
        "created_at": row["created_at"],
        "created_by": row["created_by"],
        "tags": _json_loads(row["tags_json"], []),
        "track": row["track"],
        "disease_area": row["disease_area"],
        "progress": row["progress"],
        "team": [dict(item) for item in team_rows],
        "updates": [dict(item) for item in update_rows],
    }


def _stats(connection: sqlite3.Connection) -> Dict[str, int]:
    rows = connection.execute(
        "SELECT status, COUNT(*) AS count FROM requirements GROUP BY status"
    ).fetchall()
    by_status = {row["status"]: row["count"] for row in rows}
    contributor_count = connection.execute("SELECT COUNT(*) FROM contributors").fetchone()[0]
    cohort_count = connection.execute("SELECT COUNT(*) FROM virtual_cohorts").fetchone()[0]
    return {
        "unclaimed": by_status.get("unclaimed", 0),
        "in_progress": by_status.get("in-progress", 0),
        "completed": by_status.get("completed", 0),
        "total_requirements": sum(by_status.values()),
        "contributors": contributor_count,
        "virtual_cohorts": cohort_count,
    }


@router.get("/overview")
async def get_openrd_overview() -> Dict[str, Any]:
    with closing(_get_connection()) as connection:
        return {
            **PROJECT_PROFILE,
            "stats": _stats(connection),
            "collaboration_tracks": [
                {"id": "patient-community", "label": "患者连接", "goal": "降低孤立感，形成相似病程互助。"},
                {"id": "mdt-collaboration", "label": "诊疗协作", "goal": "把病例复盘、专家意见和授权边界放到一条链路。"},
                {"id": "drug-rd-engine", "label": "药物研发", "goal": "把患者真实需求转成虚拟队列、试验招募和药物重定位线索。"},
            ],
        }


@router.get("/requirements")
async def list_requirements(
    status: Optional[str] = Query(None, pattern="^(unclaimed|in-progress|completed)$"),
    track: Optional[str] = None,
) -> Dict[str, Any]:
    with closing(_get_connection()) as connection:
        query = "SELECT * FROM requirements"
        params: List[Any] = []
        conditions: List[str] = []
        if status:
            conditions.append("status = ?")
            params.append(status)
        if track:
            conditions.append("track = ?")
            params.append(track)
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY CASE priority WHEN 'high' THEN 1 WHEN 'medium' THEN 2 ELSE 3 END, created_at DESC"
        rows = connection.execute(query, params).fetchall()
        return {
            "items": [_serialize_requirement(row, connection) for row in rows],
            "stats": _stats(connection),
        }


@router.post("/requirements")
async def create_requirement(payload: RequirementCreate) -> Dict[str, Any]:
    req_id = f"req_{uuid.uuid4().hex[:12]}"
    tags = [tag.strip() for tag in payload.tags if tag.strip()][:12]
    with closing(_get_connection()) as connection:
        connection.execute(
            """
            INSERT INTO requirements (
                id, title, description, status, priority, created_at, created_by,
                tags_json, track, disease_area, progress
            ) VALUES (?, ?, ?, 'unclaimed', ?, ?, ?, ?, ?, ?, 0)
            """,
            (
                req_id,
                payload.title.strip(),
                payload.description.strip(),
                payload.priority,
                _now(),
                payload.created_by.strip() or "OpenRD 共建者",
                json.dumps(tags, ensure_ascii=False),
                payload.track.strip() or "patient-community",
                payload.disease_area.strip() or "全病种",
            ),
        )
        row = connection.execute("SELECT * FROM requirements WHERE id = ?", (req_id,)).fetchone()
        connection.commit()
        return {"ok": True, "requirement": _serialize_requirement(row, connection)}


@router.post("/requirements/{requirement_id}/join")
async def join_requirement(requirement_id: str, payload: JoinRequirementInput) -> Dict[str, Any]:
    contributor_id = f"contrib_{uuid.uuid4().hex[:12]}"
    join_id = f"join_{uuid.uuid4().hex[:12]}"
    with closing(_get_connection()) as connection:
        row = connection.execute("SELECT * FROM requirements WHERE id = ?", (requirement_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="需求不存在")
        connection.execute(
            """
            INSERT INTO contributors (
                id, name, role, affiliation, github, contact_hash, participant_type, joined_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                contributor_id,
                payload.name.strip(),
                payload.role.strip(),
                payload.affiliation.strip(),
                payload.github.strip(),
                _hash_text(payload.contact),
                payload.participant_type.strip() or "volunteer",
                _now(),
            ),
        )
        connection.execute(
            """
            INSERT INTO requirement_contributors (
                id, requirement_id, contributor_id, role, message, status, requested_at
            ) VALUES (?, ?, ?, ?, ?, 'pending', ?)
            """,
            (join_id, requirement_id, contributor_id, payload.role.strip(), payload.message.strip(), _now()),
        )
        if row["status"] == "unclaimed":
            connection.execute(
                "UPDATE requirements SET status = 'in-progress', progress = MAX(progress, 10) WHERE id = ?",
                (requirement_id,),
            )
        connection.commit()
        updated = connection.execute("SELECT * FROM requirements WHERE id = ?", (requirement_id,)).fetchone()
        return {"ok": True, "join_request_id": join_id, "requirement": _serialize_requirement(updated, connection)}


@router.post("/requirements/{requirement_id}/progress")
async def update_requirement_progress(requirement_id: str, payload: ProgressInput) -> Dict[str, Any]:
    with closing(_get_connection()) as connection:
        row = connection.execute("SELECT * FROM requirements WHERE id = ?", (requirement_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="需求不存在")
        status = payload.status or ("completed" if payload.progress >= 100 else "in-progress")
        update_id = f"upd_{uuid.uuid4().hex[:12]}"
        connection.execute(
            "UPDATE requirements SET progress = ?, status = ? WHERE id = ?",
            (payload.progress, status, requirement_id),
        )
        connection.execute(
            """
            INSERT INTO progress_updates (
                id, requirement_id, content, author, progress, status, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (update_id, requirement_id, payload.content.strip(), payload.author.strip(), payload.progress, status, _now()),
        )
        connection.execute(
            "UPDATE projects SET progress = ? WHERE requirement_id = ?",
            (payload.progress, requirement_id),
        )
        connection.commit()
        updated = connection.execute("SELECT * FROM requirements WHERE id = ?", (requirement_id,)).fetchone()
        return {"ok": True, "requirement": _serialize_requirement(updated, connection)}


@router.get("/projects")
async def list_projects() -> Dict[str, Any]:
    with closing(_get_connection()) as connection:
        rows = connection.execute("SELECT * FROM projects ORDER BY progress DESC, target_date ASC").fetchall()
        return {"items": [dict(row) for row in rows]}


@router.get("/messages")
async def list_messages(room: str = "general", limit: int = Query(30, ge=1, le=200)) -> Dict[str, Any]:
    with closing(_get_connection()) as connection:
        rows = connection.execute(
            "SELECT * FROM room_messages WHERE room = ? ORDER BY created_at DESC LIMIT ?",
            (room, limit),
        ).fetchall()
        return {"room": room, "items": [dict(row) for row in rows]}


@router.post("/messages")
async def create_message(payload: MessageInput) -> Dict[str, Any]:
    message_id = f"msg_{uuid.uuid4().hex[:12]}"
    with closing(_get_connection()) as connection:
        connection.execute(
            """
            INSERT INTO room_messages (id, room, author_alias, role, content, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                message_id,
                payload.room.strip() or "general",
                payload.author_alias.strip() or "匿名共建者",
                payload.role.strip() or "volunteer",
                payload.content.strip(),
                _now(),
            ),
        )
        connection.commit()
        row = connection.execute("SELECT * FROM room_messages WHERE id = ?", (message_id,)).fetchone()
        return {"ok": True, "message": dict(row)}


@router.get("/consent-ledger")
async def list_consent_ledger(limit: int = Query(20, ge=1, le=200)) -> Dict[str, Any]:
    with closing(_get_connection()) as connection:
        rows = connection.execute(
            """
            SELECT event_id, scope, action, actor, note, previous_hash, event_hash, created_at
            FROM consent_events ORDER BY id DESC LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return {
            "privacy_mode": "subject alias is hashed; raw identity is not stored",
            "items": [dict(row) for row in rows],
        }


@router.post("/consent-ledger")
async def create_consent_event(payload: ConsentEventInput) -> Dict[str, Any]:
    created_at = _now()
    event_id = f"consent_{uuid.uuid4().hex[:12]}"
    subject_hash = _hash_text(payload.subject_alias)
    with closing(_get_connection()) as connection:
        previous_row = connection.execute(
            "SELECT event_hash FROM consent_events ORDER BY id DESC LIMIT 1"
        ).fetchone()
        previous_hash = previous_row["event_hash"] if previous_row else "genesis"
        event_material = "|".join(
            [
                event_id,
                subject_hash,
                payload.scope.strip(),
                payload.action,
                payload.actor.strip(),
                payload.note.strip(),
                previous_hash,
                created_at,
            ]
        )
        event_hash = hashlib.sha256(event_material.encode("utf-8")).hexdigest()
        connection.execute(
            """
            INSERT INTO consent_events (
                event_id, subject_alias_hash, scope, action, actor, note,
                previous_hash, event_hash, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event_id,
                subject_hash,
                payload.scope.strip(),
                payload.action,
                payload.actor.strip() or "MediChat-RD",
                payload.note.strip(),
                previous_hash,
                event_hash,
                created_at,
            ),
        )
        connection.commit()
        return {
            "ok": True,
            "event": {
                "event_id": event_id,
                "scope": payload.scope.strip(),
                "action": payload.action,
                "actor": payload.actor.strip() or "MediChat-RD",
                "previous_hash": previous_hash,
                "event_hash": event_hash,
                "created_at": created_at,
            },
        }


@router.get("/virtual-cohorts")
async def list_virtual_cohorts() -> Dict[str, Any]:
    with closing(_get_connection()) as connection:
        rows = connection.execute("SELECT * FROM virtual_cohorts ORDER BY created_at DESC").fetchall()
        return {
            "items": [
                {
                    **dict(row),
                    "data_sources": _json_loads(row["data_sources_json"], []),
                }
                for row in rows
            ]
        }


@router.post("/virtual-cohorts")
async def create_virtual_cohort(payload: CohortInput) -> Dict[str, Any]:
    cohort_id = f"cohort_{uuid.uuid4().hex[:12]}"
    with closing(_get_connection()) as connection:
        connection.execute(
            """
            INSERT INTO virtual_cohorts (
                id, name, disease_area, criteria, data_sources_json,
                target_size, owner, status, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 'planning', ?)
            """,
            (
                cohort_id,
                payload.name.strip(),
                payload.disease_area.strip(),
                payload.criteria.strip(),
                json.dumps([item.strip() for item in payload.data_sources if item.strip()], ensure_ascii=False),
                payload.target_size,
                payload.owner.strip() or "转化研究组",
                _now(),
            ),
        )
        connection.commit()
        row = connection.execute("SELECT * FROM virtual_cohorts WHERE id = ?", (cohort_id,)).fetchone()
        return {
            "ok": True,
            "cohort": {
                **dict(row),
                "data_sources": _json_loads(row["data_sources_json"], []),
            },
        }
