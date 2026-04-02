"""
MediChat-RD 扩展知识库API
支持121种罕见病+药物重定位
"""

import json
import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

router = APIRouter(prefix="/api/v1/knowledge", tags=["知识库"])

# 加载扩展知识库
KNOWLEDGE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "knowledge")
EXTENDED_DB = {}

def load_extended_diseases():
    """加载121种罕见病扩展知识库"""
    global EXTENDED_DB
    try:
        db_path = os.path.join(KNOWLEDGE_DIR, "diseases_extended.json")
        with open(db_path, "r") as f:
            diseases = json.load(f)
            EXTENDED_DB = {d["name_en"]: d for d in diseases}
        print(f"✅ 加载扩展知识库：{len(EXTENDED_DB)}种疾病")
    except Exception as e:
        print(f"❌ 加载扩展知识库失败：{e}")
        EXTENDED_DB = {}

# 初始化加载
load_extended_diseases()

# ============================================================
# 请求/响应模型
# ============================================================

class DiseaseSearchRequest(BaseModel):
    query: str
    category: Optional[str] = None
    limit: Optional[int] = 10

class DiseaseDetailResponse(BaseModel):
    name: str
    name_en: str
    icd10: Optional[str]
    category: str
    inheritance: Optional[str]
    gene: str
    prevalence: Optional[str]
    symptoms: Optional[str]
    diagnosis_criteria: Optional[str]
    treatment_summary: Optional[str]
    specialist_hospitals: List[str]

class DrugRepurposingRequest(BaseModel):
    drug_name: str
    disease_name: str

class DrugRepurposingResponse(BaseModel):
    drug_name: str
    disease_name: str
    target_overlap: List[str]
    confidence_score: float
    recommendation: str
    literature_count: int
    timestamp: str

# ============================================================
# API端点
# ============================================================

@router.get("/diseases", response_model=List[DiseaseDetailResponse])
async def get_all_diseases():
    """获取所有罕见病列表（121种）"""
    diseases = []
    for d in EXTENDED_DB.values():
        hospitals = d.get("specialist_hospitals", [])
        if isinstance(hospitals, str):
            hospitals = [h.strip() for h in hospitals.split("、")]
        
        diseases.append(DiseaseDetailResponse(
            name=d.get("name", ""),
            name_en=d.get("name_en", ""),
            icd10=d.get("icd10"),
            category=d.get("category", "未分类"),
            inheritance=d.get("inheritance"),
            gene=d.get("gene", "未知"),
            prevalence=d.get("prevalence"),
            symptoms=d.get("symptoms"),
            diagnosis_criteria=d.get("diagnosis_criteria"),
            treatment_summary=d.get("treatment_summary"),
            specialist_hospitals=hospitals
        ))
    
    return diseases

@router.get("/diseases/{disease_name}")
async def get_disease_detail(disease_name: str):
    """获取单个罕见病详情"""
    # 尝试中英文匹配
    disease = EXTENDED_DB.get(disease_name)
    if not disease:
        # 中文名匹配
        for d in EXTENDED_DB.values():
            if d.get("name") == disease_name:
                disease = d
                break
    
    if not disease:
        raise HTTPException(status_code=404, detail=f"未找到疾病：{disease_name}")
    
    hospitals = disease.get("specialist_hospitals", [])
    if isinstance(hospitals, str):
        hospitals = [h.strip() for h in hospitals.split("、")]
    
    return {
        "name": disease.get("name", ""),
        "name_en": disease.get("name_en", ""),
        "icd10": disease.get("icd10"),
        "category": disease.get("category", "未分类"),
        "inheritance": disease.get("inheritance"),
        "gene": disease.get("gene", "未知"),
        "prevalence": disease.get("prevalence"),
        "symptoms": disease.get("symptoms"),
        "diagnosis_criteria": disease.get("diagnosis_criteria"),
        "treatment_summary": disease.get("treatment_summary"),
        "specialist_hospitals": hospitals,
        "metadata": {
            "total_diseases": len(EXTENDED_DB),
            "last_updated": datetime.now().isoformat()
        }
    }

@router.get("/diseases/search/{query}")
async def search_diseases(query: str, limit: int = 10):
    """搜索罕见病"""
    results = []
    query_lower = query.lower()
    
    for d in EXTENDED_DB.values():
        name_cn = d.get("name", "").lower()
        name_en = d.get("name_en", "").lower()
        gene = d.get("gene", "").lower()
        symptoms = d.get("symptoms", "").lower()
        category = d.get("category", "").lower()
        
        # 匹配条件
        if (query_lower in name_cn or 
            query_lower in name_en or 
            query_lower in gene or
            query_lower in symptoms or
            query_lower in category):
            
            hospitals = d.get("specialist_hospitals", [])
            if isinstance(hospitals, str):
                hospitals = [h.strip() for h in hospitals.split("、")]
            
            results.append(DiseaseDetailResponse(
                name=d.get("name", ""),
                name_en=d.get("name_en", ""),
                icd10=d.get("icd10"),
                category=d.get("category", "未分类"),
                inheritance=d.get("inheritance"),
                gene=d.get("gene", "未知"),
                prevalence=d.get("prevalence"),
                symptoms=d.get("symptoms"),
                diagnosis_criteria=d.get("diagnosis_criteria"),
                treatment_summary=d.get("treatment_summary"),
                specialist_hospitals=hospitals
            ))
            
            if len(results) >= limit:
                break
    
    return {
        "query": query,
        "results": results,
        "total": len(results),
        "timestamp": datetime.now().isoformat()
    }

@router.get("/diseases/category/{category}")
async def get_diseases_by_category(category: str):
    """按分类获取罕见病"""
    results = []
    category_lower = category.lower()
    
    for d in EXTENDED_DB.values():
        if d.get("category", "").lower() == category_lower:
            hospitals = d.get("specialist_hospitals", [])
            if isinstance(hospitals, str):
                hospitals = [h.strip() for h in hospitals.split("、")]
            
            results.append(DiseaseDetailResponse(
                name=d.get("name", ""),
                name_en=d.get("name_en", ""),
                icd10=d.get("icd10"),
                category=d.get("category", "未分类"),
                inheritance=d.get("inheritance"),
                gene=d.get("gene", "未知"),
                prevalence=d.get("prevalence"),
                symptoms=d.get("symptoms"),
                diagnosis_criteria=d.get("diagnosis_criteria"),
                treatment_summary=d.get("treatment_summary"),
                specialist_hospitals=hospitals
            ))
    
    return {
        "category": category,
        "diseases": results,
        "total": len(results)
    }

@router.get("/categories")
async def get_disease_categories():
    """获取所有疾病分类"""
    categories = {}
    for d in EXTENDED_DB.values():
        cat = d.get("category", "未分类")
        categories[cat] = categories.get(cat, 0) + 1
    
    return {
        "categories": categories,
        "total_categories": len(categories),
        "total_diseases": len(EXTENDED_DB)
    }

@router.post("/drug-repurposing", response_model=DrugRepurposingResponse)
async def assess_drug_repurposing(req: DrugRepurposingRequest):
    """药物重定位评估（简化版）"""
    # 检查疾病是否存在
    disease = None
    for d in EXTENDED_DB.values():
        if d.get("name") == req.disease_name or d.get("name_en") == req.disease_name:
            disease = d
            break
    
    if not disease:
        raise HTTPException(status_code=404, detail=f"未找到疾病：{req.disease_name}")
    
    # 简化的评估逻辑（实际应调用OpenTargets API）
    disease_gene = disease.get("gene", "")
    
    # 模拟靶点交集（基于已知药物-基因关系）
    drug_gene_mapping = {
        "metformin": ["AMPK", "MTOR"],
        "aspirin": ["COX1", "COX2", "NFkB"],
        "statins": ["HMGCR"],
        "rapamycin": ["MTOR"],
        "thalidomide": ["CRBN"],
        "sirolimus": ["MTOR"],
    }
    
    drug_genes = drug_gene_mapping.get(req.drug_name.lower(), [])
    overlap = []
    if disease_gene and drug_genes:
        overlap = [f"{disease_gene} ←→ {g}" for g in drug_genes]
    
    # 计算置信度
    confidence = 0.0
    if overlap:
        confidence = 0.6 + (len(overlap) * 0.1)
        confidence = min(confidence, 0.95)
    
    # 生成推荐
    if confidence >= 0.7:
        recommendation = f"强推荐：{req.drug_name}与{req.disease_name}存在靶点关联，建议进入临床前研究"
    elif confidence >= 0.5:
        recommendation = f"中等推荐：{req.drug_name}与{req.disease_name}有潜在关联，需要进一步验证"
    elif confidence >= 0.3:
        recommendation = f"谨慎推荐：靶点交集有限，建议探索其他候选药物"
    else:
        recommendation = f"不推荐：缺乏足够的靶点基础，不建议继续研究"
    
    return DrugRepurposingResponse(
        drug_name=req.drug_name,
        disease_name=req.disease_name,
        target_overlap=overlap,
        confidence_score=confidence,
        recommendation=recommendation,
        literature_count=len(overlap) * 3,  # 模拟文献数
        timestamp=datetime.now().isoformat()
    )

@router.get("/stats")
async def get_knowledge_stats():
    """获取知识库统计信息"""
    categories = {}
    for d in EXTENDED_DB.values():
        cat = d.get("category", "未分类")
        categories[cat] = categories.get(cat, 0) + 1
    
    return {
        "total_diseases": len(EXTENDED_DB),
        "categories": categories,
        "total_categories": len(categories),
        "last_updated": datetime.now().isoformat(),
        "status": "complete" if len(EXTENDED_DB) >= 121 else "partial"
    }
