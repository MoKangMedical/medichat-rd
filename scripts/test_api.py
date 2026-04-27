#!/usr/bin/env python3
"""
MediChat API 快速测试脚本
测试小米MIMO模型集成
"""

import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "http://localhost:8000"


def test_health():
    """测试健康检查"""
    print("🔍 测试健康检查...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"状态: {response.status_code}")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    return response.status_code == 200


def test_agents():
    """测试Agent列表"""
    print("\n🤖 测试Agent列表...")
    response = requests.get(f"{BASE_URL}/api/v1/agents")
    print(f"状态: {response.status_code}")
    data = response.json()
    print(f"可用Agent: {len(data['agents'])} 个")
    for agent in data['agents']:
        print(f"  - {agent['name']}: {agent['role']}")
    return response.status_code == 200


def test_models():
    """测试模型信息"""
    print("\n🧠 测试模型信息...")
    response = requests.get(f"{BASE_URL}/api/v1/models")
    print(f"状态: {response.status_code}")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    return response.status_code == 200


def test_chat():
    """测试聊天功能"""
    print("\n💬 测试聊天功能...")
    
    # 测试消息
    test_messages = [
        "我最近总是头痛，伴有恶心，已经持续一周了",
        "头痛主要在早上发作，伴有视物模糊",
        "我有高血压病史，一直在服用降压药"
    ]
    
    session_id = None
    
    for i, message in enumerate(test_messages):
        print(f"\n📤 患者消息 {i+1}: {message}")
        
        payload = {"message": message}
        if session_id:
            payload["session_id"] = session_id
        
        response = requests.post(
            f"{BASE_URL}/api/v1/chat",
            json=payload
        )
        
        if response.status_code == 200:
            data = response.json()
            session_id = data.get("session_id")
            
            print(f"📥 Agent回复:")
            print(f"  Agent: {data.get('agent_name')}")
            print(f"  紧急程度: {data.get('urgency_level')}")
            print(f"  推荐科室: {data.get('recommended_department')}")
            print(f"  回复内容:\n{data.get('message')[:200]}...")
        else:
            print(f"❌ 错误: {response.status_code}")
            print(response.text)
    
    return True


def test_session_history():
    """测试会话历史"""
    print("\n📜 测试会话历史...")
    
    # 先创建一个会话
    response = requests.post(
        f"{BASE_URL}/api/v1/chat",
        json={"message": "测试消息"}
    )
    
    if response.status_code == 200:
        session_id = response.json().get("session_id")
        
        # 获取历史
        history_response = requests.get(
            f"{BASE_URL}/api/v1/sessions/{session_id}/history"
        )
        
        if history_response.status_code == 200:
            history = history_response.json()
            print(f"会话ID: {history['session_id']}")
            print(f"消息数量: {len(history['messages'])}")
            return True
    
    return False


def main():
    """运行所有测试"""
    print("=" * 50)
    print("🏥 MediChat API 测试")
    print("=" * 50)
    
    tests = [
        ("健康检查", test_health),
        ("Agent列表", test_agents),
        ("模型信息", test_models),
        ("聊天功能", test_chat),
        ("会话历史", test_session_history),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, "✅ 通过" if result else "❌ 失败"))
        except Exception as e:
            results.append((name, f"❌ 异常: {str(e)}"))
    
    print("\n" + "=" * 50)
    print("📊 测试结果汇总")
    print("=" * 50)
    
    for name, status in results:
        print(f"{name}: {status}")
    
    passed = sum(1 for _, status in results if "✅" in status)
    total = len(results)
    print(f"\n总计: {passed}/{total} 测试通过")


if __name__ == "__main__":
    main()
