# 💊 MediChat-RD

> **多Agent协作的罕见病智能诊断平台** — 用AI多Agent系统辅助罕见病诊断，缩短确诊时间

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9+-green.svg)]()
[![CrewAI](https://img.shields.io/badge/CrewAI-0.100+-orange.svg)]()
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-teal.svg)]()

---

## 🎯 一句话

**患者输入症状 → 6个AI Agent协作 → 30分钟输出结构化诊断报告**，将罕见病从平均 **5-7年确诊时间** 压缩到 **30分钟AI会诊**。

---

## 🏗️ 核心功能：6大Agent协作

```
┌─────────────┐    ┌─────────────┐    ┌─────────────────┐
│  ① 症状收集  │───▶│  ② 文献检索  │───▶│  ③ 鉴别诊断      │
│  Agent      │    │  Agent      │    │  Agent          │
└─────────────┘    └─────────────┘    └─────────────────┘
                                              │
       ┌──────────────┐    ┌──────────────┐   │
       │  ⑥ 患者教育   │◀──│  ⑤ 报告生成   │◀──│
       │  Agent       │    │  Agent       │   │
       └──────────────┘    └──────────────┘   │
                                       ┌──────────────┐
                                       │  ④ 专家会诊   │
                                       │  Agent       │
                                       └──────────────┘
```

| # | Agent | 职责 | 技术 |
|---|-------|------|------|
| ① | **症状收集Agent** | 智能问诊，收集主诉、现病史、既往史、家族史 | LLM + 症状树 |
| ② | **文献检索Agent** | 检索PubMed、OMIM、Orphanet等数据库 | PubMed API + OMIM API |
| ③ | **鉴别诊断Agent** | 基于症状+文献给出鉴别诊断列表 | LLM + 罕见病知识库 |
| ④ | **专家会诊Agent** | 模拟多专家（遗传学家、神经科、免疫科）讨论 | Multi-Agent Debate |
| ⑤ | **报告生成Agent** | 生成结构化诊断报告（ICD-10编码） | 模板引擎 + LLM |
| ⑥ | **患者教育Agent** | 用通俗语言解释病情、治疗方案、预后 | LLM + 医学知识图谱 |

---

## 🔧 技术架构

```
┌─────────────────────────────────────────────────────┐
│                    Frontend (React)                  │
│            聊天界面 + 诊断报告 + 可视化               │
└──────────────────────┬──────────────────────────────┘
                       │ REST API
┌──────────────────────▼──────────────────────────────┐
│                  FastAPI Backend                     │
│  ┌─────────────────────────────────────────────┐    │
│  │           CrewAI Orchestrator                │    │
│  │  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐  │    │
│  │  │Agent│ │Agent│ │Agent│ │Agent│ │Agent│  │    │
│  │  │  ①  │ │  ②  │ │  ③  │ │  ④  │ │  ⑤⑥ │  │    │
│  │  └──┬──┘ └──┬──┘ └──┬──┘ └──┬──┘ └──┬──┘  │    │
│  │     └───────┴───────┴───────┴───────┘      │    │
│  └─────────────────────────────────────────────┘    │
│                       │                              │
│  ┌────────────────────▼────────────────────────┐    │
│  │            External APIs                     │    │
│  │  PubMed · OMIM · Orphanet · HPO · ICD-10   │    │
│  └─────────────────────────────────────────────┘    │
│                       │                              │
│  ┌────────────────────▼────────────────────────┐    │
│  │           Data Layer                         │    │
│  │  rare-diseases.json · symptom-tree.json      │    │
│  │  Redis Cache · PostgreSQL                    │    │
│  └─────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────┘
```

**核心依赖：**
- **CrewAI** — 多Agent编排框架
- **PubMed E-utilities API** — 生物医学文献检索
- **OMIM API** — 人类孟德尔遗传数据库
- **Orphanet API** — 罕见病数据库
- **HPO (Human Phenotype Ontology)** — 表型本体
- **FastAPI** — 后端API服务
- **React + TypeScript** — 前端界面
- **PostgreSQL** — 持久化存储
- **Redis** — 缓存与会话管理

---

## 📊 罕见病数据库

内含 **30+ 种常见罕见病**的结构化数据，覆盖遗传、神经、免疫、代谢等领域：

| 疾病名称 | OMIM ID | 领域 | 发病率 |
|----------|---------|------|--------|
| 亨廷顿病 (Huntington's Disease) | #143100 | 神经 | 5-10/10万 |
| 囊性纤维化 (Cystic Fibrosis) | #219700 | 呼吸 | 1/2500-3500 |
| 杜氏肌营养不良 (Duchenne MD) | #310200 | 神经肌肉 | 1/3500-5000 |
| 马凡综合征 (Marfan Syndrome) | #154700 | 结缔组织 | 1/5000 |
| 苯丙酮尿症 (PKU) | #261600 | 代谢 | 1/10000-15000 |
| 肌萎缩侧索硬化 (ALS) | #105400 | 神经 | 2-3/10万 |
| 戈谢病 (Gaucher Disease) | #230800 | 代谢 | 1/40000-60000 |
| 法布里病 (Fabry Disease) | #301500 | 代谢 | 1/40000-117000 |
| 威尔逊病 (Wilson Disease) | #277900 | 代谢 | 1/30000 |
| 成骨不全症 (Osteogenesis Imperfecta) | #166200 | 骨骼 | 1/15000-20000 |
| 脊髓性肌萎缩症 (SMA) | #253300 | 神经肌肉 | 1/6000-10000 |
| 结节性硬化症 (TSC) | #191100 | 神经皮肤 | 1/6000-10000 |
| 雷特综合征 (Rett Syndrome) | #312750 | 神经发育 | 1/10000-15000 |
| Prader-Willi综合征 | #176270 | 遗传 | 1/15000-25000 |
| Angelman综合征 | #105830 | 遗传 | 1/12000-20000 |
| 威廉姆斯综合征 | #194050 | 遗传 | 1/7500-10000 |
| Noonan综合征 | #163950 | 遗传 | 1/1000-2500 |
| Alport综合征 | #301050 | 肾脏 | 1/5000-10000 |
| 遗传性出血性毛细血管扩张症 (HHT) | #187300 | 血管 | 1/5000-8000 |
| 白化病 (Albinism) | #203100 | 皮肤 | 1/17000-20000 |
| 先天性肾上腺皮质增生 (CAH) | #201910 | 内分泌 | 1/10000-15000 |
| 糖原累积病 (GSD) | #232200 | 代谢 | 1/20000-43000 |
| 肝豆状核变性 | #277900 | 神经代谢 | 1/30000 |
| Ehlers-Danlos综合征 | #130000 | 结缔组织 | 1/5000 |
| Stargardt病 | #248200 | 眼科 | 1/10000 |
| 视网膜色素变性 (RP) | #268000 | 眼科 | 1/4000 |
| 血友病A (Hemophilia A) | #306700 | 血液 | 1/5000-10000 |
| 血友病B (Hemophilia B) | #306900 | 血液 | 1/25000-30000 |
| 阵发性睡眠性血红蛋白尿 (PNH) | #311770 | 血液 | 1-2/10万 |
| Castleman病 | — | 血液/免疫 | 1-2/10万 |
| POEMS综合征 | — | 神经/血液 | 罕见 |

> 完整数据见 [`data/rare-diseases.json`](data/rare-diseases.json)，包含每种疾病的症状、诊断标准、治疗方案。

---

## 🚀 快速开始

### 环境要求

- Python 3.9+
- Node.js 18+ (前端)
- PostgreSQL 14+
- Redis 7+

### 安装

```bash
# 克隆仓库
git clone https://github.com/MoKangMedical/medichat-rd.git
cd medichat-rd

# 后端依赖
pip install -r requirements.txt

# 前端依赖
cd frontend && npm install && cd ..

# 配置环境变量
cp .env.example .env
# 编辑 .env 填入 API keys
```

### 配置

```bash
# .env 关键配置
OPENAI_API_KEY=sk-xxx          # 或其他LLM API key
PUBMED_API_KEY=xxx             # NCBI E-utilities API key
OMIM_API_KEY=xxx               # OMIM API key
DATABASE_URL=postgresql://...  # PostgreSQL连接
REDIS_URL=redis://localhost    # Redis连接
```

### 运行

```bash
# 启动后端
uvicorn backend.main:app --reload --port 8000

# 启动前端
cd frontend && npm run dev

# 或使用Docker
docker-compose up -d
```

### 运行Agent诊断流程

```python
from src.crew import MediChatCrew

crew = MediChatCrew()
result = crew.run_diagnosis(
    patient_input="我最近经常感到肌肉无力，走路容易摔倒，上下楼梯困难，已经持续了3个月"
)
print(result.report)
```

---

## 📁 项目结构

```
medichat-rd/
├── README.md                    # 项目说明
├── data/
│   ├── rare-diseases.json       # 30+罕见病数据库
│   └── symptom-tree.json        # 结构化症状树
├── src/
│   ├── agents/
│   │   ├── symptom_collector.py      # 症状收集Agent
│   │   ├── literature_searcher.py    # 文献检索Agent
│   │   └── differential_diagnosis.py # 鉴别诊断Agent
│   └── crew.py                  # CrewAI编排
├── examples/
│   └── case-study.md            # 3个诊断案例
├── backend/
│   ├── main.py                  # FastAPI入口
│   ├── rare_disease_api.py      # 罕见病API
│   ├── pubmed_service.py        # PubMed服务
│   └── ...
├── frontend/                    # React前端
├── docker-compose.yml           # Docker编排
└── .env.example                 # 环境变量模板
```

---

## 🔒 隐私合规

### HIPAA 合规

- ✅ 所有PHI（受保护健康信息）加密存储（AES-256）
- ✅ 传输层TLS 1.3加密
- ✅ 访问控制与审计日志
- ✅ 数据最小化原则
- ✅ 自动脱敏处理
- ✅ BAA（业务关联协议）覆盖所有第三方服务

### GDPR 合规

- ✅ 数据处理合法性基础（同意/合法利益）
- ✅ 数据主体权利（访问、删除、可携带）
- ✅ 数据保护影响评估（DPIA）
- ✅ 数据泄露通知机制（72小时内）
- ✅ DPO（数据保护官）指定

### 数据安全

- 患者数据本地化存储，不传输至第三方LLM
- LLM仅接收脱敏后的症状描述
- 所有API调用通过安全网关
- 定期安全审计与渗透测试

> 详见 [`PRIVACY_POLICY.md`](PRIVACY_POLICY.md) 和 [`SECURITY.md`](SECURITY.md)

---

## 📚 参考资源

- [OMIM - Online Mendelian Inheritance in Man](https://omim.org/)
- [Orphanet - 罕见病门户](https://www.orpha.net/)
- [HPO - Human Phenotype Ontology](https://hpo.jax.org/)
- [PubMed](https://pubmed.ncbi.nlm.nih.gov/)
- [NORD - National Organization for Rare Disorders](https://rarediseases.org/)
- [EURORDIS - 欧洲罕见病组织](https://www.eurordis.org/)

---

## 🤝 贡献

欢迎贡献！请查看 [CONTRIBUTING.md](CONTRIBUTING.md)。

## 📄 License

MIT License - 详见 [LICENSE](LICENSE)

---

> ⚠️ **免责声明：** MediChat-RD 仅供辅助诊断参考，不构成医疗建议。所有诊断结果需由执业医师确认。如有紧急情况，请立即就医。
