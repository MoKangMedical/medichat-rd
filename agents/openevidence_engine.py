"""
MediChat-RD — OpenEvidence模式引擎
参考OpenEvidence：
- 免费给基层医生AI诊断工具
- 只对接权威数据源（PubMed/Orphanet/OMIM）
- 靠药企"诊断决策时刻推荐位"变现
"""
import json
import uuid
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from enum import Enum


class AdType(str, Enum):
    """广告类型"""
    DRUG_RECOMMENDATION = "药物推荐"
    TEST_RECOMMENDATION = "检测推荐"
    CLINICAL_TRIAL = "临床试验"
    SPECIALIST_REFERRAL = "专科转诊"
    GENETIC_TESTING = "基因检测"


class DecisionMoment(str, Enum):
    """诊断决策时刻"""
    DIFFERENTIAL_DIAGNOSIS = "鉴别诊断"
    TEST_ORDER = "开检查单"
    TREATMENT_PLAN = "制定治疗方案"
    FOLLOW_UP = "随访管理"
    PATIENT_EDUCATION = "患者教育"
    CLINICAL_TRIAL = "临床试验"


@dataclass
class AdSlot:
    """广告位"""
    slot_id: str
    moment: DecisionMoment
    ad_type: AdType
    pharma_company: str
    product_name: str
    product_desc: str
    target_disease: str
    target_symptoms: List[str]
    cpc_price: float  # Cost Per Click
    cpm_price: float  # Cost Per Mille
    relevance_score: float = 0.0
    impression_count: int = 0
    click_count: int = 0


@dataclass
class DoctorProfile:
    """医生档案"""
    doctor_id: str
    name: str
    hospital: str
    department: str
    specialty_diseases: List[str]
    monthly_diagnoses: int = 0
    total_diagnoses: int = 0
    is_free_tier: bool = True
    subscription_type: str = "free"


class OpenEvidenceEngine:
    """
    OpenEvidence模式引擎
    免费诊断工具 + 药企广告变现
    """

    def __init__(self):
        # 医生数据库
        self.doctors: Dict[str, DoctorProfile] = {}
        
        # 广告位数据库
        self.ad_slots: List[AdSlot] = []
        
        # 决策时刻触发器
        self.decision_triggers = self._load_triggers()
        
        # 初始化广告位
        self._init_ad_slots()

    def _load_triggers(self) -> Dict:
        """加载决策时刻触发器"""
        return {
            "重症肌无力": {
                DecisionMoment.DIFFERENTIAL_DIAGNOSIS: [
                    "眼睑下垂", "吞咽困难", "全身无力", "下午加重"
                ],
                DecisionMoment.TEST_ORDER: [
                    "抗体", "检测", "化验", "检查"
                ],
                DecisionMoment.TREATMENT_PLAN: [
                    "治疗", "用药", "方案"
                ],
            },
            "戈谢病": {
                DecisionMoment.DIFFERENTIAL_DIAGNOSIS: [
                    "肝脾肿大", "贫血", "血小板减少", "骨痛"
                ],
                DecisionMoment.TEST_ORDER: [
                    "酶活性", "基因检测"
                ],
            },
            "脊髓性肌萎缩症": {
                DecisionMoment.DIFFERENTIAL_DIAGNOSIS: [
                    "肌无力", "萎缩", "运动发育迟缓"
                ],
                DecisionMoment.TEST_ORDER: [
                    "SMN1", "基因检测"
                ],
            },
        }

    def _init_ad_slots(self):
        """初始化广告位（模拟药企投放）"""
        self.ad_slots = [
            # MG相关
            AdSlot(
                slot_id="ad_001",
                moment=DecisionMoment.TEST_ORDER,
                ad_type=AdType.TEST_RECOMMENDATION,
                pharma_company="罗氏诊断",
                product_name="乙酰胆碱受体抗体检测",
                product_desc="AChR抗体检测，MG诊断金标准",
                target_disease="重症肌无力",
                target_symptoms=["眼睑下垂", "吞咽困难"],
                cpc_price=5.0,
                cpm_price=50.0,
            ),
            AdSlot(
                slot_id="ad_002",
                moment=DecisionMoment.TREATMENT_PLAN,
                ad_type=AdType.DRUG_RECOMMENDATION,
                pharma_company="阿斯利康",
                product_name="依库珠单抗（Soliris）",
                product_desc="C5补体抑制剂，治疗难治性MG",
                target_disease="重症肌无力",
                target_symptoms=["全身无力", "呼吸困难"],
                cpc_price=8.0,
                cpm_price=80.0,
            ),
            AdSlot(
                slot_id="ad_003",
                moment=DecisionMoment.TREATMENT_PLAN,
                ad_type=AdType.DRUG_RECOMMENDATION,
                pharma_company="优时比",
                product_name="zilucoplan",
                product_desc="皮下注射C5抑制剂，MG新疗法",
                target_disease="重症肌无力",
                target_symptoms=["全身无力"],
                cpc_price=6.0,
                cpm_price=60.0,
            ),
            # 戈谢病相关
            AdSlot(
                slot_id="ad_004",
                moment=DecisionMoment.TEST_ORDER,
                ad_type=AdType.GENETIC_TESTING,
                pharma_company="赛诺菲",
                product_name="GBA基因检测",
                product_desc="戈谢病确诊金标准",
                target_disease="戈谢病",
                target_symptoms=["肝脾肿大", "贫血"],
                cpc_price=10.0,
                cpm_price=100.0,
            ),
            AdSlot(
                slot_id="ad_005",
                moment=DecisionMoment.TREATMENT_PLAN,
                ad_type=AdType.DRUG_RECOMMENDATION,
                pharma_company="赛诺菲",
                product_name="伊米苷酶（Cerezyme）",
                product_desc="酶替代疗法，戈谢病一线用药",
                target_disease="戈谢病",
                target_symptoms=["肝脾肿大"],
                cpc_price=15.0,
                cpm_price=150.0,
            ),
            # SMA相关
            AdSlot(
                slot_id="ad_006",
                moment=DecisionMoment.TEST_ORDER,
                ad_type=AdType.GENETIC_TESTING,
                pharma_company="百健",
                product_name="SMN1/SMN2基因检测",
                product_desc="SMA确诊金标准",
                target_disease="脊髓性肌萎缩症",
                target_symptoms=["肌无力", "运动发育迟缓"],
                cpc_price=10.0,
                cpm_price=100.0,
            ),
            AdSlot(
                slot_id="ad_007",
                moment=DecisionMoment.TREATMENT_PLAN,
                ad_type=AdType.DRUG_RECOMMENDATION,
                pharma_company="诺华",
                product_name="Zolgensma",
                product_desc="基因疗法，一次性治愈SMA",
                target_disease="脊髓性肌萎缩症",
                target_symptoms=["肌无力"],
                cpc_price=20.0,
                cpm_price=200.0,
            ),
            # 通用
            AdSlot(
                slot_id="ad_008",
                moment=DecisionMoment.CLINICAL_TRIAL,
                ad_type=AdType.CLINICAL_TRIAL,
                pharma_company="多家药企",
                product_name="罕见病临床试验招募",
                product_desc="匹配适合的临床试验",
                target_disease="通用",
                target_symptoms=[],
                cpc_price=3.0,
                cpm_price=30.0,
            ),
        ]

    # ========== 医生注册（免费层） ==========

    def register_doctor(self, name: str, hospital: str, department: str, 
                       specialty_diseases: List[str]) -> Dict:
        """医生注册（免费层）"""
        doctor_id = f"doc_{uuid.uuid4().hex[:8]}"
        profile = DoctorProfile(
            doctor_id=doctor_id,
            name=name,
            hospital=hospital,
            department=department,
            specialty_diseases=specialty_diseases,
            is_free_tier=True,
            subscription_type="free",
        )
        self.doctors[doctor_id] = profile
        
        return {
            "doctor_id": doctor_id,
            "status": "registered",
            "tier": "free",
            "features": {
                "deeprare_diagnosis": True,
                "doctor_assistant": True,
                "symptom_checker": True,
                "knowledge_search": True,
                "report_generation": True,
                "ad_supported": True,
            },
            "limits": {
                "monthly_diagnoses": 1000,  # 免费层月诊断上限
                "api_calls": 10000,
            },
            "message": "欢迎加入MediChat-RD！您已获得免费AI诊断工具全功能使用权。"
        }

    # ========== 决策时刻检测 ==========

    def detect_decision_moment(self, disease: str, context: str) -> Optional[Dict]:
        """检测当前是否处于诊断决策时刻"""
        triggers = self.decision_triggers.get(disease, {})
        
        for moment, keywords in triggers.items():
            for keyword in keywords:
                if keyword in context:
                    return {
                        "detected": True,
                        "moment": moment,
                        "disease": disease,
                        "trigger_keyword": keyword,
                    }
        
        return {"detected": False}

    # ========== 广告推荐 ==========

    def get_relevant_ads(self, disease: str, symptoms: List[str], 
                        moment: DecisionMoment, limit: int = 3) -> List[Dict]:
        """获取相关广告推荐"""
        relevant_ads = []
        
        for slot in self.ad_slots:
            # 检查疾病匹配
            if slot.target_disease != "通用" and slot.target_disease != disease:
                continue
            
            # 检查决策时刻匹配
            if slot.moment != moment:
                continue
            
            # 计算相关性分数
            relevance = 0.0
            if slot.target_disease == disease:
                relevance += 0.5
            if any(s in symptoms for s in slot.target_symptoms):
                relevance += 0.3
            if slot.moment == moment:
                relevance += 0.2
            
            if relevance > 0:
                slot.relevance_score = relevance
                relevant_ads.append(slot)
        
        # 按相关性排序
        relevant_ads.sort(key=lambda x: x.relevance_score, reverse=True)
        
        # 返回广告
        result = []
        for ad in relevant_ads[:limit]:
            ad.impression_count += 1
            result.append({
                "slot_id": ad.slot_id,
                "ad_type": ad.ad_type.value,
                "pharma_company": ad.pharma_company,
                "product_name": ad.product_name,
                "product_desc": ad.product_desc,
                "relevance_score": round(ad.relevance_score, 2),
                "cpc_price": ad.cpc_price,
                "is_sponsored": True,
            })
        
        return result

    def record_click(self, slot_id: str) -> Dict:
        """记录广告点击"""
        for slot in self.ad_slots:
            if slot.slot_id == slot_id:
                slot.click_count += 1
                return {
                    "clicked": True,
                    "revenue": slot.cpc_price,
                    "pharma_company": slot.pharma_company,
                }
        return {"clicked": False}

    # ========== 诊断流程中的广告植入 ==========

    def process_diagnosis(self, doctor_id: str, disease: str, 
                         symptoms: List[str], context: str) -> Dict:
        """
        处理诊断流程 + 广告植入
        这是核心变现逻辑
        """
        # 更新医生统计
        if doctor_id in self.doctors:
            self.doctors[doctor_id].monthly_diagnoses += 1
            self.doctors[doctor_id].total_diagnoses += 1
        
        # 检测决策时刻
        moment_result = self.detect_decision_moment(disease, context)
        
        ads = []
        if moment_result.get("detected"):
            moment = moment_result["moment"]
            ads = self.get_relevant_ads(disease, symptoms, moment)
        
        # 计算收入
        total_revenue = sum(ad["cpc_price"] for ad in ads if ad.get("is_sponsored"))
        
        return {
            "diagnosis_result": {
                "disease": disease,
                "symptoms": symptoms,
                "confidence": 95,
            },
            "decision_moment": moment_result,
            "sponsored_recommendations": ads,
            "revenue_estimate": total_revenue,
            "doctor_tier": "free",
            "ad_disclosure": "以下推荐由药企赞助，仅供参考",
        }

    # ========== 数据统计 ==========

    def get_stats(self) -> Dict:
        """获取统计信息"""
        total_doctors = len(self.doctors)
        total_impressions = sum(ad.impression_count for ad in self.ad_slots)
        total_clicks = sum(ad.click_count for ad in self.ad_slots)
        total_revenue = sum(ad.click_count * ad.cpc_price for ad in self.ad_slots)
        
        # 按疾病统计
        disease_stats = {}
        for ad in self.ad_slots:
            if ad.target_disease not in disease_stats:
                disease_stats[ad.target_disease] = {
                    "impressions": 0, "clicks": 0, "revenue": 0
                }
            disease_stats[ad.target_disease]["impressions"] += ad.impression_count
            disease_stats[ad.target_disease]["clicks"] += ad.click_count
            disease_stats[ad.target_disease]["revenue"] += ad.click_count * ad.cpc_price
        
        return {
            "total_doctors": total_doctors,
            "free_tier_doctors": sum(1 for d in self.doctors.values() if d.is_free_tier),
            "total_impressions": total_impressions,
            "total_clicks": total_clicks,
            "total_revenue": round(total_revenue, 2),
            "ctr": round(total_clicks / total_impressions * 100, 2) if total_impressions > 0 else 0,
            "disease_stats": disease_stats,
        }

    # ========== 竞品分析 ==========

    def vs_openevidence(self) -> Dict:
        """vs OpenEvidence对比"""
        return {
            "openevidence": {
                "定位": "综合医学AI助手",
                "数据源": "顶级医学期刊",
                "免费策略": "给小诊所医生",
                "变现方式": "药企广告位",
                "估值": "23亿美金",
                "覆盖": "全美40%医护",
            },
            "medichat_rd": {
                "定位": "罕见病垂直AI诊断",
                "数据源": "PubMed+Orphanet+OMIM",
                "免费策略": "给基层罕见病科室",
                "变现方式": "药企推荐位+数据服务",
                "估值": "种子轮500万",
                "目标": "全国30%罕见病科室",
            },
            "差异化优势": [
                "罕见病专精（垂直领域深度）",
                "4层幻觉防护（更严谨）",
                "多Agent协作（完整诊疗流程）",
                "医生助手Jarvis模式",
                "中国本土化（中文+医保）",
            ],
        }


# ========== 测试 ==========
if __name__ == "__main__":
    engine = OpenEvidenceEngine()
    
    print("=" * 60)
    print("💊 OpenEvidence模式引擎测试")
    print("=" * 60)
    
    # 1. 医生注册
    reg = engine.register_doctor(
        name="张医生",
        hospital="某三甲医院",
        department="神经内科",
        specialty_diseases=["重症肌无力", "多发性硬化"]
    )
    print(f"\n✅ 医生注册: {reg['doctor_id']}")
    print(f"   层级: {reg['tier']}")
    print(f"   功能: {list(reg['features'].keys())}")
    
    # 2. 诊断 + 广告植入
    result = engine.process_diagnosis(
        doctor_id=reg['doctor_id'],
        disease="重症肌无力",
        symptoms=["眼睑下垂", "吞咽困难", "全身无力"],
        context="需要开检查单确认诊断"
    )
    
    print(f"\n📋 诊断结果:")
    print(f"   疾病: {result['diagnosis_result']['disease']}")
    print(f"   置信度: {result['diagnosis_result']['confidence']}%")
    
    if result['decision_moment'].get('detected'):
        print(f"\n🎯 决策时刻: {result['decision_moment']['moment']}")
    
    if result['sponsored_recommendations']:
        print(f"\n💰 赞助推荐（药企付费）:")
        for ad in result['sponsored_recommendations']:
            print(f"   • {ad['pharma_company']} - {ad['product_name']}")
            print(f"     {ad['product_desc']}")
            print(f"     CPC: ¥{ad['cpc_price']} | 相关性: {ad['relevance_score']}")
    
    print(f"\n💵 预估收入: ¥{result['revenue_estimate']}")
    
    # 3. 统计
    stats = engine.get_stats()
    print(f"\n📊 统计:")
    print(f"   注册医生: {stats['total_doctors']}")
    print(f"   广告展示: {stats['total_impressions']}")
    print(f"   广告点击: {stats['total_clicks']}")
    print(f"   总收入: ¥{stats['total_revenue']}")
    
    # 4. vs OpenEvidence
    vs = engine.vs_openevidence()
    print(f"\n⚔️ vs OpenEvidence:")
    for k, v in vs['medichat_rd'].items():
        print(f"   MediChat-RD {k}: {v}")
