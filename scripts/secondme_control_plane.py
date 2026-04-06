#!/usr/bin/env python3
"""
Shared helpers for SecondMe Develop control-plane scripts.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

import httpx


BASE_URL = "https://app.mindos.com/gate/lab"
DEV_CREDENTIALS_PATH = Path.home() / ".secondme" / "dev_credentials"


class ControlPlaneError(Exception):
    pass


def load_dev_token() -> str:
    if not DEV_CREDENTIALS_PATH.exists():
        raise ControlPlaneError("Missing ~/.secondme/dev_credentials. Run Skills Auth first.")
    payload = json.loads(DEV_CREDENTIALS_PATH.read_text(encoding="utf-8"))
    token = payload.get("accessToken")
    if not token:
        raise ControlPlaneError("Missing accessToken in ~/.secondme/dev_credentials.")
    return token


def api_request(
    token: str,
    method: str,
    path: str,
    *,
    json_body: Optional[Dict[str, Any]] = None,
    extra_headers: Optional[Dict[str, str]] = None,
    timeout: int = 30,
) -> Dict[str, Any]:
    headers = {"Authorization": f"Bearer {token}"}
    if extra_headers:
        headers.update(extra_headers)
    if json_body is not None:
        headers["Content-Type"] = "application/json"
    with httpx.Client(timeout=timeout) as client:
        response = client.request(method, f"{BASE_URL}{path}", headers=headers, json=json_body)
    try:
        payload = response.json()
    except ValueError as exc:
        raise ControlPlaneError(f"Non-JSON response from {path}: HTTP {response.status_code}") from exc
    if response.status_code >= 400 or payload.get("code") != 0:
        raise ControlPlaneError(
            f"{path} failed: HTTP {response.status_code}, code={payload.get('code')}, message={payload.get('message') or payload}"
        )
    return payload["data"]


def list_apps(token: str) -> list[Dict[str, Any]]:
    data = api_request(token, "GET", "/api/applications/external/list")
    if isinstance(data, list):
        return data
    for key in ("items", "list", "applications"):
        if isinstance(data.get(key), list):
            return data[key]
    return []


def list_integrations(token: str) -> list[Dict[str, Any]]:
    data = api_request(token, "GET", "/api/integrations/list?page=1&pageSize=100")
    if isinstance(data, list):
        return data
    for key in ("items", "list", "integrations"):
        if isinstance(data.get(key), list):
            return data[key]
    return []


def match_app_id(apps: list[Dict[str, Any]], *, client_id: Optional[str], app_id: Optional[str]) -> str:
    if app_id:
        return app_id
    if not client_id:
        raise ControlPlaneError("Either --app-id or --client-id is required.")
    for app in apps:
        if app.get("clientId") == client_id or app.get("appId") == client_id or app.get("id") == client_id:
            return app.get("appId") or app.get("id")
    raise ControlPlaneError(f"No external app matched clientId={client_id}.")


def upload_cdn_file(token: str, file_path: Path) -> Dict[str, str]:
    if not file_path.exists():
        raise ControlPlaneError(f"Asset file does not exist: {file_path}")
    headers = {
        "Authorization": f"Bearer {token}",
        "token": token,
    }
    with file_path.open("rb") as handle, httpx.Client(timeout=60) as client:
        response = client.post(
            f"{BASE_URL}/api/cdn/upload",
            headers=headers,
            files={"file": (file_path.name, handle)},
        )
    try:
        payload = response.json()
    except ValueError as exc:
        raise ControlPlaneError(f"CDN upload returned non-JSON: HTTP {response.status_code}") from exc
    if response.status_code >= 400 or payload.get("code") != 0:
        raise ControlPlaneError(
            f"CDN upload failed for {file_path}: HTTP {response.status_code}, code={payload.get('code')}, message={payload.get('message') or payload}"
        )
    data = payload.get("data") or {}
    url = data.get("url")
    key = data.get("key")
    if not url:
        raise ControlPlaneError(f"CDN upload for {file_path} returned no URL.")
    return {"url": url, "key": key or ""}
