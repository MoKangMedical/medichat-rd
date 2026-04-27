"""
MediChat-RD 患者定位功能优化模块
集成地图API，提供精准的医院和专家推荐
"""

import asyncio
import logging
import json
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import math

logger = logging.getLogger(__name__)

@dataclass
class Hospital:
    """医院信息"""
    id: str
    name: str
    address: str
    latitude: float
    longitude: float
    hospital_type: str  # 三甲/三乙/二甲等
    specialties: List[str]
    rating: float
    distance_km: float
    travel_time_minutes: int
    phone: str
    website: str

@dataclass
class Expert:
    """专家信息"""
    id: str
    name: str
    title: str
    hospital_id: str
    hospital_name: str
    department: str
    specialties: List[str]
    experience_years: int
    rating: float
    consultation_fee: float
    available_slots: List[str]

@dataclass
class LocationResult:
    """定位结果"""
    patient_location: Tuple[float, float]
    recommended_hospitals: List[Hospital]
    recommended_experts: List[Expert]
    optimal_route: Dict
    estimated_costs: Dict
    next_steps: List[str]

class EnhancedPatientLocator:
    """增强版患者定位器"""
    
    def __init__(self):
        self.map_api_key = None
        self.hospital_database = {}
        self.expert_database = {}
        self.route_optimizer = None
        
    async def initialize(self):
        """初始化定位器"""
        logger.info("🚀 初始化增强版患者定位器...")
        
        # 加载医院数据库
        await self._load_hospital_database()
        
        # 加载专家数据库
        await self._load_expert_database()
        
        # 初始化地图API
        await self._initialize_map_api()
        
        # 初始化路由优化器
        await self._initialize_route_optimizer()
        
        logger.info("✅ 患者定位器初始化完成")
    
    async def _load_hospital_database(self):
        """加载医院数据库"""
        # 模拟加载医院数据
        self.hospital_database = {
            "PUMCH": {
                "id": "PUMCH",
                "name": "北京协和医院",
                "address": "北京市东城区帅府园1号",
                "latitude": 39.9135,
                "longitude": 116.4105,
                "hospital_type": "三甲",
                "specialties": ["罕见病", "遗传病", "内分泌", "神经内科"],
                "rating": 4.9,
                "phone": "010-69156114",
                "website": "http://www.pumch.cn"
            },
            "CMUSH": {
                "id": "CMUSH",
                "name": "首都医科大学附属北京儿童医院",
                "address": "北京市西城区南礼士路56号",
                "latitude": 39.9087,
                "longitude": 116.3587,
                "hospital_type": "三甲",
                "specialties": ["儿科罕见病", "遗传代谢病", "神经遗传病"],
                "rating": 4.8,
                "phone": "010-59616161",
                "website": "http://www.bch.com.cn"
            },
            "SHCH": {
                "id": "SHCH",
                "name": "上海儿童医学中心",
                "address": "上海市浦东新区东方路1678号",
                "latitude": 31.2090,
                "longitude": 121.5270,
                "hospital_type": "三甲",
                "specialties": ["罕见病", "遗传咨询", "基因诊断"],
                "rating": 4.7,
                "phone": "021-38626161",
                "website": "http://www.scmc.com.cn"
            }
        }
        
        logger.info(f"✅ 加载 {len(self.hospital_database)} 家医院")
    
    async def _load_expert_database(self):
        """加载专家数据库"""
        # 模拟加载专家数据
        self.expert_database = {
            "DR001": {
                "id": "DR001",
                "name": "张教授",
                "title": "主任医师",
                "hospital_id": "PUMCH",
                "hospital_name": "北京协和医院",
                "department": "罕见病中心",
                "specialties": ["遗传代谢病", "溶酶体贮积症", "线粒体病"],
                "experience_years": 25,
                "rating": 4.9,
                "consultation_fee": 500,
                "available_slots": ["2026-04-03 09:00", "2026-04-03 14:00", "2026-04-04 10:00"]
            },
            "DR002": {
                "id": "DR002",
                "name": "李主任",
                "title": "副主任医师",
                "hospital_id": "CMUSH",
                "hospital_name": "北京儿童医院",
                "department": "遗传代谢科",
                "specialties": ["儿童罕见病", "遗传代谢病", "新生儿筛查"],
                "experience_years": 18,
                "rating": 4.8,
                "consultation_fee": 300,
                "available_slots": ["2026-04-03 08:30", "2026-04-04 09:00"]
            },
            "DR003": {
                "id": "DR003",
                "name": "王医生",
                "title": "主治医师",
                "hospital_id": "SHCH",
                "hospital_name": "上海儿童医学中心",
                "department": "遗传科",
                "specialties": ["基因诊断", "遗传咨询", "罕见病管理"],
                "experience_years": 12,
                "rating": 4.7,
                "consultation_fee": 200,
                "available_slots": ["2026-04-03 13:30", "2026-04-04 14:00"]
            }
        }
        
        logger.info(f"✅ 加载 {len(self.expert_database)} 位专家")
    
    async def _initialize_map_api(self):
        """初始化地图API"""
        # 模拟初始化高德/百度地图API
        self.map_api_key = "simulated_api_key"
        logger.info("✅ 地图API初始化完成")
    
    async def _initialize_route_optimizer(self):
        """初始化路由优化器"""
        self.route_optimizer = RouteOptimizer()
        logger.info("✅ 路由优化器初始化完成")
    
    async def locate_and_recommend(self, patient_location: Tuple[float, float], 
                                 disease_name: str, 
                                 preferences: Dict = None) -> LocationResult:
        """定位并推荐"""
        logger.info(f"📍 患者定位: {patient_location}, 疾病: {disease_name}")
        
        # 1. 查找合适的医院
        suitable_hospitals = await self._find_suitable_hospitals(disease_name, patient_location)
        
        # 2. 查找合适的专家
        suitable_experts = await self._find_suitable_experts(disease_name, suitable_hospitals)
        
        # 3. 计算最优路线
        optimal_route = await self._calculate_optimal_route(patient_location, suitable_hospitals)
        
        # 4. 估算费用
        estimated_costs = await self._estimate_costs(suitable_hospitals, suitable_experts)
        
        # 5. 生成下一步建议
        next_steps = self._generate_next_steps(disease_name, suitable_hospitals, suitable_experts)
        
        return LocationResult(
            patient_location=patient_location,
            recommended_hospitals=suitable_hospitals,
            recommended_experts=suitable_experts,
            optimal_route=optimal_route,
            estimated_costs=estimated_costs,
            next_steps=next_steps
        )
    
    async def _find_suitable_hospitals(self, disease_name: str, patient_location: Tuple[float, float]) -> List[Hospital]:
        """查找合适的医院"""
        suitable_hospitals = []
        
        for hospital_id, hospital_data in self.hospital_database.items():
            # 检查专科匹配
            if self._check_specialty_match(disease_name, hospital_data["specialties"]):
                # 计算距离
                distance = self._calculate_distance(
                    patient_location, 
                    (hospital_data["latitude"], hospital_data["longitude"])
                )
                
                # 创建医院对象
                hospital = Hospital(
                    id=hospital_data["id"],
                    name=hospital_data["name"],
                    address=hospital_data["address"],
                    latitude=hospital_data["latitude"],
                    longitude=hospital_data["longitude"],
                    hospital_type=hospital_data["hospital_type"],
                    specialties=hospital_data["specialties"],
                    rating=hospital_data["rating"],
                    distance_km=distance,
                    travel_time_minutes=int(distance * 3),  # 假设每公里3分钟
                    phone=hospital_data["phone"],
                    website=hospital_data["website"]
                )
                
                suitable_hospitals.append(hospital)
        
        # 按距离和评分排序
        suitable_hospitals.sort(key=lambda x: (x.distance_km, -x.rating))
        
        return suitable_hospitals[:5]  # 返回前5家
    
    def _check_specialty_match(self, disease_name: str, specialties: List[str]) -> bool:
        """检查专科匹配"""
        disease_keywords = disease_name.lower().split()
        
        for specialty in specialties:
            specialty_lower = specialty.lower()
            for keyword in disease_keywords:
                if keyword in specialty_lower:
                    return True
        
        return False
    
    def _calculate_distance(self, loc1: Tuple[float, float], loc2: Tuple[float, float]) -> float:
        """计算两点间距离（公里）"""
        lat1, lon1 = loc1
        lat2, lon2 = loc2
        
        # Haversine公式
        R = 6371  # 地球半径（公里）
        
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        
        a = (math.sin(dlat/2) * math.sin(dlat/2) + 
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * 
             math.sin(dlon/2) * math.sin(dlon/2))
        
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        distance = R * c
        
        return round(distance, 2)
    
    async def _find_suitable_experts(self, disease_name: str, hospitals: List[Hospital]) -> List[Expert]:
        """查找合适的专家"""
        suitable_experts = []
        
        hospital_ids = [h.id for h in hospitals]
        
        for expert_id, expert_data in self.expert_database.items():
            # 检查医院匹配
            if expert_data["hospital_id"] in hospital_ids:
                # 检查专科匹配
                if self._check_specialty_match(disease_name, expert_data["specialties"]):
                    expert = Expert(
                        id=expert_data["id"],
                        name=expert_data["name"],
                        title=expert_data["title"],
                        hospital_id=expert_data["hospital_id"],
                        hospital_name=expert_data["hospital_name"],
                        department=expert_data["department"],
                        specialties=expert_data["specialties"],
                        experience_years=expert_data["experience_years"],
                        rating=expert_data["rating"],
                        consultation_fee=expert_data["consultation_fee"],
                        available_slots=expert_data["available_slots"]
                    )
                    
                    suitable_experts.append(expert)
        
        # 按评分和经验排序
        suitable_experts.sort(key=lambda x: (-x.rating, -x.experience_years))
        
        return suitable_experts[:3]  # 返回前3位
    
    async def _calculate_optimal_route(self, start: Tuple[float, float], hospitals: List[Hospital]) -> Dict:
        """计算最优路线"""
        if not hospitals:
            return {}
        
        # 简单优化：选择最近的医院
        nearest_hospital = min(hospitals, key=lambda h: h.distance_km)
        
        return {
            "start_location": start,
            "destination": {
                "name": nearest_hospital.name,
                "address": nearest_hospital.address,
                "coordinates": (nearest_hospital.latitude, nearest_hospital.longitude)
            },
            "distance_km": nearest_hospital.distance_km,
            "estimated_time_minutes": nearest_hospital.travel_time_minutes,
            "transportation_options": [
                {"type": "驾车", "time": nearest_hospital.travel_time_minutes},
                {"type": "公共交通", "time": nearest_hospital.travel_time_minutes + 15},
                {"type": "打车", "time": nearest_hospital.travel_time_minutes + 5}
            ]
        }
    
    async def _estimate_costs(self, hospitals: List[Hospital], experts: List[Expert]) -> Dict:
        """估算费用"""
        costs = {
            "consultation_fee": 0,
            "transportation": 0,
            "accommodation": 0,
            "total_estimated": 0
        }
        
        if experts:
            # 取最贵的专家咨询费
            costs["consultation_fee"] = max(e.consultation_fee for e in experts)
        
        if hospitals:
            # 估算交通费（假设每公里2元）
            nearest_distance = min(h.distance_km for h in hospitals)
            costs["transportation"] = nearest_distance * 2
        
        costs["total_estimated"] = sum(costs.values())
        
        return costs
    
    def _generate_next_steps(self, disease_name: str, hospitals: List[Hospital], experts: List[Expert]) -> List[str]:
        """生成下一步建议"""
        steps = []
        
        if hospitals:
            steps.append(f"预约 {hospitals[0].name} 的专家门诊")
        
        if experts:
            steps.append(f"准备病历资料，包括既往检查报告")
            steps.append(f"提前了解 {experts[0].name} 医生的出诊时间")
        
        steps.extend([
            "准备好医保卡和相关证件",
            "提前规划出行路线",
            "准备好想要咨询的问题清单"
        ])
        
        return steps

class RouteOptimizer:
    """路由优化器"""
    
    def __init__(self):
        self.traffic_data = {}
    
    async def optimize_route(self, start: Tuple[float, float], destinations: List[Tuple[float, float]]) -> Dict:
        """优化路线"""
        # 模拟路线优化
        return {
            "optimized_order": list(range(len(destinations))),
            "total_distance": sum(self._calculate_distance(start, dest) for dest in destinations),
            "estimated_time": len(destinations) * 30  # 假设每个目的地30分钟
        }
    
    def _calculate_distance(self, loc1: Tuple[float, float], loc2: Tuple[float, float]) -> float:
        """计算距离"""
        lat1, lon1 = loc1
        lat2, lon2 = loc2
        
        R = 6371
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        
        a = (math.sin(dlat/2) * math.sin(dlat/2) + 
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * 
             math.sin(dlon/2) * math.sin(dlon/2))
        
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return R * c

# 使用示例
async def demo_patient_locator():
    """演示患者定位功能"""
    print("📍 MediChat-RD 患者定位功能演示")
    print("=" * 50)
    
    # 创建定位器
    locator = EnhancedPatientLocator()
    await locator.initialize()
    
    # 模拟患者位置（北京市中心）
    patient_location = (39.9042, 116.4074)
    
    # 测试不同疾病
    test_cases = [
        ("Albinism", "白化病"),
        ("Fabry Disease", "法布里病"),
        ("Gaucher Disease", "戈谢病")
    ]
    
    for disease_en, disease_cn in test_cases:
        print(f"\n🔍 查找 {disease_cn} ({disease_en}) 的医疗资源...")
        
        result = await locator.locate_and_recommend(
            patient_location=patient_location,
            disease_name=disease_en
        )
        
        print(f"📍 推荐医院: {len(result.recommended_hospitals)} 家")
        for hospital in result.recommended_hospitals[:2]:
            print(f"  • {hospital.name} ({hospital.distance_km}公里)")
        
        print(f"👨‍⚕️ 推荐专家: {len(result.recommended_experts)} 位")
        for expert in result.recommended_experts[:2]:
            print(f"  • {expert.name} - {expert.title} ({expert.hospital_name})")
        
        print(f"🚗 最优路线: {result.optimal_route.get('distance_km', 0)}公里")
        print(f"💰 预估费用: ¥{result.estimated_costs.get('total_estimated', 0)}")
        
        print(f"📋 下一步建议:")
        for step in result.next_steps[:3]:
            print(f"  • {step}")

if __name__ == "__main__":
    asyncio.run(demo_patient_locator())