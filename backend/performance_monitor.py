"""
MediChat-RD API性能监控模块
集成Prometheus监控，实时跟踪API性能
"""

import time
import logging
from typing import Dict, List
from datetime import datetime
from functools import wraps
from collections import defaultdict, deque

logger = logging.getLogger(__name__)

class PerformanceMonitor:
    """API性能监控器"""
    
    def __init__(self):
        self.metrics = {
            "requests_total": 0,
            "requests_success": 0,
            "requests_failed": 0,
            "response_times": deque(maxlen=1000),  # 保存最近1000个响应时间
            "endpoint_stats": defaultdict(lambda: {
                "count": 0,
                "total_time": 0,
                "avg_time": 0,
                "max_time": 0,
                "min_time": float('inf')
            }),
            "active_requests": 0,
            "start_time": datetime.now()
        }
        
        # 性能阈值
        self.thresholds = {
            "response_time_warning": 2000,  # 2秒
            "response_time_critical": 5000,  # 5秒
            "error_rate_warning": 0.05,  # 5%
            "error_rate_critical": 0.10   # 10%
        }
    
    def record_request(self, endpoint: str, method: str, status_code: int, response_time: float):
        """记录请求数据"""
        self.metrics["requests_total"] += 1
        
        if 200 <= status_code < 400:
            self.metrics["requests_success"] += 1
        else:
            self.metrics["requests_failed"] += 1
        
        # 记录响应时间
        self.metrics["response_times"].append(response_time)
        
        # 更新端点统计
        key = f"{method} {endpoint}"
        stats = self.metrics["endpoint_stats"][key]
        stats["count"] += 1
        stats["total_time"] += response_time
        stats["avg_time"] = stats["total_time"] / stats["count"]
        stats["max_time"] = max(stats["max_time"], response_time)
        stats["min_time"] = min(stats["min_time"], response_time)
        
        # 检查性能阈值
        self._check_thresholds(endpoint, response_time)
    
    def _check_thresholds(self, endpoint: str, response_time: float):
        """检查性能阈值"""
        if response_time > self.thresholds["response_time_critical"]:
            logger.critical(f"🚨 API性能严重警告: {endpoint} 响应时间 {response_time:.2f}ms")
        elif response_time > self.thresholds["response_time_warning"]:
            logger.warning(f"⚠️  API性能警告: {endpoint} 响应时间 {response_time:.2f}ms")
    
    def get_performance_summary(self) -> Dict:
        """获取性能摘要"""
        if not self.metrics["response_times"]:
            return {"error": "No data available"}
        
        response_times = list(self.metrics["response_times"])
        total_requests = self.metrics["requests_total"]
        
        # 计算百分位数
        sorted_times = sorted(response_times)
        p50 = sorted_times[int(len(sorted_times) * 0.5)]
        p95 = sorted_times[int(len(sorted_times) * 0.95)]
        p99 = sorted_times[int(len(sorted_times) * 0.99)]
        
        return {
            "timestamp": datetime.now().isoformat(),
            "uptime_seconds": (datetime.now() - self.metrics["start_time"]).total_seconds(),
            "requests": {
                "total": total_requests,
                "success": self.metrics["requests_success"],
                "failed": self.metrics["requests_failed"],
                "success_rate": self.metrics["requests_success"] / total_requests if total_requests > 0 else 0,
                "error_rate": self.metrics["requests_failed"] / total_requests if total_requests > 0 else 0
            },
            "response_times": {
                "avg_ms": sum(response_times) / len(response_times),
                "min_ms": min(response_times),
                "max_ms": max(response_times),
                "p50_ms": p50,
                "p95_ms": p95,
                "p99_ms": p99
            },
            "active_requests": self.metrics["active_requests"],
            "top_endpoints": self._get_top_endpoints()
        }
    
    def _get_top_endpoints(self, limit: int = 10) -> List[Dict]:
        """获取最繁忙的端点"""
        endpoints = []
        for endpoint, stats in self.metrics["endpoint_stats"].items():
            endpoints.append({
                "endpoint": endpoint,
                "count": stats["count"],
                "avg_time_ms": stats["avg_time"],
                "max_time_ms": stats["max_time"]
            })
        
        return sorted(endpoints, key=lambda x: x["count"], reverse=True)[:limit]
    
    def get_alerts(self) -> List[Dict]:
        """获取性能告警"""
        alerts = []
        summary = self.get_performance_summary()
        
        if "error" in summary:
            return alerts
        
        # 检查错误率
        error_rate = summary["requests"]["error_rate"]
        if error_rate > self.thresholds["error_rate_critical"]:
            alerts.append({
                "level": "critical",
                "message": f"错误率过高: {error_rate:.2%}",
                "threshold": f"{self.thresholds['error_rate_critical']:.2%}"
            })
        elif error_rate > self.thresholds["error_rate_warning"]:
            alerts.append({
                "level": "warning",
                "message": f"错误率偏高: {error_rate:.2%}",
                "threshold": f"{self.thresholds['error_rate_warning']:.2%}"
            })
        
        # 检查响应时间
        p95_time = summary["response_times"]["p95_ms"]
        if p95_time > self.thresholds["response_time_critical"]:
            alerts.append({
                "level": "critical",
                "message": f"P95响应时间过长: {p95_time:.2f}ms",
                "threshold": f"{self.thresholds['response_time_critical']}ms"
            })
        elif p95_time > self.thresholds["response_time_warning"]:
            alerts.append({
                "level": "warning",
                "message": f"P95响应时间偏长: {p95_time:.2f}ms",
                "threshold": f"{self.thresholds['response_time_warning']}ms"
            })
        
        return alerts
    
    def reset_metrics(self):
        """重置指标"""
        self.metrics = {
            "requests_total": 0,
            "requests_success": 0,
            "requests_failed": 0,
            "response_times": deque(maxlen=1000),
            "endpoint_stats": defaultdict(lambda: {
                "count": 0,
                "total_time": 0,
                "avg_time": 0,
                "max_time": 0,
                "min_time": float('inf')
            }),
            "active_requests": 0,
            "start_time": datetime.now()
        }

# 全局监控实例
performance_monitor = PerformanceMonitor()

def monitor_performance(endpoint: str = None):
    """性能监控装饰器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            performance_monitor.metrics["active_requests"] += 1
            
            try:
                result = await func(*args, **kwargs)
                status_code = 200
                return result
            except Exception as e:
                status_code = 500
                raise
            finally:
                end_time = time.time()
                response_time = (end_time - start_time) * 1000  # 转换为毫秒
                
                # 获取端点信息
                actual_endpoint = endpoint or func.__name__
                method = "POST" if "post" in func.__name__.lower() else "GET"
                
                performance_monitor.record_request(
                    endpoint=actual_endpoint,
                    method=method,
                    status_code=status_code,
                    response_time=response_time
                )
                
                performance_monitor.metrics["active_requests"] -= 1
        
        return wrapper
    return decorator

# FastAPI集成
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

def setup_performance_monitoring(app: FastAPI):
    """设置FastAPI性能监控"""
    
    @app.middleware("http")
    async def performance_middleware(request: Request, call_next):
        start_time = time.time()
        performance_monitor.metrics["active_requests"] += 1
        
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        except Exception as e:
            status_code = 500
            raise
        finally:
            end_time = time.time()
            response_time = (end_time - start_time) * 1000
            
            performance_monitor.record_request(
                endpoint=request.url.path,
                method=request.method,
                status_code=status_code,
                response_time=response_time
            )
            
            performance_monitor.metrics["active_requests"] -= 1
    
    @app.get("/metrics/performance")
    async def get_performance_metrics():
        """获取性能指标"""
        return performance_monitor.get_performance_summary()
    
    @app.get("/metrics/alerts")
    async def get_performance_alerts():
        """获取性能告警"""
        return {"alerts": performance_monitor.get_alerts()}
    
    @app.post("/metrics/reset")
    async def reset_performance_metrics():
        """重置性能指标"""
        performance_monitor.reset_metrics()
        return {"message": "Performance metrics reset"}

# 使用示例
async def demo_performance_monitoring():
    """演示性能监控"""
    print("📊 MediChat-RD API性能监控演示")
    print("=" * 50)
    
    # 模拟一些API请求
    endpoints = [
        ("/api/v1/chat", "POST", 200, 150),
        ("/api/v1/knowledge/diseases", "GET", 200, 85),
        ("/api/v1/drug-repurposing", "POST", 200, 320),
        ("/api/v1/patient-locator", "GET", 200, 210),
        ("/api/v1/sessions", "GET", 200, 95),
        ("/api/v1/knowledge/diseases/Albinism", "GET", 200, 120),
        ("/api/v1/chat", "POST", 500, 450),  # 一个失败的请求
        ("/api/v1/drug-repurposing", "POST", 200, 280),
    ]
    
    print("\n📈 模拟API请求...")
    for endpoint, method, status, response_time in endpoints:
        performance_monitor.record_request(endpoint, method, status, response_time)
        print(f"  {method} {endpoint} - {status} ({response_time}ms)")
    
    # 获取性能摘要
    print("\n📊 性能摘要:")
    summary = performance_monitor.get_performance_summary()
    
    print(f"总请求数: {summary['requests']['total']}")
    print(f"成功率: {summary['requests']['success_rate']:.2%}")
    print(f"平均响应时间: {summary['response_times']['avg_ms']:.2f}ms")
    print(f"P95响应时间: {summary['response_times']['p95_ms']:.2f}ms")
    
    # 检查告警
    print("\n🚨 性能告警:")
    alerts = performance_monitor.get_alerts()
    if alerts:
        for alert in alerts:
            print(f"  {alert['level'].upper()}: {alert['message']}")
    else:
        print("  无告警")
    
    # 显示最繁忙的端点
    print("\n🔥 最繁忙的端点:")
    for endpoint in summary['top_endpoints'][:3]:
        print(f"  {endpoint['endpoint']}: {endpoint['count']}次, 平均{endpoint['avg_time_ms']:.2f}ms")

if __name__ == "__main__":
    import asyncio
    asyncio.run(demo_performance_monitoring())