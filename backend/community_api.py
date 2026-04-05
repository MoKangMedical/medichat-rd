"""
MediChat-RD — 罕见病社群API
Second Me集成 + 社群管理
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'agents'))

router = APIRouter(prefix="/api/v1/community", tags=["罕见病社群"])

# ========== 数据模型 ==========
class CreateAvatarInput(BaseModel):
    nickname: str = Field(..., description="昵称")
    disease_type: str = Field(..., description="疾病类型")
    age: Optional[int] = Field(None, description="年龄")
    symptoms: Optional[str] = Field(None, description="主要症状")
    diagnosis: Optional[str] = Field(None, description="诊断结果")
    treatment_history: Optional[str] = Field(None, description="治疗经历")

class CreatePostInput(BaseModel):
    community_id: str = Field(..., description="社群ID")
    avatar_id: str = Field(..., description="分身ID")
    nickname: str = Field(..., description="昵称")
    content: str = Field(..., description="内容")
    post_type: str = Field("经验分享", description="帖子类型")

class ChatInput(BaseModel):
    avatar_id: str = Field(..., description="分身ID")
    message: str = Field(..., description="消息内容")

class BridgeInput(BaseModel):
    avatar_id: str = Field(..., description="自己的分身ID")
    target_avatar_id: str = Field(..., description="目标分身ID")
    context: Optional[str] = Field("", description="连接原因")


# ========== 全局实例 ==========
# 延迟导入以避免循环依赖
_community_mgr = None
_second_me_client = None

def get_community_manager():
    global _community_mgr
    if _community_mgr is None:
        from secondme_integration import CommunityManager
        _community_mgr = CommunityManager()
    return _community_mgr

def get_second_me_client():
    global _second_me_client
    if _second_me_client is None:
        from secondme_integration import SecondMeClient
        _second_me_client = SecondMeClient()
    return _second_me_client


# ========== 社群API ==========
@router.get("/list")
async def list_communities(disease_type: Optional[str] = None):
    """获取社群列表"""
    mgr = get_community_manager()
    communities = []
    for cid, comm in mgr.communities.items():
        if disease_type and comm.disease_type and disease_type not in comm.name:
            continue
        communities.append({
            "id": comm.community_id,
            "name": comm.name,
            "type": comm.community_type.value if hasattr(comm.community_type, 'value') else str(comm.community_type),
            "description": comm.description,
            "disease_type": comm.disease_type,
            "member_count": comm.member_count,
            "post_count": len(mgr.posts.get(cid, [])),
        })
    return {"ok": True, "communities": communities}


@router.get("/{community_id}/posts")
async def get_posts(community_id: str, page: int = 1, page_size: int = 20):
    """获取社群帖子"""
    mgr = get_community_manager()
    posts = mgr.get_posts(community_id, page, page_size)
    return {
        "ok": True,
        "posts": [
            {
                "id": p.post_id,
                "author": p.author_nickname,
                "content": p.content,
                "type": p.post_type.value if hasattr(p.post_type, 'value') else str(p.post_type),
                "likes": p.likes,
                "created_at": p.created_at.strftime("%Y-%m-%d %H:%M"),
            }
            for p in posts
        ],
    }


@router.post("/post")
async def create_post(input_data: CreatePostInput):
    """发帖"""
    mgr = get_community_manager()
    from secondme_integration import PostType
    post_type = PostType(input_data.post_type) if input_data.post_type in [t.value for t in PostType] else PostType.EXPERIENCE
    post = mgr.create_post(
        community_id=input_data.community_id,
        avatar_id=input_data.avatar_id,
        nickname=input_data.nickname,
        content=input_data.content,
        post_type=post_type,
    )
    return {
        "ok": True,
        "post_id": post.post_id,
        "message": "发帖成功！",
    }


# ========== 数字分身API ==========
@router.post("/avatar/create")
async def create_avatar(input_data: CreateAvatarInput):
    """创建数字分身"""
    client = get_second_me_client()
    patient_data = {
        "patient_id": f"p_{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "nickname": input_data.nickname,
        "disease_type": input_data.disease_type,
        "age": input_data.age,
        "symptoms": input_data.symptoms,
        "diagnosis": input_data.diagnosis,
        "treatment_history": input_data.treatment_history,
    }
    avatar = await client.create_avatar(patient_data)
    
    # 自动加入相关社群
    mgr = get_community_manager()
    joined = mgr.auto_join(avatar)
    
    return {
        "ok": True,
        "avatar": {
            "id": avatar.avatar_id,
            "nickname": avatar.nickname,
            "disease_type": avatar.disease_type,
            "bio": avatar.bio,
        },
        "joined_communities": joined,
    }


@router.post("/avatar/chat")
async def chat_with_avatar(input_data: ChatInput):
    """与数字分身对话"""
    client = get_second_me_client()
    reply = await client.chat(input_data.avatar_id, input_data.message)
    return {"ok": True, "reply": reply}


@router.get("/avatars")
async def list_avatars():
    """获取所有数字分身"""
    client = get_second_me_client()
    avatars = client.get_all_avatars()
    return {
        "ok": True,
        "avatars": [
            {
                "id": a.avatar_id,
                "nickname": a.nickname,
                "disease_type": a.disease_type,
                "bio": a.bio,
            }
            for a in avatars
        ],
    }


# ========== Bridge连接API ==========
@router.post("/bridge")
async def bridge_connect(input_data: BridgeInput):
    """Bridge模式连接病友"""
    client = get_second_me_client()
    conn = await client.bridge_connect(
        input_data.avatar_id,
        input_data.target_avatar_id,
        input_data.context,
    )
    if conn:
        return {
            "ok": True,
            "connection": {
                "id": conn.connection_id,
                "match_reason": conn.match_reason,
                "match_score": conn.match_score,
            },
        }
    return {"ok": False, "message": "连接失败"}


@router.get("/recommend/{disease_type}")
async def recommend_communities(disease_type: str):
    """推荐相关社群"""
    mgr = get_community_manager()
    recs = mgr.get_recommended_communities(disease_type)
    return {
        "ok": True,
        "recommendations": [
            {
                "id": c.community_id,
                "name": c.name,
                "description": c.description,
                "member_count": c.member_count,
            }
            for c in recs
        ],
    }
