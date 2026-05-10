from __future__ import annotations

import os
from typing import Any

import httpx


WECHAT_CODE2SESSION_URL = "https://api.weixin.qq.com/sns/jscode2session"


class WeChatMiniProgramClient:
    def __init__(
        self,
        app_id: str | None = None,
        app_secret: str | None = None,
        timeout: float = 10.0,
    ) -> None:
        self.app_id = app_id or os.getenv("WECHAT_APP_ID", "")
        self.app_secret = app_secret or os.getenv("WECHAT_APP_SECRET", "")
        self.timeout = timeout

    @property
    def configured(self) -> bool:
        return bool(self.app_id and self.app_secret)

    async def code_to_session(self, code: str) -> dict[str, Any]:
        if not self.configured:
            raise RuntimeError("WECHAT_APP_ID / WECHAT_APP_SECRET not configured")

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                WECHAT_CODE2SESSION_URL,
                params={
                    "appid": self.app_id,
                    "secret": self.app_secret,
                    "js_code": code,
                    "grant_type": "authorization_code",
                },
            )
            response.raise_for_status()
            payload = response.json()

        if payload.get("errcode"):
            raise RuntimeError(
                f"WeChat code2Session failed: {payload.get('errcode')} {payload.get('errmsg', '')}"
            )

        return payload
