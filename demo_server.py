"""
MediChat-RD Demo 录制专用轻量服务
不需要完整的MIMO依赖
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'agents'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from rare_disease_api import router as rare_disease_router
from community_api import router as community_router
from knowledge_api import router as knowledge_router
from crawler_service import router as crawler_router
from repurposing_api import router as repurposing_router
from rare_disease_agent import RARE_DISEASES_DB, search_rare_disease_by_symptoms
from datetime import datetime
from pydantic import BaseModel
from typing import List, Optional
import os

app = FastAPI(title="MediChat-RD Demo")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.include_router(rare_disease_router)
app.include_router(community_router)
app.include_router(knowledge_router)
app.include_router(crawler_router)
app.include_router(repurposing_router)

# ============================================================
# 患者定位API
# ============================================================

from location_service import PatientLocationService
location_service = PatientLocationService()

@app.post("/api/v1/location")
async def update_location(location: dict):
    """更新患者位置"""
    lat = location.get("latitude")
    lng = location.get("longitude")
    
    if not lat or not lng:
        return {"error": "缺少经纬度信息"}
    
    # 逆地理编码
    location_info = location_service.get_location_from_browser(lat, lng)
    
    return {
        "location": {
            "latitude": location_info.latitude,
            "longitude": location_info.longitude,
            "address": location_info.address,
            "city": location_info.city,
            "province": location_info.province,
            "district": location_info.district,
            "timestamp": location_info.timestamp
        }
    }

@app.get("/api/v1/location/nearby-hospitals")
async def get_nearby_hospitals(
    lat: float = Query(..., description="纬度"),
    lng: float = Query(..., description="经度"),
    radius: int = Query(5000, description="搜索半径（米）")
):
    """获取就近医院"""
    hospitals = location_service.find_nearby_hospitals(lat, lng, radius)
    
    return {
        "total": len(hospitals),
        "hospitals": [
            {
                "name": h.name,
                "address": h.address,
                "distance": h.distance,
                "phone": h.phone,
                "departments": h.departments,
                "specialty": h.specialty,
                "rating": h.rating,
                "source": h.source,
                "url": h.url
            }
            for h in hospitals
        ]
    }

@app.get("/health")
async def health():
    try:
        from knowledge_api import EXTENDED_DB
        diseases_count = len(EXTENDED_DB) if EXTENDED_DB else len(RARE_DISEASES_DB)
    except:
        diseases_count = len(RARE_DISEASES_DB)
    
    return {
        "status": "healthy", 
        "timestamp": datetime.now().isoformat(), 
        "diseases_loaded": diseases_count,
        "extended_knowledge": diseases_count >= 121
    }

@app.get("/api/v1/agents")
async def agents():
    return {"agents": [
        {"name": "症状采集Agent", "doctor": "陈雅琴", "title": "副主任医师", "dept": "急诊医学科"},
        {"name": "基因解读Agent", "doctor": "李明辉", "title": "主任医师", "dept": "内科"},
        {"name": "鉴别诊断Agent", "doctor": "王建国", "title": "主任医师", "dept": "全科医学科"},
        {"name": "方案推荐Agent", "doctor": "赵晓燕", "title": "副主任药师", "dept": "临床药学部"},
    ]}

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

@app.post("/api/v1/chat")
async def chat(req: ChatRequest):
    # 检测是否包含罕见病症状关键词
    msg = req.message
    rd_keywords = ["脾脏肿大", "骨痛", "血小板", "戈谢", "肌无力", "心脏肥大", "庞贝", "肢端疼痛", "少汗", "法布雷"]
    matched = [k for k in rd_keywords if k in msg]
    
    if len(matched) >= 2:
        symptoms = matched
        results = search_rare_disease_by_symptoms(symptoms)
        if results:
            d = results[0]
            return {
                "session_id": "demo_001",
                "agent_name": "鉴别诊断Agent",
                "doctor_name": "王建国",
                "doctor_title": "主任医师",
                "doctor_department": "全科医学科",
                "doctor_hospital": "协和医院",
                "message": f"根据您描述的症状组合——{'、'.join(symptoms)}——我们需要高度警惕罕见病的可能性。\n\n🔍 **罕见病筛查结果：**\n\n1. **{d.name_cn}**（{d.name_en}）匹配度 **95%**\n   - 关键症状：{'、'.join(d.key_symptoms[:4])}\n   - 相关基因：{d.gene}\n   - 诊断方法：{d.diagnosis_method}\n   - 治疗方案：{d.treatment}\n\n⚠️ 建议立即前往【儿童血液科】或【罕见病诊疗中心】就诊。",
                "suggestions": ["了解诊断详情", "治疗方案", "就医建议"],
                "urgency_level": "建议尽快就诊",
                "recommended_department": "儿童血液科 / 罕见病诊疗中心"
            }
    
    return {
        "session_id": "demo_001",
        "agent_name": "分诊Agent",
        "doctor_name": "陈雅琴",
        "doctor_title": "副主任医师",
        "doctor_department": "急诊医学科",
        "doctor_hospital": "协和医院",
        "message": f"您好，我是陈雅琴医生。听到您的描述，我建议您详细说明症状的持续时间、严重程度，以及是否有家族病史。这些信息对准确分诊非常重要。\n\n请问您的症状持续多久了？",
        "suggestions": ["头痛详情", "检查项目", "用药建议"],
        "urgency_level": "门诊",
        "recommended_department": "待定"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


# ============================================================
# 前端静态文件服务
# ============================================================

DIST_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend", "dist")

if os.path.isdir(DIST_DIR):
    # 静态资源（JS/CSS）
    app.mount("/assets", StaticFiles(directory=os.path.join(DIST_DIR, "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        """前端SPA - 所有非API路径返回index.html"""
        file_path = os.path.join(DIST_DIR, full_path)
        if full_path and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(DIST_DIR, "index.html"))
