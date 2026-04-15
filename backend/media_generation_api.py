from __future__ import annotations

from io import BytesIO
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from mimo_media import (
    MEDIA_MODEL,
    TTS_FORMAT,
    TTS_MODEL,
    TTS_VOICE,
    generate_structured_storyboard,
    get_mimo_media_client,
    mimo_media_available,
)


router = APIRouter(prefix="/api/v1/media", tags=["media"])


class TTSRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000)
    voice: Optional[str] = None
    audio_format: Optional[str] = None


class StoryboardRequest(BaseModel):
    project_name: str = "MediChat-RD"
    format_name: str = "品牌宣传片"
    brand_goal: str = "生成一个情真意切、能体现罕见病患者陪伴和产品能力的宣传片分镜"
    scene_seeds: List[Dict[str, Any]]


@router.get("/status")
async def media_status():
    return {
        "configured": mimo_media_available(),
        "media_model": MEDIA_MODEL,
        "tts_model": TTS_MODEL,
        "tts_voice": TTS_VOICE,
        "tts_format": TTS_FORMAT,
    }


@router.post("/tts-preview")
async def tts_preview(request: TTSRequest):
    if not mimo_media_available():
        raise HTTPException(status_code=500, detail="MIMO_API_KEY 未配置，无法生成语音")
    client = get_mimo_media_client()
    audio_bytes = client.tts(
        request.text,
        voice=request.voice or TTS_VOICE,
        audio_format=request.audio_format or TTS_FORMAT,
        model=TTS_MODEL,
    )
    fmt = request.audio_format or TTS_FORMAT
    media_type = "audio/wav" if fmt.lower() == "wav" else "application/octet-stream"
    return StreamingResponse(
        BytesIO(audio_bytes),
        media_type=media_type,
        headers={"Content-Disposition": f'inline; filename="mimo-tts-preview.{fmt}"'},
    )


@router.post("/storyboard")
async def generate_storyboard(request: StoryboardRequest):
    if not mimo_media_available():
        raise HTTPException(status_code=500, detail="MIMO_API_KEY 未配置，无法生成分镜")
    return generate_structured_storyboard(
        project_name=request.project_name,
        format_name=request.format_name,
        brand_goal=request.brand_goal,
        scene_seeds=request.scene_seeds,
    )
