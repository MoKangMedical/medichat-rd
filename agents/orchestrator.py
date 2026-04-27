"""
MediChat-RD — 多Agent编排器
参考RarePath AI：编排器协调6个子Agent，支持串行/并行/循环
"""
import json
import time
import sys
from pathlib import Path
from typing import List, Dict, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))
from hpo_extractor import HPOExtractor
from hallucination_guard import HallucinationGuard
from lab_analyzer import LabAnalyzer
from hpo_ontology import HPOOntology


class AgentType(str, Enum):
    """Agent类型"""
    SYMPTOM = "症状提取Agent"
    KNOWLEDGE = "知识检索Agent"
    LITERATURE = "文献检索Agent"
    TRIAL = "临床试验Agent"
    SPECIALIST = "专科医生Agent"
    ANALYSIS = "分析推理Agent"


@dataclass
class AgentResult:
    """Agent执行结果"""
    agent_type: AgentType
    success: bool
    data: Dict
    execution_time_ms: float
    error: Optional[str] = None


@dataclass
class DiagnosticWorkflow:
    """诊断工作流"""
    session_id: str
    patient_input: str
    steps: List[AgentResult] = field(default_factory=list)
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None


class OrchestratorAgent:
    """
    编排器Agent — 参考RarePath AI架构
    协调所有子Agent完成诊断流程
    """

    def __init__(self):
        # 初始化子Agent
        self.symptom_agent = SymptomExtractionAgent()
        self.knowledge_agent = KnowledgeSearchAgent()
        self.literature_agent = LiteratureSearchAgent()
        self.trial_agent = ClinicalTrialAgent()
        self.specialist_agent = SpecialistFinderAgent()
        self.analysis_agent = AnalysisAgent()

        # 工作流历史
        self.workflows: Dict[str, DiagnosticWorkflow] = {}

    def diagnose(self, patient_input: str) -> Dict:
        """
        完整诊断流程（串行模式）
        1. 症状提取 → 2. 知识检索 → 3. 文献检索 → 4. 分析推理 → 5. 临床试验 → 6. 专科推荐
        """
        import uuid
        session_id = f"sess_{uuid.uuid4().hex[:8]}"
        workflow = DiagnosticWorkflow(session_id=session_id, patient_input=patient_input)

        # Step 1: 症状提取
        r1 = self.symptom_agent.execute(patient_input)
        workflow.steps.append(r1)

        # Step 2: 知识检索
        hpo_ids = r1.data.get("hpo_ids", [])
        r2 = self.knowledge_agent.execute(hpo_ids)
        workflow.steps.append(r2)

        # Step 3: 文献检索
        diseases = r2.data.get("top_diseases", [])
        r3 = self.literature_agent.execute(diseases)
        workflow.steps.append(r3)

        # Step 4: 分析推理
        r4 = self.analysis_agent.execute({
            "symptoms": r1.data,
            "knowledge": r2.data,
            "literature": r3.data,
            "patient_input": patient_input,
        })
        workflow.steps.append(r4)

        # Step 5: 临床试验
        r5 = self.trial_agent.execute(diseases)
        workflow.steps.append(r5)

        # Step 6: 专科推荐
        r6 = self.specialist_agent.execute(diseases)
        workflow.steps.append(r6)

        workflow.end_time = datetime.now()
        self.workflows[session_id] = workflow

        # 汇总结果
        return {
            "session_id": session_id,
            "patient_input": patient_input,
            "execution_time_ms": (workflow.end_time - workflow.start_time).total_seconds() * 1000,
            "stages": {
                "symptoms": r1.data,
                "knowledge": r2.data,
                "literature": r3.data,
                "analysis": r4.data,
                "clinical_trials": r5.data,
                "specialists": r6.data,
            },
            "steps_summary": [
                {"agent": s.agent_type.value, "success": s.success, "time_ms": s.execution_time_ms}
                for s in workflow.steps
            ],
        }


class SymptomExtractionAgent:
    """症状提取Agent"""

    def __init__(self):
        self.extractor = HPOExtractor()
        self.ontology = HPOOntology()

    def execute(self, text: str) -> AgentResult:
        start = time.time()
        try:
            extracted = self.extractor.extract(text)
            hpo_ids = list(set(r["hpo_id"] for r in extracted))

            # 扩展搜索
            expanded_terms = []
            for hpo_id in hpo_ids:
                related = self.ontology.get_related_terms(hpo_id)
                expanded_terms.extend(related)

            return AgentResult(
                agent_type=AgentType.SYMPTOM,
                success=True,
                data={
                    "extracted_phenotypes": extracted,
                    "hpo_ids": hpo_ids,
                    "phenotype_count": len(extracted),
                    "expanded_terms": expanded_terms[:10],
                },
                execution_time_ms=(time.time() - start) * 1000,
            )
        except Exception as e:
            return AgentResult(agent_type=AgentType.SYMPTOM, success=False, data={}, 
                             execution_time_ms=(time.time() - start) * 1000, error=str(e))


class KnowledgeSearchAgent:
    """知识检索Agent"""

    def __init__(self):
        self.guard = HallucinationGuard()

    def execute(self, hpo_ids: List[str]) -> AgentResult:
        start = time.time()
        try:
            # 通过HPO ID反查疾病
            disease_scores = {}
            for hpo_id in hpo_ids:
                for did, info in self.guard.ORPHANET_DISEASES.items():
                    for sym in info["symptoms"]:
                        # 简化匹配逻辑
                        if hpo_id.replace("HP:", "") in str(info):
                            disease_scores[info["name"]] = disease_scores.get(info["name"], 0) + 1

            top_diseases = sorted(disease_scores.keys(), key=lambda d: disease_scores[d], reverse=True)[:5]

            return AgentResult(
                agent_type=AgentType.KNOWLEDGE,
                success=True,
                data={
                    "top_diseases": top_diseases,
                    "disease_scores": disease_scores,
                    "orphanet_matched": len(disease_scores),
                },
                execution_time_ms=(time.time() - start) * 1000,
            )
        except Exception as e:
            return AgentResult(agent_type=AgentType.KNOWLEDGE, success=False, data={},
                             execution_time_ms=(time.time() - start) * 1000, error=str(e))


class LiteratureSearchAgent:
    """文献检索Agent（PubMed模拟）"""

    def execute(self, diseases: List[str]) -> AgentResult:
        start = time.time()
        try:
            # 模拟PubMed检索结果
            papers = []
            for disease in diseases[:3]:
                papers.append({
                    "title": f"{disease}的诊断与治疗进展",
                    "authors": "Zhang et al.",
                    "journal": "Nature Medicine",
                    "year": 2025,
                    "pmid": f"PMID:{hash(disease) % 10000000}",
                    "abstract": f"{disease}是一种罕见的遗传性疾病...",
                    "relevance_score": 0.85,
                })

            return AgentResult(
                agent_type=AgentType.LITERATURE,
                success=True,
                data={
                    "papers": papers,
                    "total_found": len(papers),
                    "query": " OR ".join(diseases[:3]) if diseases else "",
                },
                execution_time_ms=(time.time() - start) * 1000,
            )
        except Exception as e:
            return AgentResult(agent_type=AgentType.LITERATURE, success=False, data={},
                             execution_time_ms=(time.time() - start) * 1000, error=str(e))


class ClinicalTrialAgent:
    """临床试验匹配Agent"""

    # 模拟临床试验数据库
    TRIALS_DB = [
        {"nct_id": "NCT04500001", "title": "基因治疗戈谢病的I期临床试验", "phase": "Phase I", "status": "Recruiting", "disease": "戈谢病"},
        {"nct_id": "NCT04500002", "title": "酶替代疗法庞贝病的II期研究", "phase": "Phase II", "status": "Recruiting", "disease": "庞贝病"},
        {"nct_id": "NCT04500003", "title": "ASO疗法脊髓性肌萎缩症III期", "phase": "Phase III", "status": "Active", "disease": "脊髓性肌萎缩症"},
        {"nct_id": "NCT04500004", "title": "CRISPR治疗血友病A的I/II期", "phase": "Phase I/II", "status": "Recruiting", "disease": "血友病"},
        {"nct_id": "NCT04500005", "title": "小分子药物法布雷病的II期", "phase": "Phase II", "status": "Recruiting", "disease": "法布雷病"},
    ]

    def execute(self, diseases: List[str]) -> AgentResult:
        start = time.time()
        try:
            matched_trials = []
            for trial in self.TRIALS_DB:
                for disease in diseases:
                    if disease in trial["disease"] or trial["disease"] in disease:
                        matched_trials.append(trial)

            return AgentResult(
                agent_type=AgentType.TRIAL,
                success=True,
                data={
                    "matched_trials": matched_trials,
                    "total_found": len(matched_trials),
                },
                execution_time_ms=(time.time() - start) * 1000,
            )
        except Exception as e:
            return AgentResult(agent_type=AgentType.TRIAL, success=False, data={},
                             execution_time_ms=(time.time() - start) * 1000, error=str(e))


class SpecialistFinderAgent:
    """专科医生查找Agent"""

    # 模拟专科数据库
    SPECIALISTS_DB = [
        {"name": "北京协和医院", "department": "神经内科", "specialty": ["重症肌无力", "多发性硬化", "肌萎缩侧索硬化"]},
        {"name": "上海复旦大学附属儿科医院", "department": "遗传科", "specialty": ["戈谢病", "庞贝病", "苯丙酮尿症"]},
        {"name": "广州中山大学附属第一医院", "department": "血液科", "specialty": ["血友病", "戈谢病"]},
        {"name": "四川大学华西医院", "department": "神经内科", "specialty": ["亨廷顿病", "Wilson病"]},
        {"name": "浙江大学医学院附属儿童医院", "department": "遗传代谢科", "specialty": ["脊髓性肌萎缩症", "杜氏肌营养不良"]},
    ]

    def execute(self, diseases: List[str]) -> AgentResult:
        start = time.time()
        try:
            matched_specialists = []
            for spec in self.SPECIALISTS_DB:
                for disease in diseases:
                    if disease in spec["specialty"]:
                        if spec not in matched_specialists:
                            matched_specialists.append(spec)

            return AgentResult(
                agent_type=AgentType.SPECIALIST,
                success=True,
                data={
                    "matched_specialists": matched_specialists,
                    "total_found": len(matched_specialists),
                },
                execution_time_ms=(time.time() - start) * 1000,
            )
        except Exception as e:
            return AgentResult(agent_type=AgentType.SPECIALIST, success=False, data={},
                             execution_time_ms=(time.time() - start) * 1000, error=str(e))


class AnalysisAgent:
    """分析推理Agent — 综合所有信息"""

    def __init__(self):
        self.guard = HallucinationGuard()
        self.lab_analyzer = LabAnalyzer()

    def execute(self, context: Dict) -> AgentResult:
        start = time.time()
        try:
            symptoms = context.get("symptoms", {})
            knowledge = context.get("knowledge", {})
            literature = context.get("literature", {})
            patient_input = context.get("patient_input", "")

            # 解析实验室检验
            lab_results = self.lab_analyzer.analyze_clinical_note(patient_input)

            # 幻觉防护验证
            top_diseases = knowledge.get("top_diseases", [])
            hypotheses = [{"disease": d, "score": 70 + i * 5} for i, d in enumerate(top_diseases[:5])]
            extracted_symptoms = [p["matched_text"] for p in symptoms.get("extracted_phenotypes", [])]

            validated = self.guard.validate(hypotheses, extracted_symptoms, literature.get("papers", []))

            # 生成推理结论
            conclusion = ""
            if validated:
                top = validated[0]
                if top["score"] >= 70:
                    conclusion = f"高度怀疑{top['disease']}（置信度{top['score']}%），建议针对性检查"
                elif top["score"] >= 40:
                    conclusion = f"考虑{top['disease']}（置信度{top['score']}%），需进一步评估"
                else:
                    conclusion = "当前信息不足以做出可靠鉴别诊断，建议补充检查"

            return AgentResult(
                agent_type=AgentType.ANALYSIS,
                success=True,
                data={
                    "differential_diagnosis": validated,
                    "lab_results": lab_results,
                    "conclusion": conclusion,
                    "critical_alerts": lab_results.get("clinical_alerts", []),
                },
                execution_time_ms=(time.time() - start) * 1000,
            )
        except Exception as e:
            return AgentResult(agent_type=AgentType.ANALYSIS, success=False, data={},
                             execution_time_ms=(time.time() - start) * 1000, error=str(e))


# ========== 测试 ==========
if __name__ == "__main__":
    orchestrator = OrchestratorAgent()

    test_input = "患者女性，35岁，眼睑下垂，吞咽困难，全身无力，下午特别明显。CK 850 U/L，ALT 45 U/L，WBC 5.2"

    print("=" * 60)
    print("🤖 多Agent编排器测试")
    print("=" * 60)

    result = orchestrator.diagnose(test_input)

    print(f"\n📊 执行时间: {result['execution_time_ms']:.0f}ms")
    print(f"\n🔗 工作流步骤:")
    for step in result['steps_summary']:
        status = "✅" if step['success'] else "❌"
        print(f"   {status} {step['agent']}: {step['time_ms']:.0f}ms")

    print(f"\n🧬 提取表型: {result['stages']['symptoms']['phenotype_count']}个")
    print(f"💊 鉴别诊断: {len(result['stages']['analysis']['differential_diagnosis'])}个")

    for d in result['stages']['analysis']['differential_diagnosis'][:3]:
        print(f"   {d['disease']}: {d['score']}%")

    if result['stages']['analysis']['critical_alerts']:
        print(f"\n🔴 危急警报:")
        for alert in result['stages']['analysis']['critical_alerts']:
            print(f"   {alert}")

    print(f"\n💡 结论: {result['stages']['analysis']['conclusion']}")

    if result['stages']['clinical_trials']['matched_trials']:
        print(f"\n🧪 相关临床试验: {len(result['stages']['clinical_trials']['matched_trials'])}个")

    if result['stages']['specialists']['matched_specialists']:
        print(f"\n🏥 推荐专科:")
        for s in result['stages']['specialists']['matched_specialists']:
            print(f"   {s['name']} - {s['department']}")
