"""
MediChat-RD 医院/专家信息爬虫服务
爬取好大夫、微医等平台的医院和专家信息
"""

import requests
import json
import re
import time
from typing import List, Dict, Optional
from dataclasses import dataclass
from bs4 import BeautifulSoup
from urllib.parse import quote
import random

@dataclass
class Doctor:
    """医生信息"""
    name: str
    title: str
    hospital: str
    department: str
    specialty: str
    rating: float
    consultation_count: int
    good_at: str  # 擅长疾病
    introduction: str
    avatar: str
    source: str
    url: str

@dataclass
class HospitalDetail:
    """医院详细信息"""
    name: str
    level: str  # 三甲/三乙/二甲等
    address: str
    phone: str
    website: str
    departments: List[str]
    specialty_departments: List[str]  # 重点科室
    rating: float
    source: str
    url: str

class HospitalExpertCrawler:
    """医院/专家信息爬虫"""
    
    def __init__(self):
        # 好大夫在线
        self.haodf_base = "https://www.haodf.com"
        self.haodf_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        }
        
        # 微医
        self.guahao_base = "https://www.guahao.com"
        self.guahao_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        }
        
        # 请求延迟（避免被封）
        self.request_delay = (1, 3)
    
    def _random_delay(self):
        """随机延迟"""
        time.sleep(random.uniform(*self.request_delay))
    
    # ============================================================
    # 好大夫在线爬虫
    # ============================================================
    
    def search_doctors_haodf(self, disease: str, city: str = "") -> List[Doctor]:
        """在好大夫搜索医生"""
        doctors = []
        
        try:
            # 搜索医生
            search_url = f"{self.haodf_base}/search"
            params = {
                "q": disease,
                "type": "doctor",
                "page": 1
            }
            
            if city:
                params["p"] = city
            
            response = requests.get(
                search_url,
                params=params,
                headers=self.haodf_headers,
                timeout=15
            )
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")
                
                # 解析医生列表
                doctor_items = soup.select(".doctor-item, .search-doctor-item")
                
                for item in doctor_items[:10]:  # 限制10个结果
                    try:
                        doctor = self._parse_haodf_doctor(item)
                        if doctor:
                            doctors.append(doctor)
                    except Exception as e:
                        print(f"解析医生失败: {e}")
                        continue
            
            self._random_delay()
            
        except Exception as e:
            print(f"好大夫搜索失败: {e}")
        
        return doctors
    
    def _parse_haodf_doctor(self, item) -> Optional[Doctor]:
        """解析好大夫医生信息"""
        try:
            # 姓名
            name_elem = item.select_one(".doctor-name a, .name a")
            name = name_elem.get_text(strip=True) if name_elem else ""
            
            # 职称
            title_elem = item.select_one(".doctor-title, .title")
            title = title_elem.get_text(strip=True) if title_elem else ""
            
            # 医院
            hospital_elem = item.select_one(".doctor-hospital a, .hospital a")
            hospital = hospital_elem.get_text(strip=True) if hospital_elem else ""
            
            # 科室
            dept_elem = item.select_one(".doctor-department, .department")
            department = dept_elem.get_text(strip=True) if dept_elem else ""
            
            # 擅长
            good_at_elem = item.select_one(".doctor-good-at, .good-at")
            good_at = good_at_elem.get_text(strip=True) if good_at_elem else ""
            
            # 评分
            rating_elem = item.select_one(".doctor-rating, .rating")
            rating_text = rating_elem.get_text(strip=True) if rating_elem else "0"
            rating = float(re.search(r"[\d.]+", rating_text).group()) if re.search(r"[\d.]+", rating_text) else 0
            
            # 接诊量
            count_elem = item.select_one(".doctor-count, .consultation-count")
            count_text = count_elem.get_text(strip=True) if count_elem else "0"
            count_match = re.search(r"(\d+)", count_text.replace(",", ""))
            consultation_count = int(count_match.group(1)) if count_match else 0
            
            # 链接
            link_elem = item.select_one("a[href]")
            url = link_elem.get("href", "") if link_elem else ""
            if url and not url.startswith("http"):
                url = self.haodf_base + url
            
            # 头像
            avatar_elem = item.select_one("img")
            avatar = avatar_elem.get("src", "") if avatar_elem else ""
            
            if name:
                return Doctor(
                    name=name,
                    title=title,
                    hospital=hospital,
                    department=department,
                    specialty=good_at,
                    rating=rating,
                    consultation_count=consultation_count,
                    good_at=good_at,
                    introduction="",
                    avatar=avatar,
                    source="好大夫在线",
                    url=url
                )
        except Exception as e:
            print(f"解析医生详情失败: {e}")
        
        return None
    
    def get_hospital_detail_haodf(self, hospital_name: str) -> Optional[HospitalDetail]:
        """获取医院详细信息"""
        try:
            search_url = f"{self.haodf_base}/search"
            params = {
                "q": hospital_name,
                "type": "hospital"
            }
            
            response = requests.get(
                search_url,
                params=params,
                headers=self.haodf_headers,
                timeout=15
            )
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")
                
                # 解析医院信息
                hospital_item = soup.select_one(".hospital-item, .search-hospital-item")
                
                if hospital_item:
                    name_elem = hospital_item.select_one(".hospital-name a, .name a")
                    name = name_elem.get_text(strip=True) if name_elem else hospital_name
                    
                    level_elem = hospital_item.select_one(".hospital-level, .level")
                    level = level_elem.get_text(strip=True) if level_elem else ""
                    
                    address_elem = hospital_item.select_one(".hospital-address, .address")
                    address = address_elem.get_text(strip=True) if address_elem else ""
                    
                    phone_elem = hospital_item.select_one(".hospital-phone, .phone")
                    phone = phone_elem.get_text(strip=True) if phone_elem else ""
                    
                    link_elem = hospital_item.select_one("a[href]")
                    url = link_elem.get("href", "") if link_elem else ""
                    if url and not url.startswith("http"):
                        url = self.haodf_base + url
                    
                    return HospitalDetail(
                        name=name,
                        level=level,
                        address=address,
                        phone=phone,
                        website="",
                        departments=[],
                        specialty_departments=[],
                        rating=0,
                        source="好大夫在线",
                        url=url
                    )
            
            self._random_delay()
            
        except Exception as e:
            print(f"获取医院详情失败: {e}")
        
        return None
    
    # ============================================================
    # 微医爬虫
    # ============================================================
    
    def search_doctors_guahao(self, disease: str, city: str = "") -> List[Doctor]:
        """在微医搜索医生"""
        doctors = []
        
        try:
            search_url = f"{self.guahao_base}/search"
            params = {
                "keyword": disease,
                "type": "expert"
            }
            
            if city:
                params["city"] = city
            
            response = requests.get(
                search_url,
                params=params,
                headers=self.guahao_headers,
                timeout=15
            )
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")
                
                # 解析医生列表
                doctor_items = soup.select(".expert-card, .doctor-card")
                
                for item in doctor_items[:10]:
                    try:
                        doctor = self._parse_guahao_doctor(item)
                        if doctor:
                            doctors.append(doctor)
                    except Exception as e:
                        print(f"解析微医医生失败: {e}")
                        continue
            
            self._random_delay()
            
        except Exception as e:
            print(f"微医搜索失败: {e}")
        
        return doctors
    
    def _parse_guahao_doctor(self, item) -> Optional[Doctor]:
        """解析微医医生信息"""
        try:
            name_elem = item.select_one(".doctor-name, .name")
            name = name_elem.get_text(strip=True) if name_elem else ""
            
            title_elem = item.select_one(".doctor-title, .title")
            title = title_elem.get_text(strip=True) if title_elem else ""
            
            hospital_elem = item.select_one(".hospital-name, .hospital")
            hospital = hospital_elem.get_text(strip=True) if hospital_elem else ""
            
            dept_elem = item.select_one(".department-name, .department")
            department = dept_elem.get_text(strip=True) if dept_elem else ""
            
            good_at_elem = item.select_one(".good-at, .specialty")
            good_at = good_at_elem.get_text(strip=True) if good_at_elem else ""
            
            link_elem = item.select_one("a[href]")
            url = link_elem.get("href", "") if link_elem else ""
            if url and not url.startswith("http"):
                url = self.guahao_base + url
            
            avatar_elem = item.select_one("img")
            avatar = avatar_elem.get("src", "") if avatar_elem else ""
            
            if name:
                return Doctor(
                    name=name,
                    title=title,
                    hospital=hospital,
                    department=department,
                    specialty=good_at,
                    rating=0,
                    consultation_count=0,
                    good_at=good_at,
                    introduction="",
                    avatar=avatar,
                    source="微医",
                    url=url
                )
        except Exception as e:
            print(f"解析微医医生失败: {e}")
        
        return None
    
    # ============================================================
    # 综合搜索
    # ============================================================
    
    def search_specialists(self, disease: str, city: str = "", limit: int = 20) -> List[Doctor]:
        """综合搜索专科医生（多平台）"""
        all_doctors = []
        
        # 好大夫搜索
        print(f"正在搜索好大夫: {disease}")
        haodf_doctors = self.search_doctors_haodf(disease, city)
        all_doctors.extend(haodf_doctors)
        
        # 微医搜索
        print(f"正在搜索微医: {disease}")
        guahao_doctors = self.search_doctors_guahao(disease, city)
        all_doctors.extend(guahao_doctors)
        
        # 去重（按姓名+医院）
        seen = set()
        unique_doctors = []
        for doctor in all_doctors:
            key = f"{doctor.name}_{doctor.hospital}"
            if key not in seen:
                seen.add(key)
                unique_doctors.append(doctor)
        
        # 按评分和接诊量排序
        unique_doctors.sort(key=lambda x: (x.rating, x.consultation_count), reverse=True)
        
        return unique_doctors[:limit]
    
    def get_hospital_info(self, hospital_name: str) -> Optional[HospitalDetail]:
        """获取医院信息"""
        # 好大夫
        return self.get_hospital_detail_haodf(hospital_name)

# API接口
from fastapi import APIRouter, Query
from typing import Optional

router = APIRouter(prefix="/api/v1/crawler", tags=["爬虫服务"])

crawler = HospitalExpertCrawler()

@router.get("/doctors/search")
async def search_doctors(
    disease: str = Query(..., description="疾病名称"),
    city: str = Query("", description="城市名称"),
    limit: int = Query(20, description="返回数量限制")
):
    """搜索专科医生"""
    doctors = crawler.search_specialists(disease, city, limit)
    return {
        "disease": disease,
        "city": city,
        "total": len(doctors),
        "doctors": [
            {
                "name": d.name,
                "title": d.title,
                "hospital": d.hospital,
                "department": d.department,
                "specialty": d.specialty,
                "rating": d.rating,
                "consultation_count": d.consultation_count,
                "good_at": d.good_at,
                "source": d.source,
                "url": d.url,
                "avatar": d.avatar
            }
            for d in doctors
        ]
    }

@router.get("/hospitals/{name}")
async def get_hospital_info(name: str):
    """获取医院信息"""
    hospital = crawler.get_hospital_info(name)
    if hospital:
        return {
            "name": hospital.name,
            "level": hospital.level,
            "address": hospital.address,
            "phone": hospital.phone,
            "website": hospital.website,
            "departments": hospital.departments,
            "specialty_departments": hospital.specialty_departments,
            "rating": hospital.rating,
            "source": hospital.source,
            "url": hospital.url
        }
    return {"error": "未找到医院信息"}

if __name__ == "__main__":
    # 测试
    crawler = HospitalExpertCrawler()
    
    # 搜索戈谢病专家
    print("搜索戈谢病专家...")
    doctors = crawler.search_specialists("戈谢病", "北京")
    
    print(f"\n找到 {len(doctors)} 位专家:")
    for d in doctors[:5]:
        print(f"  - {d.name} ({d.title}) - {d.hospital}")
        print(f"    擅长: {d.specialty[:50]}...")
        print(f"    来源: {d.source}")
