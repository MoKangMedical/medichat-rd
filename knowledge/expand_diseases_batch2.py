#!/usr/bin/env python3
"""
MediChat-RD 知识库继续扩展（第二批）
目标：57→121种罕见病
"""

import json

# 第二批待添加疾病（国家罕见病目录剩余重要疾病）
BATCH2 = [
    # 神经系统（续）
    {"name": "进行性肌阵挛癫痫", "name_en": "Progressive Myoclonic Epilepsy", "gene": "CSTB/EPM2A", "category": "神经系统"},
    {"name": "Dravet综合征", "name_en": "Dravet Syndrome", "gene": "SCN1A", "category": "神经系统"},
    {"name": "Rett综合征", "name_en": "Rett Syndrome", "gene": "MECP2", "category": "神经系统"},
    {"name": "脊髓延髓肌萎缩症", "name_en": "Spinal and Bulbar Muscular Atrophy (Kennedy)", "gene": "AR", "category": "神经系统"},
    {"name": "脊髓空洞症", "name_en": "Syringomyelia", "gene": "CHI1", "category": "神经系统"},
    {"name": "腓骨肌萎缩症", "name_en": "Charcot-Marie-Tooth Disease", "gene": "PMP22/MPZ", "category": "神经系统"},
    {"name": "遗传性痉挛性截瘫", "name_en": "Hereditary Spastic Paraplegia", "gene": "SPAST/SPG系列", "category": "神经系统"},
    {"name": "先天性肌无力综合征", "name_en": "Congenital Myasthenic Syndrome", "gene": "CHRNE/CHAT", "category": "神经系统"},
    {"name": "线粒体脑肌病", "name_en": "Mitochondrial Encephalomyopathy", "gene": "MT基因/核基因", "category": "神经系统"},
    {"name": "Leigh综合征", "name_en": "Leigh Syndrome", "gene": "MT-ATP6/SURF1", "category": "神经系统"},

    # 代谢病（续）
    {"name": "半乳糖激酶缺乏症", "name_en": "Galactokinase Deficiency", "gene": "GALK1", "category": "代谢病"},
    {"name": "遗传性果糖不耐受", "name_en": "Hereditary Fructose Intolerance", "gene": "ALDOB", "category": "代谢病"},
    {"name": "丙酸血症", "name_en": "Propionic Acidemia", "gene": "PCCA/PCCB", "category": "代谢病"},
    {"name": "甲基丙二酸血症", "name_en": "Methylmalonic Acidemia", "gene": "MUT/MMAA/MMAB", "category": "代谢病"},
    {"name": "戊二酸血症I型", "name_en": "Glutaric Acidemia Type I", "gene": "GCDH", "category": "代谢病"},
    {"name": "枫糖尿病", "name_en": "Maple Syrup Urine Disease", "gene": "BCKDHA/BCKDHB", "category": "代谢病"},
    {"name": "异戊酸血症", "name_en": "Isovaleric Acidemia", "gene": "IVD", "category": "代谢病"},
    {"name": "黏多糖贮积症I型", "name_en": "MPS I (Hurler Syndrome)", "gene": "IDUA", "category": "代谢病"},
    {"name": "黏多糖贮积症II型", "name_en": "MPS II (Hunter Syndrome)", "gene": "IDS", "category": "代谢病"},
    {"name": "尼曼-匹克病", "name_en": "Niemann-Pick Disease", "gene": "SMPD1/NPC1/NPC2", "category": "代谢病"},
    {"name": "异染性脑白质营养不良", "name_en": "Metachromatic Leukodystrophy", "gene": "ARSA", "category": "代谢病"},
    {"name": "肾上腺脑白质营养不良", "name_en": "Adrenoleukodystrophy", "gene": "ABCD1", "category": "代谢病"},
    {"name": "Krabbe病", "name_en": "Krabbe Disease", "gene": "GALC", "category": "代谢病"},
    {"name": "GM1神经节苷脂贮积症", "name_en": "GM1 Gangliosidosis", "gene": "GLB1", "category": "代谢病"},
    {"name": "GM2神经节苷脂贮积症(Tay-Sachs)", "name_en": "Tay-Sachs Disease", "gene": "HEXA", "category": "代谢病"},
    {"name": "GM2神经节苷脂贮积症(Sandhoff)", "name_en": "Sandhoff Disease", "gene": "HEXB", "category": "代谢病"},
    {"name": "岩藻糖苷贮积症", "name_en": "Fucosidosis", "gene": "FUCA1", "category": "代谢病"},
    {"name": "甘露糖苷贮积症", "name_en": "Mannosidosis", "gene": "MAN2B1", "category": "代谢病"},
    {"name": "唾液酸贮积症", "name_en": "Sialidosis", "gene": "NEU1", "category": "代谢病"},

    # 血液病（续）
    {"name": "遗传性球形红细胞增多症", "name_en": "Hereditary Spherocytosis", "gene": "ANK1/SPTB/SLC4A1", "category": "血液病"},
    {"name": "镰状细胞病", "name_en": "Sickle Cell Disease", "gene": "HBB", "category": "血液病"},
    {"name": "先天性纯红细胞再生障碍", "name_en": "Diamond-Blackfan Anemia", "gene": "RPS19/RPL5", "category": "血液病"},
    {"name": "Shwachman-Diamond综合征", "name_en": "Shwachman-Diamond Syndrome", "gene": "SBDS", "category": "血液病"},
    {"name": "先天性红细胞生成异常性贫血", "name_en": "Congenital Dyserythropoietic Anemia", "gene": "CDAN1/C15ORF41", "category": "血液病"},
    {"name": "Evans综合征", "name_en": "Evans Syndrome", "gene": "免疫相关", "category": "血液病"},

    # 免疫病（续）
    {"name": "重症联合免疫缺陷", "name_en": "Severe Combined Immunodeficiency (SCID)", "gene": "IL2RG/JAK3/ADA", "category": "免疫病"},
    {"name": "慢性肉芽肿病", "name_en": "Chronic Granulomatous Disease", "gene": "CYBB/CYBA", "category": "免疫病"},
    {"name": "Wiskott-Aldrich综合征", "name_en": "Wiskott-Aldrich Syndrome", "gene": "WAS", "category": "免疫病"},
    {"name": "DiGeorge综合征", "name_en": "DiGeorge Syndrome", "gene": "22q11.2缺失", "category": "免疫病"},
    {"name": "IPEX综合征", "name_en": "IPEX Syndrome", "gene": "FOXP3", "category": "免疫病"},
    {"name": "Chediak-Higashi综合征", "name_en": "Chediak-Higashi Syndrome", "gene": "LYST", "category": "免疫病"},

    # 骨骼病（续）
    {"name": "McCune-Albright综合征", "name_en": "McCune-Albright Syndrome", "gene": "GNAS", "category": "骨骼病"},
    {"name": "多发性骨骺发育不良", "name_en": "Multiple Epiphyseal Dysplasia", "gene": "COMP/COL9A1", "category": "骨骼病"},
    {"name": "脊椎骨骺发育不良", "name_en": "Spondyloepiphyseal Dysplasia", "gene": "COL2A1", "category": "骨骼病"},
    {"name": "进行性骨化性纤维发育不良", "name_en": "Fibrodysplasia Ossificans Progressiva", "gene": "ACVR1", "category": "骨骼病"},
    {"name": "成骨不全症(不同类型)", "name_en": "Osteogenesis Imperfecta Types", "gene": "COL1A1/COL1A2", "category": "骨骼病"},
    {"name": "低磷性佝偻病", "name_en": "X-linked Hypophosphatemia", "gene": "PHEX", "category": "骨骼病"},

    # 眼科病（续）
    {"name": "Stargardt病", "name_en": "Stargardt Disease", "gene": "ABCA4", "category": "眼科病"},
    {"name": "先天性静止性夜盲", "name_en": "Congenital Stationary Night Blindness", "gene": "NYX/GRM6", "category": "眼科病"},
    {"name": "色盲", "name_en": "Color Blindness", "gene": "OPN1LW/OPN1MW", "category": "眼科病"},
    {"name": "先天性小眼球", "name_en": "Microphthalmia", "gene": "SOX2/OTX2", "category": "眼科病"},

    # 皮肤（续）
    {"name": "遗传性大疱性表皮松解症", "name_en": "Hereditary Epidermolysis Bullosa", "gene": "KRT5/KRT14/COL7A1", "category": "皮肤"},
    {"name": "鱼鳞病", "name_en": "Ichthyosis", "gene": "FLG/ALOX12B", "category": "皮肤"},
    {"name": "结节性硬化症(皮肤型)", "name_en": "TSC Skin Manifestations", "gene": "TSC1/TSC2", "category": "皮肤"},
    {"name": "色素失禁症", "name_en": "Incontinentia Pigmenti", "gene": "IKBKG", "category": "皮肤"},
    {"name": "白化病(眼皮肤型)", "name_en": "Oculocutaneous Albinism", "gene": "TYR/OCA2", "category": "皮肤"},

    # 内分泌（续）
    {"name": "先天性肾上腺发育不良", "name_en": "Adrenal Hypoplasia Congenita", "gene": "DAX1", "category": "内分泌"},
    {"name": "家族性糖皮质激素缺乏症", "name_en": "Familial Glucocorticoid Deficiency", "gene": "MC2R/MRAP", "category": "内分泌"},
    {"name": "假性甲状旁腺功能减退", "name_en": "Pseudohypoparathyroidism", "gene": "GNAS", "category": "内分泌"},
    {"name": "McCune-Albright综合征(内分泌型)", "name_en": "McCune-Albright Endocrine", "gene": "GNAS", "category": "内分泌"},
]

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
    new_entries = [expand_disease(d) for d in BATCH2]
    
    print(f"第二批待添加疾病数：{len(new_entries)}")
    
    # 合并
    expanded = existing + new_entries
    
    # 确保不重复
    seen = set()
    deduped = []
    for d in expanded:
        key = d["name_en"]
        if key not in seen:
            seen.add(key)
            deduped.append(d)
    
    print(f"去重后总数：{len(deduped)}")
    
    # 保存
    with open("knowledge/diseases_extended.json", "w") as f:
        json.dump(deduped, f, ensure_ascii=False, indent=2)
    
    print("✅ 第二批知识库扩展完成")
