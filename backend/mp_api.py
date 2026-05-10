from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Annotated, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field

from mp_store import MiniProgramStore
from mp_wechat_client import WeChatMiniProgramClient


router = APIRouter(prefix="/api/v1/mp", tags=["mini-program"])
store = MiniProgramStore()
wechat_client = WeChatMiniProgramClient()


class MiniProgramLoginRequest(BaseModel):
    code: str = Field(min_length=1)


class DeepRareSubmitRequest(BaseModel):
    symptoms: str = Field(min_length=2, max_length=500)
    age: str = Field(min_length=1, max_length=32)


class FollowupCheckinRequest(BaseModel):
    symptom_score: int = Field(ge=0, le=100)
    mood_score: int = Field(ge=0, le=100)
    note: str = Field(default="", max_length=300)


def _read_token(authorization: Annotated[Optional[str], Header()] = None) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="missing bearer token")
    return authorization.split(" ", 1)[1]


@router.post("/auth/login")
async def login(payload: MiniProgramLoginRequest):
    wechat_code = payload.code
    if wechat_client.configured:
        session_payload = await wechat_client.code_to_session(payload.code)
        wechat_code = session_payload.get("openid") or payload.code
    session = store.create_or_refresh_session(wechat_code)
    return {
        "access_token": session["access_token"],
        "user_id": session["user_id"],
        "patient_id": session["patient_id"],
        "expires_in": 60 * 60 * 24 * 7,
    }


@router.get("/home")
def get_home(token: str = Depends(_read_token)):
    session = store.require_session(token)
    return {
        "patient_name": session["display_name"],
        "journey_stage": "确诊后第一周",
        "next_actions": ["整理病历", "完成症状初筛", "进入欢迎房"],
        "spotlight_disease": "戈谢病",
        "live_rooms": [
            {
                "title": "新确诊患者欢迎房",
                "schedule": "今晚 20:00 · SecondMe Navigator",
                "summary": "确诊后第一周怎么整理病历、检查和情绪。",
            },
            {
                "title": "家长互助圆桌",
                "schedule": "周三 19:30 · 罕见病家属志愿者",
                "summary": "长期治疗依从性、营养和学校沟通。",
            },
            {
                "title": "临床试验机会追踪",
                "schedule": "每周五更新 · 研究助理 AI",
                "summary": "新药动态、筛选标准和受试者准备事项。",
            },
        ],
    }


@router.post("/deeprare/submit")
def submit_deeprare(payload: DeepRareSubmitRequest, token: str = Depends(_read_token)):
    session = store.require_session(token)
    task_id = f"mpdr_{uuid4().hex[:10]}"
    store.save_deeprare_task(
        session["patient_id"],
        task_id,
        {
            "symptoms": payload.symptoms,
            "age": payload.age,
            "created_at": datetime.now(timezone.utc).isoformat(),
        },
    )
    return {
        "task_id": task_id,
        "status": "triaged",
        "top_diseases": ["戈谢病", "法布雷病", "重症肌无力"],
        "suggested_tests": ["酶活性检测", "基因检测", "肌电图"],
    }


@router.get("/deeprare/result/{task_id}")
def get_deeprare_result(task_id: str, token: str = Depends(_read_token)):
    session = store.require_session(token)
    task = store.get_deeprare_task(session["patient_id"], task_id)
    if not task:
        raise HTTPException(status_code=404, detail="task not found")
    return {
        "task_id": task_id,
        "status": "triaged",
        "candidate_diseases": ["戈谢病", "法布雷病", "神经肌接头疾病"],
        "next_steps": ["补录家族史", "带检查单复诊", "进入病友欢迎房"],
        "source": task,
    }


@router.get("/community/feed")
def get_community_feed(token: str = Depends(_read_token)):
    store.require_session(token)
    return {
        "feed": [
            {
                "id": "post_welcome_001",
                "author": "小林妈妈",
                "disease": "戈谢病",
                "post_type": "经验分享",
                "summary": "刚确诊的第一周，先把检查单和病史按时间线收好，会明显减轻焦虑。",
            },
            {
                "id": "post_help_002",
                "author": "阿泽爸爸",
                "disease": "重症肌无力",
                "post_type": "求助提问",
                "summary": "孩子下午疲劳明显加重，大家复诊前通常会记录哪些症状波动？",
            },
            {
                "id": "post_support_003",
                "author": "研究助理 AI",
                "disease": "法布雷病",
                "post_type": "试验追踪",
                "summary": "本周更新了两项招募中的临床试验，已整理筛选标准和准备事项。",
            },
        ]
    }


@router.post("/avatar/create")
def create_avatar(token: str = Depends(_read_token)):
    session = store.require_session(token)
    store.bind_avatar(session["patient_id"], runtime="local")
    return {"status": "created", "provider": "local"}


@router.get("/profile")
def get_profile(token: str = Depends(_read_token)):
    session = store.require_session(token)
    avatar = store.get_avatar_binding(session["patient_id"])
    return {
        "patient_id": session["patient_id"],
        "linked_runtime": avatar["runtime"] if avatar else "local",
        "secondme_bound": False,
        "followup_enabled": True,
    }


@router.post("/followup/checkin")
def save_checkin(payload: FollowupCheckinRequest, token: str = Depends(_read_token)):
    session = store.require_session(token)
    checkin_id = f"checkin_{uuid4().hex[:10]}"
    store.save_checkin(
        session["patient_id"],
        {
            "checkin_id": checkin_id,
            "symptom_score": payload.symptom_score,
            "mood_score": payload.mood_score,
            "note": payload.note,
            "next_followup_at": (datetime.now(timezone.utc) + timedelta(days=3)).isoformat(),
        },
    )
    return {"status": "saved", "checkin_id": checkin_id}
