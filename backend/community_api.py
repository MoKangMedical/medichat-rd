"""
MediChat-RD 社群API
患者数字分身 + 社群互动 + Bridge连接
"""

import sys, os

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from uuid import uuid4

from secondme_integration import (
    SecondMeClient, CommunityManager, CommunityType, PostType,
    PatientAvatar, CommunityPost, LOCAL_MODE
)

router = APIRouter(prefix="/api/v1/community", tags=["患者社群"])

# 全局实例
secondme = SecondMeClient()
community_mgr = CommunityManager()

# 内存存储
avatars: dict = {}      # patient_id -> PatientAvatar


# ============================================================
# 数据模型
# ============================================================

class CreateAvatarRequest(BaseModel):
    patient_id: str
    nickname: str
    disease_type: str
    diagnosis: Optional[str] = None
    symptoms: Optional[str] = None
    treatment_history: Optional[str] = None
    age: Optional[int] = None


class CreatePostRequest(BaseModel):
    community_id: str
    avatar_id: str
    nickname: str
    content: str
    post_type: str = "经验分享"


class BridgeRequest(BaseModel):
    avatar_id: str
    target_avatar_id: str
    context: str = ""


# ============================================================
# API端点
# ============================================================

@router.get("/status")
async def community_status():
    """社群系统状态"""
    sm_online = await secondme.health_check()
    return {
        "status": "online",
        "mode": "local" if LOCAL_MODE else "remote",
        "secondme_connected": sm_online,
        "total_communities": len(community_mgr.communities),
        "total_avatars": len(avatars),
        "communities": [
            {
                "id": c.community_id,
                "name": c.name,
                "type": c.community_type.value,
                "members": c.member_count
            }
            for c in sorted(community_mgr.communities.values(), key=lambda x: -x.member_count)[:10]
        ]
    }


@router.post("/avatar")
async def create_avatar(req: CreateAvatarRequest):
    """创建患者数字分身"""
    avatar = await secondme.create_avatar({
        "patient_id": req.patient_id,
        "nickname": req.nickname,
        "disease_type": req.disease_type,
        "diagnosis": req.diagnosis or "",
        "symptoms": req.symptoms or "",
        "treatment_history": req.treatment_history or "",
        "age": req.age
    })
    
    if not avatar:
        raise HTTPException(status_code=500, detail="创建分身失败")
    
    # 存储
    avatars[req.patient_id] = avatar
    
    # 自动加入社群
    joined = community_mgr.auto_join(avatar)
    
    # 获取推荐病友
    matches = community_mgr.find_matches(avatar)
    
    return {
        "avatar": {
            "id": avatar.avatar_id,
            "nickname": avatar.nickname,
            "disease_type": avatar.disease_type,
            "bio": avatar.bio
        },
        "joined_communities": joined,
        "recommended_matches": matches,
        "message": f"数字分身已创建，自动加入{len(joined)}个社群"
    }


@router.get("/avatar/{patient_id}")
async def get_avatar(patient_id: str):
    """获取患者数字分身信息"""
    if patient_id not in avatars:
        raise HTTPException(status_code=404, detail="未找到分身")
    
    avatar = avatars[patient_id]
    return {
        "id": avatar.avatar_id,
        "nickname": avatar.nickname,
        "disease_type": avatar.disease_type,
        "bio": avatar.bio,
        "created_at": avatar.created_at.isoformat()
    }


@router.get("/avatar/{patient_id}/communities")
async def get_my_communities(patient_id: str):
    """获取分身所在社群列表"""
    if patient_id not in avatars:
        raise HTTPException(status_code=404, detail="未找到分身")
    
    avatar = avatars[patient_id]
    my_communities = []
    for cid, members in community_mgr.members.items():
        if avatar.avatar_id in members:
            comm = community_mgr.communities[cid]
            my_communities.append({
                "id": comm.community_id,
                "name": comm.name,
                "members": comm.member_count
            })
    
    return {"communities": my_communities}


@router.get("/communities")
async def list_communities(disease_type: Optional[str] = None):
    """列出社群"""
    communities = list(community_mgr.communities.values())
    
    if disease_type:
        communities = [c for c in communities if (c.disease_type and disease_type in c.name) or c.community_type == CommunityType.BY_TOPIC]
    
    return {
        "total": len(communities),
        "communities": [
            {
                "id": c.community_id,
                "name": c.name,
                "type": c.community_type.value,
                "description": c.description,
                "members": c.member_count
            }
            for c in sorted(communities, key=lambda x: -x.member_count)
        ]
    }


@router.get("/communities/{community_id}/posts")
async def get_posts(community_id: str, limit: int = 20):
    """获取社群帖子"""
    posts = community_mgr.posts.get(community_id, [])
    return {
        "community_id": community_id,
        "total": len(posts),
        "posts": [
            {
                "id": p.post_id,
                "author": p.author_nickname,
                "content": p.content,
                "type": p.post_type.value,
                "likes": p.likes,
                "replies": len(p.replies),
                "created_at": p.created_at.isoformat()
            }
            for p in posts[:limit]
        ]
    }


@router.post("/posts")
async def create_post(req: CreatePostRequest):
    """发帖"""
    try:
        post_type = PostType(req.post_type)
    except ValueError:
        post_type = PostType.EXPERIENCE
    
    post = community_mgr.create_post(
        community_id=req.community_id,
        avatar_id=req.avatar_id,
        nickname=req.nickname,
        content=req.content,
        post_type=post_type
    )
    
    return {
        "post_id": post.post_id,
        "message": "发帖成功",
        "content": post.content[:50] + "..."
    }


@router.get("/avatar/{patient_id}/matches")
async def find_matches(patient_id: str, n: int = 5):
    """查找匹配病友（Bridge推荐）"""
    if patient_id not in avatars:
        raise HTTPException(status_code=404, detail="未找到分身")
    
    avatar = avatars[patient_id]
    matches = community_mgr.find_matches(avatar, n=n)
    
    return {
        "patient": avatar.nickname,
        "disease_type": avatar.disease_type,
        "matches": matches,
        "message": f"找到{len(matches)}位可能的病友"
    }


@router.post("/bridge")
async def bridge_connect(req: BridgeRequest):
    """Bridge模式连接两个分身"""
    conn = await secondme.bridge_connect(
        req.avatar_id,
        req.target_avatar_id,
        req.context
    )
    
    if conn:
        return {
            "connection_id": conn.connection_id,
            "match_score": conn.match_score,
            "status": conn.status,
            "message": "Bridge连接已建立"
        }
    
    return {
        "connection_id": f"local_{uuid4().hex[:8]}",
        "match_score": 0.8,
        "status": "pending",
        "message": "Bridge连接请求已发送（Second Me离线时使用本地模式）"
    }


@router.post("/avatar/{patient_id}/chat")
async def chat_with_avatar(patient_id: str, message: str):
    """与患者分身对话"""
    if patient_id not in avatars:
        raise HTTPException(status_code=404, detail="未找到分身")
    
    avatar = avatars[patient_id]
    reply = await secondme.chat(avatar.avatar_id, message)
    
    return {
        "avatar": avatar.nickname,
        "message": message,
        "reply": reply
    }
