"""
MediChat-RD — 药物-靶点网络分析模块
构建药物-靶点-疾病网络，支持药物重定位
"""
import json
from typing import List, Dict, Tuple, Set
from dataclasses import dataclass, field


@dataclass
class Drug:
    """药物节点"""
    drug_id: str
    name: str
    drug_type: str  # small_molecule / biologic / gene_therapy
    approval_status: str  # approved / clinical / preclinical
    indications: List[str] = field(default_factory=list)
    targets: List[str] = field(default_factory=list)


@dataclass
class Target:
    """靶点节点"""
    target_id: str
    name: str
    gene: str
    target_type: str  # protein / enzyme / receptor / channel
    diseases: List[str] = field(default_factory=list)


@dataclass
class DrugTargetEdge:
    """药物-靶点边"""
    drug_id: str
    target_id: str
    interaction_type: str  # inhibitor / agonist / antagonist / modulator
    potency: float  # IC50, EC50, Ki (nM)
    evidence_level: str  # experimental / clinical / computational


class DrugTargetNetwork:
    """药物-靶点网络"""

    def __init__(self):
        self.drugs: Dict[str, Drug] = {}
        self.targets: Dict[str, Target] = {}
        self.edges: List[DrugTargetEdge] = []
        self._build_network()

    def _build_network(self):
        """构建网络"""
        # 药物节点
        drugs_data = {
            "D001": Drug("D001", "溴吡斯的明", "small_molecule", "approved",
                         ["重症肌无力"], ["T001"]),
            "D002": Drug("D002", "依库珠单抗", "biologic", "approved",
                         ["重症肌无力", "PNH"], ["T002"]),
            "D003": Drug("D003", "伊米苷酶", "biologic", "approved",
                         ["戈谢病"], ["T003"]),
            "D004": Drug("D004", "Spinraza", "biologic", "approved",
                         ["脊髓性肌萎缩症"], ["T004"]),
            "D005": Drug("D005", "Zolgensma", "gene_therapy", "approved",
                         ["脊髓性肌萎缩症"], ["T004"]),
            "D006": Drug("D006", "Fabrazyme", "biologic", "approved",
                         ["法布雷病"], ["T005"]),
            "D007": Drug("D007", "泼尼松", "small_molecule", "approved",
                         ["重症肌无力", "自身免疫病"], ["T006"]),
            "D008": Drug("D008", "硫唑嘌呤", "small_molecule", "approved",
                         ["重症肌无力", "器官移植"], ["T007"]),
        }
        self.drugs = drugs_data

        # 靶点节点
        targets_data = {
            "T001": Target("T001", "乙酰胆碱酯酶", "ACHE", "enzyme",
                           ["重症肌无力"]),
            "T002": Target("T002", "补体C5", "C5", "protein",
                           ["重症肌无力", "PNH"]),
            "T003": Target("T003", "β-葡萄糖脑苷脂酶", "GBA1", "enzyme",
                           ["戈谢病"]),
            "T004": Target("T004", "SMN2剪接", "SMN2", "protein",
                           ["脊髓性肌萎缩症"]),
            "T005": Target("T005", "α-半乳糖苷酶A", "GLA", "enzyme",
                           ["法布雷病"]),
            "T006": Target("T006", "糖皮质激素受体", "NR3C1", "receptor",
                           ["炎症性疾病"]),
            "T007": Target("T007", "IMPDH", "IMPDH1", "enzyme",
                           ["免疫抑制"]),
        }
        self.targets = targets_data

        # 边
        self.edges = [
            DrugTargetEdge("D001", "T001", "inhibitor", 50.0, "experimental"),
            DrugTargetEdge("D002", "T002", "inhibitor", 0.5, "clinical"),
            DrugTargetEdge("D003", "T003", "modulator", 10.0, "experimental"),
            DrugTargetEdge("D004", "T004", "modulator", 100.0, "clinical"),
            DrugTargetEdge("D005", "T004", "modulator", 50.0, "clinical"),
            DrugTargetEdge("D006", "T005", "modulator", 20.0, "experimental"),
            DrugTargetEdge("D007", "T006", "agonist", 5.0, "experimental"),
            DrugTargetEdge("D008", "T007", "inhibitor", 100.0, "experimental"),
        ]

    def find_drugs_for_target(self, target_id: str) -> List[Dict]:
        """查找靶点相关药物"""
        results = []
        for edge in self.edges:
            if edge.target_id == target_id:
                drug = self.drugs.get(edge.drug_id)
                if drug:
                    results.append({
                        "drug_id": drug.drug_id,
                        "name": drug.name,
                        "type": drug.drug_type,
                        "status": drug.approval_status,
                        "interaction": edge.interaction_type,
                        "potency": edge.potency,
                    })
        return results

    def find_targets_for_drug(self, drug_id: str) -> List[Dict]:
        """查找药物相关靶点"""
        results = []
        for edge in self.edges:
            if edge.drug_id == drug_id:
                target = self.targets.get(edge.target_id)
                if target:
                    results.append({
                        "target_id": target.target_id,
                        "name": target.name,
                        "gene": target.gene,
                        "type": target.target_type,
                        "interaction": edge.interaction_type,
                        "potency": edge.potency,
                    })
        return results

    def find_drug_repurposing_candidates(self, disease: str) -> List[Dict]:
        """药物重定位：查找可重定位的药物"""
        candidates = []
        
        # 找到治疗该疾病的药物
        approved_drugs = set()
        for drug in self.drugs.values():
            if disease in drug.indications:
                approved_drugs.add(drug.drug_id)
        
        # 找到这些药物的靶点
        target_drug_map = {}
        for edge in self.edges:
            if edge.drug_id in approved_drugs:
                if edge.target_id not in target_drug_map:
                    target_drug_map[edge.target_id] = []
                target_drug_map[edge.target_id].append(edge)
        
        # 查找靶向相同靶点的其他药物
        for target_id, edges in target_drug_map.items():
            for edge in self.edges:
                if edge.target_id == target_id and edge.drug_id not in approved_drugs:
                    drug = self.drugs.get(edge.drug_id)
                    target = self.targets.get(target_id)
                    if drug and target:
                        candidates.append({
                            "drug_id": drug.drug_id,
                            "drug_name": drug.name,
                            "target": target.name,
                            "target_gene": target.gene,
                            "reason": f"共同靶点 {target.name}",
                            "confidence": "medium",
                        })
        
        return candidates

    def analyze_network(self) -> Dict:
        """网络分析"""
        return {
            "nodes": {
                "drugs": len(self.drugs),
                "targets": len(self.targets),
                "total": len(self.drugs) + len(self.targets),
            },
            "edges": len(self.edges),
            "avg_targets_per_drug": len(self.edges) / len(self.drugs) if self.drugs else 0,
            "drug_types": {
                "small_molecule": sum(1 for d in self.drugs.values() 
                                     if d.drug_type == "small_molecule"),
                "biologic": sum(1 for d in self.drugs.values() 
                               if d.drug_type == "biologic"),
                "gene_therapy": sum(1 for d in self.drugs.values() 
                                   if d.drug_type == "gene_therapy"),
            },
        }

    def export_network_json(self) -> Dict:
        """导出网络JSON"""
        return {
            "nodes": {
                "drugs": [
                    {"id": d.drug_id, "name": d.name, "type": d.drug_type}
                    for d in self.drugs.values()
                ],
                "targets": [
                    {"id": t.target_id, "name": t.name, "gene": t.gene}
                    for t in self.targets.values()
                ],
            },
            "edges": [
                {
                    "source": e.drug_id,
                    "target": e.target_id,
                    "type": e.interaction_type,
                    "potency": e.potency,
                }
                for e in self.edges
            ],
        }


# ========== 测试 ==========
if __name__ == "__main__":
    network = DrugTargetNetwork()
    
    print("=" * 60)
    print("💊 药物-靶点网络测试")
    print("=" * 60)
    
    # 网络分析
    analysis = network.analyze_network()
    print(f"\n📊 网络统计:")
    print(f"   药物: {analysis['nodes']['drugs']}")
    print(f"   靶点: {analysis['nodes']['targets']}")
    print(f"   边: {analysis['edges']}")
    print(f"   平均靶点/药物: {analysis['avg_targets_per_drug']:.1f}")
    
    # 查找靶点相关药物
    drugs = network.find_drugs_for_target("T001")
    print(f"\n🔍 乙酰胆碱酯酶相关药物:")
    for d in drugs:
        print(f"   {d['name']}: {d['interaction']} ({d['potency']} nM)")
    
    # 药物重定位
    candidates = network.find_drug_repurposing_candidates("重症肌无力")
    print(f"\n🎯 药物重定位候选:")
    for c in candidates:
        print(f"   {c['drug_name']} → {c['target']} ({c['reason']})")
