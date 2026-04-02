"""
MediChat-RD 增强版药物重定位API
集成OpenTargets + PubMed + 证据分类 + 质量门控
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'agents'))

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime

from enhanced_repurposing_agent import (
    EnhancedDrugRepurposingAgent,
    RepurposingReport,
    format_repurposing_report
)

router = APIRouter(prefix="/api/v1/repurposing", tags=["药物重定位"])

# 全局Agent实例
agent = EnhancedDrugRepurposingAgent()

# ============================================================
# 请求/响应模型
# ============================================================

class RepurposingRequest(BaseModel):
    drug_name: str
    disease_name: str
    auto_select: bool = True

class EntityCandidateResponse(BaseModel):
    id: str
    name: str
    score: float

class TargetOverlapResponse(BaseModel):
    symbol: str
    name: str
    drug_action: str
    disease_association_score: float

class ClaimResponse(BaseModel):
    claim_text: str
    polarity: str
    confidence: float
    verification_status: str
    source_papers: List[str]

class RepurposingResponse(BaseModel):
    # 基本信息
    drug_name: str
    drug_id: str
    disease_name: str
    disease_id: str
    
    # 实体解析
    drug_candidates: List[EntityCandidateResponse]
    disease_candidates: List[EntityCandidateResponse]
    
    # 靶点分析
    drug_targets_count: int
    disease_targets_count: int
    target_overlap: List[TargetOverlapResponse]
    
    # 文献证据
    total_papers: int
    supporting_papers: int
    contradicting_papers: int
    inconclusive_papers: int
    
    # 声明
    claims: List[ClaimResponse]
    
    # 综合评估
    overall_score: float
    confidence_level: str
    recommendation: str
    
    # 质量评估
    completeness_score: float
    quality_gates_passed: int
    quality_gates_total: int
    
    # 元数据
    timestamp: str
    processing_time: float
    formatted_report: str

# ============================================================
# API端点
# ============================================================

@router.post("/assess", response_model=RepurposingResponse)
async def assess_repurposing(req: RepurposingRequest):
    """药物重定位评估（增强版）"""
    try:
        # 执行评估
        report = agent.assess_repurposing(
            drug_name=req.drug_name,
            disease_name=req.disease_name,
            auto_select=req.auto_select
        )
        
        # 格式化报告
        formatted = format_repurposing_report(report)
        
        # 构建响应
        return RepurposingResponse(
            # 基本信息
            drug_name=report.drug_name,
            drug_id=report.drug_id,
            disease_name=report.disease_name,
            disease_id=report.disease_id,
            
            # 实体解析
            drug_candidates=[
                EntityCandidateResponse(id=c.id, name=c.name, score=c.score)
                for c in report.drug_candidates[:5]
            ],
            disease_candidates=[
                EntityCandidateResponse(id=c.id, name=c.name, score=c.score)
                for c in report.disease_candidates[:5]
            ],
            
            # 靶点分析
            drug_targets_count=len(report.drug_targets),
            disease_targets_count=len(report.disease_targets),
            target_overlap=[
                TargetOverlapResponse(
                    symbol=o["symbol"],
                    name=o["name"],
                    drug_action=o["drug_action"],
                    disease_association_score=o["disease_association_score"]
                )
                for o in report.target_overlap
            ],
            
            # 文献证据
            total_papers=report.literature_stats.get("total_papers", 0),
            supporting_papers=report.literature_stats.get("polarity_counts", {}).get("supporting", 0),
            contradicting_papers=report.literature_stats.get("polarity_counts", {}).get("contradicting", 0),
            inconclusive_papers=report.literature_stats.get("polarity_counts", {}).get("inconclusive", 0),
            
            # 声明
            claims=[
                ClaimResponse(
                    claim_text=c.claim_text,
                    polarity=c.polarity.value,
                    confidence=c.confidence,
                    verification_status=c.verification_status.value,
                    source_papers=c.source_papers
                )
                for c in report.claims
            ],
            
            # 综合评估
            overall_score=report.overall_score,
            confidence_level=report.confidence_level,
            recommendation=report.recommendation,
            
            # 质量评估
            completeness_score=report.completeness_score,
            quality_gates_passed=report.quality_gates_passed,
            quality_gates_total=report.quality_gates_total,
            
            # 元数据
            timestamp=report.timestamp,
            processing_time=report.processing_time,
            formatted_report=formatted
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"评估失败: {str(e)}")

@router.get("/search/drug/{drug_name}")
async def search_drug(drug_name: str, limit: int = 5):
    """搜索药物实体"""
    try:
        candidates = agent.opentargets.search_drug(drug_name, limit)
        return {
            "drug_name": drug_name,
            "candidates": [
                {"id": c.id, "name": c.name, "score": c.score}
                for c in candidates
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")

@router.get("/search/disease/{disease_name}")
async def search_disease(disease_name: str, limit: int = 5):
    """搜索疾病实体"""
    try:
        candidates = agent.opentargets.search_disease(disease_name, limit)
        return {
            "disease_name": disease_name,
            "candidates": [
                {"id": c.id, "name": c.name, "score": c.score}
                for c in candidates
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")

@router.get("/targets/drug/{drug_id}")
async def get_drug_targets(drug_id: str):
    """获取药物靶点"""
    try:
        targets = agent.opentargets.get_drug_targets(drug_id)
        return {
            "drug_id": drug_id,
            "targets_count": len(targets),
            "targets": [
                {"symbol": t.symbol, "name": t.name, "action_type": t.action_type}
                for t in targets
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取靶点失败: {str(e)}")

@router.get("/targets/disease/{disease_id}")
async def get_disease_targets(disease_id: str, min_score: float = 0.1):
    """获取疾病相关靶点"""
    try:
        targets = agent.opentargets.get_disease_targets(disease_id, min_score)
        return {
            "disease_id": disease_id,
            "targets_count": len(targets),
            "targets": [
                {
                    "symbol": t.symbol,
                    "name": t.name,
                    "score": t.score,
                    "datatype_scores": t.datatype_scores
                }
                for t in targets[:20]
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取靶点失败: {str(e)}")

@router.get("/literature/search")
async def search_literature(
    drug: str,
    disease: str,
    targets: Optional[str] = None,  # 逗号分隔的靶点符号
    max_results: int = 20
):
    """搜索相关文献"""
    try:
        target_list = targets.split(",") if targets else None
        
        papers, stats = agent.pubmed.comprehensive_search(
            drug, disease, targets=target_list
        )
        
        return {
            "drug": drug,
            "disease": disease,
            "stats": stats,
            "papers": [
                {
                    "pmid": p.pmid,
                    "title": p.title,
                    "year": p.year,
                    "journal": p.journal,
                    "evidence_polarity": p.evidence_polarity.value if p.evidence_polarity else None,
                    "relevance_score": p.relevance_score,
                    "abstract_preview": p.abstract[:200] + "..." if len(p.abstract) > 200 else p.abstract
                }
                for p in papers[:max_results]
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文献搜索失败: {str(e)}")
