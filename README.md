# MediChat-RD — 罕见病AI诊疗平台

> 基于AI的罕见病在线辅助诊疗系统，4C诊疗体系（Connect→Consult→Care→Community）

## 🌐 正式访问

- **官网**: https://medichatrd.cloud
- **隐私政策**: https://medichatrd.cloud/privacy-policy.html
- **健康检查**: https://medichatrd.cloud/health

## 🎯 使命

让每一个罕见病患者都能获得专业、可及、持续的医疗服务。

## 🧠 技术哲学：Harness理论

> **在AI领域，Harness（环境设计）比模型本身更重要。**
> 优秀的Harness设计（工具链+信息格式+上下文管理+失败恢复+结果验证）能使性能提升64%。

MediChat-RD的本质是**诊断Harness**——不是卖最强医疗AI，是卖最优诊断流程架构：

- **鉴别诊断决策树**：症状→分层鉴别→检查策略→确诊路径
- **多学科会诊编排**：41个专科动态组建+多轮讨论+共识达成（对标RareAgents AAAI 2026）
- **医学工具集成**：文献检索/药物数据库/影像分析的有序调用
- **信息流转格式**：病史→检查→诊断→治疗的结构化上下文
- **失败恢复机制**：诊断不确定时的自动升级（初诊→会诊→转诊）

**护城河来源**：诊断流程的Harness设计，而非医学大模型本身。
模型可以被替换（MIMO/Gemma/Claude），但Harness是私有的。

## 🏗️ 架构

```
┌─────────────────────────────────────────┐
│           MediChat-RD 平台               │
├──────────┬──────────┬───────────────────┤
│ Connect  │ Consult  │ Care + Community  │
│ 患者连接  │ AI辅助诊疗 │ 持续关怀+社群     │
├──────────┴──────────┴───────────────────┤
│  AI引擎层 (MIMO API + 66个Skill)         │
├─────────────────────────────────────────┤
│  数据层 (PubMed/OMIM/ChEMBL/OpenTargets) │
└─────────────────────────────────────────┘
```

## 📦 核心功能

### 🔬 AI辅助诊断
- 5个罕见病种专业评估（MG/SMA/DMD/ALS/PKU）
- 多维度症状分析 + 风险分级
- 自动匹配专科合作医院

### 💊 药物重定位
- 基于多源数据的药物-靶点-疾病网络分析
- PubMed/ChEMBL/OpenTargets整合
- AI驱动的候选药物优先级排序

### 📊 知识库
- 罕见病知识图谱
- 文献自动监测（PubMed/arXiv）
- 临床试验数据整合（ClinicalTrials.gov）

### 🤖 多Agent系统
- CrewAI + 多Agent编排
- Claw Code架构模式移植（ToolRegistry/Auto-Compaction/Hook系统）
- 66个专业Skill覆盖医疗+科研+记忆

## 🚀 快速启动

```bash
# 线上正式站
open https://medichatrd.cloud

# 本地开发
git clone https://github.com/MoKangMedical/medichat-rd.git
cd medichat-rd
bash start.sh                       # → http://localhost:8001
```

## 🏥 支持病种

| 病种 | ICD-10 | 科室 | 状态 |
|------|--------|------|------|
| 重症肌无力 (MG) | G70.0 | 神经内科 | ✅ |
| 脊髓性肌萎缩症 (SMA) | G12.0 | 神经内科 | ✅ |
| 杜氏肌营养不良 (DMD) | G71.0 | 神经内科 | ✅ |
| 肌萎缩侧索硬化 (ALS) | G12.2 | 神经内科 | ✅ |
| 苯丙酮尿症 (PKU) | E70.0 | 遗传科 | ✅ |

## 📈 技术能力

- **AI引擎**：MIMO API（无限额度）+ OpenClaw框架
- **知识源**：PubMed / OMIM / ChEMBL / OpenTargets / ClinicalTrials.gov
- **已安装Skill**：66个（医疗11 + 药物10 + 基因组4 + 科研5 + Agent3 + 记忆6...）
- **架构模式**：从Claw Code提取五大模式（ToolRegistry / Auto-Compaction / Hook / Session / ConfigChain）

## 🔗 关联项目

- **MediSlim** — 消费医疗平台（[仓库](https://github.com/MoKangMedical/medi-slim)）

## 📄 License

MIT
