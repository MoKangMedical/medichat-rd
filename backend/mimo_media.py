"""
MiMo 媒体生成层。

职责：
1. 用 mimo-v2-omni 生成品牌片/首页 demo 分镜 JSON
2. 用 mimo-v2-tts 生成旁白音频
3. 对上层脚本和 API 提供统一接口
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List

from mimo_client import MIMOClient


MEDIA_MODEL = os.getenv("MIMO_MEDIA_MODEL", "mimo-v2-omni")
TTS_MODEL = os.getenv("MIMO_TTS_MODEL", "mimo-v2-tts")
TTS_VOICE = os.getenv("MIMO_TTS_VOICE", "default_zh")
TTS_FORMAT = os.getenv("MIMO_TTS_FORMAT", "wav")


def mimo_media_available() -> bool:
    return bool(os.getenv("MIMO_API_KEY"))


def get_mimo_media_client() -> MIMOClient:
    return MIMOClient(model=os.getenv("MIMO_MODEL", "mimo-v2-pro"))


def synthesize_voice_to_file(text: str, output_path: Path) -> Path:
    client = get_mimo_media_client()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(
        client.tts(
            text,
            voice=TTS_VOICE,
            audio_format=TTS_FORMAT,
            model=TTS_MODEL,
        )
    )
    return output_path


def generate_structured_storyboard(
    *,
    project_name: str,
    format_name: str,
    brand_goal: str,
    scene_seeds: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    让 MiMo 根据现有 seed scene 生成更完整的镜头脚本。

    返回结构：
    {
      "title": "...",
      "tone": "...",
      "scenes": [
        {
          "id": "...",
          "chapter": "...",
          "label": "...",
          "title": "...",
          "hook": "...",
          "summary": "...",
          "narration": "...",
          "subtitleSegments": ["...", "..."],
          "visualDirection": "...",
          "motionHint": "...",
          "tags": ["...", "..."]
        }
      ]
    }
    """
    client = get_mimo_media_client()
    system_prompt = (
        "你是一名品牌影片导演和分镜编剧。"
        "请把输入的 seed scenes 重写成可直接用于产品宣传片的结构化 JSON。"
        "不要输出 markdown，不要解释，不要丢失 scene id。"
        "所有文案使用简洁自然的中文，情绪要温柔、可信、有人味。"
        "subtitleSegments 适合逐句字幕展示，每个场景 2-3 段。"
    )
    user_prompt = (
        f"项目名：{project_name}\n"
        f"片型：{format_name}\n"
        f"传播目标：{brand_goal}\n"
        "请严格返回 JSON，对象结构包含 title、tone、scenes。\n"
        "其中 scenes 必须和输入场景数量一致，且每个场景保留原始 id。\n"
        "每个 scene 输出字段：id, chapter, label, title, hook, summary, narration, subtitleSegments, visualDirection, motionHint, tags。\n"
        f"输入 seed scenes:\n{scene_seeds}"
    )
    return client.chat_json(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.65,
        max_tokens=6000,
        model=MEDIA_MODEL,
    )
