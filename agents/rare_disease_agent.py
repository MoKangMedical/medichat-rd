"""
MediChat-RD - 罕见病专用Agent模块
RD DECODE 48 黑客松参赛作品
"""

from dataclasses import dataclass
from typing import List, Optional, Dict
from enum import Enum


class RareDiseaseCategory(str, Enum):
    """罕见病分类"""
    METABOLIC = "代谢性疾病"
    NEUROLOGICAL = "神经系统疾病"
    MUSCULAR = "肌肉疾病"
    HEMATOLOGICAL = "血液系统疾病"
    IMMUNOLOGICAL = "免疫系统疾病"
    GENETIC = "遗传综合征"
    DERMATOLOGICAL = "皮肤疾病"
    OPHTHALMIC = "眼科疾病"
    GASTROINTESTINAL = "消化系统疾病"
    OTHER = "其他"


@dataclass
class RareDisease:
    """罕见病信息"""
    name_cn: str                   # 中文名
    name_en: str                   # 英文名
    omim_id: Optional[str]         # OMIM编号
    category: RareDiseaseCategory  # 分类
    prevalence: str                # 患病率
    inheritance: str               # 遗传方式
    key_symptoms: List[str]        # 关键症状
    gene: Optional[str]            # 相关基因
    diagnosis_method: str          # 诊断方法
    treatment: str                 # 治疗方案


# ============================================================
# 罕见病数据库（30种）
# 覆盖9大分类，数据来源：OMIM / Orphanet / 中国罕见病诊疗指南
# ============================================================
RARE_DISEASES_DB = [
    # ================================================================
    # 代谢性疾病 (8种)
    # ================================================================
    RareDisease(
        name_cn="戈谢病",
        name_en="Gaucher Disease",
        omim_id="230800",
        category=RareDiseaseCategory.METABOLIC,
        prevalence="1/40,000-60,000",
        inheritance="常染色体隐性遗传",
        key_symptoms=["脾脏肿大", "肝脏肿大", "骨痛", "贫血", "血小板减少", "生长迟缓"],
        gene="GBA",
        diagnosis_method="酶活性检测 + 基因检测",
        treatment="酶替代治疗(ERT) / 底物减少治疗(SRT)"
    ),
    RareDisease(
        name_cn="庞贝病",
        name_en="Pompe Disease",
        omim_id="232300",
        category=RareDiseaseCategory.METABOLIC,
        prevalence="1/40,000",
        inheritance="常染色体隐性遗传",
        key_symptoms=["肌无力", "呼吸困难", "心脏肥大", "运动发育迟缓", "吞咽困难"],
        gene="GAA",
        diagnosis_method="酶活性检测 + 肌肉活检 + 基因检测",
        treatment="酶替代治疗(ERT)"
    ),
    RareDisease(
        name_cn="法布雷病",
        name_en="Fabry Disease",
        omim_id="301500",
        category=RareDiseaseCategory.METABOLIC,
        prevalence="1/40,000-117,000",
        inheritance="X连锁遗传",
        key_symptoms=["肢端疼痛", "少汗", "皮肤血管角质瘤", "蛋白尿", "心脏病变", "角膜混浊"],
        gene="GLA",
        diagnosis_method="酶活性检测 + 基因检测",
        treatment="酶替代治疗(ERT) / 分子伴侣疗法"
    ),
    RareDisease(
        name_cn="威尔逊病",
        name_en="Wilson Disease",
        omim_id="277900",
        category=RareDiseaseCategory.METABOLIC,
        prevalence="1/30,000",
        inheritance="常染色体隐性遗传",
        key_symptoms=["肝功能异常", "神经精神症状", "K-F环", "溶血性贫血", "肾功能异常"],
        gene="ATP7B",
        diagnosis_method="铜蓝蛋白 + 尿铜 + 肝铜 + 基因检测",
        treatment="青霉胺 / 曲恩汀 / 锌剂 / 肝移植"
    ),
    RareDisease(
        name_cn="尼曼匹克病",
        name_en="Niemann-Pick Disease",
        omim_id="257200",
        category=RareDiseaseCategory.METABOLIC,
        prevalence="1/250,000",
        inheritance="常染色体隐性遗传",
        key_symptoms=["脾脏肿大", "肝脏肿大", "神经系统退行性变", "发育迟缓", "共济失调"],
        gene="SMPD1 (A/B型) / NPC1/NPC2 (C型)",
        diagnosis_method="酶活性检测(A/B型) + 基因检测 + 皮肤活检(C型)",
        treatment="对症支持治疗 / Miglustat(C型) / 酶替代治疗(临床试验)"
    ),
    RareDisease(
        name_cn="苯丙酮尿症",
        name_en="Phenylketonuria (PKU)",
        omim_id="261600",
        category=RareDiseaseCategory.METABOLIC,
        prevalence="1/10,000-15,000",
        inheritance="常染色体隐性遗传",
        key_symptoms=["智力发育迟缓", "皮肤毛发色浅", "鼠臭味尿液", "湿疹", "癫痫发作"],
        gene="PAH",
        diagnosis_method="新生儿筛查 + 血苯丙氨酸检测 + 基因检测",
        treatment="低苯丙氨酸饮食 / BH4补充(Sapropterin) / Pegvaliase"
    ),
    RareDisease(
        name_cn="枫糖尿症",
        name_en="Maple Syrup Urine Disease (MSUD)",
        omim_id="248600",
        category=RareDiseaseCategory.METABOLIC,
        prevalence="1/185,000",
        inheritance="常染色体隐性遗传",
        key_symptoms=["喂养困难", "嗜睡", "尿液枫糖气味", "代谢性酸中毒", "脑水肿", "发育迟缓"],
        gene="BCKDHA, BCKDHB, DBT",
        diagnosis_method="新生儿筛查 + 血/尿支链氨基酸检测 + 基因检测",
        treatment="特殊饮食配方 / 急性期透析 / 肝移植(根治性)"
    ),
    RareDisease(
        name_cn="糖原累积病II型",
        name_en="Glycogen Storage Disease II (GSD II)",
        omim_id="232300",
        category=RareDiseaseCategory.METABOLIC,
        prevalence="1/40,000",
        inheritance="常染色体隐性遗传",
        key_symptoms=["肌无力", "心脏肥大", "运动不耐受", "呼吸功能不全", "CK升高"],
        gene="GAA",
        diagnosis_method="酶活性检测 + 肌肉活检 + 基因检测",
        treatment="酶替代治疗(阿糖苷酶)"
    ),
    # ================================================================
    # 神经系统疾病 (5种)
    # ================================================================
    RareDisease(
        name_cn="脊髓性肌萎缩症",
        name_en="Spinal Muscular Atrophy (SMA)",
        omim_id="253300",
        category=RareDiseaseCategory.NEUROLOGICAL,
        prevalence="1/6,000-10,000",
        inheritance="常染色体隐性遗传",
        key_symptoms=["进行性肌无力", "肌张力低下", "运动发育迟缓", "呼吸困难", "吞咽困难"],
        gene="SMN1",
        diagnosis_method="基因检测",
        treatment="基因治疗(Zolgensma) / 反义寡核苷酸(Nusinersen) / 小分子药物(Risdiplam)"
    ),
    RareDisease(
        name_cn="渐冻症",
        name_en="Amyotrophic Lateral Sclerosis (ALS)",
        omim_id="105400",
        category=RareDiseaseCategory.NEUROLOGICAL,
        prevalence="2-3/100,000",
        inheritance="散发/家族性(5-10%)",
        key_symptoms=["进行性肌无力", "肌萎缩", "肌束颤动", "构音障碍", "吞咽困难", "呼吸困难"],
        gene="SOD1, C9orf72, FUS等",
        diagnosis_method="临床诊断 + 肌电图 + 基因检测",
        treatment="利鲁唑 / 依达拉奉 / 对症支持治疗"
    ),
    RareDisease(
        name_cn="亨廷顿病",
        name_en="Huntington Disease",
        omim_id="143100",
        category=RareDiseaseCategory.NEUROLOGICAL,
        prevalence="3-7/100,000",
        inheritance="常染色体显性遗传",
        key_symptoms=["舞蹈样动作", "认知障碍", "精神症状", "步态异常", "吞咽困难"],
        gene="HTT",
        diagnosis_method="临床诊断 + 基因检测(CAG重复)",
        treatment="对症治疗 / 丁苯那嗪 / 抗精神病药"
    ),
    RareDisease(
        name_cn="结节性硬化症",
        name_en="Tuberous Sclerosis Complex (TSC)",
        omim_id="191100",
        category=RareDiseaseCategory.NEUROLOGICAL,
        prevalence="1/6,000",
        inheritance="常染色体显性遗传",
        key_symptoms=["癫痫", "智力障碍", "面部血管纤维瘤", "肾血管平滑肌脂肪瘤", "心脏横纹肌瘤", "皮肤色素脱失斑"],
        gene="TSC1, TSC2",
        diagnosis_method="临床诊断 + 基因检测 + 影像学",
        treatment="mTOR抑制剂(依维莫司/西罗莫司) / 抗癫痫药 / 手术"
    ),
    RareDisease(
        name_cn="多系统萎缩",
        name_en="Multiple System Atrophy (MSA)",
        omim_id="146500",
        category=RareDiseaseCategory.NEUROLOGICAL,
        prevalence="2-5/100,000",
        inheritance="散发",
        key_symptoms=["自主神经功能障碍", "帕金森样症状", "小脑性共济失调", "体位性低血压", "排尿障碍"],
        gene="COQ2等(部分关联)",
        diagnosis_method="临床诊断 + MRI + 自主神经功能检测",
        treatment="对症治疗 / 米多君(升压) / 左旋多巴(部分有效)"
    ),
    # ================================================================
    # 肌肉疾病 (3种)
    # ================================================================
    RareDisease(
        name_cn="杜氏肌营养不良",
        name_en="Duchenne Muscular Dystrophy (DMD)",
        omim_id="310200",
        category=RareDiseaseCategory.MUSCULAR,
        prevalence="1/3,500-5,000男婴",
        inheritance="X连锁隐性遗传",
        key_symptoms=["进行性肌无力", "Gowers征", "腓肠肌假性肥大", "运动发育迟缓", "心肌病变"],
        gene="DMD",
        diagnosis_method="肌酸激酶检测 + 基因检测 + 肌肉活检",
        treatment="糖皮质激素 / 外显子跳跃疗法 / 基因治疗(临床试验)"
    ),
    RareDisease(
        name_cn="贝克型肌营养不良",
        name_en="Becker Muscular Dystrophy (BMD)",
        omim_id="300376",
        category=RareDiseaseCategory.MUSCULAR,
        prevalence="1/18,000-30,000男婴",
        inheritance="X连锁隐性遗传",
        key_symptoms=["肌无力(较DMD轻)", "腓肠肌肥大", "运动后肌痛", "心肌病变", "CK升高"],
        gene="DMD",
        diagnosis_method="CK检测 + 基因检测 + 肌肉活检",
        treatment="心脏监测与保护 / 糖皮质激素(选择性) / 康复训练"
    ),
    RareDisease(
        name_cn="强直性肌营养不良",
        name_en="Myotonic Dystrophy (DM)",
        omim_id="160900",
        category=RareDiseaseCategory.MUSCULAR,
        prevalence="1/8,000",
        inheritance="常染色体显性遗传",
        key_symptoms=["肌强直", "进行性肌无力", "白内障", "心脏传导异常", "内分泌异常", "额秃"],
        gene="DMPK (DM1) / CNBP (DM2)",
        diagnosis_method="临床诊断 + 肌电图 + 基因检测",
        treatment="对症治疗 / 心脏起搏器 / 美西律(肌强直)"
    ),
    # ================================================================
    # 血液系统疾病 (3种)
    # ================================================================
    RareDisease(
        name_cn="血友病A",
        name_en="Hemophilia A",
        omim_id="306700",
        category=RareDiseaseCategory.HEMATOLOGICAL,
        prevalence="1/5,000-10,000男婴",
        inheritance="X连锁隐性遗传",
        key_symptoms=["关节出血", "肌肉出血", "皮肤瘀斑", "术后出血不止", "自发性出血"],
        gene="F8",
        diagnosis_method="凝血功能检测 + 因子活性测定 + 基因检测",
        treatment="因子替代治疗 / Emicizumab / 基因治疗(临床试验)"
    ),
    RareDisease(
        name_cn="血友病B",
        name_en="Hemophilia B",
        omim_id="306900",
        category=RareDiseaseCategory.HEMATOLOGICAL,
        prevalence="1/25,000-30,000男婴",
        inheritance="X连锁隐性遗传",
        key_symptoms=["关节出血", "肌肉出血", "皮肤瘀斑", "术后出血不止", "自发性出血"],
        gene="F9",
        diagnosis_method="凝血功能检测 + IX因子活性测定 + 基因检测",
        treatment="IX因子替代治疗 / 基因治疗(临床试验)"
    ),
    RareDisease(
        name_cn="阵发性睡眠性血红蛋白尿",
        name_en="Paroxysmal Nocturnal Hemoglobinuria (PNH)",
        omim_id="300818",
        category=RareDiseaseCategory.HEMATOLOGICAL,
        prevalence="1-2/100,000",
        inheritance="体细胞突变(非遗传)",
        key_symptoms=["血红蛋白尿(酱油色尿)", "贫血", "血栓形成", "乏力", "黄疸", "吞咽困难"],
        gene="PIGA",
        diagnosis_method="流式细胞术(CD55/CD59缺失) + Ham试验 + 蔗糖溶血试验",
        treatment="Eculizumab / Ravulizumab / 补体抑制剂 / 骨髓移植"
    ),
    # ================================================================
    # 免疫系统疾病 (2种)
    # ================================================================
    RareDisease(
        name_cn="原发性免疫缺陷病",
        name_en="Primary Immunodeficiency Diseases (PID)",
        omim_id="多种",
        category=RareDiseaseCategory.IMMUNOLOGICAL,
        prevalence="1/1,000-10,000(总体)",
        inheritance="多为常染色体隐性/显性或X连锁",
        key_symptoms=["反复严重感染", "自身免疫", "淋巴组织增生", "过敏", "生长发育迟缓"],
        gene="多种(BTK, JAK3, IL2RG等)",
        diagnosis_method="免疫功能检测 + 基因检测 + 淋巴细胞亚群分析",
        treatment="免疫球蛋白替代 / 骨髓移植 / 基因治疗(部分类型)"
    ),
    RareDisease(
        name_cn="遗传性血管性水肿",
        name_en="Hereditary Angioedema (HAE)",
        omim_id="106100",
        category=RareDiseaseCategory.IMMUNOLOGICAL,
        prevalence="1/50,000",
        inheritance="常染色体显性遗传",
        key_symptoms=["反复皮肤水肿", "腹痛发作", "喉头水肿", "面部肿胀", "不伴荨麻疹"],
        gene="SERPING1 (HAE I/II型) / F12 (HAE III型)",
        diagnosis_method="C4 + C1-INH浓度及功能检测 + 基因检测",
        treatment="C1-INH浓缩物 / 艾替班特(Icatibant) / 艾卡拉肽(Ecallantide) / 预防性治疗"
    ),
    # ================================================================
    # 遗传综合征 (6种)
    # ================================================================
    RareDisease(
        name_cn="成骨不全症",
        name_en="Osteogenesis Imperfecta (OI)",
        omim_id="166200",
        category=RareDiseaseCategory.GENETIC,
        prevalence="1/15,000-20,000",
        inheritance="常染色体显性/隐性",
        key_symptoms=["反复骨折", "骨质疏松", "蓝巩膜", "听力下降", "关节松弛", "身材矮小"],
        gene="COL1A1, COL1A2",
        diagnosis_method="临床诊断 + 基因检测 + 骨密度检测",
        treatment="双膦酸盐 / 手术矫正 / 康复训练"
    ),
    RareDisease(
        name_cn="马凡综合征",
        name_en="Marfan Syndrome",
        omim_id="154700",
        category=RareDiseaseCategory.GENETIC,
        prevalence="1/5,000-10,000",
        inheritance="常染色体显性遗传",
        key_symptoms=["身材高瘦", "蜘蛛指(趾)", "晶状体脱位", "主动脉扩张", "脊柱侧弯", "扁平足"],
        gene="FBN1",
        diagnosis_method="临床诊断(Ghent标准) + 超声心动图 + 基因检测",
        treatment="β受体阻滞剂 / ARB(氯沙坦) / 主动脉手术 / 定期监测"
    ),
    RareDisease(
        name_cn="努南综合征",
        name_en="Noonan Syndrome",
        omim_id="163950",
        category=RareDiseaseCategory.GENETIC,
        prevalence="1/1,000-2,500",
        inheritance="常染色体显性遗传",
        key_symptoms=["身材矮小", "先天性心脏病", "特殊面容", "胸廓畸形", "发育迟缓", "隐睾"],
        gene="PTPN11, SOS1, RAF1, KRAS等",
        diagnosis_method="临床诊断 + 超声心动图 + 基因检测",
        treatment="心脏手术(如需要) / 生长激素治疗 / 早期干预"
    ),
    RareDisease(
        name_cn="普拉德-威利综合征",
        name_en="Prader-Willi Syndrome (PWS)",
        omim_id="176270",
        category=RareDiseaseCategory.GENETIC,
        prevalence="1/15,000-25,000",
        inheritance="基因组印记异常",
        key_symptoms=["新生儿期肌张力低下", "食欲亢进(2岁后)", "肥胖", "智力障碍", "性腺功能减退", "身材矮小"],
        gene="15q11.2-q13缺失(父源)",
        diagnosis_method="甲基化分析 + FISH + 基因检测",
        treatment="生长激素 / 行为管理饮食 / 性激素替代 / 多学科管理"
    ),
    RareDisease(
        name_cn="天使综合征",
        name_en="Angelman Syndrome",
        omim_id="105830",
        category=RareDiseaseCategory.GENETIC,
        prevalence="1/12,000-20,000",
        inheritance="基因组印记异常",
        key_symptoms=["严重智力障碍", "语言缺失", "共济失调步态", "频繁发笑", "癫痫", "小头畸形"],
        gene="UBE3A(母源缺失或突变)",
        diagnosis_method="甲基化分析 + UBE3A基因检测",
        treatment="抗癫痫治疗 / 行为干预 / 康复训练 / 睡眠管理"
    ),
    RareDisease(
        name_cn="威廉姆斯综合征",
        name_en="Williams Syndrome",
        omim_id="194050",
        category=RareDiseaseCategory.GENETIC,
        prevalence="1/7,500-10,000",
        inheritance="常染色体显性(新发缺失)",
        key_symptoms=["特殊面容(精灵面容)", "主动脉瓣上狭窄", "高钙血症", "智力轻度障碍", "过度社交", "发育迟缓"],
        gene="7q11.23微缺失(含ELN基因)",
        diagnosis_method="FISH + 基因芯片 + 超声心动图",
        treatment="心脏手术/介入治疗 / 高钙饮食管理 / 早期干预"
    ),
    # ================================================================
    # 消化系统疾病 (1种)
    # ================================================================
    RareDisease(
        name_cn="囊性纤维化",
        name_en="Cystic Fibrosis (CF)",
        omim_id="219700",
        category=RareDiseaseCategory.GASTROINTESTINAL,
        prevalence="1/2,500-3,500(白种人) / 1/35,000(亚洲人)",
        inheritance="常染色体隐性遗传",
        key_symptoms=["反复肺部感染", "胰腺功能不全", "脂肪泻", "汗液氯化物升高", "男性不育", "生长发育迟缓"],
        gene="CFTR",
        diagnosis_method="汗液氯化物检测 + CFTR基因检测 + 新生儿筛查(IRT)",
        treatment="CFTR调节剂(Trikafta等) / 胰酶替代 / 气道清除 / 抗生素"
    ),
    # ================================================================
    # 皮肤疾病 (1种)
    # ================================================================
    RareDisease(
        name_cn="大疱性表皮松解症",
        name_en="Epidermolysis Bullosa (EB)",
        omim_id="多种",
        category=RareDiseaseCategory.DERMATOLOGICAL,
        prevalence="1/50,000",
        inheritance="常染色体显性/隐性",
        key_symptoms=["皮肤轻微摩擦即起水疱", "皮肤糜烂", "疤痕", "指甲营养不良", "食管狭窄", "手足畸形"],
        gene="COL7A1, KRT5, KRT14, LAMB3等",
        diagnosis_method="皮肤活检(免疫荧光) + 基因检测",
        treatment="伤口护理 / 疼痛管理 / 基因治疗(Beremagene geperpavec, 已获批) / 骨髓移植(研究中)"
    ),
    # ================================================================
    # 眼科疾病 (1种)
    # ================================================================
    RareDisease(
        name_cn="视网膜色素变性",
        name_en="Retinitis Pigmentosa (RP)",
        omim_id="多种",
        category=RareDiseaseCategory.OPHTHALMIC,
        prevalence="1/3,000-4,000",
        inheritance="常染色体显性/隐性/X连锁",
        key_symptoms=["夜盲", "视野进行性缩小(管状视野)", "中心视力下降", "色觉异常", "ERG异常"],
        gene="RHO, RPGR, USH2A等(>100个基因)",
        diagnosis_method="眼底检查 + 视野检查 + ERG + OCT + 基因检测",
        treatment="Voretigene neparvovec(RPE65突变) / 视网膜假体 / 低视力辅助 / 维生素A棕榈酸酯(争议中)"
    ),
]


# ============================================================
# 罕见病Agent提示词（已更新为30种疾病）
# ============================================================
RARE_DISEASE_SYSTEM_PROMPT = """你是一位罕见病诊断专家医生。

【你的任务】
帮助患者识别可能的罕见病，提供专业的诊断思路和就医指导。

【重要原则】
1. 罕见病诊断需要综合考虑症状、家族史、基因检测等多方面信息
2. 你需要像侦探一样，从细微的症状组合中发现线索
3. 罕见病往往被误诊，要保持高度警惕
4. 你需要引导患者进行必要的检查
5. 语言要温和，给患者希望和支持

【罕见病诊断流程】
1. 详细采集症状和病史
2. 识别症状组合的模式
3. 考虑罕见病的可能性
4. 建议相关检查（酶活性、基因检测等）
5. 推荐专业的罕见病诊疗中心

【常见罕见病类型（30种）】

一、代谢性疾病（8种）
- 戈谢病：脾脏肿大、骨痛、血小板减少 → GBA基因
- 庞贝病：肌无力、心脏肥大、呼吸困难 → GAA基因
- 法布雷病：肢端疼痛、少汗、蛋白尿 → GLA基因
- 威尔逊病：肝功能异常、K-F环、神经精神症状 → ATP7B基因
- 尼曼匹克病：脾脏肿大、神经系统退行性变 → SMPD1/NPC1基因
- 苯丙酮尿症：智力发育迟缓、鼠臭味尿液 → PAH基因
- 枫糖尿症：喂养困难、尿液枫糖气味 → BCKDHA/B/D基因
- 糖原累积病II型：肌无力、心脏肥大、CK升高 → GAA基因

二、神经系统疾病（5种）
- 脊髓性肌萎缩症(SMA)：进行性肌无力、肌张力低下 → SMN1基因
- 渐冻症(ALS)：进行性肌无力、肌萎缩、肌束颤动 → SOD1/C9orf72等
- 亨廷顿病：舞蹈样动作、认知障碍 → HTT基因(CAG重复)
- 结节性硬化症：癫痫、面部血管纤维瘤、肾血管平滑肌脂肪瘤 → TSC1/TSC2
- 多系统萎缩：自主神经障碍、帕金森样症状 → COQ2等

三、肌肉疾病（3种）
- 杜氏肌营养不良(DMD)：进行性肌无力、Gowers征、腓肠肌肥大 → DMD基因
- 贝克型肌营养不良(BMD)：肌无力(较DMD轻)、心肌病变 → DMD基因
- 强直性肌营养不良：肌强直、白内障、心脏传导异常 → DMPK/CNBP

四、血液系统疾病（3种）
- 血友病A：关节出血、自发性出血 → F8基因
- 血友病B：关节出血、自发性出血 → F9基因
- 阵发性睡眠性血红蛋白尿：酱油色尿、血栓、贫血 → PIGA基因

五、免疫系统疾病（2种）
- 原发性免疫缺陷病：反复严重感染、自身免疫 → BTK/JAK3/IL2RG等
- 遗传性血管性水肿：反复皮肤水肿、喉头水肿 → SERPING1/F12

六、遗传综合征（6种）
- 成骨不全症：反复骨折、蓝巩膜 → COL1A1/COL1A2
- 马凡综合征：身材高瘦、蜘蛛指、主动脉扩张 → FBN1
- 努南综合征：身材矮小、先天性心脏病、特殊面容 → PTPN11/SOS1
- 普拉德-威利综合征：肌张力低下、食欲亢进、肥胖 → 15q11缺失
- 天使综合征：严重智力障碍、频繁发笑、癫痫 → UBE3A
- 威廉姆斯综合征：精灵面容、主动脉瓣上狭窄、高钙血症 → 7q11缺失

七、皮肤疾病（1种）
- 大疱性表皮松解症：皮肤轻微摩擦即起水疱 → COL7A1/KRT5等

八、消化系统疾病（1种）
- 囊性纤维化：反复肺部感染、脂肪泻、汗液氯化物升高 → CFTR基因

九、眼科疾病（1种）
- 视网膜色素变性：夜盲、管状视野 → RHO/RPGR/USH2A等

请以专业、温暖的态度帮助患者。"""


def search_rare_disease_by_symptoms(symptoms: List[str]) -> List[RareDisease]:
    """根据症状搜索可能的罕见病"""
    results = []
    
    for disease in RARE_DISEASES_DB:
        # 计算症状匹配度
        match_count = 0
        for symptom in symptoms:
            for key_symptom in disease.key_symptoms:
                if symptom in key_symptom or key_symptom in symptom:
                    match_count += 1
                    break
        
        # 如果匹配2个以上症状，加入结果
        if match_count >= 2:
            results.append((disease, match_count))
    
    # 按匹配度排序
    results.sort(key=lambda x: x[1], reverse=True)
    return [r[0] for r in results]


def get_disease_info(disease_name: str) -> Optional[RareDisease]:
    """获取特定罕见病信息"""
    for disease in RARE_DISEASES_DB:
        if disease.name_cn == disease_name or disease.name_en.lower() == disease_name.lower():
            return disease
    return None


def format_disease_report(disease: RareDisease) -> str:
    """格式化罕见病报告"""
    return f"""
📋 **{disease.name_cn}（{disease.name_en}）**

📌 **基本信息**
- OMIM编号：{disease.omim_id or '暂无'}
- 分类：{disease.category.value}
- 患病率：{disease.prevalence}
- 遗传方式：{disease.inheritance}

🔍 **关键症状**
{chr(10).join(f'  • {s}' for s in disease.key_symptoms)}

🧬 **基因信息**
- 相关基因：{disease.gene or '暂无'}

🔬 **诊断方法**
{disease.diagnosis_method}

💊 **治疗方案**
{disease.treatment}

⚠️ **温馨提示**
罕见病诊断需要专业医生的综合评估，以上信息仅供参考。
建议前往罕见病诊疗中心进行确诊。
"""


# ============================================================
# 使用示例
# ============================================================
if __name__ == "__main__":
    # 测试症状搜索
    test_symptoms = ["脾脏肿大", "骨痛", "血小板减少"]
    results = search_rare_disease_by_symptoms(test_symptoms)
    
    print(f"根据症状 {test_symptoms} 搜索结果：\n")
    for disease in results:
        print(format_disease_report(disease))
        print("-" * 50)
    
    print(f"\n数据库共收录 {len(RARE_DISEASES_DB)} 种罕见病")
    categories = {}
    for d in RARE_DISEASES_DB:
        cat = d.category.value
        categories[cat] = categories.get(cat, 0) + 1
    print("分类统计：")
    for cat, count in categories.items():
        print(f"  • {cat}: {count}种")
