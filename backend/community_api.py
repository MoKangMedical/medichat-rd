"""
MediChat-RD — 罕见病社群 API
Second Me 集成 + 社群管理 + 患者互动发现层
"""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime
import re
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'agents'))

from hpo_extractor import HPOExtractor
from patient_matcher import PatientMatcher, PatientProfile
from patient_registry import PatientRegistry
from secondme_oauth import SECONDME_SESSION_COOKIE_NAME, get_secondme_profile_for_session

router = APIRouter(prefix="/api/v1/community", tags=["罕见病社群"])

hpo_extractor = HPOExtractor()
patient_registry = PatientRegistry(os.path.join(os.path.dirname(__file__), '..', 'data', 'patient_registry.db'))

PROFILE_SIGNAL_KEYWORDS = {
    "家属照护": ["妈妈", "爸爸", "家属", "照护", "孩子", "育儿", "家庭"],
    "新确诊适应": ["新确诊", "刚确诊", "初诊", "第一周", "迷茫", "确诊后"],
    "治疗管理": ["治疗", "用药", "输注", "酶替代", "药", "副作用", "疗程"],
    "康复与长期管理": ["康复", "训练", "打卡", "长期", "耐量", "运动", "随访"],
    "心理支持": ["情绪", "焦虑", "害怕", "支持", "压力", "心理", "孤单"],
    "检查与就诊": ["检查", "复查", "医院", "门诊", "住院", "医生", "转诊"],
    "研究和新药关注": ["研究", "试验", "新药", "招募", "药物", "临床试验"],
}
GENERIC_PROFILE_TERMS = {
    "secondme", "用户", "患者", "病友", "罕见病", "支持", "帮助", "分享", "经历",
}

DEMO_MATCH_PROFILES = [
    PatientProfile("demo_mg_01", "重症肌无力", ["眼睑下垂", "吞咽困难", "肌无力"], 28, "女", "上海"),
    PatientProfile("demo_gd_01", "戈谢病", ["肝脾肿大", "贫血", "骨痛"], 12, "男", "北京"),
    PatientProfile("demo_fd_01", "法布雷病", ["肢端疼痛", "血管角化瘤", "肾功能不全"], 24, "男", "深圳"),
    PatientProfile("demo_sma_01", "脊髓性肌萎缩症", ["肌无力", "肌肉萎缩", "发育迟缓"], 8, "女", "成都"),
]

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


def _serialize_community(mgr, comm):
    return {
        "id": comm.community_id,
        "name": comm.name,
        "type": comm.community_type.value if hasattr(comm.community_type, 'value') else str(comm.community_type),
        "description": comm.description,
        "disease_type": comm.disease_type,
        "member_count": comm.member_count,
        "post_count": len(mgr.posts.get(comm.community_id, [])),
    }


def _serialize_post(post, community_name: Optional[str] = None):
    payload = {
        "id": post.post_id,
        "community_id": post.community_id,
        "author": post.author_nickname,
        "content": post.content,
        "type": post.post_type.value if hasattr(post.post_type, 'value') else str(post.post_type),
        "likes": post.likes,
        "created_at": post.created_at.strftime("%Y-%m-%d %H:%M"),
    }
    if community_name:
        payload["community_name"] = community_name
    return payload


def _extract_phenotypes(text: str) -> List[str]:
    if not text.strip():
        return []
    result = hpo_extractor.analyze_symptoms(text)
    seen = set()
    phenotypes = []
    for item in result.get("extracted_phenotypes", []):
        label = item.get("matched_text") or item.get("name")
        if label and label not in seen:
            seen.add(label)
            phenotypes.append(label)
    return phenotypes


def _build_patient_matcher(client) -> PatientMatcher:
    matcher = PatientMatcher()
    seen_ids = set()

    for profile in DEMO_MATCH_PROFILES:
        matcher.add_patient(profile)
        seen_ids.add(profile.patient_id)

    for row in patient_registry.search_patients(limit=200):
        patient_id = row.get("registry_id")
        if not patient_id or patient_id in seen_ids:
            continue
        matcher.add_patient(
            PatientProfile(
                patient_id=patient_id,
                disease=row.get("disease", ""),
                hpo_phenotypes=row.get("hpo_phenotypes", []),
                age=row.get("age_of_onset") or 0,
                gender=row.get("gender", "") or "",
                location=row.get("ethnicity", "") or "登记库",
            )
        )
        seen_ids.add(patient_id)

    for avatar in client.get_all_avatars():
        if avatar.avatar_id in seen_ids:
            continue
        matcher.add_patient(
            PatientProfile(
                patient_id=avatar.avatar_id,
                disease=avatar.disease_type,
                hpo_phenotypes=_extract_phenotypes(f"{avatar.memory_summary} {avatar.bio}"),
                age=0,
                gender="",
                location=f"{avatar.provider_key} runtime",
            )
        )
        seen_ids.add(avatar.avatar_id)

    return matcher


def _count_shared_terms(left: List[str], right: List[str]) -> int:
    count = 0
    for l_item in left:
        for r_item in right:
            if l_item == r_item or l_item in r_item or r_item in l_item:
                count += 1
                break
    return count


def _get_logged_in_secondme_profile(request: Request) -> Dict:
    session_id = request.cookies.get(SECONDME_SESSION_COOKIE_NAME)
    try:
        return get_secondme_profile_for_session(session_id) or {}
    except Exception:
        return {}


def _split_profile_phrases(text: str) -> List[str]:
    if not text:
        return []
    phrases = []
    for item in re.split(r"[\s,，。；、/|]+", text):
        phrase = item.strip()
        if len(phrase) < 2:
            continue
        lowered = phrase.lower()
        if lowered in GENERIC_PROFILE_TERMS:
            continue
        phrases.append(phrase)
    return phrases


def _extract_profile_signals(*texts: str) -> List[str]:
    haystack = " ".join([text for text in texts if text]).lower()
    if not haystack:
        return []
    signals = []
    for label, keywords in PROFILE_SIGNAL_KEYWORDS.items():
        if any(keyword.lower() in haystack for keyword in keywords):
            signals.append(label)
    return signals


def _find_tag_overlaps(profile: Dict, *candidate_texts: str) -> List[str]:
    tags = [str(tag).strip() for tag in profile.get("tags", []) if str(tag).strip()]
    if not tags:
        return []
    haystack = " ".join(candidate_texts).lower()
    overlaps = []
    for tag in tags:
        lowered = tag.lower()
        if len(lowered) < 2:
            continue
        if lowered in haystack:
            overlaps.append(tag)
    return overlaps[:3]


def _build_connection_points(
    *,
    avatar,
    phenotypes: List[str],
    candidate_avatar,
    candidate_disease: str,
    candidate_phenotypes: List[str],
    oauth_profile: Dict,
    shared_count: int,
) -> List[str]:
    points = []

    if candidate_disease and candidate_disease == avatar.disease_type:
        points.append(f"同病种 · {candidate_disease}")
    if shared_count:
        points.append(f"共同表型 · {shared_count} 个")

    candidate_texts = [
        getattr(candidate_avatar, "nickname", ""),
        getattr(candidate_avatar, "bio", ""),
        getattr(candidate_avatar, "memory_summary", ""),
        candidate_disease,
        " ".join(candidate_phenotypes or []),
    ]
    tag_hits = _find_tag_overlaps(oauth_profile, *candidate_texts)
    if tag_hits:
        points.append(f"SecondMe 共同关注 · {'、'.join(tag_hits[:2])}")

    user_signals = _extract_profile_signals(
        oauth_profile.get("bio", ""),
        " ".join([str(tag) for tag in oauth_profile.get("tags", [])]),
        avatar.nickname,
        avatar.bio,
        avatar.memory_summary,
        " ".join(phenotypes),
    )
    candidate_signals = _extract_profile_signals(*candidate_texts)
    shared_signals = [signal for signal in user_signals if signal in candidate_signals]
    if shared_signals:
        points.append(f"当前阶段相近 · {'、'.join(shared_signals[:2])}")

    if not shared_signals and not tag_hits:
        bio_phrases = _split_profile_phrases(oauth_profile.get("bio", ""))[:4]
        candidate_bio = " ".join(candidate_texts)
        bio_hits = [phrase for phrase in bio_phrases if phrase.lower() in candidate_bio.lower()]
        if bio_hits:
            points.append(f"表达方式接近 · {'、'.join(bio_hits[:2])}")

    if not points:
        points.append("病程与互助语境相近")

    return points[:4]


def _compose_match_reason(connection_points: List[str]) -> str:
    if not connection_points:
        return "同一类患者语境，适合先建立连接"
    return "；".join(connection_points[:3])


# ========== 社群API ==========
@router.get("/list")
async def list_communities(disease_type: Optional[str] = None):
    """获取社群列表"""
    mgr = get_community_manager()
    communities = []
    for cid, comm in mgr.communities.items():
        if disease_type and comm.disease_type and disease_type not in comm.name:
            continue
        communities.append(_serialize_community(mgr, comm))
    return {"ok": True, "communities": communities}


@router.get("/discovery")
async def discovery_feed():
    """为患者首页提供社群发现层，聚合同病圈、热门帖子和互动房间。"""
    mgr = get_community_manager()

    communities = sorted(
        mgr.communities.values(),
        key=lambda comm: (len(mgr.posts.get(comm.community_id, [])) * 5) + comm.member_count,
        reverse=True,
    )
    featured_communities = [_serialize_community(mgr, comm) for comm in communities[:6]]

    all_posts = []
    for community_id, posts in mgr.posts.items():
        community_name = mgr.communities.get(community_id).name if community_id in mgr.communities else ""
        all_posts.extend(
            _serialize_post(post, community_name=community_name)
            for post in posts
        )
    trending_posts = sorted(
        all_posts,
        key=lambda post: (post["likes"], post["created_at"]),
        reverse=True,
    )[:6]

    live_rooms = [
        {
            "id": "room_newcomer",
            "title": "新确诊患者欢迎房",
            "host": "SecondMe Navigator",
            "schedule": "今晚 20:00",
            "focus": "确诊后第一周怎么整理病历、检查和情绪",
        },
        {
            "id": "room_parents",
            "title": "家长互助圆桌",
            "host": "罕见病家属志愿者",
            "schedule": "周三 19:30",
            "focus": "长期治疗依从性、营养和学校沟通",
        },
        {
            "id": "room_trials",
            "title": "临床试验机会追踪",
            "host": "研究助理 AI",
            "schedule": "每周五更新",
            "focus": "新药动态、筛选标准和受试者准备事项",
        },
    ]

    return {
        "ok": True,
        "featured_communities": featured_communities,
        "trending_posts": trending_posts,
        "live_rooms": live_rooms,
        "engagement_prompts": [
            "分享一次确诊过程，让后来者少走弯路",
            "记录一条对自己最有帮助的日常管理经验",
            "用 SecondMe 分身介绍你的治疗阶段和当前需求",
        ],
    }


@router.get("/{community_id}/posts")
async def get_posts(community_id: str, page: int = 1, page_size: int = 20):
    """获取社群帖子"""
    mgr = get_community_manager()
    posts = mgr.get_posts(community_id, page, page_size)
    return {
        "ok": True,
        "posts": [
            _serialize_post(p)
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
            "provider": avatar.provider_key,
            "provider_avatar_id": avatar.provider_avatar_id,
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
                "provider": a.provider_key,
                "provider_avatar_id": a.provider_avatar_id,
            }
            for a in avatars
        ],
    }


@router.get("/avatar/{avatar_id}/matches")
async def list_avatar_matches(avatar_id: str, request: Request):
    """给当前患者分身推荐病友匹配。"""
    mgr = get_community_manager()
    client = get_second_me_client()
    avatar = client.get_avatar(avatar_id)
    if not avatar:
        raise HTTPException(status_code=404, detail="未找到分身")

    phenotypes = _extract_phenotypes(f"{avatar.memory_summary} {avatar.bio}")
    matcher = _build_patient_matcher(client)
    oauth_profile = _get_logged_in_secondme_profile(request)
    target_profile = PatientProfile(
        patient_id=avatar.avatar_id,
        disease=avatar.disease_type,
        hpo_phenotypes=phenotypes,
        age=0,
        gender="",
        location="",
    )

    matches = []
    for item in matcher.find_matches(target_profile, top_n=5, min_similarity=0.25):
        target_avatar = client.get_avatar(item["patient_id"])
        recommended = mgr.get_recommended_communities(item["disease"])
        shared = _count_shared_terms(item["phenotypes"], phenotypes)
        connection_points = _build_connection_points(
            avatar=avatar,
            phenotypes=phenotypes,
            candidate_avatar=target_avatar,
            candidate_disease=item["disease"],
            candidate_phenotypes=item["phenotypes"],
            oauth_profile=oauth_profile,
            shared_count=shared,
        )
        matches.append(
            {
                "avatar_id": item["patient_id"],
                "nickname": getattr(target_avatar, "nickname", "同路病友"),
                "disease_type": getattr(target_avatar, "disease_type", item["disease"]),
                "bio": getattr(target_avatar, "bio", f"与你共享 {shared or 1} 个关键表型线索"),
                "community": recommended[0].name if recommended else "罕见病互助圈",
                "connection_points": connection_points,
                "match_reason": _compose_match_reason(connection_points),
                "match_score": item["similarity"],
            }
        )

    if not matches:
        for item in mgr.find_matches(avatar):
            target_avatar = client.get_avatar(item["avatar_id"])
            connection_points = _build_connection_points(
                avatar=avatar,
                phenotypes=phenotypes,
                candidate_avatar=target_avatar,
                candidate_disease=getattr(target_avatar, "disease_type", avatar.disease_type),
                candidate_phenotypes=_extract_phenotypes(
                    f"{getattr(target_avatar, 'memory_summary', '')} {getattr(target_avatar, 'bio', '')}"
                ),
                oauth_profile=oauth_profile,
                shared_count=0,
            )
            matches.append(
                {
                    "avatar_id": item["avatar_id"],
                    "nickname": getattr(target_avatar, "nickname", "病友"),
                    "disease_type": getattr(target_avatar, "disease_type", avatar.disease_type),
                    "bio": getattr(target_avatar, "bio", "与你处于相似的病程与互助语境"),
                    "community": item["community"],
                    "connection_points": connection_points,
                    "match_reason": _compose_match_reason(connection_points),
                    "match_score": item["match_score"],
                }
            )

    if not matches:
        matches = [
            {
                "avatar_id": "companion_seed_parent",
                "nickname": f"{avatar.disease_type} 家属志愿者",
                "disease_type": avatar.disease_type,
                "bio": "擅长帮助新确诊家庭整理病历、就诊路径和情绪支持。",
                "community": f"{avatar.disease_type}互助圈",
                "connection_points": ["同病种 · 家属支持", "当前阶段相近 · 新确诊适应", "适合先建立安全连接"],
                "match_reason": "同病种 · 家属支持；当前阶段相近 · 新确诊适应；适合先建立安全连接",
                "match_score": 0.88,
            },
            {
                "avatar_id": "companion_seed_rehab",
                "nickname": "康复打卡伙伴",
                "disease_type": avatar.disease_type,
                "bio": "关注长期管理、运动耐量和生活质量。",
                "community": "康复训练交流",
                "connection_points": ["同病种 · 长期管理", "当前阶段相近 · 康复与长期管理", "适合互相提醒和打卡"],
                "match_reason": "同病种 · 长期管理；当前阶段相近 · 康复与长期管理；适合互相提醒和打卡",
                "match_score": 0.79,
            },
        ]

    return {"ok": True, "matches": matches}


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
