"""
MediChat-RD — OpenEvidence模式 API
免费诊断工具 + 药企广告变现
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "agents"))

router = APIRouter(prefix="/api/openevidence", tags=["OpenEvidence"])

# Global engine instance
_engine = None

def get_engine():
    global _engine
    if _engine is None:
        from openevidence_engine import OpenEvidenceEngine
        _engine = OpenEvidenceEngine()
    return _engine


# ============ Models ============

class DoctorRegisterReq(BaseModel):
    name: str
    hospital: str
    department: str
    specialty_diseases: List[str]

class DiagnosisReq(BaseModel):
    doctor_id: str
    disease: str
    symptoms: List[str]
    context: str

class ClickReq(BaseModel):
    slot_id: str


# ============ Endpoints ============

@router.post("/register")
async def register_doctor(req: DoctorRegisterReq):
    """医生注册（免费层）"""
    engine = get_engine()
    result = engine.register_doctor(
        req.name, req.hospital, req.department, req.specialty_diseases
    )
    return {"ok": True, "data": result}


@router.post("/diagnose")
async def process_diagnosis(req: DiagnosisReq):
    """处理诊断 + 广告植入"""
    engine = get_engine()
    result = engine.process_diagnosis(
        req.doctor_id, req.disease, req.symptoms, req.context
    )
    return {"ok": True, "data": result}


@router.post("/click/{slot_id}")
async def record_click(slot_id: str):
    """记录广告点击"""
    engine = get_engine()
    result = engine.record_click(slot_id)
    return {"ok": True, "data": result}


@router.get("/ads")
async def get_ads(disease: str, moment: str = "differential_diagnosis", limit: int = 3):
    """获取相关广告"""
    engine = get_engine()
    from openevidence_engine import DecisionMoment
    try:
        m = DecisionMoment(moment)
    except (ValueError, KeyError):
        m = DecisionMoment.DIFFERENTIAL_DIAGNOSIS
    result = engine.get_relevant_ads(disease, [], m, limit)
    return {"ok": True, "data": result}


@router.get("/stats")
async def get_stats():
    """获取统计信息"""
    engine = get_engine()
    result = engine.get_stats()
    return {"ok": True, "data": result}


@router.get("/vs-openevidence")
async def vs_openevidence():
    """vs OpenEvidence对比"""
    engine = get_engine()
    result = engine.vs_openevidence()
    return {"ok": True, "data": result}
