"""
MediChat-RD — 医生AI助手 (Doctor Agent / Jarvis模式)
参考HealthBridge AI JarvisMD：
- 语音转写（模拟）
- 诊断建议
- 病史追踪
- 实时临床决策支持
"""
import json
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass, field

import sys
sys.path.insert(0, str(Path(__file__).parent))
from hpo_extractor import HPOExtractor
from hallucination_guard import HallucinationGuard
from lab_analyzer import LabAnalyzer
from orchestrator import OrchestratorAgent
from patient_history import PatientHistory
from report_generator import ReportGenerator


@dataclass
class ConsultationSession:
    """诊疗会话"""
    session_id: str
    patient_id: str
    doctor_id: str
    chief_complaint: str
    start_time: datetime
    transcript: List[Dict] = field(default_factory=list)  # 语音转写记录
    diagnoses: List[Dict] = field(default_factory=list)
    lab_orders: List[Dict] = field(default_factory=list)
    prescriptions: List[Dict] = field(default_factory=list)
    notes: str = ""
    status: str = "active"  # active / completed / paused


class DoctorAgent:
    """
    医生AI助手 — Jarvis模式
    像钢铁侠的Jarvis一样，辅助医生高效诊疗
    """

    def __init__(self, db_path: str = "data/doctor_agent.db"):
        self.extractor = HPOExtractor()
        self.guard = HallucinationGuard()
        self.lab_analyzer = LabAnalyzer()
        self.orchestrator = OrchestratorAgent()
        self.history = PatientHistory(db_path)
        self.report_gen = ReportGenerator()

        # 当前会话
        self.active_session: Optional[ConsultationSession] = None

        # 知识库：常见鉴别诊断建议
        self.diagnostic_suggestions = self._load_suggestions()

    def _load_suggestions(self) -> Dict:
        """加载诊断建议库"""
        return {
            "肌无力": {
                "differential": ["重症肌无力", "Lambert-Eaton综合征", "多发性肌炎"],
                "tests": ["乙酰胆碱受体抗体", "肌酶谱", "肌电图", "胸部CT（胸腺）"],
                "urgency": "medium",
                "specialty": "神经内科",
            },
            "眼睑下垂": {
                "differential": ["重症肌无力", "动眼神经麻痹", "Horner综合征"],
                "tests": ["冰试验", "新斯的明试验", "眼眶MRI"],
                "urgency": "medium",
                "specialty": "神经内科/眼科",
            },
            "肝脾肿大": {
                "differential": ["戈谢病", "尼曼匹克病", "白血病", "淋巴瘤"],
                "tests": ["血常规", "肝功能", "骨髓穿刺", "β-葡萄糖脑苷脂酶活性"],
                "urgency": "high",
                "specialty": "血液科/遗传科",
            },
            "反复骨折": {
                "differential": ["成骨不全症", "骨质疏松", "骨肿瘤"],
                "tests": ["骨密度", "X线", "基因检测（COL1A1/COL1A2）"],
                "urgency": "medium",
                "specialty": "骨科/遗传科",
            },
            "发育迟缓": {
                "differential": ["脊髓性肌萎缩症", "Duchenne肌营养不良", "苯丙酮尿症"],
                "tests": ["肌酶谱", "苯丙氨酸筛查", "基因检测（SMN1/DMD）"],
                "urgency": "high",
                "specialty": "儿科/遗传科",
            },
            "血尿": {
                "differential": ["Alport综合征", "IgA肾病", "薄基底膜肾病"],
                "tests": ["尿常规", "肾功能", "肾活检", "基因检测（COL4A）"],
                "urgency": "medium",
                "specialty": "肾内科",
            },
            "皮肤变黑": {
                "differential": ["Addison病", "血色病", "肾上腺皮质功能减退"],
                "tests": ["ACTH", "皮质醇", "铁蛋白", "转铁蛋白饱和度"],
                "urgency": "medium",
                "specialty": "内分泌科",
            },
            "心脏扩大": {
                "differential": ["法布雷病", "肥厚型心肌病", "扩张型心肌病"],
                "tests": ["心超", "心电图", "α-半乳糖苷酶活性", "基因检测（GLA）"],
                "urgency": "high",
                "specialty": "心内科",
            },
        }

    # ========== 核心功能 ==========

    def start_consultation(self, patient_id: str, doctor_id: str, chief_complaint: str) -> Dict:
        """开始诊疗会话"""
        session_id = f"consult_{uuid.uuid4().hex[:8]}"
        session = ConsultationSession(
            session_id=session_id,
            patient_id=patient_id,
            doctor_id=doctor_id,
            chief_complaint=chief_complaint,
            start_time=datetime.now(),
        )
        self.active_session = session

        # 自动分析主诉
        analysis = self._analyze_complaint(chief_complaint)

        return {
            "session_id": session_id,
            "status": "started",
            "analysis": analysis,
            "ai_suggestions": self._get_suggestions(chief_complaint),
        }

    def _analyze_complaint(self, text: str) -> Dict:
        """分析主诉"""
        # 提取HPO表型
        phenotypes = self.extractor.extract(text)

        # 解析检验值
        lab_results = self.lab_analyzer.analyze_clinical_note(text)

        # 幻觉防护验证
        hypotheses = []
        for s in text.split("，"):
            s = s.strip()
            if s:
                for disease, info in self.diagnostic_suggestions.items():
                    if disease in s:
                        hypotheses.append({"disease": info["differential"][0], "score": 70})

        symptoms_list = [p["matched_text"] for p in phenotypes]
        validated = self.guard.validate(hypotheses, symptoms_list, []) if hypotheses else []

        return {
            "phenotypes": phenotypes,
            "phenotype_count": len(phenotypes),
            "lab_results": lab_results,
            "differential_diagnosis": validated,
            "alert_level": "high" if lab_results.get("critical") else "normal",
        }

    def _get_suggestions(self, text: str) -> Dict:
        """获取AI诊疗建议"""
        suggestions = {
            "differential": [],
            "tests": [],
            "urgency": "normal",
            "specialty": "",
        }

        for keyword, info in self.diagnostic_suggestions.items():
            if keyword in text:
                suggestions["differential"].extend(info["differential"])
                suggestions["tests"].extend(info["tests"])
                if info["urgency"] == "high":
                    suggestions["urgency"] = "high"
                suggestions["specialty"] = info["specialty"]

        # 去重
        suggestions["differential"] = list(set(suggestions["differential"]))
        suggestions["tests"] = list(set(suggestions["tests"]))

        return suggestions

    # ========== 语音转写（模拟） ==========

    def transcript_add(self, speaker: str, text: str, timestamp: Optional[str] = None):
        """添加转写记录"""
        if not self.active_session:
            return {"error": "无活跃会话"}

        entry = {
            "speaker": speaker,  # doctor / patient
            "text": text,
            "timestamp": timestamp or datetime.now().strftime("%H:%M:%S"),
        }
        self.active_session.transcript.append(entry)

        # 实时分析患者发言
        if speaker == "patient":
            analysis = self._analyze_complaint(text)
            if analysis["phenotype_count"] > 0 or analysis["alert_level"] == "high":
                return {
                    "entry": entry,
                    "ai_alert": True,
                    "analysis": analysis,
                    "suggestion": self._get_suggestions(text),
                }

        return {"entry": entry, "ai_alert": False}

    # ========== 诊断建议 ==========

    def get_diagnostic_support(self, query: str) -> Dict:
        """获取诊断支持"""
        # 1. 提取症状
        analysis = self._analyze_complaint(query)

        # 2. 运行多Agent编排
        orchestrator_result = self.orchestrator.diagnose(query)

        # 3. 综合AI建议
        suggestions = self._get_suggestions(query)

        return {
            "query": query,
            "hpo_phenotypes": analysis["phenotypes"],
            "differential_diagnosis": analysis["differential_diagnosis"],
            "lab_alerts": analysis["lab_results"].get("clinical_alerts", []),
            "orchestrator": orchestrator_result,
            "ai_suggestions": suggestions,
        }

    # ========== 检查建议 ==========

    def suggest_tests(self, symptoms: List[str], suspected_disease: str = "") -> List[Dict]:
        """根据症状和疑似疾病推荐检查"""
        recommended = []

        # 基于症状
        for symptom in symptoms:
            for keyword, info in self.diagnostic_suggestions.items():
                if keyword in symptom:
                    for test in info["tests"]:
                        if test not in [t["name"] for t in recommended]:
                            recommended.append({
                                "name": test,
                                "reason": f"症状：{symptom}",
                                "priority": "高" if info["urgency"] == "high" else "中",
                            })

        # 基于疑似疾病
        if suspected_disease:
            for keyword, info in self.diagnostic_suggestions.items():
                if suspected_disease in info["differential"]:
                    for test in info["tests"]:
                        if test not in [t["name"] for t in recommended]:
                            recommended.append({
                                "name": test,
                                "reason": f"疑似诊断：{suspected_disease}",
                                "priority": "高",
                            })

        return recommended

    # ========== 病历生成 ==========

    def generate_note(self) -> Dict:
        """生成当前会话的病历"""
        if not self.active_session:
            return {"error": "无活跃会话"}

        s = self.active_session

        note = f"""门诊病历
{'='*40}
会话ID: {s.session_id}
时间: {s.start_time.strftime('%Y-%m-%d %H:%M')}
主诉: {s.chief_complaint}

{'='*40}
问诊记录
{'='*40}
"""
        for entry in s.transcript:
            role = "医生" if entry["speaker"] == "doctor" else "患者"
            note += f"[{entry['timestamp']}] {role}: {entry['text']}\n"

        if s.diagnoses:
            note += f"\n{'='*40}\n诊断\n{'='*40}\n"
            for d in s.diagnoses:
                note += f"  • {d['disease']} ({d.get('confidence', '?')}%)\n"

        if s.lab_orders:
            note += f"\n{'='*40}\n检查医嘱\n{'='*40}\n"
            for lab in s.lab_orders:
                note += f"  • {lab['name']} [{lab.get('priority', '常规')}]\n"

        return {
            "note": note,
            "session_id": s.session_id,
            "format": "text",
        }

    # ========== 统计 ==========

    def get_stats(self) -> Dict:
        """获取统计信息"""
        return {
            "active_session": self.active_session.session_id if self.active_session else None,
            "diagnostic_knowledge_base": len(self.diagnostic_suggestions),
            "hpo_terms": self.extractor.stats(),
            "history_stats": self.history.get_stats(),
        }


# ========== 测试 ==========
if __name__ == "__main__":
    agent = DoctorAgent("/tmp/test_doctor_agent.db")

    print("=" * 60)
    print("🤖 医生AI助手 — Jarvis模式测试")
    print("=" * 60)

    # 1. 开始诊疗
    r = agent.start_consultation("p_test", "doctor_001", "患者眼睑下垂、吞咽困难3个月")
    print(f"\n📋 会话ID: {r['session_id']}")
    print(f"🔍 分析: {r['analysis']['phenotype_count']}个表型")
    print(f"🚨 警报级别: {r['analysis']['alert_level']}")

    # 2. AI建议
    s = r['ai_suggestions']
    print(f"\n💡 AI建议:")
    print(f"   鉴别诊断: {', '.join(s['differential'][:3])}")
    print(f"   建议检查: {', '.join(s['tests'][:4])}")
    print(f"   推荐专科: {s['specialty']}")

    # 3. 语音转写（模拟）
    r2 = agent.transcript_add("patient", "医生，我最近腿上有一些紫红色的斑点")
    print(f"\n🎙️ 转写: {r2['entry']['text']}")
    print(f"   AI警报: {r2['ai_alert']}")

    # 4. 生成病历
    note = agent.generate_note()
    print(f"\n📝 病历生成: {len(note['note'])}字")

    # 5. 检查建议
    tests = agent.suggest_tests(["眼睑下垂", "吞咽困难"], "重症肌无力")
    print(f"\n🔬 推荐检查:")
    for t in tests[:3]:
        print(f"   {t['name']} [{t['priority']}] — {t['reason']}")
