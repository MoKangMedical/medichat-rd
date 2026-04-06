#!/usr/bin/env python3
from __future__ import annotations

import json
import math
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import imageio.v2 as imageio
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont


FPS = 24
VOICE_NAME = "Tingting"
VOICE_RATE = 182
DEFAULT_OUTPUT_ROOT = Path("/Users/apple/Desktop/medichatrd-brand-film-20260407")
FONT_PATH = Path("/System/Library/Fonts/Supplemental/Arial Unicode.ttf")
TITLE_FONT_PATH = Path("/System/Library/Fonts/Helvetica.ttc")


@dataclass(frozen=True)
class Scene:
    id: str
    chapter: str
    label: str
    title: str
    hook: str
    tags: tuple[str, ...]
    summary: str
    narration: str
    subtitle_segments: tuple[str, ...]
    palette: tuple[str, str, str]
    accent: str


@dataclass(frozen=True)
class Profile:
    id: str
    width: int
    height: int
    title_size: int
    body_size: int
    quote_size: int
    footer_size: int


SCENES = [
    Scene(
        id="welcome",
        chapter="01",
        label="先接住一家人的情绪",
        title="当一个家庭第一次听见罕见病，最需要的不是更多慌张，而是先被接住。",
        hook="新确诊患者欢迎房",
        tags=("病历整理", "情绪安放", "第一周陪伴"),
        summary="MediChat-RD 先让病历、检查和情绪落到一个温柔的入口里。",
        narration="当一个家庭第一次听见罕见病，最需要的不是更多慌张，而是先被接住。MediChat-RD 先把病历、检查和情绪，放进一个可以慢慢稳下来的入口里。",
        subtitle_segments=(
            "当一个家庭第一次听见罕见病，最需要的不是更多慌张，而是先被接住。",
            "MediChat-RD 先把病历、检查和情绪，放进一个可以慢慢稳下来的入口里。",
        ),
        palette=("#fff2e8", "#ffe8d8", "#f7efff"),
        accent="#ff7a59",
    ),
    Scene(
        id="hub",
        chapter="02",
        label="把今天最重要的事排好",
        title="患者中枢把病历、检查、提醒和下一步，整理成一个看得见的旅程。",
        hook="患者中枢",
        tags=("旅程总览", "任务路径", "一页进入"),
        summary="患者和家属终于知道，现在要做什么，接下来又该去哪里。",
        narration="患者中枢把病历、检查、提醒和下一步，整理成一个看得见的旅程。患者和家属终于知道，现在要做什么，接下来又该去哪里。",
        subtitle_segments=(
            "患者中枢把病历、检查、提醒和下一步，整理成一个看得见的旅程。",
            "患者和家属终于知道，现在要做什么，接下来又该去哪里。",
        ),
        palette=("#fff9ea", "#eef7ff", "#e9fff6"),
        accent="#0dbf9b",
    ),
    Scene(
        id="deeprare",
        chapter="03",
        label="让症状真正被读懂",
        title="DeepRare 把零散描述变成候选诊断、表型线索和下一步检查建议。",
        hook="DeepRare 智能诊断",
        tags=("HPO", "鉴别诊断", "检查建议"),
        summary="从“说不清楚”到“被系统地看见”，诊断路径开始变得清晰。",
        narration="DeepRare 把零散描述变成候选诊断、表型线索和下一步检查建议。从说不清楚，到被系统地看见，诊断路径开始变得清晰。",
        subtitle_segments=(
            "DeepRare 把零散描述变成候选诊断、表型线索和下一步检查建议。",
            "从说不清楚，到被系统地看见，诊断路径开始变得清晰。",
        ),
        palette=("#eef5ff", "#eefcff", "#fff8ec"),
        accent="#4c7dff",
    ),
    Scene(
        id="avatar",
        chapter="04",
        label="让患者更容易开口",
        title="SecondMe 分身把病程、身份和真实需求，变成一句能被理解的话。",
        hook="SecondMe 分身",
        tags=("人格卡", "首帖草稿", "病程表达"),
        summary="不是替患者说话，而是帮患者把难以开口的话，说得更稳、更像自己。",
        narration="SecondMe 分身把病程、身份和真实需求，变成一句能被理解的话。它不是替患者说话，而是帮患者把难以开口的话，说得更稳、更像自己。",
        subtitle_segments=(
            "SecondMe 分身把病程、身份和真实需求，变成一句能被理解的话。",
            "它不是替患者说话，而是帮患者把难以开口的话，说得更稳、更像自己。",
        ),
        palette=("#fff4ec", "#f6f0ff", "#effcff"),
        accent="#7a5af8",
    ),
    Scene(
        id="community",
        chapter="05",
        label="让希望在现场流动",
        title="欢迎房、家长圆桌和试验追踪，把支持、经验和机会聚到一个现场。",
        hook="公开社群现场",
        tags=("欢迎房", "家长圆桌", "临床试验"),
        summary="一个人不再独自面对，病友、家属和研究机会开始真正连接。",
        narration="欢迎房、家长圆桌和试验追踪，把支持、经验和机会聚到一个现场。一个人不再独自面对，病友、家属和研究机会开始真正连接。",
        subtitle_segments=(
            "欢迎房、家长圆桌和试验追踪，把支持、经验和机会聚到一个现场。",
            "一个人不再独自面对，病友、家属和研究机会开始真正连接。",
        ),
        palette=("#fff7ea", "#effcff", "#eef6ff"),
        accent="#ff9d57",
    ),
    Scene(
        id="followup",
        chapter="06",
        label="把陪伴留到日常里",
        title="陪伴玩偶和语音随访设备，让长期管理也能温柔、明亮、持续发生。",
        hook="陪伴与随访闭环",
        tags=("玩偶陪伴", "语音设备", "长期管理"),
        summary="让长期管理不只是一份压力，也是一种真正被陪伴的生活方式。",
        narration="陪伴玩偶和语音随访设备，让长期管理也能温柔、明亮、持续发生。让长期管理不只是一份压力，也是一种真正被陪伴的生活方式。",
        subtitle_segments=(
            "陪伴玩偶和语音随访设备，让长期管理也能温柔、明亮、持续发生。",
            "让长期管理不只是一份压力，也是一种真正被陪伴的生活方式。",
        ),
        palette=("#fff8ef", "#f7f1ff", "#efffff"),
        accent="#4c7dff",
    ),
]


PROFILES = (
    Profile("landscape", 1280, 720, 58, 28, 28, 20),
    Profile("portrait", 1080, 1920, 74, 34, 34, 24),
)


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def probe_duration(path: Path) -> float:
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return float(result.stdout.strip())


def hex_to_rgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    return tuple(int(value[index : index + 2], 16) for index in (0, 2, 4))


def blend(a: tuple[int, int, int], b: tuple[int, int, int], t: float) -> tuple[int, int, int]:
    return tuple(int(a[idx] * (1 - t) + b[idx] * t) for idx in range(3))


def load_font(path: Path, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(path), size=size)


def wrap_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    lines: list[str] = []
    current = ""
    for char in text:
        trial = current + char
        bbox = draw.textbbox((0, 0), trial, font=font)
        if bbox[2] - bbox[0] > max_width and current:
            lines.append(current)
            current = char
        else:
            current = trial
    if current:
        lines.append(current)
    return lines


def rounded_box(draw: ImageDraw.ImageDraw, box, radius: int, fill, outline=None, width: int = 1):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def draw_gradient_background(image: Image.Image, profile: Profile, palette: tuple[str, str, str]) -> None:
    top = hex_to_rgb(palette[0])
    middle = hex_to_rgb(palette[1])
    bottom = hex_to_rgb(palette[2])
    width, height = image.size
    px = image.load()
    for y in range(height):
        if y < height / 2:
            t = y / (height / 2)
            color = blend(top, middle, t)
        else:
            t = (y - height / 2) / (height / 2)
            color = blend(middle, bottom, t)
        for x in range(width):
            px[x, y] = color

    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    accent = palette[0]
    rgb = hex_to_rgb(accent)
    draw.ellipse((int(width * 0.03), int(height * 0.02), int(width * 0.35), int(height * 0.28)), fill=(*rgb, 72))
    draw.ellipse((int(width * 0.65), int(height * 0.02), int(width * 0.96), int(height * 0.30)), fill=(*hex_to_rgb("#4c7dff"), 52))
    blur_radius = 50 if profile.id == "portrait" else 42
    overlay = overlay.filter(ImageFilter.GaussianBlur(radius=blur_radius))
    image.alpha_composite(overlay)


def draw_header(draw: ImageDraw.ImageDraw, scene: Scene, profile: Profile) -> None:
    title_font = load_font(TITLE_FONT_PATH, profile.title_size)
    body_font = load_font(FONT_PATH, profile.body_size)
    kicker_font = load_font(TITLE_FONT_PATH, profile.footer_size)
    label_font = load_font(TITLE_FONT_PATH, profile.footer_size - 2)
    quote_font = load_font(FONT_PATH, profile.quote_size)
    width, height = profile.width, profile.height

    if profile.id == "landscape":
        rounded_box(draw, (44, 36, 492, 136), 28, (255, 255, 255, 214), (12, 24, 49, 18))
        draw.text((72, 62), scene.hook, font=kicker_font, fill=(125, 135, 154))
        title_lines = wrap_text(draw, scene.title, title_font, 420)
        y = 88
        for line in title_lines[:3]:
            draw.text((72, y), line, font=title_font, fill=(12, 24, 49))
            y += int(profile.title_size * 1.02)

        tag_x = 72
        tag_y = 202
        tag_font = load_font(FONT_PATH, 18)
        for tag in scene.tags:
            bbox = draw.textbbox((0, 0), tag, font=tag_font)
            tag_w = bbox[2] - bbox[0] + 34
            rounded_box(draw, (tag_x, tag_y, tag_x + tag_w, tag_y + 38), 19, (255, 255, 255, 224), (12, 24, 49, 22))
            draw.text((tag_x + 17, tag_y + 10), tag, font=tag_font, fill=(12, 24, 49))
            tag_x += tag_w + 12

        rounded_box(draw, (56, 474, 598, 662), 30, (255, 255, 255, 224), (12, 24, 49, 18))
        draw.text((84, 500), scene.label, font=label_font, fill=(125, 135, 154))
        summary_lines = wrap_text(draw, scene.summary, body_font, 470)
        y = 534
        for line in summary_lines[:3]:
            draw.text((84, y), line, font=body_font, fill=(12, 24, 49))
            y += int(profile.body_size * 1.32)

        rounded_box(draw, (692, 474, 1226, 662), 30, (255, 255, 255, 220), (12, 24, 49, 18))
        draw.text((722, 500), "品牌配音节奏", font=label_font, fill=(125, 135, 154))
        quote_lines = wrap_text(draw, f"“{scene.narration}”", quote_font, 464)
        y = 536
        for line in quote_lines[:4]:
            draw.text((722, y), line, font=quote_font, fill=(27, 58, 104))
            y += int(profile.quote_size * 1.28)
    else:
        rounded_box(draw, (54, 62, width - 54, 204), 42, (255, 255, 255, 214), (12, 24, 49, 18))
        draw.text((92, 100), scene.hook, font=kicker_font, fill=(125, 135, 154))
        title_lines = wrap_text(draw, scene.title, title_font, width - 176)
        y = 136
        for line in title_lines[:4]:
            draw.text((92, y), line, font=title_font, fill=(12, 24, 49))
            y += int(profile.title_size * 1.02)

        tag_font = load_font(FONT_PATH, 26)
        tag_x = 92
        tag_y = 350
        for tag in scene.tags:
            bbox = draw.textbbox((0, 0), tag, font=tag_font)
            tag_w = bbox[2] - bbox[0] + 38
            rounded_box(draw, (tag_x, tag_y, tag_x + tag_w, tag_y + 52), 25, (255, 255, 255, 224), (12, 24, 49, 22))
            draw.text((tag_x + 19, tag_y + 13), tag, font=tag_font, fill=(12, 24, 49))
            tag_y += 68

        rounded_box(draw, (64, height - 620, width - 64, height - 420), 34, (255, 255, 255, 224), (12, 24, 49, 18))
        draw.text((96, height - 584), scene.label, font=label_font, fill=(125, 135, 154))
        summary_lines = wrap_text(draw, scene.summary, body_font, width - 188)
        y = height - 540
        for line in summary_lines[:3]:
            draw.text((96, y), line, font=body_font, fill=(12, 24, 49))
            y += int(profile.body_size * 1.36)

        rounded_box(draw, (64, height - 390, width - 64, height - 118), 34, (255, 255, 255, 220), (12, 24, 49, 18))
        draw.text((96, height - 352), "品牌配音节奏", font=label_font, fill=(125, 135, 154))
        quote_lines = wrap_text(draw, f"“{scene.narration}”", quote_font, width - 188)
        y = height - 308
        for line in quote_lines[:5]:
            draw.text((96, y), line, font=quote_font, fill=(27, 58, 104))
            y += int(profile.quote_size * 1.30)


def draw_scene_illustration(draw: ImageDraw.ImageDraw, scene: Scene, profile: Profile) -> None:
    width, height = profile.width, profile.height
    if profile.id == "landscape":
        base_x = int(width * 0.62)
        base_y = int(height * 0.28)
    else:
        base_x = int(width * 0.50)
        base_y = int(height * 0.49)

    if scene.id == "welcome":
        draw.ellipse((base_x + 120, base_y - 120, base_x + 220, base_y - 20), fill=(255, 232, 186, 255))
        rounded_box(draw, (base_x - 250, base_y + 20, base_x - 140, base_y + 220), 48, (*hex_to_rgb("#ff7a59"), 255))
        draw.ellipse((base_x - 220, base_y - 24, base_x - 170, base_y + 26), fill=(255, 221, 183, 255))
        rounded_box(draw, (base_x - 120, base_y + 70, base_x - 30, base_y + 240), 42, (*hex_to_rgb("#4c7dff"), 255))
        draw.ellipse((base_x - 95, base_y + 28, base_x - 55, base_y + 68), fill=(255, 221, 183, 255))
        rounded_box(draw, (base_x + 24, base_y + 150, base_x + 134, base_y + 292), 44, (*hex_to_rgb("#ffb258"), 255))
    elif scene.id == "hub":
        rounded_box(draw, (base_x - 250, base_y - 80, base_x + 250, base_y + 180), 40, (255, 255, 255, 188), (12, 24, 49, 18))
        rounded_box(draw, (base_x - 210, base_y - 30, base_x + 10, base_y + 120), 30, (255, 250, 241, 244), (12, 24, 49, 16))
        rounded_box(draw, (base_x + 36, base_y - 30, base_x + 210, base_y + 120), 30, (240, 248, 255, 244), (12, 24, 49, 16))
        rounded_box(draw, (base_x - 210, base_y + 136, base_x + 210, base_y + 204), 26, (240, 255, 248, 244), (12, 24, 49, 16))
    elif scene.id == "deeprare":
        rounded_box(draw, (base_x - 260, base_y - 90, base_x + 260, base_y + 190), 40, (12, 24, 49, 235))
        rounded_box(draw, (base_x - 216, base_y - 6, base_x - 10, base_y + 102), 26, (29, 73, 97, 255))
        rounded_box(draw, (base_x + 24, base_y - 6, base_x + 216, base_y + 102), 26, (41, 66, 114, 255))
        rounded_box(draw, (base_x - 216, base_y + 124, base_x + 216, base_y + 164), 18, (255, 255, 255, 22))
        font = load_font(FONT_PATH, 22 if profile.id == "landscape" else 30)
        draw.text((base_x - 190, base_y + 131), "脾肿大 / 骨痛 / 血红蛋白下降", font=font, fill=(255, 255, 255))
    elif scene.id == "avatar":
        for radius in (132, 96):
            draw.ellipse((base_x - radius, base_y - radius, base_x + radius, base_y + radius), outline=(12, 24, 49, 48), width=2)
        draw.ellipse((base_x - 70, base_y - 58, base_x + 70, base_y + 82), fill=(255, 224, 204, 255))
        rounded_box(draw, (base_x - 234, base_y - 138, base_x - 64, base_y - 22), 28, (255, 255, 255, 214), (12, 24, 49, 18))
        rounded_box(draw, (base_x + 56, base_y + 104, base_x + 276, base_y + 234), 28, (255, 255, 255, 214), (12, 24, 49, 18))
    elif scene.id == "community":
        rounded_box(draw, (base_x - 276, base_y - 90, base_x - 86, base_y + 118), 32, (255, 240, 232, 232), (12, 24, 49, 18))
        rounded_box(draw, (base_x - 46, base_y - 90, base_x + 144, base_y + 118), 32, (232, 255, 248, 232), (12, 24, 49, 18))
        rounded_box(draw, (base_x + 184, base_y - 90, base_x + 374, base_y + 118), 32, (236, 242, 255, 232), (12, 24, 49, 18))
        for node in ((base_x - 20, base_y + 164), (base_x + 116, base_y + 124), (base_x + 268, base_y + 176)):
            draw.ellipse((node[0] - 10, node[1] - 10, node[0] + 10, node[1] + 10), fill=(255, 255, 255, 255), outline=(12, 24, 49, 50))
    elif scene.id == "followup":
        for idx, color in enumerate(("#ffb061", "#ff9bc2", "#ff7a59")):
            x = base_x - 250 + idx * 122
            rounded_box(draw, (x, base_y + 80, x + 92, base_y + 214), 42, (*hex_to_rgb(color), 255))
        rounded_box(draw, (base_x + 66, base_y - 136, base_x + 320, base_y + 220), 36, (255, 255, 255, 214), (12, 24, 49, 18))
        rounded_box(draw, (base_x + 94, base_y - 102, base_x + 292, base_y + 12), 30, (*hex_to_rgb("#173a68"), 255))
        for radius in (74, 112):
            draw.ellipse((base_x + 178 - radius, base_y + 100 - radius, base_x + 178 + radius, base_y + 100 + radius), outline=(76, 125, 255, 66), width=2)


def render_scene_poster(scene: Scene, profile: Profile, output_path: Path) -> None:
    image = Image.new("RGBA", (profile.width, profile.height), (255, 255, 255, 255))
    draw_gradient_background(image, profile, scene.palette)
    draw = ImageDraw.Draw(image)
    draw_header(draw, scene, profile)
    draw_scene_illustration(draw, scene, profile)
    draw.text(
        (72 if profile.id == "landscape" else 80, 236 if profile.id == "landscape" else profile.height - 92),
        f"Chapter {scene.chapter}",
        font=load_font(TITLE_FONT_PATH, profile.footer_size),
        fill=hex_to_rgb(scene.accent),
    )
    image.convert("RGB").save(output_path, quality=95)


def generate_voice_track(text: str, output_path: Path) -> None:
    run(["say", "-v", VOICE_NAME, "-r", str(VOICE_RATE), "-o", str(output_path), text])


def format_srt_time(seconds: float) -> str:
    ms = int(round(seconds * 1000))
    hours = ms // 3_600_000
    ms %= 3_600_000
    minutes = ms // 60_000
    ms %= 60_000
    secs = ms // 1000
    ms %= 1000
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{ms:03d}"


def parse_srt_time(value: str) -> float:
    hours, minutes, rest = value.split(":")
    seconds, milliseconds = rest.split(",")
    return int(hours) * 3600 + int(minutes) * 60 + int(seconds) + int(milliseconds) / 1000


def write_voiceover_markdown(output_path: Path, scene_timings: list[dict]) -> None:
    lines = ["# MediChat-RD 品牌短片配音稿", ""]
    for timing in scene_timings:
        scene = timing["scene"]
        lines.append(f"## {scene.chapter}. {scene.label}")
        lines.append(f"- 时长：{timing['duration']:.2f} 秒")
        lines.append(f"- 配音：{scene.narration}")
        lines.append(f"- 标签：{' / '.join(scene.tags)}")
        lines.append("")
    output_path.write_text("\n".join(lines), encoding="utf-8")


def write_srt(output_path: Path, scene_timings: list[dict]) -> None:
    entries = []
    counter = 1
    current = 0.0
    for timing in scene_timings:
        scene = timing["scene"]
        duration = timing["duration"]
        text_lengths = [max(1, len(item)) for item in scene.subtitle_segments]
        total = sum(text_lengths)
        lead_in = 0.22
        lead_out = 0.24
        cursor = current + lead_in
        available = max(1.0, duration - lead_in - lead_out)
        for idx, segment in enumerate(scene.subtitle_segments):
            seg_duration = available * (text_lengths[idx] / total)
            start = cursor
            end = min(current + duration - lead_out, cursor + seg_duration)
            entries.append(f"{counter}\n{format_srt_time(start)} --> {format_srt_time(end)}\n{segment}\n")
            counter += 1
            cursor = end
        current += duration
    output_path.write_text("\n".join(entries), encoding="utf-8")


def create_scene_video(image_path: Path, audio_path: Path, output_path: Path, duration: float, profile: Profile) -> None:
    total_frames = int(math.ceil(duration * FPS))
    zoom_speed = "0.00032" if profile.id == "portrait" else "0.00045"
    zoom_expr = (
        f"zoompan=z='min(zoom+{zoom_speed},1.08)':"
        f"d={total_frames}:"
        "x='iw/2-(iw/zoom/2)':"
        "y='ih/2-(ih/zoom/2)':"
        f"fps={FPS}:"
        f"s={profile.width}x{profile.height}"
    )
    run(
        [
            "ffmpeg",
            "-y",
            "-loop",
            "1",
            "-i",
            str(image_path),
            "-i",
            str(audio_path),
            "-filter_complex",
            f"[0:v]scale={profile.width}:{profile.height},{zoom_expr},format=yuv420p[v];"
            f"[1:a]afade=t=in:st=0:d=0.16,afade=t=out:st={max(0.0, duration - 0.28):.2f}:d=0.28[a]",
            "-map",
            "[v]",
            "-map",
            "[a]",
            "-t",
            f"{duration:.2f}",
            "-r",
            str(FPS),
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            str(output_path),
        ]
    )


def draw_subtitle_overlay(image: Image.Image, text: str, font: ImageFont.FreeTypeFont, profile: Profile) -> None:
    draw = ImageDraw.Draw(image)
    max_width = profile.width - 180 if profile.id == "portrait" else profile.width - 240
    lines = wrap_text(draw, text, font, max_width)
    line_boxes = [draw.textbbox((0, 0), line, font=font) for line in lines]
    text_width = max((box[2] - box[0]) for box in line_boxes) if line_boxes else 0
    line_height = max((box[3] - box[1]) for box in line_boxes) if line_boxes else 0
    gap = 12 if profile.id == "portrait" else 10
    block_height = len(lines) * line_height + max(0, len(lines) - 1) * gap
    padding_x = 32 if profile.id == "portrait" else 30
    padding_y = 24 if profile.id == "portrait" else 22
    box_left = int((profile.width - text_width) / 2) - padding_x
    box_top = profile.height - block_height - (112 if profile.id == "portrait" else 84)
    box_right = int((profile.width + text_width) / 2) + padding_x
    box_bottom = box_top + block_height + padding_y * 2
    rounded_box(draw, (box_left, box_top, box_right, box_bottom), 32 if profile.id == "portrait" else 28, (23, 58, 104, 176))

    y = box_top + padding_y
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        line_width = bbox[2] - bbox[0]
        x = (profile.width - line_width) / 2
        draw.text((x, y), line, font=font, fill=(255, 255, 255), stroke_width=2, stroke_fill=(51, 30, 12))
        y += line_height + gap


def burn_subtitles(input_mp4: Path, srt_path: Path, output_mp4: Path, profile: Profile) -> None:
    entries: list[tuple[float, float, str]] = []
    for block in srt_path.read_text(encoding="utf-8").strip().split("\n\n"):
        lines = [line for line in block.splitlines() if line.strip()]
        if len(lines) < 3 or "-->" not in lines[1]:
            continue
        start_text, end_text = [part.strip() for part in lines[1].split("-->", 1)]
        text = " ".join(lines[2:]).strip()
        entries.append((parse_srt_time(start_text), parse_srt_time(end_text), text))

    subtitle_font = load_font(FONT_PATH, 44 if profile.id == "portrait" else 34)
    with tempfile.TemporaryDirectory(prefix=f"medichatrd-{profile.id}-subtitle-") as tmpdir:
        temp_video = Path(tmpdir) / "video_only.mp4"
        reader = imageio.get_reader(str(input_mp4))
        meta = reader.get_meta_data()
        fps = float(meta.get("fps", FPS))
        writer = imageio.get_writer(
            str(temp_video),
            fps=fps,
            codec="libx264",
            quality=8,
            pixelformat="yuv420p",
            macro_block_size=1,
        )
        try:
            for frame_index, frame in enumerate(reader):
                current_time = frame_index / fps
                pil = Image.fromarray(frame).convert("RGBA")
                active_text = next((text for start, end, text in entries if start <= current_time <= end), None)
                if active_text:
                    draw_subtitle_overlay(pil, active_text, subtitle_font, profile)
                writer.append_data(np.asarray(pil.convert("RGB")))
        finally:
            reader.close()
            writer.close()

        run(
            [
                "ffmpeg",
                "-y",
                "-i",
                str(temp_video),
                "-i",
                str(input_mp4),
                "-map",
                "0:v:0",
                "-map",
                "1:a:0",
                "-c:v",
                "copy",
                "-c:a",
                "copy",
                "-shortest",
                str(output_mp4),
            ]
        )


def zip_package(folder: Path) -> Path:
    archive = shutil.make_archive(str(folder.parent / folder.name), "zip", root_dir=str(folder))
    return Path(archive)


def build_profile(profile: Profile, output_root: Path, scene_timings: list[dict], subtitles_path: Path) -> dict:
    posters_dir = output_root / "posters"
    scenes_dir = output_root / "scenes"
    video_dir = output_root / "video"
    for path in (posters_dir, scenes_dir, video_dir):
        path.mkdir(parents=True, exist_ok=True)

    concat_lines = []
    for index, item in enumerate(scene_timings, start=1):
        scene = item["scene"]
        audio_path = item["audio_path"]
        duration = item["duration"]
        poster_path = posters_dir / f"{index:02d}_{scene.id}.png"
        scene_mp4 = scenes_dir / f"{index:02d}_{scene.id}.mp4"
        render_scene_poster(scene, profile, poster_path)
        create_scene_video(poster_path, audio_path, scene_mp4, duration, profile)
        concat_lines.append(f"file '{scene_mp4.as_posix()}'")

    concat_path = output_root / "scene_concat.txt"
    concat_path.write_text("\n".join(concat_lines), encoding="utf-8")
    master_mp4 = video_dir / f"medichatrd_brand_story_{profile.id}.mp4"
    subtitled_mp4 = video_dir / f"medichatrd_brand_story_{profile.id}_subtitled.mp4"
    run([
        "ffmpeg",
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(concat_path),
        "-c",
        "copy",
        str(master_mp4),
    ])
    burn_subtitles(master_mp4, subtitles_path, subtitled_mp4, profile)
    return {
        "masterMp4": str(master_mp4),
        "subtitledMp4": str(subtitled_mp4),
    }


def generate_campaign_pack(output_root: Path) -> dict:
    output_root.mkdir(parents=True, exist_ok=True)
    audio_dir = output_root / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)

    scene_timings: list[dict] = []
    current = 0.0
    for index, scene in enumerate(SCENES, start=1):
        audio_path = audio_dir / f"{index:02d}_{scene.id}.aiff"
        generate_voice_track(scene.narration, audio_path)
        audio_duration = probe_duration(audio_path)
        duration = max(audio_duration + 0.62, 5.2)
        scene_timings.append(
            {
                "scene": scene,
                "audio_path": audio_path,
                "audio_duration": audio_duration,
                "duration": duration,
                "start": current,
                "end": current + duration,
            }
        )
        current += duration

    voiceover_path = output_root / "medichatrd_brand_voiceover.md"
    subtitles_path = output_root / "medichatrd_brand_zh.srt"
    storyboard_path = output_root / "medichatrd_brand_storyboard.json"
    write_voiceover_markdown(voiceover_path, scene_timings)
    write_srt(subtitles_path, scene_timings)
    storyboard_path.write_text(
        json.dumps(
            {
                "generatedAt": datetime.now().isoformat(),
                "fps": FPS,
                "voice": {"name": VOICE_NAME, "rate": VOICE_RATE},
                "profiles": [{"id": p.id, "width": p.width, "height": p.height} for p in PROFILES],
                "scenes": [
                    {
                        "chapter": item["scene"].chapter,
                        "label": item["scene"].label,
                        "title": item["scene"].title,
                        "hook": item["scene"].hook,
                        "summary": item["scene"].summary,
                        "narration": item["scene"].narration,
                        "subtitleSegments": item["scene"].subtitle_segments,
                        "duration": round(item["duration"], 3),
                        "start": round(item["start"], 3),
                        "end": round(item["end"], 3),
                    }
                    for item in scene_timings
                ],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    profile_outputs = {}
    for profile in PROFILES:
        profile_root = output_root / profile.id
        profile_outputs[profile.id] = build_profile(profile, profile_root, scene_timings, subtitles_path)

    zip_path = zip_package(output_root)
    return {
        "outputRoot": str(output_root),
        "voiceover": str(voiceover_path),
        "subtitles": str(subtitles_path),
        "storyboard": str(storyboard_path),
        "profiles": profile_outputs,
        "zip": str(zip_path),
    }


if __name__ == "__main__":
    package = generate_campaign_pack(DEFAULT_OUTPUT_ROOT)
    print(json.dumps(package, ensure_ascii=False, indent=2))
