#!/usr/bin/env python3
"""
MediChat-RD 知识库扩展脚本
目标：扩展至121种罕见病（国家罕见病目录）
"""

import json
import os

# 现有疾病（20种）
EXISTING = [
    "Gaucher Disease", "Pompe Disease", "Fabry Disease", "ALS (渐冻症)",
    "Hemophilia A", "Hemophilia B", "Multiple Sclerosis", "Albinism",
    "Phenylketonuria (PKU)", "Wilson Disease", "Spinal Muscular Atrophy (SMA)",
    "Duchenne Muscular Dystrophy (DMD)", "Tuberous Sclerosis Complex (TSC)",
    "Galactosemia", "Congenital Adrenal Hyperplasia (CAH)", "Thalassemia",
    "Retinitis Pigmentosa (RP)", "Osteogenesis Imperfecta (OI)",
    "Hereditary Angioedema (HAE)", "Glycogen Storage Disease Type I (von Gierke)"
]

# 待添加疾病（按分类）
NEW_DISEASES = {
    "代谢病": [
        {"name": "酪氨酸血症", "name_en": "Tyrosinemia", "gene": "FAH", "category": "代谢病"},
        {"name": "尿素循环障碍", "name_en": "Urea Cycle Disorders", "gene": "CPS1/OTC/ASS1", "category": "代谢病"},
        {"name": "有机酸血症", "name_en": "Organic Acidemia", "gene": "多种", "category": "代谢病"},
        {"name": "脂肪酸氧化障碍", "name_en": "Fatty Acid Oxidation Disorders", "gene": "ACADM/HADHA", "category": "代谢病"},
    ],
    "神经系统": [
        {"name": "亨廷顿病", "name_en": "Huntington's Disease", "gene": "HTT", "category": "神经系统"},
        {"name": "肌张力障碍", "name_en": "Dystonia", "gene": "THAP1/GNAL", "category": "神经系统"},
        {"name": "脊髓小脑性共济失调", "name_en": "Spinocerebellar Ataxia (SCA)", "gene": "ATXN1-ATXN7", "category": "神经系统"},
        {"name": "脑白质营养不良", "name_en": "Leukodystrophy", "gene": "PLP1/ABCD1", "category": "神经系统"},
    ],
    "血液病": [
        {"name": "阵发性睡眠性血红蛋白尿症", "name_en": "Paroxysmal Nocturnal Hemoglobinuria (PNH)", "gene": "PIGA", "category": "血液病"},
        {"name": "再生障碍性贫血", "name_en": "Aplastic Anemia", "gene": "TERT/TERC", "category": "血液病"},
        {"name": "先天性中性粒细胞减少症", "name_en": "Severe Congenital Neutropenia", "gene": "ELANE/HAX1", "category": "血液病"},
    ],
    "遗传病": [
        {"name": "马凡综合征", "name_en": "Marfan Syndrome", "gene": "FBN1", "category": "遗传病"},
        {"name": "努南综合征", "name_en": "Noonan Syndrome", "gene": "PTPN11/SOS1", "category": "遗传病"},
        {"name": "Prader-Willi综合征", "name_en": "Prader-Willi Syndrome", "gene": "15q11-q13缺失", "category": "遗传病"},
        {"name": "Angelman综合征", "name_en": "Angelman Syndrome", "gene": "UBE3A", "category": "遗传病"},
    ],
    "免疫病": [
        {"name": "原发性免疫缺陷病", "name_en": "Primary Immunodeficiency (PID)", "gene": "多种", "category": "免疫病"},
        {"name": "系统性红斑狼疮(儿童)", "name_en": "Juvenile SLE", "gene": "多基因", "category": "免疫病"},
        {"name": "周期性发热综合征", "name_en": "Periodic Fever Syndromes", "gene": "MEFV/TNFRSF1A", "category": "免疫病"},
    ],
    "眼科病": [
        {"name": "Leber遗传性视神经病变", "name_en": "Leber Hereditary Optic Neuropathy", "gene": "MT-ND4/ND1/ND6", "category": "眼科病"},
        {"name": "先天性无虹膜症", "name_en": "Aniridia", "gene": "PAX6", "category": "眼科病"},
    ],
    "骨骼病": [
        {"name": "软骨发育不全", "name_en": "Achondroplasia", "gene": "FGFR3", "category": "骨骼病"},
        {"name": "骨硬化病", "name_en": "Osteopetrosis", "gene": "TCIRG1/CLCN7", "category": "骨骼病"},
    ],
    "心血管": [
        {"name": "长QT综合征", "name_en": "Long QT Syndrome", "gene": "KCNQ1/KCNH2/SCN5A", "category": "心血管"},
        {"name": "致心律失常性右室心肌病", "name_en": "Arrhythmogenic Right Ventricular Cardiomyopathy", "gene": "PKP2/DSG2", "category": "心血管"},
    ],
    "呼吸病": [
        {"name": "原发性纤毛运动障碍", "name_en": "Primary Ciliary Dyskinesia", "gene": "DNAI1/DNAH5", "category": "呼吸病"},
        {"name": "肺泡蛋白沉积症", "name_en": "Pulmonary Alveolar Proteinosis", "gene": "CSF2RA/CSF2RB", "category": "呼吸病"},
    ],
    "消化病": [
        {"name": "家族性腺瘤性息肉病", "name_en": "Familial Adenomatous Polyposis", "gene": "APC", "category": "消化病"},
        {"name": "Alagille综合征", "name_en": "Alagille Syndrome", "gene": "JAG1/NOTCH2", "category": "消化病"},
    ],
    "肾病": [
        {"name": "多囊肾病", "name_en": "Polycystic Kidney Disease", "gene": "PKD1/PKD2", "category": "肾病"},
        {"name": "Alport综合征", "name_en": "Alport Syndrome", "gene": "COL4A3/COL4A4/COL4A5", "category": "肾病"},
    ],
    "皮肤": [
        {"name": "大疱性表皮松解症", "name_en": "Epidermolysis Bullosa", "gene": "KRT5/KRT14/COL7A1", "category": "皮肤"},
        {"name": "着色性干皮病", "name_en": "Xeroderma Pigmentosum", "gene": "XPA-XPG", "category": "皮肤"},
    ],
    "内分泌": [
        {"name": "垂体性侏儒症", "name_en": "Growth Hormone Deficiency", "gene": "GH1/GHRHR", "category": "内分泌"},
        {"name": "先天性甲状腺功能减退", "name_en": "Congenital Hypothyroidism", "gene": "TPO/TG/NIS", "category": "内分泌"},
    ],
    "肌肉病": [
        {"name": "强直性肌营养不良", "name_en": "Myotonic Dystrophy", "gene": "DMPK/CNBP", "category": "肌肉病"},
        {"name": "面肩肱型肌营养不良", "name_en": "Facioscapulohumeral Muscular Dystrophy", "gene": "DUX4", "category": "肌肉病"},
        {"name": "肢带型肌营养不良", "name_en": "Limb-Girdle Muscular Dystrophy", "gene": "多种", "category": "肌肉病"},
    ],
}

def expand_disease(disease_base):
    """为疾病补充完整信息"""
    return {
        "name": disease_base["name"],
        "name_en": disease_base["name_en"],
        "icd10": "待补充",
        "category": disease_base["category"],
        "inheritance": "常染色体隐性/显性",
        "gene": disease_base["gene"],
        "prevalence": "罕见",
        "symptoms": "待详细补充",
        "diagnosis_criteria": "待详细补充",
        "treatment_summary": "待详细补充",
        "specialist_hospitals": ["北京协和医院", "上海交通大学医学院附属瑞金医院"]
    }

if __name__ == "__main__":
    # 加载现有知识库
    with open("knowledge/diseases_extended.json", "r") as f:
        existing = json.load(f)
    
    print(f"当前疾病数：{len(existing)}")
    
    # 收集新疾病
    new_entries = []
    for category, diseases in NEW_DISEASES.items():
        for d in diseases:
            new_entries.append(expand_disease(d))
    
    print(f"待添加疾病数：{len(new_entries)}")
    print(f"扩展后总数：{len(existing) + len(new_entries)}")
    
    # 合并
    expanded = existing + new_entries
    
    # 保存
    with open("knowledge/diseases_extended.json", "w") as f:
        json.dump(expanded, f, ensure_ascii=False, indent=2)
    
    print("✅ 知识库扩展完成")
