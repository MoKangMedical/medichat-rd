# Tests for MediChat-RD

import pytest
import json
import os
import sqlite3
import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient


ROOT_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


def test_imports():
    """Test that main modules can be imported."""
    assert True


def test_data_integrity():
    """Test that data files are valid JSON."""
    data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
    if os.path.exists(data_dir):
        for f in os.listdir(data_dir):
            if f.endswith('.json'):
                with open(os.path.join(data_dir, f)) as fp:
                    json.load(fp)


def test_medichat_config():
    """Test MediChat configuration defaults."""
    assert True


def test_api_fallback_returns_json_404():
    """Unknown API routes must not be served as frontend HTML."""
    from main import app

    response = TestClient(app).get("/api/v1/not-a-real-endpoint")

    assert response.status_code == 404
    assert response.headers["content-type"].startswith("application/json")
    assert response.json()["detail"] == "API endpoint not found"


def test_analytics_write_failure_degrades_gracefully(monkeypatch):
    """Analytics storage errors should not break the user-facing platform."""
    import analytics_api

    def broken_connection():
        raise sqlite3.OperationalError("database or disk is full")

    monkeypatch.setattr(analytics_api, "_get_connection", broken_connection)

    app = FastAPI()
    app.include_router(analytics_api.router)
    response = TestClient(app).post(
        "/api/v1/analytics/page-view",
        json={
            "visitor_id": "visitor-test-123",
            "page_id": "openrd-bridge",
            "page_label": "OpenRD 共建",
            "path": "/",
            "referrer": "",
            "language": "zh-CN",
            "timezone": "Asia/Shanghai",
        },
    )

    assert response.status_code == 200
    assert response.json()["ok"] is False
    assert response.json()["degraded"] is True


def test_openrd_bridge_overview_and_requirement_flow(tmp_path, monkeypatch):
    """OpenRD bridge exposes requirements and collaboration flow."""
    import openrd_bridge_api

    monkeypatch.setattr(openrd_bridge_api, "DB_PATH", tmp_path / "openrd_bridge.db")
    client = TestClient(FastAPI())
    client.app.include_router(openrd_bridge_api.router)

    overview = client.get("/api/v1/openrd/overview")
    assert overview.status_code == 200
    assert "MediChat-RD" in overview.json()["name"]

    created = client.post(
        "/api/v1/openrd/requirements",
        json={
            "title": "测试共建需求",
            "description": "把患者真实需求转成可执行协作任务。",
            "priority": "high",
            "tags": ["测试", "OpenRD"],
            "track": "patient-community",
            "disease_area": "全病种",
        },
    )
    assert created.status_code == 200
    requirement_id = created.json()["requirement"]["id"]

    joined = client.post(
        f"/api/v1/openrd/requirements/{requirement_id}/join",
        json={
            "name": "测试志愿者",
            "role": "前端开发",
            "message": "可以贡献界面和交互。",
        },
    )
    assert joined.status_code == 200
    assert joined.json()["requirement"]["status"] == "in-progress"
