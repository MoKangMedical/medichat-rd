"""
MediChat-RD — 诊断报告生成器
参考RarePath AI：生成医生可读的诊断报告
"""
import json
from typing import Dict, List, Optional
from datetime import datetime


class ReportGenerator:
    """诊断报告生成器"""

    def generate(self, result: Dict, patient_info: Optional[Dict] = None) -> str:
        """生成完整诊断报告"""
        sections = []

        # 报告头
        sections.append(self._header(patient_info))

        # 主诉
        sections.append(self._chief_complaint(result))

        # 表型提取
        sections.append(self._phenotypes(result))

        # 实验室检验
        sections.append(self._lab_results(result))

        # 鉴别诊断
        sections.append(self._differential_diagnosis(result))

        # 推荐检查
        sections.append(self._recommended_tests(result))

        # 临床试验
        sections.append(self._clinical_trials(result))

        # 推荐专科
        sections.append(self._specialists(result))

        # 结论
        sections.append(self._conclusion(result))

        # 报告尾
        sections.append(self._footer())

        return "\n\n".join(sections)

    def _header(self, patient_info: Optional[Dict]) -> str:
        now = datetime.now().strftime("%Y年%m月%d日 %H:%M")
        patient_str = ""
        if patient_info:
            patient_str = f"患者：{patient_info.get('nickname', '未知')} | "
            if patient_info.get("age"):
                patient_str += f"{patient_info['age']}岁 | "
            if patient_info.get("gender"):
                patient_str += f"{'男' if patient_info['gender'] == 'male' else '女'} | "

        return f"""{'=' * 60}
📋 MediChat-RD 智能诊断报告
{'=' * 60}
{patient_str}生成时间：{now}
报告ID：{datetime.now().strftime('%Y%m%d%H%M%S')}
⚠️ 本报告仅供参考，不作为临床诊断依据"""

    def _chief_complaint(self, result: Dict) -> str:
        input_text = result.get("patient_input", "")
        return f"""📝 主诉
{'-' * 40}
{input_text}"""

    def _phenotypes(self, result: Dict) -> str:
        stages = result.get("stages", {})
        symptoms = stages.get("symptoms", {})
        phenotypes = symptoms.get("extracted_phenotypes", [])

        if not phenotypes:
            return "🧬 表型提取\n" + "-" * 40 + "\n未提取到HPO表型"

        lines = [f"🧬 表型提取（共{len(phenotypes)}个）"]
        lines.append("-" * 40)
        for p in phenotypes:
            lines.append(f"  • {p.get('hpo_id', '?')} {p.get('name', '?')} ← \"{p.get('matched_text', '?')}\"")

        return "\n".join(lines)

    def _lab_results(self, result: Dict) -> str:
        stages = result.get("stages", {})
        analysis = stages.get("analysis", {})
        lab = analysis.get("lab_results", {})

        if not lab or lab.get("total", 0) == 0:
            return ""

        lines = ["🔬 实验室检验"]
        lines.append("-" * 40)

        # 危急值
        critical = lab.get("critical", [])
        if critical:
            lines.append("🔴 危急值：")
            for c in critical:
                lines.append(f"   {c['name']}: {c['value']} {c['unit']} (参考: {c['reference']})")

        # 所有结果
        for r in lab.get("results", []):
            lines.append(f"  {r['status_text']} {r['name']}: {r['value']} {r['unit']} (参考: {r['reference']})")

        return "\n".join(lines)

    def _differential_diagnosis(self, result: Dict) -> str:
        stages = result.get("stages", {})
        analysis = stages.get("analysis", {})
        diagnoses = analysis.get("differential_diagnosis", [])

        if not diagnoses:
            return ""

        lines = ["💡 鉴别诊断"]
        lines.append("-" * 40)
        for i, d in enumerate(diagnoses[:5], 1):
            gene = d.get("gene", "-")
            inh = d.get("inheritance", "-")
            lines.append(f"  {i}. {d['disease']} ({d['score']}%)")
            if gene and gene != "-":
                lines.append(f"     基因: {gene} | 遗传方式: {inh}")
            if d.get("layer_results"):
                for e in d["layer_results"][:2]:
                    lines.append(f"     {e}")

        return "\n".join(lines)

    def _recommended_tests(self, result: Dict) -> str:
        stages = result.get("stages", {})
        analysis = stages.get("analysis", {})
        diagnoses = analysis.get("differential_diagnosis", [])

        if not diagnoses:
            return ""

        top = diagnoses[0]
        tests = []

        if top.get("gene") and top["gene"] != "-":
            tests.append(f"🧬 {top['gene']}基因检测")

        # 基于症状的推荐
        symptoms = result.get("stages", {}).get("symptoms", {}).get("extracted_phenotypes", [])
        for s in symptoms:
            if "肌" in s.get("name", "") or "肌" in s.get("matched_text", ""):
                tests.append("📊 肌酶谱（CK, LDH, AST）")
                tests.append("⚡ 肌电图")
            if "眼" in s.get("name", "") or "眼" in s.get("matched_text", ""):
                tests.append("👁️ 眼科会诊")

        if tests:
            lines = ["📋 建议检查"]
            lines.append("-" * 40)
            for t in set(tests):
                lines.append(f"  {t}")
            return "\n".join(lines)
        return ""

    def _clinical_trials(self, result: Dict) -> str:
        stages = result.get("stages", {})
        trials = stages.get("clinical_trials", {})
        matched = trials.get("matched_trials", [])

        if not matched:
            return ""

        lines = ["🧪 相关临床试验"]
        lines.append("-" * 40)
        for t in matched[:3]:
            lines.append(f"  • {t['nct_id']}: {t['title']}")
            lines.append(f"    阶段: {t['phase']} | 状态: {t['status']}")

        return "\n".join(lines)

    def _specialists(self, result: Dict) -> str:
        stages = result.get("stages", {})
        specialists = stages.get("specialists", {})
        matched = specialists.get("matched_specialists", [])

        if not matched:
            return ""

        lines = ["🏥 推荐专科"]
        lines.append("-" * 40)
        for s in matched[:3]:
            lines.append(f"  • {s['name']} - {s['department']}")
            lines.append(f"    擅长: {', '.join(s['specialty'][:3])}")

        return "\n".join(lines)

    def _conclusion(self, result: Dict) -> str:
        stages = result.get("stages", {})
        analysis = stages.get("analysis", {})
        conclusion = analysis.get("conclusion", "")
        alerts = analysis.get("critical_alerts", [])

        lines = ["💡 诊断意见"]
        lines.append("-" * 40)
        lines.append(conclusion or "当前信息不足以做出鉴别诊断")

        if alerts:
            lines.append("")
            lines.append("⚠️ 临床警报：")
            for a in alerts:
                lines.append(f"  {a}")

        return "\n".join(lines)

    def _footer(self) -> str:
        return f"""{'=' * 60}
⚠️ 免责声明
本报告由MediChat-RD AI系统自动生成，仅供参考。
不作为临床诊断或治疗的依据。
如需专业医疗意见，请咨询执业医师。

MediChat-RD | Nature DeepRare架构 | 多Agent协作
{'=' * 60}"""

    def to_json(self, result: Dict, patient_info: Optional[Dict] = None) -> Dict:
        """生成JSON格式报告"""
        return {
            "report_id": datetime.now().strftime('%Y%m%d%H%M%S'),
            "generated_at": datetime.now().isoformat(),
            "patient_info": patient_info,
            "chief_complaint": result.get("patient_input", ""),
            "stages": result.get("stages", {}),
            "execution_time_ms": result.get("execution_time_ms", 0),
        }


# ========== 测试 ==========
if __name__ == "__main__":
    generator = ReportGenerator()

    # 模拟诊断结果
    fake_result = {
        "patient_input": "患者女性，35岁，眼睑下垂，吞咽困难，全身无力",
        "execution_time_ms": 1250,
        "stages": {
            "symptoms": {
                "extracted_phenotypes": [
                    {"hpo_id": "HP:0000508", "name": "Ptosis", "matched_text": "眼睑下垂"},
                    {"hpo_id": "HP:0002015", "name": "Dysphagia", "matched_text": "吞咽困难"},
                ],
                "hpo_ids": ["HP:0000508", "HP:0002015"],
                "phenotype_count": 2,
            },
            "analysis": {
                "differential_diagnosis": [
                    {"disease": "重症肌无力", "score": 95, "gene": "-", "inheritance": "多因素", 
                     "layer_results": ["✅ Orphanet验证通过 (ORPHA:702)", "✅ Layer 2: 匹配3个典型症状 (+30%)"]},
                    {"disease": "线粒体脑肌病", "score": 45, "gene": "-", "inheritance": "多种"},
                ],
                "lab_results": {
                    "total": 3,
                    "results": [
                        {"name": "CK", "value": 850, "unit": "U/L", "reference": "26-196", "status": "high", "status_text": "⚠️偏高"},
                        {"name": "肌钙蛋白", "value": 0.8, "unit": "ng/mL", "reference": "0-0.04", "status": "critical_high", "status_text": "🔴危急高值"},
                    ],
                    "critical": [
                        {"name": "肌钙蛋白", "value": 0.8, "unit": "ng/mL", "reference": "0-0.04"},
                    ],
                },
                "conclusion": "高度怀疑重症肌无力（置信度95%），建议针对性检查",
                "critical_alerts": ["🔴 危急值: 肌钙蛋白 = 0.8ng/mL (参考: 0-0.04)"],
            },
            "clinical_trials": {
                "matched_trials": [
                    {"nct_id": "NCT04500001", "title": "ASO疗法重症肌无力I期", "phase": "Phase I", "status": "Recruiting"},
                ],
            },
            "specialists": {
                "matched_specialists": [
                    {"name": "北京协和医院", "department": "神经内科", "specialty": ["重症肌无力"]},
                ],
            },
        },
    }

    report = generator.generate(fake_result, {"nickname": "张女士", "age": 35, "gender": "female"})
    print(report)
