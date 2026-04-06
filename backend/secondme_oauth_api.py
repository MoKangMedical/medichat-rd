"""
SecondMe OAuth API
"""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field

from secondme_oauth import (
    SECONDME_POST_LOGIN_REDIRECT,
    SecondMeOAuthClient,
    SecondMeOAuthError,
    _append_query,
)


router = APIRouter(prefix="/api/v1/secondme", tags=["SecondMe OAuth"])
_oauth_client: Optional[SecondMeOAuthClient] = None


def get_oauth_client() -> SecondMeOAuthClient:
    global _oauth_client
    if _oauth_client is None:
        _oauth_client = SecondMeOAuthClient()
    return _oauth_client


class PatientSummaryInput(BaseModel):
    nickname: str = Field(..., description="患者昵称")
    disease_type: str = Field(..., description="疾病类型")
    bio: Optional[str] = Field("", description="分身简介")
    age: Optional[int] = Field(None, description="年龄")
    symptoms: Optional[str] = Field("", description="主要症状")
    diagnosis: Optional[str] = Field("", description="诊断信息")
    treatment_history: Optional[str] = Field("", description="治疗经历")


def build_patient_summary_note(input_data: PatientSummaryInput) -> tuple[str, str]:
    title = f"MediChat-RD 患者摘要：{input_data.nickname}"
    lines = [
        f"同步时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"来源：MediChat-RD 罕见病互助社群",
        "",
        f"昵称：{input_data.nickname}",
        f"疾病类型：{input_data.disease_type}",
    ]
    if input_data.age is not None:
        lines.append(f"年龄：{input_data.age}")
    if input_data.bio:
        lines.append(f"简介：{input_data.bio}")
    if input_data.symptoms:
        lines.append(f"主要症状：{input_data.symptoms}")
    if input_data.diagnosis:
        lines.append(f"诊断信息：{input_data.diagnosis}")
    if input_data.treatment_history:
        lines.append(f"治疗经历：{input_data.treatment_history}")
    lines.extend(
        [
            "",
            "备注：此条信息由 MediChat-RD 在用户触发时同步，用于 SecondMe 侧的个人记忆沉淀。",
        ]
    )
    return title, "\n".join(lines)


def _build_frontend_redirect(status: str, reason: Optional[str] = None, return_to: Optional[str] = None) -> RedirectResponse:
    target = return_to or SECONDME_POST_LOGIN_REDIRECT
    return RedirectResponse(
        _append_query(target, secondme=status, reason=reason),
        status_code=302,
    )


@router.get("/oauth/start")
async def secondme_oauth_start(return_to: Optional[str] = Query(None, description="授权成功后的前端返回地址")):
    client = get_oauth_client()
    try:
        auth_url = client.build_authorization_url(return_to=return_to)
    except SecondMeOAuthError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return RedirectResponse(auth_url, status_code=302)


@router.get("/oauth/callback")
async def secondme_oauth_callback(
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
):
    client = get_oauth_client()

    if error:
        return _build_frontend_redirect("error", error)

    if not code or not state:
        raise HTTPException(status_code=400, detail="缺少 OAuth 回调参数 code/state")

    try:
        return_to, _user = await client.handle_callback(code, state)
    except SecondMeOAuthError as exc:
        return _build_frontend_redirect("error", exc.message)

    return _build_frontend_redirect("connected", return_to=return_to)


@router.get("/oauth/status")
async def secondme_oauth_status():
    client = get_oauth_client()
    status = await client.get_status()
    return {"ok": True, "status": status}


@router.post("/oauth/logout")
async def secondme_oauth_logout():
    client = get_oauth_client()
    client.clear()
    return {"ok": True, "message": "SecondMe OAuth 已断开"}


@router.post("/note/patient-summary")
async def sync_patient_summary(input_data: PatientSummaryInput):
    client = get_oauth_client()
    title, content = build_patient_summary_note(input_data)
    try:
        note_id = await client.add_text_note(title=title, content=content)
    except SecondMeOAuthError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

    return {"ok": True, "note_id": note_id, "message": "患者摘要已同步到 SecondMe"}
