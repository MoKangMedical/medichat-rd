"""
MediChat-RD — 患者匹配引擎
参考PhenoTips Patient Network：基于HPO表型的患者相似度匹配
"""
import json
import math
from typing import List, Dict, Tuple
from dataclasses import dataclass


@dataclass
class PatientProfile:
    """患者档案"""
    patient_id: str
    disease: str
    hpo_phenotypes: List[str]
    age: int = 0
    gender: str = ""
    location: str = ""


class PatientMatcher:
    """
    患者匹配引擎
    基于HPO表型相似度 + 地理位置 + 疾病类型的患者匹配
    """

    def __init__(self):
        self.patients: List[PatientProfile] = []

    def add_patient(self, patient: PatientProfile):
        """添加患者"""
        self.patients.append(patient)

    def calculate_similarity(self, p1: PatientProfile, p2: PatientProfile) -> float:
        """
        计算两个患者的相似度
        算法：加权Jaccard + 疾病匹配 + 地理位置
        """
        # 表型相似度（Jaccard）
        set1 = set(p1.hpo_phenotypes)
        set2 = set(p2.hpo_phenotypes)
        
        if not set1 or not set2:
            phenotype_sim = 0.0
        else:
            intersection = len(set1 & set2)
            union = len(set1 | set2)
            phenotype_sim = intersection / union if union > 0 else 0.0
        
        # 疾病匹配
        disease_sim = 1.0 if p1.disease == p2.disease else 0.0
        
        # 年龄相似度
        if p1.age and p2.age:
            age_diff = abs(p1.age - p2.age)
            age_sim = max(0, 1 - age_diff / 50)  # 50岁差距为0
        else:
            age_sim = 0.5  # 未知年龄给中性分
        
        # 性别匹配
        gender_sim = 1.0 if p1.gender == p2.gender else 0.5
        
        # 综合相似度
        total_sim = (
            phenotype_sim * 0.5 +
            disease_sim * 0.3 +
            age_sim * 0.1 +
            gender_sim * 0.1
        )
        
        return round(total_sim, 3)

    def find_matches(self, target: PatientProfile, top_n: int = 5, 
                    min_similarity: float = 0.3) -> List[Dict]:
        """查找匹配患者"""
        matches = []
        
        for patient in self.patients:
            if patient.patient_id == target.patient_id:
                continue
            
            sim = self.calculate_similarity(target, patient)
            if sim >= min_similarity:
                matches.append({
                    "patient_id": patient.patient_id,
                    "disease": patient.disease,
                    "phenotypes": patient.hpo_phenotypes,
                    "similarity": sim,
                    "location": patient.location,
                })
        
        # 按相似度排序
        matches.sort(key=lambda x: x["similarity"], reverse=True)
        return matches[:top_n]

    def find_support_group(self, disease: str, phenotype: str = "") -> List[Dict]:
        """查找互助组"""
        matches = []
        
        for patient in self.patients:
            if patient.disease == disease:
                if not phenotype or phenotype in patient.hpo_phenotypes:
                    matches.append({
                        "patient_id": patient.patient_id,
                        "disease": patient.disease,
                        "phenotypes": patient.hpo_phenotypes,
                        "location": patient.location,
                    })
        
        return matches

    def get_stats(self) -> Dict:
        """获取统计"""
        disease_count = {}
        for p in self.patients:
            disease_count[p.disease] = disease_count.get(p.disease, 0) + 1
        
        return {
            "total_patients": len(self.patients),
            "disease_distribution": disease_count,
        }


# ========== 测试 ==========
if __name__ == "__main__":
    matcher = PatientMatcher()
    
    print("=" * 60)
    print("🤝 患者匹配引擎测试")
    print("=" * 60)
    
    # 添加患者
    patients = [
        PatientProfile("p1", "重症肌无力", ["眼睑下垂", "吞咽困难", "全身无力"], 35, "female", "北京"),
        PatientProfile("p2", "重症肌无力", ["眼睑下垂", "下午加重"], 40, "female", "上海"),
        PatientProfile("p3", "戈谢病", ["肝脾肿大", "贫血"], 10, "male", "广州"),
        PatientProfile("p4", "重症肌无力", ["吞咽困难", "全身无力", "呼吸困难"], 50, "male", "北京"),
    ]
    
    for p in patients:
        matcher.add_patient(p)
    
    # 匹配
    target = PatientProfile("p0", "重症肌无力", ["眼睑下垂", "吞咽困难"], 30, "female", "")
    matches = matcher.find_matches(target)
    
    print(f"\n🔍 为患者匹配相似患者:")
    for m in matches:
        print(f"   {m['patient_id']}: {m['disease']} (相似度: {m['similarity']})")
        print(f"     表型: {', '.join(m['phenotypes'])}")
        print(f"     位置: {m['location']}")
    
    # 互助组
    group = matcher.find_support_group("重症肌无力")
    print(f"\n👥 重症肌无力互助组: {len(group)}人")
    
    stats = matcher.get_stats()
    print(f"\n📊 统计: {stats}")
