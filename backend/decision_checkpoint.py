"""
MediChat-RD 决策检查点/回滚机制
为关键诊断和API操作添加：
1. 操作前预览（Preview-Before-Execute）
2. 多级降级策略（Graceful Degradation）
3. 用户确认门控（User Confirmation Gates）
4. 回滚能力（Rollback Support）
"""

import time
import uuid
import copy
import logging
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


# ============================================================
# 枚举 & 数据结构
# ============================================================

class CheckpointStatus(Enum):
    """检查点状态"""
    PENDING = "pending"           # 等待确认
    APPROVED = "approved"         # 用户已确认
    REJECTED = "rejected"         # 用户拒绝
    AUTO_APPROVED = "auto_approved"  # 自动通过（低风险）
    FAILED = "failed"             # 执行失败
    ROLLED_BACK = "rolled_back"   # 已回滚


class RiskLevel(Enum):
    """操作风险等级"""
    LOW = "low"           # 信息查询，无需确认
    MEDIUM = "medium"     # 诊断建议，需预览
    HIGH = "high"         # 用药推荐，需确认
    CRITICAL = "critical" # 紧急处置，需强确认


@dataclass
class DecisionCheckpoint:
    """决策检查点"""
    checkpoint_id: str
    name: str
    description: str
    risk_level: RiskLevel
    status: CheckpointStatus = CheckpointStatus.PENDING
    preview_data: Optional[Dict] = None
    execution_result: Optional[Any] = None
    rollback_data: Optional[Dict] = None
    fallback_chain: List[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    resolved_at: Optional[float] = None
    metadata: Dict = field(default_factory=dict)


@dataclass
class FallbackStrategy:
    """降级策略"""
    name: str
    priority: int  # 越小越优先
    handler: Callable
    description: str


# ============================================================
# 决策检查点管理器
# ============================================================

class DecisionCheckpointManager:
    """
    决策检查点管理器
    管理操作前预览、用户确认、降级策略和回滚
    """

    def __init__(self):
        self._checkpoints: Dict[str, DecisionCheckpoint] = {}
        self._fallback_registry: Dict[str, List[FallbackStrategy]] = {}
        self._snapshots: Dict[str, Dict] = {}  # 回滚快照

    # ---- 检查点生命周期 ----

    def create_checkpoint(
        self,
        name: str,
        description: str,
        risk_level: RiskLevel,
        preview_data: Optional[Dict] = None,
        metadata: Optional[Dict] = None
    ) -> DecisionCheckpoint:
        """创建决策检查点"""
        cp = DecisionCheckpoint(
            checkpoint_id=str(uuid.uuid4())[:8],
            name=name,
            description=description,
            risk_level=risk_level,
            preview_data=preview_data or {},
            metadata=metadata or {}
        )

        # 低风险操作自动通过
        if risk_level == RiskLevel.LOW:
            cp.status = CheckpointStatus.AUTO_APPROVED

        self._checkpoints[cp.checkpoint_id] = cp
        logger.info(f"创建检查点 [{cp.checkpoint_id}] {name} (风险: {risk_level.value}, 状态: {cp.status.value})")
        return cp

    def approve(self, checkpoint_id: str) -> DecisionCheckpoint:
        """用户确认检查点"""
        cp = self._get_checkpoint(checkpoint_id)
        if cp.status != CheckpointStatus.PENDING:
            raise ValueError(f"检查点 {checkpoint_id} 状态为 {cp.status.value}，无法确认")
        cp.status = CheckpointStatus.APPROVED
        cp.resolved_at = time.time()
        logger.info(f"检查点 [{checkpoint_id}] 已确认")
        return cp

    def reject(self, checkpoint_id: str) -> DecisionCheckpoint:
        """用户拒绝检查点"""
        cp = self._get_checkpoint(checkpoint_id)
        cp.status = CheckpointStatus.REJECTED
        cp.resolved_at = time.time()
        logger.info(f"检查点 [{checkpoint_id}] 已拒绝")
        return cp

    def rollback(self, checkpoint_id: str) -> bool:
        """回滚检查点关联的操作"""
        cp = self._get_checkpoint(checkpoint_id)
        if checkpoint_id in self._snapshots:
            cp.rollback_data = self._snapshots[checkpoint_id]
            cp.status = CheckpointStatus.ROLLED_BACK
            logger.info(f"检查点 [{checkpoint_id}] 已回滚")
            return True
        logger.warning(f"检查点 [{checkpoint_id}] 无可回滚数据")
        return False

    # ---- 操作前预览 ----

    def preview_operation(
        self,
        operation_name: str,
        params: Dict,
        executor: Callable,
        risk_level: RiskLevel = RiskLevel.MEDIUM,
        description: str = ""
    ) -> Tuple[DecisionCheckpoint, Optional[Dict]]:
        """
        操作前预览模式：
        1. 生成预览数据（不执行）
        2. 创建检查点
        3. 等待确认后才真正执行

        返回 (检查点, 预览结果)
        """
        # 生成预览
        preview = self._generate_preview(operation_name, params)

        cp = self.create_checkpoint(
            name=f"preview_{operation_name}",
            description=description or f"操作 '{operation_name}' 执行前预览",
            risk_level=risk_level,
            preview_data=preview,
            metadata={"params": params, "operation": operation_name}
        )

        # 低风险直接执行
        if risk_level == RiskLevel.LOW:
            return self._execute_with_rollback(cp, executor, params)

        return cp, preview

    def _generate_preview(self, operation_name: str, params: Dict) -> Dict:
        """生成操作预览"""
        previews = {
            "chat_diagnosis": {
                "action": "将调用MIMO模型生成诊断建议",
                "input_summary": f"患者消息: {params.get('message', '')[:100]}...",
                "will_do": [
                    "分析患者症状描述",
                    "生成初步诊断建议",
                    "推荐就诊科室"
                ],
                "wont_do": [
                    "不会开具处方",
                    "不会替代医生诊断",
                    "不会存储个人信息"
                ]
            },
            "drug_repurposing": {
                "action": f"评估药物 {params.get('drug_name', '?')} 对 {params.get('disease_name', '?')} 的重定位潜力",
                "will_do": [
                    "查询OpenTargets药物/疾病实体",
                    "分析靶点重叠",
                    "检索PubMed文献",
                    "生成证据评估报告"
                ],
                "estimated_time": "约30-60秒",
                "data_sources": ["OpenTargets", "PubMed", "ChEMBL"]
            },
            "rare_disease_diagnose": {
                "action": "根据症状进行罕见病筛查",
                "input_symptoms": params.get("symptoms", []),
                "will_do": [
                    "匹配罕见病数据库",
                    "计算置信度评分",
                    "生成鉴别诊断列表"
                ],
                "disclaimer": "⚠️ 结果仅供参考，不替代专业医生诊断"
            },
            "gene_analysis": {
                "action": f"分析基因 {params.get('gene_name', '?')} 变异",
                "will_do": [
                    "查询基因-疾病关联",
                    "检索相关罕见病",
                    "提供遗传咨询建议"
                ],
                "disclaimer": "⚠️ 基因分析需结合临床表现综合判断"
            }
        }
        return previews.get(operation_name, {
            "action": operation_name,
            "params": params,
            "note": "未知操作类型，将直接执行"
        })

    # ---- 降级策略 ----

    def register_fallback(self, operation: str, strategy: FallbackStrategy):
        """注册降级策略"""
        if operation not in self._fallback_registry:
            self._fallback_registry[operation] = []
        self._fallback_registry[operation].append(strategy)
        self._fallback_registry[operation].sort(key=lambda s: s.priority)

    def execute_with_fallback(
        self,
        operation: str,
        primary_executor: Callable,
        params: Dict,
        checkpoint: Optional[DecisionCheckpoint] = None
    ) -> Tuple[Any, str]:
        """
        带降级策略的执行：
        1. 尝试主执行器
        2. 失败后按优先级尝试降级策略
        3. 返回 (结果, 使用的策略名)
        """
        # 尝试主执行器
        try:
            result = primary_executor(**params)
            if checkpoint:
                checkpoint.execution_result = result
                checkpoint.status = CheckpointStatus.APPROVED
            return result, "primary"
        except Exception as e:
            logger.warning(f"主执行器失败 [{operation}]: {e}")

        # 尝试降级策略
        strategies = self._fallback_registry.get(operation, [])
        for strategy in strategies:
            try:
                logger.info(f"尝试降级策略: {strategy.name}")
                result = strategy.handler(**params)
                if checkpoint:
                    checkpoint.execution_result = result
                    checkpoint.fallback_chain.append(strategy.name)
                return result, strategy.name
            except Exception as e:
                logger.warning(f"降级策略 {strategy.name} 失败: {e}")
                if checkpoint:
                    checkpoint.fallback_chain.append(f"{strategy.name}:failed")

        # 全部失败
        error_result = {
            "error": True,
            "message": f"所有执行策略均失败 (操作: {operation})",
            "suggestions": [
                "请检查网络连接",
                "请稍后重试",
                "如问题持续请联系技术支持"
            ]
        }
        if checkpoint:
            checkpoint.status = CheckpointStatus.FAILED
            checkpoint.execution_result = error_result
        return error_result, "all_failed"

    # ---- 回滚支持 ----

    def take_snapshot(self, checkpoint_id: str, data: Dict):
        """为检查点创建回滚快照"""
        self._snapshots[checkpoint_id] = copy.deepcopy(data)
        logger.debug(f"检查点 [{checkpoint_id}] 快照已创建")

    def _execute_with_rollback(
        self,
        cp: DecisionCheckpoint,
        executor: Callable,
        params: Dict
    ) -> Tuple[DecisionCheckpoint, Optional[Dict]]:
        """执行并支持回滚"""
        self.take_snapshot(cp.checkpoint_id, {"params": params, "status": "before_execution"})
        try:
            result = executor(**params)
            cp.execution_result = result
            cp.status = CheckpointStatus.APPROVED
            cp.resolved_at = time.time()
            return cp, result
        except Exception as e:
            cp.status = CheckpointStatus.FAILED
            cp.execution_result = {"error": str(e)}
            logger.error(f"检查点 [{cp.checkpoint_id}] 执行失败: {e}")
            return cp, None

    # ---- 工具方法 ----

    def _get_checkpoint(self, checkpoint_id: str) -> DecisionCheckpoint:
        if checkpoint_id not in self._checkpoints:
            raise ValueError(f"检查点 {checkpoint_id} 不存在")
        return self._checkpoints[checkpoint_id]

    def get_pending_checkpoints(self) -> List[DecisionCheckpoint]:
        """获取所有待确认的检查点"""
        return [cp for cp in self._checkpoints.values() if cp.status == CheckpointStatus.PENDING]

    def get_checkpoint_summary(self) -> Dict:
        """获取检查点摘要"""
        total = len(self._checkpoints)
        by_status = {}
        for cp in self._checkpoints.values():
            s = cp.status.value
            by_status[s] = by_status.get(s, 0) + 1
        return {"total": total, "by_status": by_status}


# ============================================================
# 全局单例
# ============================================================

_manager = None

def get_checkpoint_manager() -> DecisionCheckpointManager:
    """获取全局决策检查点管理器"""
    global _manager
    if _manager is None:
        _manager = DecisionCheckpointManager()
        _register_default_fallbacks(_manager)
    return _manager


def _register_default_fallbacks(mgr: DecisionCheckpointManager):
    """注册默认降级策略"""

    # --- MIMO Chat 降级链 ---
    def fallback_cached_response(**kwargs):
        """降级1：返回缓存的通用响应"""
        msg = kwargs.get("message", "")
        return {
            "response": "我理解您的问题。由于系统繁忙，我先为您提供一般性建议：\n"
                       "1. 如果症状持续，请及时就医\n"
                       "2. 保持良好的生活习惯\n"
                       "3. 如有紧急情况请拨打120\n\n"
                       "稍后系统恢复后，我可以为您提供更详细的分析。",
            "source": "cached_fallback",
            "degraded": True
        }

    def fallback_template_response(**kwargs):
        """降级2：基于模板的简单响应"""
        return {
            "response": "系统暂时无法处理您的请求。请稍后重试，或直接前往医院就诊。",
            "source": "template_fallback",
            "degraded": True
        }

    mgr.register_fallback("mimo_chat", FallbackStrategy(
        name="cached_response",
        priority=1,
        handler=fallback_cached_response,
        description="使用缓存的通用医疗建议"
    ))
    mgr.register_fallback("mimo_chat", FallbackStrategy(
        name="template_response",
        priority=2,
        handler=fallback_template_response,
        description="使用最简模板响应"
    ))

    # --- 药物重定位降级链 ---
    def fallback_local_search(**kwargs):
        """降级1：仅使用本地缓存数据"""
        return {
            "drug_name": kwargs.get("drug_name", ""),
            "disease_name": kwargs.get("disease_name", ""),
            "result": "由于外部服务不可用，仅提供本地缓存的基本信息。建议稍后重试获取完整评估。",
            "source": "local_cache",
            "degraded": True,
            "completeness_score": 0.3
        }

    def fallback_partial_report(**kwargs):
        """降级2：生成部分报告"""
        return {
            "drug_name": kwargs.get("drug_name", ""),
            "disease_name": kwargs.get("disease_name", ""),
            "result": "服务部分不可用，以下为可获取的信息片段。",
            "source": "partial",
            "degraded": True,
            "completeness_score": 0.1
        }

    mgr.register_fallback("drug_repurposing", FallbackStrategy(
        name="local_cache",
        priority=1,
        handler=fallback_local_search,
        description="使用本地缓存数据"
    ))
    mgr.register_fallback("drug_repurposing", FallbackStrategy(
        name="partial_report",
        priority=2,
        handler=fallback_partial_report,
        description="生成部分可用报告"
    ))

    # --- 罕见病诊断降级链 ---
    def fallback_symptom_based(**kwargs):
        """降级1：仅基于症状关键词匹配"""
        return {
            "diagnoses": [],
            "message": "外部数据库暂时不可用，无法完成完整筛查。建议直接咨询罕见病专科医生。",
            "source": "keyword_only",
            "degraded": True
        }

    mgr.register_fallback("rare_disease_diagnose", FallbackStrategy(
        name="symptom_keyword",
        priority=1,
        handler=fallback_symptom_based,
        description="仅使用关键词匹配"
    ))
