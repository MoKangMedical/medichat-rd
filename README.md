# MediChat - 医疗多Agent智能交互平台

## 项目简介
MediChat是一个基于多Agent协作的医疗智能交互平台，为患者提供专业的医疗咨询服务。

## 技术栈
- **后端**: Python 3.11+ / FastAPI / SQLAlchemy / PostgreSQL
- **Agent框架**: CrewAI + LangChain
- **LLM**: GPT-4 / Qwen-72B（可切换）
- **知识库**: Milvus + RAG
- **前端**: React + Ant Design + 微信小程序
- **部署**: Docker + K8s

## 项目结构
```
medical-agent-platform/
├── backend/           # FastAPI后端服务
├── agents/            # CrewAI Agent定义
├── frontend/          # React Web端
├── knowledge/         # 医疗知识库管理
├── docs/              # 文档
├── scripts/           # 部署脚本
└── docker-compose.yml # 一键部署
```

## 快速启动
```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置环境变量
cp .env.example .env

# 3. 启动服务
docker-compose up -d
```

## 商业模式
详见 docs/business-model.md
