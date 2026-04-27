#!/bin/bash

set -euo pipefail

PROFILE="${1:-core}"
ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
RUNTIME_DIR="$ROOT_DIR/scientific-runtime"
ENV_DIR="$RUNTIME_DIR/.venv-science"
PYTHON_BIN="${PYTHON_BIN:-$(command -v python3.12 || true)}"
UV_BIN="${UV_BIN:-$(command -v uv || true)}"

if [[ -z "$PYTHON_BIN" ]]; then
  echo "❌ 未找到 python3.12，请先安装 Python 3.12。"
  exit 1
fi

if [[ -z "$UV_BIN" ]]; then
  echo "❌ 未找到 uv，请先安装 uv。"
  exit 1
fi

if [[ ! -f "$RUNTIME_DIR/pyproject.toml" ]]; then
  echo "❌ scientific-runtime/pyproject.toml 不存在。"
  exit 1
fi

CORE_PACKAGES=(
  "httpx>=0.28.1"
  "networkx>=3.4.2"
  "numpy>=2.2.6"
  "pandas>=2.2.3"
  "pydantic>=2.11.10"
  "python-dotenv>=1.1.0"
  "pyyaml>=6.0.3"
  "rich>=14.3.0"
  "typer>=0.24.1"
)

CHEM_PACKAGES=(
  "medchem>=2.0.5"
  "rdkit>=2025.9.6"
)

CLINICAL_PACKAGES=(
  "lifelines>=0.30.0"
  "polars>=1.35.2"
  "pyarrow>=22.0.0"
  "pyhealth>=2.0.1"
  "scikit-learn>=1.7.2"
  "scipy>=1.17.1"
  "statsmodels>=0.14.4"
)

DOCS_PACKAGES=(
  "jupyterlab>=4.4.1"
  "matplotlib>=3.10.8"
  "plotly>=6.0.1"
  "pymupdf>=1.25.5"
  "python-docx>=1.1.2"
  "seaborn>=0.13.2"
)

EXTRA_PACKAGES=()
case "$PROFILE" in
  core)
    ;;
  chem)
    EXTRA_PACKAGES+=("${CHEM_PACKAGES[@]}")
    ;;
  clinical)
    EXTRA_PACKAGES+=("${CLINICAL_PACKAGES[@]}")
    ;;
  docs)
    EXTRA_PACKAGES+=("${DOCS_PACKAGES[@]}")
    ;;
  full)
    EXTRA_PACKAGES+=("${CHEM_PACKAGES[@]}")
    EXTRA_PACKAGES+=("${CLINICAL_PACKAGES[@]}")
    EXTRA_PACKAGES+=("${DOCS_PACKAGES[@]}")
    ;;
  *)
    echo "❌ 不支持的 profile: $PROFILE"
    echo "可选: core | chem | clinical | docs | full"
    exit 1
    ;;
esac

export UV_PROJECT_ENVIRONMENT="$ENV_DIR"
export UV_SYSTEM_CERTS=1
export PIP_DISABLE_PIP_VERSION_CHECK=1

echo "🧪 MediChat-RD 科研执行层初始化中..."
echo "   Runtime: $RUNTIME_DIR"
echo "   Python : $PYTHON_BIN"
echo "   uv     : $UV_BIN"
echo "   Profile: $PROFILE"

"$UV_BIN" venv "$ENV_DIR" --python "$PYTHON_BIN" --allow-existing --seed
"$ENV_DIR/bin/pip" install --prefer-binary "${CORE_PACKAGES[@]}"

if [[ ${#EXTRA_PACKAGES[@]} -gt 0 ]]; then
  "$ENV_DIR/bin/pip" install --prefer-binary "${EXTRA_PACKAGES[@]}"
fi

echo ""
echo "✅ 科研执行层已同步"
echo "   Venv: $ENV_DIR"
echo ""
"$PYTHON_BIN" "$ROOT_DIR/scripts/check_scientific_runtime.py"
