"""
MediChat-RD 增强版药物重定位Agent
参考OrphanCure-AI架构，实现完整的药物重定位评估流程
"""

import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from opentargets_service import OpenTargetsService, EntityCandidate, DrugTarget, DiseaseTarget
from pubmed_service import PubMedService, Paper, EvidencePolarity, LiteratureEvidence

logger = logging.getLogger(__name__)

class VerificationStatus(Enum):
    """验证状态"""
    VERIFIED = "verified"
    PARTIALLY_VERIFIED = "partially_verified"
    UNVERIFIED = "unverified"

@dataclass
class RepurposingClaim:
    """药物重定位声明"""
    claim_text: str
    evidence: List[LiteratureEvidence]
    polarity: EvidencePolarity
    confidence: float
    verification_status: VerificationStatus
    source_papers: List[str]  # PMIDs

@dataclass
class RepurposingReport:
    """药物重定位报告"""
    # 基本信息
    drug_name: str
    drug_id: str
    disease_name: str
    disease_id: str
    
    # 实体解析结果
    drug_candidates: List[EntityCandidate]
    disease_candidates: List[EntityCandidate]
    
    # 靶点分析
    drug_targets: List[DrugTarget]
    disease_targets: List[DiseaseTarget]
    target_overlap: List[Dict]
    
    # 文献证据
    papers: List[Paper]
    literature_stats: Dict
    
    # 声明和验证
    claims: List[RepurposingClaim]
    
    # 综合评估
    overall_score: float
    confidence_level: str  # high / medium / low
    recommendation: str
    
    # 质量评估
    completeness_score: float
    quality_gates_passed: int
    quality_gates_total: int
    
    # 元数据
    timestamp: str
    processing_time: float

class EnhancedDrugRepurposingAgent:
    """增强版药物重定位Agent"""
    
    def __init__(self):
        self.opentargets = OpenTargetsService()
        self.pubmed = PubMedService()
        
        # 质量门控配置
        self.quality_gates = {
            "entity_resolved": False,
            "targets_found": False,
            "target_overlap": False,
            "literature_found": False,
            "evidence_classified": False,
            "claims_generated": False
        }
    
    # ============================================================
    # 实体解析
    # ============================================================
    
    def resolve_entities(
        self,
        drug_name: str,
        disease_name: str,
        auto_select: bool = True
    ) -> Tuple[Optional[EntityCandidate], Optional[EntityCandidate], List[EntityCandidate], List[EntityCandidate]]:
        """解析药物和疾病实体"""
        logger.info(f"解析实体: {drug_name} + {disease_name}")
        
        # 搜索候选实体
        drug_candidates = self.opentargets.search_drug(drug_name)
        disease_candidates = self.opentargets.search_disease(disease_name)
        
        drug_entity = None
        disease_entity = None
        
        if auto_select:
            # 自动选择得分最高的候选
            if drug_candidates:
                drug_entity = drug_candidates[0]
                logger.info(f"自动选择药物: {drug_entity.name} ({drug_entity.id})")
            
            if disease_candidates:
                disease_entity = disease_candidates[0]
                logger.info(f"自动选择疾病: {disease_entity.name} ({disease_entity.id})")
        
        # 更新质量门控
        if drug_entity and disease_entity:
            self.quality_gates["entity_resolved"] = True
        
        return drug_entity, disease_entity, drug_candidates, disease_candidates
    
    # ============================================================
    # 靶点分析
    # ============================================================
    
    def analyze_targets(
        self,
        drug_id: str,
        disease_id: str
    ) -> Tuple[List[DrugTarget], List[DiseaseTarget], List[Dict]]:
        """分析靶点和交集"""
        logger.info(f"分析靶点: {drug_id} vs {disease_id}")
        
        # 获取药物靶点
        drug_targets = self.opentargets.get_drug_targets(drug_id)
        logger.info(f"药物靶点: {len(drug_targets)}")
        
        # 获取疾病靶点
        disease_targets = self.opentargets.get_disease_targets(disease_id)
        logger.info(f"疾病靶点: {len(disease_targets)}")
        
        # 计算交集
        overlap = self.opentargets.calculate_target_overlap(drug_targets, disease_targets)
        logger.info(f"靶点交集: {len(overlap)}")
        
        # 更新质量门控
        if drug_targets or disease_targets:
            self.quality_gates["targets_found"] = True
        if overlap:
            self.quality_gates["target_overlap"] = True
        
        return drug_targets, disease_targets, overlap
    
    # ============================================================
    # 文献检索
    # ============================================================
    
    def retrieve_literature(
        self,
        drug_name: str,
        disease_name: str,
        targets: List[str] = None
    ) -> Tuple[List[Paper], Dict]:
        """检索相关文献"""
        logger.info(f"检索文献: {drug_name} + {disease_name}")
        
        papers, stats = self.pubmed.comprehensive_search(
            drug_name,
            disease_name,
            targets=targets
        )
        
        logger.info(f"找到 {len(papers)} 篇文献")
        
        # 更新质量门控
        if papers:
            self.quality_gates["literature_found"] = True
            self.quality_gates["evidence_classified"] = True
        
        return papers, stats
    
    # ============================================================
    # 声明生成和验证
    # ============================================================
    
    def generate_claims(
        self,
        drug_name: str,
        disease_name: str,
        target_overlap: List[Dict],
        papers: List[Paper]
    ) -> List[RepurposingClaim]:
        """生成药物重定位声明"""
        claims = []
        
        # 基于靶点交集的声明
        if target_overlap:
            overlap_symbols = [o["symbol"] for o in target_overlap[:3]]
            
            claim = RepurposingClaim(
                claim_text=f"{drug_name} 可能通过作用于 {', '.join(overlap_symbols)} 等靶点对 {disease_name} 产生治疗效果",
                evidence=[],
                polarity=EvidencePolarity.SUPPORTING,
                confidence=0.7,
                verification_status=VerificationStatus.PARTIALLY_VERIFIED,
                source_papers=[]
            )
            claims.append(claim)
        
        # 基于文献的声明
        supporting_papers = [p for p in papers if p.evidence_polarity == EvidencePolarity.SUPPORTING]
        if supporting_papers:
            claim = RepurposingClaim(
                claim_text=f"已有 {len(supporting_papers)} 篇文献支持 {drug_name} 对 {disease_name} 的潜在治疗效果",
                evidence=[],
                polarity=EvidencePolarity.SUPPORTING,
                confidence=0.8,
                verification_status=VerificationStatus.VERIFIED,
                source_papers=[p.pmid for p in supporting_papers[:5]]
            )
            claims.append(claim)
        
        contradicting_papers = [p for p in papers if p.evidence_polarity == EvidencePolarity.CONTRADICTING]
        if contradicting_papers:
            claim = RepurposingClaim(
                claim_text=f"有 {len(contradicting_papers)} 篇文献报告了 {drug_name} 治疗 {disease_name} 的负面结果或不良反应",
                evidence=[],
                polarity=EvidencePolarity.CONTRADICTING,
                confidence=0.6,
                verification_status=VerificationStatus.VERIFIED,
                source_papers=[p.pmid for p in contradicting_papers[:3]]
            )
            claims.append(claim)
        
        # 更新质量门控
        if claims:
            self.quality_gates["claims_generated"] = True
        
        return claims
    
    # ============================================================
    # 综合评估
    # ============================================================
    
    def calculate_overall_score(
        self,
        target_overlap: List[Dict],
        papers: List[Paper],
        claims: List[RepurposingClaim]
    ) -> Tuple[float, str]:
        """计算综合评分"""
        score = 0.0
        
        # 靶点交集得分（0-40分）
        if target_overlap:
            target_score = min(len(target_overlap) * 10, 40)
            score += target_score
        
        # 文献支持得分（0-40分）
        supporting = [p for p in papers if p.evidence_polarity == EvidencePolarity.SUPPORTING]
        contradicting = [p for p in papers if p.evidence_polarity == EvidencePolarity.CONTRADICTING]
        
        if papers:
            support_ratio = len(supporting) / len(papers)
            literature_score = support_ratio * 40
            score += literature_score
        
        # 负面证据扣分
        if contradicting:
            penalty = min(len(contradicting) * 5, 20)
            score -= penalty
        
        # 声明质量得分（0-20分）
        if claims:
            verified_claims = [c for c in claims if c.verification_status == VerificationStatus.VERIFIED]
            claim_score = (len(verified_claims) / len(claims)) * 20
            score += claim_score
        
        # 确保分数在0-100之间
        score = max(0, min(100, score))
        
        # 确定置信度等级
        if score >= 70:
            confidence = "high"
        elif score >= 40:
            confidence = "medium"
        else:
            confidence = "low"
        
        return score, confidence
    
    def generate_recommendation(
        self,
        score: float,
        confidence: str,
        target_overlap: List[Dict],
        papers: List[Paper]
    ) -> str:
        """生成推荐意见"""
        if confidence == "high":
            return (
                f"强推荐：{len(target_overlap)}个靶点交集，{len(papers)}篇相关文献提供充分支持。"
                f"建议进入临床前研究阶段，进一步验证机制和安全性。"
            )
        elif confidence == "medium":
            return (
                f"中等推荐：存在{len(target_overlap)}个靶点交集和{len(papers)}篇文献支持，"
                f"但证据强度有限。建议补充更多机制研究和临床数据。"
            )
        else:
            return (
                f"谨慎推荐：靶点交集有限或文献支持不足。"
                f"建议探索其他候选药物，或等待更多研究证据。"
            )
    
    # ============================================================
    # 质量门控
    # ============================================================
    
    def evaluate_quality(self) -> Tuple[float, int, int]:
        """评估质量门控"""
        passed = sum(1 for v in self.quality_gates.values() if v)
        total = len(self.quality_gates)
        completeness = passed / total if total > 0 else 0
        
        return completeness, passed, total
    
    # ============================================================
    # 完整评估流程
    # ============================================================
    
    def assess_repurposing(
        self,
        drug_name: str,
        disease_name: str,
        auto_select: bool = True
    ) -> RepurposingReport:
        """完整的药物重定位评估"""
        start_time = datetime.now()
        
        # 重置质量门控
        for key in self.quality_gates:
            self.quality_gates[key] = False
        
        # 1. 实体解析
        drug_entity, disease_entity, drug_candidates, disease_candidates = self.resolve_entities(
            drug_name, disease_name, auto_select
        )
        
        if not drug_entity or not disease_entity:
            logger.error("实体解析失败")
            return self._create_error_report(drug_name, disease_name)
        
        # 2. 靶点分析
        drug_targets, disease_targets, target_overlap = self.analyze_targets(
            drug_entity.id, disease_entity.id
        )
        
        # 3. 文献检索
        target_symbols = [o["symbol"] for o in target_overlap]
        papers, lit_stats = self.retrieve_literature(
            drug_entity.name, disease_entity.name, target_symbols
        )
        
        # 4. 声明生成
        claims = self.generate_claims(
            drug_entity.name, disease_entity.name, target_overlap, papers
        )
        
        # 5. 综合评估
        overall_score, confidence = self.calculate_overall_score(target_overlap, papers, claims)
        recommendation = self.generate_recommendation(overall_score, confidence, target_overlap, papers)
        
        # 6. 质量评估
        completeness, gates_passed, gates_total = self.evaluate_quality()
        
        # 计算处理时间
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return RepurposingReport(
            drug_name=drug_entity.name,
            drug_id=drug_entity.id,
            disease_name=disease_entity.name,
            disease_id=disease_entity.id,
            drug_candidates=drug_candidates,
            disease_candidates=disease_candidates,
            drug_targets=drug_targets,
            disease_targets=disease_targets,
            target_overlap=target_overlap,
            papers=papers,
            literature_stats=lit_stats,
            claims=claims,
            overall_score=overall_score,
            confidence_level=confidence,
            recommendation=recommendation,
            completeness_score=completeness,
            quality_gates_passed=gates_passed,
            quality_gates_total=gates_total,
            timestamp=datetime.now().isoformat(),
            processing_time=processing_time
        )
    
    def _create_error_report(self, drug_name: str, disease_name: str) -> RepurposingReport:
        """创建错误报告"""
        return RepurposingReport(
            drug_name=drug_name,
            drug_id="",
            disease_name=disease_name,
            disease_id="",
            drug_candidates=[],
            disease_candidates=[],
            drug_targets=[],
            disease_targets=[],
            target_overlap=[],
            papers=[],
            literature_stats={},
            claims=[],
            overall_score=0,
            confidence_level="low",
            recommendation="无法完成评估：实体解析失败",
            completeness_score=0,
            quality_gates_passed=0,
            quality_gates_total=len(self.quality_gates),
            timestamp=datetime.now().isoformat(),
            processing_time=0
        )

# 格式化报告
def format_repurposing_report(report: RepurposingReport) -> str:
    """格式化药物重定位报告"""
    
    output = []
    output.append("=" * 60)
    output.append("药物重定位评估报告")
    output.append("=" * 60)
    
    # 基本信息
    output.append(f"\n📋 基本信息")
    output.append(f"  药物: {report.drug_name} ({report.drug_id})")
    output.append(f"  疾病: {report.disease_name} ({report.disease_id})")
    output.append(f"  评估时间: {report.timestamp}")
    output.append(f"  处理耗时: {report.processing_time:.2f}秒")
    
    # 实体解析
    output.append(f"\n🔍 实体解析")
    output.append(f"  药物候选: {len(report.drug_candidates)}个")
    output.append(f"  疾病候选: {len(report.disease_candidates)}个")
    
    # 靶点分析
    output.append(f"\n🎯 靶点分析")
    output.append(f"  药物靶点: {len(report.drug_targets)}个")
    output.append(f"  疾病靶点: {len(report.disease_targets)}个")
    output.append(f"  靶点交集: {len(report.target_overlap)}个")
    
    if report.target_overlap:
        output.append(f"\n  靶点交集详情:")
        for i, overlap in enumerate(report.target_overlap[:5], 1):
            output.append(f"    {i}. {overlap['symbol']}: {overlap['drug_action']} (score: {overlap['disease_association_score']:.2f})")
    
    # 文献证据
    output.append(f"\n📚 文献证据")
    output.append(f"  总文献数: {report.literature_stats.get('total_papers', 0)}")
    output.append(f"  支持性证据: {report.literature_stats.get('polarity_counts', {}).get('supporting', 0)}")
    output.append(f"  反对性证据: {report.literature_stats.get('polarity_counts', {}).get('contradicting', 0)}")
    output.append(f"  不确定证据: {report.literature_stats.get('polarity_counts', {}).get('inconclusive', 0)}")
    
    # 声明
    if report.claims:
        output.append(f"\n📝 评估声明")
        for i, claim in enumerate(report.claims, 1):
            output.append(f"  {i}. {claim.claim_text}")
            output.append(f"     极性: {claim.polarity.value} | 置信度: {claim.confidence:.2f} | 状态: {claim.verification_status.value}")
    
    # 综合评估
    output.append(f"\n📊 综合评估")
    output.append(f"  综合评分: {report.overall_score:.1f}/100")
    output.append(f"  置信度等级: {report.confidence_level}")
    output.append(f"\n  推荐意见:")
    output.append(f"  {report.recommendation}")
    
    # 质量门控
    output.append(f"\n✅ 质量门控")
    output.append(f"  完整度: {report.completeness_score*100:.0f}%")
    output.append(f"  通过: {report.quality_gates_passed}/{report.quality_gates_total}")
    
    output.append("\n" + "=" * 60)
    
    return "\n".join(output)

# 测试
if __name__ == "__main__":
    agent = EnhancedDrugRepurposingAgent()
    
    print("开始评估: metformin + diabetes")
    report = agent.assess_repurposing("metformin", "diabetes")
    
    print(format_repurposing_report(report))
