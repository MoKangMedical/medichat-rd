"""
MediChat-RD Demo 视频录制脚本
自动演示：前端交互 + API接口 + 罕见病诊断
输出：MP4视频
"""

import subprocess, time, sys, os, shutil, json
from playwright.sync_api import sync_playwright

PROJECT = os.path.dirname(os.path.abspath(__file__))
VIDEO_OUT = os.path.join(PROJECT, "docs", "demo-video.mp4")
VP = {"width": 500, "height": 900}

# ---------- 演示文字（逐字输入效果） ----------
SYMPTOM_MSG = "医生您好，我孩子5岁了，肚子越来越大，脾脏肿大，经常骨痛，血小板减少"

def kill_port(port):
    subprocess.run(f"fuser -k {port}/tcp 2>/dev/null", shell=True, capture_output=True)

def start_server(name, cmd, cwd, port, wait_url):
    kill_port(port)
    proc = subprocess.Popen(cmd, cwd=cwd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    for i in range(30):
        try:
            import urllib.request
            urllib.request.urlopen(f"http://localhost:{port}{wait_url}", timeout=2)
            print(f"  ✅ {name} ready (port {port})")
            return proc
        except:
            time.sleep(1)
    print(f"  ⚠️ {name} timeout, continuing...")
    return proc

def slow_type(page, selector, text, delay=80):
    """逐字输入效果"""
    page.click(selector)
    for ch in text:
        page.keyboard.type(ch, delay=delay)
        time.sleep(0.02)

def record():
    print("=" * 50)
    print("🎬 MediChat-RD Demo 录制开始")
    print("=" * 50)

    # 1. 启动服务
    print("\n📦 启动服务...")
    venv_python = os.path.join(PROJECT, "venv", "bin", "python")
    if not os.path.exists(venv_python):
        venv_python = sys.executable
    
    demo_proc = start_server(
        "Demo API",
        f"{venv_python} demo_server.py",
        PROJECT, 8000, "/health"
    )
    fe_proc = start_server(
        "Frontend",
        f"{sys.executable} -m http.server 18080",
        os.path.join(PROJECT, "frontend", "preview"), 18080, "/"
    )

    os.makedirs(os.path.dirname(VIDEO_OUT), exist_ok=True)

    try:
        with sync_playwright() as p:
            print("\n🎥 启动浏览器录制...")
            browser = p.chromium.launch(headless=True)
            ctx = browser.new_context(
                viewport=VP,
                record_video_dir=os.path.dirname(VIDEO_OUT),
                record_video_size={"width": VP["width"], "height": VP["height"]},
            )
            page = ctx.new_page()

            # ---- Scene 1: 前端首页（标题页） ----
            print("  [1/8] 前端首页展示...")
            page.goto("http://localhost:18080/index.html")
            page.wait_for_timeout(4000)

            # ---- Scene 2: 滚动展示罕见病区 ----
            print("  [2/8] 滚动展示罕见病测试区...")
            page.evaluate("window.scrollTo({top: 600, behavior: 'smooth'})")
            page.wait_for_timeout(3000)
            page.evaluate("window.scrollTo({top: 0, behavior: 'smooth'})")
            page.wait_for_timeout(2000)

            # ---- Scene 3: 输入症状并发送 ----
            print("  [3/8] 输入罕见病症状...")
            textarea = page.locator("textarea")
            textarea.click()
            page.wait_for_timeout(500)
            slow_type(page, "textarea", SYMPTOM_MSG, delay=60)
            page.wait_for_timeout(1000)

            # ---- Scene 4: 发送消息 ----
            print("  [4/8] 发送消息...")
            page.locator("button:has-text('发送')").click()
            page.wait_for_timeout(3000)

            # ---- Scene 5: 滚动查看完整回复 ----
            print("  [5/8] 查看AI回复...")
            page.evaluate("window.scrollTo({top: document.body.scrollHeight, behavior: 'smooth'})")
            page.wait_for_timeout(4000)

            # ---- Scene 6: API文档页 ----
            print("  [6/8] 展示API文档...")
            page.goto("http://localhost:8000/docs")
            page.wait_for_timeout(4000)

            # ---- Scene 7: 罕见病API ----
            print("  [7/8] 展示罕见病数据库...")
            page.goto("http://localhost:8000/api/v1/rare-disease/diseases")
            page.wait_for_timeout(3000)

            # ---- Scene 8: 统计数据 ----
            print("  [8/8] 展示统计数据...")
            page.goto("http://localhost:8000/api/v1/rare-disease/statistics")
            page.wait_for_timeout(2000)

            # 结尾停留
            page.goto("http://localhost:18080/index.html")
            page.wait_for_timeout(3000)

            # 保存视频
            vid = page.video.path()
            ctx.close()
            browser.close()

            if vid and os.path.exists(vid):
                shutil.move(vid, VIDEO_OUT)
                size_mb = os.path.getsize(VIDEO_OUT) / 1024 / 1024
                print(f"\n🎉 录制完成！")
                print(f"📹 文件: {VIDEO_OUT}")
                print(f"📏 大小: {size_mb:.1f} MB")
            else:
                print("❌ 视频文件未生成")

    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback; traceback.print_exc()
    finally:
        for proc in [demo_proc, fe_proc]:
            if proc:
                proc.terminate()
                try: proc.wait(timeout=3)
                except: proc.kill()
        print("🧹 已清理")

if __name__ == "__main__":
    record()
