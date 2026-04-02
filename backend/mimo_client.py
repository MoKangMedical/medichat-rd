"""
MediChat - 小米 MIMO 模型集成模块
OpenAI 兼容接口
"""

import os
from openai import OpenAI
from typing import List, Dict, Optional


class MIMOClient:
    """小米 MIMO 模型客户端"""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None
    ):
        self.api_key = api_key or os.getenv("MIMO_API_KEY")
        self.base_url = base_url or os.getenv(
            "MIMO_BASE_URL", 
            "https://api.xiaomimimo.com/v1"
        )
        self.model = model or os.getenv("MIMO_MODEL", "mimo-v2-pro")
        
        if not self.api_key:
            raise ValueError("MIMO_API_KEY 未配置")
        
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2048,
        stream: bool = False
    ) -> str:
        """
        发送聊天请求
        
        Args:
            messages: 对话消息列表
            temperature: 温度参数
            max_tokens: 最大token数
            stream: 是否流式输出
            
        Returns:
            模型回复内容
        """
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=stream
        )
        
        if stream:
            return self._handle_stream(response)
        return response.choices[0].message.content
    
    def _handle_stream(self, response) -> str:
        """处理流式响应"""
        full_content = ""
        for chunk in response:
            if chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                full_content += content
                print(content, end="", flush=True)
        return full_content
    
    def chat_with_system(
        self,
        system_prompt: str,
        user_message: str,
        **kwargs
    ) -> str:
        """带系统提示的聊天"""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
        return self.chat(messages, **kwargs)


# ============================================================
# 医疗场景专用提示词
# ============================================================
MEDICAL_SYSTEM_PROMPT = """你是一位专业的医疗AI助手，名叫MediChat。

你的职责：
1. 耐心倾听患者的症状描述
2. 进行专业的症状分析
3. 提供合理的就医建议
4. 解答患者的健康问题

重要原则：
- 你不能替代医生的诊断
- 对于紧急情况，必须建议患者立即就医
- 建议要具体、实用、可操作
- 语气要温和、专业、有同理心
- 使用中文回复

请始终在回复末尾加上：⚠️ 以上仅供参考，具体诊疗请咨询专业医生。"""

TRIAGE_SYSTEM_PROMPT = """你是MediChat的智能分诊员。

你的任务：
1. 分析患者的主诉
2. 评估紧急程度（急诊/普通门诊/健康咨询）
3. 推荐合适的科室
4. 给出初步建议

输出格式：
【紧急程度】急诊/门诊/咨询
【推荐科室】XXX科
【关键症状】列出主要症状
【初步建议】简要建议

请用中文回复。"""

ASSESSMENT_SYSTEM_PROMPT = """你是MediChat的症状分析专家。

你的任务：
1. 分析患者症状的特点
2. 列出可能的诊断方向（按可能性排序）
3. 建议进一步的检查项目
4. 提醒需要注意的事项

重要：你不是在做诊断，而是在提供参考性的分析。

请用中文回复，并在末尾提醒患者就医确认。"""


# ============================================================
# 使用示例
# ============================================================
if __name__ == "__main__":
    # 测试 MIMO 连接
    try:
        client = MIMOClient()
        response = client.chat_with_system(
            system_prompt=MEDICAL_SYSTEM_PROMPT,
            user_message="我最近总是头痛，伴有恶心，已经持续一周了"
        )
        print("\n\n=== MIMO 回复 ===")
        print(response)
    except Exception as e:
        print(f"错误: {e}")
        print("请配置 MIMO_API_KEY 后重试")
