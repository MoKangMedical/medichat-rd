"""
Provider adapters for avatar runtimes.

目标：
- SecondMe 只是一个 provider
- Local runtime 作为兜底和未来自有底座起点
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import json
import os
import uuid

from avatar_core import PatientAvatar


LOCAL_MODE = os.getenv("LOCAL_MODE", "true").lower() == "true"
SECONDME_API = os.getenv("SECONDME_API") or os.getenv("SECONDEME_API") or "http://localhost:8002"
SECONDME_ENABLE_L0 = os.getenv("SECONDME_ENABLE_L0_RETRIEVAL", "false").lower() == "true"
SECONDME_HTTP_TIMEOUT_SECONDS = float(os.getenv("SECONDME_HTTP_TIMEOUT_SECONDS", "90"))
SECONDME_CHAT_MAX_TOKENS = int(os.getenv("SECONDME_CHAT_MAX_TOKENS", "300"))
SECONDME_ROLE_MARKER = "[MediChat-RD Avatar]"
AVATAR_PROVIDER_PRIMARY = os.getenv(
    "AVATAR_PROVIDER_PRIMARY",
    "local" if LOCAL_MODE else "secondme",
)
AVATAR_PROVIDER_FALLBACK = os.getenv("AVATAR_PROVIDER_FALLBACK", "local")


class AvatarProviderError(Exception):
    pass


@dataclass
class AvatarProvisionResult:
    provider_avatar_id: str
    bio: Optional[str] = None
    memory_summary: Optional[str] = None
    runtime_metadata: Dict[str, Any] = field(default_factory=dict)


class AvatarProvider(ABC):
    key = "base"

    @abstractmethod
    async def health_check(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def create_avatar(
        self,
        *,
        avatar: PatientAvatar,
        patient_data: Dict[str, Any],
    ) -> AvatarProvisionResult:
        raise NotImplementedError

    @abstractmethod
    async def chat(
        self,
        *,
        avatar: PatientAvatar,
        message: str,
    ) -> str:
        raise NotImplementedError


def build_memory_text(patient_data: Dict[str, Any]) -> str:
    parts = []
    if patient_data.get("disease_type"):
        parts.append(f"我是一位{patient_data['disease_type']}患者。")
    if patient_data.get("diagnosis"):
        parts.append(f"我的诊断结果是：{patient_data['diagnosis']}")
    if patient_data.get("symptoms"):
        parts.append(f"我的主要症状包括：{patient_data['symptoms']}")
    if patient_data.get("treatment_history"):
        parts.append(f"我的治疗经历：{patient_data['treatment_history']}")
    if patient_data.get("age"):
        parts.append(f"我今年{patient_data['age']}岁。")
    parts.append("我希望通过分享自己的经历，帮助更多同病相怜的朋友。")
    parts.append("我也希望能从其他患者那里获得支持和建议。")
    return "\n".join(parts)


def build_default_bio(patient_data: Dict[str, Any]) -> str:
    return (
        f"一位{patient_data.get('disease_type', '罕见病')}患者，"
        "愿意分享经历，帮助同病伙伴。"
    )


def build_system_prompt(patient_data: Dict[str, Any], memory_text: str) -> str:
    nickname = patient_data.get("nickname", "匿名患者")
    disease_type = patient_data.get("disease_type", "罕见病")
    return "\n".join(
        [
            f"你是 {nickname} 的数字分身。",
            f"你是一位 {disease_type} 患者/家属，在罕见病互助社群中交流。",
            "你的目标是分享真实、克制、温暖的患者经验，不冒充医生，不给确定性诊断。",
            "如果涉及用药、治疗调整、急症风险，请明确建议咨询专业医生。",
            "说话风格要像有亲身经历的病友，简洁、真诚、共情。",
            "",
            "以下是你的已知背景：",
            memory_text,
        ]
    )


class LocalAvatarProvider(AvatarProvider):
    key = "local"

    async def health_check(self) -> bool:
        return True

    async def create_avatar(
        self,
        *,
        avatar: PatientAvatar,
        patient_data: Dict[str, Any],
    ) -> AvatarProvisionResult:
        memory_text = build_memory_text(patient_data)
        return AvatarProvisionResult(
            provider_avatar_id=f"local_{avatar.avatar_id}",
            bio=build_default_bio(patient_data),
            memory_summary=memory_text[:200],
            runtime_metadata={"mode": "local_runtime"},
        )

    async def chat(
        self,
        *,
        avatar: PatientAvatar,
        message: str,
    ) -> str:
        return (
            f"你好，我是{avatar.nickname}。"
            f"作为一位{avatar.disease_type}患者，我理解你的感受。"
            "如果你想了解我的治疗经历，我很乐意和你聊聊。"
        )


class SecondMeAvatarProvider(AvatarProvider):
    key = "secondme"

    def __init__(self, base_url: str = SECONDME_API):
        self.base_url = base_url
        self._http = None
        self._http_sync = None
        if not LOCAL_MODE:
            try:
                import httpx

                self._http = httpx.AsyncClient(
                    base_url=base_url,
                    timeout=SECONDME_HTTP_TIMEOUT_SECONDS,
                )
                self._http_sync = httpx.Client(
                    base_url=base_url,
                    timeout=SECONDME_HTTP_TIMEOUT_SECONDS,
                )
            except ImportError:
                self._http = None
                self._http_sync = None

    def _ensure_enabled(self) -> None:
        if LOCAL_MODE or self._http is None:
            raise AvatarProviderError("SecondMe runtime provider is not enabled.")

    def _build_role_metadata(self, patient_data: Dict[str, Any], bio: str) -> str:
        metadata = {
            "patient_id": patient_data["patient_id"],
            "nickname": patient_data.get("nickname", "匿名"),
            "disease_type": patient_data.get("disease_type", ""),
            "age": patient_data.get("age"),
            "bio": bio,
            "local_avatar_id": patient_data.get("avatar_id"),
        }
        return f"{SECONDME_ROLE_MARKER}\n{json.dumps(metadata, ensure_ascii=False, separators=(',', ':'))}"

    def _extract_chat_reply(self, payload: Dict[str, Any]) -> str:
        if not isinstance(payload, dict):
            return ""

        choices = payload.get("choices") or []
        if choices:
            choice0 = choices[0] or {}
            message = choice0.get("message") or {}
            if isinstance(message, dict) and message.get("content"):
                return message["content"]
            delta = choice0.get("delta") or {}
            if isinstance(delta, dict) and delta.get("content"):
                return delta["content"]

        data = payload.get("data")
        if isinstance(data, dict):
            return self._extract_chat_reply(data)

        return payload.get("reply", "") or payload.get("response", "") or ""

    async def health_check(self) -> bool:
        if LOCAL_MODE or self._http is None:
            return False
        try:
            resp = await self._http.get("/api/kernel2/health")
        except Exception:
            return False
        if resp.status_code != 200:
            return False
        payload = resp.json()
        return payload.get("code") == 0

    async def create_avatar(
        self,
        *,
        avatar: PatientAvatar,
        patient_data: Dict[str, Any],
    ) -> AvatarProvisionResult:
        self._ensure_enabled()

        memory_text = build_memory_text(patient_data)
        bio = build_default_bio(patient_data)
        payload = {
            "name": f"medichat_avatar_{uuid.uuid4().hex[:10]}",
            "description": self._build_role_metadata(patient_data, bio),
            "system_prompt": build_system_prompt(patient_data, memory_text),
            "icon": "🧬",
            "enable_l0_retrieval": SECONDME_ENABLE_L0,
            "enable_l1_retrieval": False,
        }
        try:
            resp = await self._http.post("/api/kernel2/roles", json=payload)
        except Exception as exc:
            raise AvatarProviderError(f"SecondMe create_avatar failed: {exc}") from exc

        if resp.status_code not in {200, 201}:
            raise AvatarProviderError(
                f"SecondMe create_avatar returned {resp.status_code}"
            )
        data = resp.json().get("data") or {}
        provider_avatar_id = data.get("uuid")
        if not provider_avatar_id:
            raise AvatarProviderError("SecondMe create_avatar missing role uuid.")

        return AvatarProvisionResult(
            provider_avatar_id=provider_avatar_id,
            bio=bio,
            memory_summary=memory_text[:200],
            runtime_metadata={
                "mode": "secondme_runtime",
                "role_name": payload["name"],
            },
        )

    async def chat(
        self,
        *,
        avatar: PatientAvatar,
        message: str,
    ) -> str:
        self._ensure_enabled()
        role_id = avatar.provider_avatar_id or avatar.avatar_id
        payload = {
            "messages": [{"role": "user", "content": message}],
            "metadata": {
                "role_id": role_id,
                "enable_l0_retrieval": SECONDME_ENABLE_L0,
            },
            "stream": False,
            "temperature": 0.4,
            "max_tokens": SECONDME_CHAT_MAX_TOKENS,
        }
        try:
            resp = await self._http.post("/api/kernel2/chat", json=payload)
        except Exception as exc:
            raise AvatarProviderError(f"SecondMe chat failed: {exc}") from exc

        if resp.status_code != 200:
            raise AvatarProviderError(f"SecondMe chat returned {resp.status_code}")
        reply = self._extract_chat_reply(resp.json())
        if not reply:
            raise AvatarProviderError("SecondMe chat returned empty reply.")
        return reply


def build_provider_registry() -> Dict[str, AvatarProvider]:
    return {
        LocalAvatarProvider.key: LocalAvatarProvider(),
        SecondMeAvatarProvider.key: SecondMeAvatarProvider(),
    }
