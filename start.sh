#!/bin/bash
# MediChat-RD 一键启动脚本
# 用法: bash start.sh

set -e

echo "🧬 MediChat-RD 启动中..."

# 检查Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 需要Python 3.10+"
    exit 1
fi

# 安装依赖
echo "📦 检查依赖..."
cd "$(dirname "$0")/backend"
pip install --quiet fastapi uvicorn python-dotenv 2>/dev/null || true

# 启动后端
echo "🚀 启动后端服务 (端口 8001)..."
cd "$(dirname "$0")/backend"
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
