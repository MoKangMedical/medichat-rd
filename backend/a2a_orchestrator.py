"""
MediChat-RD A2A 编排层

目标：
1. 为罕见病平台提供真正的 session orchestration，而不是单点工具调用
2. 把患者入口、表型、证据、药物重定位、临床试验和患者社群串成一条可执行链路
3. 复用现有 MCP / MIMO / 本地罕见病库 / 社群管理模块
"""

from __future__ import annotations

import json
import re
import sys
import uuid
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

try:
    from agents.rare_disease_agent import RARE_DISEASES_DB, search_rare_disease_by_symptoms
except ImportError:
    from rare_disease_agent import RARE_DISEASES_DB, search_rare_disease_by_symptoms

try:
    from .secondme_integration import CommunityManager, PatientAvatar, SecondMeClient
    from .raredbridge_diagnosis import RareDBridgeDiagnosisEngine
except ImportError:
    from secondme_integration import CommunityManager, PatientAvatar, SecondMeClient
    from raredbridge_diagnosis import RareDBridgeDiagnosisEngine


class A2AOrchestrator:
    """面向罕见病场景的 A2A 编排器。"""

    AGENT_CATALOG = {
        "patient_intake_agent": {
            "id": "patient_intake_agent",
            "name": "Patient Intake Agent",
            "label": "患者入口 Agent",
            "stage": "intake",
            "description": "接住患者或研究者的原始问题，整理为可执行任务。",
            "capabilities": ["主诉整理", "任务归类", "紧急程度提示", "首位 Agent 推荐"],
            "supports_modes": ["auto", "lead-agent", "roundtable"],
        },
        "phenotype_agent": {
            "id": "phenotype_agent",
            "name": "Phenotype Agent",
            "label": "表型 Agent",
            "stage": "phenotype",
            "description": "把症状输入映射为结构化表型与候选罕见病线索。",
            "capabilities": ["症状提取", "候选疾病排序", "检查建议"],
            "supports_modes": ["auto", "lead-agent", "roundtable"],
        },
        "evidence_agent": {
            "id": "evidence_agent",
            "name": "Evidence Agent",
            "label": "证据 Agent",
            "stage": "evidence",
            "description": "整合疾病知识、靶点和文献证据，形成研究级基础图谱。",
            "capabilities": ["疾病知识", "OpenTargets", "PubMed 摘要"],
            "supports_modes": ["auto", "lead-agent", "roundtable"],
        },
        "diagnosis_agent": {
            "id": "diagnosis_agent",
            "name": "RareDBridge Dx Agent",
            "label": "诊断 Agent",
            "stage": "diagnosis",
            "description": "参考 DeepRare 能力形态，融合自由文本、HPO、基因和变异线索，生成可追溯差异诊断排序。",
            "capabilities": ["HPO 标准化", "候选诊断排序", "基因/变异线索叠加", "可追溯推理链"],
            "supports_modes": ["auto", "lead-agent", "roundtable"],
        },
        "repurposing_agent": {
            "id": "repurposing_agent",
            "name": "Repurposing Agent",
            "label": "药物重定位 Agent",
            "stage": "repurposing",
            "description": "围绕疾病上下文给出已有药物池和再利用线索。",
            "capabilities": ["ChEMBL 检索", "候选药物池", "重定位线索"],
            "supports_modes": ["auto", "lead-agent", "roundtable"],
        },
        "trial_agent": {
            "id": "trial_agent",
            "name": "Trial Agent",
            "label": "临床试验 Agent",
            "stage": "trial",
            "description": "把疾病方向映射到试验登记信息，形成试验导航清单。",
            "capabilities": ["ClinicalTrials 检索", "招募状态过滤", "下一步联络建议"],
            "supports_modes": ["auto", "lead-agent", "roundtable"],
        },
        "community_agent": {
            "id": "community_agent",
            "name": "Community Agent",
            "label": "患者社群 Agent",
            "stage": "community",
            "description": "把结果回流到患者互助、数字分身和长期支持场景。",
            "capabilities": ["社群推荐", "SecondMe 分身", "病友匹配", "社群发帖建议"],
            "supports_modes": ["roundtable", "lead-agent"],
        },
        "report_agent": {
            "id": "report_agent",
            "name": "Report Agent",
            "label": "报告 Agent",
            "stage": "report",
            "description": "将多个 Agent 的输出收束为统一摘要和行动清单。",
            "capabilities": ["A2A 总结", "行动清单", "会话摘要"],
            "supports_modes": ["auto", "lead-agent", "roundtable"],
        },
    }

    LEAD_AGENT_BY_FOCUS = {
        "symptom_triage": "phenotype_agent",
        "disease_research": "evidence_agent",
        "deep_diagnosis": "diagnosis_agent",
        "repurposing": "repurposing_agent",
        "trial_matching": "trial_agent",
        "community_support": "community_agent",
        "general_consult": "patient_intake_agent",
    }

    EMERGENCY_KEYWORDS = [
        "呼吸困难",
        "无法呼吸",
        "窒息",
        "抽搐",
        "意识障碍",
        "昏迷",
        "持续高热",
        "胸痛",
        "紫绀",
        "无法吞咽",
        "严重出血",
        "突发瘫痪",
    ]

    TASK_KEYWORDS = {
        "trial_matching": ["临床试验", "招募", "试验", "nct", "trial", "入组"],
        "deep_diagnosis": ["诊断", "差异诊断", "疑似", "hpo", "vcf", "变异", "基因检测", "全外显子", "wgs", "wes", "genome"],
        "repurposing": ["药物重定位", "老药新用", "靶点", "药物", "候选药物", "repurpos"],
        "disease_research": ["研究", "文献", "证据", "机制", "综述", "靶点发现"],
        "community_support": ["社群", "病友", "互助", "家属", "支持", "经验分享", "社区"],
    }

    def __init__(
        self,
        *,
        mcp_call: Callable[[str, dict, int], dict],
        get_mimo_client: Callable[[], Any],
        model_name: str,
        load_disease_knowledge: Callable[[str], dict],
        mimo_available: bool,
    ):
        self.mcp_call = mcp_call
        self.get_mimo_client = get_mimo_client
        self.model_name = model_name
        self.load_disease_knowledge = load_disease_knowledge
        self.mimo_available = mimo_available
        self.community_manager = CommunityManager()
        self.secondme_client = SecondMeClient()
        self.diagnosis_engine = RareDBridgeDiagnosisEngine()
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.disease_lookup = self._build_disease_lookup()
        self.symptom_lexicon = self._build_symptom_lexicon()

    # ============================================================
    # 基础工具
    # ============================================================

    def _now(self) -> str:
        return datetime.now().isoformat()

    def _new_id(self, prefix: str) -> str:
        return f"{prefix}_{uuid.uuid4().hex[:10]}"

    def _build_disease_lookup(self) -> Dict[str, Any]:
        lookup: Dict[str, Any] = {}
        for disease in RARE_DISEASES_DB:
            lookup[disease.name_cn.lower()] = disease
            lookup[disease.name_en.lower()] = disease
        return lookup

    def _build_symptom_lexicon(self) -> List[str]:
        seen = set()
        for disease in RARE_DISEASES_DB:
            for symptom in disease.key_symptoms:
                cleaned = symptom.strip()
                if cleaned:
                    seen.add(cleaned)
        generic = {
            "头痛",
            "发热",
            "乏力",
            "疲劳",
            "肌无力",
            "吞咽困难",
            "呼吸困难",
            "腹痛",
            "贫血",
            "皮疹",
            "蛋白尿",
            "骨痛",
            "发育迟缓",
            "生长迟缓",
            "视力下降",
            "听力下降",
            "抽搐",
            "心肌病变",
            "肝脏肿大",
            "脾脏肿大",
        }
        seen.update(generic)
        return sorted(seen, key=len, reverse=True)

    def _dedupe_preserve_order(self, values: List[str]) -> List[str]:
        seen = set()
        result = []
        for value in values:
            if value and value not in seen:
                seen.add(value)
                result.append(value)
        return result

    def _push_event(
        self,
        session: Dict[str, Any],
        *,
        event_type: str,
        agent_id: str,
        headline: str,
        detail: str,
        status: str = "completed",
        payload: Optional[Dict[str, Any]] = None,
    ) -> None:
        session["events"].append(
            {
                "event_id": self._new_id("evt"),
                "type": event_type,
                "agent_id": agent_id,
                "headline": headline,
                "detail": detail,
                "status": status,
                "payload": payload or {},
                "created_at": self._now(),
            }
        )

    def _create_artifact(
        self,
        *,
        agent_id: str,
        artifact_type: str,
        title: str,
        content: Dict[str, Any],
        status: str = "completed",
    ) -> Dict[str, Any]:
        return {
            "artifact_id": self._new_id("art"),
            "agent_id": agent_id,
            "type": artifact_type,
            "title": title,
            "status": status,
            "content": content,
            "created_at": self._now(),
        }

    def _message_to_record(self, role: str, content: str, **extra: Any) -> Dict[str, Any]:
        message = {
            "message_id": self._new_id("msg"),
            "role": role,
            "content": content,
            "created_at": self._now(),
        }
        if extra:
            message.update(extra)
        return message

    def _match_known_disease(self, text: str) -> Optional[Any]:
        lowered = text.lower()
        for key, disease in self.disease_lookup.items():
            if key and key in lowered:
                return disease
        return None

    def _infer_disease_from_free_text(self, text: str) -> Optional[str]:
        patterns = [
            r"(?:研究|分析|查看|匹配|评估)\s+([A-Za-z][A-Za-z0-9\-\s]{3,60})",
            r"([A-Za-z][A-Za-z0-9\-\s]{3,60}\s(?:disease|syndrome|dystrophy|atrophy|disorder))",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                candidate = re.sub(r"\s+", " ", match.group(1)).strip(" .,:;，。；")
                if len(candidate) >= 4:
                    return candidate
        return None

    def _extract_symptom_terms(self, text: str) -> List[str]:
        matches = [symptom for symptom in self.symptom_lexicon if symptom in text]
        if matches:
            return self._dedupe_preserve_order(matches)[:10]

        fallback_chunks = []
        for chunk in re.split(r"[，。；;、\n]", text):
            stripped = chunk.strip()
            if not stripped or len(stripped) > 18:
                continue
            if any(keyword in stripped for keyword in ["痛", "乏力", "困难", "异常", "下降", "增高", "肿大", "迟缓", "发热"]):
                fallback_chunks.append(stripped)
        return self._dedupe_preserve_order(fallback_chunks)[:8]

    def _candidate_diseases(self, symptoms: List[str]) -> List[Dict[str, Any]]:
        if not symptoms:
            return []
        matches = search_rare_disease_by_symptoms(symptoms)
        results: List[Dict[str, Any]] = []
        for disease in matches[:5]:
            matched_symptoms = []
            for symptom in symptoms:
                for key_symptom in disease.key_symptoms:
                    if symptom in key_symptom or key_symptom in symptom:
                        matched_symptoms.append(key_symptom)
                        break
            confidence = round(len(matched_symptoms) / max(len(disease.key_symptoms), 1) * 100, 1)
            results.append(
                {
                    "name_cn": disease.name_cn,
                    "name_en": disease.name_en,
                    "omim_id": disease.omim_id,
                    "gene": disease.gene,
                    "confidence": confidence,
                    "matched_symptoms": self._dedupe_preserve_order(matched_symptoms),
                    "diagnosis_method": disease.diagnosis_method,
                    "treatment": disease.treatment,
                }
            )
        return results

    def _assess_urgency(self, text: str) -> str:
        for keyword in self.EMERGENCY_KEYWORDS:
            if keyword in text:
                return "high"
        if any(keyword in text for keyword in ["呼吸", "吞咽", "瘫痪", "抽搐", "严重疼痛"]):
            return "medium"
        return "low"

    def _classify_focus(self, text: str, symptoms: List[str], disease_query: Optional[str]) -> str:
        lowered = text.lower()
        for focus, keywords in self.TASK_KEYWORDS.items():
            if any(keyword.lower() in lowered for keyword in keywords):
                return focus
        if symptoms:
            return "symptom_triage"
        if disease_query:
            return "disease_research"
        return "general_consult"

    def _build_context(self, session: Dict[str, Any], content: str, disease_context: Optional[str]) -> Dict[str, Any]:
        full_text = "\n".join(
            [msg["content"] for msg in session["messages"] if msg["role"] == "user"] + [content]
        )
        known_disease = self._match_known_disease(full_text)
        symptoms = self._extract_symptom_terms(full_text)
        candidates = self._candidate_diseases(symptoms)

        disease_query = disease_context or session.get("disease_context")
        disease_label = disease_query
        if known_disease:
            disease_query = disease_query or known_disease.name_en
            disease_label = disease_label or known_disease.name_cn
        elif not disease_query and candidates:
            disease_query = candidates[0]["name_en"]
            disease_label = candidates[0]["name_cn"]
        elif not disease_query:
            disease_query = self._infer_disease_from_free_text(content)
            disease_label = disease_query

        focus = self._classify_focus(full_text, symptoms, disease_query)
        lead_agent = session.get("lead_agent") or self.LEAD_AGENT_BY_FOCUS.get(focus, "patient_intake_agent")

        return {
            "summary_input": content.strip(),
            "symptoms": symptoms,
            "candidate_diseases": candidates,
            "disease_query": disease_query,
            "disease_label": disease_label,
            "known_disease": {
                "name_cn": known_disease.name_cn,
                "name_en": known_disease.name_en,
                "omim_id": known_disease.omim_id,
                "gene": known_disease.gene,
                "diagnosis_method": known_disease.diagnosis_method,
            }
            if known_disease
            else None,
            "task_focus": focus,
            "recommended_lead_agent": lead_agent,
            "urgency": self._assess_urgency(full_text),
        }

    def _select_chain(self, mode: str, lead_agent: Optional[str], context: Dict[str, Any]) -> List[str]:
        chain = ["patient_intake_agent"]
        focus = context["task_focus"]
        disease_query = context["disease_query"]

        if mode == "lead-agent" and lead_agent in self.AGENT_CATALOG and lead_agent not in chain:
            chain.append(lead_agent)

        if context["symptoms"] and "phenotype_agent" not in chain:
            chain.append("phenotype_agent")

        if focus == "deep_diagnosis" and "diagnosis_agent" not in chain:
            chain.append("diagnosis_agent")

        if disease_query and "evidence_agent" not in chain:
            chain.append("evidence_agent")

        if focus in {"repurposing", "disease_research"} and disease_query and "repurposing_agent" not in chain:
            chain.append("repurposing_agent")

        if focus == "trial_matching" and disease_query and "trial_agent" not in chain:
            chain.append("trial_agent")

        if mode == "roundtable":
            if "phenotype_agent" not in chain:
                chain.append("phenotype_agent")
            if "diagnosis_agent" not in chain:
                chain.append("diagnosis_agent")
            if disease_query and "evidence_agent" not in chain:
                chain.append("evidence_agent")
            if disease_query and "repurposing_agent" not in chain:
                chain.append("repurposing_agent")
            if disease_query and "trial_agent" not in chain:
                chain.append("trial_agent")
            chain.append("community_agent")
        elif focus == "community_support":
            chain.append("community_agent")

        chain.append("report_agent")
        return self._dedupe_preserve_order(chain)

    def _safe_mcp_call(self, tool_name: str, arguments: dict, timeout: int = 60) -> dict:
        try:
            return self.mcp_call(tool_name, arguments, timeout)
        except Exception as error:
            return {"error": str(error)}

    def _safe_mimo_summary(self, system_prompt: str, user_prompt: str) -> Optional[str]:
        if not self.mimo_available:
            return None
        try:
            client = self.get_mimo_client()
            response = client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.3,
                max_tokens=1400,
            )
            return response.choices[0].message.content
        except Exception:
            return None

    def _normalize_literature(self, result: dict) -> List[Dict[str, Any]]:
        if not result or result.get("error"):
            return []
        data = result.get("data", result)
        articles = data.get("articles") if isinstance(data, dict) else data
        if isinstance(data, dict) and "results" in data:
            articles = data["results"]
        if not isinstance(articles, list):
            return []

        normalized = []
        for item in articles[:5]:
            normalized.append(
                {
                    "pmid": item.get("pmid") or item.get("id") or item.get("uid") or "",
                    "title": item.get("title") or item.get("article_title") or item.get("articleTitle") or "",
                    "journal": item.get("journal") or item.get("source") or "",
                    "summary": item.get("abstract") or item.get("summary") or item.get("snippet") or "",
                }
            )
        return normalized

    def _normalize_trials(self, result: dict) -> List[Dict[str, Any]]:
        if not result or result.get("error"):
            return []
        studies = result.get("data", {}).get("studies", [])
        normalized = []
        for study in studies[:6]:
            protocol = study.get("protocolSection", {})
            identification = protocol.get("identificationModule", {})
            status_module = protocol.get("statusModule", {})
            description = protocol.get("descriptionModule", {})
            sponsor = protocol.get("sponsorCollaboratorsModule", {})
            normalized.append(
                {
                    "nct_id": identification.get("nctId", ""),
                    "title": identification.get("briefTitle", ""),
                    "status": status_module.get("overallStatus", ""),
                    "summary": description.get("briefSummary", "")[:240],
                    "sponsor": sponsor.get("leadSponsor", {}).get("name", ""),
                }
            )
        return normalized

    def _normalize_drugs(self, result: dict) -> List[Dict[str, Any]]:
        if not result or result.get("error"):
            return []
        drugs = result.get("data", [])
        normalized = []
        for drug in drugs[:8]:
            normalized.append(
                {
                    "chembl_id": drug.get("molecule_chembl_id", ""),
                    "mesh_heading": drug.get("mesh_heading", ""),
                    "max_phase": drug.get("max_phase_for_ind", ""),
                    "refs": [ref.get("ref_url") for ref in drug.get("indication_refs", [])[:2] if ref.get("ref_url")],
                }
            )
        return normalized

    # ============================================================
    # Session API
    # ============================================================

    def list_agents(self) -> List[Dict[str, Any]]:
        return list(self.AGENT_CATALOG.values())

    def list_sessions(self) -> List[Dict[str, Any]]:
        summaries = []
        for session in self.sessions.values():
            summaries.append(
                {
                    "session_id": session["session_id"],
                    "title": session["title"],
                    "mode": session["mode"],
                    "status": session["status"],
                    "lead_agent": session.get("lead_agent"),
                    "disease_context": session.get("disease_context"),
                    "current_focus": session.get("current_focus"),
                    "messages_count": len(session["messages"]),
                    "artifacts_count": len(session["artifacts"]),
                    "updated_at": session["updated_at"],
                }
            )
        return sorted(summaries, key=lambda item: item["updated_at"], reverse=True)

    def get_session(self, session_id: str) -> Dict[str, Any]:
        session = self.sessions.get(session_id)
        if not session:
            raise KeyError(session_id)
        return deepcopy(session)

    async def create_session(
        self,
        *,
        mode: str,
        lead_agent: Optional[str],
        disease_context: Optional[str],
        patient_profile: Optional[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]],
        initial_message: Optional[str],
    ) -> Dict[str, Any]:
        session_id = self._new_id("a2a")
        normalized_mode = mode if mode in {"auto", "lead-agent", "roundtable"} else "auto"
        title = "罕见病 A2A 会话"

        session = {
            "session_id": session_id,
            "title": title,
            "mode": normalized_mode,
            "status": "active",
            "lead_agent": lead_agent if lead_agent in self.AGENT_CATALOG else None,
            "disease_context": disease_context,
            "patient_profile": patient_profile or {},
            "metadata": metadata or {},
            "created_at": self._now(),
            "updated_at": self._now(),
            "current_focus": "general_consult",
            "messages": [],
            "events": [],
            "artifacts": [],
            "orchestration": {
                "planned_chain": [],
                "executed_chain": [],
                "last_context": {},
            },
        }
        self.sessions[session_id] = session

        self._push_event(
            session,
            event_type="session_created",
            agent_id="system",
            headline="A2A 会话已创建",
            detail=f"模式：{normalized_mode}",
            payload={"lead_agent": session["lead_agent"], "disease_context": disease_context},
        )

        if initial_message:
            return await self.add_message(session_id, initial_message, disease_context=disease_context)
        return self._format_response(session, assistant_message=None)

    async def add_message(
        self,
        session_id: str,
        content: str,
        *,
        disease_context: Optional[str] = None,
    ) -> Dict[str, Any]:
        session = self.sessions.get(session_id)
        if not session:
            raise KeyError(session_id)

        content = content.strip()
        session["messages"].append(self._message_to_record("user", content))
        session["updated_at"] = self._now()

        if disease_context:
            session["disease_context"] = disease_context

        context = self._build_context(session, content, disease_context)
        session["current_focus"] = context["task_focus"]
        if not session.get("lead_agent"):
            session["lead_agent"] = context["recommended_lead_agent"]

        if session["title"] == "罕见病 A2A 会话":
            title_base = context["disease_label"] or content[:24]
            session["title"] = f"{title_base} · A2A 会话"

        chain = self._select_chain(session["mode"], session.get("lead_agent"), context)
        session["orchestration"]["planned_chain"] = chain
        session["orchestration"]["last_context"] = context

        self._push_event(
            session,
            event_type="orchestration_planned",
            agent_id="system",
            headline="A2A 链路已规划",
            detail=" → ".join(self.AGENT_CATALOG[agent]["label"] for agent in chain),
            payload={"focus": context["task_focus"], "urgency": context["urgency"]},
        )

        generated_artifacts: List[Dict[str, Any]] = []
        for agent_id in chain:
            if agent_id == "report_agent":
                artifact = self._run_report_agent(session, context, generated_artifacts)
            elif agent_id == "patient_intake_agent":
                artifact = self._run_patient_intake_agent(session, context)
            elif agent_id == "phenotype_agent":
                artifact = self._run_phenotype_agent(session, context)
            elif agent_id == "evidence_agent":
                artifact = self._run_evidence_agent(session, context)
            elif agent_id == "diagnosis_agent":
                artifact = self._run_diagnosis_agent(session, context)
            elif agent_id == "repurposing_agent":
                artifact = self._run_repurposing_agent(session, context)
            elif agent_id == "trial_agent":
                artifact = self._run_trial_agent(session, context)
            elif agent_id == "community_agent":
                artifact = await self._run_community_agent(session, context)
            else:
                continue

            session["artifacts"].append(artifact)
            generated_artifacts.append(artifact)

        session["orchestration"]["executed_chain"] = [artifact["agent_id"] for artifact in generated_artifacts]
        session["updated_at"] = self._now()

        final_report = generated_artifacts[-1] if generated_artifacts else None
        assistant_message = None
        if final_report and final_report["agent_id"] == "report_agent":
            assistant_message = final_report["content"]["assistant_message"]
            session["messages"].append(
                self._message_to_record(
                    "assistant",
                    assistant_message,
                    agent_id="report_agent",
                    focus=context["task_focus"],
                )
            )

        return self._format_response(session, assistant_message=assistant_message)

    def _format_response(self, session: Dict[str, Any], assistant_message: Optional[str]) -> Dict[str, Any]:
        snapshot = deepcopy(session)
        latest_report = next(
            (artifact for artifact in reversed(snapshot["artifacts"]) if artifact["agent_id"] == "report_agent"),
            None,
        )
        return {
            "session": snapshot,
            "assistant_message": assistant_message,
            "latest_report": latest_report["content"] if latest_report else None,
            "executed_agents": snapshot["orchestration"].get("executed_chain", []),
        }

    # ============================================================
    # Agent implementations
    # ============================================================

    def _run_patient_intake_agent(self, session: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        detail = {
            "problem_summary": context["summary_input"],
            "task_focus": context["task_focus"],
            "urgency": context["urgency"],
            "recommended_lead_agent": context["recommended_lead_agent"],
            "symptoms": context["symptoms"],
            "disease_context": context["disease_label"] or context["disease_query"],
        }
        self._push_event(
            session,
            event_type="agent_completed",
            agent_id="patient_intake_agent",
            headline="患者入口已整理问题",
            detail=f"焦点：{context['task_focus']} | 紧急程度：{context['urgency']}",
            payload=detail,
        )
        return self._create_artifact(
            agent_id="patient_intake_agent",
            artifact_type="intake_summary",
            title="患者入口摘要",
            content=detail,
        )

    def _run_phenotype_agent(self, session: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        if not context["symptoms"]:
            self._push_event(
                session,
                event_type="agent_skipped",
                agent_id="phenotype_agent",
                headline="表型 Agent 跳过",
                detail="未识别出可结构化的症状输入。",
                status="skipped",
            )
            return self._create_artifact(
                agent_id="phenotype_agent",
                artifact_type="phenotype_report",
                title="表型分析",
                status="skipped",
                content={"reason": "未识别出可结构化的症状输入。", "candidate_diseases": []},
            )

        recommended_tests = self._dedupe_preserve_order(
            [candidate["diagnosis_method"] for candidate in context["candidate_diseases"] if candidate.get("diagnosis_method")]
        )[:4]
        content = {
            "symptoms": context["symptoms"],
            "candidate_diseases": context["candidate_diseases"],
            "recommended_tests": recommended_tests,
            "recommended_actions": [
                "补充病程、家族史和既往检查结果",
                "优先围绕高匹配疾病补做针对性检查",
                "将结果带入后续证据和试验分析链路",
            ],
        }
        self._push_event(
            session,
            event_type="agent_completed",
            agent_id="phenotype_agent",
            headline="表型结构化完成",
            detail=f"识别症状 {len(context['symptoms'])} 项，候选疾病 {len(context['candidate_diseases'])} 个。",
            payload={"symptoms": context["symptoms"]},
        )
        return self._create_artifact(
            agent_id="phenotype_agent",
            artifact_type="phenotype_report",
            title="表型分析",
            content=content,
        )

    def _run_evidence_agent(self, session: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        disease_query = context["disease_query"]
        if not disease_query:
            self._push_event(
                session,
                event_type="agent_skipped",
                agent_id="evidence_agent",
                headline="证据 Agent 跳过",
                detail="当前没有可用的疾病上下文，暂不执行靶点和文献汇聚。",
                status="skipped",
            )
            return self._create_artifact(
                agent_id="evidence_agent",
                artifact_type="evidence_report",
                title="证据图谱",
                status="skipped",
                content={"reason": "没有可用的疾病上下文。"},
            )

        known_disease = context.get("known_disease")
        knowledge = self.load_disease_knowledge(disease_query) or self.load_disease_knowledge(context.get("disease_label") or "")
        disease_search = self._safe_mcp_call("opentargets_search", {"query": disease_query, "entity_type": "disease"})
        top_match = disease_search.get("data", [None])[0] if disease_search.get("data") else None
        disease_id = top_match["id"] if top_match else None

        targets = []
        if disease_id:
            target_result = self._safe_mcp_call("opentargets_get_associations", {"disease_id": disease_id, "size": 6})
            targets = [
                {
                    "gene_id": item["target"]["id"],
                    "gene_name": item["target"]["approvedName"],
                    "score": round(item["score"], 3),
                }
                for item in target_result.get("data", [])[:6]
            ]

        literature = self._normalize_literature(
            self._safe_mcp_call("pubmed_search_articles", {"diseases": [disease_query], "max_results": 5})
        )

        content = {
            "resolved_disease": {
                "query": disease_query,
                "display_name": top_match["name"] if top_match else context.get("disease_label") or disease_query,
                "disease_id": disease_id,
                "omim_id": known_disease["omim_id"] if known_disease else None,
                "gene": known_disease["gene"] if known_disease else None,
            },
            "knowledge_snapshot": knowledge if knowledge else {},
            "targets": targets,
            "literature": literature,
        }
        self._push_event(
            session,
            event_type="agent_completed",
            agent_id="evidence_agent",
            headline="证据图谱已生成",
            detail=f"疾病：{content['resolved_disease']['display_name']} | 靶点 {len(targets)} 个 | 文献 {len(literature)} 篇。",
            payload={"disease_query": disease_query},
        )
        return self._create_artifact(
            agent_id="evidence_agent",
            artifact_type="evidence_report",
            title="证据图谱",
            content=content,
        )

    def _run_diagnosis_agent(self, session: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        patient_profile = session.get("patient_profile") or {}
        diagnosis_result = self.diagnosis_engine.run(
            case_text="\n".join(msg["content"] for msg in session["messages"] if msg["role"] == "user"),
            hpo_terms=[],
            genes=[],
            variants=[],
            age=patient_profile.get("age"),
            gender=patient_profile.get("gender"),
            family_history=patient_profile.get("family_history"),
            top_k=5,
        )
        top = diagnosis_result["ranked_diagnoses"][0] if diagnosis_result["ranked_diagnoses"] else None
        self._push_event(
            session,
            event_type="agent_completed",
            agent_id="diagnosis_agent",
            headline="RareDBridge Dx 已完成差异诊断排序",
            detail=f"候选诊断 {len(diagnosis_result['ranked_diagnoses'])} 个"
            + (f"，首位：{top['name_cn']}" if top else "，未形成稳定候选。"),
            payload={"top_candidate": top},
        )
        return self._create_artifact(
            agent_id="diagnosis_agent",
            artifact_type="diagnosis_report",
            title="RareDBridge Dx 差异诊断",
            content=diagnosis_result,
        )

    def _run_repurposing_agent(self, session: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        disease_query = context["disease_query"]
        if not disease_query:
            self._push_event(
                session,
                event_type="agent_skipped",
                agent_id="repurposing_agent",
                headline="药物重定位 Agent 跳过",
                detail="没有解析到疾病上下文，暂不进行药物池分析。",
                status="skipped",
            )
            return self._create_artifact(
                agent_id="repurposing_agent",
                artifact_type="repurposing_report",
                title="药物重定位线索",
                status="skipped",
                content={"reason": "没有解析到疾病上下文。"},
            )

        drugs = self._normalize_drugs(
            self._safe_mcp_call("chembl_find_drugs_by_indication", {"disease_query": disease_query, "max_results": 10})
        )
        overlap_hints = []
        evidence_artifact = next(
            (artifact for artifact in reversed(session["artifacts"]) if artifact["agent_id"] == "evidence_agent"),
            None,
        )
        if evidence_artifact:
            overlap_hints = [target["gene_name"] for target in evidence_artifact["content"].get("targets", [])[:4]]

        content = {
            "disease_query": disease_query,
            "candidate_drugs": drugs,
            "target_hints": overlap_hints,
            "recommendation": [
                "优先查看最高临床阶段且与目标疾病已有适应证交集的药物",
                "把高相关靶点与药物机制放进后续实验设计或专家讨论",
                "若证据不足，先收集更多文献与真实世界案例再推进",
            ],
        }
        self._push_event(
            session,
            event_type="agent_completed",
            agent_id="repurposing_agent",
            headline="药物重定位线索已输出",
            detail=f"候选药物 {len(drugs)} 个。",
            payload={"disease_query": disease_query},
        )
        return self._create_artifact(
            agent_id="repurposing_agent",
            artifact_type="repurposing_report",
            title="药物重定位线索",
            content=content,
        )

    def _run_trial_agent(self, session: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        disease_query = context["disease_query"]
        if not disease_query:
            self._push_event(
                session,
                event_type="agent_skipped",
                agent_id="trial_agent",
                headline="临床试验 Agent 跳过",
                detail="没有解析到疾病上下文，无法匹配试验。",
                status="skipped",
            )
            return self._create_artifact(
                agent_id="trial_agent",
                artifact_type="trial_report",
                title="临床试验导航",
                status="skipped",
                content={"reason": "没有解析到疾病上下文。"},
            )

        trials = self._normalize_trials(
            self._safe_mcp_call("ctg_search_studies", {"condition": disease_query, "max_results": 8})
        )
        recruiting_trials = [trial for trial in trials if trial.get("status") == "RECRUITING"]
        content = {
            "disease_query": disease_query,
            "trials": trials,
            "recruiting_trials": recruiting_trials,
            "next_steps": [
                "优先核对招募状态与入排标准",
                "把候选试验与患者当前病程和年龄条件对应起来",
                "需要时进一步联系研究中心确认可入组性",
            ],
        }
        self._push_event(
            session,
            event_type="agent_completed",
            agent_id="trial_agent",
            headline="临床试验清单已生成",
            detail=f"试验 {len(trials)} 个，其中招募中 {len(recruiting_trials)} 个。",
            payload={"disease_query": disease_query},
        )
        return self._create_artifact(
            agent_id="trial_agent",
            artifact_type="trial_report",
            title="临床试验导航",
            content=content,
        )

    async def _run_community_agent(self, session: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        disease_label = context.get("disease_label")
        if not disease_label and context["candidate_diseases"]:
            disease_label = context["candidate_diseases"][0]["name_cn"]

        recommended = self.community_manager.get_recommended_communities(disease_label or "")
        topic_fallback = [
            community for community in self.community_manager.communities.values()
            if community.community_type.value == "按主题"
        ]
        communities = recommended[:6] if recommended else topic_fallback[:6]

        patient_profile = session.get("patient_profile") or {}
        avatar_payload = None
        if patient_profile.get("nickname"):
            avatar_payload = {
                "patient_id": patient_profile.get("patient_id") or session["session_id"],
                "nickname": patient_profile["nickname"],
                "disease_type": disease_label or context.get("disease_query") or "罕见病待确认",
                "diagnosis": disease_label or "",
                "symptoms": "、".join(context["symptoms"]),
                "age": patient_profile.get("age"),
            }

        avatar_result = None
        joined = []
        matches = []
        if avatar_payload:
            avatar = await self.secondme_client.create_avatar(avatar_payload)
            avatar_result = {
                "avatar_id": avatar.avatar_id,
                "nickname": avatar.nickname,
                "disease_type": avatar.disease_type,
                "bio": avatar.bio,
            }
            joined = self.community_manager.auto_join(
                PatientAvatar(
                    avatar_id=avatar.avatar_id,
                    patient_id=avatar.patient_id,
                    nickname=avatar.nickname,
                    disease_type=avatar.disease_type,
                    bio=avatar.bio,
                    memory_summary=avatar.memory_summary,
                    personality=avatar.personality,
                    created_at=avatar.created_at,
                )
            )
            matches = self.community_manager.find_matches(
                PatientAvatar(
                    avatar_id=avatar.avatar_id,
                    patient_id=avatar.patient_id,
                    nickname=avatar.nickname,
                    disease_type=avatar.disease_type,
                    bio=avatar.bio,
                    memory_summary=avatar.memory_summary,
                    personality=avatar.personality,
                    created_at=avatar.created_at,
                )
            )

        content = {
            "disease_label": disease_label,
            "avatar": avatar_result,
            "joined_communities": joined,
            "recommended_communities": [
                {
                    "id": community.community_id,
                    "name": community.name,
                    "type": community.community_type.value,
                    "members": community.member_count,
                    "description": community.description,
                }
                for community in communities
            ],
            "bridge_matches": matches,
            "suggested_post": (
                f"大家好，我想交流关于{disease_label or '当前疾病方向'}的病程、检查和治疗经验。"
                "如果有相似经历，欢迎分享。"
            ),
        }
        self._push_event(
            session,
            event_type="agent_completed",
            agent_id="community_agent",
            headline="患者社群建议已生成",
            detail=f"推荐社群 {len(content['recommended_communities'])} 个。",
            payload={"disease_label": disease_label},
        )
        return self._create_artifact(
            agent_id="community_agent",
            artifact_type="community_report",
            title="患者社群建议",
            content=content,
        )

    def _build_fallback_report(self, context: Dict[str, Any], artifacts: List[Dict[str, Any]]) -> str:
        lines = [
            f"当前任务焦点：{context['task_focus']}",
            f"推荐首位 Agent：{self.AGENT_CATALOG[context['recommended_lead_agent']]['label']}",
        ]
        if context.get("disease_label") or context.get("disease_query"):
            lines.append(f"疾病上下文：{context.get('disease_label') or context.get('disease_query')}")
        if context.get("symptoms"):
            lines.append(f"识别到的症状：{'、'.join(context['symptoms'])}")

        phenotype = next((artifact for artifact in artifacts if artifact["agent_id"] == "phenotype_agent"), None)
        if phenotype and phenotype["status"] == "completed":
            candidates = phenotype["content"].get("candidate_diseases", [])
            if candidates:
                top = candidates[0]
                lines.append(
                    f"候选疾病优先级：{top['name_cn']}（{top['confidence']}%），"
                    f"关键基因 {top.get('gene') or '待确认'}。"
                )

        evidence = next((artifact for artifact in artifacts if artifact["agent_id"] == "evidence_agent"), None)
        if evidence and evidence["status"] == "completed":
            target_count = len(evidence["content"].get("targets", []))
            literature_count = len(evidence["content"].get("literature", []))
            lines.append(f"证据图谱：靶点 {target_count} 个，文献 {literature_count} 篇。")

        diagnosis = next((artifact for artifact in artifacts if artifact["agent_id"] == "diagnosis_agent"), None)
        if diagnosis and diagnosis["status"] == "completed":
            ranked = diagnosis["content"].get("ranked_diagnoses", [])
            if ranked:
                top = ranked[0]
                lines.append(f"RareDBridge Dx：首位候选为 {top['name_cn']}，置信度 {top['confidence_label']}，评分 {top['score']}。")
            else:
                lines.append("RareDBridge Dx：当前输入尚不足以形成稳定差异诊断。")

        repurposing = next((artifact for artifact in artifacts if artifact["agent_id"] == "repurposing_agent"), None)
        if repurposing and repurposing["status"] == "completed":
            lines.append(f"药物重定位：候选药物 {len(repurposing['content'].get('candidate_drugs', []))} 个。")

        trial = next((artifact for artifact in artifacts if artifact["agent_id"] == "trial_agent"), None)
        if trial and trial["status"] == "completed":
            lines.append(f"临床试验：总计 {len(trial['content'].get('trials', []))} 个，招募中 {len(trial['content'].get('recruiting_trials', []))} 个。")

        community = next((artifact for artifact in artifacts if artifact["agent_id"] == "community_agent"), None)
        if community and community["status"] == "completed":
            lines.append(f"患者社群：推荐 {len(community['content'].get('recommended_communities', []))} 个互助入口。")

        lines.append("建议下一步：围绕最高优先级疾病补充检查，确认靶点与药物线索，再决定是否进入试验匹配或社群支持。")
        return "\n".join(lines)

    def _run_report_agent(
        self,
        session: Dict[str, Any],
        context: Dict[str, Any],
        artifacts: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        payload = {
            "mode": session["mode"],
            "focus": context["task_focus"],
            "urgency": context["urgency"],
            "disease_context": context.get("disease_label") or context.get("disease_query"),
            "artifacts": [
                {
                    "agent_id": artifact["agent_id"],
                    "title": artifact["title"],
                    "status": artifact["status"],
                    "content": artifact["content"],
                }
                for artifact in artifacts
                if artifact["agent_id"] != "report_agent"
            ],
        }
        report_text = self._safe_mimo_summary(
            "你是罕见病多智能体协同系统的总协调 Agent。请基于给定 JSON，输出专业且清晰的中文总报告。",
            (
                "请基于以下 A2A 执行结果生成汇总，格式包括：\n"
                "1. 当前判断\n2. 已执行链路\n3. 核心发现\n4. 下一步行动\n\n"
                f"{json.dumps(payload, ensure_ascii=False)}"
            ),
        )
        if not report_text:
            report_text = self._build_fallback_report(context, artifacts)

        assistant_message = (
            f"已完成 {len(artifacts)} 个 A2A 节点。\n\n"
            f"{report_text}"
        )

        next_steps = [
            "如要继续推进，请补充新的检查结果、疾病线索或研究目标。",
            "如果需要深挖药物和试验，可继续在当前 session 中追加问题。",
            "如需患者支持场景，可在 roundtable 模式下带入社群 Agent。",
        ]
        self._push_event(
            session,
            event_type="agent_completed",
            agent_id="report_agent",
            headline="A2A 汇总报告已生成",
            detail="会话已收束为统一摘要与行动清单。",
            payload={"focus": context["task_focus"]},
        )
        return self._create_artifact(
            agent_id="report_agent",
            artifact_type="final_report",
            title="A2A 汇总报告",
            content={
                "summary": report_text,
                "assistant_message": assistant_message,
                "next_steps": next_steps,
                "focus": context["task_focus"],
                "lead_agent": session.get("lead_agent"),
            },
        )
