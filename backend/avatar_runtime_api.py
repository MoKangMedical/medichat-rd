"""
Avatar runtime management API.

目标：
- 查看当前 primary/fallback provider
- 查看 provider 健康状态
- 通过后台安全切换 LocalRuntime / SecondMeRuntime
"""

from __future__ import annotations

import os
from typing import Optional

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

from avatar_service import get_avatar_service
from avatar_providers import AVATAR_PROVIDER_DETAILS


router = APIRouter(prefix="/api/v1/platform/avatar-runtime", tags=["患者平台"])

PLATFORM_ADMIN_TOKEN = os.getenv("PLATFORM_ADMIN_TOKEN", "").strip()


class AvatarRuntimeUpdateInput(BaseModel):
    primary_provider: str = Field(..., description="主运行时 provider")
    fallback_provider: str = Field(..., description="兜底 provider")


def _require_admin_token(x_admin_token: Optional[str]) -> None:
    if not PLATFORM_ADMIN_TOKEN:
        raise HTTPException(
            status_code=403,
            detail="服务端未配置 PLATFORM_ADMIN_TOKEN，暂不允许切换运行时。",
        )
    if not x_admin_token or x_admin_token != PLATFORM_ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="后台切换口令无效。")


async def _build_snapshot() -> dict:
    service = get_avatar_service()
    snapshot = await service.get_runtime_snapshot()
    snapshot["switch_enabled"] = bool(PLATFORM_ADMIN_TOKEN)
    snapshot["switch_header"] = "X-Admin-Token"
    snapshot["provider_catalog"] = AVATAR_PROVIDER_DETAILS
    return snapshot


@router.get("")
async def get_avatar_runtime_status():
    return {"ok": True, "runtime": await _build_snapshot()}


@router.post("")
async def update_avatar_runtime(
    input_data: AvatarRuntimeUpdateInput,
    x_admin_token: Optional[str] = Header(default=None, alias="X-Admin-Token"),
):
    _require_admin_token(x_admin_token)
    service = get_avatar_service()
    try:
        service.set_runtime_config(
            primary_provider=input_data.primary_provider,
            fallback_provider=input_data.fallback_provider,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        "ok": True,
        "message": "分身运行时已切换。",
        "runtime": await _build_snapshot(),
    }
