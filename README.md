# MediChat-RD — 罕见病AI诊疗平台

> 基于AI的罕见病在线辅助诊疗系统，4C诊疗体系（Connect→Consult→Care→Community）

## 🎯 使命

让每一个罕见病患者都能获得专业、可及、持续的医疗服务。

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
# 罕见病评估平台
cd medvi-model && python3 app.py    # → localhost:8080

# MediSlim消费医疗（关联项目）
cd medi-slim && python3 app.py      # → localhost:8090
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
