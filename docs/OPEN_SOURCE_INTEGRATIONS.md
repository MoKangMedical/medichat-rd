# MediChat-RD 开源功能集成清单

> 从GitHub开源罕见病项目中提取的核心功能，将嵌入MediChat-RD平台

---

## 🏆 精选开源项目

### 1. DiagnosisAssistant ⭐8 — HPO表型提取+Orphanet匹配
- **功能亮点**: PhenoTagger自动提取HPO术语 + Orphanet疾病匹配
- **可复用**: HPO术语库加载、症状搜索、疾病匹配逻辑
- **集成点**: DeepRare诊断模块

### 2. OrphaMind — 4层幻觉防护+RAG知识库
- **功能亮点**: 
  - 4层幻觉防护（Orphanet验证→症状索引→文献支持→置信度惩罚）
  - 87,848文档RAG知识库
  - OCR临床笔记扫描
  - 实验室检验值自动解析
  - SQLite患者历史
- **可复用**: 幻觉防护机制、RAG架构、OCR模块
- **集成点**: DeepRare诊断引擎

### 3. RarePath AI — 多Agent协作诊断
- **功能亮点**:
  - 编排器Agent协调6个子Agent
  - PubMed文献检索Agent
  - 临床试验匹配Agent
  - 专科医生查找Agent
  - 可观测性（日志/追踪/指标）
- **可复用**: 多Agent架构、临床试验匹配
- **集成点**: Agent编排层

### 4. MedAtlas AI — RAG实时知识检索
- **功能亮点**:
  - 混合检索引擎（语义+关键词）
  - 幻觉防护（基于文档验证）
  - Streamlit医学界面
- **可复用**: 检索架构、界面设计
- **集成点**: 知识检索模块

### 5. RDRF ⭐18 — 罕见病患者注册框架
- **功能亮点**: 可重用数据元素、动态表单、运行时配置
- **可复用**: 患者注册表结构、数据模型
- **集成点**: 患者管理模块

---

## 🔧 集成功能清单

### A. HPO表型提取增强
| 功能 | 来源 | 优先级 | 说明 |
|------|------|--------|------|
| PhenoTagger集成 | DiagnosisAssistant | P0 | 自动从自由文本提取HPO |
| 完整HPO本体加载 | DiagnosisAssistant | P0 | 加载hp.obo文件 |
| 同义词扩展搜索 | DiagnosisAssistant | P1 | 模糊匹配同义术语 |
| 超类术语推荐 | DiagnosisAssistant | P1 | 推荐上级术语 |

### B. 幻觉防护系统
| 功能 | 来源 | 优先级 | 说明 |
|------|------|--------|------|
| 4层验证 | OrphaMind | P0 | Orphanet验证→症状索引→文献→置信度 |
| Orphanet反向索引 | OrphaMind | P0 | 11,456种疾病索引 |
| RAG知识库 | OrphaMind | P1 | GeneReviews/OMIM文献 |
| 置信度惩罚 | OrphaMind | P1 | 无法验证的假设降权 |

### C. 多Agent协作
| 功能 | 来源 | 优先级 | 说明 |
|------|------|--------|------|
| 编排器模式 | RarePath AI | P0 | 协调诊断流程 |
| 文献检索Agent | RarePath AI | P0 | PubMed自动检索 |
| 临床试验匹配 | RarePath AI | P1 | ClinicalTrials.gov对接 |
| 专科医生查找 | RarePath AI | P2 | 推荐相关专科 |

### D. 输入增强
| 功能 | 来源 | 优先级 | 说明 |
|------|------|--------|------|
| OCR临床笔记 | OrphaMind | P1 | 扫描图片/PDF |
| 实验室检验解析 | OrphaMind | P0 | 自动提取检验值 |
| 输入验证 | OrphaMind | P1 | 防止无效输入/注入攻击 |
| 症状选择器 | OrphaMind | P1 | 预设症状标签 |

### E. 患者管理
| 功能 | 来源 | 优先级 | 说明 |
|------|------|--------|------|
| 病例持久化 | OrphaMind | P0 | SQLite存储诊断历史 |
| 患者注册 | RDRF | P1 | 动态表单注册 |
| 历史浏览 | OrphaMind | P1 | 按患者ID搜索 |
| 报告生成 | RarePath AI | P1 | 医生可读的诊断报告 |

---

## 📋 集成计划

### Phase 1: 核心增强（1-2天）
- [ ] 集成OrphaMind的4层幻觉防护
- [ ] 增强HPO表型提取（同义词+超类）
- [ ] 实现实验室检验值解析
- [ ] 添加病例持久化存储

### Phase 2: 多Agent升级（3-5天）
- [ ] 实现编排器Agent模式
- [ ] 集成PubMed文献检索Agent
- [ ] 添加临床试验自动匹配
- [ ] 增强输入验证机制

### Phase 3: 高级功能（1-2周）
- [ ] OCR临床笔记扫描
- [ ] 症状选择器UI
- [ ] 患者注册系统
- [ ] 诊断报告生成

---

## 🎯 集成后MediChat-RD能力矩阵

```
当前状态                    增强后
├── DeepRare诊断           ├── DeepRare诊断
│   ├── HPO表型提取        │   ├── HPO表型（完整本体）
│   ├── 知识检索           │   ├── RAG知识库（8.7万文档）
│   └── 自反思循环         │   ├── 4层幻觉防护
│                          │   └── 实验室检验解析
├── 罕见病社群             ├── 罕见病社群
│   ├── 18个互助圈         │   ├── 18+互助圈
│   ├── AI数字分身         │   ├── AI数字分身
│   └── Bridge配对         │   ├── Bridge配对
│                          │   └── 患者注册系统
├── 药物重定位             ├── 药物重定位
└── 知识库                 │   └── 临床试验匹配
                           └── 知识库
                               ├── 完整Orphanet（11,456种）
                               ├── PubMed文献
                               └── GeneReviews
```

---

## 📚 参考资源

- [DiagnosisAssistant](https://github.com/demoronator/DiagnosisAssistant) — HPO+Orphanet
- [OrphaMind](https://github.com/Satyam-Jsr/OrphaMind) — 4层防护+RAG
- [RarePath AI](https://github.com/kemval/rarepath-ai) — 多Agent架构
- [MedAtlas AI](https://github.com/harshalDharpure/MedAtlas-AI) — RAG检索
- [RDRF](https://github.com/muccg/rdrf) — 患者注册
- [DeepRare](https://www.nature.com/articles/s41586-025-10097-9) — Nature论文

---

*最后更新: 2026年4月5日*
