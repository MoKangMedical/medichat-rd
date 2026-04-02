"""
MediChat-RD - 罕见病诊断API
RD DECODE 48 黑客松参赛作品
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime
import sys
import os

# 导入罕见病模块
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'agents'))
from rare_disease_agent import (
    RARE_DISEASES_DB,
    search_rare_disease_by_symptoms,
    get_disease_info,
    format_disease_report,
    RARE_DISEASE_SYSTEM_PROMPT,
    RareDisease,
    RareDiseaseCategory
)

router = APIRouter(prefix="/api/v1/rare-disease", tags=["罕见病诊断"])


# ============================================================
# 数据模型
# ============================================================
class SymptomInput(BaseModel):
    """症状输入"""
    symptoms: List[str] = Field(..., description="症状列表")
    age: Optional[int] = Field(None, description="年龄")
    gender: Optional[str] = Field(None, description="性别")
    family_history: Optional[str] = Field(None, description="家族史")
    duration: Optional[str] = Field(None, description="症状持续时间")


class GeneReportInput(BaseModel):
    """基因报告输入"""
    gene_name: str = Field(..., description="基因名称")
    variant: str = Field(..., description="变异类型")
    zygosity: Optional[str] = Field(None, description="杂合性")


class DiagnosisResult(BaseModel):
    """诊断结果"""
    disease_name: str
    disease_name_en: str
    confidence: float
    match_symptoms: List[str]
    omim_id: Optional[str]
    gene: Optional[str]
    diagnosis_method: str
    treatment: str


class DiagnosisResponse(BaseModel):
    """诊断响应"""
    session_id: str
    input_symptoms: List[str]
    possible_diagnoses: List[DiagnosisResult]
    recommended_actions: List[str]
    timestamp: datetime


# ============================================================
# API端点
# ============================================================
@router.get("/diseases")
async def list_rare_diseases():
    """列出所有罕见病"""
    return {
        "total": len(RARE_DISEASES_DB),
        "diseases": [
            {
                "name_cn": d.name_cn,
                "name_en": d.name_en,
                "omim_id": d.omim_id,
                "category": d.category.value,
                "gene": d.gene
            }
            for d in RARE_DISEASES_DB
        ]
    }


@router.get("/diseases/{disease_name}")
async def get_disease_detail(disease_name: str):
    """获取罕见病详情"""
    disease = get_disease_info(disease_name)
    if not disease:
        raise HTTPException(status_code=404, detail=f"未找到疾病: {disease_name}")
    
    return {
        "name_cn": disease.name_cn,
        "name_en": disease.name_en,
        "omim_id": disease.omim_id,
        "category": disease.category.value,
        "prevalence": disease.prevalence,
        "inheritance": disease.inheritance,
        "key_symptoms": disease.key_symptoms,
        "gene": disease.gene,
        "diagnosis_method": disease.diagnosis_method,
        "treatment": disease.treatment
    }


@router.post("/diagnose", response_model=DiagnosisResponse)
async def diagnose_by_symptoms(input_data: SymptomInput):
    """
    根据症状进行罕见病筛查
    
    示例输入：
    {
        "symptoms": ["脾脏肿大", "骨痛", "血小板减少"],
        "age": 5,
        "gender": "男"
    }
    """
    # 搜索匹配的罕见病
    matched_diseases = search_rare_disease_by_symptoms(input_data.symptoms)
    
    # 构建诊断结果
    diagnoses = []
    for disease in matched_diseases[:5]:  # 最多返回5个结果
        # 计算匹配症状
        match_symptoms = []
        for symptom in input_data.symptoms:
            for key_symptom in disease.key_symptoms:
                if symptom in key_symptom or key_symptom in symptom:
                    match_symptoms.append(key_symptom)
                    break
        
        # 计算置信度（简化版）
        confidence = len(match_symptoms) / len(disease.key_symptoms) * 100
        
        diagnoses.append(DiagnosisResult(
            disease_name=disease.name_cn,
            disease_name_en=disease.name_en,
            confidence=round(confidence, 1),
            match_symptoms=match_symptoms,
            omim_id=disease.omim_id,
            gene=disease.gene,
            diagnosis_method=disease.diagnosis_method,
            treatment=disease.treatment
        ))
    
    # 生成建议
    recommended_actions = [
        "建议前往罕见病诊疗中心就诊",
        "携带既往检查资料",
        "如有家族史请详细告知医生"
    ]
    
    if matched_diseases:
        first_disease = matched_diseases[0]
        recommended_actions.insert(0, f"建议进行{first_disease.diagnosis_method}")
    
    return DiagnosisResponse(
        session_id=f"rd_{datetime.now().strftime('%Y%m%d%H%M%S')}",
        input_symptoms=input_data.symptoms,
        possible_diagnoses=diagnoses,
        recommended_actions=recommended_actions,
        timestamp=datetime.now()
    )


@router.post("/gene-analysis")
async def analyze_gene_report(input_data: GeneReportInput):
    """分析基因报告"""
    # 查找相关罕见病
    related_diseases = []
    for disease in RARE_DISEASES_DB:
        if disease.gene and input_data.gene_name.upper() in disease.gene.upper():
            related_diseases.append(disease)
    
    if not related_diseases:
        return {
            "gene": input_data.gene_name,
            "variant": input_data.variant,
            "related_diseases": [],
            "recommendation": "未找到与该基因相关的罕见病信息，建议咨询遗传学专家。"
        }
    
    return {
        "gene": input_data.gene_name,
        "variant": input_data.variant,
        "zygosity": input_data.zygosity,
        "related_diseases": [
            {
                "name_cn": d.name_cn,
                "name_en": d.name_en,
                "omim_id": d.omim_id,
                "inheritance": d.inheritance,
                "key_symptoms": d.key_symptoms,
                "treatment": d.treatment
            }
            for d in related_diseases
        ],
        "recommendation": f"该基因与{len(related_diseases)}种罕见病相关，建议进行详细的遗传咨询。"
    }


@router.get("/categories")
async def list_categories():
    """列出罕见病分类"""
    categories = {}
    for disease in RARE_DISEASES_DB:
        cat = disease.category.value
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(disease.name_cn)
    
    return {
        "categories": [
            {"name": name, "diseases": diseases}
            for name, diseases in categories.items()
        ]
    }


@router.get("/statistics")
async def get_statistics():
    """获取罕见病统计信息"""
    return {
        "total_diseases": len(RARE_DISEASES_DB),
        "total_patients_china": "约2000万",
        "avg_diagnosis_time": "4.3年",
        "target_diagnosis_time": "48小时",
        "diseases_with_treatment": sum(1 for d in RARE_DISEASES_DB if d.treatment),
        "diseases_with_gene": sum(1 for d in RARE_DISEASES_DB if d.gene),
        "categories": len(set(d.category for d in RARE_DISEASES_DB))
    }
