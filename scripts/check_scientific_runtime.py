#!/usr/bin/env python3
"""Inspect the dedicated scientific runtime without importing heavy packages in the app process."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Dict, List


PROJECT_ROOT = Path(__file__).resolve().parent.parent
RUNTIME_DIR = PROJECT_ROOT / "scientific-runtime"
VENV_DIR = RUNTIME_DIR / ".venv-science"
VENV_PYTHON = VENV_DIR / "bin" / "python"
PYTHON312_PATH = shutil.which("python3.12")
UV_PATH = shutil.which("uv")

PROFILE_MATRIX = {
    "core": {
        "label": "核心科学计算",
        "description": "DataFrame、统计计算、网络分析与基础机器学习。",
        "imports": {
            "numpy": "numpy",
            "pandas": "pandas",
            "networkx": "networkx",
        },
    },
    "chem": {
        "label": "药物化学与筛选",
        "description": "RDKit / MedChem，用于候选分子整理、过滤和结构分析。",
        "imports": {
            "rdkit": "rdkit",
            "medchem": "medchem",
        },
    },
    "clinical": {
        "label": "临床研究与队列建模",
        "description": "PyHealth + 生存分析 + 统计建模。",
        "imports": {
            "pyhealth": "pyhealth",
            "lifelines": "lifelines",
            "polars": "polars",
            "pyarrow": "pyarrow",
            "sklearn": "scikit-learn",
            "scipy": "scipy",
            "statsmodels": "statsmodels",
        },
    },
    "docs": {
        "label": "科研文档与可视化",
        "description": "Jupyter、绘图、Docx/PDF 输出。",
        "imports": {
            "matplotlib": "matplotlib",
            "plotly": "plotly",
            "docx": "python-docx",
            "fitz": "pymupdf",
        },
    },
}


def _run_command(command: List[str]) -> Dict[str, str]:
    try:
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=20,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"ok": False, "stdout": "", "stderr": str(exc)}

    return {
        "ok": completed.returncode == 0,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
    }


def _probe_imports(python_bin: Path, modules: Dict[str, str]) -> Dict[str, bool]:
    module_names = list(modules.keys())
    snippet = (
        "import importlib.util, json\n"
        f"modules = {json.dumps(module_names)}\n"
        "print(json.dumps({name: bool(importlib.util.find_spec(name)) for name in modules}))"
    )
    result = _run_command([str(python_bin), "-c", snippet])
    if not result["ok"] or not result["stdout"]:
        return {name: False for name in module_names}
    try:
        return json.loads(result["stdout"])
    except json.JSONDecodeError:
        return {name: False for name in module_names}


def _detect_profile_status() -> List[Dict[str, object]]:
    profiles = []
    for slug, config in PROFILE_MATRIX.items():
        checks = _probe_imports(VENV_PYTHON, config["imports"]) if VENV_PYTHON.exists() else {
            name: False for name in config["imports"]
        }
        installed = all(checks.values()) if checks else False
        profiles.append(
            {
                "slug": slug,
                "label": config["label"],
                "description": config["description"],
                "packages": list(config["imports"].values()),
                "checks": checks,
                "installed": installed,
            }
        )
    return profiles


def _state_from_profiles(venv_ready: bool, profiles: List[Dict[str, object]]) -> Dict[str, object]:
    installed = [item["slug"] for item in profiles if item["installed"]]
    if not venv_ready:
        return {"state": "not_bootstrapped", "state_label": "未初始化", "ready": False, "installed_profiles": installed}
    if "core" not in installed:
        return {"state": "partial", "state_label": "环境未完整", "ready": False, "installed_profiles": installed}
    advanced_profiles = {"chem", "clinical", "docs"} & set(installed)
    if len(advanced_profiles) == 3:
        return {"state": "full_ready", "state_label": "完整科研环境", "ready": True, "installed_profiles": installed}
    if advanced_profiles:
        return {"state": "advanced_ready", "state_label": "高级科研环境", "ready": True, "installed_profiles": installed}
    return {"state": "core_ready", "state_label": "核心科学环境", "ready": True, "installed_profiles": installed}


def collect_status() -> Dict[str, object]:
    uv_version = _run_command([UV_PATH, "--version"]) if UV_PATH else {"ok": False, "stdout": "", "stderr": ""}
    system_python = _run_command([PYTHON312_PATH, "--version"]) if PYTHON312_PATH else {"ok": False, "stdout": "", "stderr": ""}

    venv_version = _run_command([str(VENV_PYTHON), "--version"]) if VENV_PYTHON.exists() else {
        "ok": False,
        "stdout": "",
        "stderr": "",
    }

    venv_matches = venv_version["ok"] and venv_version["stdout"].startswith("Python 3.12")
    profiles = _detect_profile_status()
    state = _state_from_profiles(venv_matches, profiles)

    return {
        "required_python": "3.12",
        "runtime_dir": str(RUNTIME_DIR),
        "pyproject_path": str(RUNTIME_DIR / "pyproject.toml"),
        "system_python": {
            "path": PYTHON312_PATH or "",
            "available": bool(PYTHON312_PATH),
            "version": system_python["stdout"],
        },
        "uv": {
            "installed": bool(UV_PATH),
            "path": UV_PATH or "",
            "version": uv_version["stdout"],
        },
        "venv": {
            "path": str(VENV_DIR),
            "exists": VENV_DIR.exists(),
            "python_path": str(VENV_PYTHON),
            "version": venv_version["stdout"],
            "matches_required": bool(venv_matches),
        },
        "profiles": profiles,
        "bootstrap_commands": [
            {
                "label": "初始化核心环境",
                "command": "bash scripts/setup_scientific_runtime.sh core",
            },
            {
                "label": "初始化完整科研环境",
                "command": "bash scripts/setup_scientific_runtime.sh full",
            },
        ],
        "run_examples": [
            "bash scripts/run_scientific_workflow.sh python -c \"import pandas as pd; print(pd.__version__)\"",
            "bash scripts/run_scientific_workflow.sh python -c \"from rdkit import Chem; print(Chem.MolFromSmiles('CCO') is not None)\"",
        ],
        "notes": [
            "Web 服务继续跑在现有应用环境，科研重包单独进 scientific-runtime/.venv-science。",
            "DiffDock skill 已安装到 Codex，但真实 docking 模型、权重和 GPU 仍建议走独立容器或服务。",
        ],
        **state,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true", help="Output machine-readable JSON only.")
    args = parser.parse_args()

    payload = collect_status()
    if args.json:
        print(json.dumps(payload, ensure_ascii=False))
        return 0

    print("== MediChat-RD Scientific Runtime ==")
    print(f"Runtime dir : {payload['runtime_dir']}")
    print(f"System 3.12 : {payload['system_python']['version'] or 'missing'}")
    print(f"uv          : {payload['uv']['version'] or 'missing'}")
    print(f"Venv        : {payload['venv']['version'] or 'not created'}")
    print(f"State       : {payload['state_label']}")
    print("")
    for profile in payload["profiles"]:
        marker = "OK" if profile["installed"] else "--"
        packages = ", ".join(profile["packages"])
        print(f"[{marker}] {profile['label']}: {packages}")
    if not payload["ready"]:
        print("")
        print("Next:")
        for item in payload["bootstrap_commands"]:
            print(f"- {item['label']}: {item['command']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
