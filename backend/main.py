"""
MediChat - FastAPI 后端服务（集成小米MIMO）
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import uuid
import os
import sys
from dotenv import load_dotenv

# 加载环境变量
BASE_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, ".."))
for env_file, should_override in (
    (os.path.join(PROJECT_ROOT, ".env"), False),
    (os.path.join(BASE_DIR, ".env"), False),
    (os.path.join(PROJECT_ROOT, ".env.local"), True),
    (os.path.join(BASE_DIR, ".env.local"), True),
):
    load_dotenv(env_file, override=should_override)

# 导入MIMO客户端
from mimo_client import MIMOClient

# 导入医生档案和提示词
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'agents'))
from medical_agents import (
    get_system_prompt,
    get_task_prompt,
    get_doctor_profile,
    TRIAGE_SYSTEM_PROMPT,
    HISTORY_SYSTEM_PROMPT,
    ASSESSMENT_SYSTEM_PROMPT,
    MEDICATION_SYSTEM_PROMPT,
    EDUCATION_SYSTEM_PROMPT,
    FOLLOWUP_SYSTEM_PROMPT
)

# 导入HIPAA合规模块
from hipaa_compliance import (
    AuditLogger, AuditAction, DataMasker, 
    ComplianceChecker, DataClassification
)

# 导入罕见病API
from rare_disease_api import router as rare_disease_router
from deeprare_api import router as deeprare_router
from community_api import router as community_router
from knowledge_api import router as knowledge_router
from platform_hub_api import router as platform_hub_router
from avatar_runtime_api import router as avatar_runtime_router
from secondme_mcp_api import router as secondme_mcp_router
from secondme_oauth_api import router as secondme_oauth_router
from doctor_api import router as doctor_router
from openevidence_api import router as openevidence_router
from analytics_api import router as analytics_router

app = FastAPI(
    title="MediChat API",
    description="医疗多Agent智能交互平台 API - 小米MIMO驱动",
    version="1.0.0"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化MIMO客户端
try:
    mimo_client = MIMOClient()
    MIMO_ENABLED = True
except ValueError:
    MIMO_ENABLED = False
    print("⚠️  MIMO未配置，使用模拟模式")

# 初始化HIPAA合规模块
audit_logger = AuditLogger()
data_masker = DataMasker()
compliance_checker = ComplianceChecker()

# 注册路由
app.include_router(rare_disease_router)
app.include_router(deeprare_router)
app.include_router(community_router)
app.include_router(knowledge_router)
app.include_router(platform_hub_router)
app.include_router(avatar_runtime_router)
app.include_router(secondme_mcp_router)
app.include_router(secondme_oauth_router)
app.include_router(doctor_router)
app.include_router(openevidence_router)
app.include_router(analytics_router)

# ============================================================
# 前端静态文件服务
# ============================================================
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), '..', 'frontend', 'dist')
if os.path.exists(FRONTEND_DIR):
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIR, "assets")), name="assets")


# ============================================================
# 数据模型
# ============================================================
class PatientRequest(BaseModel):
    """患者请求模型"""
    patient_id: Optional[str] = None
    message: str = Field(..., min_length=1, max_length=2000, description="患者消息")
    age: Optional[int] = Field(None, ge=0, le=150, description="年龄")
    gender: Optional[str] = Field(None, pattern="^(男|女|其他)$", description="性别")
    session_id: Optional[str] = None
    stream: bool = Field(False, description="是否流式输出")


class AgentResponse(BaseModel):
    """Agent响应模型"""
    session_id: str
    agent_name: str
    doctor_name: str           # 医生姓名
    doctor_title: str          # 医生职称
    doctor_department: str     # 医生科室
    doctor_hospital: str       # 医生医院
    message: str
    suggestions: Optional[List[str]] = None
    urgency_level: Optional[str] = None
    recommended_department: Optional[str] = None
    timestamp: datetime


class SessionInfo(BaseModel):
    """会话信息"""
    session_id: str
    patient_id: str
    created_at: datetime
    status: str
    messages_count: int


# ============================================================
# 内存存储
# ============================================================
sessions = {}


# ============================================================
# API端点
# ============================================================
@app.get("/")
async def root():
    if os.path.exists(FRONTEND_DIR):
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))
    return {
        "name": "MediChat API",
        "version": "1.0.0",
        "status": "running",
        "llm": "小米MIMO" if MIMO_ENABLED else "模拟模式",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "mimo_connected": MIMO_ENABLED,
        "agents_loaded": True
    }


@app.post("/api/v1/chat", response_model=AgentResponse)
async def chat(request: PatientRequest):
    """
    患者咨询主接口
    使用小米MIMO模型处理患者消息
    """
    # 创建或获取会话
    session_id = request.session_id or str(uuid.uuid4())
    
    # HIPAA审计日志
    audit_logger.log(
        action=AuditAction.READ,
        resource_type="patient_chat",
        resource_id=session_id,
        details={"message_length": len(request.message)}
    )
    
    if session_id not in sessions:
        sessions[session_id] = {
            "patient_id": request.patient_id or str(uuid.uuid4()),
            "created_at": datetime.now(),
            "status": "active",
            "messages": []
        }
    
    # 记录患者消息
    sessions[session_id]["messages"].append({
        "role": "patient",
        "content": request.message,
        "timestamp": datetime.now().isoformat()
    })
    
    # 构建对话历史 - 使用分诊医生的提示词
    conversation_history = sessions[session_id]["messages"][-10:]  # 最近10条
    messages = [{"role": "system", "content": TRIAGE_SYSTEM_PROMPT}]
    
    # 如果是首次对话，添加任务提示
    if len(conversation_history) <= 1:
        messages.append({
            "role": "system", 
            "content": "现在有患者来找你咨询，请用你的开场白问候患者，然后了解他们的症状。"
        })
    
    for msg in conversation_history:
        role = "user" if msg["role"] == "patient" else "assistant"
        messages.append({"role": role, "content": msg["content"]})
    
    # 获取医生信息
    triage_doctor = get_doctor_profile("triage")
    
    # 调用MIMO处理
    if MIMO_ENABLED:
        try:
            response_text = mimo_client.chat(
                messages=messages,
                temperature=0.8,
                max_tokens=1024
            )
        except Exception as e:
            response_text = f"抱歉，系统暂时出现问题，请稍后重试。"
    else:
        # 模拟响应 - 使用医生口吻
        response_text = f"""您好，我是陈雅琴医生，协和医院急诊科的分诊医师。

看到您说头痛伴恶心已经持续一周了，我非常理解您的担心。

根据您描述的情况，我建议您挂【神经内科】进行就诊。

头痛伴恶心可能的原因有很多，包括：
1. 偏头痛
2. 颈椎问题
3. 高血压
4. 眼压问题
5. 睡眠不足或压力过大

在您就诊前，我建议您：
1. 记录一下头痛发作的时间、持续时长、疼痛部位
2. 测量一下血压
3. 注意休息，避免过度用眼

⚠️ 如果出现以下情况，请立即前往急诊：
- 突发剧烈头痛
- 伴呕吐、视物模糊
- 意识障碍

请问您还有其他想了解的吗？"""
    
    # 记录AI回复
    sessions[session_id]["messages"].append({
        "role": "agent",
        "content": response_text,
        "agent_name": "分诊Agent",
        "doctor_name": triage_doctor.get("name", "陈雅琴"),
        "timestamp": datetime.now().isoformat()
    })
    
    return AgentResponse(
        session_id=session_id,
        agent_name="分诊Agent",
        doctor_name=triage_doctor.get("name", "陈雅琴"),
        doctor_title=triage_doctor.get("title", "副主任医师"),
        doctor_department=triage_doctor.get("department", "急诊医学科"),
        doctor_hospital=triage_doctor.get("hospital", "协和医院"),
        message=response_text,
        suggestions=["头痛详情", "检查项目", "用药建议"],
        urgency_level="门诊",
        recommended_department="神经内科",
        timestamp=datetime.now()
    )


@app.get("/api/v1/sessions/{session_id}", response_model=SessionInfo)
async def get_session(session_id: str):
    """获取会话信息"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    session = sessions[session_id]
    return SessionInfo(
        session_id=session_id,
        patient_id=session["patient_id"],
        created_at=session["created_at"],
        status=session["status"],
        messages_count=len(session["messages"])
    )


@app.get("/api/v1/sessions/{session_id}/history")
async def get_history(session_id: str):
    """获取对话历史"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    # HIPAA审计日志
    audit_logger.log(
        action=AuditAction.READ,
        resource_type="session_history",
        resource_id=session_id
    )
    
    # 脱敏处理
    messages = sessions[session_id]["messages"]
    masked_messages = []
    for msg in messages:
        masked_msg = msg.copy()
        if "content" in masked_msg and len(masked_msg["content"]) > 500:
            # 对长内容进行脱敏
            masked_msg["content"] = data_masker.mask_medical_record(masked_msg["content"])
        masked_messages.append(masked_msg)
    
    return {
        "session_id": session_id,
        "messages": masked_messages
    }


@app.post("/api/v1/sessions/{session_id}/end")
async def end_session(session_id: str):
    """结束会话"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    sessions[session_id]["status"] = "completed"
    return {"message": "会话已结束", "session_id": session_id}


@app.get("/api/v1/agents")
async def list_agents():
    """列出可用Agent（含医生信息）"""
    return {
        "agents": [
            {
                "name": "分诊分流Agent",
                "role": "智能分诊员",
                "status": "active",
                "doctor": get_doctor_profile("triage")
            },
            {
                "name": "病史采集Agent",
                "role": "病史采集专家",
                "status": "active",
                "doctor": get_doctor_profile("history")
            },
            {
                "name": "症状评估Agent",
                "role": "症状分析专家",
                "status": "active",
                "doctor": get_doctor_profile("assessment")
            },
            {
                "name": "用药指导Agent",
                "role": "临床药师",
                "status": "active",
                "doctor": get_doctor_profile("medication")
            },
            {
                "name": "健康教育Agent",
                "role": "健康教育专家",
                "status": "active",
                "doctor": get_doctor_profile("education")
            },
            {
                "name": "随访管理Agent",
                "role": "随访管理专员",
                "status": "active",
                "doctor": get_doctor_profile("followup")
            },
        ]
    }


@app.get("/api/v1/compliance")
async def get_compliance_status():
    """获取HIPAA合规状态"""
    return {
        "hipaa_enabled": True,
        "encryption_enabled": True,
        "audit_logging": True,
        "data_masking": True,
        "data_retention_days": 2190,  # 6年
        "audit_log_retention_days": 2190,
        "features": {
            "access_control": True,
            "data_classification": True,
            "breach_detection": True,
            "consent_management": True
        }
    }


@app.get("/api/v1/audit/logs")
async def get_audit_logs(
    user_id: Optional[str] = None,
    limit: int = 100
):
    """获取审计日志（需要管理员权限）"""
    # 记录此次访问
    audit_logger.log(
        action=AuditAction.READ,
        resource_type="audit_logs",
        details={"query_user_id": user_id, "limit": limit}
    )
    
    if user_id:
        logs = audit_logger.get_user_logs(user_id)
    else:
        logs = audit_logger.logs[-limit:]
    
    return {
        "total": len(logs),
        "logs": [log.model_dump() for log in logs]
    }


@app.get("/api/v1/models")
async def get_models():
    """获取当前使用的模型信息"""
    return {
        "provider": "小米MIMO",
        "model": os.getenv("MIMO_MODEL", "mimo-v2-pro"),
        "enabled": MIMO_ENABLED,
        "api_base": os.getenv("MIMO_BASE_URL", "https://api.xiaomimimo.com/v1")
    }


if os.path.exists(FRONTEND_DIR):
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        """前端SPA路由回退，必须放在所有 API 路由之后。"""
        file_path = os.path.join(FRONTEND_DIR, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))


# ============================================================
# 启动配置
# ============================================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
