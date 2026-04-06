"""
Avatar service orchestrator.

职责：
- 使用自有 AvatarCoreStore 作为主数据源
- 调用 provider 运行时创建/对话
- 支持主 provider + fallback provider
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from datetime import datetime
import uuid

from avatar_core import AvatarCoreStore, PatientAvatar
from avatar_providers import (
    AVATAR_PROVIDER_FALLBACK,
    AVATAR_PROVIDER_PRIMARY,
    AvatarProviderError,
    build_default_bio,
    build_memory_text,
    build_provider_registry,
)


class AvatarService:
    def __init__(self, store: Optional[AvatarCoreStore] = None):
        self.store = store or AvatarCoreStore()
        self.providers = build_provider_registry()
        self.primary_provider_key = AVATAR_PROVIDER_PRIMARY
        self.fallback_provider_key = AVATAR_PROVIDER_FALLBACK

    def _provider_chain(self) -> List[str]:
        order = [self.primary_provider_key, self.fallback_provider_key, "local"]
        deduped = []
        for key in order:
            if key and key not in deduped and key in self.providers:
                deduped.append(key)
        return deduped

    def _build_avatar_draft(self, patient_data: Dict[str, Any]) -> PatientAvatar:
        now = datetime.utcnow()
        return PatientAvatar(
            avatar_id=f"avt_{uuid.uuid4().hex[:8]}",
            patient_id=patient_data.get("patient_id") or f"p_{now.strftime('%Y%m%d%H%M%S')}",
            nickname=patient_data.get("nickname", "匿名"),
            disease_type=patient_data.get("disease_type", ""),
            bio=build_default_bio(patient_data),
            memory_summary=build_memory_text(patient_data)[:200],
            personality="温暖、共情、乐于助人",
            provider_key="pending",
            created_at=now,
            updated_at=now,
        )

    async def create_avatar(self, patient_data: Dict[str, Any]) -> PatientAvatar:
        draft = self._build_avatar_draft(patient_data)
        patient_data = dict(patient_data)
        patient_data.setdefault("patient_id", draft.patient_id)
        patient_data.setdefault("avatar_id", draft.avatar_id)

        last_error: Optional[Exception] = None
        for provider_key in self._provider_chain():
            provider = self.providers[provider_key]
            try:
                provision = await provider.create_avatar(avatar=draft, patient_data=patient_data)
                avatar = PatientAvatar(
                    avatar_id=draft.avatar_id,
                    patient_id=draft.patient_id,
                    nickname=draft.nickname,
                    disease_type=draft.disease_type,
                    bio=provision.bio or draft.bio,
                    memory_summary=provision.memory_summary or draft.memory_summary,
                    personality=draft.personality,
                    provider_key=provider_key,
                    provider_avatar_id=provision.provider_avatar_id,
                    runtime_metadata=provision.runtime_metadata,
                    created_at=draft.created_at,
                    updated_at=datetime.utcnow(),
                )
                stored = self.store.upsert_avatar(avatar)
                self.store.append_memory(
                    stored.avatar_id,
                    "profile_seed",
                    build_memory_text(patient_data),
                    metadata={
                        "provider_key": provider_key,
                        "disease_type": stored.disease_type,
                    },
                )
                return stored
            except Exception as exc:
                last_error = exc
                continue

        if last_error:
            raise last_error
        raise AvatarProviderError("No avatar provider is available.")

    async def chat(self, avatar_id: str, message: str) -> str:
        avatar = self.get_avatar(avatar_id)
        if not avatar:
            raise AvatarProviderError("Avatar not found.")

        self.store.append_message(
            avatar.avatar_id,
            "user",
            message,
            metadata={"provider_key": avatar.provider_key},
        )

        provider_keys = [avatar.provider_key]
        if avatar.provider_key != "local":
            provider_keys.append("local")

        last_error: Optional[Exception] = None
        for provider_key in provider_keys:
            provider = self.providers.get(provider_key)
            if provider is None:
                continue
            try:
                reply = await provider.chat(avatar=avatar, message=message)
                self.store.append_message(
                    avatar.avatar_id,
                    "assistant",
                    reply,
                    metadata={"provider_key": provider_key},
                )
                return reply
            except Exception as exc:
                last_error = exc
                continue

        if last_error:
            raise last_error
        raise AvatarProviderError("No avatar runtime is available.")

    async def health_check(self) -> bool:
        primary = self.providers.get(self.primary_provider_key)
        if primary is None:
            return False
        try:
            return await primary.health_check()
        except Exception:
            return False

    def get_avatar(self, avatar_id: str) -> Optional[PatientAvatar]:
        return self.store.get_avatar(avatar_id)

    def list_avatars(self) -> List[PatientAvatar]:
        return self.store.list_avatars()

    def get_runtime_summary(self, avatar_id: str) -> Dict[str, Any]:
        avatar = self.get_avatar(avatar_id)
        if not avatar:
            return {}
        return {
            "provider_key": avatar.provider_key,
            "provider_avatar_id": avatar.provider_avatar_id,
            "runtime_metadata": avatar.runtime_metadata,
        }


_avatar_service: Optional[AvatarService] = None


def get_avatar_service() -> AvatarService:
    global _avatar_service
    if _avatar_service is None:
        _avatar_service = AvatarService()
    return _avatar_service
