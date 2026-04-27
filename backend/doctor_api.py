"""
MediChat-RD — 医生AI助手 API
Jarvis模式：语音转写+实时诊断+病历生成+检查建议
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict
from pathlib import Path
import sys
import os

# Add agents to path
sys.path.insert(0, str(Path(__file__).parent.parent / "agents"))

router = APIRouter(prefix="/api/doctor", tags=["Doctor Agent"])

# Global agent instance (lazy init)
_agent = None

def get_agent():
    global _agent
    if _agent is None:
        from doctor_agent import DoctorAgent
        db_path = os.getenv("DB_PATH", "data/doctor_agent.db")
        _agent = DoctorAgent(db_path)
    return _agent


# ============ Request/Response Models ============

class StartConsultationReq(BaseModel):
    patient_id: str
    doctor_id: str
    chief_complaint: str

class TranscriptReq(BaseModel):
    session_id: str
    speaker: str  # doctor / patient
    text: str
    timestamp: Optional[str] = None

class DiagnosticSupportReq(BaseModel):
    query: str

class SuggestTestsReq(BaseModel):
    symptoms: List[str]
    suspected_disease: Optional[str] = ""

class SaveNoteReq(BaseModel):
    session_id: str
    patient_id: str


# ============ Endpoints ============

@router.post("/start")
async def start_consultation(req: StartConsultationReq):
    """开始诊疗会话"""
    agent = get_agent()
    try:
        result = agent.start_consultation(
            req.patient_id, req.doctor_id, req.chief_complaint
        )
        return {"ok": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/transcript")
async def add_transcript(req: TranscriptReq):
    """添加语音转写记录（实时分析）"""
    agent = get_agent()
    try:
        result = agent.transcript_add(req.speaker, req.text, req.timestamp)
        return {"ok": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/support")
async def diagnostic_support(req: DiagnosticSupportReq):
    """获取诊断支持"""
    agent = get_agent()
    try:
        result = agent.get_diagnostic_support(req.query)
        return {"ok": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/suggest-tests")
async def suggest_tests(req: SuggestTestsReq):
    """推荐检查项目"""
    agent = get_agent()
    try:
        result = agent.suggest_tests(req.symptoms, req.suspected_disease)
        return {"ok": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/note/{session_id}")
async def generate_note(session_id: str):
    """生成当前会话病历"""
    agent = get_agent()
    try:
        result = agent.generate_note()
        return {"ok": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_stats():
    """获取统计信息"""
    agent = get_agent()
    try:
        result = agent.get_stats()
        return {"ok": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
