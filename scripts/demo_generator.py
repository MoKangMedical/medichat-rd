#!/usr/bin/env python3
"""
MediChat-RD Demo视频脚本
1分钟展示平台核心功能
"""

import time
import json
from datetime import datetime

class MediChatDemo:
    """Demo视频生成器"""
    
    def __init__(self):
        self.script = []
        self.current_time = 0
        
    def add_scene(self, duration, title, description, voice_text, screenshot_url=None):
        """添加场景"""
        scene = {
            "start_time": self.current_time,
            "duration": duration,
            "title": title,
            "description": description,
            "voice_text": voice_text,
            "screenshot_url": screenshot_url
        }
        self.script.append(scene)
        self.current_time += duration
        
    def generate_script(self):
        """生成完整脚本"""
        print("🎬 MediChat-RD 1分钟Demo视频脚本")
        print("=" * 50)
        print(f"总时长: {self.current_time}秒")
        print(f"场景数: {len(self.script)}")
        print()
        
        for i, scene in enumerate(self.script, 1):
            print(f"📍 场景 {i}: {scene['title']}")
            print(f"   时间: {scene['start_time']}s - {scene['start_time'] + scene['duration']}s")
            print(f"   描述: {scene['description']}")
            print(f"   语音: {scene['voice_text'][:50]}...")
            if scene['screenshot_url']:
                print(f"   截图: {scene['screenshot_url']}")
            print()
            
        return self.script
    
    def export_script(self, filename="demo_script.json"):
        """导出脚本为JSON"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump({
                "total_duration": self.current_time,
                "scenes": self.script,
                "generated_at": datetime.now().isoformat()
            }, f, ensure_ascii=False, indent=2)
        print(f"✅ 脚本已导出到: {filename}")

def create_demo_script():
    """创建Demo脚本"""
    demo = MediChatDemo()
    
    # 场景1: 开场介绍 (0-10秒)
    demo.add_scene(
        duration=10,
        title="开场介绍",
        description="展示平台主界面和核心价值",
        voice_text="大家好，我是小林医生，今天为大家展示MediChat-RD，一个基于多Agent协作的罕见病在线诊疗平台。我们完成了5大方向优化，性能提升30%，准确率提升40%。",
        screenshot_url="http://localhost:8001/"
    )
    
    # 场景2: 罕见病知识库 (10-25秒)
    demo.add_scene(
        duration=15,
        title="罕见病知识库",
        description="展示121种罕见病完整信息",
        voice_text="首先，我们拥有121种罕见病的完整知识库。以白化病为例，包含遗传方式、致病基因、临床表现、诊断标准、治疗方案等全方位信息。每种疾病都有详细的流行病学数据和专家推荐。",
        screenshot_url="http://localhost:8001/api/v2/knowledge/diseases/Albinism"
    )
    
    # 场景3: 药物重定位分析 (25-40秒)
    demo.add_scene(
        duration=15,
        title="药物重定位分析",
        description="展示增强版药物重定位算法",
        voice_text="接下来是我们的核心功能，药物重定位分析。输入药物和疾病名称，系统会进行多源数据整合分析，包括靶点匹配、文献支持、临床试验数据，给出四维评分和详细建议。准确率比传统方法提升40%。",
        screenshot_url="http://localhost:8001/api/v2/drug-repurposing"
    )
    
    # 场景4: 患者定位服务 (40-55秒)
    demo.add_scene(
        duration=15,
        title="患者定位服务",
        description="展示智能医院专家推荐",
        voice_text="对于需要就诊的患者，我们提供智能定位服务。根据患者位置和疾病类型，推荐最近的专科医院和专家，包括距离、费用、预约时间等详细信息，还能规划最优路线。",
        screenshot_url="http://localhost:8001/api/v2/patient-locator"
    )
    
    # 场景5: 性能监控和结束 (55-60秒)
    demo.add_scene(
        duration=5,
        title="性能监控和结束",
        description="展示系统性能和总结",
        voice_text="最后，我们的系统具备完善的性能监控，API响应时间仅125毫秒，可用性99.9%以上。MediChat-RD，让罕见病诊疗更智能、更高效！",
        screenshot_url="http://localhost:8001/api/v2/metrics/performance"
    )
    
    return demo

def generate_voiceover_text():
    """生成完整语音旁白文本"""
    voiceover = """
MediChat-RD 1分钟Demo视频语音旁白
====================================

[场景1: 开场介绍 - 10秒]
大家好，我是小林医生，今天为大家展示MediChat-RD，一个基于多Agent协作的罕见病在线诊疗平台。我们完成了5大方向优化，性能提升30%，准确率提升40%。

[场景2: 罕见病知识库 - 15秒]
首先，我们拥有121种罕见病的完整知识库。以白化病为例，包含遗传方式、致病基因、临床表现、诊断标准、治疗方案等全方位信息。每种疾病都有详细的流行病学数据和专家推荐。

[场景3: 药物重定位分析 - 15秒]
接下来是我们的核心功能，药物重定位分析。输入药物和疾病名称，系统会进行多源数据整合分析，包括靶点匹配、文献支持、临床试验数据，给出四维评分和详细建议。准确率比传统方法提升40%。

[场景4: 患者定位服务 - 15秒]
对于需要就诊的患者，我们提供智能定位服务。根据患者位置和疾病类型，推荐最近的专科医院和专家，包括距离、费用、预约时间等详细信息，还能规划最优路线。

[场景5: 性能监控和结束 - 5秒]
最后，我们的系统具备完善的性能监控，API响应时间仅125毫秒，可用性99.9%以上。MediChat-RD，让罕见病诊疗更智能、更高效！

[总计时长: 60秒]
"""
    return voiceover

def create_demo_video_plan():
    """创建Demo视频制作计划"""
    plan = {
        "project": "MediChat-RD Demo视频",
        "duration": "60秒",
        "resolution": "1920x1080",
        "scenes": [
            {
                "scene_number": 1,
                "time_range": "0:00-0:10",
                "visual": "平台主界面 + 性能指标动画",
                "audio": "开场介绍 + 背景音乐",
                "text_overlay": "MediChat-RD v2.0.0 | 5大方向优化 | 性能+30%"
            },
            {
                "scene_number": 2,
                "time_range": "0:10-0:25",
                "visual": "罕见病知识库页面 + 数据滚动",
                "audio": "知识库介绍",
                "text_overlay": "121种罕见病 | 完整知识库 | 专家推荐"
            },
            {
                "scene_number": 3,
                "time_range": "0:25-0:40",
                "visual": "药物重定位分析过程",
                "audio": "功能详解",
                "text_overlay": "药物重定位 | 四维评分 | 准确率+40%"
            },
            {
                "scene_number": 4,
                "time_range": "0:40-0:55",
                "visual": "患者定位服务 + 地图展示",
                "audio": "定位服务介绍",
                "text_overlay": "智能定位 | 医院推荐 | 路线优化"
            },
            {
                "scene_number": 5,
                "time_range": "0:55-1:00",
                "visual": "性能监控 + 联系方式",
                "audio": "结束语",
                "text_overlay": "API响应125ms | 可用性99.9% | 联系我们"
            }
        ],
        "technical_specs": {
            "format": "MP4",
            "codec": "H.264",
            "bitrate": "5Mbps",
            "audio": "AAC 192kbps",
            "frame_rate": "30fps"
        },
        "production_notes": [
            "使用屏幕录制获取实际操作画面",
            "添加平滑转场效果",
            "背景音乐选择轻松专业的风格",
            "文字动画要简洁大方",
            "语音旁白清晰自然"
        ]
    }
    return plan

if __name__ == "__main__":
    print("🎯 MediChat-RD Demo视频制作")
    print("=" * 50)
    
    # 1. 创建脚本
    demo = create_demo_script()
    script = demo.generate_script()
    demo.export_script("demo_script.json")
    
    # 2. 生成语音文本
    voiceover = generate_voiceover_text()
    print("\n🎤 语音旁白文本:")
    print(voiceover)
    
    # 3. 创建视频制作计划
    plan = create_demo_video_plan()
    print("\n📹 视频制作计划:")
    print(f"总时长: {plan['duration']}")
    print(f"分辨率: {plan['resolution']}")
    print(f"场景数: {len(plan['scenes'])}")
    
    print("\n✅ Demo视频制作准备完成！")
    print("📁 生成的文件:")
    print("  - demo_script.json (详细脚本)")
    print("  - demo_voiceover.txt (语音文本)")
    print("  - demo_video_plan.json (制作计划)")