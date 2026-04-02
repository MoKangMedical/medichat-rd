"""
MediChat-RD OpenTargets GraphQL 服务
参考OrphanCure-AI实现，对接真实OpenTargets API
"""

import requests
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class EntityCandidate:
    """实体候选项"""
    id: str
    name: str
    score: float
    entity_type: str  # drug / disease

@dataclass
class DrugTarget:
    """药物靶点"""
    symbol: str
    name: str
    action_type: str  # inhibitor / agonist / antagonist / modulator

@dataclass
class DiseaseTarget:
    """疾病相关靶点"""
    symbol: str
    name: str
    score: float
    datatype_scores: Dict[str, float]

class OpenTargetsService:
    """OpenTargets Platform GraphQL API 服务"""
    
    def __init__(self):
        self.base_url = "https://api.platform.opentargets.org/api/v4/graphql"
        self.timeout = 15
    
    def _execute_query(self, query: str, variables: Dict = None) -> Dict:
        """执行GraphQL查询"""
        try:
            payload = {"query": query}
            if variables:
                payload["variables"] = variables
            
            response = requests.post(
                self.base_url,
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                if "errors" in result:
                    logger.error(f"GraphQL errors: {result['errors']}")
                    return {}
                return result.get("data", {})
            else:
                logger.error(f"OpenTargets API error: {response.status_code}")
                return {}
        except Exception as e:
            logger.error(f"OpenTargets query failed: {e}")
            return {}
    
    # ============================================================
    # 实体搜索
    # ============================================================
    
    def search_drug(self, drug_name: str, size: int = 5) -> List[EntityCandidate]:
        """搜索药物实体"""
        query = """
        query SearchDrug($q: String!, $size: Int!) {
            search(queryString: $q, entityNames: ["drug"], page: {index: 0, size: $size}) {
                hits {
                    id
                    name
                    score
                    entity
                }
            }
        }
        """
        
        data = self._execute_query(query, {"q": drug_name, "size": size})
        hits = data.get("search", {}).get("hits", [])
        
        return [
            EntityCandidate(
                id=hit["id"],
                name=hit["name"],
                score=hit["score"],
                entity_type="drug"
            )
            for hit in hits
        ]
    
    def search_disease(self, disease_name: str, size: int = 5) -> List[EntityCandidate]:
        """搜索疾病实体"""
        query = """
        query SearchDisease($q: String!, $size: Int!) {
            search(queryString: $q, entityNames: ["disease"], page: {index: 0, size: $size}) {
                hits {
                    id
                    name
                    score
                    entity
                }
            }
        }
        """
        
        data = self._execute_query(query, {"q": disease_name, "size": size})
        hits = data.get("search", {}).get("hits", [])
        
        return [
            EntityCandidate(
                id=hit["id"],
                name=hit["name"],
                score=hit["score"],
                entity_type="disease"
            )
            for hit in hits
        ]
    
    # ============================================================
    # 药物详情
    # ============================================================
    
    def get_drug_details(self, drug_id: str) -> Dict:
        """获取药物详情（包括作用机制和靶点）"""
        query = """
        query DrugDetails($id: String!) {
            drug(chemblId: $id) {
                id
                name
                drugType
                maximumClinicalTrialPhase
                mechanismsOfAction {
                    rows {
                        actionType
                        targets {
                            id
                            approvedSymbol
                            approvedName
                        }
                    }
                }
                approvedIndications
            }
        }
        """
        
        data = self._execute_query(query, {"id": drug_id})
        return data.get("drug", {})
    
    def get_drug_targets(self, drug_id: str) -> List[DrugTarget]:
        """获取药物靶点列表"""
        drug = self.get_drug_details(drug_id)
        targets = []
        
        for mechanism in drug.get("mechanismsOfAction", {}).get("rows", []):
            action_type = mechanism.get("actionType", "modulator")
            for target in mechanism.get("targets", []):
                targets.append(DrugTarget(
                    symbol=target.get("approvedSymbol", ""),
                    name=target.get("approvedName", ""),
                    action_type=action_type
                ))
        
        return targets
    
    # ============================================================
    # 疾病详情
    # ============================================================
    
    def get_disease_details(self, disease_id: str) -> Dict:
        """获取疾病详情（包括相关靶点）"""
        query = """
        query DiseaseDetails($id: String!) {
            disease(efoId: $id) {
                id
                name
                description
                therapeuticAreas {
                    id
                    name
                }
                associatedTargets(page: {index: 0, size: 100}) {
                    count
                    rows {
                        target {
                            id
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
        """
        
        data = self._execute_query(query, {"id": disease_id})
        return data.get("disease", {})
    
    def get_disease_targets(self, disease_id: str, min_score: float = 0.1) -> List[DiseaseTarget]:
        """获取疾病相关靶点列表"""
        disease = self.get_disease_details(disease_id)
        targets = []
        
        for row in disease.get("associatedTargets", {}).get("rows", []):
            score = row.get("score", 0)
            if score < min_score:
                continue
            
            target = row.get("target", {})
            datatype_scores = {
                ds["id"]: ds["score"]
                for ds in row.get("datatypeScores", [])
            }
            
            targets.append(DiseaseTarget(
                symbol=target.get("approvedSymbol", ""),
                name=target.get("approvedName", ""),
                score=score,
                datatype_scores=datatype_scores
            ))
        
        return targets
    
    # ============================================================
    # 靶点交集计算
    # ============================================================
    
    def calculate_target_overlap(
        self,
        drug_targets: List[DrugTarget],
        disease_targets: List[DiseaseTarget]
    ) -> List[Dict]:
        """计算药物靶点与疾病靶点的交集"""
        drug_symbols = {t.symbol for t in drug_targets}
        disease_symbols = {t.symbol for t in disease_targets}
        
        overlap_symbols = drug_symbols & disease_symbols
        
        overlap_details = []
        for symbol in overlap_symbols:
            drug_target = next((t for t in drug_targets if t.symbol == symbol), None)
            disease_target = next((t for t in disease_targets if t.symbol == symbol), None)
            
            if drug_target and disease_target:
                overlap_details.append({
                    "symbol": symbol,
                    "name": drug_target.name,
                    "drug_action": drug_target.action_type,
                    "disease_association_score": disease_target.score,
                    "datatype_scores": disease_target.datatype_scores
                })
        
        # 按疾病关联分数排序
        overlap_details.sort(key=lambda x: x["disease_association_score"], reverse=True)
        
        return overlap_details

# 测试
if __name__ == "__main__":
    service = OpenTargetsService()
    
    # 测试搜索药物
    print("搜索药物 metformin:")
    drugs = service.search_drug("metformin")
    for d in drugs[:3]:
        print(f"  - {d.name} ({d.id}) - score: {d.score:.2f}")
    
    # 测试搜索疾病
    print("\n搜索疾病 Gaucher disease:")
    diseases = service.search_disease("Gaucher disease")
    for d in diseases[:3]:
        print(f"  - {d.name} ({d.id}) - score: {d.score:.2f}")
    
    if drugs and diseases:
        # 测试靶点交集
        print("\n计算靶点交集:")
        drug_targets = service.get_drug_targets(drugs[0].id)
        disease_targets = service.get_disease_targets(diseases[0].id)
        
        print(f"  药物靶点: {len(drug_targets)}")
        print(f"  疾病靶点: {len(disease_targets)}")
        
        overlap = service.calculate_target_overlap(drug_targets, disease_targets)
        print(f"  靶点交集: {len(overlap)}")
        for o in overlap[:5]:
            print(f"    - {o['symbol']}: {o['drug_action']} (score: {o['disease_association_score']:.2f})")
