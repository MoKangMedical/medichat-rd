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

编辑 `medichat-rd/.env` 或 `medichat-rd/backend/.env`:
```bash
# 关闭模拟模式，连接真正的Second Me
LOCAL_MODE=false
SECONDME_API=http://localhost:8002
# 是否让分身聊天时带上Second Me的L0知识检索
SECONDME_ENABLE_L0_RETRIEVAL=false
```

然后重启MediChat-RD后端即可。

说明：
- `3000` 是 Second Me 的网页前端
- `8002` 才是 MediChat-RD 需要调用的 Second Me 后端 API

### 4. SecondMe OAuth 平台联调

如果你要走开放平台 OAuth，而不是只用本地 Docker：

```bash
SECONDME_CLIENT_ID=your_secondme_client_id
SECONDME_CLIENT_SECRET=your_secondme_client_secret
SECONDME_REDIRECT_URI=http://localhost:8001/api/v1/secondme/oauth/callback
SECONDME_POST_LOGIN_REDIRECT=http://localhost:8001/index.html
SECONDME_OAUTH_SCOPES=userinfo,note.write
SECONDME_OAUTH_INCLUDE_SCOPE_IN_REDIRECT=true
SECONDME_AUTHORIZE_URL=https://go.second.me/oauth/
SECONDME_API_BASE=https://api.mindverse.com/gate/lab
SECONDME_SECRET_STORE_PATH=.secrets/secondme_oauth.json
```

完成后：
1. 打开 `http://localhost:8001/index.html`
2. 进入「互助社群」
3. 点击「连接 SecondMe」
4. 授权成功后，再点击「同步患者摘要」

联调检查点：
- 未登录：`/api/v1/secondme/oauth/status` 应返回 `state=unauthenticated`
- 登录成功：返回 `state=connected`，并能看到 `granted_scopes`
- token 失效：返回 `state=expired`，前端提示重新连接
- 生产环境不要把 access token / refresh token 打到日志；当前实现只在服务端 secret 文件中保存

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
| Bridge连接 | POST /api/v1/community/bridge | MediChat本地配对层，底层分身ID来自Second Me role |

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
