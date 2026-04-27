"""
MediChat-RD Redis缓存管理模块
提供智能缓存策略，提升系统性能
"""

import asyncio
import json
import logging
import hashlib
from typing import Any, Optional, Dict, List
from datetime import datetime, timedelta
from functools import wraps

logger = logging.getLogger(__name__)

class RedisCacheManager:
    """Redis缓存管理器"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379", default_ttl: int = 3600):
        self.redis_url = redis_url
        self.default_ttl = default_ttl
        self.redis_client = None
        self.enabled = False
        
        # 缓存统计
        self.stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0,
            "errors": 0
        }
    
    async def connect(self):
        """连接Redis"""
        try:
            import redis.asyncio as redis
            self.redis_client = redis.from_url(self.redis_url)
            await self.redis_client.ping()
            self.enabled = True
            logger.info("✅ Redis连接成功")
        except Exception as e:
            logger.warning(f"⚠️  Redis连接失败: {e}，缓存功能禁用")
            self.enabled = False
    
    async def disconnect(self):
        """断开Redis连接"""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("🔌 Redis连接已断开")
    
    def _generate_cache_key(self, prefix: str, params: dict) -> str:
        """生成缓存键"""
        # 对参数进行排序和序列化，确保相同参数生成相同键
        param_str = json.dumps(params, sort_keys=True, default=str)
        hash_obj = hashlib.md5(param_str.encode())
        return f"{prefix}:{hash_obj.hexdigest()}"
    
    async def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        if not self.enabled:
            return None
        
        try:
            data = await self.redis_client.get(key)
            if data:
                self.stats["hits"] += 1
                return json.loads(data)
            else:
                self.stats["misses"] += 1
                return None
        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"缓存获取失败: {e}")
            return None
    
    async def set(self, key: str, data: Any, ttl: Optional[int] = None) -> bool:
        """设置缓存"""
        if not self.enabled:
            return False
        
        try:
            ttl = ttl or self.default_ttl
            serialized_data = json.dumps(data, default=str)
            await self.redis_client.setex(key, ttl, serialized_data)
            self.stats["sets"] += 1
            return True
        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"缓存设置失败: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """删除缓存"""
        if not self.enabled:
            return False
        
        try:
            await self.redis_client.delete(key)
            self.stats["deletes"] += 1
            return True
        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"缓存删除失败: {e}")
            return False
    
    async def get_cached_disease(self, disease_name: str) -> Optional[Dict]:
        """获取缓存的疾病信息"""
        key = self._generate_cache_key("disease", {"name": disease_name})
        return await self.get(key)
    
    async def cache_disease(self, disease_name: str, disease_data: Dict, ttl: int = 86400):
        """缓存疾病信息（24小时）"""
        key = self._generate_cache_key("disease", {"name": disease_name})
        return await self.set(key, disease_data, ttl)
    
    async def get_cached_drug_targets(self, drug_name: str) -> Optional[Dict]:
        """获取缓存的药物靶点"""
        key = self._generate_cache_key("drug_targets", {"drug": drug_name})
        return await self.get(key)
    
    async def cache_drug_targets(self, drug_name: str, targets_data: Dict, ttl: int = 43200):
        """缓存药物靶点（12小时）"""
        key = self._generate_cache_key("drug_targets", {"drug": drug_name})
        return await self.set(key, targets_data, ttl)
    
    async def get_cached_repurposing(self, drug_name: str, disease_name: str) -> Optional[Dict]:
        """获取缓存的药物重定位结果"""
        key = self._generate_cache_key("repurposing", {"drug": drug_name, "disease": disease_name})
        return await self.get(key)
    
    async def cache_repurposing(self, drug_name: str, disease_name: str, result: Dict, ttl: int = 7200):
        """缓存药物重定位结果（2小时）"""
        key = self._generate_cache_key("repurposing", {"drug": drug_name, "disease": disease_name})
        return await self.set(key, result, ttl)
    
    async def get_cached_pubmed(self, query: str, max_results: int = 10) -> Optional[List]:
        """获取缓存的PubMed结果"""
        key = self._generate_cache_key("pubmed", {"query": query, "max": max_results})
        return await self.get(key)
    
    async def cache_pubmed(self, query: str, max_results: int, results: List, ttl: int = 3600):
        """缓存PubMed结果（1小时）"""
        key = self._generate_cache_key("pubmed", {"query": query, "max": max_results})
        return await self.set(key, results, ttl)
    
    def get_cache_stats(self) -> Dict:
        """获取缓存统计"""
        total_requests = self.stats["hits"] + self.stats["misses"]
        hit_rate = self.stats["hits"] / total_requests if total_requests > 0 else 0
        
        return {
            "enabled": self.enabled,
            "hits": self.stats["hits"],
            "misses": self.stats["misses"],
            "sets": self.stats["sets"],
            "deletes": self.stats["deletes"],
            "errors": self.stats["errors"],
            "hit_rate": hit_rate,
            "total_requests": total_requests
        }

# 全局缓存实例
cache_manager = RedisCacheManager()

def cached(prefix: str, ttl: int = 3600):
    """缓存装饰器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 生成缓存键
            cache_key = cache_manager._generate_cache_key(prefix, kwargs)
            
            # 尝试从缓存获取
            cached_result = await cache_manager.get(cache_key)
            if cached_result is not None:
                logger.debug(f"🎯 缓存命中: {prefix}")
                return cached_result
            
            # 执行原函数
            result = await func(*args, **kwargs)
            
            # 缓存结果
            if result is not None:
                await cache_manager.set(cache_key, result, ttl)
                logger.debug(f"💾 缓存设置: {prefix}")
            
            return result
        return wrapper
    return decorator

# 使用示例
async def demo_cache_usage():
    """演示缓存使用"""
    print("📊 MediChat-RD Redis缓存演示")
    print("=" * 50)
    
    # 连接Redis
    await cache_manager.connect()
    
    # 测试疾病信息缓存
    print("\n🏥 测试疾病信息缓存...")
    disease_data = {
        "name": "Albinism",
        "category": "遗传性皮肤病",
        "symptoms": ["皮肤白皙", "头发浅色", "视力问题"],
        "treatment": "对症治疗"
    }
    
    # 设置缓存
    await cache_manager.cache_disease("Albinism", disease_data)
    print("✅ 疾病信息已缓存")
    
    # 获取缓存
    cached_disease = await cache_manager.get_cached_disease("Albinism")
    print(f"📖 缓存获取: {cached_disease['name']}")
    
    # 测试药物重定位缓存
    print("\n💊 测试药物重定位缓存...")
    repurposing_data = {
        "drug": "metformin",
        "disease": "Polycystic Ovary Syndrome",
        "confidence": 0.85,
        "targets": ["AMPK", "mTOR"]
    }
    
    await cache_manager.cache_repurposing("metformin", "Polycystic Ovary Syndrome", repurposing_data)
    print("✅ 药物重定位结果已缓存")
    
    cached_repurposing = await cache_manager.get_cached_repurposing("metformin", "Polycystic Ovary Syndrome")
    print(f"📖 缓存获取: {cached_repurposing['drug']} → {cached_repurposing['disease']}")
    
    # 显示缓存统计
    print("\n📊 缓存统计:")
    stats = cache_manager.get_cache_stats()
    print(f"命中率: {stats['hit_rate']:.2%}")
    print(f"命中次数: {stats['hits']}")
    print(f"未命中次数: {stats['misses']}")
    print(f"缓存设置: {stats['sets']}")
    
    # 断开连接
    await cache_manager.disconnect()

# FastAPI集成
from fastapi import FastAPI

def setup_cache_monitoring(app: FastAPI):
    """设置FastAPI缓存监控"""
    
    @app.get("/metrics/cache")
    async def get_cache_metrics():
        """获取缓存指标"""
        return cache_manager.get_cache_stats()
    
    @app.post("/cache/clear")
    async def clear_cache():
        """清空缓存"""
        if cache_manager.enabled:
            await cache_manager.redis_client.flushdb()
            return {"message": "Cache cleared"}
        else:
            return {"message": "Cache not enabled"}

if __name__ == "__main__":
    asyncio.run(demo_cache_usage())