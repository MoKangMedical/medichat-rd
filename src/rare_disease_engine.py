"""
MediChat-RD — 罕见病诊断引擎
基于HPO表型分析 + 知识图谱推理的罕见病智能诊断系统
"""

import logging
import json
import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


class ConfidenceLevel(str, Enum):
    """诊断置信度等级"""
    HIGH = "high"           # ≥0.8
    MODERATE = "moderate"   # 0.5-0.8
    LOW = "low"             # 0.2-0.5
    SPECULATIVE = "speculative"  # <0.2


class DiagnosticStatus(str, Enum):
    """诊断流程状态"""
    INITIATED = "initiated"
    PHENOTYPE_EXTRACTING = "phenotype_extracting"
    KNOWLEDGE_RETRIEVING = "knowledge_retrieving"
    REASONING = "reasoning"
    VALIDATING = "validating"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class HPOAnnotation:
    """HPO表型注释"""
    hpo_id: str
    term: str
    frequency: str = "typical"  # very_frequent, frequent, occasional, very_rare
    onset: Optional[str] = None
    severity: str = "moderate"
    evidence_code: str = "IEA"  # IEA, PCS, TAS


@dataclass
class DiseaseCandidate:
    """疾病候选结果"""
    disease_id: str
    name: str
    omim_id: Optional[str]
    orphanet_id: Optional[str]
    score: float
    matched_phenotypes: list[str]
    missing_phenotypes: list[str]
    key_evidence: list[str]
    confidence: ConfidenceLevel
    inheritance_pattern: Optional[str] = None
    prevalence: Optional[str] = None
    gene_associations: list[str] = field(default_factory=list)


@dataclass
class DiagnosticReport:
    """诊断报告"""
    session_id: str
    status: DiagnosticStatus
    patient_phenotypes: list[HPOAnnotation]
    candidates: list[DiseaseCandidate]
    reasoning_chain: list[dict]
    recommendations: list[str]
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    confidence_summary: str = ""


class PhenotypeExtractor:
    """从临床描述中提取HPO表型"""

    # 常见临床术语到HPO映射
    TERM_MAP = {
        "发育迟缓": ("HP:0001263", "Global developmental delay"),
        "智力障碍": ("HP:0001249", "Intellectual disability"),
        "肌张力低下": ("HP:0001252", "Hypotonia"),
        "癫痫": ("HP:0001250", "Seizures"),
        "小头畸形": ("HP:0000252", "Microcephaly"),
        "大头畸形": ("HP:0000256", "Macrocephaly"),
        "身材矮小": ("HP:0004322", "Short stature"),
        "心脏缺陷": ("HP:0001626", "Cardiac anomaly"),
        "肝脏肿大": ("HP:0002240", "Hepatomegaly"),
        "脾脏肿大": ("HP:0001744", "Splenomegaly"),
        "面部畸形": ("HP:0000271", "Abnormal facial appearance"),
        "眼异常": ("HP:0000478", "Abnormality of the eye"),
        "听力损失": ("HP:0000365", "Hearing impairment"),
        "骨骼异常": ("HP:0000924", "Abnormality of the skeletal system"),
        "皮肤异常": ("HP:0000951", "Abnormality of the skin"),
        "肾脏异常": ("HP:0000077", "Abnormality of the kidney"),
        "免疫缺陷": ("HP:0002721", "Immunodeficiency"),
        "贫血": ("HP:0001903", "Anemia"),
        "血小板减少": ("HP:0001873", "Thrombocytopenia"),
        "代谢性酸中毒": ("HP:0001942", "Metabolic acidosis",
        "共济失调": ("HP:0001251", "Ataxia"),
        "肌无力": ("HP:0001324", "Muscle weakness"),
        "呼吸困难": ("HP:0002093", "Dyspnea"),
        "喂养困难": ("HP:0011968", "Feeding difficulties"),
        "生长迟缓": ("HP:0001510", "Growth delay"),
        "关节挛缩": ("HP:0001376", "Contractures"),
        "脊柱侧弯": ("HP:0002650", "Scoliosis"),
        "白内障": ("HP:0000518", "Cataract"),
        "视网膜病变": ("HP:0000488", "Retinopathy"),
        "耳聋": ("HP:0000365", "Deafness"),
        "多指": ("HP:0010442", "Polydactyly"),
        "并指": ("HP:0001159", "Syndactyly"),
        "唇裂": ("HP:0000202", "Cleft lip"),
        "腭裂": ("HP:0000175", "Cleft palate"),
        "隐睾": ("HP:0000028", "Cryptorchidism"),
        "性腺发育不全": ("HP:0000133", "Gonadal dysgenesis"),
        "多毛症": ("HP:0000998", "Hypertrichosis"),
        "色素沉着异常": ("HP:0001000", "Abnormality of skin pigmentation"),
        "牙异常": ("HP:0000164", "Abnormality of the teeth"),
        "指甲异常": ("HP:0001597", "Abnormality of the nails"),
        "语言发育迟缓": ("HP:0000750", "Delayed speech and language development"),
        "行为异常": ("HP:0000708", "Behavioral abnormality"),
        "自闭症": ("HP:0000717", "Autism"),
        "多动症": ("HP:0007018", "Attention deficit hyperactivity disorder"),
        "焦虑": ("HP:0000739", "Anxiety"),
        "抑郁": ("HP:0000716", "Depression"),
        "睡眠障碍": ("HP:0002360", "Sleep disturbance"),
        "肥胖": ("HP:0001513", "Obesity"),
        "消瘦": ("HP:0001507", "Wasting"),
        "淋巴水肿": ("HP:0001004", "Lymphedema"),
        "血管瘤": ("HP:0001028", "Hemangioma"),
    }

    def extract(self, clinical_text: str) -> list[HPOAnnotation]:
        """从临床文本中提取HPO表型"""
        annotations = []
        seen = set()

        for term, (hpo_id, hpo_term) in self.TERM_MAP.items():
            if term in clinical_text and hpo_id not in seen:
                seen.add(hpo_id)
                annotations.append(HPOAnnotation(
                    hpo_id=hpo_id,
                    term=hpo_term,
                    frequency=self._estimate_frequency(clinical_text, term),
                    evidence_code="IEA",
                ))

        return annotations

    def _estimate_frequency(self, text: str, term: str) -> str:
        """根据上下文估计表型频率"""
        context_window = 50
        idx = text.find(term)
        if idx < 0:
            return "typical"
        start = max(0, idx - context_window)
        end = min(len(text), idx + len(term) + context_window)
        context = text[start:end]

        if any(w in context for w in ["常见", "主要", "核心", "典型"]):
            return "very_frequent"
        if any(w in context for w in ["偶见", "有时", "部分"]):
            return "occasional"
        if any(w in context for w in ["罕见", "极少", "少数"]):
            return "very_rare"
        return "frequent"


class KnowledgeGraphRetriever:
    """罕见病知识图谱检索"""

    def __init__(self, data_path: Optional[str] = None):
        self.data_path = data_path or os.path.join(DATA_DIR, "rare-diseases.json")
        self.diseases: list[dict] = []
        self._load()

    def _load(self):
        """加载罕见病数据库"""
        try:
            with open(self.data_path, "r", encoding="utf-8") as f:
                self.diseases = json.load(f)
            logger.info(f"加载了 {len(self.diseases)} 种罕见病数据")
        except FileNotFoundError:
            logger.warning(f"罕见病数据文件不存在: {self.data_path}，使用内置数据")
            self.diseases = self._builtin_diseases()

    def _builtin_diseases(self) -> list[dict]:
        """内置核心罕见病数据（兜底）"""
        return [
            {
                "id": "RD001", "name": "脊髓性肌萎缩症",
                "omim": "253300", "orphanet": "ORPHA:70",
                "hpo": ["HP:0001252", "HP:0001324", "HP:0001263"],
                "inheritance": "autosomal_recessive", "gene": "SMN1",
                "prevalence": "1/10000",
            },
            {
                "id": "RD002", "name": "杜氏肌营养不良",
                "omim": "310200", "orphanet": "ORPHA:98896",
                "hpo": ["HP:0001324", "HP:0003701", "HP:0001252"],
                "inheritance": "x_linked", "gene": "DMD",
                "prevalence": "1/5000",
            },
        ]

    def search_by_phenotypes(
        self, phenotypes: list[HPOAnnotation], top_k: int = 10
    ) -> list[dict]:
        """根据表型组合检索匹配疾病"""
        query_hpo = {p.hpo_id for p in phenotypes}
        scored = []

        for disease in self.diseases:
            disease_hpo = set(disease.get("hpo", []))
            if not disease_hpo:
                continue

            overlap = query_hpo & disease_hpo
            if not overlap:
                continue

            # 加权Jaccard相似度
            union = query_hpo | disease_hpo
            jaccard = len(overlap) / len(union)

            # 频率加权
            freq_bonus = sum(
                self._freq_weight(p.frequency)
                for p in phenotypes if p.hpo_id in overlap
            ) / max(len(overlap), 1)

            score = 0.7 * jaccard + 0.3 * freq_bonus

            scored.append({
                **disease,
                "score": round(score, 4),
                "matched": list(overlap),
                "missing": list(disease_hpo - query_hpo),
            })

        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:top_k]

    @staticmethod
    def _freq_weight(freq: str) -> float:
        return {
            "very_frequent": 1.0,
            "frequent": 0.8,
            "typical": 0.6,
            "occasional": 0.4,
            "very_rare": 0.2,
        }.get(freq, 0.5)


class RareDiseaseDiagnosticEngine:
    """
    罕见病诊断引擎主类

    流程：
    1. 表型提取 — 从临床文本提取HPO注释
    2. 知识检索 — 在罕见病知识图谱中检索候选
    3. 推理排序 — 多维度评分排序候选疾病
    4. 验证生成 — 生成诊断报告和建议
    """

    def __init__(self, data_path: Optional[str] = None):
        self.extractor = PhenotypeExtractor()
        self.retriever = KnowledgeGraphRetriever(data_path)
        logger.info("罕见病诊断引擎初始化完成")

    def diagnose(
        self,
        clinical_text: str,
        session_id: Optional[str] = None,
        top_k: int = 5,
    ) -> DiagnosticReport:
        """执行完整的罕见病诊断流程"""
        import uuid
        session_id = session_id or str(uuid.uuid4())[:8]
        reasoning = []

        # Step 1: 表型提取
        reasoning.append({
            "step": 1,
            "action": "phenotype_extraction",
            "description": "从临床描述中提取HPO表型",
        })
        phenotypes = self.extractor.extract(clinical_text)
        reasoning[-1]["result"] = f"提取到 {len(phenotypes)} 个表型"

        if not phenotypes:
            return DiagnosticReport(
                session_id=session_id,
                status=DiagnosticStatus.FAILED,
                patient_phenotypes=[],
                candidates=[],
                reasoning_chain=reasoning,
                recommendations=["未能从描述中识别出HPO表型，请提供更详细的临床信息"],
            )

        # Step 2: 知识检索
        reasoning.append({
            "step": 2,
            "action": "knowledge_retrieval",
            "description": "在罕见病知识图谱中检索候选",
        })
        raw_candidates = self.retriever.search_by_phenotypes(phenotypes, top_k=top_k * 2)
        reasoning[-1]["result"] = f"检索到 {len(raw_candidates)} 个候选疾病"

        # Step 3: 推理排序
        reasoning.append({
            "step": 3,
            "action": "reasoning_ranking",
            "description": "多维度评分并排序候选",
        })
        candidates = self._rank_candidates(raw_candidates, phenotypes)
        reasoning[-1]["result"] = f"排序完成，Top候选: {candidates[0].name if candidates else '无'}"

        # Step 4: 验证与报告
        reasoning.append({
            "step": 4,
            "action": "report_generation",
            "description": "生成诊断报告和建议",
        })
        recommendations = self._generate_recommendations(candidates, phenotypes)
        confidence_summary = self._summarize_confidence(candidates)

        return DiagnosticReport(
            session_id=session_id,
            status=DiagnosticStatus.COMPLETED,
            patient_phenotypes=phenotypes,
            candidates=candidates[:top_k],
            reasoning_chain=reasoning,
            recommendations=recommendations,
            confidence_summary=confidence_summary,
        )

    def _rank_candidates(
        self, raw: list[dict], phenotypes: list[HPOAnnotation]
    ) -> list[DiseaseCandidate]:
        """将原始候选转为结构化结果并排序"""
        candidates = []
        for item in raw:
            score = item["score"]
            conf = self._score_to_confidence(score)

            candidates.append(DiseaseCandidate(
                disease_id=item["id"],
                name=item["name"],
                omim_id=item.get("omim"),
                orphanet_id=item.get("orphanet"),
                score=score,
                matched_phenotypes=item.get("matched", []),
                missing_phenotypes=item.get("missing", []),
                key_evidence=[],
                confidence=conf,
                inheritance_pattern=item.get("inheritance"),
                prevalence=item.get("prevalence"),
                gene_associations=[item.get("gene", "")] if item.get("gene") else [],
            ))

        candidates.sort(key=lambda c: c.score, reverse=True)
        return candidates

    @staticmethod
    def _score_to_confidence(score: float) -> ConfidenceLevel:
        if score >= 0.8:
            return ConfidenceLevel.HIGH
        if score >= 0.5:
            return ConfidenceLevel.MODERATE
        if score >= 0.2:
            return ConfidenceLevel.LOW
        return ConfidenceLevel.SPECULATIVE

    def _generate_recommendations(
        self, candidates: list[DiseaseCandidate], phenotypes: list[HPOAnnotation]
    ) -> list[str]:
        """生成诊断建议"""
        recs = []

        if not candidates:
            recs.append("未找到匹配的罕见病，建议扩大检索范围或补充更多表型信息")
            return recs

        top = candidates[0]
        if top.confidence == ConfidenceLevel.HIGH:
            recs.append(f"高度怀疑 {top.name}（{top.omim_id or 'N/A'}），建议进行基因检测确认")
        elif top.confidence == ConfidenceLevel.MODERATE:
            recs.append(f"可能为 {top.name}，建议结合基因检测和影像学检查")
        else:
            recs.append(f"低置信度候选 {top.name}，建议进一步专科评估")

        if top.gene_associations:
            recs.append(f"相关基因: {', '.join(top.gene_associations)}，建议针对性基因检测")

        if len(candidates) > 1:
            others = ", ".join(c.name for c in candidates[1:3])
            recs.append(f"鉴别诊断需排除: {others}")

        missing = len(top.missing_phenotypes)
        if missing > 0:
            recs.append(f"候选疾病预期的 {missing} 个表型未在描述中发现，建议针对性检查")

        recs.append("罕见病诊断需要多学科团队（MDT）会诊确认")
        return recs

    @staticmethod
    def _summarize_confidence(candidates: list[DiseaseCandidate]) -> str:
        if not candidates:
            return "无匹配候选"
        top = candidates[0]
        parts = [f"首选: {top.name} (置信度: {top.confidence.value}, 评分: {top.score:.2f})"]
        if len(candidates) > 1:
            parts.append(f"次选: {candidates[1].name} (评分: {candidates[1].score:.2f})")
        return " | ".join(parts)
