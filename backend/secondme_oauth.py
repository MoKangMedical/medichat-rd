"""
SecondMe OAuth 平台接入

默认以本地单用户联调为主：
- access token / refresh token 仅保存在服务端受控 secret 文件
- 前端只拿到归一化后的用户信息与状态，不暴露 token
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.parse import urlencode, urlparse
import json
import os
import secrets

import httpx


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SECRET_STORE_PATH = PROJECT_ROOT / ".secrets" / "secondme_oauth.json"

SECONDME_AUTHORIZE_URL = os.getenv("SECONDME_AUTHORIZE_URL", "https://go.second.me/oauth/")
SECONDME_API_BASE = os.getenv("SECONDME_API_BASE", "https://api.mindverse.com/gate/lab")
SECONDME_CLIENT_ID = os.getenv("SECONDME_CLIENT_ID", "")
SECONDME_CLIENT_SECRET = os.getenv("SECONDME_CLIENT_SECRET", "")
SECONDME_REDIRECT_URI = os.getenv(
    "SECONDME_REDIRECT_URI",
    "http://localhost:8001/api/v1/secondme/oauth/callback",
)
SECONDME_POST_LOGIN_REDIRECT = os.getenv(
    "SECONDME_POST_LOGIN_REDIRECT",
    "http://localhost:8001/index.html",
)
SECONDME_OAUTH_SCOPES = [
    scope.strip()
    for scope in os.getenv("SECONDME_OAUTH_SCOPES", "userinfo,note.write").split(",")
    if scope.strip()
]
SECONDME_INCLUDE_SCOPE_IN_REDIRECT = (
    os.getenv("SECONDME_OAUTH_INCLUDE_SCOPE_IN_REDIRECT", "true").lower() == "true"
)
SECONDME_SECRET_STORE_PATH = Path(
    os.getenv("SECONDME_SECRET_STORE_PATH", str(DEFAULT_SECRET_STORE_PATH))
)
SECONDME_TOKEN_SKEW_SECONDS = int(os.getenv("SECONDME_TOKEN_SKEW_SECONDS", "120"))
SECONDME_PENDING_STATE_TTL_SECONDS = int(
    os.getenv("SECONDME_PENDING_STATE_TTL_SECONDS", "900")
)
SECONDME_SESSION_COOKIE_NAME = os.getenv(
    "SECONDME_SESSION_COOKIE_NAME",
    "medichatrd_secondme_sid",
)
SECONDME_SESSION_COOKIE_MAX_AGE = int(
    os.getenv("SECONDME_SESSION_COOKIE_MAX_AGE", str(60 * 60 * 24 * 30))
)
_COOKIE_REDIRECT = urlparse(SECONDME_REDIRECT_URI)
SECONDME_SESSION_COOKIE_SECURE = (
    os.getenv(
        "SECONDME_SESSION_COOKIE_SECURE",
        "true"
        if _COOKIE_REDIRECT.scheme == "https"
        and _COOKIE_REDIRECT.hostname not in {"localhost", "127.0.0.1"}
        else "false",
    ).lower()
    == "true"
)

AUTH_ERROR_CODES = {"401", "invalid_grant", "token_expired", "unauthorized"}
AUTH_ERROR_KEYWORDS = ("invalid", "expired", "unauthorized", "revoked", "forbidden")


class SecondMeOAuthError(Exception):
    """SecondMe OAuth 交互失败。"""

    def __init__(
        self,
        message: str,
        *,
        status_code: int = 400,
        code: Optional[str] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _isoformat(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat()


def _parse_isoformat(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    return datetime.fromisoformat(value)


def _new_session_id() -> str:
    return f"s2m_{secrets.token_urlsafe(24)}"


def _build_url(path: str) -> str:
    return f"{SECONDME_API_BASE.rstrip('/')}/{path.lstrip('/')}"


def _normalize_scope_list(raw_scope: Any) -> list[str]:
    if isinstance(raw_scope, str):
        return [scope.strip() for scope in raw_scope.replace(",", " ").split() if scope.strip()]
    if isinstance(raw_scope, list):
        return [str(scope).strip() for scope in raw_scope if str(scope).strip()]
    return []


def _missing_scopes(granted_scopes: list[str], required_scopes: list[str]) -> list[str]:
    if not granted_scopes:
        return []
    granted = set(granted_scopes)
    return [scope for scope in required_scopes if scope not in granted]


def _normalize_user_info(raw_user: Dict[str, Any]) -> Dict[str, Any]:
    display_name = (
        raw_user.get("name")
        or raw_user.get("nickname")
        or raw_user.get("userName")
        or raw_user.get("username")
        or "SecondMe 用户"
    )
    avatar = raw_user.get("avatar") or raw_user.get("avatarUrl") or raw_user.get("headImage") or ""
    tags = raw_user.get("tags") or raw_user.get("interests") or []
    if not isinstance(tags, list):
        tags = [tags]
    return {
        "display_name": display_name,
        "name": raw_user.get("name") or display_name,
        "nickname": raw_user.get("nickname") or raw_user.get("userName") or display_name,
        "bio": raw_user.get("bio") or raw_user.get("description") or "",
        "avatar": avatar,
        "email": raw_user.get("email") or "",
        "user_id": raw_user.get("userId") or raw_user.get("id") or raw_user.get("uid") or "",
        "tags": [str(tag) for tag in tags if str(tag).strip()],
    }


def _is_safe_return_to(value: Optional[str]) -> bool:
    if not value:
        return False
    parsed = urlparse(value)
    if not parsed.scheme:
        return value.startswith("/")
    if parsed.scheme not in {"http", "https"}:
        return False
    allowed_hosts = {"localhost", "127.0.0.1"}
    for candidate in (SECONDME_POST_LOGIN_REDIRECT, SECONDME_REDIRECT_URI):
        candidate_host = urlparse(candidate).hostname
        if candidate_host:
            allowed_hosts.add(candidate_host)
    return parsed.hostname in allowed_hosts


def _append_query(url: str, **params: str) -> str:
    parsed = urlparse(url)
    query_pairs = []
    if parsed.query:
        from urllib.parse import parse_qsl

        query_pairs.extend(parse_qsl(parsed.query, keep_blank_values=True))
    for key, value in params.items():
        if value is not None:
            query_pairs.append((key, value))
    from urllib.parse import urlunparse

    return urlunparse(parsed._replace(query=urlencode(query_pairs)))


def _looks_like_auth_error(
    *,
    status_code: int,
    code: Optional[str],
    message: str,
) -> bool:
    if code == "note.add.not_whitelisted":
        return False
    if status_code in {401, 403}:
        return True
    normalized_code = (code or "").strip().lower()
    if normalized_code in AUTH_ERROR_CODES:
        return True
    lowered_message = message.lower()
    return any(keyword in lowered_message for keyword in AUTH_ERROR_KEYWORDS)


def _public_error_message(
    *,
    path: str,
    status_code: int,
    code: Optional[str],
    message: str,
) -> str:
    lowered_message = message.lower()
    if code == "note.add.not_whitelisted" or "not authorized to add notes" in lowered_message:
        return "当前 SecondMe 应用尚未开通 note.write 白名单，无法写入 note。"
    if "scope" in lowered_message:
        return "SecondMe 授权 scope 不满足当前操作。"
    if _looks_like_auth_error(status_code=status_code, code=code, message=message):
        return "SecondMe 授权已失效，请重新连接。"
    if path == "api/oauth/token/code":
        return "SecondMe code exchange 失败，请检查回调地址、scope 和应用配置。"
    if status_code >= 500:
        return "SecondMe 服务暂时不可用，请稍后再试。"
    if not message:
        return "SecondMe 请求失败。"
    return message


def _resolve_error_status(response_status: int, response_code: Any) -> int:
    if response_status >= 400:
        return response_status
    try:
        code_int = int(response_code)
    except (TypeError, ValueError):
        return response_status or 400
    if 400 <= code_int <= 599:
        return code_int
    return response_status or 400


@dataclass
class SecondMeTokenBundle:
    access_token: str
    refresh_token: str
    token_type: str
    scope: list[str]
    expires_at: datetime

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SecondMeTokenBundle":
        expires_at = _parse_isoformat(data.get("expiresAt"))
        if expires_at is None:
            raise SecondMeOAuthError("SecondMe token data is incomplete")
        return cls(
            access_token=data["accessToken"],
            refresh_token=data["refreshToken"],
            token_type=data.get("tokenType", "Bearer"),
            scope=_normalize_scope_list(data.get("scope", [])),
            expires_at=expires_at,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "accessToken": self.access_token,
            "refreshToken": self.refresh_token,
            "tokenType": self.token_type,
            "scope": self.scope,
            "expiresAt": _isoformat(self.expires_at),
        }

    @property
    def is_expired(self) -> bool:
        return _utc_now() >= self.expires_at - timedelta(seconds=SECONDME_TOKEN_SKEW_SECONDS)


class SecondMeSessionStore:
    """把 OAuth 凭证按浏览器会话隔离写到服务端受控 secret 文件。"""

    def __init__(self, path: Path = SECONDME_SECRET_STORE_PATH):
        self.path = path

    def _ensure_parent(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        try:
            self.path.parent.chmod(0o700)
        except OSError:
            pass

    def _normalize_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        sessions = payload.get("sessions")
        if isinstance(sessions, dict):
            return {"sessions": sessions}

        legacy_session = {}
        if payload.get("oauth"):
            legacy_session["oauth"] = payload["oauth"]
        if payload.get("oauthPending"):
            legacy_session["oauthPending"] = payload["oauthPending"]
        if payload.get("updatedAt"):
            legacy_session["updatedAt"] = payload["updatedAt"]

        if legacy_session:
            return {"sessions": {"legacy_default": legacy_session}}
        return {"sessions": {}}

    def load(self) -> Dict[str, Any]:
        if not self.path.exists():
            return {"sessions": {}}
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {"sessions": {}}
        return self._normalize_payload(raw if isinstance(raw, dict) else {})

    def save(self, payload: Dict[str, Any]) -> None:
        normalized = self._normalize_payload(payload)
        self._ensure_parent()
        self.path.write_text(
            json.dumps(normalized, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        try:
            self.path.chmod(0o600)
        except OSError:
            pass

    def ensure_session(self, session_id: Optional[str] = None) -> str:
        payload = self.load()
        sessions = payload["sessions"]
        session_key = session_id or _new_session_id()
        session = sessions.get(session_key) or {}
        session.setdefault("createdAt", _isoformat(_utc_now()))
        session["updatedAt"] = _isoformat(_utc_now())
        sessions[session_key] = session
        self.save(payload)
        return session_key

    def get_session(self, session_id: Optional[str]) -> Dict[str, Any]:
        if not session_id:
            return {}
        return self.load()["sessions"].get(session_id, {})

    def _save_session(self, session_id: str, session_payload: Dict[str, Any]) -> None:
        payload = self.load()
        session = session_payload or {}
        session.setdefault("createdAt", _isoformat(_utc_now()))
        session["updatedAt"] = _isoformat(_utc_now())
        payload["sessions"][session_id] = session
        self.save(payload)

    def get_token_bundle(self, session_id: Optional[str]) -> Optional[SecondMeTokenBundle]:
        session = self.get_session(session_id)
        oauth = session.get("oauth") or {}
        token = oauth.get("token")
        if not token:
            return None
        return SecondMeTokenBundle.from_dict(token)

    def get_user_normalized(self, session_id: Optional[str]) -> Optional[Dict[str, Any]]:
        session = self.get_session(session_id)
        oauth = session.get("oauth") or {}
        user = oauth.get("user") or {}
        return user.get("normalized")

    def get_scope_summary(self, session_id: Optional[str]) -> Dict[str, Any]:
        session = self.get_session(session_id)
        oauth = session.get("oauth") or {}
        scope = oauth.get("scope") or {}
        return {
            "requested": scope.get("requested", SECONDME_OAUTH_SCOPES),
            "granted": scope.get("granted", []),
            "missing": scope.get("missing", []),
            "verified": scope.get("verified"),
        }

    def save_oauth(self, session_id: str, token_data: Dict[str, Any], user_raw: Dict[str, Any]) -> None:
        session_key = self.ensure_session(session_id)
        payload = self.load()
        session = payload["sessions"].get(session_key, {})
        expires_in = int(token_data.get("expiresIn") or 7200)
        granted_scopes = _normalize_scope_list(token_data.get("scope"))
        missing_scopes = _missing_scopes(granted_scopes, SECONDME_OAUTH_SCOPES)
        bundle = SecondMeTokenBundle(
            access_token=token_data["accessToken"],
            refresh_token=token_data["refreshToken"],
            token_type=token_data.get("tokenType", "Bearer"),
            scope=granted_scopes,
            expires_at=_utc_now() + timedelta(seconds=expires_in),
        )
        session["oauth"] = {
            "token": bundle.to_dict(),
            "user": {
                "normalized": _normalize_user_info(user_raw),
                "raw": user_raw,
            },
            "scope": {
                "requested": SECONDME_OAUTH_SCOPES,
                "granted": granted_scopes,
                "missing": missing_scopes,
                "verified": not missing_scopes if granted_scopes else None,
            },
            "updatedAt": _isoformat(_utc_now()),
        }
        session.pop("oauthPending", None)
        self._save_session(session_key, session)

    def update_user(self, session_id: str, user_raw: Dict[str, Any]) -> None:
        session = self.get_session(session_id)
        oauth = session.get("oauth")
        if not oauth:
            return
        oauth["user"] = {
            "normalized": _normalize_user_info(user_raw),
            "raw": user_raw,
        }
        oauth["updatedAt"] = _isoformat(_utc_now())
        session["oauth"] = oauth
        self._save_session(session_id, session)

    def clear_oauth(self, session_id: Optional[str]) -> None:
        if not session_id:
            return
        session = self.get_session(session_id)
        if not session:
            return
        session.pop("oauth", None)
        session.pop("oauthPending", None)
        self._save_session(session_id, session)

    def save_pending_state(self, session_id: str, state: str, return_to: Optional[str]) -> None:
        session_key = self.ensure_session(session_id)
        session = self.get_session(session_key)
        session["oauthPending"] = {
            "state": state,
            "returnTo": return_to,
            "redirectUri": SECONDME_REDIRECT_URI,
            "requestedScopes": SECONDME_OAUTH_SCOPES,
            "createdAt": _isoformat(_utc_now()),
        }
        self._save_session(session_key, session)

    def pop_pending_state(self, state: str) -> tuple[Optional[str], Optional[Dict[str, Any]]]:
        payload = self.load()
        sessions = payload["sessions"]
        matched_session_id = None
        pending = None
        for session_id, session in sessions.items():
            maybe_pending = session.get("oauthPending")
            if maybe_pending and maybe_pending.get("state") == state:
                matched_session_id = session_id
                pending = maybe_pending
                session.pop("oauthPending", None)
                session["updatedAt"] = _isoformat(_utc_now())
                sessions[session_id] = session
                break

        if matched_session_id is None or pending is None:
            return None, None

        self.save(payload)
        created_at = _parse_isoformat(pending.get("createdAt"))
        if created_at is None:
            return matched_session_id, None
        if _utc_now() - created_at > timedelta(seconds=SECONDME_PENDING_STATE_TTL_SECONDS):
            return matched_session_id, None
        return matched_session_id, pending


_session_store_singleton: Optional[SecondMeSessionStore] = None


def get_secondme_session_store() -> SecondMeSessionStore:
    global _session_store_singleton
    if _session_store_singleton is None:
        _session_store_singleton = SecondMeSessionStore()
    return _session_store_singleton


def get_secondme_profile_for_session(session_id: Optional[str]) -> Dict[str, Any]:
    if not session_id:
        return {}
    return get_secondme_session_store().get_user_normalized(session_id) or {}


class SecondMeCredentialStore:
    """兼容层：保留旧类名，内部转发到会话级 store。"""

    def __init__(
        self,
        session_id: Optional[str] = None,
        store: Optional[SecondMeSessionStore] = None,
    ):
        self.session_id = session_id
        self.store = store or get_secondme_session_store()

    def get_token_bundle(self) -> Optional[SecondMeTokenBundle]:
        return self.store.get_token_bundle(self.session_id)

    def get_user_normalized(self) -> Optional[Dict[str, Any]]:
        return self.store.get_user_normalized(self.session_id)

    def get_scope_summary(self) -> Dict[str, Any]:
        return self.store.get_scope_summary(self.session_id)

    def save_oauth(self, token_data: Dict[str, Any], user_raw: Dict[str, Any]) -> None:
        if not self.session_id:
            raise SecondMeOAuthError("Missing SecondMe session id", status_code=400)
        self.store.save_oauth(self.session_id, token_data, user_raw)

    def update_user(self, user_raw: Dict[str, Any]) -> None:
        if self.session_id:
            self.store.update_user(self.session_id, user_raw)

    def clear_oauth(self) -> None:
        self.store.clear_oauth(self.session_id)

    def save_pending_state(self, state: str, return_to: Optional[str]) -> None:
        if not self.session_id:
            raise SecondMeOAuthError("Missing SecondMe session id", status_code=400)
        self.store.save_pending_state(self.session_id, state, return_to)

    def pop_pending_state(self, state: str) -> Optional[Dict[str, Any]]:
        session_id, pending = self.store.pop_pending_state(state)
        if session_id and not self.session_id:
            self.session_id = session_id
        return pending


class SecondMeOAuthClient:
    def __init__(self, store: Optional[SecondMeSessionStore] = None):
        self.store = store or get_secondme_session_store()

    @property
    def configured(self) -> bool:
        return bool(SECONDME_CLIENT_ID and SECONDME_CLIENT_SECRET)

    def build_authorization_url(self, session_id: str, return_to: Optional[str] = None) -> str:
        if not self.configured:
            raise SecondMeOAuthError(
                "SecondMe OAuth 未配置 Client ID / Client Secret。",
                status_code=500,
                code="misconfigured",
            )

        state = secrets.token_urlsafe(24)
        safe_return_to = return_to if _is_safe_return_to(return_to) else None
        self.store.save_pending_state(session_id, state, safe_return_to)

        params = {
            "client_id": SECONDME_CLIENT_ID,
            "redirect_uri": SECONDME_REDIRECT_URI,
            "response_type": "code",
            "state": state,
        }
        if SECONDME_INCLUDE_SCOPE_IN_REDIRECT and SECONDME_OAUTH_SCOPES:
            params["scope"] = " ".join(SECONDME_OAUTH_SCOPES)
        return f"{SECONDME_AUTHORIZE_URL}?{urlencode(params)}"

    async def handle_callback(self, code: str, state: str) -> tuple[str, str, Dict[str, Any]]:
        session_id, pending = self.store.pop_pending_state(state)
        if not session_id or not pending:
            raise SecondMeOAuthError(
                "SecondMe OAuth state 校验失败或已过期。",
                status_code=400,
                code="invalid_state",
            )
        if pending.get("redirectUri") != SECONDME_REDIRECT_URI:
            raise SecondMeOAuthError(
                "SecondMe 回调地址与服务端配置不匹配。",
                status_code=400,
                code="redirect_uri_mismatch",
            )

        token_data = await self.exchange_code(code)
        self._validate_granted_scope(token_data)
        user_raw = await self.fetch_user_info_raw(access_token=token_data["accessToken"])
        self.store.save_oauth(session_id, token_data, user_raw)

        return_to = pending.get("returnTo")
        if _is_safe_return_to(return_to):
            return session_id, return_to, _normalize_user_info(user_raw)
        return session_id, SECONDME_POST_LOGIN_REDIRECT, _normalize_user_info(user_raw)

    async def exchange_code(self, code: str) -> Dict[str, Any]:
        form = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": SECONDME_REDIRECT_URI,
            "client_id": SECONDME_CLIENT_ID,
            "client_secret": SECONDME_CLIENT_SECRET,
        }
        payload = await self._post_form("api/oauth/token/code", form)
        return payload["data"]

    async def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        form = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": SECONDME_CLIENT_ID,
            "client_secret": SECONDME_CLIENT_SECRET,
        }
        payload = await self._post_form("api/oauth/token/refresh", form)
        return payload["data"]

    async def get_valid_access_token(self, session_id: Optional[str]) -> SecondMeTokenBundle:
        bundle = self.store.get_token_bundle(session_id)
        if bundle is None:
            raise SecondMeOAuthError(
                "SecondMe 尚未授权。",
                status_code=401,
                code="unauthenticated",
            )
        if not bundle.is_expired:
            return bundle

        try:
            refreshed = await self.refresh_token(bundle.refresh_token)
        except SecondMeOAuthError as exc:
            if _looks_like_auth_error(
                status_code=exc.status_code,
                code=exc.code,
                message=exc.message,
            ):
                self.store.clear_oauth(session_id)
                raise SecondMeOAuthError(
                    "SecondMe 授权已失效，请重新连接。",
                    status_code=401,
                    code="token_expired",
                ) from exc
            raise

        self._validate_granted_scope(refreshed)
        existing_user = self.store.get_user_normalized(session_id) or {}
        self.store.save_oauth(
            session_id,
            refreshed,
            {
                "name": existing_user.get("name"),
                "nickname": existing_user.get("nickname"),
                "bio": existing_user.get("bio"),
                "avatar": existing_user.get("avatar"),
                "email": existing_user.get("email"),
                "userId": existing_user.get("user_id"),
                "tags": existing_user.get("tags"),
            },
        )
        refreshed_bundle = self.store.get_token_bundle(session_id)
        if refreshed_bundle is None:
            raise SecondMeOAuthError("SecondMe token 刷新后写入失败。", status_code=500)
        return refreshed_bundle

    async def fetch_user_info_raw(
        self,
        session_id: Optional[str] = None,
        access_token: Optional[str] = None,
    ) -> Dict[str, Any]:
        token = access_token
        if token is None:
            bundle = await self.get_valid_access_token(session_id)
            token = bundle.access_token

        try:
            payload = await self._request(
                "GET",
                "api/secondme/user/info",
                headers={"Authorization": f"Bearer {token}"},
            )
        except SecondMeOAuthError as exc:
            if access_token is None and _looks_like_auth_error(
                status_code=exc.status_code,
                code=exc.code,
                message=exc.message,
            ):
                self.store.clear_oauth(session_id)
                raise SecondMeOAuthError(
                    "SecondMe 授权已失效，请重新连接。",
                    status_code=401,
                    code="token_expired",
                ) from exc
            raise

        user_raw = payload["data"]
        if access_token is None and session_id:
            self.store.update_user(session_id, user_raw)
        return user_raw

    async def add_text_note(self, session_id: Optional[str], title: str, content: str) -> int:
        bundle = await self.get_valid_access_token(session_id)
        if bundle.scope and "note.write" not in bundle.scope:
            raise SecondMeOAuthError(
                "当前 SecondMe 授权不包含 note.write scope。",
                status_code=403,
                code="missing_scope",
            )

        payload = await self._request(
            "POST",
            "api/secondme/note/add",
            headers={"Authorization": f"Bearer {bundle.access_token}"},
            json={
                "title": title,
                "content": content,
                "memoryType": "TEXT",
            },
        )
        return payload["data"]["noteId"]

    async def get_status(self, session_id: Optional[str]) -> Dict[str, Any]:
        base_status = {
            "configured": self.configured,
            "connected": False,
            "authorized": self.store.get_token_bundle(session_id) is not None,
            "state": "unauthenticated",
            "redirect_uri": SECONDME_REDIRECT_URI,
            "authorize_url": SECONDME_AUTHORIZE_URL,
            "token_storage": "server_secret_file_per_session",
            "required_scopes": SECONDME_OAUTH_SCOPES,
            "scope_sent_in_authorize_url": SECONDME_INCLUDE_SCOPE_IN_REDIRECT,
            "session_isolated": True,
            "session_cookie_name": SECONDME_SESSION_COOKIE_NAME,
            "granted_scopes": [],
            "missing_scopes": [],
            "scope_match": None,
            "reauth_required": False,
            "expires_at": None,
            "user": None,
            "error": None,
        }

        if not self.configured:
            base_status["state"] = "misconfigured"
            base_status["error"] = "服务端未配置 SecondMe Client ID / Client Secret。"
            return base_status

        bundle = self.store.get_token_bundle(session_id)
        if bundle is None:
            return base_status

        scope_summary = self.store.get_scope_summary(session_id)
        base_status.update(
            {
                "authorized": True,
                "granted_scopes": scope_summary["granted"],
                "missing_scopes": scope_summary["missing"],
                "scope_match": scope_summary["verified"],
            }
        )

        try:
            valid_bundle = await self.get_valid_access_token(session_id)
            await self.fetch_user_info_raw(session_id)
            scope_summary = self.store.get_scope_summary(session_id)
            base_status.update(
                {
                    "connected": True,
                    "authorized": True,
                    "state": "connected",
                    "expires_at": _isoformat(valid_bundle.expires_at),
                    "user": self.store.get_user_normalized(session_id),
                    "granted_scopes": scope_summary["granted"],
                    "missing_scopes": scope_summary["missing"],
                    "scope_match": scope_summary["verified"],
                }
            )
            return base_status
        except SecondMeOAuthError as exc:
            if exc.code == "token_expired":
                base_status.update(
                    {
                        "authorized": False,
                        "state": "expired",
                        "reauth_required": True,
                        "error": exc.message,
                    }
                )
                return base_status

            base_status.update(
                {
                    "state": "api_error",
                    "authorized": True,
                    "error": exc.message,
                    "user": self.store.get_user_normalized(session_id),
                }
            )
            return base_status

    def clear(self, session_id: Optional[str]) -> None:
        self.store.clear_oauth(session_id)

    def _validate_granted_scope(self, token_data: Dict[str, Any]) -> None:
        granted_scopes = _normalize_scope_list(token_data.get("scope"))
        missing_scopes = _missing_scopes(granted_scopes, SECONDME_OAUTH_SCOPES)
        if granted_scopes and missing_scopes:
            raise SecondMeOAuthError(
                f"SecondMe 授权缺少必要 scope: {', '.join(missing_scopes)}",
                status_code=403,
                code="missing_scope",
            )

    async def _post_form(self, path: str, form: Dict[str, str]) -> Dict[str, Any]:
        return await self._request(
            "POST",
            path,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data=form,
        )

    async def _request(
        self,
        method: str,
        path: str,
        *,
        headers: Optional[Dict[str, str]] = None,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.request(
                method,
                _build_url(path),
                headers=headers,
                json=json,
                data=data,
            )

        try:
            payload = response.json()
        except ValueError as exc:
            raise SecondMeOAuthError(
                "SecondMe 返回了不可解析的响应。",
                status_code=response.status_code or 502,
            ) from exc

        response_code = payload.get("code")
        if response.status_code >= 400 or response_code not in (0, "0", None):
            internal_message = (
                payload.get("message")
                or payload.get("error_description")
                or payload.get("error")
                or ""
            )
            normalized_code = str(
                payload.get("subCode")
                or response_code
                or payload.get("error")
                or ""
            ).strip() or None
            resolved_status = _resolve_error_status(response.status_code or 400, response_code)
            raise SecondMeOAuthError(
                _public_error_message(
                    path=path,
                    status_code=resolved_status,
                    code=normalized_code,
                    message=internal_message,
                ),
                status_code=resolved_status,
                code=normalized_code,
            )

        return payload
