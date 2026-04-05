"""
MediChat-RD DeepRare模式 — 知识检索Agent
整合PubMed + Orphanet + OMIM多源检索
参考DeepRare：Knowledge Searcher + Case Searcher
"""
import json
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import time
from pathlib import Path

# MCP端点
MCP_BASE = "http://mcp.cloud.curiloo.com"


class KnowledgeRetriever:
    """知识检索Agent — 参考DeepRare Knowledge Searcher"""

    def __init__(self, mcp_base=None):
        self.mcp_base = mcp_base or MCP_BASE
        self.cache = {}

    # ========== PubMed检索 ==========
    def search_pubmed(self, query, max_results=5):
        """通过MCP端点检索PubMed"""
        cache_key = f"pubmed:{query}:{max_results}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        try:
            # 通过MCP端点调用
            payload = json.dumps({
                "query": query,
                "max_results": max_results,
            }).encode()

            req = urllib.request.Request(
                f"{self.mcp_base}/tool/call",
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            resp = urllib.request.urlopen(req, timeout=15)
            result = json.loads(resp.read())

            papers = result.get("results", [])
            self.cache[cache_key] = papers
            return papers

        except Exception as e:
            return [{"error": str(e), "source": "pubmed"}]

    # ========== Orphanet检索 ==========
    def search_orphanet(self, hpo_ids):
        """通过HPO ID检索Orphanet罕见病"""
        diseases = []
        for hpo_id in hpo_ids[:5]:  # 限制数量
            try:
                # Orphanet API: HPO → 疾病
                url = f"https://api.orphacode.org/EN/ClinicalEntity/orphaCode/hpo/{hpo_id}/all"
                req = urllib.request.Request(url, headers={"Accept": "application/json"})
                resp = urllib.request.urlopen(req, timeout=10)
                data = json.loads(resp.read())
                if isinstance(data, list):
                    diseases.extend(data[:3])
            except:
                pass
        return diseases

    # ========== OMIM检索 ==========
    def search_omim(self, hpo_ids):
        """通过HPO ID检索OMIM疾病"""
        diseases = []
        for hpo_id in hpo_ids[:5]:
            try:
                # 通过MCP端点调用OMIM
                payload = json.dumps({
                    "tool": "openfda_search",
                    "params": {"search": hpo_id},
                }).encode()

                req = urllib.request.Request(
                    f"{self.mcp_base}/tool/call",
                    data=payload,
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                resp = urllib.request.urlopen(req, timeout=10)
                data = json.loads(resp.read())
                if data.get("results"):
                    diseases.extend(data["results"][:3])
            except:
                pass
        return diseases

    # ========== OpenTargets检索 ==========
    def search_opentargets(self, hpo_ids):
        """通过OpenTargets API检索靶点-疾病关联"""
        results = []
        for hpo_id in hpo_ids[:3]:
            try:
                query = """
                query SearchTargets($queryString: String!) {
                    search(queryString: $queryString, entityNames: ["disease"], page: {size: 5}) {
                        hits {
                            id
                            name
                            description
                        }
                    }
                }
                """
                payload = json.dumps({
                    "query": query,
                    "variables": {"queryString": hpo_id}
                }).encode()

                req = urllib.request.Request(
                    "https://api.platform.opentargets.org/api/v4/graphql",
                    data=payload,
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                resp = urllib.request.urlopen(req, timeout=10)
                data = json.loads(resp.read())
                hits = data.get("data", {}).get("search", {}).get("hits", [])
                results.extend(hits[:3])
            except:
                pass
        return results

    # ========== 综合检索 ==========
    def retrieve_all(self, hpo_ids, free_text=""):
        """
        多源综合检索 — 参考DeepRare的并行信息收集
        同时检索PubMed + Orphanet + OMIM + OpenTargets
        """
        results = {
            "query": {
                "hpo_ids": hpo_ids,
                "free_text": free_text,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            },
            "sources": {},
        }

        # PubMed文献
        query_text = " OR ".join(hpo_ids) if hpo_ids else free_text
        if query_text:
            results["sources"]["pubmed"] = self.search_pubmed(query_text)

        # Orphanet疾病
        if hpo_ids:
            results["sources"]["orphanet"] = self.search_orphanet(hpo_ids)

        # OMIM
        if hpo_ids:
            results["sources"]["omim"] = self.search_omim(hpo_ids)

        # OpenTargets
        if hpo_ids:
            results["sources"]["opentargets"] = self.search_opentargets(hpo_ids)

        return results


# ========== 可追溯推理链 ==========
class ReasoningChain:
    """可追溯推理链 — 参考DeepRare的traceable reasoning"""

    def __init__(self):
        self.steps = []

    def add_step(self, step_type, content, evidence=None, confidence=None):
        """
        添加推理步骤
        step_type: "observation" | "hypothesis" | "evidence" | "validation" | "conclusion"
        """
        step = {
            "step_number": len(self.steps) + 1,
            "type": step_type,
            "content": content,
            "evidence": evidence,
            "confidence": confidence,
            "timestamp": time.strftime("%H:%M:%S"),
        }
        self.steps.append(step)
        return step

    def to_text(self):
        """转为可读文本"""
        lines = []
        type_emoji = {
            "observation": "👁️",
            "hypothesis": "💡",
            "evidence": "📚",
            "validation": "✅",
            "conclusion": "🎯",
            "reflection": "🔄",
        }
        for step in self.steps:
            emoji = type_emoji.get(step["type"], "•")
            lines.append(f"{emoji} [{step['type'].upper()}] {step['content']}")
            if step.get("evidence"):
                lines.append(f"   📎 证据: {step['evidence']}")
            if step.get("confidence"):
                lines.append(f"   📊 置信度: {step['confidence']}")
        return "\n".join(lines)

    def to_json(self):
        return json.dumps(self.steps, ensure_ascii=False, indent=2)


# ========== 自反思诊断引擎 ==========
class SelfReflectiveDiagnostic:
    """
    自反思诊断引擎 — 参考DeepRare的核心创新
    假设→验证→修正 循环
    """

    def __init__(self, hpo_extractor, knowledge_retriever):
        self.extractor = hpo_extractor
        self.retriever = knowledge_retriever
        self.max_iterations = 3

    def diagnose(self, patient_text):
        """
        完整诊断流程
        1. 提取表型
        2. 检索知识
        3. 生成假设
        4. 自反思验证
        5. 输出可追溯结论
        """
        chain = ReasoningChain()

        # Step 1: 表型提取
        chain.add_step("observation", f"患者主诉: {patient_text}")
        phenotype_analysis = self.extractor.analyze_symptoms(patient_text)
        chain.add_step("observation",
            f"提取到 {phenotype_analysis['phenotype_count']} 个HPO表型",
            evidence=", ".join(phenotype_analysis["hpo_ids"]),
            confidence=phenotype_analysis["confidence_avg"])

        if phenotype_analysis["systems_involved"]:
            chain.add_step("observation",
                f"涉及系统: {', '.join(phenotype_analysis['systems_involved'])}")

        # Step 2: 知识检索
        hpo_ids = phenotype_analysis["hpo_ids"]
        chain.add_step("evidence", "正在多源检索（PubMed/Orphanet/OMIM/OpenTargets）...")
        knowledge = self.retriever.retrieve_all(hpo_ids, patient_text)

        source_counts = {k: len(v) for k, v in knowledge["sources"].items() if isinstance(v, list)}
        chain.add_step("evidence",
            f"检索完成: {json.dumps(source_counts, ensure_ascii=False)}",
            evidence=f"来源: {', '.join(knowledge['sources'].keys())}")

        # Step 3: 生成假设（基于表型匹配的疾病映射）
        hypotheses = self._generate_hypotheses(phenotype_analysis, knowledge)
        for i, h in enumerate(hypotheses[:3]):
            chain.add_step("hypothesis",
                f"假设{i+1}: {h['disease']} (匹配度: {h['score']}%)",
                evidence=h.get("reasoning", ""),
                confidence=f"{h['score']}%")

        # Step 4: 自反思验证
        if hypotheses:
            validated = self._self_reflect(hypotheses[0], phenotype_analysis, chain)
            if validated:
                chain.add_step("conclusion",
                    f"最终诊断倾向: {validated['disease']}",
                    confidence=f"{validated['confidence']}%")

        return {
            "reasoning_chain": chain.to_text(),
            "steps": chain.steps,
            "phenotype_analysis": phenotype_analysis,
            "hypotheses": hypotheses,
            "knowledge": knowledge,
        }

    def _generate_hypotheses(self, phenotype, knowledge):
        """基于表型-疾病映射生成诊断假设"""
        # 简化版：基于HPO术语库中的疾病映射
        hpo_to_diseases = {
            "HP:0000508": ["重症肌无力", "线粒体脑肌病", "先天性肌病"],
            "HP:0002015": ["重症肌无力", "食管癌", "脑干病变"],
            "HP:0001252": ["重症肌无力", "肌营养不良", "多发性肌炎"],
            "HP:0000651": ["重症肌无力", "多发性硬化", "脑干病变"],
            "HP:0001260": ["重症肌无力", "帕金森病", "脑卒中"],
            "HP:0001263": ["Rett综合征", "天使综合征", "脆性X综合征"],
            "HP:0001250": ["Dravet综合征", "Lennox-Gastaut", "结节性硬化"],
            "HP:0001251": ["脊髓小脑共济失调", "Friedreich共济失调"],
            "HP:0001337": ["帕金森病", "原发性震颤", "Wilson病"],
            "HP:0000988": ["系统性红斑狼疮", "过敏性紫癜", "皮肌炎"],
            "HP:0001638": ["肥厚型心肌病", "扩张型心肌病", "Fabry病"],
            "HP:0000957": ["神经纤维瘤病", "McCune-Albright综合征"],
            "HP:0002650": ["马凡综合征", "Ehlers-Danlos综合征", "成骨不全"],
        }

        disease_scores = {}
        for hpo_id in phenotype["hpo_ids"]:
            diseases = hpo_to_diseases.get(hpo_id, [])
            for d in diseases:
                disease_scores[d] = disease_scores.get(d, 0) + 1

        # 按匹配数排序
        hypotheses = []
        for disease, count in sorted(disease_scores.items(), key=lambda x: x[1], reverse=True)[:5]:
            score = round(count / max(len(phenotype["hpo_ids"]), 1) * 100)
            hypotheses.append({
                "disease": disease,
                "score": score,
                "matched_symptoms": count,
                "reasoning": f"匹配 {count} 个表型特征",
            })

        return hypotheses

    def _self_reflect(self, hypothesis, phenotype, chain):
        """自反思验证 — DeepRare核心创新"""
        chain.add_step("reflection",
            f"自反思验证: {hypothesis['disease']}")

        # 检查是否有矛盾表型
        contradictory_pairs = [
            ("HP:0001252", "HP:0001257"),  # 肌无力 vs 痉挛
            ("HP:0001945", "HP:0004395"),  # 发热 vs 体重下降
        ]

        has_contradiction = False
        for a, b in contradictory_pairs:
            if a in phenotype["hpo_ids"] and b in phenotype["hpo_ids"]:
                has_contradiction = True
                chain.add_step("reflection",
                    f"⚠️ 注意: 同时存在矛盾表型，需进一步评估")

        if hypothesis["score"] >= 50 and not has_contradiction:
            chain.add_step("validation",
                f"✅ {hypothesis['disease']} 假设通过自反思验证",
                confidence=f"{hypothesis['score']}%")
            return {"disease": hypothesis["disease"], "confidence": hypothesis["score"]}
        elif hypothesis["score"] >= 30:
            chain.add_step("validation",
                f"⚠️ {hypothesis['disease']} 置信度中等，建议补充检查")
            return {"disease": hypothesis["disease"], "confidence": hypothesis["score"]}
        else:
            chain.add_step("validation",
                f"❌ 假设置信度不足，需进一步信息")
            return None


# ========== 测试 ==========
if __name__ == "__main__":
    from hpo_extractor import HPOExtractor

    extractor = HPOExtractor()
    retriever = KnowledgeRetriever()
    engine = SelfReflectiveDiagnostic(extractor, retriever)

    test = "我最近眼睑下垂，吞咽困难，全身无力，说话也不清楚了，下午特别明显"
    result = engine.diagnose(test)

    print("=" * 60)
    print(result["reasoning_chain"])
    print("=" * 60)
    print(f"\n假设列表:")
    for h in result["hypotheses"]:
        print(f"  {h['disease']}: {h['score']}% ({h['matched_symptoms']}个表型匹配)")
