"""
MediChat-RD × Second Me 集成模块
患者数字分身 + 罕见病社群
"""

import os
import json
import uuid
from typing import Optional, List, Dict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

# 本地模式开关：不连接外部API，全部用内存模拟
LOCAL_MODE = os.getenv("LOCAL_MODE", "true").lower() == "true"

# ============================================================
# 数据模型
# ============================================================

class CommunityType(str, Enum):
    """社群类型"""
    BY_DISEASE = "按疾病"
    BY_TOPIC = "按主题"
    BY_REGION = "按地域"


class PostType(str, Enum):
    """帖子类型"""
    EXPERIENCE = "经验分享"
    QUESTION = "求助提问"
    SUPPORT = "心理支持"
    INFO = "科普信息"


@dataclass
class PatientAvatar:
    """患者数字分身"""
    avatar_id: str
    patient_id: str
    nickname: str
    disease_type: str
    bio: str = ""
    memory_summary: str = ""
    personality: str = "温暖、共情、乐于助人"
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class PatientCommunity:
    """患者社群"""
    community_id: str
    name: str
    community_type: CommunityType
    description: str = ""
    disease_type: Optional[str] = None
    topic: Optional[str] = None
    region: Optional[str] = None
    member_count: int = 0
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class CommunityPost:
    """社群帖子"""
    post_id: str
    community_id: str
    author_avatar_id: str
    author_nickname: str
    content: str
    post_type: PostType
    likes: int = 0
    replies: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class BridgeConnection:
    """Bridge连接（AI分身间配对）"""
    connection_id: str
    avatar_a_id: str
    avatar_b_id: str
    match_reason: str
    match_score: float
    status: str = "active"
    created_at: datetime = field(default_factory=datetime.now)


# ============================================================
# Second Me 客户端（本地模式）
# ============================================================

class SecondMeClient:
    """
    Second Me API客户端
    LOCAL_MODE=true 时：纯内存模拟，不发HTTP
    LOCAL_MODE=false 时：连接外部Second Me服务
    """

    def __init__(self, base_url: str = "http://localhost:3000"):
        self.base_url = base_url
        self._local_avatars: Dict[str, PatientAvatar] = {}
        self._local_connections: Dict[str, BridgeConnection] = {}

        if not LOCAL_MODE:
            try:
                import httpx
                self._http = httpx.AsyncClient(base_url=base_url, timeout=30)
            except ImportError:
                print("⚠️ httpx 未安装，回退到本地模式")
                self._http = None
        else:
            self._http = None

    async def health_check(self) -> bool:
        """检查服务状态"""
        if LOCAL_MODE:
            return True  # 本地模式始终可用
        try:
            resp = await self._http.get("/api/health")
            return resp.status_code == 200
        except:
            return False

    async def create_avatar(self, patient_data: Dict) -> PatientAvatar:
        """为患者创建数字分身"""
        memory_text = self._build_memory(patient_data)

        if not LOCAL_MODE and self._http:
            try:
                payload = {
                    "name": patient_data.get("nickname", "匿名患者"),
                    "bio": f"一位{patient_data.get('disease_type', '罕见病')}患者，"
                           f"愿意分享经历，帮助同病伙伴。",
                    "personality": "温暖、共情、乐于助人、积极乐观",
                    "initial_memory": memory_text
                }
                resp = await self._http.post("/api/avatars", json=payload)
                if resp.status_code in [200, 201]:
                    data = resp.json()
                    avatar = PatientAvatar(
                        avatar_id=data.get("id", ""),
                        patient_id=patient_data["patient_id"],
                        nickname=patient_data.get("nickname", "匿名"),
                        disease_type=patient_data.get("disease_type", ""),
                        bio=payload["bio"],
                        memory_summary=memory_text[:200],
                        personality=payload["personality"]
                    )
                    self._local_avatars[avatar.avatar_id] = avatar
                    return avatar
            except Exception as e:
                print(f"⚠️ Second Me不可用，使用本地模式: {e}")

        # 本地模式 / 降级：纯内存创建
        avatar_id = f"avt_{uuid.uuid4().hex[:8]}"
        avatar = PatientAvatar(
            avatar_id=avatar_id,
            patient_id=patient_data["patient_id"],
            nickname=patient_data.get("nickname", "匿名"),
            disease_type=patient_data.get("disease_type", ""),
            bio=f"一位{patient_data.get('disease_type', '')}患者",
            memory_summary=memory_text[:200],
        )
        self._local_avatars[avatar_id] = avatar
        return avatar

    def _build_memory(self, patient_data: Dict) -> str:
        """构建分身的初始记忆文本"""
        parts = []
        if patient_data.get("disease_type"):
            parts.append(f"我是一位{patient_data['disease_type']}患者。")
        if patient_data.get("diagnosis"):
            parts.append(f"我的诊断结果是：{patient_data['diagnosis']}")
        if patient_data.get("symptoms"):
            parts.append(f"我的主要症状包括：{patient_data['symptoms']}")
        if patient_data.get("treatment_history"):
            parts.append(f"我的治疗经历：{patient_data['treatment_history']}")
        if patient_data.get("age"):
            parts.append(f"我今年{patient_data['age']}岁。")
        parts.append("我希望通过分享自己的经历，帮助更多同病相怜的朋友。")
        parts.append("我也希望能从其他患者那里获得支持和建议。")
        return "\n".join(parts)

    async def chat(self, avatar_id: str, message: str) -> str:
        """与分身对话"""
        avatar = self._local_avatars.get(avatar_id)

        if not LOCAL_MODE and self._http:
            try:
                resp = await self._http.post(
                    f"/api/avatars/{avatar_id}/chat",
                    json={"message": message}
                )
                if resp.status_code == 200:
                    return resp.json().get("reply", "")
            except:
                pass

        # 本地模拟回复
        if avatar:
            return (
                f"你好，我是{avatar.nickname}。"
                f"作为一位{avatar.disease_type}患者，我理解你的感受。"
                f"如果你想了解我的治疗经历，我很乐意和你聊聊。💕"
            )
        return "（分身暂时无法回复，请稍后再试）"

    async def bridge_connect(
        self,
        avatar_id: str,
        target_avatar_id: str,
        context: str = ""
    ) -> Optional[BridgeConnection]:
        """Bridge模式连接两个分身"""

        if not LOCAL_MODE and self._http:
            try:
                resp = await self._http.post("/api/bridge", json={
                    "source_avatar": avatar_id,
                    "target_avatar": target_avatar_id,
                    "context": context
                })
                if resp.status_code in [200, 201]:
                    data = resp.json()
                    conn = BridgeConnection(
                        connection_id=data.get("id", ""),
                        avatar_a_id=avatar_id,
                        avatar_b_id=target_avatar_id,
                        match_reason=context,
                        match_score=data.get("score", 0.8)
                    )
                    self._local_connections[conn.connection_id] = conn
                    return conn
            except:
                pass

        # 本地模式：直接创建连接
        conn_id = f"brg_{uuid.uuid4().hex[:8]}"
        conn = BridgeConnection(
            connection_id=conn_id,
            avatar_a_id=avatar_id,
            avatar_b_id=target_avatar_id,
            match_reason=context or "同病相怜",
            match_score=0.85
        )
        self._local_connections[conn_id] = conn
        return conn

    def get_all_avatars(self) -> List[PatientAvatar]:
        """获取所有本地分身"""
        return list(self._local_avatars.values())

    def get_avatar(self, avatar_id: str) -> Optional[PatientAvatar]:
        """获取单个分身"""
        return self._local_avatars.get(avatar_id)


# ============================================================
# 社群管理器（纯内存，本地即可运行）
# ============================================================

class CommunityManager:
    """患者社群管理器"""

    DEFAULT_COMMUNITIES = [
        "戈谢病互助圈", "庞贝病互助圈", "法布雷病互助圈",
        "脊髓性肌萎缩症互助圈", "渐冻症互助圈", "亨廷顿病互助圈",
        "杜氏肌营养不良互助圈", "贝克型肌营养不良互助圈",
        "血友病A互助圈", "血友病B互助圈", "成骨不全症互助圈",
        "马凡综合征互助圈", "苯丙酮尿症互助圈",
        "用药经验分享", "康复训练交流", "心理支持",
        "医保政策讨论", "新药临床试验信息",
    ]

    def __init__(self):
        self.communities: Dict[str, PatientCommunity] = {}
        self.members: Dict[str, List[str]] = {}
        self.posts: Dict[str, List[CommunityPost]] = {}

        for name in self.DEFAULT_COMMUNITIES:
            cid = f"comm_{name.replace('互助圈','').replace('分享','').replace('交流','').replace('讨论','').replace('信息','')[:6]}"
            self.communities[cid] = PatientCommunity(
                community_id=cid,
                name=name,
                community_type=CommunityType.BY_DISEASE if "互助圈" in name else CommunityType.BY_TOPIC,
                disease_type=name.replace("互助圈", "") if "互助圈" in name else None,
                topic=name if "互助圈" not in name else None,
                description=f"{name} - 让我们互相支持，共同前行"
            )
            self.members[cid] = []
            self.posts[cid] = []

        # 预置一些示例帖子让社群看起来不空
        self._seed_posts()

    def _seed_posts(self):
        """预置示例帖子"""
        seed_data = [
            ("戈谢病互助圈", "小米妈妈", "孩子确诊两年了，一直在用酶替代治疗，目前情况稳定。有需要了解治疗流程的家长可以交流。", "经验分享"),
            ("庞贝病互助圈", "乐乐爸爸", "刚确诊庞贝病，很迷茫。有家长能分享一下国内哪几家医院比较专业吗？", "求助提问"),
            ("法布雷病互助圈", "匿名", "最近天气变化，疼痛发作频繁。大家有什么缓解疼痛的好方法吗？", "求助提问"),
            ("心理支持", "心理咨询师小王", "罕见病患者和家属的心理健康同样重要。如果你感到焦虑或抑郁，请不要独自承受。", "科普信息"),
            ("用药经验分享", "老张", "分享一下我用药三年的心得：按时服药、定期复查、保持心态平和。", "经验分享"),
            ("康复训练交流", "康复师李老师", "分享一套居家康复训练动作，适合大部分罕见病患者。每天15分钟，坚持就会有效果。", "科普信息"),
        ]
        for comm_name, author, content, post_type_str in seed_data:
            # 找到对应的社群
            for cid, comm in self.communities.items():
                if comm.name == comm_name:
                    post_type = PostType(post_type_str)
                    post = CommunityPost(
                        post_id=f"post_seed_{uuid.uuid4().hex[:6]}",
                        community_id=cid,
                        author_avatar_id=f"seed_{author}",
                        author_nickname=author,
                        content=content,
                        post_type=post_type,
                        likes=5 + hash(author) % 20,
                    )
                    self.posts[cid].append(post)
                    break

    def auto_join(self, avatar: PatientAvatar) -> List[str]:
        """根据患者疾病自动加入相关社群"""
        joined = []
        for cid, comm in self.communities.items():
            if comm.disease_type and avatar.disease_type in comm.name:
                if avatar.avatar_id not in self.members[cid]:
                    self.members[cid].append(avatar.avatar_id)
                    self.communities[cid].member_count += 1
                    joined.append(comm.name)
            elif comm.community_type == CommunityType.BY_TOPIC:
                if avatar.avatar_id not in self.members[cid]:
                    self.members[cid].append(avatar.avatar_id)
                    self.communities[cid].member_count += 1
        return joined

    def get_recommended_communities(self, disease_type: str) -> List[PatientCommunity]:
        """获取推荐社群"""
        return [
            c for c in self.communities.values()
            if (c.disease_type and disease_type in c.name) or c.community_type == CommunityType.BY_TOPIC
        ]

    def create_post(
        self,
        community_id: str,
        avatar_id: str,
        nickname: str,
        content: str,
        post_type: PostType = PostType.EXPERIENCE
    ) -> CommunityPost:
        """发帖"""
        post = CommunityPost(
            post_id=f"post_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:4]}",
            community_id=community_id,
            author_avatar_id=avatar_id,
            author_nickname=nickname,
            content=content,
            post_type=post_type
        )
        if community_id not in self.posts:
            self.posts[community_id] = []
        self.posts[community_id].insert(0, post)
        return post

    def find_matches(self, avatar: PatientAvatar, n: int = 5) -> List[Dict]:
        """查找匹配的病友"""
        matches = []
        for cid, comm in self.communities.items():
            if comm.disease_type and avatar.disease_type in comm.name:
                for member_id in self.members.get(cid, []):
                    if member_id != avatar.avatar_id:
                        matches.append({
                            "avatar_id": member_id,
                            "community": comm.name,
                            "match_reason": f"同为{avatar.disease_type}患者",
                            "match_score": 0.9
                        })
        return matches[:n]

    def get_posts(self, community_id: str, page: int = 1, page_size: int = 20) -> List[CommunityPost]:
        """获取社群帖子列表"""
        all_posts = self.posts.get(community_id, [])
        start = (page - 1) * page_size
        return all_posts[start:start + page_size]


if __name__ == "__main__":
    print("=" * 50)
    print("🧬 MediChat-RD 社群系统（本地模式）")
    print(f"📡 LOCAL_MODE = {LOCAL_MODE}")
    print("=" * 50)

    mgr = CommunityManager()
    print(f"\n📦 已初始化 {len(mgr.communities)} 个社群")

    patient = PatientAvatar(
        avatar_id=str(uuid.uuid4())[:8],
        patient_id="patient_001",
        nickname="小明妈妈",
        disease_type="戈谢病",
        memory_summary="5岁男孩，脾脏肿大、骨痛、血小板减少"
    )
    print(f"\n👤 新患者: {patient.nickname} ({patient.disease_type})")

    joined = mgr.auto_join(patient)
    print(f"✅ 自动加入 {len(joined)} 个社群: {', '.join(joined[:3])}...")

    recs = mgr.get_recommended_communities("戈谢病")
    print(f"\n📋 推荐社群: {len(recs)} 个")

    post = mgr.create_post(
        community_id=list(mgr.communities.keys())[0],
        avatar_id=patient.avatar_id,
        nickname=patient.nickname,
        content="孩子刚确诊戈谢病，很担心。有没有经验丰富的家长可以分享一下治疗经历？",
        post_type=PostType.QUESTION
    )
    print(f"\n📝 已发帖: {post.content[:30]}...")

    matches = mgr.find_matches(patient)
    print(f"\n🤝 推荐Bridge连接: {len(matches)} 位病友")

    print("\n✅ 演示完成！")
