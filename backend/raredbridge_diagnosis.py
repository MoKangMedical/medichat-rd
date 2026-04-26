"""
RareDBridge Dx - traceable rare disease differential diagnosis.

This module implements our own lightweight capability inspired by the
DeepRare paper/product pattern: heterogeneous clinical input, phenotype
normalization, ranked hypotheses, self-check, and traceable evidence.
It does not depend on DeepRare code, data, or model weights.
"""

from __future__ import annotations

import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

try:
    from agents.rare_disease_agent import RARE_DISEASES_DB
except ImportError:
    from rare_disease_agent import RARE_DISEASES_DB


HPO_SEED_TERMS = {
    "肌无力": {"hpo_id": "HP:0001324", "term": "Muscle weakness"},
    "进行性肌无力": {"hpo_id": "HP:0003323", "term": "Progressive muscle weakness"},
    "吞咽困难": {"hpo_id": "HP:0002015", "term": "Dysphagia"},
    "呼吸困难": {"hpo_id": "HP:0002094", "term": "Dyspnea"},
    "运动发育迟缓": {"hpo_id": "HP:0001270", "term": "Motor delay"},
    "发育迟缓": {"hpo_id": "HP:0001263", "term": "Global developmental delay"},
    "生长迟缓": {"hpo_id": "HP:0001510", "term": "Growth delay"},
    "脾脏肿大": {"hpo_id": "HP:0001744", "term": "Splenomegaly"},
    "肝脏肿大": {"hpo_id": "HP:0002240", "term": "Hepatomegaly"},
    "骨痛": {"hpo_id": "HP:0002653", "term": "Bone pain"},
    "贫血": {"hpo_id": "HP:0001903", "term": "Anemia"},
    "血小板减少": {"hpo_id": "HP:0001873", "term": "Thrombocytopenia"},
    "蛋白尿": {"hpo_id": "HP:0000093", "term": "Proteinuria"},
    "心脏病变": {"hpo_id": "HP:0001627", "term": "Abnormal heart morphology"},
    "心脏肥大": {"hpo_id": "HP:0001640", "term": "Cardiomegaly"},
    "心肌病变": {"hpo_id": "HP:0001638", "term": "Cardiomyopathy"},
    "腓肠肌假性肥大": {"hpo_id": "HP:0003707", "term": "Calf muscle pseudohypertrophy"},
    "腓肠肌肥大": {"hpo_id": "HP:0003707", "term": "Calf muscle pseudohypertrophy"},
    "Gowers征": {"hpo_id": "HP:0003391", "term": "Gowers sign"},
    "CK升高": {"hpo_id": "HP:0003236", "term": "Elevated serum creatine kinase"},
    "癫痫": {"hpo_id": "HP:0001250", "term": "Seizure"},
    "抽搐": {"hpo_id": "HP:0001250", "term": "Seizure"},
    "智力障碍": {"hpo_id": "HP:0001249", "term": "Intellectual disability"},
    "认知障碍": {"hpo_id": "HP:0100543", "term": "Cognitive impairment"},
    "步态异常": {"hpo_id": "HP:0001288", "term": "Gait disturbance"},
    "共济失调": {"hpo_id": "HP:0001251", "term": "Ataxia"},
    "视力下降": {"hpo_id": "HP:0000505", "term": "Visual impairment"},
    "听力下降": {"hpo_id": "HP:0000365", "term": "Hearing impairment"},
    "皮疹": {"hpo_id": "HP:0000988", "term": "Skin rash"},
    "少汗": {"hpo_id": "HP:0000970", "term": "Hypohidrosis"},
    "皮肤血管角质瘤": {"hpo_id": "HP:0001071", "term": "Angiokeratoma"},
    "角膜混浊": {"hpo_id": "HP:0007957", "term": "Corneal opacity"},
    "K-F环": {"hpo_id": "HP:0200087", "term": "Kayser-Fleischer ring"},
    "肝功能异常": {"hpo_id": "HP:0002910", "term": "Elevated hepatic transaminase"},
    "神经精神症状": {"hpo_id": "HP:0000708", "term": "Behavioral abnormality"},
    "面部血管纤维瘤": {"hpo_id": "HP:0009724", "term": "Facial angiofibromas"},
    "肾血管平滑肌脂肪瘤": {"hpo_id": "HP:0006772", "term": "Renal angiomyolipoma"},
}

DEEPRARE_METHOD_FRAMEWORK = {
    "source": {
        "title": "An agentic system for rare disease diagnosis with traceable reasoning",
        "doi": "10.1038/s41586-025-10097-9",
        "github": "https://github.com/MAGIC-AI4Med/DeepRare",
        "local_pdf": "/Users/linzhang/Downloads/罕见病-An agentic system for rare disease diagnosis with traceable reasoning.pdf",
        "role": "Methodology reference. RareDBridge implements its own platform module and does not copy DeepRare code, data, weights, or performance claims.",
    },
    "github_implementation_reference": {
        "repository": "MAGIC-AI4Med/DeepRare",
        "description": "Code implementation of DeepRare (Nature 2026).",
        "observed_modules": [
            "hpo_extractor.py for free-text phenotype preprocessing",
            "diagnosis.py for HPO-based diagnosis workflow",
            "diagnosisGene.py for HPO plus gene/genotype workflow",
            "tools/ for specialized retrieval and analysis tools",
            "api/interface.py for LLM provider abstraction",
            "inference.sh, inference_gene.sh and extract_hpo.sh for runnable pipelines",
        ],
        "web_engineering_reference": [
            "FastAPI workflow packaging",
            "central host backed by a local DeepSeek-V3 deployment in the reference implementation",
            "Redis session management",
            "SQL persistent storage",
            "Exomiser integration for gene/VCF-oriented analysis",
        ],
        "raredbridge_adaptation_policy": [
            "Use the repository to map functional modules and deployment patterns.",
            "Do not vendor, copy, or depend on DeepRare source code in this platform.",
            "Implement RareDBridge Dx as a separate A2A-native capability using our own local disease DB and APIs.",
        ],
    },
    "problem_formulation": {
        "input_modalities": [
            "free_text_clinical_description",
            "structured_hpo_terms",
            "gene_or_variant_summary",
            "future_raw_vcf_or_lab_files",
        ],
        "output_objects": [
            "ranked_differential_diagnoses",
            "evidence_grounded_reasoning_chain",
            "self_reflection_gaps",
            "clinician_review_report",
        ],
    },
    "three_tier_architecture": [
        {
            "tier": "central_host_with_memory",
            "paper_role": "Coordinate diagnostic workflow, synthesize evidence, generate and re-check hypotheses.",
            "raredbridge_mapping": "A2A orchestrator plus RareDBridge Dx report builder and session artifacts.",
            "status": "implemented",
        },
        {
            "tier": "specialized_agent_servers",
            "paper_role": "Run phenotype, genotype, retrieval, case search and normalization tools.",
            "raredbridge_mapping": "Diagnosis Agent, phenotype Agent, evidence Agent, trial Agent and planned external tool adapters.",
            "status": "partially_implemented",
        },
        {
            "tier": "external_evidence_environment",
            "paper_role": "Use medical literature, rare disease knowledge bases, similar cases and genetic variant resources.",
            "raredbridge_mapping": "Local rare disease DB, HPO seed table, OMIM/PubMed/Orphanet links, MCP evidence APIs and future case-bank/VCF integrations.",
            "status": "partially_implemented",
        },
    ],
    "agent_server_map": [
        {
            "agent": "phenotype_extractor",
            "paper_function": "Convert free-text clinical descriptions into standardized HPO-like phenotype entities.",
            "raredbridge_status": "implemented_seed",
        },
        {
            "agent": "disease_normalizer",
            "paper_function": "Normalize candidate disease names to controlled disease identifiers.",
            "raredbridge_status": "implemented_local_db",
        },
        {
            "agent": "knowledge_searcher",
            "paper_function": "Retrieve and summarize literature, rare disease databases and reliable medical pages.",
            "raredbridge_status": "partially_implemented_mcp_and_links",
        },
        {
            "agent": "case_searcher",
            "paper_function": "Search similar patient cases based on HPO profile similarity and re-rank relevance.",
            "raredbridge_status": "roadmap",
        },
        {
            "agent": "phenotype_analyser",
            "paper_function": "Call phenotype-driven diagnostic tools and combine their suggestions.",
            "raredbridge_status": "implemented_local_ranker",
        },
        {
            "agent": "genotype_analyser",
            "paper_function": "Prioritize variants with HPO context and genetic databases.",
            "raredbridge_status": "roadmap_variant_summary_now_vcf_next",
        },
    ],
    "web_workflow": [
        {
            "phase": "clinical_data_entry",
            "label": "临床资料录入",
            "paper_function": "Collect demographics, family history, symptoms and optional clinical/genomic files.",
        },
        {
            "phase": "systematic_clinical_enquiry",
            "label": "系统化追问",
            "paper_function": "Clarify organ involvement, disease progression and family/genetic clues.",
        },
        {
            "phase": "hpo_phenotype_mapping",
            "label": "HPO 表型映射",
            "paper_function": "Map clinical input to standardized phenotype terms with clinician curation.",
        },
        {
            "phase": "diagnostic_analysis",
            "label": "诊断分析输出",
            "paper_function": "Invoke tools, literature and case evidence to rank diagnoses and treatment clues.",
        },
        {
            "phase": "report_export",
            "label": "报告导出",
            "paper_function": "Export structured clinical reports for documentation and follow-up.",
        },
    ],
    "diagnostic_loop": [
        "information_collection",
        "hypothesis_generation",
        "self_reflection_validation_or_refutation",
        "evidence_linked_rationale",
        "ranked_report",
    ],
}


class RareDBridgeDiagnosisEngine:
    """Local traceable diagnosis engine for the platform."""

    def __init__(self):
        self.diseases = RARE_DISEASES_DB
        self.symptom_terms = sorted(HPO_SEED_TERMS.keys(), key=len, reverse=True)

    def run(
        self,
        *,
        case_text: str,
        hpo_terms: Optional[List[str]] = None,
        genes: Optional[List[str]] = None,
        variants: Optional[List[Dict[str, Any]]] = None,
        age: Optional[int] = None,
        gender: Optional[str] = None,
        family_history: Optional[str] = None,
        top_k: int = 5,
    ) -> Dict[str, Any]:
        normalized_hpo = self._normalize_phenotypes(case_text, hpo_terms or [])
        normalized_genes = self._normalize_genes(genes or [], case_text)
        normalized_variants = self._normalize_variants(variants or [], case_text)
        candidates = self._rank_candidates(
            normalized_hpo=normalized_hpo,
            genes=normalized_genes,
            variants=normalized_variants,
            top_k=top_k,
        )
        reflection = self._self_reflect(
            candidates=candidates,
            normalized_hpo=normalized_hpo,
            genes=normalized_genes,
            variants=normalized_variants,
            case_text=case_text,
        )
        reasoning_chain = self._build_reasoning_chain(
            normalized_hpo=normalized_hpo,
            genes=normalized_genes,
            variants=normalized_variants,
            candidates=candidates,
            reflection=reflection,
        )

        return {
            "capability": "RareDBridge Dx",
            "timestamp": datetime.now().isoformat(),
            "paper_methodology": self.get_methodology(),
            "input_summary": {
                "case_text": case_text,
                "age": age,
                "gender": gender,
                "family_history": family_history,
                "genes": normalized_genes,
                "variants": normalized_variants,
            },
            "normalized_phenotypes": normalized_hpo,
            "ranked_diagnoses": candidates,
            "reasoning_chain": reasoning_chain,
            "workflow_phase_status": self._workflow_phase_status(
                case_text=case_text,
                normalized_hpo=normalized_hpo,
                genes=normalized_genes,
                variants=normalized_variants,
                candidates=candidates,
                reflection=reflection,
            ),
            "self_reflection": reflection,
            "report": self._build_report(candidates, normalized_hpo, reflection),
            "references": [
                {
                    "label": "Nature DeepRare paper",
                    "url": "https://www.nature.com/articles/s41586-025-10097-9",
                    "role": "Capability pattern: multi-agent diagnosis, heterogeneous input, traceable reasoning.",
                },
                {
                    "label": "DeepRare WebApp",
                    "url": "https://deeprare.cn",
                    "role": "Product reference: doctor workflow, VCF/report-oriented diagnostic interface.",
                },
                {
                    "label": "DeepRare GitHub",
                    "url": "https://github.com/MAGIC-AI4Med/DeepRare",
                    "role": "Public implementation reference, not copied into this platform.",
                },
                {
                    "label": "ICT&health DeepRare coverage",
                    "url": "https://www.icthealth.org/news/deeprare-ai-outperforms-physicians-in-rare-disease-diagnosis",
                    "role": "External benchmark context: multi-agent diagnosis and physician comparison coverage.",
                },
            ],
            "disclaimer": "本结果用于罕见病诊断决策支持，不构成临床诊断。需要由遗传科、专科医生结合检查和基因检测复核。",
        }

    def get_methodology(self) -> Dict[str, Any]:
        return DEEPRARE_METHOD_FRAMEWORK

    def _normalize_phenotypes(self, case_text: str, hpo_terms: List[str]) -> List[Dict[str, Any]]:
        normalized: List[Dict[str, Any]] = []
        seen = set()
        lowered = case_text.lower()

        for raw in hpo_terms:
            term = raw.strip()
            if not term:
                continue
            hpo_match = re.search(r"HP:\d{7}", term, re.IGNORECASE)
            hpo_id = hpo_match.group(0).upper() if hpo_match else None
            key = hpo_id or term.lower()
            if key in seen:
                continue
            seen.add(key)
            normalized.append(
                {
                    "source_text": term,
                    "hpo_id": hpo_id,
                    "term": term,
                    "status": "provided",
                    "confidence": 1.0 if hpo_id else 0.78,
                }
            )

        for symptom in self.symptom_terms:
            if symptom in case_text or HPO_SEED_TERMS[symptom]["term"].lower() in lowered:
                mapping = HPO_SEED_TERMS[symptom]
                if mapping["hpo_id"] in seen:
                    continue
                seen.add(mapping["hpo_id"])
                normalized.append(
                    {
                        "source_text": symptom,
                        "hpo_id": mapping["hpo_id"],
                        "term": mapping["term"],
                        "status": "mapped",
                        "confidence": 0.92,
                    }
                )

        fallback_terms = self._extract_fallback_symptoms(case_text)
        for symptom in fallback_terms:
            key = symptom.lower()
            if key in seen:
                continue
            seen.add(key)
            normalized.append(
                {
                    "source_text": symptom,
                    "hpo_id": None,
                    "term": symptom,
                    "status": "local_phenotype",
                    "confidence": 0.62,
                }
            )

        return normalized[:14]

    def _normalize_genes(self, genes: List[str], case_text: str) -> List[str]:
        candidates = []
        for gene in genes:
            candidates.extend(re.split(r"[,，;；\s]+", gene.strip()))

        gene_like = re.findall(r"\b[A-Z][A-Z0-9]{2,10}\b", case_text)
        candidates.extend(gene_like)
        return self._dedupe([gene.upper() for gene in candidates if len(gene) >= 3])[:12]

    def _normalize_variants(self, variants: List[Dict[str, Any]], case_text: str) -> List[Dict[str, Any]]:
        normalized = []
        for variant in variants:
            gene = str(variant.get("gene") or "").strip().upper()
            notation = str(variant.get("variant") or variant.get("notation") or "").strip()
            consequence = str(variant.get("consequence") or variant.get("impact") or "").strip()
            if gene or notation:
                normalized.append({"gene": gene, "variant": notation, "consequence": consequence})

        variant_hits = re.findall(r"\b([A-Z][A-Z0-9]{2,10})[:\s]+(c\.[A-Za-z0-9_>\+\-\.]+|p\.[A-Za-z0-9_>\+\-\.]+)", case_text)
        for gene, notation in variant_hits:
            normalized.append({"gene": gene.upper(), "variant": notation, "consequence": ""})

        seen = set()
        deduped = []
        for variant in normalized:
            key = (variant.get("gene"), variant.get("variant"))
            if key in seen:
                continue
            seen.add(key)
            deduped.append(variant)
        return deduped[:10]

    def _rank_candidates(
        self,
        *,
        normalized_hpo: List[Dict[str, Any]],
        genes: List[str],
        variants: List[Dict[str, Any]],
        top_k: int,
    ) -> List[Dict[str, Any]]:
        phenotype_texts = [item["source_text"] for item in normalized_hpo] + [item["term"] for item in normalized_hpo]
        variant_genes = [item.get("gene", "") for item in variants if item.get("gene")]
        gene_inputs = set(genes + variant_genes)
        scored = []

        for disease in self.diseases:
            symptom_matches = []
            for disease_symptom in disease.key_symptoms:
                if any(self._soft_contains(input_term, disease_symptom) for input_term in phenotype_texts):
                    symptom_matches.append(disease_symptom)

            disease_genes = self._split_disease_genes(disease.gene or "")
            gene_matches = sorted(gene_inputs.intersection(disease_genes))
            phenotype_score = len(set(symptom_matches)) / max(len(disease.key_symptoms), 1)
            input_coverage = len(set(symptom_matches)) / max(len(normalized_hpo), 1)
            gene_score = 1.0 if gene_matches else 0.0
            score = min(0.99, 0.48 * phenotype_score + 0.28 * input_coverage + 0.24 * gene_score)

            if score <= 0:
                continue

            scored.append(
                {
                    "name_cn": disease.name_cn,
                    "name_en": disease.name_en,
                    "omim_id": disease.omim_id,
                    "category": disease.category.value,
                    "prevalence": disease.prevalence,
                    "inheritance": disease.inheritance,
                    "gene": disease.gene,
                    "score": round(score, 3),
                    "confidence_label": self._confidence_label(score),
                    "matched_phenotypes": self._dedupe(symptom_matches),
                    "matched_genes": gene_matches,
                    "diagnosis_method": disease.diagnosis_method,
                    "treatment": disease.treatment,
                    "evidence_links": self._evidence_links(disease),
                    "reason": self._candidate_reason(disease, symptom_matches, gene_matches),
                }
            )

        scored.sort(key=lambda item: item["score"], reverse=True)
        for index, candidate in enumerate(scored[:top_k], start=1):
            candidate["rank"] = index
        return scored[:top_k]

    def _self_reflect(
        self,
        *,
        candidates: List[Dict[str, Any]],
        normalized_hpo: List[Dict[str, Any]],
        genes: List[str],
        variants: List[Dict[str, Any]],
        case_text: str,
    ) -> Dict[str, Any]:
        missing = []
        if len(normalized_hpo) < 3:
            missing.append("表型数量偏少，建议补充阴性体征、起病年龄、进展速度和系统受累情况。")
        if not genes and not variants:
            missing.append("缺少基因或变异线索，建议接入 WES/WGS/Panel 或 VCF 摘要。")
        if "家族" not in case_text and "遗传" not in case_text:
            missing.append("缺少家族史和遗传方式线索。")
        if not candidates:
            missing.append("当前本地罕见病库没有足够匹配项，需要扩展 Orphanet/OMIM 知识库。")

        top_score = candidates[0]["score"] if candidates else 0
        return {
            "diagnostic_confidence": self._confidence_label(top_score),
            "top_score": top_score,
            "candidate_count": len(candidates),
            "missing_information": missing,
            "review_flags": [
                "候选结果需要临床医生复核",
                "基因匹配只是支持证据，不能替代致病性判读",
                "未匹配并不代表排除罕见病，需要继续扩展知识源",
            ],
        }

    def _build_reasoning_chain(
        self,
        *,
        normalized_hpo: List[Dict[str, Any]],
        genes: List[str],
        variants: List[Dict[str, Any]],
        candidates: List[Dict[str, Any]],
        reflection: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        return [
            {
                "step": "input_intake",
                "title": "多模态输入接收",
                "detail": f"接收自由文本、{len(normalized_hpo)} 个表型、{len(genes)} 个基因和 {len(variants)} 条变异线索。",
            },
            {
                "step": "hpo_normalization",
                "title": "HPO/表型标准化",
                "detail": "将症状映射到 HPO 种子词表；未覆盖表型保留为本地 phenotype signal。",
                "payload": normalized_hpo,
            },
            {
                "step": "hypothesis_ranking",
                "title": "候选诊断排序",
                "detail": f"基于表型覆盖、疾病表型重叠和基因匹配生成 {len(candidates)} 个候选诊断。",
            },
            {
                "step": "traceable_evidence",
                "title": "可追溯证据",
                "detail": "每个候选输出 OMIM/PubMed/Orphanet 检索入口和匹配理由，便于人工复核。",
            },
            {
                "step": "self_reflection",
                "title": "自反复核",
                "detail": f"当前置信度：{reflection['diagnostic_confidence']}；待补充信息 {len(reflection['missing_information'])} 项。",
            },
        ]

    def _build_report(
        self,
        candidates: List[Dict[str, Any]],
        normalized_hpo: List[Dict[str, Any]],
        reflection: Dict[str, Any],
    ) -> str:
        if not candidates:
            return "当前输入尚不足以在本地罕见病库中形成稳定候选诊断。建议补充 HPO 表型、基因检测结果和家族史后再次分析。"

        top = candidates[0]
        phenotype_names = "、".join(item["source_text"] for item in normalized_hpo[:6]) or "暂未识别"
        return (
            f"RareDBridge Dx 识别到的主要表型包括：{phenotype_names}。\n"
            f"当前最高优先级候选为 {top['name_cn']}（{top['name_en']}），"
            f"综合评分 {top['score']}，置信度为{top['confidence_label']}。\n"
            f"主要依据：{top['reason']}\n"
            f"建议下一步：{top['diagnosis_method']}。"
            f"需要补充的信息：{'；'.join(reflection['missing_information']) if reflection['missing_information'] else '暂无关键缺口。'}"
        )

    def _workflow_phase_status(
        self,
        *,
        case_text: str,
        normalized_hpo: List[Dict[str, Any]],
        genes: List[str],
        variants: List[Dict[str, Any]],
        candidates: List[Dict[str, Any]],
        reflection: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        return [
            {
                "phase": "clinical_data_entry",
                "label": "临床资料录入",
                "status": "active" if case_text else "missing",
                "detail": "已接收病例文本、人口学信息、家族史、基因和变异摘要；原始 VCF/影像/检验文件为下一阶段能力。",
            },
            {
                "phase": "systematic_clinical_enquiry",
                "label": "系统化追问",
                "status": "needs_review" if reflection["missing_information"] else "sufficient_for_first_pass",
                "detail": "通过自反复核列出缺失信息，用于下一轮病史、系统受累和遗传方式追问。",
            },
            {
                "phase": "hpo_phenotype_mapping",
                "label": "HPO 表型映射",
                "status": "active" if normalized_hpo else "missing",
                "detail": f"已标准化或保留 {len(normalized_hpo)} 个表型信号；当前使用 HPO 种子词表，完整 HPO 检索为路线图。",
            },
            {
                "phase": "diagnostic_analysis",
                "label": "诊断分析输出",
                "status": "active" if candidates else "insufficient_evidence",
                "detail": f"已结合表型、{len(genes)} 个基因和 {len(variants)} 条变异线索生成 {len(candidates)} 个候选诊断。",
            },
            {
                "phase": "report_export",
                "label": "报告导出",
                "status": "text_report_available",
                "detail": "当前可生成结构化文本报告；PDF/Word 导出和电子病历归档为后续产品能力。",
            },
        ]

    def _extract_fallback_symptoms(self, case_text: str) -> List[str]:
        result = []
        for chunk in re.split(r"[，。；;、\n]", case_text):
            stripped = chunk.strip()
            if not stripped or len(stripped) > 22:
                continue
            if any(keyword in stripped for keyword in ["痛", "困难", "异常", "下降", "升高", "肿大", "迟缓", "无力", "发热"]):
                result.append(stripped)
        return self._dedupe(result)[:6]

    def _soft_contains(self, left: str, right: str) -> bool:
        left = left.lower()
        right = right.lower()
        return bool(left and right and (left in right or right in left))

    def _split_disease_genes(self, genes: str) -> set:
        tokens = re.split(r"[,，/、\s()（）]+", genes.upper())
        return {token for token in tokens if re.match(r"^[A-Z][A-Z0-9]{2,10}$", token)}

    def _confidence_label(self, score: float) -> str:
        if score >= 0.72:
            return "高"
        if score >= 0.38:
            return "中"
        if score > 0:
            return "低"
        return "待确认"

    def _candidate_reason(self, disease: Any, symptoms: List[str], genes: List[str]) -> str:
        parts = []
        if symptoms:
            parts.append(f"匹配关键表型 {', '.join(self._dedupe(symptoms)[:5])}")
        if genes:
            parts.append(f"匹配基因 {', '.join(genes)}")
        if not parts:
            parts.append("弱匹配，需要更多表型和遗传证据")
        return "；".join(parts) + f"；该病常见诊断方式为 {disease.diagnosis_method}"

    def _evidence_links(self, disease: Any) -> List[Dict[str, str]]:
        query = disease.name_en.replace(" ", "+")
        links = [
            {"label": "PubMed", "url": f"https://pubmed.ncbi.nlm.nih.gov/?term={query}"},
            {"label": "Orphanet", "url": f"https://www.orpha.net/en/disease/search?query={query}"},
        ]
        if disease.omim_id:
            links.insert(0, {"label": "OMIM", "url": f"https://omim.org/entry/{disease.omim_id}"})
        return links

    def _dedupe(self, values: List[str]) -> List[str]:
        seen = set()
        result = []
        for value in values:
            if value and value not in seen:
                seen.add(value)
                result.append(value)
        return result
