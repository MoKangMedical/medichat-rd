#!/bin/bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
RUNTIME_DIR="$ROOT_DIR/scientific-runtime"
ENV_DIR="$RUNTIME_DIR/.venv-science"

if [[ ! -x "$ENV_DIR/bin/python" ]]; then
  echo "❌ 科研执行环境尚未初始化，请先运行:"
  echo "   bash scripts/setup_scientific_runtime.sh core"
  exit 1
fi

if [[ $# -eq 0 ]]; then
  echo "用法:"
  echo "  bash scripts/run_scientific_workflow.sh python -c \"import pandas as pd; print(pd.__version__)\""
  exit 1
fi

export PATH="$ENV_DIR/bin:$PATH"

exec "$@"
