"""
MediChat-RD v4.0 - 罕见病在线诊疗平台
统一后端服务：MIMO AI + ToolUniverse + 知识库
"""

import os
import json
import asyncio
import requests
from datetime import datetime
from typing import List, Optional, Dict, Any, Literal
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
from openai import OpenAI

try:
    from .a2a_orchestrator import A2AOrchestrator
except ImportError:
    from a2a_orchestrator import A2AOrchestrator

# ═══════════════════════════════════════════════════
# 配置
# ═══════════════════════════════════════════════════
MIMO_API_KEY = os.getenv("MIMO_API_KEY", "")
MIMO_BASE_URL = os.getenv("MIMO_BASE_URL", "https://api.xiaomimimo.com/v1")
MIMO_MODEL = os.getenv("MIMO_MODEL", "mimo-v2-pro")
MCP_ENDPOINT = "https://mcp.cloud.curiloo.com/tools/unified/mcp"

app = FastAPI(
    title="MediChat-RD",
    description="罕见病在线诊疗平台 - AI驱动的罕见病研究与诊疗",
    version="4.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ═══════════════════════════════════════════════════
# MIMO AI 客户端
# ═══════════════════════════════════════════════════
def get_mimo_client() -> OpenAI:
    return OpenAI(api_key=MIMO_API_KEY, base_url=MIMO_BASE_URL)

SYSTEM_PROMPT = """你是 MediChat-RD 的AI助手，一位专注于罕见病领域的顶级医疗AI。
你的能力：
1. 深入理解罕见病的病理机制、遗传背景和临床特征
2. 熟悉全球罕见病诊疗指南和最新研究进展
3. 能够整合多源数据（OpenTargets、ChEMBL、ClinicalTrials、PubMed）进行综合分析
4. 输出专业、结构化、患者友好的回答

请用清晰、专业的中文回答。对于患者提问，用易懂的语言解释；
对于医生/研究者，提供更深入的专业分析。
重要提示：你提供的信息仅供参考，不能替代专业医疗诊断和治疗。"""

# ═══════════════════════════════════════════════════
# ToolUniverse MCP 调用
# ═══════════════════════════════════════════════════
def mcp_call(tool_name: str, arguments: dict, timeout: int = 60) -> dict:
    """调用ToolUniverse MCP工具"""
    payload = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {"name": tool_name, "arguments": arguments},
        "id": 1
    }
    try:
        resp = requests.post(MCP_ENDPOINT, json=payload, headers={
            "Content-Type": "application/json",
            "Accept": "application/json"
        }, timeout=timeout)
        result = resp.json()
        if result.get("isError"):
            return {"error": result["result"]["content"][0]["text"]}
        return json.loads(result["result"]["content"][0]["text"])
    except Exception as e:
        return {"error": str(e)}

# ═══════════════════════════════════════════════════
# 数据模型
# ═══════════════════════════════════════════════════
class ChatMessage(BaseModel):
    role: str = Field(..., description="user 或 assistant")
    content: str = Field(..., description="消息内容")

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    disease_context: Optional[str] = Field(None, description="当前疾病上下文")
    stream: bool = Field(False, description="是否流式输出")

class ResearchRequest(BaseModel):
    disease_name: str = Field(..., description="疾病名称")
    include_drugs: bool = Field(True, description="包含药物信息")
    include_targets: bool = Field(True, description="包含靶点信息")
    include_trials: bool = Field(True, description="包含临床试验")
    include_analysis: bool = Field(True, description="包含AI分析")

class SymptomCheckRequest(BaseModel):
    symptoms: str = Field(..., description="症状描述")
    age: Optional[int] = Field(None, description="年龄")
    gender: Optional[str] = Field(None, description="性别")


class A2APatientProfile(BaseModel):
    patient_id: Optional[str] = Field(None, description="患者ID")
    nickname: Optional[str] = Field(None, description="昵称")
    age: Optional[int] = Field(None, description="年龄")
    gender: Optional[str] = Field(None, description="性别")
    diagnosis: Optional[str] = Field(None, description="诊断结果")
    disease_type: Optional[str] = Field(None, description="疾病类型")
    symptoms: Optional[str] = Field(None, description="主要症状")
    treatment_history: Optional[str] = Field(None, description="治疗经历")


class A2ASessionCreateRequest(BaseModel):
    mode: Literal["auto", "lead-agent", "roundtable"] = Field("auto", description="A2A模式")
    lead_agent: Optional[str] = Field(None, description="首位Agent")
    disease_context: Optional[str] = Field(None, description="疾病上下文")
    patient_profile: Optional[A2APatientProfile] = Field(None, description="患者档案")
    metadata: Optional[Dict[str, Any]] = Field(None, description="扩展元数据")
    initial_message: Optional[str] = Field(None, description="初始消息")


class A2AMessageRequest(BaseModel):
    content: str = Field(..., description="用户消息")
    disease_context: Optional[str] = Field(None, description="可选疾病上下文")

# ═══════════════════════════════════════════════════
# 知识库（121种罕见病）
# ═══════════════════════════════════════════════════
KNOWLEDGE_DIR = os.path.join(os.path.dirname(__file__), "..", "knowledge")

def load_disease_knowledge(disease_name: str) -> dict:
    """加载疾病知识库"""
    try:
        # 尝试从知识库目录加载
        for filename in os.listdir(KNOWLEDGE_DIR) if os.path.exists(KNOWLEDGE_DIR) else []:
            if disease_name.lower().replace(" ", "_") in filename.lower():
                filepath = os.path.join(KNOWLEDGE_DIR, filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
    except Exception:
        pass
    return {}


a2a_orchestrator = A2AOrchestrator(
    mcp_call=mcp_call,
    get_mimo_client=get_mimo_client,
    model_name=MIMO_MODEL,
    load_disease_knowledge=load_disease_knowledge,
    mimo_available=bool(MIMO_API_KEY),
)

# ═══════════════════════════════════════════════════
# API 路由
# ═══════════════════════════════════════════════════

# --- 健康检查 ---
@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "MediChat-RD v4.0",
        "timestamp": datetime.now().isoformat(),
        "mimo_configured": bool(MIMO_API_KEY),
        "mcp_available": True,
        "a2a_available": True,
    }

# --- AI 对话 ---
@app.post("/api/v2/chat")
async def chat(request: ChatRequest):
    """MIMO驱动的AI对话"""
    if not MIMO_API_KEY:
        raise HTTPException(status_code=500, detail="MIMO API未配置")
    
    client = get_mimo_client()
    
    # 构建消息
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    
    # 如果有疾病上下文，注入知识
    if request.disease_context:
        knowledge = load_disease_knowledge(request.disease_context)
        if knowledge:
            context_msg = f"当前讨论的疾病是：{request.disease_context}\n相关知识：{json.dumps(knowledge, ensure_ascii=False)[:3000]}"
            messages.append({"role": "system", "content": context_msg})
    
    # 添加用户对话历史
    for msg in request.messages:
        messages.append({"role": msg.role, "content": msg.content})
    
    if request.stream:
        def generate():
            stream = client.chat.completions.create(
                model=MIMO_MODEL,
                messages=messages,
                temperature=0.7,
                max_tokens=4096,
                stream=True
            )
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield f"data: {json.dumps({'content': chunk.choices[0].delta.content}, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"
        return StreamingResponse(generate(), media_type="text/event-stream")
    else:
        response = client.chat.completions.create(
            model=MIMO_MODEL,
            messages=messages,
            temperature=0.7,
            max_tokens=4096
        )
        return {
            "response": response.choices[0].message.content,
            "model": MIMO_MODEL,
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                "completion_tokens": response.usage.completion_tokens if response.usage else 0
            }
        }

# --- 疾病研究（一键研究） ---
@app.post("/api/v2/research")
async def research_disease(request: ResearchRequest):
    """一键疾病研究：靶点+药物+临床试验+AI分析"""
    result = {
        "disease": request.disease_name,
        "timestamp": datetime.now().isoformat(),
        "stages": {}
    }
    
    # 1. OpenTargets搜索
    disease_search = mcp_call("opentargets_search", {
        "query": request.disease_name,
        "entity_type": "disease"
    })
    disease_id = None
    if "data" in disease_search and disease_search["data"]:
        top = disease_search["data"][0]
        disease_id = top["id"]
        result["stages"]["disease_info"] = {
            "id": disease_id,
            "name": top["name"],
            "description": top.get("description", "")
        }
    
    # 2. 靶点关联
    if request.include_targets and disease_id:
        targets = mcp_call("opentargets_get_associations", {
            "disease_id": disease_id,
            "size": 10
        })
        if "data" in targets:
            result["stages"]["targets"] = [
                {
                    "gene_id": t["target"]["id"],
                    "gene_name": t["target"]["approvedName"],
                    "score": round(t["score"], 3),
                    "genetic_association": next(
                        (s["score"] for s in t.get("datatypeScores", []) if s["id"] == "genetic_association"),
                        None
                    ),
                    "clinical": next(
                        (s["score"] for s in t.get("datatypeScores", []) if s["id"] == "clinical"),
                        None
                    )
                }
                for t in targets["data"][:10]
            ]
    
    # 3. 药物搜索
    if request.include_drugs:
        drugs = mcp_call("chembl_find_drugs_by_indication", {
            "disease_query": request.disease_name,
            "max_results": 20
        })
        if "data" in drugs:
            result["stages"]["drugs"] = [
                {
                    "chembl_id": d.get("molecule_chembl_id", ""),
                    "max_phase": d.get("max_phase_for_ind", ""),
                    "phase_label": {
                        "0.5": "临床前",
                        "1.0": "I期",
                        "2.0": "II期",
                        "3.0": "III期",
                        "4.0": "已上市"
                    }.get(str(d.get("max_phase_for_ind", "")), "未知"),
                    "mesh_heading": d.get("mesh_heading", ""),
                    "refs": [r["ref_url"] for r in d.get("indication_refs", [])[:2]]
                }
                for d in drugs["data"][:15]
            ]
    
    # 4. 临床试验
    if request.include_trials:
        trials = mcp_call("ctg_search_studies", {
            "condition": request.disease_name,
            "max_results": 10
        })
        if "data" in trials and "studies" in trials["data"]:
            result["stages"]["clinical_trials"] = []
            for t in trials["data"]["studies"][:10]:
                proto = t.get("protocolSection", {})
                ident = proto.get("identificationModule", {})
                status_mod = proto.get("statusModule", {})
                desc = proto.get("descriptionModule", {})
                sponsor = proto.get("sponsorCollaboratorsModule", {})
                result["stages"]["clinical_trials"].append({
                    "nct_id": ident.get("nctId", ""),
                    "title": ident.get("briefTitle", ""),
                    "status": status_mod.get("overallStatus", ""),
                    "status_cn": {
                        "RECRUITING": "正在招募",
                        "COMPLETED": "已完成",
                        "ACTIVE_NOT_RECRUITING": "进行中（不招募）",
                        "NOT_YET_RECRUITING": "尚未招募",
                        "TERMINATED": "已终止",
                        "SUSPENDED": "已暂停"
                    }.get(status_mod.get("overallStatus", ""), status_mod.get("overallStatus", "")),
                    "sponsor": sponsor.get("leadSponsor", {}).get("name", ""),
                    "summary": desc.get("briefSummary", "")[:200] + "..." if desc.get("briefSummary", "") else ""
                })
    
    # 5. MIMO AI 分析
    if request.include_analysis:
        analysis_data = json.dumps(result["stages"], ensure_ascii=False, indent=2)
        client = get_mimo_client()
        response = client.chat.completions.create(
            model=MIMO_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"基于以下罕见病 '{request.disease_name}' 的研究数据，生成一份结构化分析报告：\n\n{analysis_data}\n\n请包含：\n1. 疾病概述（200字以内）\n2. 关键靶点分析（表格形式）\n3. 现有药物评价\n4. 药物重定位机会\n5. 临床试验现状\n6. 研究建议\n\n请用专业但易懂的中文，避免乱码和特殊字符。"}
            ],
            temperature=0.4,
            max_tokens=4096
        )
        result["stages"]["analysis"] = response.choices[0].message.content
    
    return result

# --- 症状自查 ---
@app.post("/api/v2/symptom-check")
async def symptom_check(request: SymptomCheckRequest):
    """症状自查 → 可能的罕见病建议"""
    if not MIMO_API_KEY:
        raise HTTPException(status_code=500, detail="MIMO API未配置")
    
    client = get_mimo_client()
    
    prompt = f"""一位{f'{request.age}岁' if request.age else ''}{request.gender if request.gender else ''}患者描述以下症状：
{request.symptoms}

请作为罕见病领域的专家，分析：
1. 这些症状可能指向哪些罕见病？（列出前3-5个最可能的）
2. 每个可能疾病的概率估计（高/中/低）
3. 建议的进一步检查项目
4. 需要注意的警示症状

请用清晰的中文回答，格式整洁，避免使用特殊符号。"""

    response = client.chat.completions.create(
        model=MIMO_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
        max_tokens=3000
    )
    
    return {
        "symptoms": request.symptoms,
        "analysis": response.choices[0].message.content,
        "disclaimer": "本分析仅供参考，不构成医疗诊断。如有疑虑，请咨询专业医生。",
        "timestamp": datetime.now().isoformat()
    }

# --- 药物重定位分析 ---
@app.post("/api/v2/drug-repurposing")
async def drug_repurposing(disease_name: str = Query(..., description="疾病名称")):
    """药物重定位深度分析"""
    # 获取疾病ID
    disease_search = mcp_call("opentargets_search", {
        "query": disease_name, "entity_type": "disease"
    })
    if not disease_search.get("data"):
        raise HTTPException(status_code=404, detail=f"未找到疾病: {disease_name}")
    
    disease_id = disease_search["data"][0]["id"]
    
    # 并行获取数据
    targets = mcp_call("opentargets_get_associations", {"disease_id": disease_id, "size": 15})
    drugs = mcp_call("chembl_find_drugs_by_indication", {"disease_query": disease_name, "max_results": 25})
    
    # MIMO分析
    client = get_mimo_client()
    analysis = client.chat.completions.create(
        model=MIMO_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"""作为药物重定位专家，深度分析 {disease_name} 的药物重定位机会：

靶点数据：
{json.dumps(targets.get('data', [])[:10], ensure_ascii=False)}

现有药物：
{json.dumps(drugs.get('data', [])[:15], ensure_ascii=False)}

请提供：
1. 最有前景的5个药物重定位候选（附详细理由和证据等级）
2. 潜在的新靶点机会
3. 需要验证的关键假设
4. 建议的下一步实验设计
5. 潜在风险和注意事项

请用结构化、专业的中文回答。"""}
        ],
        temperature=0.4,
        max_tokens=4096
    )
    
    return {
        "disease": disease_name,
        "disease_id": disease_id,
        "targets": targets.get("data", [])[:10],
        "existing_drugs": drugs.get("data", [])[:15],
        "repurposing_analysis": analysis.choices[0].message.content,
        "timestamp": datetime.now().isoformat()
    }

# --- 疾病列表 ---
@app.get("/api/v2/diseases")
async def list_diseases():
    """获取平台支持的罕见病列表"""
    # 从知识库目录读取
    diseases = []
    if os.path.exists(KNOWLEDGE_DIR):
        for filename in sorted(os.listdir(KNOWLEDGE_DIR)):
            if filename.endswith('.json'):
                try:
                    with open(os.path.join(KNOWLEDGE_DIR, filename), 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        diseases.append({
                            "id": filename.replace('.json', ''),
                            "name": data.get("name", filename.replace('.json', '').replace('_', ' ')),
                            "category": data.get("category", "未分类"),
                            "prevalence": data.get("prevalence", "未知")
                        })
                except Exception:
                    pass
    
    return {"total": len(diseases), "diseases": diseases}

# --- PubMed文献搜索 ---
@app.get("/api/v2/literature")
async def search_literature(
    query: str = Query(..., description="搜索关键词"),
    max_results: int = Query(10, description="最大结果数")
):
    """PubMed文献搜索"""
    result = mcp_call("pubmed_search_articles", {
        "diseases": [query],
        "max_results": max_results
    })
    return result


# --- A2A Orchestration ---
@app.get("/api/v2/a2a/agents")
async def list_a2a_agents():
    return {"agents": a2a_orchestrator.list_agents()}


@app.get("/api/v2/a2a/sessions")
async def list_a2a_sessions():
    return {"sessions": a2a_orchestrator.list_sessions()}


@app.post("/api/v2/a2a/sessions")
async def create_a2a_session(request: A2ASessionCreateRequest):
    return await a2a_orchestrator.create_session(
        mode=request.mode,
        lead_agent=request.lead_agent,
        disease_context=request.disease_context,
        patient_profile=request.patient_profile.model_dump(exclude_none=True) if request.patient_profile else None,
        metadata=request.metadata,
        initial_message=request.initial_message,
    )


@app.get("/api/v2/a2a/sessions/{session_id}")
async def get_a2a_session(session_id: str):
    try:
        session = a2a_orchestrator.get_session(session_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"A2A session not found: {session_id}")

    latest_report = next(
        (artifact for artifact in reversed(session["artifacts"]) if artifact["agent_id"] == "report_agent"),
        None,
    )
    return {
        "session": session,
        "latest_report": latest_report["content"] if latest_report else None,
        "executed_agents": session.get("orchestration", {}).get("executed_chain", []),
    }


@app.post("/api/v2/a2a/sessions/{session_id}/messages")
async def add_a2a_message(session_id: str, request: A2AMessageRequest):
    try:
        return await a2a_orchestrator.add_message(
            session_id,
            request.content,
            disease_context=request.disease_context,
        )
    except KeyError:
        raise HTTPException(status_code=404, detail=f"A2A session not found: {session_id}")

# --- Landing Page (介绍主页) ---
@app.get("/landing")
async def landing_page():
    landing_path = os.path.join(os.path.dirname(__file__), "..", "pages", "landing.html")
    from fastapi.responses import FileResponse
    return FileResponse(landing_path, media_type="text/html")

# --- 挂载前端静态文件 ---
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
if os.path.exists(FRONTEND_DIR):
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
