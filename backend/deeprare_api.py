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
    phenotype_profile: Dict
    mechanism_routing: List[Dict]
    acmg_evidence_matrix: List[Dict]
    actionability_map: List[Dict]
    phenopacket_lite: Dict
    agent_orchestration: List[Dict]
    longitudinal_timeline: List[Dict]
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
    workflow_phase_status = _build_workflow_phase_status(report)

    return DeepRareResponse(
        session_id=session_id,
        input_text=input_data.text,
        phenotypes=[PhenotypeResult(**p) for p in report["phenotypes"]],
        systems_involved=report["summary"]["systems_involved"],
        differential_diagnosis=[HypothesisResult(**d) for d in report["differential_diagnosis"]],
        recommendations=report["recommendations"],
        reasoning_chain=report["reasoning_chain"],
        workflow_phase_status=workflow_phase_status,
        github_module_mapping=DEEPRARE_OPEN_SOURCE_FRAMEWORK["github_modules"],
        methodology=DEEPRARE_OPEN_SOURCE_FRAMEWORK,
        phenotype_profile=_build_phenotype_profile(report, input_data, full_input),
        mechanism_routing=_build_mechanism_routing(report, full_input),
        acmg_evidence_matrix=_build_acmg_evidence_matrix(report, full_input),
        actionability_map=_build_actionability_map(report, full_input),
        phenopacket_lite=_build_phenopacket_lite(session_id, report, input_data, full_input),
        agent_orchestration=_build_agent_orchestration(report, full_input),
        longitudinal_timeline=_build_longitudinal_timeline(report, input_data, workflow_phase_status),
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


def _score_from_confidence(value, fallback: int = 0) -> int:
    if isinstance(value, (int, float)):
        score = value * 100 if value <= 1 else value
        return max(0, min(100, round(score)))
    if isinstance(value, str):
        digits = "".join(ch if ch.isdigit() or ch == "." else " " for ch in value).split()
        if digits:
            return max(0, min(100, round(float(digits[0]))))
        if "高" in value:
            return 82
        if "中" in value:
            return 58
        if "低" in value:
            return 34
    return fallback


def _contains_any(text: str, keywords: List[str]) -> bool:
    return any(keyword.lower() in text.lower() for keyword in keywords)


def _infer_onset_bucket(text: str, age: Optional[int]) -> Dict:
    if _contains_any(text, ["胎儿", "孕", "NT", "早孕", "新生儿"]):
        return {"label": "胎儿/围产期", "evidence": "文本包含胎儿、妊娠或围产期线索"}
    if _contains_any(text, ["婴儿", "婴幼儿", "幼儿"]):
        return {"label": "婴幼儿期", "evidence": "文本包含婴幼儿期线索"}
    if _contains_any(text, ["儿童", "孩子", "发育迟缓", "智力低下", "语言发育"]):
        return {"label": "儿童期", "evidence": "文本包含儿童发育或神经发育线索"}
    if age is not None:
        if age < 2:
            return {"label": "婴幼儿期", "evidence": f"输入年龄 {age} 岁"}
        if age < 18:
            return {"label": "儿童/青少年期", "evidence": f"输入年龄 {age} 岁"}
        return {"label": "成人期", "evidence": f"输入年龄 {age} 岁"}
    return {"label": "未明确", "evidence": "需要继续追问起病年龄"}


def _infer_progression(text: str) -> Dict:
    if _contains_any(text, ["进行性", "加重", "越来越", "进展", "下降"]):
        return {"label": "进行性", "evidence": "文本包含进展或加重描述"}
    if _contains_any(text, ["反复", "复发", "多次"]):
        return {"label": "复发性", "evidence": "文本包含复发或多次发生描述"}
    if _contains_any(text, ["急性", "突然"]):
        return {"label": "急性/亚急性", "evidence": "文本包含急性发生描述"}
    return {"label": "未明确", "evidence": "需要补充进展速度和稳定性"}


def _build_phenotype_profile(report: Dict, input_data: DeepRareInput, full_input: str) -> Dict:
    phenotypes = report.get("phenotypes", [])
    systems = report.get("summary", {}).get("systems_involved", [])
    confidence_scores = [_score_from_confidence(p.get("confidence", 0)) for p in phenotypes]
    average_confidence = round(sum(confidence_scores) / len(confidence_scores)) if confidence_scores else 0
    specificity_score = min(
        100,
        (len(phenotypes) * 14)
        + (len(systems) * 10)
        + (18 if report.get("summary", {}).get("multi_system") else 0)
        + (10 if _contains_any(full_input, ["发育", "胎儿", "重复", "甲基化", "癫痫", "肌萎缩"]) else 0),
    )
    negative_signals = [
        token for token in ["无家族史", "父母未携带", "基因阴性", "WES阴性", "WGS阴性", "CMA阴性", "AR阴性", "非FSHD1"]
        if token.lower() in full_input.lower()
    ]

    return {
        "onset": _infer_onset_bucket(full_input, input_data.age),
        "progression": _infer_progression(full_input),
        "systems": systems,
        "multi_system": bool(report.get("summary", {}).get("multi_system")),
        "hpo_count": len(phenotypes),
        "average_hpo_confidence": average_confidence,
        "specificity_score": specificity_score,
        "positive_phenotypes": [
            {
                "hpo_id": p.get("hpo_id"),
                "name": p.get("name"),
                "matched": p.get("matched"),
                "weight": "high" if _score_from_confidence(p.get("confidence", 0)) >= 80 else "moderate",
            }
            for p in phenotypes
        ],
        "negative_or_boundary_signals": negative_signals or ["尚未结构化记录阴性表型，需要继续追问。"],
        "next_questions": [
            "起病年龄、进展速度和是否存在平台期？",
            "是否存在明确阴性体征，例如无癫痫、无肌萎缩、无家族史？",
            "是否有原始基因检测、CNV、重复扩增或甲基化报告？",
        ],
    }


def _build_mechanism_routing(report: Dict, full_input: str) -> List[Dict]:
    phenotype_count = len(report.get("phenotypes", []))
    systems = report.get("summary", {}).get("systems_involved", [])
    routes = [
        {
            "mechanism": "SNV/Indel 单基因变异",
            "score": 72 if phenotype_count >= 3 else 48,
            "status": "优先评估" if phenotype_count >= 3 else "需要更多表型",
            "triggers": ["HPO 表型组合", "差异诊断候选"],
            "next_action": "对候选基因进行 Trio/WES/WGS 和 ACMG 证据矩阵复核。",
        },
        {
            "mechanism": "CNV / 结构变异",
            "score": 82 if _contains_any(full_input, ["CNV", "CMA", "缺失", "重复", "DEL", "DUP", "结构变异", "D4Z4"]) else 42,
            "status": "重点复核" if _contains_any(full_input, ["CNV", "CMA", "缺失", "重复", "DEL", "DUP", "结构变异", "D4Z4"]) else "备选路径",
            "triggers": ["CMA/CNV 线索", "肌营养不良或重复区域线索"],
            "next_action": "复核 CNV calling、IGV 断点、MLPA/qPCR 或长读长验证。",
        },
        {
            "mechanism": "重复扩增",
            "score": 86 if _contains_any(full_input, ["CAG", "重复扩增", "Kennedy", "RFC1", "C9orf72", "ATXN2", "D4Z4"]) else 36,
            "status": "专项检测" if _contains_any(full_input, ["CAG", "重复扩增", "Kennedy", "RFC1", "C9orf72", "ATXN2", "D4Z4"]) else "按表型决定",
            "triggers": ["神经肌肉表型", "常规测序阴性", "重复序列相关疾病谱"],
            "next_action": "使用 PCR/毛细管电泳、RP-PCR、Southern blot 或长读长测序确认。",
        },
        {
            "mechanism": "表观遗传 / 甲基化",
            "score": 88 if _contains_any(full_input, ["甲基化", "FSHD2", "表观遗传", "DUX4"]) else 30,
            "status": "机制转向" if _contains_any(full_input, ["甲基化", "FSHD2", "表观遗传", "DUX4"]) else "低优先级",
            "triggers": ["FSHD 谱系", "重复区域阴性但表型强匹配", "甲基化异常"],
            "next_action": "补充甲基化检测、SMCHD1/DNMT3B/LRIF1 等调控基因和单倍型分析。",
        },
        {
            "mechanism": "母胎免疫 / 非基因组机制",
            "score": 90 if _contains_any(full_input, ["胎儿水肿", "NT", "CD36", "抗体", "母胎", "妊娠", "水囊瘤"]) else 28,
            "status": "不能被 WGS 排除" if _contains_any(full_input, ["胎儿水肿", "NT", "CD36", "抗体", "母胎", "妊娠", "水囊瘤"]) else "场景依赖",
            "triggers": ["复发性妊娠异常", "胎儿水肿", "免疫血液学线索"],
            "next_action": "做免疫血液学专项检测，避免把 WGS 阴性误判为机制排除。",
        },
        {
            "mechanism": "可治疗 mimic",
            "score": 78 if _contains_any(full_input, ["肌无力", "神经病", "癫痫", "贫血", "骨痛", "内分泌", "乳房发育"]) or "神经系统" in systems else 46,
            "status": "并行排查" if _contains_any(full_input, ["肌无力", "神经病", "癫痫", "贫血", "骨痛", "内分泌", "乳房发育"]) or "神经系统" in systems else "安全网",
            "triggers": ["有可干预疾病相似表型", "基因结果阴性或 VUS"],
            "next_action": "同步排查免疫、代谢、血液肿瘤、淀粉样变和副肿瘤等可干预方向。",
        },
    ]
    return sorted(routes, key=lambda item: item["score"], reverse=True)


def _build_acmg_evidence_matrix(report: Dict, full_input: str) -> List[Dict]:
    rows = []
    phenotype_count = len(report.get("phenotypes", []))
    phenotype_strength = "Moderate" if phenotype_count >= 3 else "Supporting"
    for diagnosis in report.get("differential_diagnosis", [])[:5]:
        confidence = _score_from_confidence(diagnosis.get("confidence"), 30)
        rows.append({
            "candidate": diagnosis.get("disease"),
            "classification_boundary": "LP 倾向" if confidence >= 70 else "VUS / 待复核",
            "criteria": [
                {
                    "code": "PP4",
                    "strength": phenotype_strength,
                    "status": "supporting" if phenotype_count else "missing",
                    "rationale": f"当前有 {phenotype_count} 个 HPO/表型信号支持疾病谱匹配。",
                },
                {
                    "code": "PM2",
                    "strength": "Supporting",
                    "status": "pending",
                    "rationale": "需要接入 gnomAD/本地人群频率后判断是否为低频或缺失。",
                },
                {
                    "code": "PP3",
                    "strength": "Supporting",
                    "status": "pending",
                    "rationale": "需要整合 REVEL、AlphaMissense、CADD、SpliceAI 等计算预测。",
                },
                {
                    "code": "PS2/PM6",
                    "strength": "Moderate" if _contains_any(full_input, ["de novo", "新发", "父母未携带"]) else "Pending",
                    "status": "supporting" if _contains_any(full_input, ["de novo", "新发", "父母未携带"]) else "missing",
                    "rationale": "Trio 新发证据必须保留亲子关系和测序质量控制。",
                },
                {
                    "code": "PM3",
                    "strength": "Supporting" if _contains_any(full_input, ["复合杂合", "双等位", "trans"]) else "Not applicable",
                    "status": "supporting" if _contains_any(full_input, ["复合杂合", "双等位", "trans"]) else "not_applicable",
                    "rationale": "仅在隐性遗传和反式复合杂合证据存在时使用。",
                },
            ],
            "next_evidence": [
                "补充原始 VCF/变异注释、人群频率和遗传模式。",
                "复核家系来源、共分离和表型特异性。",
                "将支持证据与冲突证据分开记录，避免直接把 VUS 包装成确诊。",
            ],
        })
    return rows


def _build_actionability_map(report: Dict, full_input: str) -> List[Dict]:
    rows = []
    systems = report.get("summary", {}).get("systems_involved", [])
    for diagnosis in report.get("differential_diagnosis", [])[:3]:
        confidence = _score_from_confidence(diagnosis.get("confidence"), 30)
        rows.append({
            "target": diagnosis.get("disease"),
            "type": "候选诊断",
            "actionability_score": min(100, confidence + 10),
            "why_it_matters": "高排序候选需要尽快转化为可验证检查和遗传咨询问题。",
            "recommended_action": "带着候选诊断、HPO 表型和 ACMG 证据缺口去遗传门诊复核。",
        })

    mimic_rules = [
        ("CIDP/MMN", ["肌无力", "神经病", "运动感觉", "肌萎缩"], "免疫介导，部分患者可用 IVIG/免疫治疗。", "完善 EMG/NCS、脑脊液、神经免疫指标。"),
        ("POEMS 综合征", ["乳房发育", "内分泌", "周围神经病", "水肿"], "血液系统相关，漏诊会影响治疗窗口。", "查 VEGF、免疫固定电泳、骨病灶和内分泌轴。"),
        ("ATTR/AL 淀粉样变", ["周围神经病", "心肌", "自主神经", "蛋白尿"], "存在靶向药物和血液科治疗路径。", "查心超/心肌 MRI、游离轻链、TTR 和组织 Congo red。"),
        ("代谢/溶酶体病", ["脾大", "骨痛", "贫血", "发育迟缓"], "多种代谢病有酶替代、底物减少或试验机会。", "补充酶活、代谢筛查和专病基因 panel。"),
        ("母胎免疫机制", ["胎儿水肿", "NT", "CD36", "水囊瘤"], "不由 WGS 直接确诊，但影响再妊娠管理。", "做 CD36 表达、抗体、父胎抗原状态闭环验证。"),
    ]
    for target, keywords, why, action in mimic_rules:
        if _contains_any(full_input, keywords):
            rows.append({
                "target": target,
                "type": "可治疗 / 可干预 mimic",
                "actionability_score": 88,
                "why_it_matters": why,
                "recommended_action": action,
            })
    if not rows:
        rows.append({
            "target": "可治疗 mimic 安全网",
            "type": "安全检查",
            "actionability_score": 52,
            "why_it_matters": "未识别到明确可治疗 mimic，但未诊断病例应保留安全网。",
            "recommended_action": "根据系统受累补充免疫、代谢、感染、肿瘤和药物相关鉴别。",
        })
    return sorted(rows, key=lambda item: item["actionability_score"], reverse=True)


def _build_phenopacket_lite(session_id: str, report: Dict, input_data: DeepRareInput, full_input: str) -> Dict:
    onset = _infer_onset_bucket(full_input, input_data.age)
    return {
        "phenopacket_schema_version": "2.0-lite",
        "id": f"medichat-rd-{session_id}",
        "subject": {
            "id": f"anon-{session_id}",
            "age_at_last_encounter": input_data.age,
            "sex": input_data.gender or "unknown",
            "privacy": "anonymous_demo_record",
        },
        "phenotypic_features": [
            {
                "type": {"id": p.get("hpo_id"), "label": p.get("name")},
                "excluded": False,
                "description": p.get("matched"),
                "evidence": {"confidence": p.get("confidence")},
            }
            for p in report.get("phenotypes", [])
        ],
        "diseases": [
            {
                "term": {"label": d.get("disease")},
                "rank": d.get("rank"),
                "confidence": d.get("confidence"),
            }
            for d in report.get("differential_diagnosis", [])
        ],
        "medical_actions": [
            {"action": recommendation, "status": "recommended"}
            for recommendation in report.get("recommendations", [])
        ],
        "meta_data": {
            "created_by": "MediChat-RD DeepRare domain knowledge layer",
            "onset_bucket": onset["label"],
            "source_text_retained": False,
            "consent_scope": "platform_demo_or_clinical_review_only",
        },
    }


def _build_agent_orchestration(report: Dict, full_input: str) -> List[Dict]:
    phenotype_count = len(report.get("phenotypes", []))
    diagnosis_count = len(report.get("differential_diagnosis", []))
    has_genomic_hint = _contains_any(full_input, ["VCF", "WES", "WGS", "CNV", "变异", "基因", "CAG", "甲基化", "Trio"])
    return [
        {
            "agent": "Phenotype Agent",
            "status": "completed" if phenotype_count else "needs_input",
            "domain_contract": "自然语言 -> HPO、阴性表型、起病年龄、系统受累。",
            "output": f"{phenotype_count} 个 HPO/表型信号。",
        },
        {
            "agent": "Genotype Agent",
            "status": "ready" if has_genomic_hint else "waiting_for_vcf",
            "domain_contract": "VCF/CNV/重复扩增/甲基化 -> 候选变异与质量控制。",
            "output": "检测到基因组线索，建议接入原始报告。" if has_genomic_hint else "等待 VCF、CNV、重复扩增或甲基化报告。",
        },
        {
            "agent": "Mechanism Agent",
            "status": "completed",
            "domain_contract": "判断 SNV、CNV、重复扩增、表观遗传、母胎免疫和 mimic 路径。",
            "output": "已生成机制分流排序。",
        },
        {
            "agent": "ACMG Agent",
            "status": "drafted" if diagnosis_count else "waiting_for_candidate",
            "domain_contract": "候选变异 -> ACMG/AMP 证据项、冲突证据和分类边界。",
            "output": "已生成证据矩阵草案，需要原始变异数据补强。",
        },
        {
            "agent": "Mimic Agent",
            "status": "completed",
            "domain_contract": "并行识别可治疗、可干预或不能漏诊的 mimic。",
            "output": "已生成 actionability 安全网。",
        },
        {
            "agent": "Report Agent",
            "status": "completed",
            "domain_contract": "生成患者版、医生版和研究队列可复用结构。",
            "output": "已输出 Phenopacket-lite 和可追溯报告结构。",
        },
    ]


def _build_longitudinal_timeline(report: Dict, input_data: DeepRareInput, workflow_phase_status: List[Dict]) -> List[Dict]:
    onset = _infer_onset_bucket(report.get("summary", {}).get("patient_input", ""), input_data.age)
    return [
        {
            "timepoint": onset["label"],
            "event": "首发表型出现",
            "evidence": onset["evidence"],
            "privacy_mode": "使用年龄段，不展示精确日期。",
        },
        {
            "timepoint": "当前就诊/复盘",
            "event": "HPO 表型标准化",
            "evidence": f"识别 {len(report.get('phenotypes', []))} 个 HPO/表型信号。",
            "privacy_mode": "保留结构化表型，不保留原始身份信息。",
        },
        {
            "timepoint": "诊断转向点",
            "event": "机制分流与鉴别诊断",
            "evidence": f"生成 {len(report.get('differential_diagnosis', []))} 个候选诊断。",
            "privacy_mode": "展示候选和证据缺口，不展示原始报告编号。",
        },
        {
            "timepoint": "下一步",
            "event": "验证动作和随访计划",
            "evidence": f"{len(report.get('recommendations', []))} 条建议；{len(workflow_phase_status)} 个工作流节点。",
            "privacy_mode": "输出行动清单，可进入患者随访和研究队列。",
        },
    ]
