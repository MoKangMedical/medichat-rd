"""
MediChat-RD Demo 视频 - 旁白字幕合成
1. 生成中文旁白音频 (edge-tts)
2. 生成SRT字幕
3. ffmpeg合成最终视频
"""

import asyncio
import edge_tts
import subprocess
import os
import json

PROJECT = os.path.dirname(os.path.abspath(__file__))
SRC_VIDEO = os.path.join(PROJECT, "docs", "demo-video.mp4")
OUT_VIDEO = os.path.join(PROJECT, "docs", "demo-video-final.mp4")
TMP = os.path.join(PROJECT, "docs", "tmp_audio")
os.makedirs(TMP, exist_ok=True)

# 中文语音 - 使用云希（成熟男声，适合科技产品介绍）
VOICE = "zh-CN-YunxiNeural"

# 场景定义：每段旁白 + 对应视频时间段（秒）
SCENES = [
    {
        "id": "intro",
        "text": "大家好，欢迎来到MediChat-RD。这是一款基于多Agent协作的罕见病AI辅助诊断平台。",
        "start": 0,
        "end": 6,
    },
    {
        "id": "problem",
        "text": "在中国，有两千万罕见病患者。他们平均需要四点三年才能确诊，要看七到八位医生，超过一半曾被误诊。我们的目标，是把这个时间压缩到四十八小时。",
        "start": 6,
        "end": 13,
    },
    {
        "id": "symptom",
        "text": "让我们来看一个真实案例。一位五岁男孩，脾脏肿大、骨痛、血小板减少。家长把这些症状输入系统。",
        "start": 13,
        "end": 19,
    },
    {
        "id": "result",
        "text": "系统在几秒内返回了结果：戈谢病，匹配度百分之九十五。相关基因GBA，建议做酶活性检测和基因检测。",
        "start": 19,
        "end": 25,
    },
    {
        "id": "tech",
        "text": "系统目前已收录三十种罕见病，覆盖九大分类。背后接入了OMIM、ClinVar等国际权威数据库，通过RAG增强减少AI幻觉。",
        "start": 25,
        "end": 31,
    },
    {
        "id": "ending",
        "text": "罕见病不罕见，每一个患者都值得被看见。MediChat-RD，用AI点亮希望。谢谢大家！",
        "start": 31,
        "end": 37,
    },
]


async def generate_audio(scene):
    """生成单段旁白音频"""
    out_path = os.path.join(TMP, f"{scene['id']}.mp3")
    communicate = edge_tts.Communicate(scene["text"], VOICE, rate="+10%")
    await communicate.save(out_path)
    duration = float(subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", out_path]
    ).decode().strip())
    print(f"  ✅ {scene['id']}.mp3 ({duration:.1f}s)")
    return out_path, duration


async def main():
    print("=" * 50)
    print("🎙️ MediChat-RD 旁白字幕合成")
    print("=" * 50)

    # Step 1: 生成所有音频
    print("\n📢 Step 1: 生成旁白音频...")
    audio_files = []
    for scene in SCENES:
        path, dur = await generate_audio(scene)
        audio_files.append({"scene": scene, "path": path, "duration": dur})

    # Step 2: 按时间轴拼接音频（静音填充到视频长度）
    print("\n🔗 Step 2: 拼接音频轨道...")
    # 获取视频总时长
    vid_duration = float(subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", SRC_VIDEO]
    ).decode().strip())
    print(f"  视频时长: {vid_duration:.1f}s")

    # 创建完整音频轨道：每个场景音频放在对应时间段
    concat_filter = ""
    inputs = []
    input_idx = 0

    for af in audio_files:
        scene = af["scene"]
        # 音频延迟到对应开始时间
        delay_ms = int(scene["start"] * 1000)
        inputs.extend(["-i", af["path"]])
        if input_idx == 0:
            concat_filter += f"[{input_idx}:a]adelay={delay_ms}|{delay_ms}[a{input_idx}];"
        else:
            concat_filter += f"[{input_idx}:a]adelay={delay_ms}|{delay_ms}[a{input_idx}];"
        input_idx += 1

    # 混合所有延迟后的音频
    mix_inputs = "".join(f"[a{i}]" for i in range(input_idx))
    concat_filter += f"{mix_inputs}amix=inputs={input_idx}:duration=longest:dropout_transition=2[aout]"

    mixed_audio = os.path.join(TMP, "mixed_audio.aac")
    cmd = ["ffmpeg", "-y"] + inputs + [
        "-filter_complex", concat_filter,
        "-map", "[aout]",
        "-t", str(vid_duration),
        "-c:a", "aac", "-b:a", "128k",
        mixed_audio
    ]
    subprocess.run(cmd, capture_output=True)
    print(f"  ✅ 混合音频: {mixed_audio}")

    # Step 3: 生成SRT字幕
    print("\n📝 Step 3: 生成SRT字幕...")
    srt_path = os.path.join(TMP, "subtitles.srt")

    def format_srt_time(seconds):
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        ms = int((seconds % 1) * 1000)
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

    with open(srt_path, "w", encoding="utf-8") as f:
        for i, af in enumerate(audio_files, 1):
            scene = af["scene"]
            start = format_srt_time(scene["start"])
            end = format_srt_time(scene["end"])
            f.write(f"{i}\n{start} --> {end}\n{scene['text']}\n\n")
    print(f"  ✅ 字幕文件: {srt_path}")

    # Step 4: 合成最终视频
    print("\n🎬 Step 4: 合成最终视频...")
    # 使用ffmpeg把字幕烧录进去 + 添加音频
    # 字幕样式：底部居中，白字黑边，字号20
    srt_escaped = srt_path.replace(":", "\\:").replace("'", "\\'")
    subtitle_filter = f"subtitles='{srt_escaped}':force_style='FontName=Noto Sans CJK SC,FontSize=16,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,Outline=2,Shadow=1,MarginV=30'"

    cmd = [
        "ffmpeg", "-y",
        "-i", SRC_VIDEO,
        "-i", mixed_audio,
        "-vf", subtitle_filter,
        "-map", "0:v", "-map", "1:a",
        "-c:v", "libx264", "-preset", "medium", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k",
        "-shortest",
        OUT_VIDEO
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  ⚠️ ffmpeg stderr: {result.stderr[-500:]}")
        # Fallback: 不烧字幕，只加音频
        print("  🔄 尝试不带字幕合成...")
        cmd = [
            "ffmpeg", "-y",
            "-i", SRC_VIDEO,
            "-i", mixed_audio,
            "-map", "0:v", "-map", "1:a",
            "-c:v", "copy", "-c:a", "aac", "-b:a", "128k",
            "-shortest",
            OUT_VIDEO
        ]
        subprocess.run(cmd, capture_output=True)

    if os.path.exists(OUT_VIDEO):
        size_mb = os.path.getsize(OUT_VIDEO) / 1024 / 1024
        dur = float(subprocess.check_output(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", OUT_VIDEO]
        ).decode().strip())
        print(f"\n🎉 完成！")
        print(f"📹 文件: {OUT_VIDEO}")
        print(f"📏 大小: {size_mb:.1f} MB")
        print(f"⏱️ 时长: {dur:.1f}s")
    else:
        print("❌ 最终视频生成失败")


if __name__ == "__main__":
    asyncio.run(main())
