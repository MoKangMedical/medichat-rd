"""
MediChat-RD — 知识图谱可视化模块
构建罕见病知识图谱：疾病-基因-药物-表型-文献关联
"""
import json
from typing import List, Dict, Optional
from dataclasses import dataclass, field


@dataclass
class GraphNode:
    """图谱节点"""
    id: str
    label: str
    node_type: str  # disease / gene / drug / phenotype / literature
    properties: Dict = field(default_factory=dict)


@dataclass
class GraphEdge:
    """图谱边"""
    source: str
    target: str
    relation: str  # causes / treats / has_phenotype / associated_with
    weight: float = 1.0
    properties: Dict = field(default_factory=dict)


class KnowledgeGraph:
    """罕见病知识图谱"""

    def __init__(self):
        self.nodes: Dict[str, GraphNode] = {}
        self.edges: List[GraphEdge] = []
        self._build_graph()

    def _build_graph(self):
        """构建知识图谱"""
        # 核心疾病
        diseases = {
            "MG": ("重症肌无力", "OMIM:254200"),
            "GD": ("戈谢病", "OMIM:230800"),
            "SMA": ("脊髓性肌萎缩症", "OMIM:253300"),
            "DMD": ("Duchenne肌营养不良", "OMIM:310200"),
            "FD": ("法布雷病", "OMIM:301500"),
            "HA": ("血友病A", "OMIM:306700"),
            "OI": ("成骨不全症", "OMIM:166200"),
            "PKU": ("苯丙酮尿症", "OMIM:261600"),
        }
        
        for did, (name, omim) in diseases.items():
            self.nodes[did] = GraphNode(
                id=did, label=name, node_type="disease",
                properties={"omim": omim}
            )
        
        # 基因
        genes = {
            "CHRNA1": ("CHRNA1", "乙酰胆碱受体α1亚基"),
            "GBA1": ("GBA1", "β-葡萄糖脑苷脂酶"),
            "SMN1": ("SMN1", "运动神经元存活基因1"),
            "DMD": ("DMD", "抗肌萎缩蛋白基因"),
            "GLA": ("GLA", "α-半乳糖苷酶A"),
            "F8": ("F8", "凝血因子VIII"),
            "COL1A1": ("COL1A1", "I型胶原α1链"),
            "PAH": ("PAH", "苯丙氨酸羟化酶"),
        }
        
        for gid, (name, desc) in genes.items():
            self.nodes[f"gene_{gid}"] = GraphNode(
                id=f"gene_{gid}", label=name, node_type="gene",
                properties={"description": desc}
            )
        
        # 药物
        drugs = {
            "pyridostigmine": ("溴吡斯的明", "胆碱酯酶抑制剂"),
            "cerezyme": ("伊米苷酶", "酶替代疗法"),
            "spinraza": ("Spinraza", "反义寡核苷酸"),
            "zolgensma": ("Zolgensma", "基因疗法"),
            "fabrazyme": ("Fabrazyme", "酶替代疗法"),
            "advate": ("Advate", "重组凝血因子VIII"),
            "bisphosphonate": ("双膦酸盐", "骨保护剂"),
        }
        
        for did, (name, desc) in drugs.items():
            self.nodes[f"drug_{did}"] = GraphNode(
                id=f"drug_{did}", label=name, node_type="drug",
                properties={"mechanism": desc}
            )
        
        # 表型
        phenotypes = {
            "ptosis": ("眼睑下垂", "HP:0000508"),
            "dysphagia": ("吞咽困难", "HP:0002015"),
            "weakness": ("肌无力", "HP:0001252"),
            "hepatosplenomegaly": ("肝脾肿大", "HP:0001433"),
            "anemia": ("贫血", "HP:0001889"),
            "fractures": ("反复骨折", "HP:0002757"),
            "pain": ("肢端疼痛", "HP:0003338"),
            "bleeding": ("出血倾向", "HP:0000492"),
        }
        
        for pid, (name, hpo) in phenotypes.items():
            self.nodes[f"pheno_{pid}"] = GraphNode(
                id=f"pheno_{pid}", label=name, node_type="phenotype",
                properties={"hpo": hpo}
            )
        
        # 疾病-基因关联
        disease_gene = [
            ("MG", "gene_CHRNA1", "caused_by"),
            ("GD", "gene_GBA1", "caused_by"),
            ("SMA", "gene_SMN1", "caused_by"),
            ("DMD", "gene_DMD", "caused_by"),
            ("FD", "gene_GLA", "caused_by"),
            ("HA", "gene_F8", "caused_by"),
            ("OI", "gene_COL1A1", "caused_by"),
            ("PKU", "gene_PAH", "caused_by"),
        ]
        
        for src, tgt, rel in disease_gene:
            self.edges.append(GraphEdge(source=src, target=tgt, relation=rel))
        
        # 疾病-药物关联
        disease_drug = [
            ("MG", "drug_pyridostigmine", "treated_by"),
            ("GD", "drug_cerezyme", "treated_by"),
            ("SMA", "drug_spinraza", "treated_by"),
            ("SMA", "drug_zolgensma", "treated_by"),
            ("FD", "drug_fabrazyme", "treated_by"),
            ("HA", "drug_advate", "treated_by"),
            ("OI", "drug_bisphosphonate", "treated_by"),
        ]
        
        for src, tgt, rel in disease_drug:
            self.edges.append(GraphEdge(source=src, target=tgt, relation=rel))
        
        # 疾病-表型关联
        disease_phenotype = [
            ("MG", "pheno_ptosis", "has_phenotype"),
            ("MG", "pheno_dysphagia", "has_phenotype"),
            ("MG", "pheno_weakness", "has_phenotype"),
            ("GD", "pheno_hepatosplenomegaly", "has_phenotype"),
            ("GD", "pheno_anemia", "has_phenotype"),
            ("OI", "pheno_fractures", "has_phenotype"),
            ("FD", "pheno_pain", "has_phenotype"),
            ("HA", "pheno_bleeding", "has_phenotype"),
        ]
        
        for src, tgt, rel in disease_phenotype:
            self.edges.append(GraphEdge(source=src, target=tgt, relation=rel))

    def query_related(self, node_id: str, relation: str = None) -> Dict:
        """查询关联节点"""
        related = {"diseases": [], "genes": [], "drugs": [], "phenotypes": []}
        
        for edge in self.edges:
            if edge.source == node_id and (relation is None or edge.relation == relation):
                target = self.nodes.get(edge.target)
                if target:
                    related[f"{target.node_type}s"].append({
                        "id": target.id,
                        "label": target.label,
                        "relation": edge.relation,
                    })
            elif edge.target == node_id and (relation is None or edge.relation == relation):
                source = self.nodes.get(edge.source)
                if source:
                    related[f"{source.node_type}s"].append({
                        "id": source.id,
                        "label": source.label,
                        "relation": edge.relation,
                    })
        
        return related

    def search(self, query: str) -> List[Dict]:
        """搜索图谱"""
        results = []
        for nid, node in self.nodes.items():
            if query.lower() in node.label.lower():
                results.append({
                    "id": nid,
                    "label": node.label,
                    "type": node.node_type,
                    "properties": node.properties,
                })
        return results

    def get_graph_stats(self) -> Dict:
        """获取图谱统计"""
        node_types = {}
        for node in self.nodes.values():
            node_types[node.node_type] = node_types.get(node.node_type, 0) + 1
        
        edge_types = {}
        for edge in self.edges:
            edge_types[edge.relation] = edge_types.get(edge.relation, 0) + 1
        
        return {
            "total_nodes": len(self.nodes),
            "total_edges": len(self.edges),
            "node_types": node_types,
            "edge_types": edge_types,
        }

    def export_graph_json(self) -> Dict:
        """导出图谱JSON格式"""
        return {
            "nodes": [
                {
                    "id": n.id,
                    "label": n.label,
                    "type": n.node_type,
                    "properties": n.properties,
                }
                for n in self.nodes.values()
            ],
            "edges": [
                {
                    "source": e.source,
                    "target": e.target,
                    "relation": e.relation,
                    "weight": e.weight,
                }
                for e in self.edges
            ],
        }


# ========== 测试 ==========
if __name__ == "__main__":
    kg = KnowledgeGraph()
    
    print("=" * 60)
    print("🕸️ 罕见病知识图谱测试")
    print("=" * 60)
    
    stats = kg.get_graph_stats()
    print(f"\n📊 图谱统计:")
    print(f"   节点: {stats['total_nodes']}")
    print(f"   边: {stats['total_edges']}")
    print(f"   节点类型: {stats['node_types']}")
    print(f"   关系类型: {stats['edge_types']}")
    
    # 查询MG相关
    related = kg.query_related("MG")
    print(f"\n🔍 重症肌无力关联:")
    print(f"   基因: {[g['label'] for g in related['genes']]}")
    print(f"   药物: {[d['label'] for d in related['drugs']]}")
    print(f"   表型: {[p['label'] for p in related['phenotypes']]}")
    
    # 搜索
    results = kg.search("肌无力")
    print(f"\n🔍 搜索'肌无力': {len(results)}个结果")
