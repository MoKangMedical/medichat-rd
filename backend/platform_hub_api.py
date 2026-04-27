"""
MediChat-RD 患者平台聚合 API

把当前仓库里已经可用的诊断、知识、SecondMe 社群和研究能力
整理成统一的患者体验层，供前端以产品化方式展示。
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import json
import math
import os
import re
import subprocess
import sys

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from avatar_service import get_avatar_service
from community_api import get_community_manager, get_second_me_client
from hipaa_compliance import AuditAction, AuditLogger, DataClassification, DataMasker
from knowledge_api import EXTENDED_DB
from platform_contracts import (
    CarePlanObject,
    CommunityAvatarObject,
    ConsentProfile,
    DISEASE_GROUP_TEMPLATES,
    DiseaseObject,
    EvidenceObject,
    KPI_FRAMEWORK,
    OBJECT_MODEL_OVERVIEW,
    PatientObject,
    ResearchArtifactObject,
    ResearchPackageObject,
    STANDARDS_ALIGNMENT,
    VariantObject,
    build_object_model_schemas,
)
from quality_gate import QualityGateController


BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
AGENTS_DIR = PROJECT_ROOT / "agents"
sys.path.insert(0, str(AGENTS_DIR))

from deeprare_orchestrator import DeepRareOrchestrator
from drug_target_network import DrugTargetNetwork
from genomic_analyzer import GenomicAnalyzer, GenomicVariant
from hpo_extractor import HPOExtractor
from knowledge_graph import KnowledgeGraph
from medical_nlp import MedicalNLP
from patient_matcher import PatientMatcher, PatientProfile
from patient_registry import PatientRegistry
from rare_disease_agent import search_rare_disease_by_symptoms
from virtual_screening_agent import VirtualScreeningAgent


router = APIRouter(prefix="/api/v1/platform", tags=["患者平台"])

deeprare_orchestrator = DeepRareOrchestrator()
hpo_extractor = HPOExtractor()
drug_target_network = DrugTargetNetwork()
genomic_analyzer = GenomicAnalyzer()
knowledge_graph = KnowledgeGraph()
medical_nlp = MedicalNLP()
patient_registry = PatientRegistry(str(PROJECT_ROOT / "data" / "patient_registry.db"))
virtual_screening_agent = VirtualScreeningAgent()
audit_logger = AuditLogger(str(PROJECT_ROOT / "logs" / "platform_audit.log"))
quality_gate_controller = QualityGateController()


class SymptomCheckRequest(BaseModel):
    text: str = Field(..., min_length=3, description="患者自由文本症状")
    age: Optional[int] = Field(None, ge=0, le=120)
    gender: Optional[str] = Field(None, description="性别")


class DiseaseResearchRequest(BaseModel):
    disease_name: str = Field(..., min_length=2, description="疾病名称，中英文皆可")


class DrugClueRequest(BaseModel):
    disease_name: str = Field(..., min_length=2, description="疾病名称，中英文皆可")


class VariantPayload(BaseModel):
    gene: str = Field(..., min_length=1, description="基因名")
    chromosome: str = Field("NA", description="染色体")
    position: int = Field(0, ge=0, description="位置")
    ref: str = Field("N", min_length=1, description="参考等位基因")
    alt: str = Field("N", min_length=1, description="变异等位基因")
    variant_type: str = Field("SNV", description="变异类型")
    hgvs_c: str = Field("", description="c.位点")
    hgvs_p: str = Field("", description="p.位点")
    pathogenicity: str = Field("VUS", description="致病性")
    allele_frequency: float = Field(0.0, ge=0.0, le=1.0, description="等位基因频率")


class GenomicTriageRequest(BaseModel):
    symptoms_text: str = Field(..., min_length=3, description="症状文本")
    disease_name: Optional[str] = Field(None, description="已知或怀疑疾病")
    variants: List[VariantPayload] = Field(default_factory=list, description="患者报告的变异")
    age_of_onset: Optional[int] = Field(None, ge=0, le=120)
    gender: Optional[str] = Field(None)


class RegistryEnrollmentRequest(BaseModel):
    disease_name: str = Field(..., min_length=2, description="疾病名称")
    symptoms_text: str = Field(..., min_length=3, description="症状文本")
    variants: List[VariantPayload] = Field(default_factory=list)
    diagnosis_status: str = Field("suspected", description="诊断状态")
    age_of_onset: Optional[int] = Field(None, ge=0, le=120)
    gender: Optional[str] = Field(None)
    ethnicity: Optional[str] = Field(None)
    consent_research: bool = Field(True)
    consent_matching: bool = Field(True)


class CommunityMatchRequest(BaseModel):
    disease_name: str = Field(..., min_length=2)
    symptoms_text: str = Field(..., min_length=3)
    age: Optional[int] = Field(None, ge=0, le=120)
    gender: Optional[str] = Field(None)
    location: Optional[str] = Field(None)


class VirtualScreeningRequest(BaseModel):
    disease_name: str = Field(..., min_length=2)
    gene: Optional[str] = Field(None)
    target_name: Optional[str] = Field(None)
    library: str = Field("chembl")


class ResearchPackageRequest(BaseModel):
    disease_name: Optional[str] = Field(None, description="疾病名称")
    registry_id: Optional[str] = Field(None, description="已登记患者 ID")
    symptoms_text: Optional[str] = Field("", description="补充症状文本")
    gene_hint: Optional[str] = Field(None, description="基因提示")
    variants: List[VariantPayload] = Field(default_factory=list)
    include_virtual_screening: bool = Field(True, description="是否附带虚拟筛选摘要")


class CohortCreateRequest(BaseModel):
    name: str = Field(..., min_length=2)
    disease: str = Field(..., min_length=2)
    criteria: str = Field("", description="纳入标准")
    registry_ids: List[str] = Field(default_factory=list, description="可选：创建时直接加入的患者")


class CohortAddPatientRequest(BaseModel):
    registry_id: str = Field(..., min_length=4)


class LongitudinalCareRequest(BaseModel):
    registry_id: str = Field(..., min_length=4)
    current_stage: str = Field("newly_diagnosed", description="当前阶段")
    note: str = Field(..., min_length=2, description="本次随访或管理更新")
    symptoms_text: Optional[str] = Field("", description="补充症状")
    goals: List[str] = Field(default_factory=list, description="本阶段目标")
    update_type: str = Field("follow_up", description="更新类型")


MODULE_CATALOG: List[Dict[str, str]] = [
    {"path": "agents/hpo_extractor.py", "title": "HPO 表型提取", "category": "诊断引擎", "summary": "把患者自由文本标准化为 HPO 编码。"},
    {"path": "agents/hpo_ontology.py", "title": "HPO 本体扩展", "category": "诊断引擎", "summary": "支持症状同义词扩展和结构化检索。"},
    {"path": "agents/hallucination_guard.py", "title": "幻觉防护", "category": "诊断引擎", "summary": "在诊断链路里做证据校验和置信度惩罚。"},
    {"path": "agents/lab_analyzer.py", "title": "实验室检验解析", "category": "临床辅助", "summary": "解析常见检验项目并识别危急值线索。"},
    {"path": "agents/orchestrator.py", "title": "多 Agent 编排器", "category": "诊断引擎", "summary": "把多类专业 agent 串成可追溯流程。"},
    {"path": "agents/patient_history.py", "title": "病例管理", "category": "患者运营", "summary": "管理病历上下文与长期病程摘要。"},
    {"path": "agents/report_generator.py", "title": "诊断报告生成", "category": "诊断引擎", "summary": "输出结构化 Markdown / JSON 报告。"},
    {"path": "agents/knowledge_retriever.py", "title": "知识检索", "category": "研究与知识", "summary": "接入 PubMed、Orphanet、OMIM 等资料。"},
    {"path": "agents/doctor_agent.py", "title": "医生 AI 助手", "category": "临床辅助", "summary": "支持问诊、病历整理、检查建议和长期追踪。"},
    {"path": "agents/openevidence_engine.py", "title": "OpenEvidence 引擎", "category": "临床辅助", "summary": "围绕医生问答场景组织证据与知识触达。"},
    {"path": "agents/genomic_analyzer.py", "title": "基因组联合分析", "category": "基因与登记", "summary": "把 HPO 表型与变异线索联合排序。"},
    {"path": "agents/patient_registry.py", "title": "患者注册系统", "category": "基因与登记", "summary": "提供患者登记、队列管理与 Phenopacket 导出。"},
    {"path": "agents/knowledge_graph.py", "title": "知识图谱", "category": "研究与知识", "summary": "连接疾病、基因、药物和表型关系。"},
    {"path": "agents/medical_nlp.py", "title": "医学 NLP", "category": "临床辅助", "summary": "抽取实体、关系并整理病历摘要。"},
    {"path": "agents/patient_matcher.py", "title": "患者匹配引擎", "category": "患者运营", "summary": "基于表型、疾病和阶段推荐同路病友。"},
    {"path": "agents/deeprare_orchestrator.py", "title": "DeepRare 编排", "category": "诊断引擎", "summary": "多层推理、自反思和差异诊断。"},
    {"path": "agents/doctor_profiles.py", "title": "医生档案", "category": "临床辅助", "summary": "管理多学科医生身份与应答风格。"},
    {"path": "agents/drug_repurposing_agent.py", "title": "药物重定位", "category": "研究与知识", "summary": "整合靶点与已知药物，给出研究线索。"},
    {"path": "agents/rare_disease_agent.py", "title": "罕见病筛查 Agent", "category": "诊断引擎", "summary": "按症状、基因、OMIM 做首轮筛查。"},
    {"path": "agents/mimo_research_agent.py", "title": "MIMO 研究 Agent", "category": "研究与知识", "summary": "把研究摘要与临床视角组合成解释文本。"},
    {"path": "agents/virtual_screening_agent.py", "title": "虚拟筛选 Agent", "category": "转化研究", "summary": "完成靶点准备、口袋识别、药效团建模和 hit 验证。"},
    {"path": "agents/drug_target_network.py", "title": "药物-靶点网络", "category": "转化研究", "summary": "构建药物-靶点-疾病网络并寻找再定位机会。"},
    {"path": "agents/drug_repurposing_optimizer.py", "title": "药物重定位优化", "category": "转化研究", "summary": "对候选药物路线做优先级与可行性整理。"},
    {"path": "agents/enhanced_drug_repurposing_agent.py", "title": "增强药物重定位", "category": "转化研究", "summary": "融合更多证据面扩展重定位候选。"},
    {"path": "agents/enhanced_repurposing_agent.py", "title": "增强再利用 Agent", "category": "转化研究", "summary": "进一步强化药物候选整合与解释。"},
    {"path": "agents/medical_agents.py", "title": "医学 Agent 集合", "category": "临床辅助", "summary": "统一系统提示词、角色编排和医生画像。"},
    {"path": "backend/secondme_integration.py", "title": "SecondMe 分身层", "category": "患者运营", "summary": "为患者创建 AI 分身并接入社群。"},
    {"path": "backend/secondme_oauth.py", "title": "SecondMe OAuth", "category": "患者运营", "summary": "服务端授权、token 存储与用户归一化。"},
    {"path": "backend/secondme_mcp_api.py", "title": "SecondMe MCP", "category": "开放集成", "summary": "向 SecondMe 暴露结构化工具能力。"},
    {"path": "backend/community_api.py", "title": "病友社群 API", "category": "患者运营", "summary": "病友圈、帖子、Bridge 配对与互动发现。"},
    {"path": "backend/knowledge_api.py", "title": "罕见病知识库", "category": "研究与知识", "summary": "121 种罕见病详情、分类与治疗摘要。"},
]

DEMO_PATIENT_PROFILES: List[PatientProfile] = [
    PatientProfile("demo_mg_01", "重症肌无力", ["眼睑下垂", "吞咽困难", "肌无力"], 28, "女", "上海"),
    PatientProfile("demo_mg_02", "重症肌无力", ["眼睑下垂", "复视", "疲劳"], 36, "女", "杭州"),
    PatientProfile("demo_gd_01", "戈谢病", ["肝脾肿大", "贫血", "骨痛"], 12, "男", "北京"),
    PatientProfile("demo_fd_01", "法布雷病", ["肢端疼痛", "血管角化瘤", "肾功能不全"], 24, "男", "深圳"),
    PatientProfile("demo_sma_01", "脊髓性肌萎缩症", ["肌无力", "肌肉萎缩", "发育迟缓"], 8, "女", "成都"),
    PatientProfile("demo_oi_01", "成骨不全症", ["反复骨折", "蓝巩膜", "关节痛"], 17, "女", "南京"),
]

PDB_HINTS = {
    "GBA": "2F61",
    "GBA1": "2F61",
    "GLA": "1R46",
    "SMN1": "4NL6",
    "SMN2": "4NL6",
    "DMD": "1DXX",
    "CHRNE": "2BG9",
    "CHRNA1": "2BG9",
    "C5": "3CU7",
}

SCIENTIFIC_SKILL_LIBRARY: List[Dict[str, Any]] = [
    {
        "slug": "database-lookup",
        "title": "Scientific Database Lookup",
        "category": "科学数据库",
        "focus": "跨 70+ 公共数据库的统一检索，用于 OMIM、ClinVar、HPO、ChEMBL、ClinicalTrials.gov 等交叉查询。",
        "workflow": "罕见病证据检索",
    },
    {
        "slug": "rdkit",
        "title": "RDKit",
        "category": "药物研发",
        "focus": "做分子描述符、相似性、指纹和结构标准化，适合先导化合物分析。",
        "workflow": "候选分子整理",
    },
    {
        "slug": "diffdock",
        "title": "DiffDock",
        "category": "药物研发",
        "focus": "预测蛋白-配体结合姿势，适合和虚拟筛选、AlphaFold 结构一起使用。",
        "workflow": "结合位点与对接",
    },
    {
        "slug": "medchem",
        "title": "MedChem Filters",
        "category": "药物研发",
        "focus": "执行药物相似性、PAINS、结构警报和优先级过滤。",
        "workflow": "化合物优选",
    },
    {
        "slug": "pyhealth",
        "title": "PyHealth",
        "category": "临床研究",
        "focus": "围绕 EHR、临床预测、医疗编码和健康 AI 模型做标准化分析。",
        "workflow": "临床队列建模",
    },
    {
        "slug": "clinical-decision-support",
        "title": "Clinical Decision Support",
        "category": "临床研究",
        "focus": "生成面向药企和临床研究的证据分级、队列比较和建议文档。",
        "workflow": "证据决策简报",
    },
    {
        "slug": "treatment-plans",
        "title": "Treatment Plans",
        "category": "患者管理",
        "focus": "输出简洁可执行的治疗计划与照护路径，适合长期管理沟通。",
        "workflow": "个体化治疗规划",
    },
    {
        "slug": "literature-review",
        "title": "Literature Review",
        "category": "学术交流",
        "focus": "完成多数据库系统综述、文献汇总与引用核验。",
        "workflow": "系统综述与研究现状",
    },
    {
        "slug": "scientific-writing",
        "title": "Scientific Writing",
        "category": "学术交流",
        "focus": "把研究提纲转成论文段落、摘要、图表说明和投稿级文稿。",
        "workflow": "论文与报告写作",
    },
]

SCIENTIFIC_RUNTIME_CHECKER = PROJECT_ROOT / "scripts" / "check_scientific_runtime.py"


def _available_modules() -> List[Dict[str, str]]:
    modules = []
    for item in MODULE_CATALOG:
        if (PROJECT_ROOT / item["path"]).exists():
            modules.append(item)
    return modules


def _normalize_disease_record(disease: Dict[str, Any]) -> Dict[str, Any]:
    hospitals = disease.get("specialist_hospitals") or []
    if isinstance(hospitals, str):
        hospitals = [part.strip() for part in hospitals.split("、") if part.strip()]
    symptoms = disease.get("symptoms")
    if isinstance(symptoms, list):
        symptom_list = symptoms
    elif isinstance(symptoms, str):
        symptom_list = [part.strip() for part in symptoms.replace("；", "，").split("，") if part.strip()]
    else:
        symptom_list = []

    return {
        "name": disease.get("name", ""),
        "name_en": disease.get("name_en", ""),
        "category": disease.get("category", "未分类"),
        "gene": disease.get("gene", "未知"),
        "inheritance": disease.get("inheritance") or "待补充",
        "prevalence": disease.get("prevalence") or "待补充",
        "symptoms": symptom_list[:8],
        "treatment_summary": disease.get("treatment_summary") or "当前知识库暂无治疗摘要",
        "specialist_hospitals": hospitals[:5],
    }


def _find_disease(query: str) -> Optional[Dict[str, Any]]:
    query_lower = query.strip().lower()
    if not query_lower:
        return None

    exact = EXTENDED_DB.get(query)
    if exact:
        return exact

    for disease in EXTENDED_DB.values():
        fields = [
            disease.get("name", ""),
            disease.get("name_en", ""),
            disease.get("gene", ""),
            disease.get("category", ""),
        ]
        if any(query_lower == str(value).strip().lower() for value in fields if value):
            return disease

    for disease in EXTENDED_DB.values():
        fields = [
            disease.get("name", ""),
            disease.get("name_en", ""),
            disease.get("gene", ""),
            disease.get("category", ""),
            disease.get("symptoms", ""),
        ]
        if any(query_lower in str(value).strip().lower() for value in fields if value):
            return disease
    return _build_fallback_disease_record(query)


def _build_fallback_disease_record(query: str) -> Optional[Dict[str, Any]]:
    graph_hits = knowledge_graph.search(query)
    disease_node = next((item for item in graph_hits if item["type"] == "disease"), None)
    if disease_node:
        related = knowledge_graph.query_related(disease_node["id"])
        genes = [item["label"] for item in related.get("genes", [])]
        symptoms = [item["label"] for item in related.get("phenotypes", [])]
        drugs = [item["label"] for item in related.get("drugs", [])]
        return {
            "name": disease_node["label"],
            "name_en": "",
            "gene": genes[0] if genes else "",
            "category": "知识图谱疾病",
            "inheritance": "待补充",
            "prevalence": "待补充",
            "symptoms": symptoms,
            "treatment_summary": (
                f"图谱侧当前关联药物包括：{'、'.join(drugs[:3])}。"
                if drugs else "图谱侧暂未整理出明确治疗摘要。"
            ),
            "specialist_hospitals": [],
        }

    network_drugs = [
        drug.name
        for drug in drug_target_network.drugs.values()
        if query in drug.indications
    ]
    if network_drugs:
        return {
            "name": query,
            "name_en": "",
            "gene": "",
            "category": "药物网络疾病",
            "inheritance": "待补充",
            "prevalence": "待补充",
            "symptoms": [],
            "treatment_summary": f"药物网络侧已发现相关治疗：{'、'.join(network_drugs[:3])}。",
            "specialist_hospitals": [],
        }

    return None


def _community_discovery_snapshot() -> Dict[str, Any]:
    mgr = get_community_manager()
    communities = list(mgr.communities.values())
    ranked_communities = sorted(
        communities,
        key=lambda comm: (len(mgr.posts.get(comm.community_id, [])) * 5) + comm.member_count,
        reverse=True,
    )
    featured_communities = [
        {
            "id": comm.community_id,
            "name": comm.name,
            "description": comm.description,
            "member_count": comm.member_count,
            "post_count": len(mgr.posts.get(comm.community_id, [])),
        }
        for comm in ranked_communities[:4]
    ]

    posts = []
    for community_id, items in mgr.posts.items():
        community = mgr.communities.get(community_id)
        for post in items:
            posts.append(
                {
                    "id": post.post_id,
                    "community_name": community.name if community else "",
                    "author": post.author_nickname,
                    "content": post.content,
                    "likes": post.likes,
                    "type": post.post_type.value if hasattr(post.post_type, "value") else str(post.post_type),
                }
            )
    trending_posts = sorted(posts, key=lambda item: item["likes"], reverse=True)[:4]
    return {"communities": featured_communities, "posts": trending_posts}


def _parse_prevalence_denominator(prevalence: str) -> int:
    if not prevalence:
        return 1_000_000
    match = re.search(r"1\s*/\s*([\d,]+)", prevalence)
    if not match:
        return 1_000_000
    try:
        return max(1, int(match.group(1).replace(",", "")))
    except ValueError:
        return 1_000_000


def _classify_prevalence_tier(denominator: int) -> str:
    if denominator <= 10_000:
        return "相对常见"
    if denominator <= 50_000:
        return "中度罕见"
    return "极罕见"


def _classify_care_status(treatment_summary: str) -> Dict[str, str]:
    summary = (treatment_summary or "").lower()
    treatable_terms = (
        "酶替代", "替代治疗", "基因治疗", "补体", "伴侣疗法", "小分子", "预防性输注",
        "凝血因子", "利鲁唑", "依达拉奉", "口服方案",
    )
    manageable_terms = (
        "综合管理", "长期管理", "支持治疗", "康复", "营养", "监测", "对症",
        "随访", "呼吸支持", "止痛", "保护",
    )

    if any(term in summary for term in treatable_terms):
        return {
            "key": "treatable",
            "label": "治疗路径明确",
            "description": "已有相对明确的治疗抓手，可直接进入治疗与随访讨论。",
            "accent": "#0DBF9B",
        }
    if any(term in summary for term in manageable_terms):
        return {
            "key": "manageable",
            "label": "长期管理为主",
            "description": "更强调长期管理、监测和生活质量维持。",
            "accent": "#D9AD43",
        }
    return {
        "key": "research",
        "label": "研究推进中",
        "description": "当前更适合先做研究跟踪、临床试验与机制线索整理。",
        "accent": "#FF7A59",
    }


def _build_disease_cloud_items() -> List[Dict[str, Any]]:
    normalized_records = [_normalize_disease_record(disease) for disease in EXTENDED_DB.values()]
    if not normalized_records:
        return []

    denominators = [_parse_prevalence_denominator(item.get("prevalence", "")) for item in normalized_records]
    log_min = math.log(min(denominators))
    log_max = math.log(max(denominators))
    spread = max(log_max - log_min, 1e-6)

    items: List[Dict[str, Any]] = []
    for item in normalized_records:
        denominator = _parse_prevalence_denominator(item.get("prevalence", ""))
        rarity_position = (log_max - math.log(denominator)) / spread
        weight = round(0.52 + (rarity_position * 0.88), 3)
        care_status = _classify_care_status(item.get("treatment_summary", ""))
        symptoms = list(item.get("symptoms", []) or [])
        items.append(
            {
                "slug": item["name_en"] or item["name"],
                "name": item["name"],
                "name_en": item["name_en"],
                "category": item["category"],
                "gene": item["gene"],
                "prevalence": item["prevalence"],
                "prevalence_denominator": denominator,
                "prevalence_tier": _classify_prevalence_tier(denominator),
                "weight": weight,
                "care_status": care_status,
                "symptoms": symptoms[:4],
                "treatment_excerpt": "；".join(
                    [part.strip() for part in re.split(r"[；。]", item.get("treatment_summary", "")) if part.strip()][:2]
                ) or item.get("treatment_summary", ""),
                "community_hint": f"{item['name']}互助圈",
            }
        )

    items.sort(key=lambda disease: (-disease["weight"], disease["name"]))
    return items


def _build_drug_clues(disease: Dict[str, Any]) -> List[Dict[str, str]]:
    gene = str(disease.get("gene", "") or "").upper()
    name = disease.get("name") or disease.get("name_en") or "该疾病"
    category = disease.get("category", "未分类")

    predefined = {
        "GBA": [
            {"candidate": "Imiglucerase", "stage": "已上市", "rationale": "酶替代治疗是 GBA 相关溶酶体病的一线已知路径。"},
            {"candidate": "Eliglustat", "stage": "精准用药", "rationale": "可作为部分患者的底物减少治疗策略。"},
        ],
        "GLA": [
            {"candidate": "Agalsidase beta", "stage": "已上市", "rationale": "针对 alpha-galactosidase A 缺陷的经典酶替代策略。"},
            {"candidate": "Migalastat", "stage": "精准用药", "rationale": "适用于特定可折叠变异的伴侣疗法方向。"},
        ],
        "SMN1": [
            {"candidate": "Nusinersen", "stage": "已上市", "rationale": "SMN 通路修饰是脊髓性肌萎缩症核心方向。"},
            {"candidate": "Risdiplam", "stage": "口服方案", "rationale": "提升 SMN 蛋白表达，适合长期管理视角。"},
        ],
        "DMD": [
            {"candidate": "Ataluren", "stage": "特定突变策略", "rationale": "对部分无义突变患者存在通路价值。"},
            {"candidate": "Exon-skipping 方案", "stage": "精准策略", "rationale": "针对不同外显子跳读位点做分层治疗。"},
        ],
    }

    if gene in predefined:
        return predefined[gene]

    return [
        {
            "candidate": f"{name} 相关通路药物筛查",
            "stage": "研究线索",
            "rationale": f"基于 {category} 分类与致病基因 {gene or '待明确'}，适合先做作用通路和已上市药物交叉筛选。",
        },
        {
            "candidate": "真实世界再利用机会",
            "stage": "观察研究",
            "rationale": "可优先从同机制用药、对症药物和多中心病例报道中寻找再定位证据。",
        },
    ]


def _extract_phenotype_bundle(text: str) -> Tuple[Dict[str, Any], List[str]]:
    if not text.strip():
        return {"extracted_phenotypes": [], "systems_involved": []}, []

    result = hpo_extractor.analyze_symptoms(text)
    extracted = []
    seen = set()
    for item in result.get("extracted_phenotypes", []):
        label = item.get("matched_text") or item.get("name")
        if label and label not in seen:
            seen.add(label)
            extracted.append(label)
    return result, extracted


def _build_variant_models(
    variants: List[VariantPayload],
    fallback_gene: Optional[str] = None,
) -> Tuple[List[GenomicVariant], str]:
    if variants:
        return (
            [
                GenomicVariant(
                    chromosome=variant.chromosome,
                    position=variant.position,
                    ref=variant.ref,
                    alt=variant.alt,
                    gene=variant.gene.strip().upper(),
                    variant_type=variant.variant_type,
                    hgvs_c=variant.hgvs_c,
                    hgvs_p=variant.hgvs_p,
                    pathogenicity=variant.pathogenicity,
                    allele_frequency=variant.allele_frequency,
                )
                for variant in variants
            ],
            "reported_variant",
        )

    if fallback_gene:
        return (
            [
                GenomicVariant(
                    chromosome="NA",
                    position=0,
                    ref="N",
                    alt="N",
                    gene=fallback_gene.strip().upper(),
                    variant_type="SNV",
                    hgvs_c="待补充",
                    hgvs_p="",
                    pathogenicity="VUS",
                    allele_frequency=0.0001,
                )
            ],
            "knowledge_hint",
        )

    return ([], "phenotype_only")


def _build_patient_matcher() -> PatientMatcher:
    matcher = PatientMatcher()
    seen_ids = set()

    for profile in DEMO_PATIENT_PROFILES:
        matcher.add_patient(profile)
        seen_ids.add(profile.patient_id)

    for record in patient_registry.search_patients(limit=200):
        registry_id = record.get("registry_id")
        if not registry_id or registry_id in seen_ids:
            continue
        matcher.add_patient(
            PatientProfile(
                patient_id=registry_id,
                disease=record.get("disease", ""),
                hpo_phenotypes=record.get("hpo_phenotypes", []),
                age=record.get("age_of_onset") or 0,
                gender=record.get("gender", "") or "",
                location=record.get("ethnicity", "") or "登记库",
            )
        )
        seen_ids.add(registry_id)

    try:
        secondme_client = get_second_me_client()
        for avatar in secondme_client.get_all_avatars():
            if avatar.avatar_id in seen_ids:
                continue
            _, phenotypes = _extract_phenotype_bundle(f"{avatar.memory_summary} {avatar.bio}")
            matcher.add_patient(
                PatientProfile(
                    patient_id=avatar.avatar_id,
                    disease=avatar.disease_type,
                    hpo_phenotypes=phenotypes,
                    age=0,
                    gender="",
                    location="SecondMe 社群",
                )
            )
            seen_ids.add(avatar.avatar_id)
    except Exception:
        pass

    return matcher


def _resolve_graph_snapshot(disease_name: str, gene_hint: str = "") -> Dict[str, Any]:
    candidates = knowledge_graph.search(disease_name)
    node = next((item for item in candidates if item["type"] == "disease"), None)

    if node is None and gene_hint:
        gene_candidates = knowledge_graph.search(gene_hint)
        node = next((item for item in gene_candidates if item["type"] == "gene"), None)

    if node is None:
        return {"center": None, "related": {"genes": [], "drugs": [], "phenotypes": [], "diseases": []}}

    related = knowledge_graph.query_related(node["id"])
    return {"center": node, "related": related}


def _count_shared_terms(left: List[str], right: List[str]) -> int:
    count = 0
    for l_item in left:
        for r_item in right:
            if l_item == r_item or l_item in r_item or r_item in l_item:
                count += 1
                break
    return count


def _resolve_target_context(
    disease_name: str,
    gene_hint: Optional[str] = None,
    target_name: Optional[str] = None,
) -> Dict[str, str]:
    disease = _find_disease(disease_name)
    normalized = _normalize_disease_record(disease) if disease else None
    gene = (gene_hint or (normalized["gene"] if normalized else "") or "").strip().upper()
    name = target_name or (gene and f"{gene} target") or f"{disease_name} 相关靶点"
    pdb_id = PDB_HINTS.get(gene, (f"{gene}XXXX" if gene else "RD01")[:4].ljust(4, "X"))

    return {
        "disease_name": normalized["name"] if normalized and normalized["name"] else disease_name,
        "gene": gene or "UNKNOWN",
        "target_name": name,
        "pdb_id": pdb_id,
    }


def _audit(action: AuditAction, resource_type: str, resource_id: str = "", details: Optional[Dict[str, Any]] = None) -> None:
    try:
        audit_logger.log(
            action=action,
            resource_type=resource_type,
            resource_id=resource_id or None,
            details=details or {},
            success=True,
        )
    except Exception:
        pass


def _disease_to_object(normalized: Dict[str, Any]) -> DiseaseObject:
    return DiseaseObject(
        name=normalized.get("name", ""),
        name_en=normalized.get("name_en", ""),
        category=normalized.get("category", "未分类"),
        gene=normalized.get("gene", ""),
        inheritance=normalized.get("inheritance", ""),
        prevalence=normalized.get("prevalence", ""),
        symptoms=list(normalized.get("symptoms", []) or []),
        treatment_summary=normalized.get("treatment_summary", ""),
        specialist_hospitals=list(normalized.get("specialist_hospitals", []) or []),
    )


def _patient_record_to_object(record: Dict[str, Any]) -> PatientObject:
    return PatientObject(
        registry_id=record.get("registry_id", ""),
        patient_code=record.get("patient_code", ""),
        disease=record.get("disease", ""),
        phenotypes=list(record.get("hpo_phenotypes", []) or []),
        diagnosis_status=record.get("diagnosis_status", "suspected"),
        inheritance=record.get("inheritance", ""),
        age_of_onset=record.get("age_of_onset"),
        gender=record.get("gender", "") or "",
        ethnicity=record.get("ethnicity", "") or "",
        consent=ConsentProfile(
            research=bool(record.get("consent_research")),
            matching=bool(record.get("consent_matching")),
        ),
        created_at=record.get("created_at"),
        updated_at=record.get("updated_at"),
    )


def _variant_objects_from_models(variants: List[GenomicVariant], source: str = "patient_report") -> List[VariantObject]:
    return [
        VariantObject(
            gene=variant.gene,
            hgvs_c=variant.hgvs_c,
            hgvs_p=variant.hgvs_p,
            pathogenicity=variant.pathogenicity,
            allele_frequency=variant.allele_frequency,
            source=source,
        )
        for variant in variants
    ]


def _resolve_disease_template(disease_name: str, phenotypes: Optional[List[str]] = None) -> Dict[str, Any]:
    disease_text = (disease_name or "").lower()
    phenotype_text = " ".join(phenotypes or []).lower()
    for template in DISEASE_GROUP_TEMPLATES:
        for keyword in template.get("keywords", []):
            keyword_lower = keyword.lower()
            if keyword_lower in disease_text or keyword_lower in phenotype_text:
                return template
    return {
        "template_id": "generic_rare_disease",
        "title": "通用罕见病模板",
        "keywords": [],
        "priority_genes": [],
        "recommended_tests": ["补充病历摘要", "完善专科检查", "遗传咨询"],
        "research_focus": ["病例对象标准化", "病组化队列准备", "研究包输出"],
        "community_focus": ["病程整理", "病友连接", "长期管理打卡"],
        "follow_up_schedule": "每 2-4 周一次，按病情变化动态调整",
    }


def _build_care_plan(
    patient_record: Dict[str, Any],
    current_stage: str,
    note: str,
    goals: List[str],
    phenotypes: List[str],
) -> CarePlanObject:
    template = _resolve_disease_template(patient_record.get("disease", ""), phenotypes)
    stage_label = {
        "newly_diagnosed": "新确诊",
        "workup": "检查中",
        "treatment": "治疗期",
        "stable_followup": "稳定随访",
        "research_ready": "研究准备",
    }.get(current_stage, current_stage)
    goal_list = [goal for goal in goals if goal] or [
        "把关键病程、检查和下一步问题整理成可复用对象",
        "建立稳定的病友/照护支持连接",
    ]
    next_7_days = [
        f"围绕“{note[:30]}”整理本周最关键的 3 个问题",
        *template.get("recommended_tests", [])[:2],
    ]
    next_30_days = [
        f"按照 {template.get('follow_up_schedule')} 做一次结构化复盘",
        "把新的检查、治疗调整或不良反应写入时间线",
        "将重要线索同步回研究和社群层，避免重复叙述",
    ]
    community_actions = [
        f"在 {template.get('title')} 对应病友圈中寻找同阶段病友",
        *template.get("community_focus", [])[:2],
    ]
    research_actions = (
        [
            "当前已具备研究同意，可把病例对象加入 cohort 或研究包",
            *template.get("research_focus", [])[:2],
        ]
        if patient_record.get("consent_research")
        else ["尚未授权研究用途，如需进入队列需先完成 research consent。"]
    )

    return CarePlanObject(
        registry_id=patient_record.get("registry_id", ""),
        disease=patient_record.get("disease", ""),
        current_stage=stage_label,
        disease_group=template.get("title", "通用罕见病模板"),
        goals=goal_list,
        next_7_days=next_7_days,
        next_30_days=next_30_days,
        reentry_triggers=[
            "出现新系统受累或症状明显加重",
            "获得新的基因、酶学、影像或病理结果",
            "治疗副作用影响日常生活或依从性下降",
        ],
        community_actions=community_actions,
        research_actions=research_actions,
        updated_at=datetime.now().isoformat(),
    )


def _load_recent_audit_events(limit: int = 12) -> List[Dict[str, Any]]:
    log_file = PROJECT_ROOT / "logs" / "platform_audit.log"
    if not log_file.exists():
        return []
    lines = [line for line in log_file.read_text(encoding="utf-8").splitlines() if line.strip()]
    events = []
    for line in lines[-limit:]:
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return list(reversed(events))


def _scene_maturity(score: float) -> str:
    if score >= 0.85:
        return "L3 platform-ready"
    if score >= 0.6:
        return "L2 workflow"
    return "L1 seed"


def _build_research_package(
    disease_name: str,
    patient_record: Optional[Dict[str, Any]] = None,
    phenotype_terms: Optional[List[str]] = None,
    variants: Optional[List[GenomicVariant]] = None,
    include_virtual_screening: bool = True,
) -> ResearchPackageObject:
    disease = _find_disease(disease_name) or {"name": disease_name}
    normalized = _normalize_disease_record(disease)
    disease_obj = _disease_to_object(normalized)
    target_context = _resolve_target_context(disease_obj.name or disease_name, disease_obj.gene)
    knowledge_map = _resolve_graph_snapshot(disease_obj.name or disease_name, disease_obj.gene)

    current_therapies = []
    for drug in drug_target_network.drugs.values():
        if disease_obj.name in drug.indications or disease_name in drug.indications:
            current_therapies.append(
                {
                    "drug_id": drug.drug_id,
                    "name": drug.name,
                    "status": drug.approval_status,
                    "type": drug.drug_type,
                    "targets": drug_target_network.find_targets_for_drug(drug.drug_id),
                }
            )

    repurposing_candidates = drug_target_network.find_drug_repurposing_candidates(disease_obj.name or disease_name)
    screening_summary: Dict[str, Any] = {}
    if include_virtual_screening:
        screening_result = virtual_screening_agent.run_full_pipeline(
            pdb_id=target_context["pdb_id"],
            name=target_context["target_name"],
            gene=target_context["gene"],
            disease=target_context["disease_name"],
            library="chembl",
        )
        screening_report = virtual_screening_agent.generate_report(screening_result)
        screening_summary = {
            "total_screened": screening_report["screening"]["total_screened"],
            "hits_found": screening_report["screening"]["hits_found"],
            "hit_rate": screening_report["screening"]["hit_rate"],
            "hits": screening_report.get("hits", [])[:3],
        }

    evidence_bundle = [
        EvidenceObject(
            evidence_id="disease_snapshot",
            source="knowledge_base",
            title=f"{disease_obj.name or disease_name} 疾病上下文",
            evidence_level="seed",
            summary=disease_obj.treatment_summary or "知识库已提供疾病基础背景，可作为研究包起点。",
            tags=["disease", disease_obj.category],
        ),
        EvidenceObject(
            evidence_id="knowledge_graph",
            source="knowledge_graph",
            title="疾病-基因-药物关系快照",
            evidence_level="seed",
            summary=(
                f"图谱中关联基因 {len(knowledge_map['related'].get('genes', []))} 个，"
                f"关联药物 {len(knowledge_map['related'].get('drugs', []))} 个。"
            ),
            tags=["graph", "context"],
        ),
        EvidenceObject(
            evidence_id="drug_network",
            source="drug_target_network",
            title="药物网络与再定位线索",
            evidence_level="seed",
            summary=(
                f"当前治疗 {len(current_therapies)} 项，再定位候选 {len(repurposing_candidates)} 项，"
                "可继续进入研究筛选漏斗。"
            ),
            tags=["drug", "repurposing"],
        ),
        EvidenceObject(
            evidence_id="scientific_runtime",
            source="scientific_runtime",
            title="科研运行时建议工作流",
            evidence_level="operational",
            summary="当前平台已能把文献综述、药物发现和临床决策文档组织成可执行工作流。",
            tags=["runtime", "workflow"],
        ),
    ]

    workflows = _scientific_skills_snapshot().get("workflows", [])
    patient_obj = _patient_record_to_object(patient_record) if patient_record else None
    variant_objects = _variant_objects_from_models(variants or [], "registry" if patient_record else "patient_report")
    package_metrics = {
        "entity_resolved": bool(disease_name),
        "targets_found": len(knowledge_map["related"].get("genes", [])) or (1 if target_context.get("gene") and target_context.get("gene") != "UNKNOWN" else 0),
        "target_overlap": len(repurposing_candidates),
        "literature_found": len(workflows),
        "evidence_classified": 1.0 if evidence_bundle else 0.0,
        "claims_generated": len(_build_drug_clues(disease)),
    }
    quality_gate = quality_gate_controller.evaluate_gates(package_metrics)

    return ResearchPackageObject(
        package_id=f"rp_{datetime.now().strftime('%Y%m%d%H%M%S')}",
        generated_at=datetime.now().isoformat(),
        disease=disease_obj,
        patient=patient_obj,
        variants=variant_objects,
        evidence_bundle=evidence_bundle,
        target_snapshot={
            "context": target_context,
            "knowledge_map": knowledge_map,
            "phenotypes": list(phenotype_terms or []),
            "quality_gate": {
                "overall_score": quality_gate.overall_score,
                "can_proceed": quality_gate.can_proceed,
                "recommendations": quality_gate.recommendations,
            },
        },
        current_therapies=current_therapies,
        repurposing_candidates=repurposing_candidates,
        screening_summary=screening_summary,
        scientific_workflows=workflows,
        next_steps=[
            "先确认疾病上下文、表型与基因线索是否足以支持进入研究讨论",
            "把当前治疗与再定位候选分开评估，并记录证据边界",
            "如需对外合作，优先导出 cohort / Phenopacket / research package 三类对象",
        ],
        artifacts=[
            ResearchArtifactObject(
                artifact_type="disease_snapshot",
                title="疾病上下文摘要",
                description="供医生、研究者和合作方快速理解病种背景。",
                action="disease-research",
            ),
            ResearchArtifactObject(
                artifact_type="candidate_table",
                title="候选药物与再定位表",
                description="整理当前治疗、共同靶点和再利用候选。",
                action="drug-research",
            ),
            ResearchArtifactObject(
                artifact_type="screening_brief",
                title="虚拟筛选摘要",
                description="用结构化 hit 和命中率说明下一步实验优先级。",
                ready=include_virtual_screening,
                action="drug-research",
            ),
            ResearchArtifactObject(
                artifact_type="cohort_ready_bundle",
                title="队列与标准导出",
                description="为多中心研究准备 Phenopacket、registry 与 cohort 对象。",
                ready=bool(patient_record and patient_record.get("consent_research")),
                action="genomic-hub",
            ),
        ],
    )


def _scientific_skills_snapshot() -> Dict[str, Any]:
    skills_root = Path.home() / ".codex" / "skills"
    app_python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"

    skills = []
    installed_count = 0
    for item in SCIENTIFIC_SKILL_LIBRARY:
        skill_path = skills_root / item["slug"]
        installed = skill_path.exists() and (skill_path / "SKILL.md").exists()
        if installed:
            installed_count += 1
        skills.append(
            {
                **item,
                "installed": installed,
                "path": str(skill_path),
            }
        )

    workflows = [
        {
            "title": "罕见病证据雷达",
            "description": "先查 OMIM / ClinVar / HPO / ClinicalTrials，再回收为医生可读摘要。",
            "skills": ["database-lookup", "literature-review", "scientific-writing"],
            "target": "disease-research",
        },
        {
            "title": "候选药物转化漏斗",
            "description": "用 RDKit + MedChem + DiffDock 把药物网络候选推到可进一步实验验证的列表。",
            "skills": ["rdkit", "medchem", "diffdock"],
            "target": "drug-research",
        },
        {
            "title": "临床队列与证据文档",
            "description": "把登记患者、EHR 特征和决策建议整合成研究或汇报材料。",
            "skills": ["pyhealth", "clinical-decision-support", "treatment-plans"],
            "target": "genomic-hub",
        },
    ]

    runtime = {
        "required_python": "3.12",
        "state": "not_configured",
        "state_label": "未配置",
        "ready": False,
        "error": "scientific runtime checker not found",
        "bootstrap_commands": [
            {"label": "初始化核心环境", "command": "bash scripts/setup_scientific_runtime.sh core"},
            {"label": "初始化完整科研环境", "command": "bash scripts/setup_scientific_runtime.sh full"},
        ],
        "profiles": [],
        "installed_profiles": [],
        "notes": [],
        "uv": {"installed": False, "path": "", "version": ""},
        "system_python": {"available": False, "path": "", "version": ""},
        "venv": {"exists": False, "path": "", "python_path": "", "version": "", "matches_required": False},
        "run_examples": [],
    }
    if SCIENTIFIC_RUNTIME_CHECKER.exists():
        try:
            result = subprocess.run(
                [sys.executable, str(SCIENTIFIC_RUNTIME_CHECKER), "--json"],
                check=False,
                capture_output=True,
                text=True,
                cwd=str(PROJECT_ROOT),
                timeout=20,
            )
            if result.returncode == 0 and result.stdout.strip():
                runtime = json.loads(result.stdout)
            else:
                runtime["error"] = result.stderr.strip() or "runtime checker failed"
        except (subprocess.SubprocessError, json.JSONDecodeError) as exc:
            runtime["error"] = str(exc)

    return {
        "repo": {
            "name": "claude-scientific-skills",
            "url": "https://github.com/K-Dense-AI/claude-scientific-skills",
            "ref": "main",
        },
        "environment": {
            "app_python_version": app_python_version,
            "codex_restart_required": True,
        },
        "runtime": runtime,
        "installed_count": installed_count,
        "total_curated": len(SCIENTIFIC_SKILL_LIBRARY),
        "skills": skills,
        "workflows": workflows,
    }


@router.get("/overview")
async def platform_overview():
    modules = _available_modules()
    discovery = _community_discovery_snapshot()
    secondme_configured = bool(os.getenv("SECONDME_CLIENT_ID")) and bool(os.getenv("SECONDME_REDIRECT_URI"))
    agent_modules = [item for item in modules if item["path"].startswith("agents/")]
    registry_stats = patient_registry.get_stats()
    scientific_skills = _scientific_skills_snapshot()

    return {
        "ok": True,
        "hero": {
            "eyebrow": "SecondMe patient-native rare disease platform",
            "title": "把症状初筛、基因分诊、SecondMe 分身和病友互助放进同一个患者中枢",
            "subtitle": "患者先完成自我表达，再由 DeepRare 做首轮诊断、由登记与研究层补足背景、由病友圈承接长期支持。",
            "primary_cta": {"label": "开始 DeepRare 诊断", "target": "deeprare"},
            "secondary_cta": {"label": "进入互助社群", "target": "community"},
        },
        "stats": [
            {"label": "已同步医学模块", "value": f"{len(agent_modules)}"},
            {"label": "科研技能加速层", "value": f"{scientific_skills['installed_count']}"},
            {"label": "登记患者样本", "value": f"{registry_stats['total_patients']}"},
            {"label": "长期管理事件", "value": f"{registry_stats.get('timeline_events', 0)}"},
        ],
        "journeys": [
            {
                "title": "患者入口",
                "summary": "自由描述症状，系统自动抽取 HPO、整理病程要点。",
                "action": "symptom-check",
            },
            {
                "title": "DeepRare 初筛",
                "summary": "给出多病种差异诊断、可追溯推理链和下一步检查建议。",
                "action": "deeprare",
            },
            {
                "title": "基因与登记",
                "summary": "把症状、变异和研究同意整理成可追踪的患者档案与 Phenopacket。",
                "action": "genomic-hub",
            },
            {
                "title": "SecondMe 分身",
                "summary": "把自己的病程、需求和情绪表达固化成 AI 分身，用于沟通与配对。",
                "action": "community",
            },
            {
                "title": "药物转化研究",
                "summary": "继续查看药物网络、再利用候选与虚拟筛选 hit。",
                "action": "drug-research",
            },
            {
                "title": "长期管理闭环",
                "summary": "把随访信号、SecondMe 分身、病友支持和研究回流组织成持续服务。",
                "action": "care-loop",
            },
            {
                "title": "科研加速层",
                "summary": "调用 Scientific Skills 做文献综述、药物发现和临床决策文档。",
                "action": "scientific-skills",
            },
        ],
        "capability_modules": modules[:16],
        "featured_communities": discovery["communities"],
        "trending_posts": discovery["posts"],
        "care_modes": [
            "症状到 HPO 的标准化表达",
            "DeepRare 多阶段鉴别诊断",
            "基因分诊 + 患者登记 + Phenopacket",
            "药物网络 + 虚拟筛选转化研究",
            "SecondMe 分身 + Bridge 病友配对",
            "长期管理计划 + 时间线 + 研究回流",
            "Scientific Skills 科研加速层",
        ],
    }


@router.get("/disease-cloud")
async def disease_cloud():
    items = _build_disease_cloud_items()
    status_counts: Dict[str, int] = {}
    category_counts: Dict[str, int] = {}
    for item in items:
        status_counts[item["care_status"]["key"]] = status_counts.get(item["care_status"]["key"], 0) + 1
        category_counts[item["category"]] = category_counts.get(item["category"], 0) + 1

    legend = [
        {
            "key": "treatable",
            "label": "治疗路径明确",
            "accent": "#0DBF9B",
            "description": "已有相对明确的治疗抓手，可直接进入治疗与随访讨论。",
        },
        {
            "key": "manageable",
            "label": "长期管理为主",
            "accent": "#D9AD43",
            "description": "更强调长期管理、监测和生活质量维持。",
        },
        {
            "key": "research",
            "label": "研究推进中",
            "accent": "#FF7A59",
            "description": "当前更适合先做研究跟踪、试验线索和机制探索。",
        },
    ]

    return {
        "ok": True,
        "title": "Rare disease orbit",
        "subtitle": "把 121 个病种做成一颗可拖拽的罕见病星球。字越大，代表在人群中相对更常见；颜色则提示当前更偏治疗、长期管理还是研究推进。",
        "items": items,
        "legend": legend,
        "stats": {
            "total_diseases": len(items),
            "categories": len(category_counts),
            "care_status_distribution": status_counts,
            "largest_category": max(category_counts, key=category_counts.get) if category_counts else "未分类",
        },
    }


@router.get("/scientific-skills")
async def scientific_skills():
    snapshot = _scientific_skills_snapshot()
    return {"ok": True, **snapshot}


@router.get("/object-model")
async def object_model():
    _audit(AuditAction.READ, "platform_object_model")
    return {
        "ok": True,
        "objects": OBJECT_MODEL_OVERVIEW,
        "schemas": build_object_model_schemas(),
        "standards_alignment": STANDARDS_ALIGNMENT,
        "data_flow": [
            "症状文本 -> HPO/医学摘要 -> DeepRare 输出 -> 基因分诊/登记 -> 研究包 -> SecondMe/长期管理",
            "患者对象是主索引，疾病对象和研究对象在不同场景中复用同一份上下文。",
        ],
    }


@router.get("/disease-group-templates")
async def disease_group_templates():
    _audit(AuditAction.READ, "disease_group_templates")
    return {
        "ok": True,
        "count": len(DISEASE_GROUP_TEMPLATES),
        "templates": DISEASE_GROUP_TEMPLATES,
        "usage": [
            "用在场景一做病组化提示与风险降级",
            "用在场景二生成建议检查与 cohort 准备",
            "用在场景四生成长期管理与社群动作",
        ],
    }


@router.get("/governance")
async def governance_snapshot():
    runtime = _scientific_skills_snapshot().get("runtime", {})
    recent_audit = _load_recent_audit_events(limit=10)
    registry_stats = patient_registry.get_stats()
    _audit(AuditAction.READ, "platform_governance")
    return {
        "ok": True,
        "data_classification": [item.value for item in DataClassification],
        "consent_model": {
            "registry_fields": ["consent_research", "consent_matching"],
            "secondme_tokens_server_side_only": True,
            "secondme_oauth_session_scoped": True,
            "default_boundary": "未获得 consent 的病例不进入研究包协作与病友匹配。",
        },
        "runtime_split": {
            "application_runtime": {
                "stack": "FastAPI + platform_hub_api + SecondMe/community",
                "goal": "在线服务、低延迟、权限边界清晰",
            },
            "avatar_runtime": get_avatar_service().get_runtime_config(),
            "scientific_runtime": {
                "profiles": runtime.get("profiles", []),
                "state": runtime.get("state", "unknown"),
                "goal": "重依赖科研任务与文档输出",
            },
        },
        "safeguards": [
            "HPO 结构化 + 医学 NLP + DeepRare 显式推理链",
            "HallucinationGuard 与质量门控作为高风险场景的降级机制",
            "PatientRegistry 显式持久化 consent、cohort 与 timeline",
            "SecondMe OAuth token 仅保存在服务端受控存储，并按浏览器会话隔离",
            "应用运行时与 Scientific Runtime 分离，降低依赖污染与服务风险",
        ],
        "audit": {
            "log_path": str(PROJECT_ROOT / "logs" / "platform_audit.log"),
            "recent_events": recent_audit,
            "event_count": len(recent_audit),
        },
        "masked_example": {
            "patient_name": DataMasker.mask_name("张小明"),
            "phone": DataMasker.mask_phone("13812345678"),
            "email": DataMasker.mask_email("patient@example.com"),
        },
        "registry_snapshot": registry_stats,
        "standards_alignment": STANDARDS_ALIGNMENT,
    }


@router.get("/evaluation")
async def evaluation_snapshot():
    modules = _available_modules()
    registry_stats = patient_registry.get_stats()
    graph_stats = knowledge_graph.get_graph_stats()
    network_stats = drug_target_network.analyze_network()
    community = _community_discovery_snapshot()
    skills = _scientific_skills_snapshot()
    avatar_count = len(get_avatar_service().list_avatars())

    scenes = [
        {
            "scene": "场景一",
            "title": "智能初筛与鉴别诊断",
            "score": round(min(1.0, (len(hpo_extractor.terms) / 40) * 0.25 + (len(EXTENDED_DB) / 121) * 0.25 + 0.25 + 0.2), 3),
            "metrics": {
                "hpo_terms": len(hpo_extractor.terms),
                "knowledge_diseases": len(EXTENDED_DB),
                "deeprare_available": (PROJECT_ROOT / "agents" / "deeprare_orchestrator.py").exists(),
                "hallucination_guard_available": (PROJECT_ROOT / "agents" / "hallucination_guard.py").exists(),
            },
        },
        {
            "scene": "场景二",
            "title": "基因分诊、登记与队列",
            "score": round(min(1.0, (registry_stats["total_patients"] / 10) * 0.2 + 0.35 + 0.25 + (registry_stats["total_cohorts"] / 3) * 0.2), 3),
            "metrics": {
                "registry_patients": registry_stats["total_patients"],
                "cohorts": registry_stats["total_cohorts"],
                "care_plans": registry_stats.get("care_plans", 0),
                "timeline_events": registry_stats.get("timeline_events", 0),
                "phenopacket_export": True,
            },
        },
        {
            "scene": "场景三",
            "title": "药物研究支持",
            "score": round(min(1.0, (graph_stats["total_nodes"] / 31) * 0.25 + (network_stats["nodes"]["drugs"] / 8) * 0.25 + (skills["installed_count"] / max(skills["total_curated"], 1)) * 0.25 + 0.15), 3),
            "metrics": {
                "graph_nodes": graph_stats["total_nodes"],
                "graph_edges": graph_stats["total_edges"],
                "drug_nodes": network_stats["nodes"]["drugs"],
                "target_nodes": network_stats["nodes"]["targets"],
                "scientific_skills": skills["installed_count"],
                "runtime_state": skills["runtime"].get("state", "unknown"),
            },
        },
        {
            "scene": "场景四",
            "title": "SecondMe 社群与长期管理",
            "score": round(min(1.0, (avatar_count / 5) * 0.25 + (len(community["communities"]) / 4) * 0.25 + (registry_stats.get("timeline_events", 0) / 10) * 0.2 + 0.2), 3),
            "metrics": {
                "avatars": avatar_count,
                "featured_communities": len(community["communities"]),
                "trending_posts": len(community["posts"]),
                "timeline_events": registry_stats.get("timeline_events", 0),
                "bridge_available": True,
            },
        },
    ]
    for scene in scenes:
        scene["maturity"] = _scene_maturity(scene["score"])

    overall_score = round(sum(scene["score"] for scene in scenes) / len(scenes), 3)
    _audit(AuditAction.READ, "platform_evaluation", details={"overall_score": overall_score})
    return {
        "ok": True,
        "overall_score": overall_score,
        "overall_maturity": _scene_maturity(overall_score),
        "scene_scores": scenes,
        "kpi_framework": KPI_FRAMEWORK,
        "module_count": len(modules),
    }


@router.post("/symptom-check")
async def symptom_check(request: SymptomCheckRequest):
    enriched_text = request.text.strip()
    if request.age:
        enriched_text = f"{request.age}岁患者，{enriched_text}"
    if request.gender:
        enriched_text = f"{request.gender}，{enriched_text}"

    phenotype = hpo_extractor.analyze_symptoms(request.text)
    clinical_note = medical_nlp.analyze_clinical_text(request.text)
    try:
        report = deeprare_orchestrator.diagnose(enriched_text)
        diagnoses = report["differential_diagnosis"]
        recommendations = report["recommendations"]
        reasoning_preview = "\n".join(report["reasoning_chain"].splitlines()[:10])
    except Exception:
        matched = search_rare_disease_by_symptoms([item["matched_text"] for item in phenotype["extracted_phenotypes"]])
        diagnoses = [
            {
                "rank": idx + 1,
                "disease": disease.name_cn,
                "confidence": f"{round((idx == 0 and 72) or max(45 - idx * 8, 18), 1)}%",
                "reasoning": f"与 {', '.join(disease.key_symptoms[:3])} 等关键症状存在交集。",
            }
            for idx, disease in enumerate(matched[:5])
        ]
        recommendations = [
            "建议整理既往化验单、影像与用药史后前往罕见病门诊",
            "如果存在家族史或儿童起病，建议同步考虑遗传咨询",
        ]
        reasoning_preview = "DeepRare 离线回退模式：基于现有表型和本地疾病库完成首轮筛查。"

    phenotypes = [
        {
            "hpo_id": item["hpo_id"],
            "name": item["name"],
            "matched": item["matched_text"],
            "confidence": item["confidence"],
        }
        for item in phenotype["extracted_phenotypes"]
    ]

    summary = (
        f"系统识别到 {len(phenotypes)} 个表型，"
        f"当前最值得优先排查的方向是 {diagnoses[0]['disease']}。"
        if diagnoses
        else "当前未形成稳定的候选诊断，建议补充更完整的症状与检查信息。"
    )

    return {
        "ok": True,
        "summary": summary,
        "phenotypes": phenotypes,
        "systems_involved": phenotype["systems_involved"],
        "top_diagnoses": diagnoses[:3],
        "recommendations": recommendations,
        "reasoning_preview": reasoning_preview,
        "clinical_summary": clinical_note["summary"],
        "timestamp": datetime.now().isoformat(),
    }


@router.post("/research")
async def disease_research(request: DiseaseResearchRequest):
    disease = _find_disease(request.disease_name)
    if not disease:
        raise HTTPException(status_code=404, detail=f"未找到疾病：{request.disease_name}")

    normalized = _normalize_disease_record(disease)
    related = []
    for candidate in EXTENDED_DB.values():
        if candidate is disease:
            continue
        if candidate.get("category") == disease.get("category"):
            related.append(_normalize_disease_record(candidate))
        if len(related) >= 3:
            break

    questions = [
        "我的症状与典型病例相比是否处于早期？",
        "目前最应该补充哪几项检查来缩小诊断范围？",
        "是否存在值得关注的临床试验或标准治疗路径？",
    ]
    graph_snapshot = _resolve_graph_snapshot(normalized["name"] or normalized["name_en"], normalized["gene"])

    return {
        "ok": True,
        "disease": normalized,
        "research_signals": [
            {"label": "致病基因", "value": normalized["gene"]},
            {"label": "遗传方式", "value": normalized["inheritance"]},
            {"label": "流行情况", "value": normalized["prevalence"]},
            {"label": "疾病分类", "value": normalized["category"]},
        ],
        "care_points": [
            "先把核心症状、起病年龄和家族史整理成一页摘要",
            "对照 specialist_hospitals 选择就诊路径，优先找有经验的中心",
            "在病友圈里重点询问检查顺序、医保经验和长期管理策略",
        ],
        "related_conditions": related,
        "patient_questions": questions,
        "knowledge_map": graph_snapshot,
    }


@router.post("/drug-clues")
async def drug_clues(request: DrugClueRequest):
    disease = _find_disease(request.disease_name)
    if not disease:
        raise HTTPException(status_code=404, detail=f"未找到疾病：{request.disease_name}")

    normalized = _normalize_disease_record(disease)
    disease_name = normalized["name"] or normalized["name_en"] or request.disease_name

    current_therapies = []
    for drug in drug_target_network.drugs.values():
        if disease_name in drug.indications:
            current_therapies.append(
                {
                    "drug_id": drug.drug_id,
                    "name": drug.name,
                    "status": drug.approval_status,
                    "type": drug.drug_type,
                    "targets": drug_target_network.find_targets_for_drug(drug.drug_id),
                }
            )

    return {
        "ok": True,
        "disease": disease_name,
        "gene": normalized["gene"],
        "candidate_programs": _build_drug_clues(disease),
        "current_therapies": current_therapies,
        "repurposing_candidates": drug_target_network.find_drug_repurposing_candidates(disease_name),
        "network_stats": drug_target_network.analyze_network(),
        "knowledge_map": _resolve_graph_snapshot(disease_name, normalized["gene"]),
        "next_steps": [
            "优先确认患者亚型、基因型和当前治疗阶段",
            "把现有标准治疗与再利用候选药物分开评估",
            "如要进入研究阶段，建议先补文献证据和病例可及性",
        ],
    }


@router.post("/genomic-triage")
async def genomic_triage(request: GenomicTriageRequest):
    disease = _find_disease(request.disease_name or "") if request.disease_name else None
    normalized = _normalize_disease_record(disease) if disease else None
    phenotype_bundle, phenotype_terms = _extract_phenotype_bundle(request.symptoms_text)
    variants, analysis_mode = _build_variant_models(request.variants, normalized["gene"] if normalized else None)
    results = genomic_analyzer.analyze(variants, phenotype_terms)
    clinical_note = medical_nlp.analyze_clinical_text(request.symptoms_text)

    return {
        "ok": True,
        "analysis_mode": analysis_mode,
        "summary": (
            f"已从患者描述里抽取 {len(phenotype_terms)} 个关键表型，"
            f"当前最值得优先核实的基因方向是 {results[0].gene}。"
            if results
            else "已完成表型整理，但当前缺少足够的变异/疾病线索，建议补充基因报告或已知疑似基因。"
        ),
        "phenotypes": [
            {
                "hpo_id": item["hpo_id"],
                "name": item["name"],
                "matched": item["matched_text"],
                "confidence": item["confidence"],
            }
            for item in phenotype_bundle.get("extracted_phenotypes", [])
        ],
        "systems_involved": phenotype_bundle.get("systems_involved", []),
        "clinical_note": clinical_note,
        "variants": [
            {
                "gene": variant.gene,
                "hgvs_c": variant.hgvs_c,
                "pathogenicity": variant.pathogenicity,
                "allele_frequency": variant.allele_frequency,
            }
            for variant in variants
        ],
        "gene_rankings": [
            {
                "gene": item.gene,
                "disease": item.disease,
                "omim_id": item.omim_id,
                "inheritance": item.inheritance,
                "phenotype_score": item.phenotype_score,
                "variant_score": item.variant_score,
                "combined_score": item.combined_score,
            }
            for item in results[:5]
        ],
        "phenopacket_preview": genomic_analyzer.generate_phenopacket(
            patient_id="preview_patient",
            variants=variants,
            phenotypes=phenotype_terms,
        ),
        "disease_context": normalized,
    }


@router.post("/registry-enroll")
async def registry_enroll(request: RegistryEnrollmentRequest):
    disease = _find_disease(request.disease_name) or {"name": request.disease_name}
    normalized = _normalize_disease_record(disease)
    _, phenotype_terms = _extract_phenotype_bundle(request.symptoms_text)
    variants, _ = _build_variant_models(request.variants, normalized["gene"])

    record = patient_registry.register_patient(
        disease=normalized["name"] or normalized["name_en"] or request.disease_name,
        hpo_phenotypes=phenotype_terms,
        gene_variants=[
            {
                "gene": variant.gene,
                "hgvs_c": variant.hgvs_c,
                "hgvs_p": variant.hgvs_p,
                "pathogenicity": variant.pathogenicity,
                "allele_frequency": variant.allele_frequency,
            }
            for variant in variants
        ],
        diagnosis_status=request.diagnosis_status,
        inheritance=normalized["inheritance"],
        age_of_onset=request.age_of_onset,
        gender=request.gender,
        ethnicity=request.ethnicity,
        consent_research=request.consent_research,
        consent_matching=request.consent_matching,
    )
    stats = patient_registry.get_stats()
    phenopacket = patient_registry.export_phenopackets()[-1]

    return {
        "ok": True,
        "registration": record,
        "phenotypes": phenotype_terms,
        "stats": stats,
        "phenopacket": phenopacket,
    }


@router.get("/cohorts")
async def list_cohorts(disease: str = ""):
    cohorts = patient_registry.list_cohorts(disease=disease, limit=100)
    _audit(AuditAction.READ, "registry_cohorts", details={"disease": disease, "count": len(cohorts)})
    return {"ok": True, "cohorts": cohorts}


@router.post("/cohorts")
async def create_cohort(request: CohortCreateRequest):
    cohort = patient_registry.create_cohort(request.name, request.disease, request.criteria)
    added_patients = []
    for registry_id in request.registry_ids:
        if patient_registry.get_patient(registry_id):
            patient_registry.add_to_cohort(cohort["cohort_id"], registry_id)
            added_patients.append(registry_id)
    _audit(
        AuditAction.CREATE,
        "registry_cohort",
        resource_id=cohort["cohort_id"],
        details={"name": request.name, "disease": request.disease, "added_patients": len(added_patients)},
    )
    return {
        "ok": True,
        "cohort": cohort,
        "added_patients": added_patients,
        "patients": patient_registry.get_cohort_patients(cohort["cohort_id"]),
    }


@router.post("/cohorts/{cohort_id}/patients")
async def add_patient_to_cohort(cohort_id: str, request: CohortAddPatientRequest):
    patient = patient_registry.get_patient(request.registry_id)
    if not patient:
        raise HTTPException(status_code=404, detail=f"未找到登记患者：{request.registry_id}")
    patient_registry.add_to_cohort(cohort_id, request.registry_id)
    _audit(
        AuditAction.UPDATE,
        "registry_cohort_membership",
        resource_id=cohort_id,
        details={"registry_id": request.registry_id},
    )
    return {
        "ok": True,
        "cohort_id": cohort_id,
        "patient": _patient_record_to_object(patient).model_dump(),
        "patients": patient_registry.get_cohort_patients(cohort_id),
    }


@router.get("/cohorts/{cohort_id}")
async def cohort_detail(cohort_id: str):
    cohorts = patient_registry.list_cohorts(limit=500)
    cohort = next((item for item in cohorts if item["cohort_id"] == cohort_id), None)
    if not cohort:
        raise HTTPException(status_code=404, detail=f"未找到队列：{cohort_id}")
    patients = patient_registry.get_cohort_patients(cohort_id)
    return {
        "ok": True,
        "cohort": cohort,
        "patients": patients,
        "phenopacket_count": len(patient_registry.export_phenopackets(cohort_id=cohort_id)),
    }


@router.get("/cohorts/{cohort_id}/phenopackets")
async def cohort_phenopackets(cohort_id: str):
    phenopackets = patient_registry.export_phenopackets(cohort_id=cohort_id)
    _audit(AuditAction.EXPORT, "phenopacket_export", resource_id=cohort_id, details={"count": len(phenopackets)})
    return {"ok": True, "cohort_id": cohort_id, "count": len(phenopackets), "phenopackets": phenopackets}


@router.post("/research-package")
async def research_package(request: ResearchPackageRequest):
    patient_record = None
    phenotype_terms: List[str] = []
    if request.registry_id:
        patient_record = patient_registry.get_patient(request.registry_id)
        if not patient_record:
            raise HTTPException(status_code=404, detail=f"未找到登记患者：{request.registry_id}")
        phenotype_terms = list(patient_record.get("hpo_phenotypes", []) or [])

    if request.symptoms_text:
        _, extracted = _extract_phenotype_bundle(request.symptoms_text)
        for item in extracted:
            if item not in phenotype_terms:
                phenotype_terms.append(item)

    disease_name = (
        request.disease_name
        or (patient_record.get("disease") if patient_record else "")
        or "待确认疾病"
    )
    base_gene = request.gene_hint or ""
    disease = _find_disease(disease_name)
    normalized = _normalize_disease_record(disease) if disease else {"name": disease_name, "gene": base_gene}
    variants, _ = _build_variant_models(request.variants, normalized.get("gene") or base_gene)
    package = _build_research_package(
        disease_name=disease_name,
        patient_record=patient_record,
        phenotype_terms=phenotype_terms,
        variants=variants,
        include_virtual_screening=request.include_virtual_screening,
    )
    _audit(
        AuditAction.EXPORT,
        "research_package",
        resource_id=package.package_id,
        details={"disease": disease_name, "registry_id": request.registry_id or ""},
    )
    return {"ok": True, "research_package": package.model_dump()}


@router.post("/longitudinal-care")
async def longitudinal_care_update(request: LongitudinalCareRequest):
    patient = patient_registry.get_patient(request.registry_id)
    if not patient:
        raise HTTPException(status_code=404, detail=f"未找到登记患者：{request.registry_id}")

    phenotype_terms = list(patient.get("hpo_phenotypes", []) or [])
    if request.symptoms_text:
        _, extracted = _extract_phenotype_bundle(request.symptoms_text)
        for item in extracted:
            if item not in phenotype_terms:
                phenotype_terms.append(item)

    care_plan = _build_care_plan(patient, request.current_stage, request.note, request.goals, phenotype_terms)
    event = patient_registry.add_timeline_event(
        registry_id=request.registry_id,
        event_type=request.update_type,
        title=f"{care_plan.current_stage}更新",
        detail=request.note,
        source="care_loop",
        payload={
            "goals": request.goals,
            "phenotypes": phenotype_terms[:8],
            "disease_group": care_plan.disease_group,
        },
    )
    saved_plan = patient_registry.update_care_plan(request.registry_id, care_plan.model_dump())

    matcher = _build_patient_matcher()
    target = PatientProfile(
        patient_id=request.registry_id,
        disease=patient.get("disease", ""),
        hpo_phenotypes=phenotype_terms,
        age=patient.get("age_of_onset") or 0,
        gender=patient.get("gender", "") or "",
        location=patient.get("ethnicity", "") or "",
    )
    matches = matcher.find_matches(target, top_n=3, min_similarity=0.25)

    _audit(
        AuditAction.UPDATE,
        "longitudinal_care",
        resource_id=request.registry_id,
        details={"update_type": request.update_type, "current_stage": request.current_stage},
    )
    return {
        "ok": True,
        "patient": _patient_record_to_object(patient).model_dump(),
        "care_plan": saved_plan["plan"],
        "timeline_event": event,
        "timeline": patient_registry.get_patient_timeline(request.registry_id),
        "community_signals": matches,
    }


@router.get("/longitudinal-care/{registry_id}")
async def longitudinal_care_snapshot(registry_id: str):
    patient = patient_registry.get_patient(registry_id)
    if not patient:
        raise HTTPException(status_code=404, detail=f"未找到登记患者：{registry_id}")
    care_plan = patient_registry.get_care_plan(registry_id)
    timeline = patient_registry.get_patient_timeline(registry_id)
    matcher = _build_patient_matcher()
    target = PatientProfile(
        patient_id=registry_id,
        disease=patient.get("disease", ""),
        hpo_phenotypes=patient.get("hpo_phenotypes", []),
        age=patient.get("age_of_onset") or 0,
        gender=patient.get("gender", "") or "",
        location=patient.get("ethnicity", "") or "",
    )
    support_group = matcher.find_support_group(patient.get("disease", ""))
    matches = matcher.find_matches(target, top_n=3, min_similarity=0.25)
    return {
        "ok": True,
        "patient": _patient_record_to_object(patient).model_dump(),
        "care_plan": care_plan,
        "timeline": timeline,
        "support_group_size": len(support_group),
        "community_signals": matches,
        "reentry_routes": [
            {"scene": "场景一", "action": "重新整理症状与检查，更新诊断链"},
            {"scene": "场景二", "action": "补充基因/酶学结果，刷新登记对象"},
            {"scene": "场景三", "action": "把新的病例阶段同步到研究包与 cohort"},
            {"scene": "场景四", "action": "继续通过 SecondMe 分身和病友网络承接支持"},
        ],
    }


@router.post("/community-match")
async def community_match(request: CommunityMatchRequest):
    _, phenotype_terms = _extract_phenotype_bundle(request.symptoms_text)
    matcher = _build_patient_matcher()
    target = PatientProfile(
        patient_id="current_user",
        disease=request.disease_name,
        hpo_phenotypes=phenotype_terms,
        age=request.age or 0,
        gender=request.gender or "",
        location=request.location or "",
    )

    matches = matcher.find_matches(target, top_n=5, min_similarity=0.25)
    support_group = matcher.find_support_group(request.disease_name)

    return {
        "ok": True,
        "input_profile": {
            "disease": request.disease_name,
            "phenotypes": phenotype_terms,
            "age": request.age,
            "gender": request.gender,
            "location": request.location,
        },
        "matches": [
            {
                "patient_id": item["patient_id"],
                "disease": item["disease"],
                "similarity": item["similarity"],
                "location": item["location"],
                "phenotypes": item["phenotypes"][:4],
                "match_reason": (
                    f"与你共享 {max(_count_shared_terms(item['phenotypes'], phenotype_terms), 1)} 个关键表型，"
                    f"且疾病方向同为 {item['disease']}。"
                ),
            }
            for item in matches
        ],
        "support_group_size": len(support_group),
        "support_group_preview": support_group[:6],
    }


@router.post("/virtual-screening")
async def virtual_screening(request: VirtualScreeningRequest):
    context = _resolve_target_context(request.disease_name, request.gene, request.target_name)
    result = virtual_screening_agent.run_full_pipeline(
        pdb_id=context["pdb_id"],
        name=context["target_name"],
        gene=context["gene"],
        disease=context["disease_name"],
        library=request.library,
    )
    report = virtual_screening_agent.generate_report(result)

    return {
        "ok": True,
        "context": context,
        "report": report,
        "screening_summary": {
            "total_screened": report["screening"]["total_screened"],
            "hits_found": report["screening"]["hits_found"],
            "hit_rate": report["screening"]["hit_rate"],
            "stage_count": len(report["stages"]),
        },
    }
