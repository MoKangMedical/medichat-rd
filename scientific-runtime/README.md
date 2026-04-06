# Scientific Runtime

MediChat-RD 的 Web 服务目前仍可继续运行在现有应用环境里；这个目录单独承载更重的科研执行层。

设计目标：

- 固定 `Python 3.12`
- 统一使用 `uv` 管理环境和锁文件
- 把 Web 服务依赖和科研重包拆开，避免前端/接口启动被科研包拖慢
- 让 `RDKit / PyHealth / Literature Review / Clinical Decision Support` 这类能力有可验证的执行环境

## 快速开始

在仓库根目录执行：

```bash
bash scripts/setup_scientific_runtime.sh core
```

如果要打开更完整的药物研发 / 临床研究 / 文档输出能力：

```bash
bash scripts/setup_scientific_runtime.sh full
```

## 运行命令

```bash
bash scripts/run_scientific_workflow.sh python -c "import sys; print(sys.version)"
bash scripts/run_scientific_workflow.sh python -c "import rdkit, pandas; print('ok')"
```

## Profile 说明

- `core`: 基础科学计算栈，适合特征工程、网络分析、结构化数据处理
- `chem`: RDKit + MedChem，适合药物筛选、分子过滤、候选化合物整理
- `clinical`: PyHealth + 生存分析/统计建模，适合队列研究与临床建模
- `docs`: 科学绘图、Jupyter、PDF/Docx 输出

## 当前边界

- `DiffDock` skill 已接入 Codex，但真实 docking 模型、权重和 GPU 资源建议继续走独立服务或专门容器，不塞进当前 Web 服务环境。
- 平台会通过 `/api/v1/platform/scientific-skills` 暴露当前 runtime 是否完成初始化、哪些 profile 已就绪、以及对应启动命令。
