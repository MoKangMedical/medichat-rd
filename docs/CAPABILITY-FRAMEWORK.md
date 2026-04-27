# 贾维斯能力增强框架 (Jarvis Capability Framework)

> 基于Claw Code架构 + OpenClaw-Medical-Skills + ToolUniverse + LabClaw

## 📐 架构总览

```
┌─────────────────────────────────────────────────────┐
│                   Jarvis (贾维斯)                      │
├─────────────────────────────────────────────────────┤
│  Layer 4: 项目应用层 (MediChat-RD)                    │
│  ├── 4C诊疗体系 (Connect→Consult→Care→Community)    │
│  ├── 药物重定位 Agent                                │
│  ├── 罕见病知识库                                    │
│  └── 患者定位 + 医院推荐                              │
├─────────────────────────────────────────────────────┤
│  Layer 3: 能力执行层 (Skills)                         │
│  ├── 🧠 记忆架构 (4 modules)                         │
│  ├── 🏥 医疗核心 (7 + N modules)                     │
│  ├── 🧬 基因组学 (variant/GWAS/single-cell)          │
│  ├── 💊 药物发现 (drug-repurposing/ADMET/docking)    │
│  ├── 📚 科研文献 (PubMed/arXiv/CNKI)                 │
│  ├── 🤖 Agent编排 (CrewAI/multi-agent)               │
│  └── 🔬 协作研究 (Lobster Tank)                      │
├─────────────────────────────────────────────────────┤
│  Layer 2: 工具集成层 (MCP + API)                      │
│  ├── MCP Server (medical-research-toolkit)           │
│  ├── ToolUniverse (1000+ ML models/tools)            │
│  ├── ChEMBL / OpenTargets / ClinicalTrials.gov       │
│  └── PubMed / OMIM / Reactome / KEGG / UniProt       │
├─────────────────────────────────────────────────────┤
│  Layer 1: 架构基础层 (From Claw Code Patterns)        │
│  ├── ToolRegistry (统一工具注册中心)                   │
│  ├── Hook系统 (PreSkillUse/PostSkillUse)             │
│  ├── Auto-Compaction (上下文自动压缩)                  │
│  ├── Session持久化 (会话状态管理)                      │
│  └── CLAUDE.md链 (分层配置发现)                        │
└─────────────────────────────────────────────────────┘
```

## 🔧 技能分类体系 (Skill Taxonomy)

### T1 - 核心基础 (Core Foundation)
> 必须安装，系统运行基础
- memory-management: 记忆蒸馏、认知记忆、记忆流水线
- security: skill-vetter安全审查
- orchestration: CrewAI、多Agent编排

### T2 - 医疗专业 (Medical Domain)
> 医疗领域核心能力
- clinical: 病历结构化、医学分诊、临床报告
- drug-discovery: 药物重定位、ADMET、靶点验证
- genomics: 变异分析、GWAS、单细胞
- rare-disease: 罕见病诊断、Orphanet/OMIM查询

### T3 - 科研工具 (Research Tools)
> 文献搜索和数据分析
- literature: PubMed、arXiv、CNKI监测
- bioinformatics: Scanpy、BioPython、AlphaFold
- data-science: 统计分析、机器学习

### T4 - 协作与集成 (Integration)
> 外部系统对接
- collaboration: Lobster Tank、GitHub
- infrastructure: 腾讯云COS、腾讯文档、飞书
- communication: 企业微信

## 📊 能力成熟度评估

| 能力域 | 当前水平 | 目标水平 | 差距 |
|-------|---------|---------|------|
| 记忆管理 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Auto-Compaction |
| 医疗核心 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 罕见病+基因组学 |
| 药物发现 | ⭐⭐ | ⭐⭐⭐⭐⭐ | ToolUniverse集成 |
| 科研文献 | ⭐⭐ | ⭐⭐⭐⭐ | 自动监测+推送 |
| Agent编排 | ⭐⭐ | ⭐⭐⭐⭐ | Hook系统+编排 |
| 知识图谱 | ⭐ | ⭐⭐⭐⭐ | 建设中 |

## 🔄 能力迭代流程 (Capability Loop)

```
Discover (发现) → Evaluate (评估) → Install (安装) → Test (测试) → Integrate (集成) → Monitor (监控)
     ↑                                                                                    |
     └──────────────────────── AutoDream (记忆漂移修正) ←──────────────────────────────────┘
```

## 📋 Skill管理规范

### 安装流程
1. 从 skillhub/clawhub/OpenClaw-Medical-Skills/LabClaw 发现候选skill
2. skill-vetter 安全审查
3. 测试skill功能（至少一个真实用例）
4. 记录到 heartbeat-state.json
5. 如需环境变量，写入 .env.skills

### 分级策略
- T1 (核心): 自动加载到每次session
- T2 (专业): 按需加载，医疗相关任务触发
- T3 (工具): 按需加载，研究相关任务触发
- T4 (集成): 需要外部API Key时激活

### 版本追踪
- 每个skill记录来源（skillhub/labclaw/medical-skills）
- 定期检查更新（AutoDream流程中）
- 冲突检测（同名skill优先级: medical-skills > labclaw > skillhub）

---

## 🏗️ Claw Code 架构精华提取与Python移植方案

> 来源：ultraworkers/claw-code（149K+ Stars），Rust实现，clean-room重写
> 作者：Sigrid Jin（@instructkr），2026年3月31日创建
> 决策：不安装Rust CLI，提取架构模式移植到MediChat-RD Python技术栈

### Claw Code 原始Rust工作区结构

```
rust/crates/
├── runtime/          — 核心运行时（500K代码）
│   ├── conversation.rs   56K — 会话运行时，泛型设计 ConversationRuntime<C,T>
│   ├── session.rs        41K — 会话状态管理（序列化/反序列化）
│   ├── hooks.rs          29K — PreToolUse/PostToolUse 钩子管道
│   ├── permissions.rs    20K — 权限策略框架（danger-full-access等）
│   ├── compact.rs        23K — 自动压缩（10万token阈值触发）
│   ├── config.rs         48K — 运行时特性配置
│   ├── mcp_stdio.rs      88K — MCP外部工具集成（标准I/O协议）
│   └── prompt.rs         28K — 提示词管理（系统提示+上下文拼接）
├── tools/            — 工具注册中心（179K）
├── api/              — API客户端（OAuth + 流式支持）
├── plugins/          — 插件模型（钩子管道+捆绑插件）
├── commands/         — 斜杠命令/Skills发现/配置检查
├── telemetry/        — 遥测
└── claw-cli/         — 交互式REPL + Markdown渲染
```

### 五大架构模式详解

#### 模式1：ToolRegistry（统一工具注册中心）

**Rust原版设计：**
- 内置工具 + 插件工具的统一注册表
- 支持名称别名映射（`read` → `read_file`）
- 工具冲突检测和优先级排序
- 运行时动态加载/卸载

**Python移植方案：**
```python
# mediChatRD/core/tool_registry.py
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Any

@dataclass
class ToolMeta:
    """工具元数据"""
    name: str
    handler: Callable
    aliases: List[str] = field(default_factory=list)
    category: str = "general"  # medical/research/memory/infra
    priority: int = 50  # 数字越小优先级越高
    enabled: bool = True
    source: str = "builtin"  # builtin/plugin/mcp
    description: str = ""

class ToolRegistry:
    """统一工具注册中心（借鉴Claw Code ToolRegistry）"""
    
    def __init__(self):
        self._tools: Dict[str, ToolMeta] = {}
        self._alias_map: Dict[str, str] = {}
        self._hooks: Dict[str, List[Callable]] = {
            "pre_register": [],
            "post_register": [],
            "pre_execute": [],
            "post_execute": [],
        }
    
    def register(self, meta: ToolMeta) -> None:
        """注册工具（含别名和冲突检测）"""
        # 冲突检测
        if meta.name in self._tools:
            existing = self._tools[meta.name]
            if existing.priority <= meta.priority:
                return  # 高优先级工具不被覆盖
        
        # 执行pre_register钩子
        for hook in self._hooks["pre_register"]:
            hook(meta)
        
        self._tools[meta.name] = meta
        
        # 别名映射
        for alias in meta.aliases:
            self._alias_map[alias] = meta.name
        
        # 执行post_register钩子
        for hook in self._hooks["post_register"]:
            hook(meta)
    
    def resolve(self, name: str) -> Optional[ToolMeta]:
        """解析工具名（支持别名）"""
        # 直接查找
        if name in self._tools and self._tools[name].enabled:
            return self._tools[name]
        # 别名查找
        canonical = self._alias_map.get(name)
        if canonical and canonical in self._tools and self._tools[canonical].enabled:
            return self._tools[canonical]
        return None
    
    def list_by_category(self, category: str) -> List[ToolMeta]:
        """按分类列出工具"""
        return [t for t in self._tools.values() if t.category == category and t.enabled]
    
    def execute(self, name: str, **kwargs) -> Any:
        """执行工具（带钩子管道）"""
        meta = self.resolve(name)
        if not meta:
            raise ToolNotFoundError(f"Tool '{name}' not found")
        
        # PreExecute钩子
        context = {"tool": meta, "args": kwargs}
        for hook in self._hooks["pre_execute"]:
            result = hook(context)
            if result is ABORT_SIGNAL:
                raise ToolAbortedError(f"Tool '{name}' aborted by pre-execute hook")
        
        # 执行
        try:
            output = meta.handler(**kwargs)
        except Exception as e:
            output = ToolError(str(e))
        
        # PostExecute钩子
        context["output"] = output
        for hook in self._hooks["post_execute"]:
            hook(context)
        
        return output
```

**与MediChat-RD的集成点：**
- 统一66个OpenClaw skill的注册和发现
- 支持medical/research/memory/infra四分类
- 别名映射解决同名skill冲突
- 钩子管道实现执行监控

---

#### 模式2：Auto-Compaction（上下文自动压缩）

**Rust原版设计：**
- `compact.rs`（23K）：token阈值100K自动触发
- 保留关键上下文（系统提示、最新消息摘要）
- 压缩历史对话为摘要token
- 支持增量压缩和全量压缩两种模式

**Python移植方案：**
```python
# mediChatRD/core/auto_compaction.py
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum
import tiktoken

class CompactionMode(Enum):
    INCREMENTAL = "incremental"  # 增量压缩（保留最近N条）
    FULL = "full"                # 全量压缩（摘要全部历史）

@dataclass
class ConversationTurn:
    """对话轮次"""
    role: str  # system/user/assistant/tool
    content: str
    tokens: int = 0
    timestamp: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    compressed: bool = False

@dataclass
class CompactionResult:
    """压缩结果"""
    original_tokens: int
    compressed_tokens: int
    turns_preserved: int
    turns_summarized: int
    mode: CompactionMode

class AutoCompactor:
    """自动上下文压缩器（借鉴Claw Code compact.rs）"""
    
    DEFAULT_THRESHOLD = 100_000  # 100K token触发
    MIN_PRESERVE_TURNS = 6       # 最少保留最近6条
    SUMMARY_RATIO = 0.15         # 压缩比目标15%
    
    def __init__(self, 
                 threshold: int = DEFAULT_THRESHOLD,
                 min_preserve: int = MIN_PRESERVE_TURNS,
                 llm_summarize: callable = None):
        self.threshold = threshold
        self.min_preserve = min_preserve
        self.llm_summarize = llm_summarize  # 用于生成摘要的LLM调用
        self.encoder = tiktoken.encoding_for_model("gpt-4")
    
    def count_tokens(self, text: str) -> int:
        """精确token计数"""
        return len(self.encoder.encode(text))
    
    def should_compact(self, turns: List[ConversationTurn]) -> bool:
        """判断是否需要压缩"""
        total = sum(t.tokens for t in turns)
        return total >= self.threshold
    
    def compact(self, 
                turns: List[ConversationTurn],
                mode: CompactionMode = CompactionMode.INCREMENTAL
                ) -> tuple[List[ConversationTurn], CompactionResult]:
        """
        执行压缩
        
        Returns:
            (压缩后的turns列表, 压缩结果元数据)
        """
        original_tokens = sum(t.tokens for t in turns)
        
        if mode == CompactionMode.INCREMENTAL:
            return self._incremental_compact(turns, original_tokens)
        else:
            return self._full_compact(turns, original_tokens)
    
    def _incremental_compact(self, 
                              turns: List[ConversationTurn],
                              original_tokens: int
                              ) -> tuple[List[ConversationTurn], CompactionResult]:
        """增量压缩：保留system prompt + 最近N条 + 历史摘要"""
        system_turns = [t for t in turns if t.role == "system"]
        non_system = [t for t in turns if t.role != "system"]
        
        # 保留最近的turns
        preserved = non_system[-self.min_preserve:]
        to_summarize = non_system[:-self.min_preserve]
        
        if not to_summarize:
            return turns, CompactionResult(original_tokens, original_tokens, 
                                           len(turns), 0, CompactionMode.INCREMENTAL)
        
        # 生成历史摘要
        history_text = "\n".join(f"[{t.role}]: {t.content}" for t in to_summarize)
        summary = self.llm_summarize(
            f"请将以下对话历史压缩为简洁摘要，保留关键信息（诊断、药物、结论）：\n{history_text}"
        ) if self.llm_summarize else "[对话历史已压缩]"
        
        summary_turn = ConversationTurn(
            role="system",
            content=f"## 之前对话摘要\n{summary}",
            tokens=self.count_tokens(summary),
            compressed=True
        )
        
        result_turns = system_turns + [summary_turn] + preserved
        compressed_tokens = sum(t.tokens for t in result_turns)
        
        return result_turns, CompactionResult(
            original_tokens=original_tokens,
            compressed_tokens=compressed_tokens,
            turns_preserved=len(preserved) + len(system_turns),
            turns_summarized=len(to_summarize),
            mode=CompactionMode.INCREMENTAL
        )
```

**与MediChat-RD的集成点：**
- MediChat-RD的药物重定位Agent对话可达50K+token
- 100K阈值适合多Agent长对话场景
- 摘要保留诊断、药物、结论等关键医疗信息
- 支持与MIMO API对接生成摘要

---

#### 模式3：Hook系统（生命周期钩子管道）

**Rust原版设计：**
- `hooks.rs`（29K）：PreToolUse / PostToolUse 钩子
- 支持中止信号（Abort Signal）
- 钩子管道可链式调用
- 用于权限检查、日志记录、进度报告

**Python移植方案：**
```python
# mediChatRD/core/hooks.py
from typing import Callable, Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import asyncio

class HookPhase(Enum):
    PRE_SKILL_USE = "pre_skill_use"
    POST_SKILL_USE = "post_skill_use"
    PRE_AGENT_CALL = "pre_agent_call"
    POST_AGENT_CALL = "post_agent_call"
    ON_ERROR = "on_error"
    ON_COMPACT = "on_compact"

class AbortSignal(Exception):
    """中止信号：钩子可以通过raise此异常中断执行"""
    def __init__(self, reason: str, fallback: Any = None):
        self.reason = reason
        self.fallback = fallback
        super().__init__(reason)

@dataclass
class HookContext:
    """钩子上下文"""
    phase: HookPhase
    tool_name: str = ""
    agent_name: str = ""
    args: Dict[str, Any] = field(default_factory=dict)
    result: Any = None
    error: Optional[Exception] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

class HookPipeline:
    """钩子管道系统（借鉴Claw Code hooks.rs）"""
    
    def __init__(self):
        self._hooks: Dict[HookPhase, List[Callable]] = {
            phase: [] for phase in HookPhase
        }
        self._async_hooks: Dict[HookPhase, List[Callable]] = {
            phase: [] for phase in HookPhase
        }
    
    def on(self, phase: HookPhase, handler: Callable, priority: int = 50):
        """注册钩子（同步）"""
        self._hooks[phase].append((priority, handler))
        self._hooks[phase].sort(key=lambda x: x[0])
    
    def on_async(self, phase: HookPhase, handler: Callable, priority: int = 50):
        """注册钩子（异步）"""
        self._async_hooks[phase].append((priority, handler))
        self._async_hooks[phase].sort(key=lambda x: x[0])
    
    def trigger(self, phase: HookPhase, context: HookContext) -> HookContext:
        """触发同步钩子管道"""
        for _, handler in self._hooks[phase]:
            try:
                context = handler(context)
            except AbortSignal:
                raise
            except Exception as e:
                context.error = e
                # 触发ON_ERROR钩子
                if phase != HookPhase.ON_ERROR:
                    self.trigger(HookPhase.ON_ERROR, context)
        return context
    
    async def trigger_async(self, phase: HookPhase, context: HookContext) -> HookContext:
        """触发异步钩子管道"""
        for _, handler in self._async_hooks[phase]:
            try:
                context = await handler(context)
            except AbortSignal:
                raise
            except Exception as e:
                context.error = e
                if phase != HookPhase.ON_ERROR:
                    await self.trigger_async(HookPhase.ON_ERROR, context)
        return context

# 预置钩子示例
def permission_guard(context: HookContext) -> HookContext:
    """权限守卫：PreSkillUse阶段检查权限"""
    if context.tool_name in ("exec", "write", "edit"):
        # 检查是否有危险操作标记
        if context.args.get("elevated"):
            raise AbortSignal("权限不足，需要用户确认", fallback="请求授权")
    return context

def execution_logger(context: HookContext) -> HookContext:
    """执行日志：PostSkillUse阶段记录"""
    import logging
    logging.info(f"[Hook] {context.phase.value}: {context.tool_name} -> {context.result}")
    return context

def auto_compact_hook(context: HookContext) -> HookContext:
    """自动压缩钩子：ON_COMPACT阶段触发"""
    from .auto_compaction import AutoCompactor
    compactor = context.metadata.get("compactor")
    if compactor and context.metadata.get("turns"):
        turns, result = compactor.compact(context.metadata["turns"])
        context.metadata["compacted_turns"] = turns
        context.metadata["compaction_result"] = result
    return context
```

**与MediChat-RD的集成点：**
- PreSkillUse：权限检查、输入验证、安全审计
- PostSkillUse：结果日志、性能监控、缓存写入
- ON_ERROR：自动重试、降级处理、告警通知
- ON_COMPACT：自动触发上下文压缩

---

#### 模式4：Session持久化（会话状态管理）

**Rust原版设计：**
- `session.rs`（41K）：完整会话状态序列化/反序列化
- 支持会话快照、恢复、分支
- 会话元数据（创建时间、token计数、工具调用历史）

**Python移植方案：**
```python
# mediChatRD/core/session.py
import json
import time
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional
from uuid import uuid4

@dataclass
class SessionState:
    """会话状态"""
    session_id: str = field(default_factory=lambda: str(uuid4())[:12])
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    turns: List[Dict[str, Any]] = field(default_factory=list)
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)
    total_tokens: int = 0
    compaction_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)

class SessionManager:
    """会话管理器（借鉴Claw Code session.rs）"""
    
    def __init__(self, storage_dir: str = "./sessions"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self._active: Dict[str, SessionState] = {}
    
    def create(self, tags: List[str] = None) -> SessionState:
        """创建新会话"""
        state = SessionState(tags=tags or [])
        self._active[state.session_id] = state
        self._save(state)
        return state
    
    def load(self, session_id: str) -> Optional[SessionState]:
        """加载会话"""
        if session_id in self._active:
            return self._active[session_id]
        
        path = self.storage_dir / f"{session_id}.json"
        if path.exists():
            data = json.loads(path.read_text())
            state = SessionState(**data)
            self._active[session_id] = state
            return state
        return None
    
    def save(self, session_id: str) -> None:
        """保存会话"""
        if session_id in self._active:
            self._save(self._active[session_id])
    
    def snapshot(self, session_id: str) -> str:
        """创建会话快照"""
        state = self._active.get(session_id)
        if not state:
            raise ValueError(f"Session {session_id} not found")
        
        snapshot_id = f"{session_id}_snap_{int(time.time())}"
        snapshot_path = self.storage_dir / "snapshots" / f"{snapshot_id}.json"
        snapshot_path.parent.mkdir(parents=True, exist_ok=True)
        snapshot_path.write_text(json.dumps(asdict(state), ensure_ascii=False, indent=2))
        return snapshot_id
    
    def _save(self, state: SessionState) -> None:
        state.updated_at = time.time()
        path = self.storage_dir / f"{state.session_id}.json"
        path.write_text(json.dumps(asdict(state), ensure_ascii=False, indent=2))
```

**与MediChat-RD的集成点：**
- 患者咨询会话持久化（支持断点续聊）
- 多Agent协作会话的分支和合并
- 会话快照用于调试和回溯
- 与Auto-Compaction联动管理上下文

---

#### 模式5：分层配置发现链（CLAUDE.md链）

**Rust原版设计：**
- 从工作目录向上递归查找配置文件
- 支持多级配置合并（项目级 > 用户级 > 全局级）
- 配置文件名约定（CLAUDE.md / .claude.json）

**Python移植方案：**
```python
# mediChatRD/core/config_chain.py
from pathlib import Path
from typing import List, Dict, Any, Optional
import json
import yaml

class ConfigChain:
    """分层配置发现链（借鉴Claw Code CLAUDE.md链）"""
    
    CONFIG_NAMES = [
        "AGENTS.md",        # 项目级（当前已存在）
        "SOUL.md",          # 人格定义
        "USER.md",          # 用户偏好
        "TOOLS.md",         # 工具配置
        "HEARTBEAT.md",     # 心跳协议
        "CAPABILITY-FRAMEWORK.md",  # 能力框架
    ]
    
    SEARCH_DEPTH = 5  # 向上搜索层数
    
    def __init__(self, start_dir: str = "."):
        self.start_dir = Path(start_dir).resolve()
        self._chain: List[Path] = []
        self._configs: Dict[str, str] = {}
        self._discover()
    
    def _discover(self):
        """向上递归发现配置文件"""
        current = self.start_dir
        for _ in range(self.SEARCH_DEPTH):
            for name in self.CONFIG_NAMES:
                path = current / name
                if path.exists() and path not in self._chain:
                    self._chain.append(path)
                    self._configs[name] = path.read_text()
            
            parent = current.parent
            if parent == current:
                break
            current = parent
    
    def get(self, name: str) -> Optional[str]:
        """获取配置内容"""
        return self._configs.get(name)
    
    def get_chain(self) -> List[Dict[str, str]]:
        """获取完整配置链"""
        return [
            {"file": p.name, "path": str(p), "size": p.stat().st_size}
            for p in self._chain
        ]
    
    def merge_json_configs(self) -> Dict[str, Any]:
        """合并所有JSON配置（深层合并）"""
        merged = {}
        for path in reversed(self._chain):  # 从底层到顶层
            if path.suffix == ".json":
                try:
                    data = json.loads(path.read_text())
                    merged = self._deep_merge(merged, data)
                except json.JSONDecodeError:
                    pass
        return merged
    
    def _deep_merge(self, base: Dict, override: Dict) -> Dict:
        """深层合并字典"""
        result = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        return result
```

**与MediChat-RD的集成点：**
- 已在OpenClaw中实现（AGENTS.md/SOUL.md/USER.md/TOOLS.md/HEARTBEAT.md）
- MediChat-RD项目可复用此模式做自己的配置发现
- 支持用户级 vs 项目级 vs 全局级配置分层

---

### 移植优先级与实施路线

| 优先级 | 模式 | 预计工作量 | 依赖 | 收益 |
|-------|------|----------|------|------|
| P0 | ToolRegistry | 3天 | 无 | 统一66个skill管理 |
| P0 | Auto-Compaction | 2天 | tiktoken + MIMO API | 解决长对话溢出 |
| P1 | Hook系统 | 2天 | ToolRegistry | 执行监控+权限 |
| P1 | Session持久化 | 3天 | 无 | 断点续聊+快照 |
| P2 | 配置发现链 | 1天 | 无 | 配置分层管理 |

### Claw Code vs MediChat-RD 技术栈对照

| 维度 | Claw Code (Rust) | MediChat-RD (Python) |
|------|------------------|---------------------|
| 运行时 | `tokio`异步运行时 | `asyncio` + `uvicorn` |
| 序列化 | `serde` + JSON | `dataclasses` + `json` |
| API客户端 | `reqwest` + OAuth | `aiohttp` + `httpx` |
| 类型系统 | Rust强类型 + trait泛型 | Python typing + Protocol |
| 插件系统 | 动态链接库(DLL) | Python模块导入 |
| 配置发现 | `CLAUDE.md`链 | `AGENTS.md` / `SOUL.md`链 |
| 上下文压缩 | 100K token阈值 | 100K token阈值（可调） |
| 钩子系统 | 生命周期枚举 + AbortSignal | 生命周期枚举 + AbortSignal |

### 安全与伦理备注

- Claw Code是 clean-room 重写，非Claude Code源码直接拷贝
- 仅提取架构模式，不复制任何具体代码实现
- 所有移植代码均为原创Python实现
- 符合开源社区对"架构借鉴"的共识规范
