"""
MediChat-RD 质量门控循环
参考OrphanCure-AI，实现自动化质量评估和定向重跑
"""

import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)

class GateStatus(Enum):
    """质量门状态"""
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"

@dataclass
class QualityGate:
    """质量门"""
    name: str
    description: str
    status: GateStatus
    score: float  # 0-1
    message: str
    suggestions: List[str] = field(default_factory=list)

@dataclass
class QualityGateResult:
    """质量门控结果"""
    gates: List[QualityGate]
    overall_score: float
    passed_count: int
    failed_count: int
    warning_count: int
    can_proceed: bool
    recommendations: List[str]

class QualityGateController:
    """质量门控控制器"""
    
    def __init__(self):
        # 定义质量门
        self.gate_definitions = {
            "entity_resolved": {
                "description": "药物和疾病实体已成功解析",
                "weight": 0.15,
                "threshold": 1.0
            },
            "targets_found": {
                "description": "找到了药物或疾病的相关靶点",
                "weight": 0.20,
                "threshold": 0.5
            },
            "target_overlap": {
                "description": "药物和疾病之间存在靶点交集",
                "weight": 0.25,
                "threshold": 0.0
            },
            "literature_found": {
                "description": "找到了相关文献",
                "weight": 0.15,
                "threshold": 1.0
            },
            "evidence_classified": {
                "description": "文献证据已分类",
                "weight": 0.10,
                "threshold": 0.5
            },
            "claims_generated": {
                "description": "生成了有意义的声明",
                "weight": 0.15,
                "threshold": 1.0
            }
        }
    
    def evaluate_gates(self, metrics: Dict) -> QualityGateResult:
        """评估所有质量门"""
        gates = []
        total_score = 0.0
        total_weight = 0.0
        
        for gate_name, definition in self.gate_definitions.items():
            # 获取指标值
            metric_value = metrics.get(gate_name, 0)
            
            # 计算分数
            if gate_name == "entity_resolved":
                score = 1.0 if metric_value else 0.0
            elif gate_name == "targets_found":
                score = min(metric_value / 10, 1.0)  # 10个靶点得满分
            elif gate_name == "target_overlap":
                score = min(metric_value / 3, 1.0)  # 3个交集得满分
            elif gate_name == "literature_found":
                score = min(metric_value / 5, 1.0)  # 5篇文献得满分
            elif gate_name == "evidence_classified":
                score = metric_value if isinstance(metric_value, float) else (1.0 if metric_value else 0.0)
            elif gate_name == "claims_generated":
                score = min(metric_value / 2, 1.0)  # 2个声明得满分
            else:
                score = 0.0
            
            # 确定状态
            threshold = definition["threshold"]
            if score >= threshold:
                status = GateStatus.PASSED
            elif score >= threshold * 0.5:
                status = GateStatus.WARNING
            else:
                status = GateStatus.FAILED
            
            # 生成消息和建议
            message, suggestions = self._generate_gate_message(
                gate_name, score, status, metric_value
            )
            
            # 创建质量门
            gate = QualityGate(
                name=gate_name,
                description=definition["description"],
                status=status,
                score=score,
                message=message,
                suggestions=suggestions
            )
            
            gates.append(gate)
            
            # 累加分数
            weight = definition["weight"]
            total_score += score * weight
            total_weight += weight
        
        # 计算总体分数
        overall_score = total_score / total_weight if total_weight > 0 else 0.0
        
        # 统计状态
        passed_count = sum(1 for g in gates if g.status == GateStatus.PASSED)
        failed_count = sum(1 for g in gates if g.status == GateStatus.FAILED)
        warning_count = sum(1 for g in gates if g.status == GateStatus.WARNING)
        
        # 确定是否可以继续
        can_proceed = failed_count == 0
        
        # 生成建议
        recommendations = self._generate_recommendations(gates)
        
        return QualityGateResult(
            gates=gates,
            overall_score=overall_score,
            passed_count=passed_count,
            failed_count=failed_count,
            warning_count=warning_count,
            can_proceed=can_proceed,
            recommendations=recommendations
        )
    
    def _generate_gate_message(
        self,
        gate_name: str,
        score: float,
        status: GateStatus,
        metric_value
    ) -> Tuple[str, List[str]]:
        """生成质量门消息和建议"""
        messages = {
            "entity_resolved": {
                GateStatus.PASSED: ("实体解析成功", []),
                GateStatus.FAILED: ("实体解析失败", ["尝试使用更准确的药物/疾病名称", "检查拼写是否正确", "尝试使用同义词或商品名"])
            },
            "targets_found": {
                GateStatus.PASSED: (f"找到{metric_value}个相关靶点", []),
                GateStatus.WARNING: (f"只找到{metric_value}个靶点，可能不够充分", ["尝试更具体的目标疾病名称", "检查药物是否有已知靶点"]),
                GateStatus.FAILED: ("未找到相关靶点", ["确认药物/疾病ID是否正确", "尝试其他候选实体"])
            },
            "target_overlap": {
                GateStatus.PASSED: (f"发现{metric_value}个靶点交集", []),
                GateStatus.WARNING: (f"靶点交集有限（{metric_value}个）", ["这可能意味着作用机制不明确", "建议查阅更多文献"]),
                GateStatus.FAILED: ("无靶点交集", ["药物可能通过其他机制起作用", "考虑药物的多靶点特性", "建议进一步研究"])
            },
            "literature_found": {
                GateStatus.PASSED: (f"找到{metric_value}篇相关文献", []),
                GateStatus.WARNING: (f"文献数量有限（{metric_value}篇）", ["尝试扩大检索范围", "使用同义词进行检索"]),
                GateStatus.FAILED: ("未找到相关文献", ["尝试不同的检索词组合", "检查药物/疾病名称是否常用", "考虑这是一个研究空白"])
            },
            "evidence_classified": {
                GateStatus.PASSED: ("证据分类完成", []),
                GateStatus.WARNING: ("部分证据未分类", ["人工审查未分类的证据", "优化分类算法"]),
                GateStatus.FAILED: ("证据分类失败", ["检查文献质量", "人工审查证据"])
            },
            "claims_generated": {
                GateStatus.PASSED: (f"生成{metric_value}个有意义的声明", []),
                GateStatus.WARNING: ("声明数量有限", ["尝试发现更多潜在作用", "结合临床经验进行判断"]),
                GateStatus.FAILED: ("无法生成声明", ["证据不足以支持任何声明", "建议进行更多研究"])
            }
        }
        
        gate_messages = messages.get(gate_name, {})
        return gate_messages.get(status, ("未知状态", []))
    
    def _generate_recommendations(self, gates: List[QualityGate]) -> List[str]:
        """生成总体建议"""
        recommendations = []
        
        failed_gates = [g for g in gates if g.status == GateStatus.FAILED]
        warning_gates = [g for g in gates if g.status == GateStatus.WARNING]
        
        if failed_gates:
            recommendations.append(f"❌ {len(failed_gates)}个质量门未通过，建议先解决这些问题")
            for gate in failed_gates:
                recommendations.append(f"  - {gate.description}: {gate.message}")
        
        if warning_gates:
            recommendations.append(f"⚠️ {len(warning_gates)}个质量门有警告，建议关注")
        
        if not failed_gates and not warning_gates:
            recommendations.append("✅ 所有质量门通过，可以生成最终报告")
        
        return recommendations
    
    def generate_report(self, result: QualityGateResult) -> str:
        """生成质量门控报告"""
        output = []
        output.append("=" * 60)
        output.append("质量门控评估报告")
        output.append("=" * 60)
        
        output.append(f"\n📊 总体评分: {result.overall_score:.1%}")
        output.append(f"✅ 通过: {result.passed_count}")
        output.append(f"⚠️ 警告: {result.warning_count}")
        output.append(f"❌ 失败: {result.failed_count}")
        output.append(f"🚦 可以继续: {'是' if result.can_proceed else '否'}")
        
        output.append(f"\n📋 质量门详情:")
        for i, gate in enumerate(result.gates, 1):
            status_icon = {
                GateStatus.PASSED: "✅",
                GateStatus.WARNING: "⚠️",
                GateStatus.FAILED: "❌"
            }.get(gate.status, "❓")
            
            output.append(f"\n{i}. {status_icon} {gate.description}")
            output.append(f"   分数: {gate.score:.1%}")
            output.append(f"   状态: {gate.message}")
            
            if gate.suggestions:
                output.append(f"   建议:")
                for suggestion in gate.suggestions:
                    output.append(f"     - {suggestion}")
        
        if result.recommendations:
            output.append(f"\n💡 总体建议:")
            for rec in result.recommendations:
                output.append(f"  {rec}")
        
        output.append("\n" + "=" * 60)
        
        return "\n".join(output)

# 测试
if __name__ == "__main__":
    controller = QualityGateController()
    
    # 模拟指标
    metrics = {
        "entity_resolved": True,
        "targets_found": 8,
        "target_overlap": 2,
        "literature_found": 3,
        "evidence_classified": 0.8,
        "claims_generated": 2
    }
    
    # 评估质量门
    result = controller.evaluate_gates(metrics)
    
    # 生成报告
    report = controller.generate_report(result)
    print(report)
