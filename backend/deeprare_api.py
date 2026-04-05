"""
MediChat-RD — DeepRare诊断模式API
参考Nature 2026 DeepRare论文架构
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'agents'))
from deeprare_orchestrator import DeepRareOrchestrator
from hpo_extractor import HPOExtractor

router = APIRouter(prefix="/api/v1/deeprare", tags=["DeepRare诊断"])

# 全局实例
orchestrator = DeepRareOrchestrator()


# ========== 数据模型 ==========
class DeepRareInput(BaseModel):
    """DeepRare诊断输入"""
    text: str = Field(..., description="症状描述（自由文本）")
    age: Optional[int] = Field(None, description="年龄")
    gender: Optional[str] = Field(None, description="性别")
    duration: Optional[str] = Field(None, description="症状持续时间")


class FollowUpInput(BaseModel):
    """追问输入"""
    question: str = Field(..., description="追问内容")


class PhenotypeResult(BaseModel):
    """表型提取结果"""
    hpo_id: str
    name: str
    matched: str
    confidence: float


class HypothesisResult(BaseModel):
    """诊断假设"""
    rank: int
    disease: str
    confidence: str
    reasoning: str


class DeepRareResponse(BaseModel):
    """DeepRare诊断响应"""
    session_id: str
    input_text: str
    phenotypes: List[PhenotypeResult]
    systems_involved: List[str]
    differential_diagnosis: List[HypothesisResult]
    recommendations: List[str]
    reasoning_chain: str
    timestamp: str


# ========== API端点 ==========
@router.post("/diagnose", response_model=DeepRareResponse)
async def deeprare_diagnose(input_data: DeepRareInput):
    """
    DeepRare模式诊断
    1. HPO表型提取（自由文本→标准化术语）
    2. 多源知识检索（PubMed/Orphanet/OMIM）
    3. 假设生成+自反思验证
    4. 输出可追溯推理链
    """
    import uuid
    session_id = str(uuid.uuid4())[:8]

    # 构建完整输入
    full_input = input_data.text
    if input_data.age:
        full_input = f"{input_data.age}岁患者，" + full_input
    if input_data.gender:
        full_input = f"{'男' if input_data.gender == 'male' else '女'}性，" + full_input
    if input_data.duration:
        full_input += f"，持续{input_data.duration}"

    # 执行诊断
    report = orchestrator.diagnose(full_input)

    return DeepRareResponse(
        session_id=session_id,
        input_text=input_data.text,
        phenotypes=[PhenotypeResult(**p) for p in report["phenotypes"]],
        systems_involved=report["summary"]["systems_involved"],
        differential_diagnosis=[HypothesisResult(**d) for d in report["differential_diagnosis"]],
        recommendations=report["recommendations"],
        reasoning_chain=report["reasoning_chain"],
        timestamp=datetime.now().isoformat(),
    )


@router.post("/follow-up")
async def deeprare_followup(input_data: FollowUpInput):
    """追问模式"""
    report = orchestrator.follow_up(input_data.question)
    return {
        "ok": True,
        "result": report,
    }


@router.get("/history")
async def deeprare_history():
    """获取诊断历史"""
    return {
        "ok": True,
        "memory": orchestrator.memory,
    }


@router.post("/extract-hpo")
async def extract_hpo(input_data: DeepRareInput):
    """仅提取HPO表型（不执行诊断）"""
    extractor = HPOExtractor()
    result = extractor.analyze_symptoms(input_data.text)
    return {
        "ok": True,
        "result": result,
    }
