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

DEEPRARE_OPEN_SOURCE_FRAMEWORK = {
    "source": {
        "paper": "An agentic system for rare disease diagnosis with traceable reasoning",
        "doi": "10.1038/s41586-025-10097-9",
        "github": "https://github.com/MAGIC-AI4Med/DeepRare",
        "policy": "作为功能和模块映射参考，不复制 DeepRare 源码、数据、模型权重或性能声明。",
    },
    "architecture": [
        {
            "name": "Central Host + Memory",
            "paper_role": "编排诊断流程、综合证据、生成候选并自反复核。",
            "medichat_mapping": "DeepRareOrchestrator + 患者 session + 可追溯推理链。",
            "status": "已接入",
        },
        {
            "name": "Specialized Agent Servers",
            "paper_role": "承载表型抽取、疾病标准化、知识检索、病例检索、表型分析和基因型分析。",
            "medichat_mapping": "HPOExtractor、KnowledgeRetriever、SelfReflectiveDiagnostic 和后续外部工具适配器。",
            "status": "部分接入",
        },
        {
            "name": "External Evidence Environment",
            "paper_role": "连接文献、指南、知识库、相似病例库和变异数据库。",
            "medichat_mapping": "本地罕见病库、HPO 词表、OMIM/Orphanet/PubMed 线索和平台研究能力。",
            "status": "持续扩展",
        },
    ],
    "github_modules": [
        {
            "module": "hpo_extractor.py",
            "capability": "自由文本表型抽取与 HPO 映射",
            "medichat_mapping": "HPOExtractor 与 DeepRare 输入解析",
        },
        {
            "module": "diagnosis.py",
            "capability": "HPO 驱动的差异诊断主流程",
            "medichat_mapping": "DeepRareOrchestrator.diagnose",
        },
        {
            "module": "diagnosisGene.py",
            "capability": "HPO + 基因/基因型联合诊断流程",
            "medichat_mapping": "基因摘要已在平台内展示，VCF/Exomiser 为下一步接入",
        },
        {
            "module": "tools/",
            "capability": "文献、知识库和专业工具检索",
            "medichat_mapping": "KnowledgeRetriever、MCP 数据工具和证据卡片",
        },
        {
            "module": "api/interface.py",
            "capability": "LLM provider 抽象",
            "medichat_mapping": "MIMO / OpenAI-compatible 客户端配置",
        },
        {
            "module": "inference.sh / inference_gene.sh / extract_hpo.sh",
            "capability": "可运行推理管线",
            "medichat_mapping": "Web 工作台按钮触发 API 管线",
        },
    ],
    "workflow": [
        {"phase": "临床资料录入", "status_key": "clinical_data_entry"},
        {"phase": "系统化追问", "status_key": "systematic_enquiry"},
        {"phase": "HPO 表型映射", "status_key": "hpo_mapping"},
        {"phase": "诊断分析与自反复核", "status_key": "diagnosis_and_reflection"},
        {"phase": "可追溯报告输出", "status_key": "traceable_report"},
    ],
}


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
    workflow_phase_status: List[Dict]
    github_module_mapping: List[Dict]
    methodology: Dict
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
        workflow_phase_status=_build_workflow_phase_status(report),
        github_module_mapping=DEEPRARE_OPEN_SOURCE_FRAMEWORK["github_modules"],
        methodology=DEEPRARE_OPEN_SOURCE_FRAMEWORK,
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


@router.get("/framework")
async def deeprare_framework():
    """DeepRare 论文和 GitHub 开源实现的能力映射"""
    return DEEPRARE_OPEN_SOURCE_FRAMEWORK


@router.post("/extract-hpo")
async def extract_hpo(input_data: DeepRareInput):
    """仅提取HPO表型（不执行诊断）"""
    extractor = HPOExtractor()
    result = extractor.analyze_symptoms(input_data.text)
    return {
        "ok": True,
        "result": result,
    }


def _build_workflow_phase_status(report: Dict) -> List[Dict]:
    phenotype_count = len(report.get("phenotypes", []))
    diagnosis_count = len(report.get("differential_diagnosis", []))
    recommendation_count = len(report.get("recommendations", []))
    reasoning_available = bool(report.get("reasoning_chain"))

    return [
        {
            "phase": "临床资料录入",
            "status": "已接收",
            "detail": "已接收自由文本症状、年龄和性别；家族史、检查报告、VCF 文件为下一阶段增强输入。",
        },
        {
            "phase": "系统化追问",
            "status": "待增强" if phenotype_count < 3 else "可继续复核",
            "detail": "根据表型数量判断是否需要继续追问系统受累、起病年龄、进展速度、阴性体征和遗传方式。",
        },
        {
            "phase": "HPO 表型映射",
            "status": "已完成" if phenotype_count else "未识别",
            "detail": f"当前识别 {phenotype_count} 个 HPO/表型信号。",
        },
        {
            "phase": "诊断分析与自反复核",
            "status": "已完成" if diagnosis_count else "证据不足",
            "detail": f"当前生成 {diagnosis_count} 个候选诊断，并保留可追溯推理链。",
        },
        {
            "phase": "可追溯报告输出",
            "status": "已生成" if reasoning_available else "待生成",
            "detail": f"已生成推理链和 {recommendation_count} 条下一步建议；PDF/Word 导出为后续增强。",
        },
    ]
