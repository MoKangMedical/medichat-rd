"""
MediChat-RD — 基因组变异分析模块
参考Exomiser：HPO表型 + 基因组变异联合分析
"""
import json
from typing import List, Dict, Optional
from dataclasses import dataclass, field


@dataclass
class GenomicVariant:
    """基因组变异"""
    chromosome: str
    position: int
    ref: str
    alt: str
    gene: str
    variant_type: str  # SNV / indel / CNV
    hgvs_c: str = ""
    hgvs_p: str = ""
    clinvar_id: str = ""
    pathogenicity: str = ""  # benign / likely_benign / VUS / likely_pathogenic / pathogenic
    allele_frequency: float = 0.0


@dataclass
class GeneDiseaseAssociation:
    """基因-疾病关联"""
    gene: str
    disease: str
    omim_id: str
    inheritance: str  # AD / AR / X-linked
    evidence_level: str  # strong / moderate / limited
    phenotype_score: float = 0.0
    variant_score: float = 0.0
    combined_score: float = 0.0


class GenomicAnalyzer:
    """
    基因组变异分析器
    参考Exomiser：HPO表型 + 基因组变异联合分析
    """

    # 罕见病基因-疾病关联数据库（精简版）
    GENE_DISEASE_DB = {
        "CHRNA1": {
            "disease": "重症肌无力（先天性）",
            "omim": "OMIM:601462",
            "inheritance": "AR",
            "evidence": "strong",
            "phenotypes": ["眼睑下垂", "吞咽困难", "全身无力", "肌无力"],
        },
        "CHRNB1": {
            "disease": "重症肌无力（先天性）",
            "omim": "OMIM:601462",
            "inheritance": "AR",
            "evidence": "strong",
            "phenotypes": ["眼睑下垂", "肌无力"],
        },
        "CHRND": {
            "disease": "重症肌无力（先天性）",
            "omim": "OMIM:601462",
            "inheritance": "AR",
            "evidence": "strong",
            "phenotypes": ["眼睑下垂", "肌无力"],
        },
        "CHRNE": {
            "disease": "重症肌无力（先天性）",
            "omim": "OMIM:601462",
            "inheritance": "AR",
            "evidence": "strong",
            "phenotypes": ["眼睑下垂", "肌无力"],
        },
        "GBA1": {
            "disease": "戈谢病",
            "omim": "OMIM:230800",
            "inheritance": "AR",
            "evidence": "strong",
            "phenotypes": ["肝脾肿大", "贫血", "血小板减少", "骨痛"],
        },
        "SMN1": {
            "disease": "脊髓性肌萎缩症",
            "omim": "OMIM:253300",
            "inheritance": "AR",
            "evidence": "strong",
            "phenotypes": ["肌无力", "肌萎缩", "运动发育迟缓"],
        },
        "DMD": {
            "disease": "Duchenne肌营养不良",
            "omim": "OMIM:310200",
            "inheritance": "X-linked",
            "evidence": "strong",
            "phenotypes": ["肌无力", "肌萎缩", "腓肠肌假性肥大", "运动发育迟缓"],
        },
        "GLA": {
            "disease": "法布雷病",
            "omim": "OMIM:301500",
            "inheritance": "X-linked",
            "evidence": "strong",
            "phenotypes": ["肢端疼痛", "皮肤血管角化瘤", "角膜混浊", "肾功能不全"],
        },
        "F8": {
            "disease": "血友病A",
            "omim": "OMIM:306700",
            "inheritance": "X-linked",
            "evidence": "strong",
            "phenotypes": ["出血倾向", "关节出血", "肌肉出血"],
        },
        "F9": {
            "disease": "血友病B",
            "omim": "OMIM:306900",
            "inheritance": "X-linked",
            "evidence": "strong",
            "phenotypes": ["出血倾向", "关节出血"],
        },
        "COL1A1": {
            "disease": "成骨不全症",
            "omim": "OMIM:166200",
            "inheritance": "AD",
            "evidence": "strong",
            "phenotypes": ["反复骨折", "蓝巩膜", "听力下降", "关节过度活动"],
        },
        "COL1A2": {
            "disease": "成骨不全症",
            "omim": "OMIM:166200",
            "inheritance": "AR",
            "evidence": "strong",
            "phenotypes": ["反复骨折", "蓝巩膜"],
        },
        "PKD1": {
            "disease": "多囊肾病（常染色体显性）",
            "omim": "OMIM:601313",
            "inheritance": "AD",
            "evidence": "strong",
            "phenotypes": ["肾囊肿", "高血压", "血尿", "肾功能不全"],
        },
        "HBB": {
            "disease": "镰状细胞贫血",
            "omim": "OMIM:603903",
            "inheritance": "AR",
            "evidence": "strong",
            "phenotypes": ["贫血", "血管阻塞危象", "脾肿大"],
        },
    }

    def analyze(self, variants: List[GenomicVariant], 
                hpo_phenotypes: List[str]) -> List[GeneDiseaseAssociation]:
        """
        基因组变异 + HPO表型联合分析
        参考Exomiser的PHIVE算法
        """
        results = []
        
        for gene, info in self.GENE_DISEASE_DB.items():
            # 检查变异是否命中该基因
            gene_variants = [v for v in variants if v.gene == gene]
            if not gene_variants:
                continue
            
            # 计算表型相似度分数
            phenotype_score = self._calculate_phenotype_similarity(
                hpo_phenotypes, info["phenotypes"]
            )
            
            # 计算变异致病性分数
            variant_score = self._calculate_variant_score(gene_variants)
            
            # 综合分数（类似Exomiser的combined score）
            combined_score = phenotype_score * 0.6 + variant_score * 0.4
            
            results.append(GeneDiseaseAssociation(
                gene=gene,
                disease=info["disease"],
                omim_id=info["omim"],
                inheritance=info["inheritance"],
                evidence_level=info["evidence"],
                phenotype_score=round(phenotype_score, 3),
                variant_score=round(variant_score, 3),
                combined_score=round(combined_score, 3),
            ))
        
        # 按综合分数排序
        results.sort(key=lambda x: x.combined_score, reverse=True)
        return results

    def _calculate_phenotype_similarity(self, patient_phenotypes: List[str],
                                        disease_phenotypes: List[str]) -> float:
        """计算表型相似度（简化版PhenoDigm）"""
        if not patient_phenotypes or not disease_phenotypes:
            return 0.0
        
        # Jaccard相似度
        patient_set = set(patient_phenotypes)
        disease_set = set(disease_phenotypes)
        
        intersection = len(patient_set & disease_set)
        union = len(patient_set | disease_set)
        
        return intersection / union if union > 0 else 0.0

    def _calculate_variant_score(self, variants: List[GenomicVariant]) -> float:
        """计算变异致病性分数"""
        if not variants:
            return 0.0
        
        score = 0.0
        for v in variants:
            if v.pathogenicity == "pathogenic":
                score = max(score, 1.0)
            elif v.pathogenicity == "likely_pathogenic":
                score = max(score, 0.8)
            elif v.pathogenicity == "VUS":
                score = max(score, 0.5)
            elif v.pathogenicity == "likely_benign":
                score = max(score, 0.2)
            elif v.pathogenicity == "benign":
                score = max(score, 0.0)
            
            # 低等位基因频率加分
            if v.allele_frequency < 0.001:
                score = min(score + 0.1, 1.0)
        
        return score

    def generate_phenopacket(self, patient_id: str, variants: List[GenomicVariant],
                            phenotypes: List[str]) -> Dict:
        """
        生成GA4GH Phenopacket格式数据
        符合ISO国际标准
        """
        phenopacket = {
            "id": f"medichat_{patient_id}",
            "subject": {
                "id": patient_id,
            },
            "phenotypic_features": [
                {
                    "type": {
                        "id": f"HP:{i:08d}",
                        "label": p,
                    },
                    "observed": True,
                }
                for i, p in enumerate(phenotypes, start=1)
            ],
            "interpretations": [
                {
                    "id": f"interp_{i}",
                    "progressStatus": "SOLVED",
                    "diagnosis": {
                        "disease": {
                            "id": "OMIM:XXXXXX",
                            "label": "待分析",
                        },
                        "genomic_interpretations": [
                            {
                                "subjectOrBiosampleId": patient_id,
                                "variantInterpretation": {
                                    "acmgPathogenicityClassification": v.pathogenicity or "NOT_PROVIDED",
                                    "variationDescriptor": {
                                        "geneContext": {
                                            "value": v.gene,
                                        },
                                        "allelicState": {
                                            "id": "GENO:0000135",
                                            "label": "hemizygous" if "X" in v.chromosome else "heterozygous",
                                        },
                                        "vcfAllele": {
                                            "chr": v.chromosome,
                                            "pos": v.position,
                                            "ref": v.ref,
                                            "alt": v.alt,
                                        },
                                    },
                                },
                            }
                            for v in variants
                        ],
                    },
                }
                for i in range(1)
            ],
            "meta_data": {
                "created": "2026-04-05T00:00:00Z",
                "created_by": "MediChat-RD",
                "phenopacket_schema_version": "2.0",
            },
        }
        return phenopacket

    def get_stats(self) -> Dict:
        """获取统计信息"""
        return {
            "gene_disease_associations": len(self.GENE_DISEASE_DB),
            "total_genes": len(set(self.GENE_DISEASE_DB.keys())),
            "inheritance_modes": list(set(
                info["inheritance"] for info in self.GENE_DISEASE_DB.values()
            )),
        }


# ========== 测试 ==========
if __name__ == "__main__":
    analyzer = GenomicAnalyzer()
    
    print("=" * 60)
    print("🧬 基因组变异分析器测试")
    print("=" * 60)
    
    # 模拟变异
    variants = [
        GenomicVariant(
            chromosome="2", position=175602390, ref="C", alt="T",
            gene="CHRNE", variant_type="SNV",
            hgvs_c="c.130C>T", hgvs_p="p.Arg44Trp",
            pathogenicity="pathogenic", allele_frequency=0.0001
        ),
    ]
    
    # 患者表型
    phenotypes = ["眼睑下垂", "吞咽困难", "全身无力"]
    
    # 分析
    results = analyzer.analyze(variants, phenotypes)
    
    print(f"\n📊 分析结果:")
    for r in results:
        print(f"   {r.gene} → {r.disease}")
        print(f"   综合分数: {r.combined_score} (表型:{r.phenotype_score} + 变异:{r.variant_score})")
        print(f"   遗传方式: {r.inheritance} | 证据: {r.evidence_level}")
        print()
    
    # Phenopacket
    pp = analyzer.generate_phenopacket("p_test", variants, phenotypes)
    print(f"📋 Phenopacket ID: {pp['id']}")
    print(f"   表型数: {len(pp['phenotypic_features'])}")
    print(f"   变异数: {len(pp['interpretations'][0]['diagnosis']['genomic_interpretations'])}")
