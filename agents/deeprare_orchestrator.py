"""
MediChat-RD DeepRare模式 — 多Agent诊断编排器
三层架构：Host编排 → Agent服务器 → 外部数据源
参考DeepRare Nature论文的核心架构
"""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from hpo_extractor import HPOExtractor
from knowledge_retriever import KnowledgeRetriever, SelfReflectiveDiagnostic, ReasoningChain


class DeepRareOrchestrator:
    """
    多Agent诊断编排器
    参考DeepRare三层架构：
    - Tier 1: 中央Host（本类）— 编排+记忆+自反思
    - Tier 2: 专业Agent（HPO提取器、知识检索器）
    - Tier 3: 外部数据源（PubMed、Orphanet、OMIM等）
    """

    def __init__(self):
        self.hpo_extractor = HPOExtractor()
        self.knowledge_retriever = KnowledgeRetriever()
        self.diagnostic_engine = SelfReflectiveDiagnostic(
            self.hpo_extractor, self.knowledge_retriever
        )
        self.memory = []  # 长期记忆（对话历史）

    def diagnose(self, patient_input, context=None):
        """
        完整诊断流程
        1. 接收患者输入
        2. 表型提取（HPO标准化）
        3. 多源知识检索
        4. 假设生成
        5. 自反思验证
        6. 输出可追溯推理链
        """
        # 保存到记忆
        self.memory.append({
            "role": "patient",
            "content": patient_input,
            "timestamp": time.strftime("%H:%M:%S"),
        })

        # 合并上下文
        full_input = patient_input
        if context:
            full_input = f"{context}\n\n{patient_input}"

        # 执行诊断
        result = self.diagnostic_engine.diagnose(full_input)

        # 保存结果到记忆
        self.memory.append({
            "role": "system",
            "content": result["reasoning_chain"],
            "timestamp": time.strftime("%H:%M:%S"),
        })

        # 格式化输出
        output = self._format_output(result, patient_input)
        return output

    def follow_up(self, question):
        """追问模式 — 基于已有上下文回答"""
        context = "\n".join(
            f"[{m['role']}] {m['content']}" for m in self.memory[-6:]
        )
        return self.diagnose(question, context)

    def _format_output(self, result, patient_input):
        """格式化输出为用户友好的报告"""
        phenotype = result["phenotype_analysis"]
        hypotheses = result["hypotheses"]

        report = {
            "summary": {
                "patient_input": patient_input,
                "phenotypes_found": phenotype["phenotype_count"],
                "systems_involved": phenotype["systems_involved"],
                "multi_system": phenotype["multi_system"],
            },
            "phenotypes": [
                {
                    "hpo_id": p["hpo_id"],
                    "name": p["name"],
                    "matched": p["matched_text"],
                    "confidence": p["confidence"],
                }
                for p in phenotype["extracted_phenotypes"]
            ],
            "differential_diagnosis": [
                {
                    "rank": i + 1,
                    "disease": h["disease"],
                    "confidence": f"{h['score']}%",
                    "reasoning": h["reasoning"],
                }
                for i, h in enumerate(hypotheses[:5])
            ],
            "reasoning_chain": result["reasoning_chain"],
            "recommendations": self._generate_recommendations(phenotype, hypotheses),
        }

        return report

    def _generate_recommendations(self, phenotype, hypotheses):
        """生成建议检查和下一步"""
        recs = []

        if phenotype["multi_system"]:
            recs.append("🔬 多系统受累，建议全面检查")

        system_recs = {
            "神经系统": "建议神经科就诊，完善肌电图、脑MRI",
            "肌肉骨骼": "建议肌酶谱检查、肌肉活检",
            "皮肤": "建议皮肤科会诊，必要时皮肤活检",
            "眼部": "建议眼科检查，裂隙灯检查",
            "心血管": "建议心电图、超声心动图",
            "消化系统": "建议腹部超声、肝功能检查",
            "泌尿系统": "建议尿常规、肾功能检查",
            "肾脏": "建议肾功能、肾脏超声",
        }

        for system in phenotype["systems_involved"]:
            if system in system_recs:
                recs.append(f"📋 {system}: {system_recs[system]}")

        if hypotheses:
            top = hypotheses[0]
            if top["score"] >= 50:
                recs.append(f"🎯 高度怀疑 {top['disease']}，建议针对性基因检测")
            elif top["score"] >= 30:
                recs.append(f"💡 考虑 {top['disease']}，建议进一步检查排除")

        return recs

    def to_text_report(self, report):
        """转为文本报告"""
        lines = []
        lines.append("=" * 50)
        lines.append("📋 MediChat-RD 诊断分析报告")
        lines.append("=" * 50)

        # 表型
        lines.append(f"\n👁️ 提取到 {report['summary']['phenotypes_found']} 个表型:")
        for p in report["phenotypes"]:
            lines.append(f"   • {p['hpo_id']} {p['name']} (原文: \"{p['matched']}\")")

        # 涉及系统
        if report["summary"]["systems_involved"]:
            lines.append(f"\n🏥 涉及系统: {', '.join(report['summary']['systems_involved'])}")

        # 鉴别诊断
        lines.append(f"\n💡 鉴别诊断:")
        for d in report["differential_diagnosis"]:
            lines.append(f"   {d['rank']}. {d['disease']} ({d['confidence']})")

        # 推荐
        if report["recommendations"]:
            lines.append(f"\n📌 建议:")
            for r in report["recommendations"]:
                lines.append(f"   {r}")

        # 推理链
        lines.append(f"\n{'=' * 50}")
        lines.append("🔗 可追溯推理链:")
        lines.append(report["reasoning_chain"])

        return "\n".join(lines)


# ========== API接口 ==========
def create_api_handler(orchestrator=None):
    """创建HTTP API处理器"""
    if orchestrator is None:
        orchestrator = DeepRareOrchestrator()

    def handle_request(method, path, body=None):
        if path == "/api/deeprare/diagnose" and method == "POST":
            text = body.get("text", "") if body else ""
            result = orchestrator.diagnose(text)
            return {"ok": True, "result": result}

        elif path == "/api/deeprare/follow-up" and method == "POST":
            question = body.get("question", "") if body else ""
            result = orchestrator.follow_up(question)
            return {"ok": True, "result": result}

        elif path == "/api/deeprare/history" and method == "GET":
            return {"ok": True, "memory": orchestrator.memory}

        return {"error": "not found"}

    return handle_request


# ========== 测试 ==========
if __name__ == "__main__":
    orchestrator = DeepRareOrchestrator()

    # 测试案例
    test_cases = [
        "我最近眼睑下垂，吞咽困难，全身无力，说话也不清楚了，下午特别明显",
        "孩子3岁，发育迟缓，经常抽搐，走路不稳",
    ]

    for text in test_cases:
        print(f"\n{'=' * 60}")
        print(f"📝 患者: {text}")
        report = orchestrator.diagnose(text)
        print(orchestrator.to_text_report(report))
