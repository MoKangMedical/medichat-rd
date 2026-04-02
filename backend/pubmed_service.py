"""
MediChat-RD PubMed E-utilities 服务
参考OrphanCure-AI实现，支持多策略查询和多维度重排序
"""

import requests
import logging
import xml.etree.ElementTree as ET
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)

class EvidencePolarity(Enum):
    """证据极性"""
    SUPPORTING = "supporting"      # 支持
    CONTRADICTING = "contradicting"  # 反对
    INCONCLUSIVE = "inconclusive"  # 不确定

@dataclass
class Paper:
    """论文信息"""
    pmid: str
    title: str
    abstract: str
    authors: List[str]
    journal: str
    year: int
    doi: str
    keywords: List[str]
    relevance_score: float = 0.0
    evidence_polarity: Optional[EvidencePolarity] = None
    verified: bool = False

@dataclass
class RetrievalQuery:
    """检索查询"""
    query_text: str
    query_type: str  # basic / expanded / target
    max_results: int = 20

@dataclass
class LiteratureEvidence:
    """文献证据"""
    paper: Paper
    claim: str
    polarity: EvidencePolarity
    confidence: float
    source_abstract: str

class PubMedService:
    """PubMed E-utilities 服务"""
    
    def __init__(self):
        self.search_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
        self.fetch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
        self.summary_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
        
        # 速率限制（NCBI要求每秒不超过3个请求）
        self.request_delay = 0.34
        self.last_request_time = 0
    
    def _rate_limit(self):
        """速率限制"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.request_delay:
            time.sleep(self.request_delay - elapsed)
        self.last_request_time = time.time()
    
    # ============================================================
    # 基础API调用
    # ============================================================
    
    def search_ids(self, query: str, max_results: int = 20) -> List[str]:
        """搜索PubMed，返回PMID列表"""
        self._rate_limit()
        
        params = {
            "db": "pubmed",
            "term": query,
            "retmode": "json",
            "retmax": max_results,
            "sort": "relevance"
        }
        
        try:
            response = requests.get(self.search_url, params=params, timeout=15)
            if response.ok:
                data = response.json()
                return data.get("esearchresult", {}).get("idlist", [])
        except Exception as e:
            logger.error(f"PubMed search failed: {e}")
        
        return []
    
    def fetch_details(self, pmids: List[str]) -> List[Paper]:
        """获取论文详情"""
        if not pmids:
            return []
        
        self._rate_limit()
        
        params = {
            "db": "pubmed",
            "id": ",".join(pmids),
            "retmode": "xml"
        }
        
        try:
            response = requests.get(self.fetch_url, params=params, timeout=20)
            if response.ok:
                return self._parse_xml(response.text)
        except Exception as e:
            logger.error(f"PubMed fetch failed: {e}")
        
        return []
    
    def _parse_xml(self, xml_text: str) -> List[Paper]:
        """解析PubMed XML"""
        papers = []
        
        try:
            root = ET.fromstring(xml_text)
            
            for article in root.findall(".//PubmedArticle"):
                try:
                    paper = self._parse_article(article)
                    if paper:
                        papers.append(paper)
                except Exception as e:
                    logger.error(f"Failed to parse article: {e}")
                    continue
        except ET.ParseError as e:
            logger.error(f"XML parse error: {e}")
        
        return papers
    
    def _parse_article(self, article) -> Optional[Paper]:
        """解析单篇文章"""
        # PMID
        pmid_elem = article.find(".//PMID")
        pmid = pmid_elem.text if pmid_elem is not None else ""
        
        # 标题
        title_elem = article.find(".//ArticleTitle")
        title = "".join(title_elem.itertext()) if title_elem is not None else ""
        
        # 摘要
        abstract_parts = []
        for abstract_text in article.findall(".//AbstractText"):
            label = abstract_text.get("Label", "")
            text = "".join(abstract_text.itertext())
            if label:
                abstract_parts.append(f"{label}: {text}")
            else:
                abstract_parts.append(text)
        abstract = "\n".join(abstract_parts)
        
        # 作者
        authors = []
        for author in article.findall(".//Author"):
            last_name = author.find("LastName")
            fore_name = author.find("ForeName")
            if last_name is not None:
                name = last_name.text or ""
                if fore_name is not None:
                    name = f"{fore_name.text} {name}"
                authors.append(name)
        
        # 期刊
        journal_elem = article.find(".//Journal/Title")
        journal = journal_elem.text if journal_elem is not None else ""
        
        # 年份
        year_elem = article.find(".//PubDate/Year")
        year = int(year_elem.text) if year_elem is not None else 0
        
        # DOI
        doi = ""
        for article_id in article.findall(".//ArticleId"):
            if article_id.get("IdType") == "doi":
                doi = article_id.text or ""
                break
        
        # 关键词
        keywords = []
        for keyword in article.findall(".//Keyword"):
            if keyword.text:
                keywords.append(keyword.text)
        
        return Paper(
            pmid=pmid,
            title=title,
            abstract=abstract,
            authors=authors,
            journal=journal,
            year=year,
            doi=doi,
            keywords=keywords
        )
    
    # ============================================================
    # 多策略查询
    # ============================================================
    
    def build_queries(
        self,
        drug: str,
        disease: str,
        drug_aliases: List[str] = None,
        disease_aliases: List[str] = None,
        targets: List[str] = None,
        year_start: int = 2010
    ) -> List[RetrievalQuery]:
        """构建多种查询策略"""
        queries = []
        
        # 基础查询
        basic_query = f'({drug}[Title/Abstract]) AND ({disease}[Title/Abstract])'
        queries.append(RetrievalQuery(
            query_text=basic_query,
            query_type="basic",
            max_results=20
        ))
        
        # 扩展查询（包含同义词）
        if drug_aliases or disease_aliases:
            drug_terms = [drug] + (drug_aliases or [])
            disease_terms = [disease] + (disease_aliases or [])
            
            drug_query = " OR ".join([f'"{t}"[Title/Abstract]' for t in drug_terms])
            disease_query = " OR ".join([f'"{t}"[Title/Abstract]' for t in disease_terms])
            
            expanded_query = f'({drug_query}) AND ({disease_query})'
            queries.append(RetrievalQuery(
                query_text=expanded_query,
                query_type="expanded",
                max_results=30
            ))
        
        # 靶点查询
        if targets:
            target_query = " OR ".join([f'{t}[Title/Abstract]' for t in targets[:5]])
            target_full_query = f'({drug}[Title/Abstract]) AND ({disease}[Title/Abstract]) AND ({target_query})'
            queries.append(RetrievalQuery(
                query_text=target_full_query,
                query_type="target",
                max_results=15
            ))
        
        # 添加时间限制
        for q in queries:
            q.query_text = f'{q.query_text} AND ({year_start}:3000[PDAT])'
        
        return queries
    
    def execute_queries(self, queries: List[RetrievalQuery]) -> List[Paper]:
        """执行多个查询，合并去重结果"""
        all_papers = {}
        
        for query in queries:
            pmids = self.search_ids(query.query_text, query.max_results)
            papers = self.fetch_details(pmids[:query.max_results])
            
            for paper in papers:
                if paper.pmid not in all_papers:
                    all_papers[paper.pmid] = paper
        
        return list(all_papers.values())
    
    # ============================================================
    # 重排序
    # ============================================================
    
    def rerank_papers(
        self,
        papers: List[Paper],
        drug: str,
        disease: str,
        targets: List[str] = None
    ) -> List[Paper]:
        """多维度重排序"""
        for paper in papers:
            score = 0.0
            
            title_lower = paper.title.lower()
            abstract_lower = paper.abstract.lower()
            drug_lower = drug.lower()
            disease_lower = disease.lower()
            
            # 标题匹配（权重最高）
            if drug_lower in title_lower and disease_lower in title_lower:
                score += 3.0
            elif drug_lower in title_lower or disease_lower in title_lower:
                score += 1.5
            
            # 摘要匹配
            if drug_lower in abstract_lower and disease_lower in abstract_lower:
                score += 2.0
            
            # 靶点匹配
            if targets:
                for target in targets:
                    if target.lower() in abstract_lower:
                        score += 0.5
            
            # 时效性（近5年加分）
            current_year = datetime.now().year
            if paper.year >= current_year - 5:
                score += 0.5
            if paper.year >= current_year - 2:
                score += 0.5
            
            # 摘要长度（有完整摘要的优先）
            if len(paper.abstract) > 500:
                score += 0.3
            
            paper.relevance_score = score
        
        # 按分数排序
        papers.sort(key=lambda x: x.relevance_score, reverse=True)
        
        return papers
    
    # ============================================================
    # 证据分类
    # ============================================================
    
    def classify_evidence(self, paper: Paper, drug: str, disease: str) -> EvidencePolarity:
        """简单的证据极性分类"""
        text = (paper.title + " " + paper.abstract).lower()
        
        # 支持性证据关键词
        support_keywords = [
            "effective", "efficacy", "beneficial", "improvement", "treatment",
            "therapeutic", "promising", "successful", "positive", "significant"
        ]
        
        # 反对性证据关键词
        contradict_keywords = [
            "ineffective", "no effect", "failed", "adverse", "toxicity",
            "negative", "contraindicated", "risk", "worse", "harmful"
        ]
        
        support_count = sum(1 for kw in support_keywords if kw in text)
        contradict_count = sum(1 for kw in contradict_keywords if kw in text)
        
        if support_count > contradict_count:
            return EvidencePolarity.SUPPORTING
        elif contradict_count > support_count:
            return EvidencePolarity.CONTRADICTING
        else:
            return EvidencePolarity.INCONCLUSIVE
    
    # ============================================================
    # 综合检索
    # ============================================================
    
    def comprehensive_search(
        self,
        drug: str,
        disease: str,
        drug_aliases: List[str] = None,
        disease_aliases: List[str] = None,
        targets: List[str] = None
    ) -> Tuple[List[Paper], Dict]:
        """综合文献检索"""
        # 构建查询
        queries = self.build_queries(
            drug, disease,
            drug_aliases, disease_aliases,
            targets
        )
        
        # 执行查询
        papers = self.execute_queries(queries)
        
        # 重排序
        papers = self.rerank_papers(papers, drug, disease, targets)
        
        # 证据分类
        for paper in papers:
            paper.evidence_polarity = self.classify_evidence(paper, drug, disease)
        
        # 统计信息
        stats = {
            "total_papers": len(papers),
            "queries_executed": len(queries),
            "polarity_counts": {
                "supporting": sum(1 for p in papers if p.evidence_polarity == EvidencePolarity.SUPPORTING),
                "contradicting": sum(1 for p in papers if p.evidence_polarity == EvidencePolarity.CONTRADICTING),
                "inconclusive": sum(1 for p in papers if p.evidence_polarity == EvidencePolarity.INCONCLUSIVE)
            }
        }
        
        return papers, stats

# 测试
if __name__ == "__main__":
    service = PubMedService()
    
    print("搜索文献: metformin + diabetes")
    papers, stats = service.comprehensive_search("metformin", "diabetes")
    
    print(f"\n找到 {stats['total_papers']} 篇文献")
    print(f"证据分类:")
    print(f"  - 支持: {stats['polarity_counts']['supporting']}")
    print(f"  - 反对: {stats['polarity_counts']['contradicting']}")
    print(f"  - 不确定: {stats['polarity_counts']['inconclusive']}")
    
    print(f"\n前5篇文献:")
    for i, paper in enumerate(papers[:5], 1):
        print(f"\n{i}. {paper.title}")
        print(f"   PMID: {paper.pmid} | 年份: {paper.year}")
        print(f"   证据: {paper.evidence_polarity.value if paper.evidence_polarity else 'unknown'}")
        print(f"   相关性: {paper.relevance_score:.2f}")
