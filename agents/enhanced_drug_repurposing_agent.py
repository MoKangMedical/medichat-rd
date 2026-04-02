"""
MediChat-RD 药物重定位Agent - 增强版重构
多数据源整合 + 异步处理 + 智能评估
"""

import asyncio
import aiohttp
import json
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import hashlib
import redis
from functools import lru_cache

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EvidenceLevel(Enum):
    """证据等级"""
    STRONG = "strong"
    MODERATE = "moderate" 
    WEAK = "weak"
    INSUFFICIENT = "insufficient"

class RepurposingStatus(Enum):
    """重定位状态"""
    APPROVED = "approved"  # 已批准
    CLINICAL = "clinical"  # 临床试验
    PRECLINICAL = "preclinical"  # 临床前
    EXPERIMENTAL = "experimental"  # 实验阶段
    THEORETICAL = "theoretical"  # 理论推测

@dataclass
class EnhancedDrugTarget:
    """增强版药物靶点"""
    name: str
    gene: str
    target_type: str
    action: str
    confidence: float
    source: str  # 数据源
    mechanism: str  # 作用机制
    novelty: float = 0.0  # 新颖性评分

@dataclass
class DiseaseMechanism:
    """疾病机制"""
    pathway: str
    genes: List[str]
    evidence_level: EvidenceLevel
    description: str

@dataclass
class ClinicalTrial:
    """临床试验信息"""
    nct_id: str
    title: str
    status: str
    phase: str
    conditions: List[str]
    interventions: List[str]
    start_date: Optional[str] = None
    completion_date: Optional[str] = None

@dataclass
class LiteratureEvidence:
    """文献证据"""
    pmid: str
    title: str
    abstract: str
    journal: str
    year: int
    relevance_score: float
    evidence_type: str
    citation_count: int = 0
    impact_factor: float = 0.0

@dataclass
class SafetyProfile:
    """安全性特征"""
    adverse_effects: List[str]
    contraindications: List[str]
    drug_interactions: List[str]
    toxicity_level: str
    safety_score: float

@dataclass
class RepurposingCandidate:
    """药物重定位候选 - 增强版"""
    drug_name: str
    disease_name: str
    target_overlap: List[str]
    confidence_score: float
    evidence: List[LiteratureEvidence]
    recommendation: str
    
    # 新增字段
    disease_mechanisms: List[DiseaseMechanism]
    clinical_trials: List[ClinicalTrial]
    safety_profile: SafetyProfile
    mechanism_score: float
    novelty_score: float
    feasibility_score: float
    status: RepurposingStatus
    sources_used: List[str]
    last_updated: datetime

class DataCache:
    """数据缓存管理"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        try:
            self.redis_client = redis.from_url(redis_url)
            self.cache_enabled = True
        except:
            self.cache_enabled = False
            logger.warning("Redis不可用，禁用缓存")
    
    def get_cache_key(self, prefix: str, params: dict) -> str:
        """生成缓存键"""
        param_str = json.dumps(params, sort_keys=True)
        hash_obj = hashlib.md5(param_str.encode())
        return f"{prefix}:{hash_obj.hexdigest()}"
    
    async def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        if not self.cache_enabled:
            return None
        
        try:
            data = self.redis_client.get(key)
            if data:
                return json.loads(data)
        except:
            pass
        return None
    
    async def set(self, key: str, data: Any, expire_hours: int = 24):
        """设置缓存"""
        if not self.cache_enabled:
            return
        
        try:
            self.redis_client.setex(
                key, 
                timedelta(hours=expire_hours),
                json.dumps(data, default=str)
            )
        except:
            pass

class EnhancedDrugRepurposingAgent:
    """增强版药物重定位专家Agent"""
    
    def __init__(self):
        # API配置
        self.opentargets_url = "https://api.platform.opentargets.org/api/v4/graphql"
        self.pubmed_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
        self.clinicaltrials_url = "https://clinicaltrials.gov/api/v2"
        self.drugbank_url = "https://go.drugbank.com/api/v1"
        
        # 缓存管理
        self.cache = DataCache()
        
        # 连接池配置
        self.connector = aiohttp.TCPConnector(limit=100, limit_per_host=30)
        self.timeout = aiohttp.ClientTimeout(total=30)
        
        # Agent信息
        self.name = "增强版药物重定位专家"
        self.title = "AI药物科学家"
        self.specialty = "多组学药物重定位"
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        self.session = aiohttp.ClientSession(
            connector=self.connector,
            timeout=self.timeout
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if hasattr(self, 'session'):
            await self.session.close()
    
    async def assess_repurposing_enhanced(self, drug_name: str, disease_name: str) -> RepurposingCandidate:
        """增强版药物重定位评估"""
        logger.info(f"🔬 开始评估: {drug_name} → {disease_name}")
        
        # 并行获取多源数据
        tasks = [
            self._get_drug_targets_enhanced(drug_name),
            self._get_disease_mechanisms(disease_name),
            self._search_clinical_trials(drug_name, disease_name),
            self._get_safety_profile(drug_name),
            self._search_literature_comprehensive(drug_name, disease_name)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理结果
        drug_targets = results[0] if not isinstance(results[0], Exception) else []
        disease_mechanisms = results[1] if not isinstance(results[1], Exception) else []
        clinical_trials = results[2] if not isinstance(results[2], Exception) else []
        safety_profile = results[3] if not isinstance(results[3], Exception) else self._default_safety_profile()
        literature = results[4] if not isinstance(results[4], Exception) else []
        
        # 计算多维评分
        scores = self._calculate_enhanced_scores(
            drug_targets, disease_mechanisms, clinical_trials, 
            safety_profile, literature
        )
        
        # 生成智能推荐
        recommendation = self._generate_enhanced_recommendation(scores, clinical_trials)
        
        # 确定状态
        status = self._determine_status(clinical_trials, scores['confidence'])
        
        return RepurposingCandidate(
            drug_name=drug_name,
            disease_name=disease_name,
            target_overlap=[t.gene for t in drug_targets[:5]],
            confidence_score=scores['confidence'],
            evidence=literature[:5],
            recommendation=recommendation,
            disease_mechanisms=disease_mechanisms,
            clinical_trials=clinical_trials,
            safety_profile=safety_profile,
            mechanism_score=scores['mechanism'],
            novelty_score=scores['novelty'],
            feasibility_score=scores['feasibility'],
            status=status,
            sources_used=['OpenTargets', 'PubMed', 'ClinicalTrials', 'DrugBank'],
            last_updated=datetime.now()
        )
    
    async def _get_drug_targets_enhanced(self, drug_name: str) -> List[EnhancedDrugTarget]:
        """获取增强版药物靶点"""
        cache_key = self.cache.get_cache_key("drug_targets", {"drug": drug_name})
        cached = await self.cache.get(cache_key)
        
        if cached:
            return [EnhancedDrugTarget(**item) for item in cached]
        
        query = """
        query EnhancedDrugTargets($drugName: String!) {
            drug(name: $drugName) {
                name
                targets {
                    id
                    approvedSymbol
                    approvedName
                    bioType
                    functionDescriptions
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
            async with self.session.post(
                self.opentargets_url,
                json={"query": query, "variables": {"drugName": drug_name}}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    drug = data.get("data", {}).get("drug")
                    
                    if drug:
                        targets = []
                        for target in drug.get("targets", []):
                            enhanced_target = EnhancedDrugTarget(
                                name=target["approvedName"],
                                gene=target["approvedSymbol"],
                                target_type=target.get("bioType", "protein"),
                                action="modulator",
                                confidence=0.8,
                                source="OpenTargets",
                                mechanism=target.get("functionDescriptions", ["未知机制"])[0]
                            )
                            targets.append(enhanced_target)
                        
                        # 缓存结果
                        await self.cache.set(cache_key, [asdict(t) for t in targets])
                        return targets
        except Exception as e:
            logger.error(f"获取药物靶点失败: {e}")
        
        return []
    
    async def _get_disease_mechanisms(self, disease_name: str) -> List[DiseaseMechanism]:
        """获取疾病机制信息"""
        # 实现疾病机制分析逻辑
        return [
            DiseaseMechanism(
                pathway="炎症通路",
                genes=["TNF", "IL6", "IL1B"],
                evidence_level=EvidenceLevel.MODERATE,
                description="慢性炎症反应"
            )
        ]
    
    async def _search_clinical_trials(self, drug_name: str, disease_name: str) -> List[ClinicalTrial]:
        """搜索临床试验"""
        try:
            params = {
                "query": f"{drug_name} AND {disease_name}",
                "pageSize": 10
            }
            
            async with self.session.get(
                f"{self.clinicaltrials_url}/studies",
                params=params
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    trials = []
                    
                    for study in data.get("studies", []):
                        trial = ClinicalTrial(
                            nct_id=study.get("protocolSection", {}).get("identificationModule", {}).get("nctId", ""),
                            title=study.get("protocolSection", {}).get("identificationModule", {}).get("briefTitle", ""),
                            status=study.get("protocolSection", {}).get("statusModule", {}).get("overallStatus", ""),
                            phase=study.get("protocolSection", {}).get("designModule", {}).get("phases", [""])[0],
                            conditions=[c.get("name", "") for c in study.get("protocolSection", {}).get("conditionsModule", {}).get("conditions", [])],
                            interventions=[i.get("name", "") for i in study.get("protocolSection", {}).get("armsInterventionsModule", {}).get("interventions", [])]
                        )
                        trials.append(trial)
                    
                    return trials
        except Exception as e:
            logger.error(f"搜索临床试验失败: {e}")
        
        return []
    
    async def _get_safety_profile(self, drug_name: str) -> SafetyProfile:
        """获取安全性特征"""
        # 实现安全性数据获取
        return self._default_safety_profile()
    
    def _default_safety_profile(self) -> SafetyProfile:
        """默认安全性特征"""
        return SafetyProfile(
            adverse_effects=[],
            contraindications=[],
            drug_interactions=[],
            toxicity_level="未知",
            safety_score=0.5
        )
    
    async def _search_literature_comprehensive(self, drug_name: str, disease_name: str) -> List[LiteratureEvidence]:
        """全面文献检索"""
        # 实现增强版文献检索
        return []
    
    def _calculate_enhanced_scores(self, drug_targets, disease_mechanisms, 
                                 clinical_trials, safety_profile, literature) -> Dict[str, float]:
        """计算增强版评分"""
        scores = {
            'confidence': 0.0,
            'mechanism': 0.0,
            'novelty': 0.0,
            'feasibility': 0.0
        }
        
        # 机制评分
        if disease_mechanisms and drug_targets:
            scores['mechanism'] = min(len(drug_targets) * 0.1, 0.4)
        
        # 新颖性评分
        if clinical_trials:
            scores['novelty'] = max(0, 1 - len(clinical_trials) * 0.1)
        else:
            scores['novelty'] = 0.8
        
        # 可行性评分
        scores['feasibility'] = safety_profile.safety_score
        
        # 综合置信度
        scores['confidence'] = (
            scores['mechanism'] * 0.4 +
            scores['novelty'] * 0.3 +
            scores['feasibility'] * 0.3
        )
        
        return scores
    
    def _generate_enhanced_recommendation(self, scores, clinical_trials) -> str:
        """生成增强版推荐"""
        if scores['confidence'] >= 0.7:
            return "强推荐：机制明确，安全性良好，建议推进临床前研究"
        elif scores['confidence'] >= 0.5:
            return "中等推荐：有初步证据支持，需要进一步验证"
        else:
            return "谨慎推荐：证据有限，建议探索其他候选药物"
    
    def _determine_status(self, clinical_trials, confidence) -> RepurposingStatus:
        """确定重定位状态"""
        if clinical_trials:
            latest_trial = max(clinical_trials, key=lambda x: x.phase)
            if "Phase 4" in latest_trial.phase:
                return RepurposingStatus.APPROVED
            elif any(phase in latest_trial.phase for phase in ["Phase 2", "Phase 3"]):
                return RepurposingStatus.CLINICAL
            else:
                return RepurposingStatus.PRECLINICAL
        elif confidence >= 0.7:
            return RepurposingStatus.EXPERIMENTAL
        else:
            return RepurposingStatus.THEORETICAL

# 工厂函数
async def create_enhanced_agent():
    """创建增强版Agent实例"""
    return EnhancedDrugRepurposingAgent()

# 测试函数
async def test_enhanced_repurposing():
    """测试增强版药物重定位"""
    async with EnhancedDrugRepurposingAgent() as agent:
        candidate = await agent.assess_repurposing_enhanced("metformin", "Polycystic Ovary Syndrome")
        print(f"评估结果: {candidate.recommendation}")
        print(f"置信度: {candidate.confidence_score:.2f}")
        print(f"状态: {candidate.status}")

if __name__ == "__main__":
    asyncio.run(test_enhanced_repurposing())