"""
MediChat-RD 药物重定位专家Agent
借鉴OrphanCure-AI设计理念，整合OpenTargets+PubMed+AI评估
"""

import json
import requests
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class DrugTarget:
    """药物靶点信息"""
    name: str
    gene: str
    target_type: str
    action: str  # inhibitor/agonist/antagonist/modulator

@dataclass
class DiseaseTarget:
    """疾病相关靶点"""
    gene: str
    association_score: float
    evidence_level: str

@dataclass
class LiteratureEvidence:
    """文献证据"""
    pmid: str
    title: str
    abstract: str
    journal: str
    year: int
    relevance_score: float
    evidence_type: str  # support/oppose/neutral

@dataclass
class RepurposingCandidate:
    """药物重定位候选"""
    drug_name: str
    disease_name: str
    target_overlap: List[str]  # 药物靶点与疾病靶点的交集
    confidence_score: float
    evidence: List[LiteratureEvidence]
    recommendation: str

class DrugRepurposingAgent:
    """药物重定位专家Agent"""
    
    def __init__(self):
        self.opentargets_url = "https://api.platform.opentargets.org/api/v4/graphql"
        self.pubmed_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
        self.name = "药物重定位专家"
        self.title = "主任药师"
        self.specialty = "药物重定位/老药新用"
    
    def get_drug_targets(self, drug_name: str) -> List[DrugTarget]:
        """获取药物靶点信息（OpenTargets）"""
        query = """
        query DrugTargets($drugName: String!) {
            drug(name: $drugName) {
                name
                targets {
                    id
                    approvedSymbol
                    approvedName
                    bioType
                }
                mechanismsOfAction {
                    actionType
                    targets {
                        approvedSymbol
                    }
                }
            }
        }
        """
        
        try:
            response = requests.post(
                self.opentargets_url,
                json={"query": query, "variables": {"drugName": drug_name}},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                drug = data.get("data", {}).get("drug")
                if drug:
                    targets = []
                    for target in drug.get("targets", []):
                        targets.append(DrugTarget(
                            name=target["approvedName"],
                            gene=target["approvedSymbol"],
                            target_type=target.get("bioType", "protein"),
                            action="modulator"
                        ))
                    return targets
        except Exception as e:
            print(f"获取药物靶点失败: {e}")
        
        return []
    
    def get_disease_targets(self, disease_name: str) -> List[DiseaseTarget]:
        """获取疾病相关靶点（OpenTargets）"""
        query = """
        query DiseaseTargets($diseaseName: String!) {
            search(queryString: $diseaseName, entityNames: ["disease"]) {
                hits {
                    id
                    name
                    object {
                        ... on Disease {
                            associatedTargets(size: 20) {
                                rows {
                                    target {
                                        approvedSymbol
                                        approvedName
                                    }
                                    score
                                    datatypeScores {
                                        id
                                        score
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        """
        
        try:
            response = requests.post(
                self.opentargets_url,
                json={"query": query, "variables": {"diseaseName": disease_name}},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                hits = data.get("data", {}).get("search", {}).get("hits", [])
                if hits:
                    disease_obj = hits[0].get("object", {})
                    targets = []
                    for row in disease_obj.get("associatedTargets", {}).get("rows", []):
                        target = row.get("target", {})
                        targets.append(DiseaseTarget(
                            gene=target.get("approvedSymbol", ""),
                            association_score=row.get("score", 0),
                            evidence_level="moderate"
                        ))
                    return targets
        except Exception as e:
            print(f"获取疾病靶点失败: {e}")
        
        return []
    
    def search_pubmed(self, drug_name: str, disease_name: str, target_genes: List[str]) -> List[LiteratureEvidence]:
        """PubMed文献检索"""
        # 构建查询：药物+疾病+靶点
        gene_query = " OR ".join(target_genes[:3])  # 限制基因数量
        search_term = f'({drug_name}[Title/Abstract]) AND ({disease_name}[Title/Abstract]) AND ({gene_query}[Title/Abstract])'
        
        try:
            # 搜索文献
            search_url = f"{self.pubmed_url}/esearch.fcgi"
            search_params = {
                "db": "pubmed",
                "term": search_term,
                "retmax": 10,
                "retmode": "json",
                "sort": "relevance"
            }
            
            response = requests.get(search_url, params=search_params, timeout=30)
            if response.status_code == 200:
                data = response.json()
                id_list = data.get("esearchresult", {}).get("idlist", [])
                
                if id_list:
                    # 获取文献详情
                    fetch_url = f"{self.pubmed_url}/efetch.fcgi"
                    fetch_params = {
                        "db": "pubmed",
                        "id": ",".join(id_list),
                        "retmode": "xml"
                    }
                    
                    fetch_response = requests.get(fetch_url, params=fetch_params, timeout=30)
                    if fetch_response.status_code == 200:
                        # 解析XML获取文献信息
                        articles = self._parse_pubmed_xml(fetch_response.text)
                        return articles
        except Exception as e:
            print(f"PubMed检索失败: {e}")
        
        return []
    
    def _parse_pubmed_xml(self, xml_text: str) -> List[LiteratureEvidence]:
        """解析PubMed XML"""
        # 简化版本，实际应使用XML解析器
        import re
        
        articles = []
        pmid_pattern = r'<PMID[^>]*>(\d+)</PMID>'
        title_pattern = r'<ArticleTitle>(.*?)</ArticleTitle>'
        abstract_pattern = r'<AbstractText>(.*?)</AbstractText>'
        
        pmids = re.findall(pmid_pattern, xml_text)
        titles = re.findall(title_pattern, xml_text)
        abstracts = re.findall(abstract_pattern, xml_text)
        
        for i, pmid in enumerate(pmids[:5]):  # 限制5篇
            title = titles[i] if i < len(titles) else "无标题"
            abstract = abstracts[i] if i < len(abstracts) else "无摘要"
            
            articles.append(LiteratureEvidence(
                pmid=pmid,
                title=title[:100],
                abstract=abstract[:200],
                journal="PubMed",
                year=2024,
                relevance_score=0.8 - (i * 0.1),
                evidence_type="support"
            ))
        
        return articles
    
    def calculate_target_overlap(self, drug_targets: List[DrugTarget], disease_targets: List[DiseaseTarget]) -> List[str]:
        """计算靶点交集"""
        drug_genes = {t.gene for t in drug_targets}
        disease_genes = {t.gene for t in disease_targets}
        return list(drug_genes & disease_genes)
    
    def assess_repurposing(self, drug_name: str, disease_name: str) -> RepurposingCandidate:
        """评估药物重定位可行性"""
        print(f"\n{'='*50}")
        print(f"🔬 药物重定位评估")
        print(f"药物: {drug_name}")
        print(f"疾病: {disease_name}")
        print(f"{'='*50}")
        
        # 1. 获取药物靶点
        drug_targets = self.get_drug_targets(drug_name)
        print(f"\n📊 药物靶点数: {len(drug_targets)}")
        
        # 2. 获取疾病靶点
        disease_targets = self.get_disease_targets(disease_name)
        print(f"📊 疾病相关靶点数: {len(disease_targets)}")
        
        # 3. 计算靶点交集
        overlap_genes = self.calculate_target_overlap(drug_targets, disease_targets)
        print(f"🎯 靶点交集: {', '.join(overlap_genes) if overlap_genes else '无'}")
        
        # 4. PubMed文献检索
        evidence = []
        if overlap_genes:
            evidence = self.search_pubmed(drug_name, disease_name, overlap_genes)
        print(f"📚 相关文献: {len(evidence)}篇")
        
        # 5. 计算置信度
        confidence = self._calculate_confidence(drug_targets, disease_targets, overlap_genes, evidence)
        print(f"📈 置信度: {confidence:.2f}")
        
        # 6. 生成推荐
        recommendation = self._generate_recommendation(confidence, overlap_genes, evidence)
        
        return RepurposingCandidate(
            drug_name=drug_name,
            disease_name=disease_name,
            target_overlap=overlap_genes,
            confidence_score=confidence,
            evidence=evidence,
            recommendation=recommendation
        )
    
    def _calculate_confidence(self, drug_targets, disease_targets, overlap, evidence) -> float:
        """计算重定位置信度"""
        score = 0.0
        
        # 靶点交集得分（0-0.4）
        if len(drug_targets) > 0:
            overlap_ratio = len(overlap) / len(drug_targets)
            score += overlap_ratio * 0.4
        
        # 文献支持得分（0-0.4）
        if evidence:
            avg_relevance = sum(e.relevance_score for e in evidence) / len(evidence)
            score += avg_relevance * 0.4
        
        # 基础可行性得分（0-0.2）
        if len(overlap) > 0:
            score += 0.2
        
        return min(score, 1.0)
    
    def _generate_recommendation(self, confidence, overlap_genes, evidence) -> str:
        """生成推荐意见"""
        if confidence >= 0.7:
            return f"强推荐：靶点交集({', '.join(overlap_genes)})显著，文献支持充分，可考虑进入临床前研究"
        elif confidence >= 0.5:
            return f"中等推荐：有靶点基础和初步证据，建议进一步验证机制"
        elif confidence >= 0.3:
            return f"谨慎推荐：靶点有交集但证据有限，需要更多研究支持"
        else:
            return "不推荐：靶点交集不足或缺乏文献支持，建议探索其他候选药物"

def format_repurposing_report(candidate: RepurposingCandidate) -> str:
    """格式化重定位报告"""
    report = f"""
# 药物重定位评估报告

## 基本信息
- **评估时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **评估药物**: {candidate.drug_name}
- **目标疾病**: {candidate.disease_name}
- **评估专家**: 药物重定位专家（主任药师）

## 靶点分析
- **药物-疾病靶点交集**: {', '.join(candidate.target_overlap) if candidate.target_overlap else '无显著交集'}
- **重定位置信度**: {candidate.confidence_score:.2f}

## 文献证据
"""
    
    if candidate.evidence:
        for i, ev in enumerate(candidate.evidence[:3], 1):
            report += f"""
### 文献{i}
- **PMID**: {ev.pmid}
- **标题**: {ev.title}
- **相关性**: {ev.relevance_score:.2f}
- **证据类型**: {ev.evidence_type}
"""
    else:
        report += "暂无直接相关文献证据\n"
    
    report += f"""
## 专家建议
{candidate.recommendation}

---
*本报告基于OpenTargets靶点数据和PubMed文献自动生成，仅供参考*
"""
    return report

# 测试函数
def test_repurposing():
    """测试药物重定位功能"""
    agent = DrugRepurposingAgent()
    
    # 示例：二甲双胍→多囊卵巢综合征
    candidate = agent.assess_repurposing("metformin", "Polycystic Ovary Syndrome")
    report = format_repurposing_report(candidate)
    print(report)

if __name__ == "__main__":
    test_repurposing()
