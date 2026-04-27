"""
MediChat - HIPAA 合规模块
医疗数据安全与隐私保护
"""

import hashlib
import json
import uuid
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from functools import wraps
from enum import Enum
from pydantic import BaseModel


# ============================================================
# 常量定义
# ============================================================
class DataClassification(str, Enum):
    """数据分类级别"""
    PUBLIC = "public"           # 公开数据
    INTERNAL = "internal"       # 内部数据
    CONFIDENTIAL = "confidential"  # 机密数据
    PHI = "phi"                 # 受保护健康信息 (Protected Health Information)


class AuditAction(str, Enum):
    """审计操作类型"""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    EXPORT = "export"
    LOGIN = "login"
    LOGOUT = "logout"
    ACCESS_DENIED = "access_denied"


# ============================================================
# 数据脱敏
# ============================================================
class DataMasker:
    """数据脱敏处理器"""
    
    @staticmethod
    def mask_name(name: str) -> str:
        """姓名脱敏：保留姓，名用*代替"""
        if not name or len(name) < 2:
            return "***"
        return name[0] + "*" * (len(name) - 1)
    
    @staticmethod
    def mask_phone(phone: str) -> str:
        """手机号脱敏：保留前3后4"""
        if not phone or len(phone) < 7:
            return "***"
        return phone[:3] + "****" + phone[-4:]
    
    @staticmethod
    def mask_id_card(id_card: str) -> str:
        """身份证脱敏：保留前3后4"""
        if not id_card or len(id_card) < 11:
            return "***"
        return id_card[:3] + "***********" + id_card[-4:]
    
    @staticmethod
    def mask_email(email: str) -> str:
        """邮箱脱敏"""
        if not email or "@" not in email:
            return "***"
        local, domain = email.split("@")
        if len(local) <= 2:
            return "***@" + domain
        return local[0] + "***" + local[-1] + "@" + domain
    
    @staticmethod
    def mask_medical_record(record: str) -> str:
        """病历脱敏：保留结构，隐藏敏感内容"""
        if not record:
            return "***"
        # 保留前20字符，其余用*代替
        if len(record) <= 20:
            return record[:5] + "***"
        return record[:20] + "... [已脱敏]"


# ============================================================
# 审计日志
# ============================================================
class AuditLog(BaseModel):
    """审计日志模型"""
    log_id: str
    timestamp: datetime
    user_id: Optional[str]
    action: AuditAction
    resource_type: str
    resource_id: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    details: Optional[Dict[str, Any]]
    success: bool
    error_message: Optional[str]


class AuditLogger:
    """HIPAA审计日志系统"""
    
    def __init__(self, log_file: str = "logs/audit.log"):
        self.log_file = log_file
        self.logs: List[AuditLog] = []
    
    def log(
        self,
        action: AuditAction,
        resource_type: str,
        user_id: Optional[str] = None,
        resource_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        success: bool = True,
        error_message: Optional[str] = None
    ) -> AuditLog:
        """记录审计日志"""
        audit_log = AuditLog(
            log_id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details=self._sanitize_details(details),
            success=success,
            error_message=error_message
        )
        
        self.logs.append(audit_log)
        self._write_to_file(audit_log)
        return audit_log
    
    def _sanitize_details(self, details: Optional[Dict]) -> Optional[Dict]:
        """脱敏日志详情中的敏感信息"""
        if not details:
            return None
        
        sanitized = {}
        sensitive_keys = ['password', 'token', 'api_key', 'ssn', 'id_card', 'phone']
        
        for key, value in details.items():
            if any(s in key.lower() for s in sensitive_keys):
                sanitized[key] = "***REDACTED***"
            elif isinstance(value, str) and len(value) > 100:
                sanitized[key] = value[:100] + "...[TRUNCATED]"
            else:
                sanitized[key] = value
        
        return sanitized
    
    def _write_to_file(self, audit_log: AuditLog):
        """写入审计日志文件"""
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(audit_log.model_dump(), default=str) + "\n")
    
    def get_user_logs(
        self,
        user_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[AuditLog]:
        """获取用户审计日志"""
        return [
            log for log in self.logs
            if log.user_id == user_id
            and (not start_time or log.timestamp >= start_time)
            and (not end_time or log.timestamp <= end_time)
        ]


# ============================================================
# 数据加密
# ============================================================
class DataEncryptor:
    """数据加密器"""
    
    def __init__(self, key: Optional[str] = None):
        # 注意：生产环境应使用专业的加密库如cryptography
        self.key = key or os.getenv("ENCRYPTION_KEY", "default_key_change_me")
    
    def hash_sensitive_data(self, data: str) -> str:
        """敏感数据哈希（不可逆）"""
        return hashlib.sha256(f"{self.key}{data}".encode()).hexdigest()
    
    def encrypt_phi(self, phi_data: str) -> str:
        """
        加密PHI数据
        生产环境应使用AES-256等强加密
        """
        # 这里简化处理，实际应使用专业加密库
        import base64
        encoded = base64.b64encode(phi_data.encode()).decode()
        return f"ENC:{encoded}"
    
    def decrypt_phi(self, encrypted_data: str) -> str:
        """解密PHI数据"""
        import base64
        if not encrypted_data.startswith("ENC:"):
            raise ValueError("Invalid encrypted data format")
        encoded = encrypted_data[4:]
        return base64.b64decode(encoded.encode()).decode()


# ============================================================
# 访问控制
# ============================================================
class AccessControl:
    """HIPAA访问控制"""
    
    def __init__(self):
        self.permissions = {
            "admin": ["read", "write", "delete", "export", "manage_users"],
            "doctor": ["read", "write", "export"],
            "nurse": ["read", "write"],
            "patient": ["read_own"],
            "viewer": ["read"]
        }
    
    def check_permission(
        self,
        user_role: str,
        required_permission: str,
        resource_owner_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> bool:
        """检查用户权限"""
        # 患者只能访问自己的数据
        if user_role == "patient" and required_permission == "read_own":
            return resource_owner_id == user_id
        
        user_permissions = self.permissions.get(user_role, [])
        return required_permission in user_permissions
    
    def enforce_minimum_necessary(
        self,
        user_role: str,
        data_fields: List[str]
    ) -> List[str]:
        """
        最小必要原则：只返回用户角色需要的字段
        """
        role_fields = {
            "admin": data_fields,  # 管理员可以看全部
            "doctor": ["name", "age", "gender", "medical_history", "symptoms", "diagnosis"],
            "nurse": ["name", "age", "gender", "symptoms", "vitals"],
            "patient": ["name", "age", "gender", "my_records"],
            "viewer": ["name", "age", "gender"]
        }
        
        allowed = role_fields.get(user_role, [])
        return [f for f in data_fields if f in allowed]


# ============================================================
# 合规检查器
# ============================================================
class ComplianceChecker:
    """HIPAA合规检查器"""
    
    def __init__(self):
        self.audit_logger = AuditLogger()
        self.encryptor = DataEncryptor()
        self.access_control = AccessControl()
    
    def check_data_retention(self, created_at: datetime) -> bool:
        """检查数据保留期限（6年）"""
        retention_period = timedelta(days=365 * 6)
        return datetime.now() - created_at < retention_period
    
    def validate_consent(self, patient_id: str, consent_type: str) -> bool:
        """
        验证患者同意
        生产环境应查询数据库
        """
        # 模拟：总是返回True
        return True
    
    def generate_breach_report(
        self,
        breach_type: str,
        affected_records: int,
        description: str
    ) -> Dict[str, Any]:
        """生成数据泄露报告"""
        return {
            "report_id": str(uuid.uuid4()),
            "timestamp": datetime.now().isoformat(),
            "breach_type": breach_type,
            "affected_records": affected_records,
            "description": description,
            "status": "reported",
            "notification_required": affected_records >= 500,  # HIPAA要求
            "notification_deadline": (datetime.now() + timedelta(days=60)).isoformat()
        }


# ============================================================
# 装饰器：自动审计日志
# ============================================================
def audit_log(action: AuditAction, resource_type: str):
    """装饰器：自动记录审计日志"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            audit = AuditLogger()
            try:
                result = await func(*args, **kwargs)
                audit.log(
                    action=action,
                    resource_type=resource_type,
                    success=True
                )
                return result
            except Exception as e:
                audit.log(
                    action=action,
                    resource_type=resource_type,
                    success=False,
                    error_message=str(e)
                )
                raise
        return wrapper
    return decorator


# ============================================================
# 使用示例
# ============================================================
if __name__ == "__main__":
    # 数据脱敏测试
    masker = DataMasker()
    print("=== 数据脱敏测试 ===")
    print(f"姓名: 张三 -> {masker.mask_name('张三')}")
    print(f"手机: 13812345678 -> {masker.mask_phone('13812345678')}")
    print(f"邮箱: zhangsan@example.com -> {masker.mask_email('zhangsan@example.com')}")
    
    # 审计日志测试
    audit = AuditLogger()
    audit.log(
        action=AuditAction.READ,
        resource_type="patient_record",
        user_id="doctor_001",
        resource_id="patient_123"
    )
    print("\n=== 审计日志已记录 ===")
    
    # 合规检查
    checker = ComplianceChecker()
    print(f"\n=== 数据保留检查 ===")
    print(f"1年前数据: {checker.check_data_retention(datetime.now() - timedelta(days=365))}")
    print(f"7年前数据: {checker.check_data_retention(datetime.now() - timedelta(days=365*7))}")
