#!/bin/bash
# MediChat-RD 启动脚本
set -e

cd "$(dirname "$0")/.."

echo "🚀 启动 MediChat-RD..."

# 后端 + 前端静态服务
source venv/bin/activate
uvicorn demo_server:app --host 0.0.0.0 --port 8000
