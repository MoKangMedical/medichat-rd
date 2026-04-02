#!/usr/bin/env python3
"""
贾维斯 × MIMO 罕见病研究Agent
利用小米MIMO无限额度API + ToolUniverse医疗数据源
自动执行疾病研究→靶点发现→药物重定位→临床试验匹配 全流程
"""

import os
import json
import requests
from openai import OpenAI
from datetime import datetime

# ═══════════════════════════════════════════════════
# MIMO 客户端（无限额度）
# ═══════════════════════════════════════════════════
MIMO_API_KEY = os.getenv("MIMO_API_KEY", "")
MIMO_BASE_URL = os.getenv("MIMO_BASE_URL", "https://api.xiaomimimo.com/v1")
MIMO_MODEL = os.getenv("MIMO_MODEL", "mimo-v2-pro")

# ═══════════════════════════════════════════════════
# ToolUniverse MCP 端点
# ═══════════════════════════════════════════════════
MCP_ENDPOINT = "https://mcp.cloud.curiloo.com/tools/unified/mcp"

def mcp_call(tool_name: str, arguments: dict, timeout: int = 60) -> dict:
    """调用ToolUniverse MCP工具"""
    payload = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {"name": tool_name, "arguments": arguments},
        "id": 1
    }
    try:
        resp = requests.post(
            MCP_ENDPOINT,
            json=payload,
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            timeout=timeout
        )
        result = resp.json()
        if result.get("isError"):
            return {"error": result["result"]["content"][0]["text"]}
        return json.loads(result["result"]["content"][0]["text"])
    except Exception as e:
        return {"error": str(e)}

def mimo_chat(system: str, user: str, temperature: float = 0.3) -> str:
    """调用MIMO进行推理"""
    if not MIMO_API_KEY:
        return "[ERROR] MIMO_API_KEY未配置"
    client = OpenAI(api_key=MIMO_API_KEY, base_url=MIMO_BASE_URL)
    response = client.chat.completions.create(
        model=MIMO_MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user}
        ],
        temperature=temperature,
        max_tokens=4096
    )
    return response.choices[0].message.content


class MIMOResearchAgent:
    """MIMO驱动的罕见病研究Agent"""
    
    SYSTEM_PROMPT = """你是一位顶级的罕见病研究专家AI助手，具备以下能力：
1. 深入理解罕见病的病理机制、遗传背景和临床特征
2. 熟悉药物重定位策略和靶点验证方法
3. 能够整合多源数据进行综合分析
4. 输出结构化的研究报告

请用专业、简洁的中文回答，重点突出临床转化价值。"""

    def research_disease(self, disease_name: str) -> dict:
        """完整疾病研究流程"""
        report = {
            "disease": disease_name,
            "timestamp": datetime.now().isoformat(),
            "stages": {}
        }
        
        # Stage 1: OpenTargets搜索疾病
        print(f"🔍 Stage 1: 搜索疾病 '{disease_name}'...")
        disease_search = mcp_call("opentargets_search", {
            "query": disease_name,
            "entity_type": "disease"
        })
        disease_id = None
        if "data" in disease_search and disease_search["data"]:
            top = disease_search["data"][0]
            disease_id = top["id"]
            report["stages"]["disease_search"] = {
                "id": disease_id,
                "name": top["name"],
                "description": top.get("description", "")
            }
            print(f"  ✅ 疾病ID: {disease_id} - {top['name']}")
        
        # Stage 2: 获取疾病靶点
        if disease_id:
            print(f"🧬 Stage 2: 获取疾病靶点...")
            targets = mcp_call("opentargets_get_associations", {
                "disease_id": disease_id,
                "size": 10
            })
            if "data" in targets:
                target_list = []
                for t in targets["data"][:5]:
                    target_list.append({
                        "gene_id": t["target"]["id"],
                        "gene_name": t["target"]["approvedName"],
                        "score": round(t["score"], 3)
                    })
                report["stages"]["targets"] = target_list
                print(f"  ✅ 获取到 {len(target_list)} 个靶点")
        
        # Stage 3: ChEMBL搜索药物
        print(f"💊 Stage 3: 搜索治疗药物...")
        drugs = mcp_call("chembl_find_drugs_by_indication", {
            "disease_query": disease_name,
            "max_results": 15
        })
        if "data" in drugs:
            drug_list = []
            for d in drugs["data"][:10]:
                drug_list.append({
                    "chembl_id": d.get("molecule_chembl_id", ""),
                    "max_phase": d.get("max_phase_for_ind", ""),
                    "mesh_heading": d.get("mesh_heading", "")
                })
            report["stages"]["drugs"] = drug_list
            print(f"  ✅ 获取到 {len(drug_list)} 个化合物")
        
        # Stage 4: ClinicalTrials搜索
        print(f"📋 Stage 4: 搜索临床试验...")
        trials = mcp_call("ctg_search_studies", {
            "condition": disease_name,
            "recruitment_status": "RECRUITING",
            "max_results": 5
        })
        if "data" in trials and "studies" in trials["data"]:
            trial_list = []
            for t in trials["data"]["studies"][:5]:
                proto = t.get("protocolSection", {})
                ident = proto.get("identificationModule", {})
                status = proto.get("statusModule", {})
                trial_list.append({
                    "nct_id": ident.get("nctId", ""),
                    "title": ident.get("briefTitle", ""),
                    "status": status.get("overallStatus", "")
                })
            report["stages"]["clinical_trials"] = trial_list
            print(f"  ✅ 获取到 {len(trial_list)} 个正在招募的试验")
        
        # Stage 5: MIMO综合分析
        print(f"🧠 Stage 5: MIMO综合分析...")
        analysis_input = json.dumps(report["stages"], ensure_ascii=False, indent=2)
        analysis = mimo_chat(
            self.SYSTEM_PROMPT,
            f"基于以下罕见病 '{disease_name}' 的研究数据，生成一份结构化分析报告：\n\n"
            f"{analysis_input}\n\n"
            f"请包含：1) 疾病概述 2) 关键靶点分析 3) 现有药物评价 4) 药物重定位机会 5) 临床试验现状 6) 研究建议"
        )
        report["stages"]["mimo_analysis"] = analysis
        print(f"  ✅ 分析完成")
        
        return report

    def batch_drug_repurposing(self, disease_name: str) -> str:
        """批量药物重定位分析（MIMO + 数据源）"""
        # 获取靶点
        disease_search = mcp_call("opentargets_search", {
            "query": disease_name, "entity_type": "disease"
        })
        if not disease_search.get("data"):
            return "未找到疾病数据"
        
        disease_id = disease_search["data"][0]["id"]
        
        # 获取靶点关联
        targets = mcp_call("opentargets_get_associations", {
            "disease_id": disease_id, "size": 10
        })
        
        # 获取药物
        drugs = mcp_call("chembl_find_drugs_by_indication", {
            "disease_query": disease_name, "max_results": 20
        })
        
        # MIMO分析药物重定位机会
        prompt = f"""作为药物重定位专家，基于以下数据分析 {disease_name} 的药物重定位机会：

靶点数据：
{json.dumps(targets.get('data', [])[:5], ensure_ascii=False)}

药物数据：
{json.dumps(drugs.get('data', [])[:10], ensure_ascii=False)}

请提供：
1. 最有前景的3个药物重定位候选（附理由）
2. 潜在的新靶点机会
3. 需要验证的关键假设
4. 建议的下一步实验"""

        return mimo_chat(self.SYSTEM_PROMPT, prompt, temperature=0.4)


# ═══════════════════════════════════════════════════
# CLI入口
# ═══════════════════════════════════════════════════
if __name__ == "__main__":
    import sys
    
    agent = MIMOResearchAgent()
    
    if len(sys.argv) > 1:
        disease = " ".join(sys.argv[1:])
    else:
        disease = "Myasthenia Gravis"  # 默认：重症肌无力
    
    print(f"\n{'='*60}")
    print(f"🧬 贾维斯 × MIMO 罕见病研究Agent")
    print(f"📋 研究目标: {disease}")
    print(f"{'='*60}\n")
    
    report = agent.research_disease(disease)
    
    print(f"\n{'='*60}")
    print(f"📊 研究报告")
    print(f"{'='*60}\n")
    print(report["stages"].get("mimo_analysis", "分析生成失败"))
    
    # 保存报告
    output_file = f"/tmp/research_{disease.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"\n📁 完整报告已保存: {output_file}")
