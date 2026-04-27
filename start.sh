#!/bin/bash
# MediChat-RD 一键启动脚本
# 用法: bash start.sh

set -e

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"

echo "🧬 MediChat-RD 启动中..."

# 检查Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 需要Python 3.10+"
    exit 1
fi

# 安装依赖
echo "📦 检查依赖..."
python3 -m pip install --quiet fastapi uvicorn python-dotenv httpx openai 2>/dev/null || true

if [ -d "$FRONTEND_DIR" ] && command -v npm >/dev/null 2>&1; then
    echo "🎨 构建前端..."
    (cd "$FRONTEND_DIR" && npm run build >/dev/null 2>&1 || true)
fi

# 启动后端
echo "🚀 启动后端服务 (端口 8001)..."
cd "$BACKEND_DIR"
python3 -m uvicorn main:app --host 0.0.0.0 --port 8001 --reload &
BACKEND_PID=$!

echo ""
echo "✅ MediChat-RD 已启动!"
echo ""
echo "🌐 访问: http://localhost:8001"
echo "📄 DeepRare诊断: http://localhost:8001 → 点击侧栏"
echo "🤝 罕见病社群: http://localhost:8001 → 点击互助社群"
echo ""
echo "按 Ctrl+C 停止服务"

# 等待
wait $BACKEND_PID
