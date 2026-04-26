# 达尔文棘轮 · 自动推送协议

> **铁律**：每次创新产出必须在10分钟内推送到GitHub，确保网站实时呈现最新能力。

## 推送清单（每次创新后自动执行）

### Step 1: 代码MVP
```
cd /root/[project-repo]
git add [new-module]/
git commit -m "feat: [模块名] - [一句话描述]"
git push origin main
```

### Step 2: 文档更新
```
cd /root/[project-repo]
# 更新README.md新增模块描述
git add README.md
git commit -m "docs: README新增[模块名]章节"
git push origin main
```

### Step 3: 理论文档
```
cd /root/.openclaw/workspace
git add projects/[THEORY].md
git commit -m "theory: [理论名] - [一句话描述]"
git push origin master
```

### Step 4: 记忆更新
```
更新 MEMORY.md + memory/YYYY-MM-DD.md
```

## GitHub仓库矩阵

| 仓库 | 分支 | 路径 | 内容 |
|------|------|------|------|
| medichat-rd | main | /root/medichat-rd/ | 罕见病诊断平台（含pharma-b2b）|
| medichat-rd | master | /root/.openclaw/workspace/ | 理论文档/MEMORY/projects |
| medi-slim | main | /root/medi-slim/ | 消费医疗平台（含enterprise-b2b）|
| medi-pharma | main | /root/medi-pharma/ | AI制药平台 |
| narrowgate | main | /root/narrowgate/ | 窄门AI大师引导 |

## GitHub Pages

| 仓库 | URL | 用途 |
|------|-----|------|
| medichat-rd | https://mokangmedical.github.io/medichat-rd/ | MediChat-RD主页 |
| medi-slim | 需配置 | MediSlim主页 |
| medi-pharma | 需配置 | MediPharma主页 |

## 自动化规则

1. **MVP完成后立即推送** — 不等"全部做完"
2. **README同步更新** — 每个新模块必须在README中有描述
3. **理论文档独立提交** — 理论和代码分开commit
4. **memory 30秒内更新** — 用户给的任何信息立即记录

---

*本协议由贾维斯执行，小林医生监督*
