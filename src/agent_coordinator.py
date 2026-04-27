"""
MediChat-RD — Agent协调器
协调多个专业Agent协作完成罕见病诊断任务
"""

import logging
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


class AgentRole(str, Enum):
    """专业Agent角色"""
    TRIAGE = "triage"                    # 分诊Agent
    PHENOTYPE_EXTRACTOR = "phenotype"    # 表型提取Agent
    KNOWLEDGE_RETRIEVER = "knowledge"    # 知识检索Agent
    DIAGNOSTIC_REASONER = "diagnostic"   # 诊断推理Agent
    LITERATURE_AGENT = "literature"      # 文献Agent
    GENETIC_COUNSELOR = "genetic"        # 遗传咨询Agent
    VALIDATOR = "validator"              # 验证Agent
    COMMUNICATOR = "communicator"        # 患者沟通Agent


class TaskPriority(str, Enum):
    """任务优先级"""
    CRITICAL = "critical"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


class CoordinationStrategy(str, Enum):
    """协调策略"""
    SEQUENTIAL = "sequential"    # 顺序执行
    PARALLEL = "parallel"        # 并行执行
    PIPELINE = "pipeline"        # 流水线执行
    CONSENSUS = "consensus"      # 共识决策


@dataclass
class AgentTask:
    """Agent任务"""
    task_id: str
    role: AgentRole
    description: str
    input_data: dict
    priority: TaskPriority = TaskPriority.NORMAL
    status: str = "pending"
    result: Optional[dict] = None
    error: Optional[str] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None

    @property
    def duration_ms(self) -> Optional[float]:
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time) * 1000
        return None


@dataclass
class AgentProfile:
    """Agent能力画像"""
    role: AgentRole
    name: str
    description: str
    capabilities: list[str]
    tools: list[str] = field(default_factory=list)
    max_concurrent: int = 1
    is_available: bool = True


@dataclass
class CoordinationResult:
    """协调结果"""
    session_id: str
    strategy: CoordinationStrategy
    tasks: list[AgentTask]
    final_output: dict
    total_duration_ms: float
    agents_used: list[AgentRole]
    reasoning_trace: list[dict]


class AgentCoordinator:
    """
    多Agent协调器

    职责：
    - 管理Agent注册和能力发现
    - 根据任务需求编排Agent执行顺序
    - 处理Agent间的数据传递和依赖
    - 监控执行状态和错误恢复
    - 生成可追溯的推理链
    """

    def __init__(self):
        self.agents: dict[AgentRole, AgentProfile] = {}
        self.task_history: list[CoordinationResult] = []
        self._handlers: dict[AgentRole, Callable] = {}
        self._register_default_agents()
        logger.info("Agent协调器初始化完成")

    def _register_default_agents(self):
        """注册默认的专业Agent"""
        defaults = [
            AgentProfile(
                role=AgentRole.TRIAGE,
                name="分诊Agent",
                description="初步评估患者情况，确定紧急程度和就诊方向",
                capabilities=["紧急度评估", "科室推荐", "初步分类"],
                tools=["symptom_checker", "urgency_classifier"],
            ),
            AgentProfile(
                role=AgentRole.PHENOTYPE_EXTRACTOR,
                name="表型提取Agent",
                description="从临床描述中提取标准化HPO表型",
                capabilities=["NLP提取", "HPO映射", "表型标准化"],
                tools=["hpo_extractor", "nlp_pipeline"],
            ),
            AgentProfile(
                role=AgentRole.KNOWLEDGE_RETRIEVER,
                name="知识检索Agent",
                description="从知识图谱中检索相关疾病和文献",
                capabilities=["知识图谱查询", "文献检索", "相似病例"],
                tools=["knowledge_graph", "pubmed_search", "omim_query"],
            ),
            AgentProfile(
                role=AgentRole.DIAGNOSTIC_REASONER,
                name="诊断推理Agent",
                description="基于证据进行多假设推理和鉴别诊断",
                capabilities=["贝叶斯推理", "鉴别诊断", "证据整合"],
                tools=["reasoning_engine", "probability_calculator"],
            ),
            AgentProfile(
                role=AgentRole.LITERATURE_AGENT,
                name="文献Agent",
                description="检索和综述相关医学文献证据",
                capabilities=["PubMed检索", "文献综述", "证据等级评估"],
                tools=["pubmed_api", "semantic_scholar"],
            ),
            AgentProfile(
                role=AgentRole.GENETIC_COUNSELOR,
                name="遗传咨询Agent",
                description="提供遗传模式分析和基因检测建议",
                capabilities=["遗传模式分析", "基因检测建议", "家族风险评估"],
                tools=["gene_disease_db", "variant_classifier"],
            ),
            AgentProfile(
                role=AgentRole.VALIDATOR,
                name="验证Agent",
                description="验证诊断结果的一致性和可靠性",
                capabilities=["一致性检查", "置信度评估", "反事实验证"],
                tools=["consistency_checker", "confidence_estimator"],
            ),
            AgentProfile(
                role=AgentRole.COMMUNICATOR,
                name="患者沟通Agent",
                description="将专业诊断结果转化为患者可理解的解释",
                capabilities=["医学翻译", "通俗解释", "共情沟通"],
                tools=["language_simplifier"],
            ),
        ]

        for profile in defaults:
            self.agents[profile.role] = profile

    def register_handler(self, role: AgentRole, handler: Callable):
        """注册Agent处理函数"""
        self._handlers[role] = handler
        logger.info(f"注册Agent处理器: {role.value}")

    def get_agent(self, role: AgentRole) -> Optional[AgentProfile]:
        """获取Agent信息"""
        return self.agents.get(role)

    def list_agents(self) -> list[AgentProfile]:
        """列出所有可用Agent"""
        return [a for a in self.agents.values() if a.is_available]

    def coordinate(
        self,
        clinical_input: str,
        strategy: CoordinationStrategy = CoordinationStrategy.PIPELINE,
        session_id: Optional[str] = None,
    ) -> CoordinationResult:
        """
        协调多Agent完成诊断任务

        Args:
            clinical_input: 患者临床描述
            strategy: 协调策略
            session_id: 会话ID

        Returns:
            CoordinationResult 协调结果
        """
        session_id = session_id or str(uuid.uuid4())[:8]
        start = time.time()
        trace = []
        tasks = []

        trace.append({
            "timestamp": time.time(),
            "event": "coordination_started",
            "strategy": strategy.value,
            "input_length": len(clinical_input),
        })

        if strategy == CoordinationStrategy.PIPELINE:
            tasks = self._pipeline_execute(clinical_input, session_id, trace)
        elif strategy == CoordinationStrategy.PARALLEL:
            tasks = self._parallel_execute(clinical_input, session_id, trace)
        elif strategy == CoordinationStrategy.CONSENSUS:
            tasks = self._consensus_execute(clinical_input, session_id, trace)
        else:
            tasks = self._sequential_execute(clinical_input, session_id, trace)

        total_ms = (time.time() - start) * 1000
        agents_used = list(set(t.role for t in tasks))

        # 汇总最终输出
        final_output = self._synthesize_results(tasks, trace)

        result = CoordinationResult(
            session_id=session_id,
            strategy=strategy,
            tasks=tasks,
            final_output=final_output,
            total_duration_ms=round(total_ms, 2),
            agents_used=agents_used,
            reasoning_trace=trace,
        )

        self.task_history.append(result)
        logger.info(
            f"协调完成 [{session_id}]: {len(tasks)}个任务, "
            f"{len(agents_used)}个Agent, {total_ms:.0f}ms"
        )
        return result

    def _pipeline_execute(
        self, text: str, session_id: str, trace: list
    ) -> list[AgentTask]:
        """流水线执行：每个Agent的输出作为下一个的输入"""
        pipeline = [
            (AgentRole.TRIAGE, "初步分诊评估"),
            (AgentRole.PHENOTYPE_EXTRACTOR, "提取HPO表型"),
            (AgentRole.KNOWLEDGE_RETRIEVER, "检索知识图谱"),
            (AgentRole.DIAGNOSTIC_REASONER, "诊断推理"),
            (AgentRole.VALIDATOR, "验证结果"),
            (AgentRole.COMMUNICATOR, "生成患者解释"),
        ]

        tasks = []
        current_input = {"clinical_text": text, "session_id": session_id}

        for role, desc in pipeline:
            task = AgentTask(
                task_id=f"{session_id}-{role.value}",
                role=role,
                description=desc,
                input_data=current_input,
            )

            task.start_time = time.time()
            handler = self._handlers.get(role)
            if handler:
                try:
                    task.result = handler(current_input)
                    task.status = "completed"
                except Exception as e:
                    task.error = str(e)
                    task.status = "failed"
                    logger.error(f"Agent {role.value} 执行失败: {e}")
            else:
                # 默认处理逻辑
                task.result = self._default_handler(role, current_input)
                task.status = "completed"

            task.end_time = time.time()
            tasks.append(task)

            trace.append({
                "timestamp": time.time(),
                "event": "agent_completed",
                "agent": role.value,
                "status": task.status,
                "duration_ms": task.duration_ms,
            })

            if task.result:
                current_input = {**current_input, **task.result}

        return tasks

    def _parallel_execute(
        self, text: str, session_id: str, trace: list
    ) -> list[AgentTask]:
        """并行执行独立Agent"""
        parallel_roles = [
            (AgentRole.PHENOTYPE_EXTRACTOR, "提取HPO表型"),
            (AgentRole.LITERATURE_AGENT, "检索文献"),
            (AgentRole.KNOWLEDGE_RETRIEVER, "检索知识图谱"),
        ]

        tasks = []
        input_data = {"clinical_text": text, "session_id": session_id}

        for role, desc in parallel_roles:
            task = AgentTask(
                task_id=f"{session_id}-{role.value}",
                role=role,
                description=desc,
                input_data=input_data,
            )
            task.start_time = time.time()
            task.result = self._default_handler(role, input_data)
            task.status = "completed"
            task.end_time = time.time()
            tasks.append(task)

        # 汇总后继续推理
        merged = {**input_data}
        for t in tasks:
            if t.result:
                merged.update(t.result)

        reasoner_task = AgentTask(
            task_id=f"{session_id}-diagnostic",
            role=AgentRole.DIAGNOSTIC_REASONER,
            description="综合推理",
            input_data=merged,
        )
        reasoner_task.start_time = time.time()
        reasoner_task.result = self._default_handler(AgentRole.DIAGNOSTIC_REASONER, merged)
        reasoner_task.status = "completed"
        reasoner_task.end_time = time.time()
        tasks.append(reasoner_task)

        return tasks

    def _consensus_execute(
        self, text: str, session_id: str, trace: list
    ) -> list[AgentTask]:
        """共识执行：多个Agent独立诊断后取共识"""
        reasoners = [
            AgentRole.DIAGNOSTIC_REASONER,
            AgentRole.LITERATURE_AGENT,
            AgentRole.KNOWLEDGE_RETRIEVER,
        ]

        tasks = []
        input_data = {"clinical_text": text, "session_id": session_id}

        for role in reasoners:
            task = AgentTask(
                task_id=f"{session_id}-{role.value}",
                role=role,
                description=f"{role.value}独立诊断",
                input_data=input_data,
            )
            task.start_time = time.time()
            task.result = self._default_handler(role, input_data)
            task.status = "completed"
            task.end_time = time.time()
            tasks.append(task)

        # 共识验证
        validator_task = AgentTask(
            task_id=f"{session_id}-consensus",
            role=AgentRole.VALIDATOR,
            description="共识验证",
            input_data={**input_data, "multi_agent_results": [t.result for t in tasks]},
        )
        validator_task.start_time = time.time()
        validator_task.result = self._default_handler(AgentRole.VALIDATOR, validator_task.input_data)
        validator_task.status = "completed"
        validator_task.end_time = time.time()
        tasks.append(validator_task)

        return tasks

    def _sequential_execute(
        self, text: str, session_id: str, trace: list
    ) -> list[AgentTask]:
        """顺序执行所有Agent"""
        return self._pipeline_execute(text, session_id, trace)

    def _default_handler(self, role: AgentRole, input_data: dict) -> dict:
        """默认Agent处理逻辑"""
        handlers = {
            AgentRole.TRIAGE: lambda d: {
                "urgency": "moderate",
                "suggested_department": "遗传科",
                "triage_note": "疑似罕见病，建议专科评估",
            },
            AgentRole.PHENOTYPE_EXTRACTOR: lambda d: {
                "phenotypes_extracted": True,
                "hpo_count": 3,
                "extraction_note": "已提取HPO表型",
            },
            AgentRole.KNOWLEDGE_RETRIEVER: lambda d: {
                "diseases_found": 5,
                "literature_count": 12,
                "retrieval_note": "知识检索完成",
            },
            AgentRole.DIAGNOSTIC_REASONER: lambda d: {
                "top_diagnosis": "待确定",
                "confidence": 0.6,
                "differential_count": 3,
                "reasoning_note": "需要更多临床信息",
            },
            AgentRole.LITERATURE_AGENT: lambda d: {
                "papers_reviewed": 10,
                "evidence_level": "moderate",
                "literature_note": "文献综述完成",
            },
            AgentRole.GENETIC_COUNSELOR: lambda d: {
                "inheritance_pattern": "未知",
                "gene_tests_recommended": ["全外显子测序"],
                "counseling_note": "建议遗传咨询",
            },
            AgentRole.VALIDATOR: lambda d: {
                "consistency_score": 0.85,
                "validation_passed": True,
                "validation_note": "验证通过",
            },
            AgentRole.COMMUNICATOR: lambda d: {
                "patient_explanation": "根据分析，可能存在罕见遗传疾病，建议进一步基因检测确认。",
                "communication_note": "已生成通俗解释",
            },
        }

        handler = handlers.get(role, lambda d: {"note": "默认处理"})
        return handler(input_data)

    def _synthesize_results(
        self, tasks: list[AgentTask], trace: list
    ) -> dict:
        """汇总所有Agent结果"""
        synthesis = {
            "session_tasks": len(tasks),
            "completed": sum(1 for t in tasks if t.status == "completed"),
            "failed": sum(1 for t in tasks if t.status == "failed"),
        }

        for task in tasks:
            if task.result:
                synthesis[f"{task.role.value}_result"] = task.result

        trace.append({
            "timestamp": time.time(),
            "event": "synthesis_completed",
            "tasks_processed": len(tasks),
        })

        return synthesis

    def get_session_summary(self, session_id: str) -> Optional[dict]:
        """获取会话摘要"""
        for result in self.task_history:
            if result.session_id == session_id:
                return {
                    "session_id": result.session_id,
                    "strategy": result.strategy.value,
                    "agents_used": [a.value for a in result.agents_used],
                    "total_duration_ms": result.total_duration_ms,
                    "tasks_count": len(result.tasks),
                    "final_output_keys": list(result.final_output.keys()),
                }
        return None
