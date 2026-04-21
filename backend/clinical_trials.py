"""
MediChat-RD 临床试验对接模块 — Hermes改进
从ClinicalTrials.gov API拉取相关临床试验

用户视角：罕见病患者最需要的是"有没有新的治疗机会"
"""

import json
import urllib.request
import urllib.parse
from typing import Dict, List, Optional
from datetime import datetime

BASE_URL = "https://clinicaltrials.gov/api/v2"


def search_trials(
    disease: str,
    status: str = "RECRUITING",
    max_results: int = 5,
    country: str = "China"
) -> List[Dict]:
    """
    搜索临床试验
    
    Args:
        disease: 疾病名称（中文或英文）
        status: 状态（RECRUITING/ACTIVE_NOT_RECRUITING/COMPLETED）
        max_results: 最多返回数量
        country: 国家过滤
    
    Returns:
        临床试验列表
    """
    params = {
        "query.cond": disease,
        "filter.overallStatus": status,
        "pageSize": max_results,
        "format": "json",
    }
    
    if country:
        params["filter.geo"] = f"distance(39.9,116.4,5000km)"  # 中国为中心
    
    url = f"{BASE_URL}/studies?{urllib.parse.urlencode(params)}"
    
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "MediChat-RD/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
        
        studies = data.get("studies", [])
        results = []
        
        for study in studies:
            proto = study.get("protocolSection", {})
            ident = proto.get("identificationModule", {})
            status_mod = proto.get("statusModule", {})
            design = proto.get("designModule", {})
            contacts = proto.get("contactsLocationsModule", {})
            
            # 提取关键信息
            nct_id = ident.get("nctId", "")
            title = ident.get("briefTitle", "")
            status_text = status_mod.get("overallStatus", "")
            
            # 中国站点
            locations = contacts.get("locations", [])
            china_sites = [
                loc.get("facility", "") 
                for loc in locations 
                if loc.get("country") == "China"
            ][:3]
            
            results.append({
                "nct_id": nct_id,
                "title": title,
                "status": status_text,
                "url": f"https://clinicaltrials.gov/study/{nct_id}",
                "china_sites": china_sites,
                "phase": design.get("phases", ["N/A"])[0] if design.get("phases") else "N/A",
            })
        
        return results
    except Exception as e:
        return [{"error": str(e)}]


def format_trials_for_patient(trials: List[Dict], disease: str) -> str:
    """
    将临床试验格式化为患者友好的文本
    """
    if not trials or (len(trials) == 1 and "error" in trials[0]):
        return f"\n📋 **{disease}相关临床试验**：暂无正在招募的试验信息"
    
    lines = [f"\n📋 **{disease}相关临床试验**\n"]
    
    for i, trial in enumerate(trials, 1):
        if "error" in trial:
            continue
        lines.append(f"### {i}. {trial['title'][:60]}")
        lines.append(f"   🔬 编号：{trial['nct_id']}")
        lines.append(f"   📊 阶段：{trial['phase']}")
        lines.append(f"   🟢 状态：{trial['status']}")
        if trial.get("china_sites"):
            lines.append(f"   🏥 中国站点：{', '.join(trial['china_sites'])}")
        lines.append(f"   🔗 详情：{trial['url']}")
        lines.append("")
    
    lines.append("💡 参加临床试验可能是获得最新治疗的机会，建议与主治医生讨论是否适合。")
    
    return "\n".join(lines)


def get_trials_json(disease: str, max_results: int = 5) -> Dict:
    """返回JSON格式的试验结果（供API使用）"""
    trials = search_trials(disease, max_results=max_results)
    return {
        "disease": disease,
        "count": len(trials),
        "trials": trials,
        "formatted_text": format_trials_for_patient(trials, disease),
        "source": "ClinicalTrials.gov",
        "disclaimer": "临床试验信息仅供参考，参加前请咨询主治医生。"
    }


if __name__ == "__main__":
    # 测试
    result = get_trials_json("罕见病", max_results=3)
    print(result["formatted_text"])
