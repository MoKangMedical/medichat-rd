"""
MediChat-RD Claim级验证服务
参考OrphanCure-AI，验证生成的声明是否与原始摘要一致
"""

import re
import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class VerificationStatus(Enum):
    """验证状态"""
    VERIFIED = "verified"                # 已验证
    PARTIALLY_VERIFIED = "partially_verified"  # 部分验证
    UNVERIFIED = "unverified"            # 未验证
    CONTRADICTED = "contradicted"        # 被反驳

@dataclass
class ClaimVerification:
    """声明验证结果"""
    claim: str
    status: VerificationStatus
    confidence: float
    matched_sentences: List[str]
    source_pmids: List[str]
    explanation: str

class ClaimVerifier:
    """Claim级验证器"""
    
    def __init__(self):
        # 支持性证据关键词
        self.support_keywords = [
            "effective", "efficacy", "beneficial", "improvement", "treatment",
            "therapeutic", "promising", "successful", "positive", "significant",
            "reduces", "decreases", "improves", "enhances", "prevents"
        ]
        
        # 反对性证据关键词
        self.contradict_keywords = [
            "ineffective", "no effect", "failed", "adverse", "toxicity",
            "negative", "contraindicated", "risk", "worse", "harmful",
            "increases", "worsens", "aggravates", "detrimental"
        ]
        
        # 不确定性关键词
        self.uncertain_keywords = [
            "may", "might", "could", "possibly", "potential", "suggests",
            "indicates", "preliminary", "limited evidence", "further studies needed"
        ]
    
    def verify_claim(
        self,
        claim: str,
        papers: List[Dict],
        drug: str,
        disease: str
    ) -> ClaimVerification:
        """验证单个声明"""
        
        # 从声明中提取关键信息
        claim_lower = claim.lower()
        drug_lower = drug.lower()
        disease_lower = disease.lower()
        
        # 收集相关句子
        matched_sentences = []
        source_pmids = []
        
        for paper in papers:
            abstract = paper.get("abstract", "").lower()
            title = paper.get("title", "").lower()
            pmid = paper.get("pmid", "")
            
            # 检查是否包含药物和疾病
            if drug_lower in abstract and disease_lower in abstract:
                # 提取相关句子
                sentences = self._extract_relevant_sentences(
                    abstract, drug_lower, disease_lower
                )
                
                if sentences:
                    matched_sentences.extend(sentences)
                    if pmid not in source_pmids:
                        source_pmids.append(pmid)
        
        # 分析匹配的句子
        if not matched_sentences:
            return ClaimVerification(
                claim=claim,
                status=VerificationStatus.UNVERIFIED,
                confidence=0.0,
                matched_sentences=[],
                source_pmids=[],
                explanation="未找到相关证据支持此声明"
            )
        
        # 计算支持/反对比例
        support_count = 0
        contradict_count = 0
        
        for sentence in matched_sentences:
            if any(kw in sentence for kw in self.support_keywords):
                support_count += 1
            if any(kw in sentence for kw in self.contradict_keywords):
                contradict_count += 1
        
        total = len(matched_sentences)
        
        # 确定验证状态
        if support_count > contradict_count and support_count > 0:
            status = VerificationStatus.VERIFIED
            confidence = support_count / total
            explanation = f"找到 {support_count} 个支持性证据，{contradict_count} 个反对性证据"
        elif contradict_count > support_count and contradict_count > 0:
            status = VerificationStatus.CONTRADICTED
            confidence = contradict_count / total
            explanation = f"找到 {contradict_count} 个反对性证据，{support_count} 个支持性证据"
        elif support_count > 0 and contradict_count > 0:
            status = VerificationStatus.PARTIALLY_VERIFIED
            confidence = 0.5
            explanation = f"找到混合证据：{support_count} 个支持，{contradict_count} 个反对"
        else:
            status = VerificationStatus.PARTIALLY_VERIFIED
            confidence = 0.3
            explanation = f"找到 {total} 个相关句子，但无法明确判断极性"
        
        return ClaimVerification(
            claim=claim,
            status=status,
            confidence=confidence,
            matched_sentences=matched_sentences[:5],  # 最多返回5个
            source_pmids=source_pmids,
            explanation=explanation
        )
    
    def _extract_relevant_sentences(
        self,
        text: str,
        drug: str,
        disease: str
    ) -> List[str]:
        """提取相关句子"""
        sentences = re.split(r'[.!?]+', text)
        relevant = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 20:  # 太短的句子跳过
                continue
            
            # 检查是否包含药物和疾病
            if drug in sentence and disease in sentence:
                relevant.append(sentence)
            # 或者包含药物且与疾病相关
            elif drug in sentence and any(
                word in sentence for word in [disease, "diabetes", "diabetic"]
            ):
                relevant.append(sentence)
        
        return relevant
    
    def verify_claims_batch(
        self,
        claims: List[str],
        papers: List[Dict],
        drug: str,
        disease: str
    ) -> List[ClaimVerification]:
        """批量验证声明"""
        results = []
        
        for claim in claims:
            verification = self.verify_claim(claim, papers, drug, disease)
            results.append(verification)
        
        return results
    
    def generate_verification_report(
        self,
        verifications: List[ClaimVerification]
    ) -> str:
        """生成验证报告"""
        output = []
        output.append("=" * 60)
        output.append("Claim级验证报告")
        output.append("=" * 60)
        
        for i, v in enumerate(verifications, 1):
            output.append(f"\n{i}. 声明: {v.claim}")
            output.append(f"   状态: {v.status.value}")
            output.append(f"   置信度: {v.confidence:.2f}")
            output.append(f"   解释: {v.explanation}")
            
            if v.matched_sentences:
                output.append(f"   相关证据:")
                for j, sentence in enumerate(v.matched_sentences[:3], 1):
                    output.append(f"     {j}. {sentence[:100]}...")
            
            if v.source_pmids:
                output.append(f"   来源: {', '.join(v.source_pmids)}")
        
        # 统计
        total = len(verifications)
        verified = sum(1 for v in verifications if v.status == VerificationStatus.VERIFIED)
        partially = sum(1 for v in verifications if v.status == VerificationStatus.PARTIALLY_VERIFIED)
        contradicted = sum(1 for v in verifications if v.status == VerificationStatus.CONTRADICTED)
        unverified = sum(1 for v in verifications if v.status == VerificationStatus.UNVERIFIED)
        
        output.append(f"\n" + "=" * 60)
        output.append(f"验证统计:")
        output.append(f"  总声明数: {total}")
        output.append(f"  已验证: {verified} ({verified/total*100:.0f}%)")
        output.append(f"  部分验证: {partially} ({partially/total*100:.0f}%)")
        output.append(f"  被反驳: {contradicted} ({contradicted/total*100:.0f}%)")
        output.append(f"  未验证: {unverified} ({unverified/total*100:.0f}%)")
        output.append("=" * 60)
        
        return "\n".join(output)

# 测试
if __name__ == "__main__":
    verifier = ClaimVerifier()
    
    # 模拟声明
    claims = [
        "Metformin有效治疗糖尿病",
        "Metformin可能增加心血管风险",
        "Metformin对癌症有潜在益处"
    ]
    
    # 模拟论文
    papers = [
        {
            "pmid": "33176588",
            "title": "Metformin and diabetes",
            "abstract": "Metformin is effective in treating type 2 diabetes. It significantly reduces blood glucose levels and improves insulin sensitivity."
        },
        {
            "pmid": "34428850",
            "title": "Metformin and cardiovascular outcomes",
            "abstract": "Metformin therapy was associated with improved cardiovascular outcomes in patients with diabetes."
        }
    ]
    
    # 验证声明
    verifications = verifier.verify_claims_batch(claims, papers, "metformin", "diabetes")
    
    # 生成报告
    report = verifier.generate_verification_report(verifications)
    print(report)
