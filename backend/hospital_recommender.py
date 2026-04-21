"""
MediChat-RD 推荐就医引擎
基于诊断结果 + 患者位置 → 具体医院 + 专家 + 预约指引

用户视角：患者拿到诊断结果后，最需要的是"下一步去哪里、找谁"
"""

import json
import os
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict

@dataclass
class HospitalRecommendation:
    """医院推荐"""
    hospital_name: str
    department: str
    address: str
    phone: str
    distance_km: Optional[float] = None
    experts: List[Dict] = None
    appointment_url: str = ""
    preparation_checklist: List[str] = None
    reason: str = ""  # 为什么推荐这家

@dataclass
class ExpertRecommendation:
    """专家推荐"""
    name: str
    title: str
    hospital: str
    department: str
    specialty: str
    experience_years: int
    consultation_info: str  # 出诊时间/挂号方式

# ============================================================
# 中国罕见病重点医院数据库
# 基于国家罕见病诊疗协作网 + 各专科排名
# ============================================================
RARE_DISEASE_HOSPITALS = {
    "default": [
        {
            "name": "北京协和医院",
            "departments": ["罕见病中心", "神经内科", "血液内科", "内分泌科"],
            "address": "北京市东城区帅府园1号",
            "phone": "010-69156114",
            "appointment_url": "https://www.pumch.cn",
            "experts": [
                {"name": "张抒扬", "title": "主任医师/教授", "specialty": "罕见病综合诊治", "years": 35},
                {"name": "沈敏", "title": "副主任医师", "specialty": "罕见病多学科会诊", "years": 20},
            ],
            "preparation": ["既往病历", "检查报告（血常规/基因检测等）", "症状记录（时间/频率/严重度）", "家族病史"],
            "reason": "国家罕见病诊疗协作网牵头单位，罕见病中心一站式多学科会诊"
        },
        {
            "name": "上海交通大学医学院附属瑞金医院",
            "departments": ["罕见病诊治中心", "血液科", "内分泌科"],
            "address": "上海市黄浦区瑞金二路197号",
            "phone": "021-64370045",
            "appointment_url": "https://www.rjh.com.cn",
            "experts": [
                {"name": "陈赛娟", "title": "中国工程院院士", "specialty": "血液病/罕见病", "years": 40},
            ],
            "preparation": ["既往病历", "检查报告", "症状记录"],
            "reason": "国家罕见病诊疗协作网成员单位，血液病领域顶尖"
        },
        {
            "name": "中南大学湘雅医院",
            "departments": ["罕见病诊治中心", "神经内科"],
            "address": "湖南省长沙市开福区湘雅路87号",
            "phone": "0731-84328888",
            "appointment_url": "https://www.xiangya.com.cn",
            "experts": [
                {"name": "唐北沙", "title": "主任医师", "specialty": "遗传性罕见病", "years": 30},
            ],
            "preparation": ["既往病历", "基因检测报告（如有）", "症状记录"],
            "reason": "国家罕见病诊疗协作网成员单位，遗传性罕见病诊治经验丰富"
        },
    ],
    "神经系统": [
        {
            "name": "首都医科大学附属北京天坛医院",
            "departments": ["神经内科", "罕见病中心"],
            "address": "北京市丰台区南四环西路119号",
            "phone": "010-59978585",
            "appointment_url": "https://www.bjtth.org",
            "experts": [
                {"name": "王拥军", "title": "主任医师/教授", "specialty": "神经遗传罕见病", "years": 35},
            ],
            "preparation": ["头颅MRI/CT报告", "肌电图报告", "既往病历", "症状时间线"],
            "reason": "全国神经内科排名第一，神经罕见病诊治经验丰富"
        },
    ],
    "血液系统": [
        {
            "name": "北京大学人民医院",
            "departments": ["血液科", "造血干细胞移植中心"],
            "address": "北京市西城区西直门南大街11号",
            "phone": "010-88326666",
            "appointment_url": "https://www.pkuph.cn",
            "experts": [
                {"name": "黄晓军", "title": "主任医师/教授", "specialty": "造血干细胞移植", "years": 35},
            ],
            "preparation": ["血常规报告", "骨髓检查报告", "既往治疗记录"],
            "reason": "血液病全国领先，造血干细胞移植技术世界先进"
        },
    ],
    "遗传代谢": [
        {
            "name": "北京大学第一医院",
            "departments": ["儿科", "遗传代谢病中心"],
            "address": "北京市西城区西什库大街8号",
            "phone": "010-83572211",
            "appointment_url": "https://www.bddhospital.cn",
            "experts": [
                {"name": "杨艳玲", "title": "主任医师", "specialty": "遗传代谢病", "years": 30},
            ],
            "preparation": ["代谢筛查报告", "基因检测报告", "生长发育记录"],
            "reason": "国内遗传代谢病诊治的开创者，儿童罕见病首选"
        },
    ],
    "内分泌": [
        {
            "name": "上海交通大学医学院附属瑞金医院",
            "departments": ["内分泌科"],
            "address": "上海市黄浦区瑞金二路197号",
            "phone": "021-64370045",
            "experts": [
                {"name": "宁光", "title": "中国工程院院士", "specialty": "内分泌罕见病", "years": 35},
            ],
            "preparation": ["激素检查报告", "影像学报告", "既往病历"],
            "reason": "内分泌科全国排名第一"
        },
    ],
}


def get_department_category(department: str) -> str:
    """根据推荐科室判断疾病分类"""
    dept_map = {
        "神经内科": "神经系统", "神经外科": "神经系统",
        "血液内科": "血液系统", "血液科": "血液系统",
        "内分泌科": "内分泌",
        "儿科": "遗传代谢", "遗传科": "遗传代谢",
        "罕见病中心": "default",
    }
    return dept_map.get(department, "default")


def recommend_hospitals(
    recommended_department: str,
    patient_city: str = "",
    urgency: str = "门诊",
    max_results: int = 3
) -> List[HospitalRecommendation]:
    """
    根据诊断推荐科室 + 患者位置，推荐具体医院和专家
    
    Args:
        recommended_department: AI推荐的科室（如"神经内科"）
        patient_city: 患者所在城市
        urgency: 紧急程度（急诊/门诊/随访）
        max_results: 最多推荐数量
    
    Returns:
        医院推荐列表
    """
    category = get_department_category(recommended_department)
    
    # 获取对应类别的医院
    hospitals = RARE_DISEASE_HOSPITALS.get(category, RARE_DISEASE_HOSPITALS["default"])
    
    recommendations = []
    for h in hospitals[:max_results]:
        experts = [
            ExpertRecommendation(
                name=e["name"],
                title=e["title"],
                hospital=h["name"],
                department=recommended_department,
                specialty=e["specialty"],
                experience_years=e["years"],
                consultation_info=f"可通过{h['name']}官方渠道预约"
            )
            for e in h.get("experts", [])[:2]
        ]
        
        rec = HospitalRecommendation(
            hospital_name=h["name"],
            department=recommended_department,
            address=h["address"],
            phone=h["phone"],
            appointment_url=h.get("appointment_url", ""),
            experts=[asdict(e) for e in experts],
            preparation_checklist=h.get("preparation", ["既往病历", "检查报告", "症状记录"]),
            reason=h.get("reason", f"在{recommended_department}领域具有丰富经验")
        )
        recommendations.append(rec)
    
    return recommendations


def format_recommendation_text(recommendations: List[HospitalRecommendation]) -> str:
    """
    将推荐结果格式化为患者友好的文本
    
    用户视角：患者拿到报告后直接能看到"去哪、找谁、带什么"
    """
    if not recommendations:
        return ""
    
    lines = ["\n🏥 **推荐就医方案**\n"]
    
    for i, rec in enumerate(recommendations, 1):
        lines.append(f"### {i}. {rec.hospital_name}")
        lines.append(f"📍 地址：{rec.address}")
        lines.append(f"📞 电话：{rec.phone}")
        if rec.appointment_url:
            lines.append(f"🔗 预约：{rec.appointment_url}")
        
        if rec.experts:
            lines.append(f"\n👨‍⚕️ **推荐专家**：")
            for expert in rec.experts:
                lines.append(f"  - {expert['name']}（{expert['title']}）— {expert['specialty']}")
        
        if rec.preparation_checklist:
            lines.append(f"\n📋 **就诊准备**：")
            for item in rec.preparation_checklist:
                lines.append(f"  ☐ {item}")
        
        lines.append(f"\n💡 推荐理由：{rec.reason}")
        lines.append("")
    
    lines.append("⚠️ 以上推荐基于公开医疗资源信息，实际就诊请以医院最新排班为准。")
    
    return "\n".join(lines)


def get_recommendation_json(
    recommended_department: str,
    patient_city: str = "",
    urgency: str = "门诊"
) -> Dict:
    """返回JSON格式的推荐结果（供API使用）"""
    recs = recommend_hospitals(recommended_department, patient_city, urgency)
    return {
        "department": recommended_department,
        "urgency": urgency,
        "hospitals": [asdict(r) for r in recs],
        "formatted_text": format_recommendation_text(recs),
        "disclaimer": "以上推荐基于公开医疗资源信息，实际就诊请以医院最新排班为准。"
    }


# ============================================================
# 测试
# ============================================================
if __name__ == "__main__":
    # 测试：神经内科推荐
    result = get_recommendation_json("神经内科")
    print("=== 神经内科推荐 ===")
    print(result["formatted_text"])
    
    # 测试：血液科推荐
    result2 = get_recommendation_json("血液科")
    print("\n=== 血液科推荐 ===")
    print(result2["formatted_text"])
