"""
MediChat-RD 患者定位服务
基于HTML5 Geolocation + 逆地理编码
"""

import requests
import json
from typing import Dict, Optional, List
from dataclasses import dataclass
from datetime import datetime

@dataclass
class Location:
    """患者位置信息"""
    latitude: float
    longitude: float
    address: str
    city: str
    province: str
    district: str
    timestamp: str

@dataclass
class NearbyHospital:
    """就近医院信息"""
    name: str
    address: str
    distance: float  # 公里
    phone: str
    departments: List[str]
    specialty: str
    rating: float
    source: str
    url: str

class PatientLocationService:
    """患者定位服务"""
    
    def __init__(self):
        # 高德地图API（免费额度足够）
        self.amap_key = "YOUR_AMAP_KEY"  # 需要申请
        self.amap_geocode_url = "https://restapi.amap.com/v3/geocode/regeo"
        self.amap_poi_url = "https://restapi.amap.com/v3/place/around"
        
        # 百度地图API（备用）
        self.baidu_key = "YOUR_BAIDU_KEY"
        self.baidu_geocode_url = "https://api.map.baidu.com/reverse_geocoding/v3"
    
    def get_location_from_browser(self, lat: float, lng: float) -> Location:
        """从浏览器获取的经纬度，逆地理编码获取地址"""
        try:
            # 使用高德地图逆地理编码
            params = {
                "key": self.amap_key,
                "location": f"{lng},{lat}",
                "output": "JSON",
                "extensions": "base"
            }
            
            response = requests.get(self.amap_geocode_url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "1":
                    regeocode = data.get("regeocode", {})
                    address = regeocode.get("formatted_address", "")
                    address_component = regeocode.get("addressComponent", {})
                    
                    return Location(
                        latitude=lat,
                        longitude=lng,
                        address=address,
                        city=address_component.get("city", ""),
                        province=address_component.get("province", ""),
                        district=address_component.get("district", ""),
                        timestamp=datetime.now().isoformat()
                    )
        except Exception as e:
            print(f"逆地理编码失败: {e}")
        
        # 返回基本信息
        return Location(
            latitude=lat,
            longitude=lng,
            address=f"{lat:.4f}, {lng:.4f}",
            city="",
            province="",
            district="",
            timestamp=datetime.now().isoformat()
        )
    
    def find_nearby_hospitals(self, lat: float, lng: float, radius: int = 5000, keyword: str = "医院") -> List[NearbyHospital]:
        """查找就近医院（高德地图POI搜索）"""
        hospitals = []
        
        try:
            params = {
                "key": self.amap_key,
                "location": f"{lng},{lat}",
                "keywords": keyword,
                "radius": radius,
                "types": "090100",  # 医院类型编码
                "output": "JSON",
                "offset": 20,  # 返回20个结果
                "page": 1
            }
            
            response = requests.get(self.amap_poi_url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "1":
                    pois = data.get("pois", [])
                    for poi in pois:
                        # 计算距离
                        location = poi.get("location", "").split(",")
                        if len(location) == 2:
                            poi_lng, poi_lat = float(location[0]), float(location[1])
                            distance = self._calculate_distance(lat, lng, poi_lat, poi_lng)
                        else:
                            distance = 0
                        
                        hospitals.append(NearbyHospital(
                            name=poi.get("name", ""),
                            address=poi.get("address", ""),
                            distance=round(distance, 2),
                            phone=poi.get("tel", ""),
                            departments=[],  # 高德地图不提供科室信息
                            specialty=poi.get("type", ""),
                            rating=float(poi.get("biz_ext", {}).get("rating", 0)),
                            source="高德地图",
                            url=""
                        ))
        except Exception as e:
            print(f"查找就近医院失败: {e}")
        
        # 按距离排序
        hospitals.sort(key=lambda x: x.distance)
        return hospitals[:10]  # 返回最近的10家
    
    def find_nearby_specialists(self, lat: float, lng: float, disease: str) -> List[Dict]:
        """查找就近专科医生（需要爬虫配合）"""
        # 这个功能需要配合爬虫服务
        # 先返回基础信息
        return []
    
    def _calculate_distance(self, lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """计算两点之间的距离（公里）"""
        import math
        
        R = 6371  # 地球半径（公里）
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lng = math.radians(lng2 - lng1)
        
        a = math.sin(delta_lat / 2) ** 2 + \
            math.cos(lat1_rad) * math.cos(lat2_rad) * \
            math.sin(delta_lng / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c

# 前端JavaScript代码（供参考）
FRONTEND_GEOLOCATION_CODE = """
// 患者定位功能
class PatientLocation {
  constructor() {
    this.location = null;
    this.permission = null;
  }
  
  // 请求定位权限
  async requestLocation() {
    return new Promise((resolve, reject) => {
      if (!navigator.geolocation) {
        reject(new Error('浏览器不支持定位'));
        return;
      }
      
      navigator.geolocation.getCurrentPosition(
        (position) => {
          this.location = {
            latitude: position.coords.latitude,
            longitude: position.coords.longitude,
            accuracy: position.coords.accuracy,
            timestamp: new Date().toISOString()
          };
          resolve(this.location);
        },
        (error) => {
          switch(error.code) {
            case error.PERMISSION_DENIED:
              reject(new Error('用户拒绝定位请求'));
              break;
            case error.POSITION_UNAVAILABLE:
              reject(new Error('位置信息不可用'));
              break;
            case error.TIMEOUT:
              reject(new Error('定位请求超时'));
              break;
            default:
              reject(new Error('定位失败'));
          }
        },
        {
          enableHighAccuracy: true,
          timeout: 10000,
          maximumAge: 300000  // 5分钟缓存
        }
      );
    });
  }
  
  // 发送位置到后端
  async sendLocation() {
    if (!this.location) {
      await this.requestLocation();
    }
    
    try {
      const response = await fetch('/api/v1/location', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(this.location)
      });
      return await response.json();
    } catch (error) {
      console.error('发送位置失败:', error);
      throw error;
    }
  }
  
  // 获取就近医院
  async getNearbyHospitals(radius = 5000) {
    if (!this.location) {
      await this.requestLocation();
    }
    
    try {
      const response = await fetch(`/api/v1/location/nearby-hospitals?lat=${this.location.latitude}&lng=${this.location.longitude}&radius=${radius}`);
      return await response.json();
    } catch (error) {
      console.error('获取就近医院失败:', error);
      throw error;
    }
  }
}
"""

if __name__ == "__main__":
    # 测试
    service = PatientLocationService()
    
    # 模拟北京协和医院附近的位置
    lat, lng = 39.9136, 116.4244
    
    location = service.get_location_from_browser(lat, lng)
    print(f"位置: {location.address}")
    print(f"城市: {location.city}")
    
    hospitals = service.find_nearby_hospitals(lat, lng)
    print(f"\n就近医院 ({len(hospitals)}家):")
    for h in hospitals[:5]:
        print(f"  - {h.name} ({h.distance}km)")
