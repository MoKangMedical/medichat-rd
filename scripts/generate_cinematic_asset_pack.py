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
from typing import List

import imageio.v2 as imageio
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont


WIDTH = 1280
HEIGHT = 720
FPS = 24
VOICE_NAME = "Tingting"
VOICE_RATE = 190

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_ROOT = Path("/Users/apple/Desktop/medichatrd-demo-pack-20260407")
FONT_PATH = Path("/System/Library/Fonts/Supplemental/Arial Unicode.ttf")
TITLE_FONT_PATH = Path("/System/Library/Fonts/Helvetica.ttc")


@dataclass
class Scene:
    id: str
    chapter: str
    label: str
    title: str
    kicker: str
    tags: List[str]
    summary: str
    narration: str
    subtitle_segments: List[str]
    palette: tuple[str, str, str]
    accent: str


SCENES = [
    Scene(
        id="welcome",
        chapter="01",
        label="新确诊的夜晚",
        title="先让一个家庭被接住，再让产品开始工作",
        kicker="今晚 20:00 · 新确诊患者欢迎房",
        tags=["欢迎房", "病历整理", "情绪安放"],
        summary="先接住病历、检查和情绪，再让一个家庭慢慢稳下来。",
        narration="孩子刚拿到诊断的那几天，家里常常像被夜色压住。我们想做的第一件事，是先把病历、检查和情绪轻轻接住。",
        subtitle_segments=[
            "孩子刚拿到诊断的那几天，家里常常像被夜色压住。",
            "我们想做的第一件事，是先把病历、检查和情绪轻轻接住。",
        ],
        palette=("#fff0e5", "#fde7e1", "#f8f0ff"),
        accent="#ff7a59",
    ),
    Scene(
        id="hub",
        chapter="02",
        label="把慌张变成路径",
        title="患者中枢把病历、检查和下一步安排成可执行旅程",
        kicker="今天的第一条路径",
        tags=["患者中枢", "旅程总览", "一页进入"],
        summary="把今天最重要的事排好，让患者和家属知道下一步该做什么。",
        narration="患者中枢会把今天最重要的事排好。让家属知道下一步该问什么，该准备什么，也让患者知道自己并没有被落下。",
        subtitle_segments=[
            "患者中枢会把今天最重要的事排好。",
            "让家属知道下一步该问什么、该准备什么，也让患者知道自己并没有被落下。",
        ],
        palette=("#fff7e8", "#eef6ff", "#e7fff8"),
        accent="#0dbf9b",
    ),
    Scene(
        id="deeprare",
        chapter="03",
        label="诊断不再散乱",
        title="DeepRare 把零散描述整理成候选诊断和下一步检查",
        kicker="DeepRare 诊断工作台",
        tags=["DeepRare", "HPO 表型", "检查建议"],
        summary="把症状、表型和检查线索收束成更清晰的诊断路径。",
        narration="DeepRare 会把零散的描述整理成候选诊断和检查线索。患者终于能把害怕和症状一起讲清楚，不再只剩下模糊的担心。",
        subtitle_segments=[
            "DeepRare 会把零散的描述整理成候选诊断和检查线索。",
            "患者终于能把害怕和症状一起讲清楚，不再只剩下模糊的担心。",
        ],
        palette=("#f2f7ff", "#eefcff", "#fff6ea"),
        accent="#4c7dff",
    ),
    Scene(
        id="avatar",
        chapter="04",
        label="让分身替你开口",
        title="SecondMe 分身把患者身份、病程和第一条动态连接在一起",
        kicker="人格卡与首帖草稿",
        tags=["SecondMe", "AI 分身", "首条动态"],
        summary="让患者更稳地表达病程、需求和此刻最想得到的帮助。",
        narration="SecondMe 分身不替患者说假话。它只是帮患者更稳地说出此刻最需要的帮助，让第一句开口不再那么难。",
        subtitle_segments=[
            "SecondMe 分身不替患者说假话。",
            "它只是帮患者更稳地说出此刻最需要的帮助，让第一句开口不再那么难。",
        ],
        palette=("#fff4ec", "#f4f1ff", "#effcff"),
        accent="#7a5af8",
    ),
    Scene(
        id="community",
        chapter="05",
        label="让病友真正说上话",
        title="欢迎房、家长圆桌和试验追踪，把支持、经验和机会聚到一个现场",
        kicker="公开社群现场",
        tags=["病友圈", "欢迎房", "临床试验机会"],
        summary="把支持、经验和机会聚到同一个现场，让回应真正流动起来。",
        narration="欢迎房、家长圆桌和试验追踪，让一个人慢慢变成一群人。回应、经验和希望，不再散落，而是在这里真正流动起来。",
        subtitle_segments=[
            "欢迎房、家长圆桌和试验追踪，让一个人慢慢变成一群人。",
            "回应、经验和希望，不再散落，而是在这里真正流动起来。",
        ],
        palette=("#fff7ea", "#f0fcff", "#eef6ff"),
        accent="#ff9d57",
    ),
    Scene(
        id="followup",
        chapter="06",
        label="陪伴留到日常里",
        title="陪伴玩偶和语音随访设备，让长期管理变得更温柔",
        kicker="陪伴与随访闭环",
        tags=["陪伴硬件", "语音随访", "长期管理"],
        summary="把玩偶陪伴和语音随访留在日常里，让长期管理更温柔。",
        narration="到了日常里，玩偶陪伴和语音随访会继续留在身边。让长期管理不再只有压力，也能有温柔的提醒和真正的陪伴。",
        subtitle_segments=[
            "到了日常里，玩偶陪伴和语音随访会继续留在身边。",
            "让长期管理不再只有压力，也能有温柔的提醒和真正的陪伴。",
        ],
        palette=("#fff7ef", "#f7f2ff", "#efffff"),
        accent="#4c7dff",
    ),
]


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
    return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))


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


def draw_gradient_background(image: Image.Image, palette: tuple[str, str, str]) -> None:
    top = hex_to_rgb(palette[0])
    middle = hex_to_rgb(palette[1])
    bottom = hex_to_rgb(palette[2])
    px = image.load()
    for y in range(HEIGHT):
        if y < HEIGHT / 2:
            t = y / (HEIGHT / 2)
            color = blend(top, middle, t)
        else:
            t = (y - HEIGHT / 2) / (HEIGHT / 2)
            color = blend(middle, bottom, t)
        for x in range(WIDTH):
            px[x, y] = color


def add_glow(image: Image.Image, xy: tuple[int, int], radius: int, color: str, alpha: int) -> None:
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    rgb = hex_to_rgb(color)
    draw.ellipse((xy[0] - radius, xy[1] - radius, xy[0] + radius, xy[1] + radius), fill=(*rgb, alpha))
    overlay = overlay.filter(ImageFilter.GaussianBlur(radius=42))
    image.alpha_composite(overlay)


def rounded_box(draw: ImageDraw.ImageDraw, box, radius: int, fill, outline=None, width: int = 1):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def render_scene_poster(scene: Scene, output_path: Path) -> None:
    image = Image.new("RGBA", (WIDTH, HEIGHT), (255, 255, 255, 255))
    draw_gradient_background(image, scene.palette)
    add_glow(image, (190, 130), 160, "#ffd16f", 80)
    add_glow(image, (1100, 140), 140, "#4c7dff", 64)

    draw = ImageDraw.Draw(image)
    title_font = load_font(TITLE_FONT_PATH, 54)
    subtitle_font = load_font(FONT_PATH, 22)
    kicker_font = load_font(TITLE_FONT_PATH, 20)
    label_font = load_font(TITLE_FONT_PATH, 18)
    body_font = load_font(FONT_PATH, 28)
    quote_font = load_font(FONT_PATH, 26)
    small_font = load_font(FONT_PATH, 18)

    rounded_box(draw, (42, 34, 470, 132), 28, (255, 255, 255, 210), (12, 24, 49, 18))
    draw.text((68, 58), scene.kicker, font=kicker_font, fill=(125, 135, 154))
    title_lines = wrap_text(draw, scene.title, title_font, 360)
    ty = 78
    for line in title_lines[:2]:
        draw.text((68, ty), line, font=title_font, fill=(12, 24, 49))
        ty += 58

    summary_box = (56, 468, 592, 660)
    rounded_box(draw, summary_box, 30, (255, 255, 255, 220), (12, 24, 49, 18))
    draw.text((84, 498), scene.label, font=label_font, fill=(125, 135, 154))
    summary_lines = wrap_text(draw, scene.summary, body_font, 460)
    sy = 528
    for line in summary_lines[:3]:
        draw.text((84, sy), line, font=body_font, fill=(12, 24, 49))
        sy += 38

    quote_box = (694, 474, 1228, 658)
    rounded_box(draw, quote_box, 30, (255, 255, 255, 216), (12, 24, 49, 18))
    draw.text((724, 502), "配音情绪线", font=label_font, fill=(125, 135, 154))
    quote_lines = wrap_text(draw, f"“{scene.narration}”", quote_font, 460)
    qy = 536
    for line in quote_lines[:4]:
        draw.text((724, qy), line, font=quote_font, fill=(27, 58, 104))
        qy += 34

    tag_x = 70
    for tag in scene.tags:
        bbox = draw.textbbox((0, 0), tag, font=small_font)
        tag_w = bbox[2] - bbox[0] + 34
        rounded_box(draw, (tag_x, 160, tag_x + tag_w, 198), 19, (255, 255, 255, 220), (12, 24, 49, 20))
        draw.text((tag_x + 17, 170), tag, font=small_font, fill=(12, 24, 49))
        tag_x += tag_w + 12

    accent = hex_to_rgb(scene.accent)
    if scene.id == "welcome":
        draw.ellipse((985, 94, 1085, 194), fill=(255, 232, 186, 255))
        rounded_box(draw, (160, 262, 250, 420), 42, (*hex_to_rgb("#ff7a59"), 255))
        draw.ellipse((187, 228, 223, 264), fill=(255, 221, 183, 255))
        rounded_box(draw, (258, 300, 328, 430), 34, (*hex_to_rgb("#4c7dff"), 255))
        draw.ellipse((278, 272, 308, 302), fill=(255, 221, 183, 255))
        rounded_box(draw, (346, 346, 430, 454), 40, (*hex_to_rgb("#ffb258"), 255))
    elif scene.id == "hub":
        rounded_box(draw, (648, 194, 1186, 444), 38, (255, 255, 255, 188), (12, 24, 49, 18))
        rounded_box(draw, (684, 238, 908, 384), 26, (255, 250, 241, 244), (12, 24, 49, 16))
        rounded_box(draw, (930, 238, 1142, 384), 26, (240, 248, 255, 244), (12, 24, 49, 16))
        rounded_box(draw, (684, 400, 1142, 458), 24, (240, 255, 248, 244), (12, 24, 49, 16))
    elif scene.id == "deeprare":
        rounded_box(draw, (648, 194, 1184, 470), 36, (12, 24, 49, 235))
        rounded_box(draw, (684, 280, 912, 390), 24, (29, 73, 97, 255))
        rounded_box(draw, (936, 280, 1142, 390), 24, (41, 66, 114, 255))
        rounded_box(draw, (684, 412, 1142, 452), 18, (255, 255, 255, 22))
        draw.text((700, 420), "脾肿大 / 骨痛 / 血红蛋白下降", font=subtitle_font, fill=(255, 255, 255))
    elif scene.id == "avatar":
        center = (900, 318)
        for radius in (126, 92):
            draw.ellipse((center[0] - radius, center[1] - radius, center[0] + radius, center[1] + radius), outline=(12, 24, 49, 48), width=2)
        draw.ellipse((840, 258, 960, 378), fill=(255, 224, 204, 255))
        rounded_box(draw, (682, 178, 820, 280), 26, (255, 255, 255, 214), (12, 24, 49, 18))
        rounded_box(draw, (980, 414, 1200, 544), 26, (255, 255, 255, 214), (12, 24, 49, 18))
    elif scene.id == "community":
        rounded_box(draw, (642, 214, 820, 422), 30, (255, 240, 232, 232), (12, 24, 49, 18))
        rounded_box(draw, (850, 214, 1028, 422), 30, (232, 255, 248, 232), (12, 24, 49, 18))
        rounded_box(draw, (1058, 214, 1236, 422), 30, (236, 242, 255, 232), (12, 24, 49, 18))
        for node in ((820, 450), (940, 412), (1092, 458)):
            draw.ellipse((node[0] - 8, node[1] - 8, node[0] + 8, node[1] + 8), fill=(255, 255, 255, 255), outline=(12, 24, 49, 50))
    elif scene.id == "followup":
        for idx, color in enumerate(("#ffb061", "#ff9bc2", "#ff7a59")):
            x = 690 + idx * 104
            rounded_box(draw, (x, 400, x + 82, 516), 40, (*hex_to_rgb(color), 255))
        rounded_box(draw, (932, 176, 1186, 500), 34, (255, 255, 255, 214), (12, 24, 49, 18))
        rounded_box(draw, (958, 206, 1160, 314), 28, (*hex_to_rgb("#173a68"), 255))
        for radius in (68, 96):
            draw.ellipse((1030 - radius, 392 - radius, 1030 + radius, 392 + radius), outline=(76, 125, 255, 66), width=2)

    draw.text((70, 220), f"Chapter {scene.chapter}", font=kicker_font, fill=accent)
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


def write_voiceover_markdown(output_path: Path, scene_timings: list[dict]) -> None:
    lines = ["# MediChat-RD 首页剧情 Demo 配音稿", ""]
    for timing in scene_timings:
        scene: Scene = timing["scene"]
        lines.append(f"## {scene.chapter}. {scene.label}")
        lines.append(f"- 时长：{timing['duration']:.2f} 秒")
        lines.append(f"- 配音：{scene.narration}")
        lines.append(f"- 关键词：{' / '.join(scene.tags)}")
        lines.append("")
    output_path.write_text("\n".join(lines), encoding="utf-8")


def write_srt(output_path: Path, scene_timings: list[dict]) -> None:
    entries = []
    counter = 1
    current = 0.0
    for timing in scene_timings:
        scene: Scene = timing["scene"]
        duration = timing["duration"]
        segments = scene.subtitle_segments
        text_lengths = [max(1, len(segment)) for segment in segments]
        total = sum(text_lengths)
        lead_in = 0.18
        lead_out = 0.22
        cursor = current + lead_in
        available = max(0.8, duration - lead_in - lead_out)
        for index, segment in enumerate(segments):
            share = text_lengths[index] / total
            seg_duration = available * share
            start = cursor
            end = min(current + duration - lead_out, cursor + seg_duration)
            entries.append(
                f"{counter}\n{format_srt_time(start)} --> {format_srt_time(end)}\n{segment}\n"
            )
            counter += 1
            cursor = end
        current += duration
    output_path.write_text("\n".join(entries), encoding="utf-8")


def create_scene_video(image_path: Path, audio_path: Path, output_path: Path, duration: float) -> None:
    total_frames = int(math.ceil(duration * FPS))
    zoom_expr = "zoompan=z='min(zoom+0.00045,1.08)':d={}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':fps={}".format(total_frames, FPS)
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
            f"[0:v]scale={WIDTH}:{HEIGHT},{zoom_expr},format=yuv420p[v];"
            f"[1:a]afade=t=in:st=0:d=0.18,afade=t=out:st={max(0.0, duration - 0.25):.2f}:d=0.25[a]",
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


def burn_subtitles(input_mp4: Path, srt_path: Path, output_mp4: Path) -> None:
    subtitle_entries: list[tuple[float, float, str]] = []
    raw_blocks = srt_path.read_text(encoding="utf-8").strip().split("\n\n")
    for block in raw_blocks:
        lines = [line for line in block.splitlines() if line.strip()]
        if len(lines) < 3 or "-->" not in lines[1]:
            continue
        start_text, end_text = [part.strip() for part in lines[1].split("-->", 1)]
        content = " ".join(lines[2:]).strip()
        if not content:
            continue
        start = parse_srt_time(start_text)
        end = parse_srt_time(end_text)
        subtitle_entries.append((start, end, content))

    subtitle_font = load_font(FONT_PATH, 34)
    with tempfile.TemporaryDirectory(prefix="medichatrd-subtitle-") as tmpdir:
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
        )
        try:
            for frame_index, frame in enumerate(reader):
                current_time = frame_index / fps
                pil = Image.fromarray(frame).convert("RGBA")
                active_text = next(
                    (text for start, end, text in subtitle_entries if start <= current_time <= end),
                    None,
                )
                if active_text:
                    draw_subtitle_overlay(pil, active_text, subtitle_font)
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


def parse_srt_time(value: str) -> float:
    hours, minutes, rest = value.split(":")
    seconds, milliseconds = rest.split(",")
    return (
        int(hours) * 3600
        + int(minutes) * 60
        + int(seconds)
        + int(milliseconds) / 1000
    )


def draw_subtitle_overlay(image: Image.Image, text: str, font: ImageFont.FreeTypeFont) -> None:
    draw = ImageDraw.Draw(image)
    lines = wrap_text(draw, text, font, WIDTH - 240)
    line_boxes = [draw.textbbox((0, 0), line, font=font) for line in lines]
    text_width = max((box[2] - box[0]) for box in line_boxes) if line_boxes else 0
    line_height = max((box[3] - box[1]) for box in line_boxes) if line_boxes else 0
    block_height = len(lines) * line_height + max(0, len(lines) - 1) * 10
    box_padding_x = 30
    box_padding_y = 22
    box_left = int((WIDTH - text_width) / 2) - box_padding_x
    box_top = HEIGHT - block_height - 76
    box_right = int((WIDTH + text_width) / 2) + box_padding_x
    box_bottom = box_top + block_height + box_padding_y * 2
    rounded_box(draw, (box_left, box_top, box_right, box_bottom), 28, (23, 58, 104, 172))

    y = box_top + box_padding_y
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        line_width = bbox[2] - bbox[0]
        x = (WIDTH - line_width) / 2
        draw.text(
            (x, y),
            line,
            font=font,
            fill=(255, 255, 255),
            stroke_width=2,
            stroke_fill=(51, 30, 12),
        )
        y += line_height + 10


def zip_package(folder: Path) -> Path:
    zip_base = folder.parent / folder.name
    archive = shutil.make_archive(str(zip_base), "zip", root_dir=str(folder))
    return Path(archive)


def generate_asset_pack(output_root: Path) -> dict:
    output_root.mkdir(parents=True, exist_ok=True)
    scenes_dir = output_root / "scenes"
    audio_dir = output_root / "audio"
    posters_dir = output_root / "posters"
    video_dir = output_root / "video"
    for path in (scenes_dir, audio_dir, posters_dir, video_dir):
        path.mkdir(parents=True, exist_ok=True)

    scene_timings = []
    concat_lines = []
    current = 0.0

    for index, scene in enumerate(SCENES, start=1):
        poster_path = posters_dir / f"{index:02d}_{scene.id}.png"
        audio_path = audio_dir / f"{index:02d}_{scene.id}.aiff"
        scene_video_path = scenes_dir / f"{index:02d}_{scene.id}.mp4"

        render_scene_poster(scene, poster_path)
        generate_voice_track(scene.narration, audio_path)
        audio_duration = probe_duration(audio_path)
        scene_duration = max(audio_duration + 0.45, 4.6)
        create_scene_video(poster_path, audio_path, scene_video_path, scene_duration)

        concat_lines.append(f"file '{scene_video_path.as_posix()}'")
        scene_timings.append(
            {
                "scene": scene,
                "audio_duration": audio_duration,
                "duration": scene_duration,
                "start": current,
                "end": current + scene_duration,
                "poster": poster_path.name,
                "audio": audio_path.name,
                "video": scene_video_path.name,
            }
        )
        current += scene_duration

    concat_path = output_root / "scene_concat.txt"
    concat_path.write_text("\n".join(concat_lines), encoding="utf-8")

    voiceover_path = output_root / "medichatrd_homepage_demo_voiceover.md"
    storyboard_path = output_root / "medichatrd_homepage_demo_storyboard.json"
    subtitles_path = output_root / "medichatrd_homepage_demo_zh.srt"
    master_mp4 = video_dir / "medichatrd_homepage_demo_master.mp4"
    master_webm = video_dir / "medichatrd_homepage_demo_master.webm"
    subtitled_mp4 = video_dir / "medichatrd_homepage_demo_master_subtitled.mp4"

    write_voiceover_markdown(voiceover_path, scene_timings)
    storyboard_path.write_text(
        json.dumps(
            {
                "generatedAt": datetime.now().isoformat(),
                "width": WIDTH,
                "height": HEIGHT,
                "fps": FPS,
                "voice": {"name": VOICE_NAME, "rate": VOICE_RATE},
                "scenes": [
                    {
                        "chapter": item["scene"].chapter,
                        "label": item["scene"].label,
                        "title": item["scene"].title,
                        "kicker": item["scene"].kicker,
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
    write_srt(subtitles_path, scene_timings)

    run(
        [
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
        ]
    )
    burn_subtitles(master_mp4, subtitles_path, subtitled_mp4)
    run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(master_mp4),
            "-c:v",
            "libvpx-vp9",
            "-b:v",
            "2M",
            "-c:a",
            "libopus",
            str(master_webm),
        ]
    )

    zip_path = zip_package(output_root)
    return {
        "outputRoot": str(output_root),
        "masterMp4": str(master_mp4),
        "subtitledMp4": str(subtitled_mp4),
        "masterWebm": str(master_webm),
        "subtitles": str(subtitles_path),
        "voiceover": str(voiceover_path),
        "storyboard": str(storyboard_path),
        "zip": str(zip_path),
    }


if __name__ == "__main__":
    package = generate_asset_pack(DEFAULT_OUTPUT_ROOT)
    print(json.dumps(package, ensure_ascii=False, indent=2))
