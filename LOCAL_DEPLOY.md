# MediChat-RD 本地部署指南

> 在Mac上运行完整平台 + Second Me数字分身

## 快速开始

### 1. 克隆仓库
```bash
git clone https://github.com/MoKangMedical/medichat-rd.git
cd medichat-rd
```

### 2. 安装依赖
```bash
cd backend
pip install fastapi uvicorn python-dotenv httpx
```

### 3. 启动MediChat-RD后端
```bash
cd backend
python3 -m uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

访问 http://localhost:8001 即可看到平台

---

## Second Me数字分身部署

### 1. 克隆Second Me
```bash
cd ~
git clone https://github.com/mindverse/Second-Me.git
cd Second-Me
```

### 2. 启动Second Me（Docker方式）
```bash
# 确保Docker Desktop已安装并启动
make docker-up
```

Second Me服务将运行在：
- 前端: http://localhost:3000
- 后端: http://localhost:8002

### 3. 连接MediChat-RD与Second Me

编辑 `medichat-rd/backend/.env`:
```bash
# 关闭模拟模式，连接真正的Second Me
LOCAL_MODE=false
SECONDEME_API=http://localhost:3000
```

然后重启MediChat-RD后端即可。

---

## 功能一览

### MediChat-RD平台
| 功能 | 路径 | 说明 |
|------|------|------|
| DeepRare诊断 | /api/v1/deeprare/diagnose | Nature论文架构 |
| 罕见病社群 | /api/v1/community/list | 18个互助圈 |
| 数字分身 | /api/v1/community/avatar/create | Second Me集成 |
| Bridge配对 | /api/v1/community/bridge | 同病相怜匹配 |

### Second Me集成
| 功能 | API端点 | 说明 |
|------|---------|------|
| 创建分身 | POST /api/v1/community/avatar/create | 自动创建AI分身 |
| 分身对话 | POST /api/v1/community/avatar/chat | 与分身对话 |
| 加入社群 | 自动 | 根据疾病类型自动入群 |
| Bridge连接 | POST /api/v1/community/bridge | 智能匹配病友 |

---

## 目录结构

```
medichat-rd/
├── backend/          # FastAPI后端
│   ├── main.py       # 主服务入口
│   ├── deeprare_api.py    # DeepRare诊断API
│   ├── community_api.py   # 社群API
│   └── secondme_integration.py  # Second Me集成
├── frontend/         # React前端
│   └── src/components/
│       ├── DeepRarePanel.jsx  # 诊断界面
│       └── CommunityPanel.jsx # 社群界面
├── agents/           # AI Agent模块
│   ├── hpo_extractor.py      # HPO表型提取
│   ├── knowledge_retriever.py # 知识检索
│   └── deeprare_orchestrator.py # 多Agent编排
└── docs/             # 文档
    ├── BUSINESS_PLAN.md      # 商业计划书
    └── secondme-integration.md  # Second Me集成方案
```

---

## 常见问题

### Q: 端口被占用怎么办？
```bash
# 查看占用
lsof -i :8001
# 杀掉进程
kill -9 <PID>
```

### Q: Second Me启动失败？
- 确保Docker Desktop已分配至少8GB内存
- Mac推荐16GB+才能流畅运行
- 检查: docker stats

### Q: 前端无法访问后端？
检查CORS配置，确保后端允许跨域:
```bash
curl http://localhost:8001/api/v1/health
```

---

## 联系支持
- GitHub Issues: https://github.com/MoKangMedical/medichat-rd/issues
- 创建者: 小林医生 (莫康医生)
