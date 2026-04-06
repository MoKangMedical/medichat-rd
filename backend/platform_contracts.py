"""
MediChat-RD 平台对象契约与模板配置。

把白皮书中反复提到的患者、疾病、变异、证据、研究包和社区对象
显式收敛成可序列化的数据模型，供聚合 API 与前端共用。
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ConsentProfile(BaseModel):
    research: bool = False
    matching: bool = False
    note_write: bool = False
    scopes: List[str] = Field(default_factory=list)


class PatientObject(BaseModel):
    registry_id: str
    patient_code: str = ""
    disease: str
    phenotypes: List[str] = Field(default_factory=list)
    diagnosis_status: str = "suspected"
    inheritance: str = ""
    age_of_onset: Optional[int] = None
    gender: str = ""
    ethnicity: str = ""
    consent: ConsentProfile = Field(default_factory=ConsentProfile)
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class DiseaseObject(BaseModel):
    name: str
    name_en: str = ""
    category: str = "未分类"
    gene: str = ""
    inheritance: str = ""
    prevalence: str = ""
    symptoms: List[str] = Field(default_factory=list)
    treatment_summary: str = ""
    specialist_hospitals: List[str] = Field(default_factory=list)


class VariantObject(BaseModel):
    gene: str
    hgvs_c: str = ""
    hgvs_p: str = ""
    pathogenicity: str = ""
    allele_frequency: float = 0.0
    source: str = "patient_report"


class EvidenceObject(BaseModel):
    evidence_id: str
    source: str
    title: str
    evidence_level: str
    summary: str
    url: str = ""
    tags: List[str] = Field(default_factory=list)
    generated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class ResearchArtifactObject(BaseModel):
    artifact_type: str
    title: str
    description: str
    ready: bool = True
    action: str = ""


class ResearchPackageObject(BaseModel):
    package_id: str
    generated_at: str
    disease: DiseaseObject
    patient: Optional[PatientObject] = None
    variants: List[VariantObject] = Field(default_factory=list)
    evidence_bundle: List[EvidenceObject] = Field(default_factory=list)
    target_snapshot: Dict[str, Any] = Field(default_factory=dict)
    current_therapies: List[Dict[str, Any]] = Field(default_factory=list)
    repurposing_candidates: List[Dict[str, Any]] = Field(default_factory=list)
    screening_summary: Dict[str, Any] = Field(default_factory=dict)
    scientific_workflows: List[Dict[str, Any]] = Field(default_factory=list)
    next_steps: List[str] = Field(default_factory=list)
    artifacts: List[ResearchArtifactObject] = Field(default_factory=list)


class CareTimelineEvent(BaseModel):
    event_id: str
    registry_id: str
    event_type: str
    title: str
    detail: str = ""
    source: str = "platform"
    created_at: str
    payload: Dict[str, Any] = Field(default_factory=dict)


class CarePlanObject(BaseModel):
    registry_id: str
    disease: str
    current_stage: str
    disease_group: str
    goals: List[str] = Field(default_factory=list)
    next_7_days: List[str] = Field(default_factory=list)
    next_30_days: List[str] = Field(default_factory=list)
    reentry_triggers: List[str] = Field(default_factory=list)
    community_actions: List[str] = Field(default_factory=list)
    research_actions: List[str] = Field(default_factory=list)
    updated_at: str


class CommunityAvatarObject(BaseModel):
    avatar_id: str
    nickname: str
    disease_type: str
    bio: str = ""
    communities: List[str] = Field(default_factory=list)
    current_need: str = ""


OBJECT_MODEL_OVERVIEW: List[Dict[str, Any]] = [
    {
        "slug": "patient",
        "title": "患者对象",
        "description": "贯穿症状初筛、基因分诊、登记入库、长期管理与社区互动的核心对象。",
        "fields": ["registry_id", "patient_code", "disease", "phenotypes", "diagnosis_status", "consent"],
    },
    {
        "slug": "disease",
        "title": "疾病对象",
        "description": "统一承载疾病名称、分类、致病基因、遗传方式、核心表型和治疗摘要。",
        "fields": ["name", "category", "gene", "inheritance", "symptoms", "treatment_summary"],
    },
    {
        "slug": "variant",
        "title": "变异对象",
        "description": "将报告中的变异线索对象化，便于联合排序、导出和审计。",
        "fields": ["gene", "hgvs_c", "hgvs_p", "pathogenicity", "allele_frequency"],
    },
    {
        "slug": "evidence",
        "title": "证据对象",
        "description": "把图谱、知识库、药物网络和 Scientific Runtime 产出统一整理成证据层。",
        "fields": ["source", "title", "evidence_level", "summary", "tags"],
    },
    {
        "slug": "research_package",
        "title": "研究包对象",
        "description": "面向研究机构和药企的结构化交付物，聚合疾病上下文、证据、候选与下一步动作。",
        "fields": ["disease", "patient", "evidence_bundle", "repurposing_candidates", "screening_summary", "artifacts"],
    },
    {
        "slug": "community_avatar",
        "title": "社区分身对象",
        "description": "SecondMe 分身在平台中的稳定表示，用于病友匹配、Bridge 和长期管理回流。",
        "fields": ["avatar_id", "nickname", "disease_type", "communities", "current_need"],
    },
    {
        "slug": "care_plan",
        "title": "长期管理对象",
        "description": "把随访事件、下一步动作、复诊触发条件和社区/研究回流收敛成闭环对象。",
        "fields": ["registry_id", "current_stage", "goals", "next_7_days", "next_30_days", "reentry_triggers"],
    },
]


DISEASE_GROUP_TEMPLATES: List[Dict[str, Any]] = [
    {
        "template_id": "neuromuscular",
        "title": "神经肌肉病组模板",
        "keywords": ["重症肌无力", "肌无力", "SMA", "肌营养不良", "神经肌肉"],
        "priority_genes": ["CHRNE", "SMN1", "DMD", "RYR1"],
        "recommended_tests": ["肌电图", "肌酶谱", "抗体检测", "遗传咨询"],
        "research_focus": ["神经肌肉接头", "运动功能量表", "长期随访"],
        "community_focus": ["疲劳管理", "吞咽与呼吸支持", "康复训练"],
        "follow_up_schedule": "新确诊 2 周一次，稳定后 1-3 个月一次",
    },
    {
        "template_id": "lysosomal_storage",
        "title": "溶酶体贮积病模板",
        "keywords": ["戈谢病", "法布雷病", "尼曼匹克", "溶酶体"],
        "priority_genes": ["GBA1", "GLA", "SMPD1", "NPC1"],
        "recommended_tests": ["酶活性检测", "肝脾超声", "肾功能", "心脏评估"],
        "research_focus": ["酶替代治疗", "底物减少治疗", "器官受累分层"],
        "community_focus": ["长期输注管理", "疼痛管理", "医保与转诊路径"],
        "follow_up_schedule": "治疗期每月复盘，稳定后每季度复盘",
    },
    {
        "template_id": "bone_connective_tissue",
        "title": "骨与结缔组织病组模板",
        "keywords": ["成骨不全", "反复骨折", "蓝巩膜", "结缔组织"],
        "priority_genes": ["COL1A1", "COL1A2", "P3H1"],
        "recommended_tests": ["骨密度", "骨代谢指标", "遗传检测", "康复评估"],
        "research_focus": ["骨折频次", "功能结局", "辅助器具依从性"],
        "community_focus": ["家庭照护", "康复打卡", "青少年心理支持"],
        "follow_up_schedule": "骨折后即时记录，常规每 1-2 个月复盘",
    },
    {
        "template_id": "hematology_metabolism",
        "title": "血液与代谢病组模板",
        "keywords": ["贫血", "血友病", "代谢病", "肝脾肿大"],
        "priority_genes": ["F8", "F9", "HBB", "GBA1"],
        "recommended_tests": ["血常规", "凝血功能", "代谢谱", "酶学检测"],
        "research_focus": ["真实世界治疗响应", "并发症预警", "多中心队列"],
        "community_focus": ["输血/止血经验", "就诊准备", "家族筛查沟通"],
        "follow_up_schedule": "风险高时按事件驱动，常规每月复盘",
    },
]


STANDARDS_ALIGNMENT: List[Dict[str, str]] = [
    {"standard": "HPO", "scope": "症状与表型", "status": "已采用", "implementation": "HPO 提取与中文词表映射"},
    {"standard": "Phenopacket", "scope": "病例交换", "status": "已采用", "implementation": "基因分诊与登记导出"},
    {"standard": "OMIM / Orphanet", "scope": "疾病知识", "status": "部分采用", "implementation": "知识检索与幻觉防护"},
    {"standard": "SecondMe OAuth / MCP", "scope": "长期管理与开放集成", "status": "已采用", "implementation": "服务端 OAuth + MCP 适配层"},
    {"standard": "Runtime Split", "scope": "运行时治理", "status": "已采用", "implementation": "应用运行时与 Scientific Runtime 分离"},
]


KPI_FRAMEWORK: List[Dict[str, Any]] = [
    {
        "scene": "场景一",
        "title": "智能初筛与鉴别诊断",
        "kpis": ["表型提取覆盖度", "候选病种排序质量", "建议检查可执行性", "安全降级率"],
    },
    {
        "scene": "场景二",
        "title": "基因分诊、登记与队列",
        "kpis": ["联合排序稳定性", "Phenopacket 完整度", "登记转化率", "cohort 可复用性"],
    },
    {
        "scene": "场景三",
        "title": "药物研究支持",
        "kpis": ["疾病上下文快照质量", "再定位候选解释性", "筛选漏斗命中率", "研究包复用度"],
    },
    {
        "scene": "场景四",
        "title": "SecondMe 社群与长期管理",
        "kpis": ["分身激活率", "病友匹配质量", "长期管理回流率", "真实互动留存"],
    },
]


def build_object_model_schemas() -> Dict[str, Dict[str, Any]]:
    return {
        "consent": ConsentProfile.model_json_schema(),
        "patient": PatientObject.model_json_schema(),
        "disease": DiseaseObject.model_json_schema(),
        "variant": VariantObject.model_json_schema(),
        "evidence": EvidenceObject.model_json_schema(),
        "research_package": ResearchPackageObject.model_json_schema(),
        "care_timeline_event": CareTimelineEvent.model_json_schema(),
        "care_plan": CarePlanObject.model_json_schema(),
        "community_avatar": CommunityAvatarObject.model_json_schema(),
    }
