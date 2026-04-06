import React, { useEffect, useState } from 'react';
import RareDiseaseGlobe from './RareDiseaseGlobe';

const API_BASE = import.meta.env.VITE_API_URL || '';
const AVATAR_STORAGE_KEY = 'medichat_secondme_avatar';
const NOTE_SYNC_STORAGE_KEY = 'medichat_secondme_note_sync';
const FIRST_POST_MODES = [
  {
    key: '求助提问',
    title: '求助提问',
    subtitle: '把眼前最卡住的一个问题说清楚，最容易收到回应。',
    accent: '#FF7A59',
    background: 'rgba(255, 122, 89, 0.08)',
    prompt: [
      '把重点放在当前最想获得的帮助和一个最具体的问题。',
      '允许表达迷茫、焦虑或不确定，但不要堆太多问题。',
      '语气真诚克制，像患者本人第一次求助。',
    ],
  },
  {
    key: '经验分享',
    title: '经验分享',
    subtitle: '讲一段真实经历，帮后来者少走一点弯路。',
    accent: '#0DBF9B',
    background: 'rgba(13, 191, 155, 0.1)',
    prompt: [
      '重点写自己踩过的坑、后来怎么调整、什么最有帮助。',
      '不要写成科普稿，要保留患者亲历感。',
      '结尾留一个开放点，方便病友继续接话。',
    ],
  },
  {
    key: '心理支持',
    title: '心理支持',
    subtitle: '更适合表达情绪、找陪伴和建立同阶段连接。',
    accent: '#6D28D9',
    background: 'rgba(109, 40, 217, 0.08)',
    prompt: [
      '重点说当前情绪状态、最难熬的时刻，以及希望被怎样理解。',
      '避免过度鸡汤，允许脆弱，但语气要温和真实。',
      '让对方知道怎样的回应会真正帮到自己。',
    ],
  },
];

const LIVE_ROOM_STYLES = {
  room_newcomer: {
    accent: '#FF7A59',
    eyebrow: '欢迎引导',
    blurb: '适合刚拿到诊断结果、准备整理第一轮病历和情绪的患者。',
    actionLabel: '进入欢迎房入口',
    background: 'linear-gradient(180deg, rgba(255, 240, 235, 0.96) 0%, rgba(255, 248, 245, 0.92) 100%)',
  },
  room_parents: {
    accent: '#0DBF9B',
    eyebrow: '家长圆桌',
    blurb: '围绕长期治疗、日常营养和学校沟通，适合家属直接加入。',
    actionLabel: '查看家长支持入口',
    background: 'linear-gradient(180deg, rgba(234, 255, 248, 0.96) 0%, rgba(246, 255, 252, 0.92) 100%)',
  },
  room_trials: {
    accent: '#4C7DFF',
    eyebrow: '研究机会',
    blurb: '把试验动态、入排标准和受试准备拆成患者能理解的行动项。',
    actionLabel: '查看试验机会',
    background: 'linear-gradient(180deg, rgba(236, 242, 255, 0.96) 0%, rgba(248, 250, 255, 0.92) 100%)',
  },
};

const COMPANION_TOYS = [
  {
    id: 'bear',
    name: '小熊陪伴玩偶',
    tone: '#FFB066',
    animal: 'bear',
    purpose: '更适合刚确诊、需要安全感和睡前陪伴的孩子。',
    features: ['拥抱安抚', '睡前语音', '随访问候', '情绪记录'],
  },
  {
    id: 'rabbit',
    name: '小兔子安心玩偶',
    tone: '#FF8FB1',
    animal: 'rabbit',
    purpose: '更适合打针、复查和住院前后，帮助孩子降低紧张感。',
    features: ['检查前安抚', '就诊提醒', '亲子沟通', '勇气练习'],
  },
  {
    id: 'fox',
    name: '小狐狸勇气玩偶',
    tone: '#FF7A59',
    animal: 'fox',
    purpose: '更适合长期治疗阶段，陪孩子说出每天最真实的感受。',
    features: ['每日打卡', '用药提醒', '故事陪伴', '病友问候'],
  },
];

const FOLLOWUP_DEVICES = [
  {
    id: 'kids-voice',
    name: '儿童语音随访盒',
    tone: '#4C7DFF',
    summary: '像一个会说话的小伙伴，孩子按一下就能和 SecondMe 说今天哪里不舒服。',
    points: ['语音打卡', '家长代记', '症状变化提醒'],
  },
  {
    id: 'family-hub',
    name: '家庭陪伴随访屏',
    tone: '#0DBF9B',
    summary: '适合放在家里，串起家长、孩子和随访计划，减少漏记和漏问。',
    points: ['复诊清单', '营养记录', '学校沟通备忘'],
  },
  {
    id: 'adult-terminal',
    name: '成人病愈语音终端',
    tone: '#7A5AF8',
    summary: '更适合青年和成人患者，把复查、康复、情绪和研究机会放在一个入口。',
    points: ['语音随访', '康复提醒', '试验机会推送'],
  },
];

async function fetchJson(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, options);
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.detail || data.message || '请求失败');
  }
  return data;
}

function cardStyle(extra = {}) {
  return {
    background: 'rgba(255, 253, 249, 0.88)',
    border: '1px solid rgba(12, 24, 49, 0.08)',
    borderRadius: 24,
    boxShadow: '0 24px 80px rgba(17, 28, 56, 0.08)',
    backdropFilter: 'blur(12px)',
    ...extra,
  };
}

function softButtonStyle(kind = 'ghost', disabled = false) {
  if (kind === 'primary') {
    return {
      padding: '12px 18px',
      borderRadius: 999,
      border: 'none',
      background: disabled ? '#9CA3AF' : 'linear-gradient(135deg, #0C1831 0%, #173A68 100%)',
      color: '#fff',
      cursor: disabled ? 'not-allowed' : 'pointer',
      fontSize: 14,
      fontWeight: 700,
    };
  }
  return {
    padding: '11px 16px',
    borderRadius: 999,
    border: '1px solid rgba(12, 24, 49, 0.08)',
    background: 'rgba(255,255,255,0.82)',
    color: '#0C1831',
    cursor: disabled ? 'not-allowed' : 'pointer',
    fontSize: 14,
    fontWeight: 600,
    opacity: disabled ? 0.6 : 1,
  };
}

function toneStyle(kind = 'neutral') {
  if (kind === 'success') {
    return { background: '#ECFDF5', color: '#166534' };
  }
  if (kind === 'error') {
    return { background: '#FEF2F2', color: '#B91C1C' };
  }
  if (kind === 'warning') {
    return { background: '#FFF7ED', color: '#C2410C' };
  }
  return { background: '#F5F7FA', color: '#44506A' };
}

export default function CommunityPanel({ onNavigate }) {
  const [communities, setCommunities] = useState([]);
  const [selectedComm, setSelectedComm] = useState(null);
  const [posts, setPosts] = useState([]);
  const [dashboard, setDashboard] = useState(null);
  const [loadingPosts, setLoadingPosts] = useState(false);
  const [showCreateAvatar, setShowCreateAvatar] = useState(false);
  const [showCreatePost, setShowCreatePost] = useState(false);
  const [myAvatar, setMyAvatar] = useState(null);
  const [matchSuggestions, setMatchSuggestions] = useState([]);
  const [bridgeLoadingId, setBridgeLoadingId] = useState('');
  const [secondMeStatus, setSecondMeStatus] = useState(null);
  const [secondMeMessage, setSecondMeMessage] = useState('');
  const [secondMeTone, setSecondMeTone] = useState('neutral');
  const [syncingSummary, setSyncingSummary] = useState(false);
  const [draftingIntro, setDraftingIntro] = useState(false);
  const [draftingFirstPostMode, setDraftingFirstPostMode] = useState('');
  const [avatarIntro, setAvatarIntro] = useState('');
  const [firstPostDraft, setFirstPostDraft] = useState('');
  const [firstPostType, setFirstPostType] = useState('求助提问');
  const [summarySyncMeta, setSummarySyncMeta] = useState(null);
  const [diseaseStory, setDiseaseStory] = useState(null);
  const [diseaseStoryLoading, setDiseaseStoryLoading] = useState(false);
  const [recommendedCircles, setRecommendedCircles] = useState([]);

  useEffect(() => {
    readOAuthResult();
    restoreAvatar();
    loadCommunities();
    loadDashboard();
    loadSecondMeStatus();
  }, []);

  useEffect(() => {
    if (myAvatar?.id) {
      loadMatchSuggestions(myAvatar.id);
    }
  }, [myAvatar?.id]);

  useEffect(() => {
    if (!myAvatar?.id) {
      setSummarySyncMeta(null);
      return;
    }
    try {
      const raw = window.localStorage.getItem(`${NOTE_SYNC_STORAGE_KEY}:${myAvatar.id}`);
      if (!raw) {
        setSummarySyncMeta(null);
        return;
      }
      setSummarySyncMeta(JSON.parse(raw));
    } catch (error) {
      console.error(error);
      setSummarySyncMeta(null);
    }
  }, [myAvatar?.id]);

  useEffect(() => {
    const diseaseType = myAvatar?.disease_type || selectedComm?.disease_type || '';
    if (!diseaseType) {
      setDiseaseStory(null);
      setRecommendedCircles([]);
      return;
    }
    loadDiseaseStory(diseaseType);
  }, [myAvatar?.disease_type, selectedComm?.disease_type]);

  const restoreAvatar = () => {
    try {
      const raw = window.localStorage.getItem(AVATAR_STORAGE_KEY);
      if (!raw) return;
      const saved = JSON.parse(raw);
      if (saved?.id) setMyAvatar(saved);
    } catch (error) {
      console.error(error);
    }
  };

  const persistAvatar = (avatar) => {
    setMyAvatar(avatar);
    window.localStorage.setItem(AVATAR_STORAGE_KEY, JSON.stringify(avatar));
  };

  const persistSummarySyncMeta = (avatarId, meta) => {
    setSummarySyncMeta(meta);
    window.localStorage.setItem(`${NOTE_SYNC_STORAGE_KEY}:${avatarId}`, JSON.stringify(meta));
  };

  const setStatusMessage = (message, tone = 'neutral') => {
    setSecondMeMessage(message);
    setSecondMeTone(tone);
  };

  const readOAuthResult = () => {
    const url = new URL(window.location.href);
    const status = url.searchParams.get('secondme');
    const reason = url.searchParams.get('reason');
    if (!status) return;

    if (status === 'connected') {
      setStatusMessage('SecondMe 已完成授权，现在可以同步患者摘要并连接病友。', 'success');
      loadSecondMeStatus();
    } else if (status === 'error') {
      setStatusMessage(`SecondMe 授权失败：${reason || '未知错误'}`, 'error');
    }

    url.searchParams.delete('secondme');
    url.searchParams.delete('reason');
    window.history.replaceState({}, '', `${url.pathname}${url.search}${url.hash}`);
  };

  const loadCommunities = async () => {
    try {
      const data = await fetchJson('/api/v1/community/list');
      if (data.ok) {
        setCommunities(data.communities);
        return data.communities;
      }
    } catch (error) {
      console.error(error);
    }
    return [];
  };

  const loadDashboard = async () => {
    try {
      const data = await fetchJson('/api/v1/community/discovery');
      if (data.ok) {
        setDashboard(data);
        return data;
      }
    } catch (error) {
      console.error(error);
    }
    return null;
  };

  const loadSecondMeStatus = async () => {
    try {
      const data = await fetchJson('/api/v1/secondme/oauth/status');
      if (!data.ok) return;
      setSecondMeStatus(data.status);
      if (data.status.state === 'expired') {
        setStatusMessage(data.status.error || 'SecondMe 授权已失效，请重新连接。', 'warning');
      } else if (data.status.state === 'misconfigured') {
        setStatusMessage(data.status.error || 'SecondMe OAuth 服务端尚未配置完成。', 'warning');
      } else if (data.status.state === 'api_error') {
        setStatusMessage(data.status.error || 'SecondMe 当前不可用，请稍后再试。', 'error');
      }
      return data.status;
    } catch (error) {
      console.error(error);
    }
    return null;
  };

  const loadDiseaseStory = async (diseaseType) => {
    if (!diseaseType?.trim()) return;
    setDiseaseStoryLoading(true);
    try {
      const [research, recommendations] = await Promise.all([
        fetchJson('/api/v1/platform/research', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ disease_name: diseaseType }),
        }).catch(() => null),
        fetchJson(`/api/v1/community/recommend/${encodeURIComponent(diseaseType)}`).catch(() => null),
      ]);

      setDiseaseStory(research?.ok ? research : null);
      setRecommendedCircles(recommendations?.ok ? recommendations.recommendations : []);
    } catch (error) {
      console.error(error);
      setDiseaseStory(null);
      setRecommendedCircles([]);
    } finally {
      setDiseaseStoryLoading(false);
    }
  };

  const buildSummaryPayload = (avatar, profileSource = {}) => ({
    nickname: avatar.nickname,
    disease_type: avatar.disease_type,
    bio: avatar.bio,
    age: profileSource.age ? Number(profileSource.age) : null,
    symptoms: profileSource.symptoms || '',
    diagnosis: profileSource.diagnosis || '',
    treatment_history: profileSource.treatment_history || '',
  });

  const syncSummaryForAvatar = async (avatar, profileSource = {}, { silent = false } = {}) => {
    const data = await fetchJson('/api/v1/secondme/note/patient-summary', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(buildSummaryPayload(avatar, profileSource)),
    });
    const meta = {
      noteId: data.note_id,
      syncedAt: new Date().toISOString(),
    };
    persistSummarySyncMeta(avatar.id, meta);
    if (!silent) {
      setStatusMessage(`患者摘要已同步到 SecondMe，note_id=${data.note_id}`, 'success');
    }
    return meta;
  };

  const buildProfileAwareContext = (avatar, community) => {
    const linkedProfile = secondMeStatus?.user || avatar?.linked_secondme_profile || {};
    const disease = diseaseStory?.disease || {};
    const carePoints = (diseaseStory?.care_points || []).slice(0, 2);
    const questions = (diseaseStory?.patient_questions || []).slice(0, 2);
    const tags = Array.isArray(linkedProfile.tags) ? linkedProfile.tags.filter(Boolean).slice(0, 4) : [];

    return [
      `患者昵称：${avatar?.nickname || ''}`,
      `疾病类型：${avatar?.disease_type || disease.name || ''}`,
      community?.name ? `目标病友圈：${community.name}` : '',
      linkedProfile.display_name ? `SecondMe 账号名：${linkedProfile.display_name}` : '',
      linkedProfile.bio ? `SecondMe 背景摘要：${linkedProfile.bio.slice(0, 180)}` : '',
      tags.length ? `SecondMe tags：${tags.join('、')}` : '',
      disease.gene ? `关键基因：${disease.gene}` : '',
      disease.inheritance ? `遗传方式：${disease.inheritance}` : '',
      carePoints.length ? `建议先问：${carePoints.join('；')}` : '',
      questions.length ? `患者常问：${questions.join('；')}` : '',
    ].filter(Boolean).join('\n');
  };

  const loadPosts = async (communityId) => {
    setLoadingPosts(true);
    try {
      const data = await fetchJson(`/api/v1/community/${communityId}/posts`);
      if (data.ok) setPosts(data.posts);
    } catch (error) {
      console.error(error);
    } finally {
      setLoadingPosts(false);
    }
  };

  const loadMatchSuggestions = async (avatarId) => {
    try {
      const data = await fetchJson(`/api/v1/community/avatar/${avatarId}/matches`);
      if (data.ok) setMatchSuggestions(data.matches);
    } catch (error) {
      console.error(error);
      setMatchSuggestions([]);
    }
  };

  const handleSelectComm = (community) => {
    setSelectedComm(community);
    loadPosts(community.id);
  };

  const handleOpenDiseaseResearch = (disease) => {
    if (!disease?.name) return;
    onNavigate?.('disease-research');
  };

  const handleOpenDiseaseCommunity = (disease) => {
    if (!disease?.name) return;
    const target = communities.find((item) => item.name.includes(disease.name))
      || communitiesShown.find((item) => item.name.includes(disease.name));
    if (target) {
      handleSelectComm(target);
      setStatusMessage(`已切换到 ${target.name}，可以直接查看相关病友讨论。`, 'success');
      return;
    }
    loadDiseaseStory(disease.name);
    setStatusMessage(`${disease.name} 的公开病友圈正在整理中，先为你打开疾病上下文。`, 'neutral');
  };

  const findCommunityByKeyword = (...keywords) => {
    const pool = [...communities, ...communitiesShown];
    return pool.find((item) => keywords.some((keyword) => item.name.includes(keyword)));
  };

  const handleOpenLiveRoom = (room) => {
    if (!room?.id) return;

    if (room.id === 'room_trials') {
      onNavigate?.('drug-research');
      setStatusMessage('已为你打开临床试验与药物线索页，可以继续看新药动态和筛选标准。', 'success');
      return;
    }

    if (room.id === 'room_parents') {
      const target = findCommunityByKeyword('康复训练', '心理支持');
      if (target) {
        handleSelectComm(target);
        setStatusMessage(`已为你打开 ${target.name}，方便继续承接家长圆桌的话题。`, 'success');
        return;
      }
      setStatusMessage('家长互助入口正在整理中，先从康复和心理支持话题开始。', 'warning');
      return;
    }

    if (!myAvatar) {
      setShowCreateAvatar(true);
      setStatusMessage('欢迎房建议先创建患者分身，这样系统会更准确地帮你整理病历和情绪。', 'warning');
      return;
    }

    const diseaseTarget = myAvatar?.disease_type ? findCommunityByKeyword(myAvatar.disease_type) : null;
    const fallback = diseaseTarget || findCommunityByKeyword('心理支持') || communitiesShown[0] || communities[0];
    if (fallback) {
      handleSelectComm(fallback);
      setStatusMessage(`已为你打开 ${fallback.name}，可以把欢迎房里的问题继续带入病友圈。`, 'success');
    }
  };

  const handleOpenToyProgram = () => {
    onNavigate?.('care-loop');
    setStatusMessage('已为你打开长期管理页，可以继续把陪伴玩偶和随访计划接进管理闭环。', 'success');
  };

  const handleOpenVoiceFollowup = () => {
    onNavigate?.('ai-chat');
    setStatusMessage('已为你打开 AI 陪诊入口，下一步可以把语音随访设备接到持续沟通链路里。', 'success');
  };

  const handleConnectSecondMe = () => {
    const returnTo = `${window.location.origin}/index.html`;
    window.location.href = `${API_BASE}/api/v1/secondme/oauth/start?return_to=${encodeURIComponent(returnTo)}`;
  };

  const handleDisconnectSecondMe = async () => {
    try {
      await fetchJson('/api/v1/secondme/oauth/logout', { method: 'POST' });
      setStatusMessage('SecondMe 已断开授权。', 'neutral');
      loadSecondMeStatus();
    } catch (error) {
      console.error(error);
      setStatusMessage(error.message, 'error');
    }
  };

  const handleSyncSummary = async () => {
    if (!myAvatar) return;
    setSyncingSummary(true);
    try {
      await syncSummaryForAvatar(myAvatar, myAvatar.profile_source || {});
    } catch (error) {
      console.error(error);
      setStatusMessage(error.message, 'error');
      loadSecondMeStatus();
    } finally {
      setSyncingSummary(false);
    }
  };

  const handleDraftIntro = async () => {
    if (!myAvatar) return;
    setDraftingIntro(true);
    try {
      const context = buildProfileAwareContext(myAvatar, selectedComm);
      const data = await fetchJson('/api/v1/community/avatar/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          avatar_id: myAvatar.id,
          message: [
            '请用第一人称写一段 80-120 字的社群自我介绍，语气真诚，包含我希望获得什么帮助。',
            '不要像医院宣传文，不要列清单，要像患者本人第一次进群时会说的话。',
            context,
          ].filter(Boolean).join('\n\n'),
        }),
      });
      setAvatarIntro(data.reply);
    } catch (error) {
      console.error(error);
      setStatusMessage(error.message, 'error');
    } finally {
      setDraftingIntro(false);
    }
  };

  const handleDraftFirstPost = async (modeKey = firstPostType) => {
    if (!myAvatar) return;
    const community = selectedComm || communitiesShown[0] || communities[0] || null;
    const mode = FIRST_POST_MODES.find((item) => item.key === modeKey) || FIRST_POST_MODES[0];
    if (community && !selectedComm) {
      setSelectedComm(community);
    }

    setDraftingFirstPostMode(mode.key);
    setFirstPostType(mode.key);
    try {
      const context = buildProfileAwareContext(myAvatar, community);
      const data = await fetchJson('/api/v1/community/avatar/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          avatar_id: myAvatar.id,
          message: [
            `请为我生成一条适合发在病友社群的首条动态，模式为「${mode.key}」，长度 90-150 字。`,
            '要求：像患者本人真实发帖，不要太像 AI；不要编造医学结论；尽量结合我的个人背景、SecondMe 资料和病种信息。',
            ...mode.prompt,
            community?.name ? `发布场景：${community.name}` : '',
            context,
          ].filter(Boolean).join('\n\n'),
        }),
      });
      setFirstPostDraft(data.reply);
      setShowCreatePost(true);
    } catch (error) {
      console.error(error);
      setStatusMessage(error.message, 'error');
    } finally {
      setDraftingFirstPostMode('');
    }
  };

  const handleAvatarCreated = async ({ avatar, profileSource, joinedCommunities }) => {
    const nextAvatar = {
      ...avatar,
      profile_source: profileSource,
      joined_communities: joinedCommunities,
      linked_secondme_profile: secondMeStatus?.user || null,
    };
    persistAvatar(nextAvatar);
    setShowCreateAvatar(false);

    const [nextCommunities] = await Promise.all([
      loadCommunities(),
      loadDashboard(),
    ]);

    if (Array.isArray(nextCommunities) && joinedCommunities?.length > 0) {
      const preferred = nextCommunities.find((item) => item.name === joinedCommunities[0]);
      if (preferred) setSelectedComm(preferred);
    }

    if (secondMeState === 'connected') {
      try {
        const meta = await syncSummaryForAvatar(nextAvatar, profileSource, { silent: true });
        setStatusMessage(
          `AI 分身创建完成，并已把患者摘要同步到 SecondMe。note_id=${meta.noteId}`,
          'success',
        );
      } catch (error) {
        console.error(error);
        setStatusMessage(
          `AI 分身已创建，但摘要同步失败：${error.message}`,
          'warning',
        );
        loadSecondMeStatus();
      }
      return;
    }

    setStatusMessage('AI 分身创建成功。连接 SecondMe 后可把病程摘要同步为长期记忆。', 'success');
  };

  const handleBridgeConnect = async (targetAvatarId, context) => {
    if (!myAvatar) return;
    setBridgeLoadingId(targetAvatarId);
    try {
      const data = await fetchJson('/api/v1/community/bridge', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          avatar_id: myAvatar.id,
          target_avatar_id: targetAvatarId,
          context,
        }),
      });
      if (data.ok) {
        setStatusMessage(
          `已创建 Bridge 连接，匹配理由：${data.connection.match_reason}，匹配度 ${Math.round(data.connection.match_score * 100)}%`,
          'success',
        );
      }
    } catch (error) {
      console.error(error);
      setStatusMessage(error.message, 'error');
    } finally {
      setBridgeLoadingId('');
    }
  };

  const secondMeState = secondMeStatus?.state || 'unauthenticated';
  const secondMeDisplayName = secondMeStatus?.user?.display_name || secondMeStatus?.user?.nickname || 'SecondMe 用户';
  const canConnectSecondMe = secondMeStatus?.configured !== false;
  const summaryReady = Boolean(summarySyncMeta?.noteId);
  const linkedProfile = secondMeStatus?.user || myAvatar?.linked_secondme_profile || null;
  const connectButtonLabel = secondMeState === 'expired' ? '重新连接 SecondMe' : '连接 SecondMe';
  const communitiesShown = dashboard?.featured_communities || communities.slice(0, 6);
  const trendingPosts = dashboard?.trending_posts || [];
  const liveRooms = dashboard?.live_rooms || [];
  const prompts = dashboard?.engagement_prompts || [];
  const linkedProfileTags = Array.isArray(linkedProfile?.tags) ? linkedProfile.tags.slice(0, 4) : [];
  const featuredLiveRooms = liveRooms.map((room) => ({
    ...room,
    ...(LIVE_ROOM_STYLES[room.id] || {}),
  }));
  const onboardingSteps = [
    {
      key: 'oauth',
      title: '连接 SecondMe',
      description: '用真实账号完成授权，让患者长期记忆和社群入口连在一起。',
      done: secondMeState === 'connected',
      actionLabel: canConnectSecondMe ? connectButtonLabel : '等待配置',
      action: canConnectSecondMe ? handleConnectSecondMe : null,
      tone: secondMeState === 'connected' ? 'success' : secondMeState === 'expired' ? 'warning' : 'neutral',
      meta: secondMeState === 'connected' ? `已连接 ${secondMeDisplayName}` : '未连接时仍可创建本地分身，但无法写入记忆',
    },
    {
      key: 'avatar',
      title: '创建 AI 分身',
      description: '整理昵称、病程、主要症状和治疗阶段，生成社群身份卡。',
      done: Boolean(myAvatar),
      actionLabel: myAvatar ? '已完成' : '创建分身',
      action: myAvatar ? null : () => setShowCreateAvatar(true),
      tone: myAvatar ? 'success' : 'neutral',
      meta: myAvatar ? `${myAvatar.nickname} · ${myAvatar.disease_type}` : '分身会用于发帖、病友匹配和自我介绍',
    },
    {
      key: 'summary',
      title: '同步患者摘要',
      description: '把病情摘要写入 SecondMe，后续社群和病友连接会更准确。',
      done: summaryReady,
      actionLabel: summaryReady ? '已同步' : '同步摘要',
      action: myAvatar && secondMeState === 'connected' && !summaryReady ? handleSyncSummary : null,
      tone: summaryReady ? 'success' : myAvatar && secondMeState === 'connected' ? 'warning' : 'neutral',
      meta: summaryReady ? `note_id=${summarySyncMeta.noteId}` : '需要已登录 + 已创建分身',
    },
    {
      key: 'community',
      title: '进入病友圈',
      description: '选择合适的病友圈，发第一条动态，建立第一批互助连接。',
      done: Boolean(selectedComm),
      actionLabel: selectedComm ? '已进入' : '逛病友圈',
      action: selectedComm ? null : () => setSelectedComm(communitiesShown[0] || communities[0] || null),
      tone: selectedComm ? 'success' : 'neutral',
      meta: selectedComm ? `${selectedComm.name}` : '推荐病友圈和热门帖子已经准备好',
    },
  ];

  return (
    <div className="community-page">
      <section className="community-cosmos-hero">
        <div className="community-cosmos-top">
          <div className="community-cosmos-copy">
            <div className="community-cosmos-kicker">SecondMe patient community</div>
            <h1>让患者不只是“看内容”，而是真的进来、留下、和病友建立连接</h1>
            <p>
              用 SecondMe 建立患者分身，用 Bridge 做病友连接，再用病友圈承接长期情绪支持、就诊经验和治疗打卡。
              第一屏直接把欢迎区、病种地球和行动入口连成一个整体，不再让页面碎成几块。
            </p>
            <div className="community-cosmos-tags">
              {['更轻松的陪伴', '明亮的病友空间', '真实互动与连接'].map((label) => (
                <span key={label}>{label}</span>
              ))}
            </div>
          </div>

          <div className="community-cosmos-board">
            <div className="community-cosmos-board-kicker">社群实时看板</div>
            <div className="community-cosmos-metrics">
              {[
                { label: '推荐病友圈', value: `${communitiesShown.length}` },
                { label: '热门帖子', value: `${trendingPosts.length}` },
                { label: '互动房间', value: `${liveRooms.length}` },
                { label: 'SecondMe 状态', value: secondMeState === 'connected' ? '已连接' : '待连接' },
              ].map((item) => (
                <div key={item.label} className="community-cosmos-metric">
                  <span>{item.label}</span>
                  <strong>{item.value}</strong>
                </div>
              ))}
            </div>
          </div>
        </div>

        <RareDiseaseGlobe
          embedded
          onOpenDisease={handleOpenDiseaseResearch}
          onOpenCommunity={handleOpenDiseaseCommunity}
        />
      </section>

      {featuredLiveRooms.length > 0 && (
        <FeaturedLiveRoomsPanel
          rooms={featuredLiveRooms}
          onOpenRoom={handleOpenLiveRoom}
        />
      )}

      <CompanionHardwarePanel
        onOpenToyProgram={handleOpenToyProgram}
        onOpenVoiceFollowup={handleOpenVoiceFollowup}
      />

      <OnboardingJourney steps={onboardingSteps} />

      <section style={{ display: 'grid', gap: 18, marginTop: 18 }}>
        <SecondMeStatusPanel
          secondMeState={secondMeState}
          secondMeStatus={secondMeStatus}
          secondMeDisplayName={secondMeDisplayName}
          secondMeMessage={secondMeMessage}
          secondMeTone={secondMeTone}
          canConnectSecondMe={canConnectSecondMe}
          connectButtonLabel={connectButtonLabel}
          myAvatar={myAvatar}
          syncingSummary={syncingSummary}
          summarySyncMeta={summarySyncMeta}
          onConnect={handleConnectSecondMe}
          onDisconnect={handleDisconnectSecondMe}
          onSync={handleSyncSummary}
        />

        {myAvatar ? (
          <section style={{ display: 'grid', gap: 18 }}>
            <div style={{
              ...cardStyle({ padding: 24 }),
              display: 'grid',
              gridTemplateColumns: 'minmax(0, 1fr) minmax(340px, 0.8fr)',
              gap: 18,
            }}>
              <div>
                <div style={{ fontSize: 12, letterSpacing: '0.08em', textTransform: 'uppercase', color: '#FF7A59', fontWeight: 700 }}>
                  My SecondMe identity
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginTop: 14 }}>
                  <div style={{
                    width: 72, height: 72, borderRadius: '50%',
                    background: 'linear-gradient(135deg, #0DBF9B 0%, #173A68 100%)',
                    color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center',
                    fontWeight: 800, fontSize: 24,
                    overflow: 'hidden',
                  }}>
                    {linkedProfile?.avatar ? (
                      <img
                        src={linkedProfile.avatar}
                        alt={myAvatar.nickname || 'avatar'}
                        style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                      />
                    ) : (
                      myAvatar.nickname?.slice(0, 1) || '我'
                    )}
                  </div>
                  <div>
                    <div style={{ fontSize: 24, fontWeight: 800, color: '#0C1831' }}>{myAvatar.nickname}</div>
                    <div style={{ fontSize: 14, color: '#44506A', marginTop: 4 }}>{myAvatar.disease_type} · AI 分身已上线</div>
                    <div style={{ fontSize: 12, color: '#7D879A', marginTop: 6 }}>
                      {summaryReady ? `摘要已同步 · note_id=${summarySyncMeta.noteId}` : '摘要尚未同步到 SecondMe'}
                    </div>
                  </div>
                </div>
                {linkedProfile && (
                  <div style={{
                    marginTop: 16,
                    padding: 16,
                    borderRadius: 18,
                    background: 'rgba(12,24,49,0.04)',
                    border: '1px solid rgba(12,24,49,0.06)',
                  }}>
                    <div style={{ fontSize: 12, letterSpacing: '0.08em', textTransform: 'uppercase', color: '#0DBF9B', fontWeight: 700 }}>
                      Linked SecondMe profile
                    </div>
                    <div style={{ fontSize: 16, fontWeight: 800, color: '#0C1831', marginTop: 8 }}>
                      {linkedProfile.display_name || linkedProfile.nickname || 'SecondMe 用户'}
                    </div>
                    {linkedProfile.bio && (
                      <div style={{ fontSize: 13, color: '#44506A', lineHeight: 1.75, marginTop: 8 }}>
                        {linkedProfile.bio.slice(0, 220)}{linkedProfile.bio.length > 220 ? '…' : ''}
                      </div>
                    )}
                    {Array.isArray(linkedProfile.tags) && linkedProfile.tags.length > 0 && (
                      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginTop: 10 }}>
                        {linkedProfile.tags.slice(0, 4).map((tag) => (
                          <span key={tag} style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            padding: '6px 10px',
                            borderRadius: 999,
                            background: 'rgba(255,255,255,0.82)',
                            border: '1px solid rgba(12,24,49,0.08)',
                            fontSize: 12,
                            color: '#44506A',
                          }}>
                            {tag}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                )}
                <p style={{ fontSize: 14, color: '#44506A', lineHeight: 1.8, marginTop: 14 }}>
                  {myAvatar.bio || '这个分身会帮你在病友圈里完成第一轮自我介绍、病程表达与互动连接。'}
                </p>
                <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginTop: 16 }}>
                  <button type="button" onClick={handleDraftIntro} disabled={draftingIntro} style={softButtonStyle('ghost', draftingIntro)}>
                    {draftingIntro ? '生成中...' : '让分身写自我介绍'}
                  </button>
                </div>
                {avatarIntro && (
                  <div style={{
                    marginTop: 16, padding: 16, borderRadius: 18,
                    background: 'rgba(12,24,49,0.04)', color: '#44506A', lineHeight: 1.8,
                  }}>
                    {avatarIntro}
                  </div>
                )}
                <div style={{ marginTop: 18 }}>
                  <div style={{ fontSize: 12, letterSpacing: '0.08em', textTransform: 'uppercase', color: '#0DBF9B', fontWeight: 700 }}>
                    First post modes
                  </div>
                  <div style={{ display: 'grid', gap: 10, marginTop: 12 }}>
                    {FIRST_POST_MODES.map((mode) => (
                      <div
                        key={mode.key}
                        style={{
                          borderRadius: 18,
                          padding: 16,
                          background: mode.background,
                          border: `1px solid ${mode.accent}22`,
                        }}
                      >
                        <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, alignItems: 'flex-start', flexWrap: 'wrap' }}>
                          <div>
                            <div style={{ fontSize: 16, fontWeight: 800, color: '#0C1831' }}>{mode.title}</div>
                            <div style={{ fontSize: 13, color: '#44506A', lineHeight: 1.7, marginTop: 6 }}>{mode.subtitle}</div>
                          </div>
                          <button
                            type="button"
                            onClick={() => handleDraftFirstPost(mode.key)}
                            disabled={Boolean(draftingFirstPostMode)}
                            style={{
                              ...softButtonStyle(mode.key === '经验分享' ? 'ghost' : 'primary', Boolean(draftingFirstPostMode)),
                              background: mode.key === '经验分享'
                                ? 'rgba(255,255,255,0.82)'
                                : undefined,
                              borderColor: mode.key === '经验分享' ? `${mode.accent}33` : undefined,
                            }}
                          >
                            {draftingFirstPostMode === mode.key ? '生成中...' : `生成${mode.title}`}
                          </button>
                        </div>
                        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginTop: 10 }}>
                          {mode.prompt.slice(0, 2).map((item) => (
                            <span
                              key={item}
                              style={{
                                display: 'inline-flex',
                                alignItems: 'center',
                                padding: '6px 10px',
                                borderRadius: 999,
                                background: 'rgba(255,255,255,0.82)',
                                border: '1px solid rgba(12,24,49,0.08)',
                                color: '#44506A',
                                fontSize: 12,
                              }}
                            >
                              {item}
                            </span>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              <div style={{
                borderRadius: 24,
                padding: 20,
                background: 'linear-gradient(160deg, rgba(12,24,49,0.96) 0%, rgba(23,58,104,0.92) 100%)',
                color: '#fff',
              }}>
                <div style={{ fontSize: 12, letterSpacing: '0.08em', textTransform: 'uppercase', opacity: 0.82, fontWeight: 700 }}>
                  今日互动脚本
                </div>
                <div style={{ fontSize: 24, fontWeight: 800, lineHeight: 1.12, marginTop: 12 }}>
                  从“我是谁”走到“我能跟谁说话”
                </div>
                <div style={{ display: 'grid', gap: 14, marginTop: 18 }}>
                  {[
                    `先把 ${myAvatar.disease_type} 的病程摘要写入 SecondMe，保证后续输出稳定一致。`,
                    '优先建立 1-2 个同阶段病友连接，再进入更广的公开社群。',
                    '第一条动态尽量只问一个最具体的问题，最容易获得回应。',
                  ].map((item, index) => (
                    <div key={item} style={{ display: 'grid', gridTemplateColumns: '28px minmax(0, 1fr)', gap: 12, alignItems: 'flex-start' }}>
                      <div style={{
                        width: 28, height: 28, borderRadius: '50%',
                        background: 'rgba(255,255,255,0.14)', display: 'flex',
                        alignItems: 'center', justifyContent: 'center', fontWeight: 800,
                      }}>
                        {index + 1}
                      </div>
                      <div style={{ color: 'rgba(255,255,255,0.84)', lineHeight: 1.7 }}>{item}</div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <DiseaseStoryPanel
              story={diseaseStory}
              loading={diseaseStoryLoading}
              recommendedCircles={recommendedCircles}
              onSelectCommunity={(communityName) => {
                const target = communities.find((item) => item.name === communityName) || communitiesShown.find((item) => item.name === communityName);
                if (target) handleSelectComm(target);
              }}
            />

            <div style={{ ...cardStyle({ padding: 24 }) }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', gap: 16, alignItems: 'center', flexWrap: 'wrap' }}>
                <div>
                  <div style={{ fontSize: 12, letterSpacing: '0.08em', textTransform: 'uppercase', color: '#0DBF9B', fontWeight: 700 }}>
                    Bridge matching
                  </div>
                  <div style={{ fontSize: 22, fontWeight: 800, color: '#0C1831', marginTop: 8 }}>
                    推荐先和这些病友建立连接
                  </div>
                  {linkedProfileTags.length > 0 && (
                    <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginTop: 10 }}>
                      <span style={{ fontSize: 12, color: '#7D879A' }}>已参考你的 SecondMe 标签</span>
                      {linkedProfileTags.map((tag) => (
                        <span
                          key={tag}
                          style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            padding: '6px 10px',
                            borderRadius: 999,
                            background: 'rgba(13,191,155,0.12)',
                            color: '#08886F',
                            fontSize: 12,
                            fontWeight: 700,
                          }}
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: 14, marginTop: 18 }}>
                {matchSuggestions.map((match) => (
                  <div key={`${match.avatar_id}-${match.nickname}`} style={{
                    borderRadius: 20, padding: 18, background: 'rgba(12,24,49,0.04)',
                    border: '1px solid rgba(12,24,49,0.06)',
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', gap: 10, alignItems: 'flex-start' }}>
                      <div>
                        <div style={{ fontSize: 18, fontWeight: 800, color: '#0C1831' }}>{match.nickname}</div>
                        <div style={{ fontSize: 13, color: '#0DBF9B', marginTop: 4 }}>{match.community}</div>
                      </div>
                      <span style={{
                        padding: '6px 10px',
                        borderRadius: 999,
                        background: 'rgba(13,191,155,0.12)',
                        color: '#08886F',
                        fontSize: 12,
                        fontWeight: 700,
                      }}>
                        {Math.round(match.match_score * 100)}%
                      </span>
                    </div>
                    <p style={{ fontSize: 13, color: '#44506A', lineHeight: 1.7 }}>{match.bio}</p>
                    {Array.isArray(match.connection_points) && match.connection_points.length > 0 && (
                      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginTop: 10 }}>
                        {match.connection_points.slice(0, 4).map((point) => (
                          <span
                            key={point}
                            style={{
                              display: 'inline-flex',
                              alignItems: 'center',
                              padding: '6px 10px',
                              borderRadius: 999,
                              background: 'rgba(255,255,255,0.84)',
                              border: '1px solid rgba(12,24,49,0.08)',
                              color: '#44506A',
                              fontSize: 12,
                            }}
                          >
                            {point}
                          </span>
                        ))}
                      </div>
                    )}
                    <div style={{ fontSize: 12, color: '#7D879A', lineHeight: 1.7 }}>
                      匹配理由：{match.match_reason}
                    </div>
                    <div style={{
                      height: 8,
                      borderRadius: 999,
                      marginTop: 12,
                      background: 'rgba(12,24,49,0.08)',
                      overflow: 'hidden',
                    }}>
                      <div style={{
                        width: `${Math.max(18, Math.round(match.match_score * 100))}%`,
                        height: '100%',
                        background: 'linear-gradient(90deg, #0DBF9B 0%, #173A68 100%)',
                      }} />
                    </div>
                    <button
                      type="button"
                      onClick={() => handleBridgeConnect(match.avatar_id, match.match_reason)}
                      disabled={bridgeLoadingId === match.avatar_id}
                      style={{ ...softButtonStyle('primary', bridgeLoadingId === match.avatar_id), marginTop: 14, width: '100%' }}
                    >
                      {bridgeLoadingId === match.avatar_id ? '连接中...' : 'Bridge 连接'}
                    </button>
                  </div>
                ))}
              </div>
            </div>
          </section>
        ) : (
          <section style={{
            ...cardStyle({ padding: 26 }),
            display: 'grid',
            gridTemplateColumns: 'minmax(0, 1fr) minmax(320px, 0.78fr)',
            gap: 18,
          }}>
            <div>
              <div style={{ fontSize: 12, letterSpacing: '0.08em', textTransform: 'uppercase', color: '#FF7A59', fontWeight: 700 }}>
                Patient onboarding
              </div>
              <div style={{ fontSize: 30, fontWeight: 800, color: '#0C1831', marginTop: 10, lineHeight: 1.05 }}>
                先登录，再生成一个真正会替你说话的患者分身
              </div>
              <p style={{ fontSize: 14, color: '#44506A', lineHeight: 1.9, maxWidth: 620 }}>
                这一步会把昵称、疾病类型、主要症状和就诊阶段整理成一个持续可用的患者身份卡。登录成功后，摘要会同步进 SecondMe；之后无论是发帖、匹配病友还是建立长期记忆，都会沿着同一条链路走。
              </p>
              <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginTop: 14 }}>
                {secondMeState === 'connected' ? (
                  <button type="button" onClick={() => setShowCreateAvatar(true)} style={softButtonStyle('primary')}>
                    创建我的 AI 分身
                  </button>
                ) : (
                  <button type="button" onClick={handleConnectSecondMe} disabled={!canConnectSecondMe} style={softButtonStyle('primary', !canConnectSecondMe)}>
                    {connectButtonLabel}
                  </button>
                )}
                <button type="button" onClick={() => setShowCreateAvatar(true)} style={softButtonStyle('ghost')}>
                  先预填病程信息
                </button>
              </div>
            </div>

            <div style={{
              borderRadius: 24,
              padding: 22,
              background: 'linear-gradient(180deg, rgba(12,24,49,0.04) 0%, rgba(12,24,49,0.01) 100%)',
              border: '1px solid rgba(12,24,49,0.06)',
            }}>
              <div style={{ fontSize: 16, fontWeight: 800, color: '#0C1831' }}>创建后会自动发生</div>
              <div style={{ display: 'grid', gap: 14, marginTop: 16 }}>
                {[
                  '自动匹配同病种病友圈与主题房间，减少“我该先去哪里”的犹豫。',
                  '生成适合病友社群的自我介绍口吻，降低第一次发帖的心理门槛。',
                  '若已连接 SecondMe，会直接把核心病程写入记忆，后续更像同一个人。',
                ].map((item, index) => (
                  <div key={item} style={{ display: 'grid', gridTemplateColumns: '28px minmax(0, 1fr)', gap: 12 }}>
                    <div style={{
                      width: 28, height: 28, borderRadius: '50%',
                      background: index === 0 ? 'rgba(13,191,155,0.14)' : index === 1 ? 'rgba(255,122,89,0.14)' : 'rgba(12,24,49,0.08)',
                      color: '#0C1831',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontWeight: 800,
                    }}>
                      {index + 1}
                    </div>
                    <div style={{ color: '#44506A', lineHeight: 1.75 }}>{item}</div>
                  </div>
                ))}
              </div>
            </div>
          </section>
        )}
      </section>

      {!selectedComm ? (
        <section style={{ display: 'grid', gap: 18, marginTop: 18 }}>
          <div style={{ ...cardStyle({ padding: 24 }) }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', gap: 16, alignItems: 'center', flexWrap: 'wrap' }}>
              <div>
                <div style={{ fontSize: 12, letterSpacing: '0.08em', textTransform: 'uppercase', color: '#0DBF9B', fontWeight: 700 }}>
                  Featured circles
                </div>
                <div style={{ fontSize: 22, fontWeight: 800, color: '#0C1831', marginTop: 8 }}>推荐先逛这些社群</div>
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: 14, marginTop: 18 }}>
              {communitiesShown.map((community) => (
                <button
                  key={community.id}
                  type="button"
                  onClick={() => handleSelectComm(community)}
                  style={{
                    textAlign: 'left',
                    padding: 18,
                    borderRadius: 20,
                    background: 'rgba(12,24,49,0.04)',
                    border: '1px solid rgba(12,24,49,0.06)',
                    cursor: 'pointer',
                  }}
                >
                  <div style={{ fontSize: 18, fontWeight: 800, color: '#0C1831' }}>{community.name}</div>
                  <p style={{ fontSize: 13, color: '#44506A', lineHeight: 1.7, margin: '8px 0 0' }}>
                    {community.description}
                  </p>
                  <div style={{ display: 'flex', justifyContent: 'space-between', gap: 10, marginTop: 14, fontSize: 12, color: '#7D879A' }}>
                    <span>{community.member_count} 成员</span>
                    <span>{community.post_count} 帖子</span>
                  </div>
                </button>
              ))}
            </div>
          </div>

          <div>
            <div style={{ ...cardStyle({ padding: 24 }) }}>
              <div style={{ fontSize: 12, letterSpacing: '0.08em', textTransform: 'uppercase', color: '#0DBF9B', fontWeight: 700 }}>
                Trending posts
              </div>
              <div style={{ display: 'grid', gap: 12, marginTop: 14 }}>
                {trendingPosts.map((post) => (
                  <div key={post.id} style={{
                    padding: 16, borderRadius: 18, background: 'rgba(12,24,49,0.04)',
                    border: '1px solid rgba(12,24,49,0.06)',
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, fontSize: 12, color: '#7D879A' }}>
                      <span>{post.community_name}</span>
                      <span>{post.likes} 喜欢</span>
                    </div>
                    <div style={{ fontSize: 15, fontWeight: 700, color: '#0C1831', marginTop: 10 }}>{post.author}</div>
                    <p style={{ fontSize: 13, color: '#44506A', lineHeight: 1.7, margin: '8px 0 0' }}>{post.content}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {prompts.length > 0 && (
            <div style={{ ...cardStyle({ padding: 24 }) }}>
              <div style={{ fontSize: 12, letterSpacing: '0.08em', textTransform: 'uppercase', color: '#0DBF9B', fontWeight: 700 }}>
                今日发帖灵感
              </div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 10, marginTop: 14 }}>
                {prompts.map((prompt) => (
                  <span key={prompt} style={{
                    display: 'inline-flex', alignItems: 'center', padding: '9px 14px',
                    borderRadius: 999, background: 'rgba(255,255,255,0.82)', border: '1px solid rgba(12,24,49,0.08)',
                    color: '#44506A', fontSize: 13,
                  }}>
                    {prompt}
                  </span>
                ))}
              </div>
            </div>
          )}
        </section>
      ) : (
        <section style={{ ...cardStyle({ padding: 24, marginTop: 18 }) }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', gap: 16, alignItems: 'center', flexWrap: 'wrap' }}>
            <div>
              <button
                type="button"
                onClick={() => {
                  setSelectedComm(null);
                  setPosts([]);
                }}
                style={{ ...softButtonStyle('ghost'), marginBottom: 10 }}
              >
                返回社群首页
              </button>
              <div style={{ fontSize: 26, fontWeight: 800, color: '#0C1831' }}>{selectedComm.name}</div>
              <div style={{ fontSize: 13, color: '#7D879A', marginTop: 6 }}>{selectedComm.description}</div>
            </div>

            {myAvatar && (
              <button type="button" onClick={() => setShowCreatePost(true)} style={softButtonStyle('primary')}>
                发表新帖子
              </button>
            )}
          </div>

          {loadingPosts ? (
            <div style={{ padding: '40px 0', textAlign: 'center', color: '#7D879A' }}>正在加载帖子...</div>
          ) : posts.length === 0 ? (
            <div style={{ padding: '40px 0', textAlign: 'center', color: '#7D879A' }}>这里还没有帖子，发第一条吧。</div>
          ) : (
            <div style={{ display: 'grid', gap: 14, marginTop: 20 }}>
              {posts.map((post) => (
                <article key={post.id} style={{
                  padding: 18, borderRadius: 20, background: 'rgba(12,24,49,0.04)',
                  border: '1px solid rgba(12,24,49,0.06)',
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, alignItems: 'flex-start', flexWrap: 'wrap' }}>
                    <div>
                      <div style={{ fontSize: 15, fontWeight: 800, color: '#0C1831' }}>{post.author}</div>
                      <div style={{ fontSize: 12, color: '#7D879A', marginTop: 4 }}>{post.created_at}</div>
                    </div>
                    <span style={{
                      padding: '6px 10px', borderRadius: 999, fontSize: 12, fontWeight: 700,
                      background: post.type === '求助提问' ? '#FFF7ED'
                        : post.type === '经验分享' ? '#ECFDF5'
                          : post.type === '心理支持' ? '#F5F3FF'
                            : '#EFF6FF',
                      color: post.type === '求助提问' ? '#C2410C'
                        : post.type === '经验分享' ? '#166534'
                          : post.type === '心理支持' ? '#6D28D9'
                            : '#1D4ED8',
                    }}>
                      {post.type}
                    </span>
                  </div>
                  <p style={{ fontSize: 14, color: '#44506A', lineHeight: 1.8, margin: '12px 0 0' }}>{post.content}</p>
                  <div style={{ display: 'flex', gap: 18, marginTop: 12, fontSize: 12, color: '#7D879A' }}>
                    <span>❤️ {post.likes}</span>
                    <span>💬 回复</span>
                    <span>🔗 Bridge</span>
                  </div>
                </article>
              ))}
            </div>
          )}
        </section>
      )}

      {showCreateAvatar && (
        <CreateAvatarModal
          secondMeStatus={secondMeStatus}
          onClose={() => setShowCreateAvatar(false)}
          onSuccess={handleAvatarCreated}
        />
      )}

      {showCreatePost && myAvatar && selectedComm && (
        <CreatePostModal
          communityId={selectedComm.id}
          avatarId={myAvatar.id}
          nickname={myAvatar.nickname}
          initialContent={firstPostDraft || avatarIntro}
          initialPostType={firstPostType}
          linkedProfile={linkedProfile}
          onClose={() => {
            setShowCreatePost(false);
            setFirstPostDraft('');
          }}
          onSuccess={() => {
            setShowCreatePost(false);
            setFirstPostDraft('');
            loadPosts(selectedComm.id);
            loadDashboard();
          }}
        />
      )}
    </div>
  );
}


function OnboardingJourney({ steps }) {
  return (
    <section style={{
      ...cardStyle({
        padding: 24,
        marginTop: 18,
        background: 'linear-gradient(180deg, rgba(255,253,249,0.96) 0%, rgba(250,248,244,0.9) 100%)',
      }),
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', gap: 16, alignItems: 'center', flexWrap: 'wrap' }}>
        <div>
          <div style={{ fontSize: 12, letterSpacing: '0.08em', textTransform: 'uppercase', color: '#0DBF9B', fontWeight: 700 }}>
            Patient journey
          </div>
          <div style={{ fontSize: 24, fontWeight: 800, color: '#0C1831', marginTop: 8 }}>
            把登录、建分身、同步记忆和进入病友圈做成一条连续流程
          </div>
        </div>
        <div style={{ fontSize: 13, color: '#7D879A' }}>
          已完成 {steps.filter((step) => step.done).length} / {steps.length}
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 14, marginTop: 18 }}>
        {steps.map((step, index) => (
          <div key={step.key} style={{
            borderRadius: 22,
            padding: 18,
            background: step.done
              ? 'linear-gradient(180deg, rgba(13,191,155,0.1) 0%, rgba(13,191,155,0.03) 100%)'
              : 'rgba(12,24,49,0.03)',
            border: `1px solid ${step.done ? 'rgba(13,191,155,0.24)' : 'rgba(12,24,49,0.08)'}`,
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', gap: 10, alignItems: 'center' }}>
              <span style={{
                display: 'inline-flex',
                alignItems: 'center',
                justifyContent: 'center',
                width: 30,
                height: 30,
                borderRadius: '50%',
                background: step.done ? '#0DBF9B' : 'rgba(12,24,49,0.08)',
                color: step.done ? '#fff' : '#0C1831',
                fontWeight: 800,
                fontSize: 13,
              }}>
                {index + 1}
              </span>
              <span style={{
                padding: '6px 10px',
                borderRadius: 999,
                ...toneStyle(step.tone),
                fontSize: 12,
                fontWeight: 700,
              }}>
                {step.done ? '已完成' : step.tone === 'warning' ? '待处理' : '下一步'}
              </span>
            </div>
            <div style={{ fontSize: 18, fontWeight: 800, color: '#0C1831', marginTop: 14 }}>{step.title}</div>
            <div style={{ fontSize: 13, color: '#44506A', lineHeight: 1.7, marginTop: 8 }}>{step.description}</div>
            <div style={{ fontSize: 12, color: '#7D879A', lineHeight: 1.7, marginTop: 10 }}>{step.meta}</div>
            {step.action && (
              <button type="button" onClick={step.action} style={{ ...softButtonStyle(step.key === 'oauth' || step.key === 'summary' ? 'primary' : 'ghost'), marginTop: 14, width: '100%' }}>
                {step.actionLabel}
              </button>
            )}
          </div>
        ))}
      </div>
    </section>
  );
}

function LiveProgramPosterIllustration({ roomId }) {
  if (roomId === 'room_newcomer') {
    return (
      <div className="live-program-illustration scene-newcomer" aria-hidden="true">
        <span className="scene-star star-one" />
        <span className="scene-star star-two" />
        <span className="scene-star star-three" />
        <span className="scene-moon" />
        <span className="scene-cloud cloud-one" />
        <span className="scene-cloud cloud-two" />
        <span className="scene-hill hill-back" />
        <span className="scene-hill hill-front" />
        <span className="scene-character child" />
        <span className="scene-character bear" />
      </div>
    );
  }

  if (roomId === 'room_parents') {
    return (
      <div className="live-program-illustration scene-parents" aria-hidden="true">
        <span className="scene-sun" />
        <span className="scene-heart heart-one" />
        <span className="scene-heart heart-two" />
        <span className="scene-sofa" />
        <span className="scene-character parent-left" />
        <span className="scene-character child-center" />
        <span className="scene-character parent-right" />
      </div>
    );
  }

  return (
    <div className="live-program-illustration scene-trials" aria-hidden="true">
      <span className="scene-grid-line grid-h-one" />
      <span className="scene-grid-line grid-h-two" />
      <span className="scene-grid-line grid-v-one" />
      <span className="scene-grid-line grid-v-two" />
      <span className="scene-node node-one" />
      <span className="scene-node node-two" />
      <span className="scene-node node-three" />
      <span className="scene-route" />
      <span className="scene-capsule" />
      <span className="scene-card" />
    </div>
  );
}

function FeaturedLiveRoomsPanel({ rooms, onOpenRoom }) {
  const [activeIndex, setActiveIndex] = useState(0);

  useEffect(() => {
    if (rooms.length <= 1) return undefined;
    const intervalId = window.setInterval(() => {
      setActiveIndex((current) => (current + 1) % rooms.length);
    }, 5200);
    return () => window.clearInterval(intervalId);
  }, [rooms.length]);

  const activeRoom = rooms[activeIndex] || rooms[0] || null;

  return (
    <section className="live-program-panel">
      <div className="live-program-head">
        <div>
          <div className="live-program-kicker">
            Featured Live Rooms
          </div>
          <div className="live-program-title">今晚该点哪里，一眼就能知道</div>
          <div className="live-program-summary">
            一个给新确诊患者，一个给长期照护的家长，一个给关注临床试验机会的人。它们不是隐藏功能，而是首页最先能进入的真实入口。
          </div>
        </div>
        <div className="live-program-pills">
          {rooms.map((room, index) => (
            <button
              key={room.id}
              type="button"
              className={`live-program-pill ${index === activeIndex ? 'active' : ''}`}
              onClick={() => setActiveIndex(index)}
            >
              {room.title}
            </button>
          ))}
        </div>
      </div>

      <div className="live-program-stage">
        <div
          className="live-program-track"
          style={{ transform: `translateX(-${activeIndex * 100}%)` }}
        >
          {rooms.map((room) => (
            <article
              key={room.id}
              className="live-program-slide"
              style={{ '--room-accent': room.accent, '--room-bg': room.background }}
            >
              <div className="live-program-slide-copy">
                <div className="live-program-slide-kicker">
                  <span>{room.eyebrow}</span>
                  <strong>{room.schedule}</strong>
                </div>
                <h3>{room.title}</h3>
                <div className="live-program-host">{room.host}</div>
                <p>{room.focus}</p>
                <div className="live-program-blurb">{room.blurb}</div>
                <div className="live-program-actions">
                  <button
                    type="button"
                    className="live-program-cta"
                    onClick={() => onOpenRoom(room)}
                  >
                    {room.actionLabel}
                  </button>
                  <span className="live-program-hint">
                    {room.schedule.includes('今晚') ? '今晚推荐先点这里' : '这周值得提前留意'}
                  </span>
                </div>
              </div>

              <div className="live-program-slide-art">
                <div className={`live-program-poster poster-${room.id}`}>
                  <LiveProgramPosterIllustration roomId={room.id} />
                  <div className="live-program-poster-top">{room.eyebrow}</div>
                  <div className="live-program-poster-title">{room.title}</div>
                  <div className="live-program-poster-time">{room.schedule}</div>
                  <div className="live-program-poster-focus">{room.focus}</div>
                </div>
              </div>
            </article>
          ))}
        </div>
      </div>

      <div className="live-program-rail">
        {rooms.map((room, index) => (
          <button
            key={room.id}
            type="button"
            className={`live-program-rail-card ${index === activeIndex ? 'active' : ''}`}
            onClick={() => setActiveIndex(index)}
            style={{ '--room-accent': room.accent }}
          >
            <span className="live-program-rail-dot" />
            <div className="live-program-rail-copy">
              <strong>{room.title}</strong>
              <span>{room.schedule} · {room.host}</span>
            </div>
          </button>
        ))}
      </div>

      {activeRoom && (
        <div className="live-program-progress">
          <span>{activeIndex + 1} / {rooms.length}</span>
          <span>{activeRoom.schedule} · {activeRoom.title}</span>
        </div>
      )}
    </section>
  );
}

function ToyIllustration({ animal, tone }) {
  const earStyle = animal === 'rabbit'
    ? { width: 18, height: 38, borderRadius: 999 }
    : { width: 26, height: 26, borderRadius: '50%' };
  const leftEarTransform = animal === 'fox' ? 'rotate(-22deg)' : 'rotate(-10deg)';
  const rightEarTransform = animal === 'fox' ? 'rotate(22deg)' : 'rotate(10deg)';

  return (
    <div style={{ position: 'relative', width: 110, height: 110 }}>
      <span style={{
        position: 'absolute',
        left: 18,
        top: animal === 'rabbit' ? 4 : 12,
        background: tone,
        ...earStyle,
        transform: leftEarTransform,
      }} />
      <span style={{
        position: 'absolute',
        right: 18,
        top: animal === 'rabbit' ? 4 : 12,
        background: tone,
        ...earStyle,
        transform: rightEarTransform,
      }} />
      <div style={{
        position: 'absolute',
        inset: 18,
        borderRadius: '46% 46% 42% 42%',
        background: `linear-gradient(180deg, ${tone} 0%, color-mix(in srgb, ${tone} 78%, white) 100%)`,
        boxShadow: `0 18px 34px ${tone}33`,
      }}>
        <span style={{
          position: 'absolute',
          left: '50%',
          top: '50%',
          width: 56,
          height: 40,
          borderRadius: 999,
          transform: 'translate(-50%, -18%)',
          background: 'rgba(255,255,255,0.74)',
        }} />
        <span style={{
          position: 'absolute',
          left: 34,
          top: 36,
          width: 8,
          height: 8,
          borderRadius: '50%',
          background: '#0C1831',
        }} />
        <span style={{
          position: 'absolute',
          right: 34,
          top: 36,
          width: 8,
          height: 8,
          borderRadius: '50%',
          background: '#0C1831',
        }} />
        <span style={{
          position: 'absolute',
          left: '50%',
          top: 50,
          width: 10,
          height: 10,
          borderRadius: '50%',
          transform: 'translateX(-50%)',
          background: '#0C1831',
        }} />
      </div>
    </div>
  );
}

function CompanionHardwarePanel({ onOpenToyProgram, onOpenVoiceFollowup }) {
  return (
    <section style={{
      ...cardStyle({
        padding: 24,
        marginTop: 18,
        background: 'linear-gradient(180deg, rgba(255, 248, 239, 0.98) 0%, rgba(244, 253, 255, 0.96) 100%)',
      }),
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', gap: 16, alignItems: 'center', flexWrap: 'wrap' }}>
        <div>
          <div style={{ fontSize: 12, letterSpacing: '0.08em', textTransform: 'uppercase', color: '#FF7A59', fontWeight: 700 }}>
            Companion Hardware
          </div>
          <div style={{ fontSize: 24, fontWeight: 800, color: '#0C1831', marginTop: 8 }}>
            把陪伴玩偶和语音随访设备一起放进首页，让孩子先感到温暖，再开始沟通
          </div>
          <div style={{ fontSize: 14, color: '#44506A', lineHeight: 1.8, marginTop: 10, maxWidth: 820 }}>
            玩偶不是周边摆设，而是孩子与平台建立关系的第一步；语音设备也不是冷冰冰的硬件，而是把病愈随访、情绪表达和家庭沟通接进日常生活的入口。
          </div>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: 18, marginTop: 18 }}>
        <div style={{
          borderRadius: 28,
          padding: 20,
          background: 'rgba(255,255,255,0.72)',
          border: '1px solid rgba(12,24,49,0.08)',
        }}>
          <div style={{ fontSize: 12, letterSpacing: '0.08em', textTransform: 'uppercase', color: '#0DBF9B', fontWeight: 700 }}>
            陪伴玩偶
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(210px, 1fr))', gap: 16, marginTop: 16 }}>
            {COMPANION_TOYS.map((toy) => (
              <div
                key={toy.id}
                style={{
                  padding: 18,
                  borderRadius: 24,
                  background: 'rgba(255,255,255,0.84)',
                  border: `1px solid ${toy.tone}22`,
                  boxShadow: `0 16px 30px ${toy.tone}18`,
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'center' }}>
                  <ToyIllustration animal={toy.animal} tone={toy.tone} />
                </div>
                <div style={{ fontSize: 18, fontWeight: 800, color: '#0C1831', marginTop: 8, textAlign: 'center' }}>
                  {toy.name}
                </div>
                <div style={{ fontSize: 13, color: '#44506A', lineHeight: 1.75, marginTop: 8, textAlign: 'center' }}>
                  {toy.purpose}
                </div>
                <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginTop: 12, justifyContent: 'center' }}>
                  {toy.features.map((feature) => (
                    <span
                      key={feature}
                      style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        padding: '6px 10px',
                        borderRadius: 999,
                        background: 'rgba(255,255,255,0.86)',
                        border: '1px solid rgba(12,24,49,0.08)',
                        fontSize: 12,
                        color: '#44506A',
                      }}
                    >
                      {feature}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
          <button type="button" onClick={onOpenToyProgram} style={{ ...softButtonStyle('primary'), marginTop: 18 }}>
            查看陪伴玩偶如何接入长期随访
          </button>
        </div>

        <div style={{
          borderRadius: 28,
          padding: 20,
          background: 'linear-gradient(180deg, rgba(12,24,49,0.94) 0%, rgba(33,62,108,0.9) 100%)',
          color: '#fff',
        }}>
          <div style={{ fontSize: 12, letterSpacing: '0.08em', textTransform: 'uppercase', opacity: 0.82, fontWeight: 700 }}>
            语音随访设备
          </div>
          <div style={{ fontSize: 22, fontWeight: 800, lineHeight: 1.15, marginTop: 10 }}>
            儿童、大人和家庭都可以接入一个随时能说话的病愈随访入口
          </div>
          <div style={{ display: 'grid', gap: 14, marginTop: 16 }}>
            {FOLLOWUP_DEVICES.map((device) => (
              <div
                key={device.id}
                style={{
                  padding: 16,
                  borderRadius: 22,
                  background: 'rgba(255,255,255,0.1)',
                  border: '1px solid rgba(255,255,255,0.12)',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, alignItems: 'flex-start' }}>
                  <div>
                    <div style={{ fontSize: 17, fontWeight: 800 }}>{device.name}</div>
                    <div style={{ fontSize: 13, color: 'rgba(255,255,255,0.8)', lineHeight: 1.75, marginTop: 6 }}>
                      {device.summary}
                    </div>
                  </div>
                  <span style={{
                    width: 12,
                    height: 12,
                    borderRadius: '50%',
                    background: device.tone,
                    boxShadow: `0 0 0 8px ${device.tone}22`,
                    flexShrink: 0,
                    marginTop: 4,
                  }} />
                </div>
                <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginTop: 12 }}>
                  {device.points.map((point) => (
                    <span
                      key={point}
                      style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        padding: '6px 10px',
                        borderRadius: 999,
                        background: 'rgba(255,255,255,0.14)',
                        fontSize: 12,
                        color: 'rgba(255,255,255,0.88)',
                      }}
                    >
                      {point}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
          <button type="button" onClick={onOpenVoiceFollowup} style={{ ...softButtonStyle('ghost'), marginTop: 18, background: 'rgba(255,255,255,0.88)' }}>
            查看语音随访接入方式
          </button>
        </div>
      </div>
    </section>
  );
}


function SecondMeStatusPanel({
  secondMeState,
  secondMeStatus,
  secondMeDisplayName,
  secondMeMessage,
  secondMeTone,
  canConnectSecondMe,
  connectButtonLabel,
  myAvatar,
  syncingSummary,
  summarySyncMeta,
  onConnect,
  onDisconnect,
  onSync,
}) {
  const grantedScopes = secondMeStatus?.granted_scopes || [];

  return (
    <section style={{
      ...cardStyle({ padding: 22 }),
      display: 'grid',
      gridTemplateColumns: 'minmax(0, 1fr) minmax(280px, 0.76fr)',
      gap: 18,
    }}>
      <div>
        <div style={{ fontSize: 12, letterSpacing: '0.08em', textTransform: 'uppercase', color: '#0DBF9B', fontWeight: 700 }}>
          SecondMe OAuth
        </div>
        <div style={{ fontSize: 26, fontWeight: 800, marginTop: 8, color: '#0C1831', lineHeight: 1.1 }}>
          {secondMeState === 'connected' ? `已连接 ${secondMeDisplayName}` : '先连上 SecondMe，再让病友互动真正发生'}
        </div>
        <div style={{ fontSize: 14, color: '#44506A', lineHeight: 1.8, marginTop: 10 }}>
          {secondMeState === 'connected'
            ? '当前可以把患者摘要同步给 SecondMe，并让分身在社群里用同一份记忆发起第一轮连接。'
            : '授权完成后，患者摘要、分身人格和病友圈互动会进入同一条链路。'}
        </div>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginTop: 14 }}>
          {(grantedScopes.length > 0 ? grantedScopes : secondMeStatus?.required_scopes || []).map((scope) => (
            <span key={scope} style={{
              display: 'inline-flex',
              alignItems: 'center',
              padding: '7px 10px',
              borderRadius: 999,
              background: grantedScopes.includes(scope) ? 'rgba(13,191,155,0.12)' : 'rgba(12,24,49,0.05)',
              color: grantedScopes.includes(scope) ? '#08886F' : '#44506A',
              fontSize: 12,
              fontWeight: 700,
            }}>
              {scope}
            </span>
          ))}
        </div>
        <div style={{ fontSize: 12, color: '#7D879A', marginTop: 12, lineHeight: 1.7 }}>
          redirect_uri: {secondMeStatus?.redirect_uri || 'http://localhost:8001/api/v1/secondme/oauth/callback'}
          {summarySyncMeta?.syncedAt && (
            <span> · 最近同步：{new Date(summarySyncMeta.syncedAt).toLocaleString('zh-CN')}</span>
          )}
        </div>

        {secondMeMessage && (
          <div style={{
            marginTop: 14, padding: '12px 14px', borderRadius: 18, fontSize: 13, lineHeight: 1.7,
            ...toneStyle(secondMeTone),
          }}>
            {secondMeMessage}
          </div>
        )}
      </div>

      <div style={{
        borderRadius: 22,
        padding: 18,
        background: 'rgba(12,24,49,0.04)',
        border: '1px solid rgba(12,24,49,0.06)',
      }}>
        <div style={{ fontSize: 16, fontWeight: 800, color: '#0C1831' }}>连接概览</div>
        <div style={{ display: 'grid', gap: 12, marginTop: 14 }}>
          {[
            { label: '账号状态', value: secondMeState === 'connected' ? '已连接' : '未连接' },
            { label: '记忆同步', value: summarySyncMeta?.noteId ? '已完成' : '未同步' },
            { label: '分身状态', value: myAvatar ? '已创建' : '未创建' },
            { label: 'Token 到期', value: secondMeStatus?.expires_at ? new Date(secondMeStatus.expires_at).toLocaleDateString('zh-CN') : '待授权' },
          ].map((item) => (
            <div key={item.label} style={{
              display: 'flex', justifyContent: 'space-between', gap: 12, paddingBottom: 10,
              borderBottom: '1px solid rgba(12,24,49,0.08)',
            }}>
              <span style={{ color: '#7D879A', fontSize: 13 }}>{item.label}</span>
              <strong style={{ color: '#0C1831', fontSize: 14 }}>{item.value}</strong>
            </div>
          ))}
        </div>
        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginTop: 16 }}>
          {secondMeState === 'connected' ? (
            <>
              <button type="button" onClick={onDisconnect} style={softButtonStyle('ghost')}>
                断开授权
              </button>
              {myAvatar && (
                <button type="button" onClick={onSync} disabled={syncingSummary} style={softButtonStyle('primary', syncingSummary)}>
                  {syncingSummary ? '同步中...' : '同步患者摘要'}
                </button>
              )}
            </>
          ) : (
            <button type="button" onClick={onConnect} disabled={!canConnectSecondMe} style={softButtonStyle('primary', !canConnectSecondMe)}>
              {connectButtonLabel}
            </button>
          )}
        </div>
      </div>
    </section>
  );
}


function DiseaseStoryPanel({ story, loading, recommendedCircles, onSelectCommunity }) {
  if (!loading && !story && recommendedCircles.length === 0) {
    return null;
  }

  const signals = story?.research_signals || [];
  const disease = story?.disease || {};
  const carePoints = story?.care_points || [];
  const symptomList = disease?.symptoms || [];
  const hospitals = disease?.specialist_hospitals || [];
  const knowledgeCounts = story?.knowledge_map?.related
    ? [
        { label: '关联基因', value: story.knowledge_map.related.genes?.length || 0 },
        { label: '关联药物', value: story.knowledge_map.related.drugs?.length || 0 },
        { label: '相关表型', value: story.knowledge_map.related.phenotypes?.length || 0 },
      ]
    : [];

  return (
    <section style={{
      ...cardStyle({ padding: 24 }),
      display: 'grid',
      gridTemplateColumns: 'minmax(0, 1.05fr) minmax(320px, 0.95fr)',
      gap: 18,
    }}>
      <div>
        <div style={{ fontSize: 12, letterSpacing: '0.08em', textTransform: 'uppercase', color: '#FF7A59', fontWeight: 700 }}>
          Disease spotlight
        </div>
        <div style={{ fontSize: 26, fontWeight: 800, color: '#0C1831', marginTop: 8 }}>
          {loading ? '正在整理疾病介绍…' : disease.name || '当前病种介绍'}
        </div>
        {disease.category && (
          <div style={{ fontSize: 13, color: '#0DBF9B', marginTop: 6 }}>{disease.category}</div>
        )}
        <p style={{ fontSize: 14, color: '#44506A', lineHeight: 1.8, marginTop: 12 }}>
          {loading ? '正在从知识库整理疾病背景、常见症状和建议关注点。' : disease.treatment_summary || '知识库暂无更详细的治疗摘要。'}
        </p>

        {signals.length > 0 && (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: 12, marginTop: 16 }}>
            {signals.map((item) => (
              <div key={item.label} style={{
                padding: 14,
                borderRadius: 18,
                background: 'rgba(12,24,49,0.04)',
                border: '1px solid rgba(12,24,49,0.06)',
              }}>
                <div style={{ fontSize: 12, color: '#7D879A' }}>{item.label}</div>
                <div style={{ fontSize: 18, fontWeight: 800, color: '#0C1831', marginTop: 8 }}>{item.value}</div>
              </div>
            ))}
          </div>
        )}

        {symptomList.length > 0 && (
          <div style={{ marginTop: 18 }}>
            <div style={{ fontSize: 13, fontWeight: 700, color: '#0C1831' }}>常见症状</div>
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginTop: 10 }}>
              {symptomList.map((item) => (
                <span key={item} style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  padding: '8px 12px',
                  borderRadius: 999,
                  background: 'rgba(255,255,255,0.86)',
                  border: '1px solid rgba(12,24,49,0.08)',
                  fontSize: 12,
                  color: '#44506A',
                }}>
                  {item}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>

      <div style={{ display: 'grid', gap: 16 }}>
        <div style={{
          borderRadius: 22,
          padding: 18,
          background: 'rgba(12,24,49,0.04)',
          border: '1px solid rgba(12,24,49,0.06)',
        }}>
          <div style={{ fontSize: 16, fontWeight: 800, color: '#0C1831' }}>患者最值得先问的事</div>
          <div style={{ display: 'grid', gap: 10, marginTop: 14 }}>
            {carePoints.map((item) => (
              <div key={item} style={{ display: 'grid', gridTemplateColumns: '10px minmax(0, 1fr)', gap: 10, alignItems: 'flex-start' }}>
                <span style={{ width: 10, height: 10, borderRadius: '50%', background: '#FF7A59', marginTop: 7 }} />
                <span style={{ color: '#44506A', lineHeight: 1.7 }}>{item}</span>
              </div>
            ))}
          </div>
        </div>

        {knowledgeCounts.length > 0 && (
          <div style={{
            borderRadius: 22,
            padding: 18,
            background: 'rgba(12,24,49,0.04)',
            border: '1px solid rgba(12,24,49,0.06)',
          }}>
            <div style={{ fontSize: 16, fontWeight: 800, color: '#0C1831' }}>图谱信号</div>
            <div style={{ display: 'grid', gap: 10, marginTop: 14 }}>
              {knowledgeCounts.map((item) => (
                <div key={item.label} style={{ display: 'flex', justifyContent: 'space-between', gap: 12 }}>
                  <span style={{ color: '#7D879A', fontSize: 13 }}>{item.label}</span>
                  <strong style={{ color: '#0C1831' }}>{item.value}</strong>
                </div>
              ))}
            </div>
          </div>
        )}

        {(recommendedCircles.length > 0 || hospitals.length > 0) && (
          <div style={{
            borderRadius: 22,
            padding: 18,
            background: 'rgba(12,24,49,0.04)',
            border: '1px solid rgba(12,24,49,0.06)',
          }}>
            <div style={{ fontSize: 16, fontWeight: 800, color: '#0C1831' }}>病友圈与就诊提示</div>
            {recommendedCircles.length > 0 && (
              <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginTop: 12 }}>
                {recommendedCircles.slice(0, 4).map((item) => (
                  <button key={item.id} type="button" onClick={() => onSelectCommunity(item.name)} style={softButtonStyle('ghost')}>
                    {item.name}
                  </button>
                ))}
              </div>
            )}
            {hospitals.length > 0 && (
              <div style={{ marginTop: 14, display: 'grid', gap: 8 }}>
                {hospitals.map((item) => (
                  <div key={item} style={{ color: '#44506A', lineHeight: 1.7, fontSize: 13 }}>
                    {item}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </section>
  );
}


function CreateAvatarModal({ secondMeStatus, onClose, onSuccess }) {
  const [form, setForm] = useState({
    nickname: secondMeStatus?.user?.display_name || secondMeStatus?.user?.nickname || '',
    disease_type: '',
    age: '',
    symptoms: '',
    diagnosis: '',
    treatment_history: '',
  });
  const [loading, setLoading] = useState(false);
  const [lookupLoading, setLookupLoading] = useState(false);
  const [diseasePreview, setDiseasePreview] = useState(null);
  const [circlePreview, setCirclePreview] = useState([]);
  const [error, setError] = useState('');

  useEffect(() => {
    if ((secondMeStatus?.user?.display_name || secondMeStatus?.user?.nickname) && !form.nickname) {
      setForm((current) => ({
        ...current,
        nickname: secondMeStatus.user.display_name || secondMeStatus.user.nickname,
      }));
    }
  }, [secondMeStatus?.user?.display_name, secondMeStatus?.user?.nickname]);

  useEffect(() => {
    const disease = form.disease_type.trim();
    if (!disease) {
      setDiseasePreview(null);
      setCirclePreview([]);
      return undefined;
    }

    const timer = window.setTimeout(async () => {
      setLookupLoading(true);
      try {
        const [research, recommendations] = await Promise.all([
          fetchJson('/api/v1/platform/research', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ disease_name: disease }),
          }).catch(() => null),
          fetchJson(`/api/v1/community/recommend/${encodeURIComponent(disease)}`).catch(() => null),
        ]);
        setDiseasePreview(research?.ok ? research : null);
        setCirclePreview(recommendations?.ok ? recommendations.recommendations : []);
      } catch (previewError) {
        console.error(previewError);
        setDiseasePreview(null);
        setCirclePreview([]);
      } finally {
        setLookupLoading(false);
      }
    }, 320);

    return () => window.clearTimeout(timer);
  }, [form.disease_type]);

  const handleSubmit = async () => {
    if (!form.nickname || !form.disease_type) return;
    setLoading(true);
    setError('');
    try {
      const data = await fetchJson('/api/v1/community/avatar/create', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form),
      });
      if (data.ok) {
        await onSuccess({
          avatar: data.avatar,
          profileSource: form,
          joinedCommunities: data.joined_communities || circlePreview.map((item) => item.name),
        });
      }
    } catch (error) {
      console.error(error);
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };

  const fields = [
    { key: 'nickname', label: '昵称', placeholder: '例如：小米妈妈' },
    { key: 'disease_type', label: '疾病类型', placeholder: '例如：戈谢病' },
    { key: 'age', label: '年龄', placeholder: '选填', type: 'number' },
    { key: 'symptoms', label: '主要症状', placeholder: '选填，例如 脾大、骨痛、贫血' },
    { key: 'diagnosis', label: '诊断结果', placeholder: '选填' },
    { key: 'treatment_history', label: '治疗经历', placeholder: '选填，例如 酶替代治疗 18 个月' },
  ];

  return (
    <ModalFrame
      title="创建你的 SecondMe 分身"
      subtitle="把病程、症状和当前阶段整理成可用于社群互动的患者身份卡"
      onClose={onClose}
      maxWidth={940}
    >
      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 1fr) minmax(300px, 0.9fr)', gap: 18 }}>
        <div>
          <div style={{
            padding: 14,
            borderRadius: 18,
            ...toneStyle(secondMeStatus?.state === 'connected' ? 'success' : 'warning'),
            fontSize: 13,
            lineHeight: 1.7,
            marginBottom: 14,
          }}>
            {secondMeStatus?.state === 'connected'
              ? `已连接 ${secondMeStatus.user?.display_name || secondMeStatus.user?.nickname || 'SecondMe 用户'}，创建后会自动同步患者摘要。`
              : '当前未连接 SecondMe。你仍可先创建本地分身，但患者摘要不会自动写入 SecondMe note。'}
          </div>

          <div style={{ display: 'grid', gap: 12 }}>
            {fields.map((field) => (
              <label key={field.key} style={{ display: 'grid', gap: 6 }}>
                <span style={{ fontSize: 13, color: '#44506A', fontWeight: 700 }}>{field.label}</span>
                {field.key === 'treatment_history' ? (
                  <textarea
                    rows={3}
                    value={form[field.key]}
                    onChange={(event) => setForm({ ...form, [field.key]: event.target.value })}
                    placeholder={field.placeholder}
                    style={inputStyle(true)}
                  />
                ) : (
                  <input
                    type={field.type || 'text'}
                    value={form[field.key]}
                    onChange={(event) => setForm({ ...form, [field.key]: event.target.value })}
                    placeholder={field.placeholder}
                    style={inputStyle()}
                  />
                )}
              </label>
            ))}
          </div>

          {error && (
            <div style={{ marginTop: 14, padding: '12px 14px', borderRadius: 18, ...toneStyle('error'), fontSize: 13 }}>
              {error}
            </div>
          )}

          <div style={{ display: 'flex', gap: 10, marginTop: 18 }}>
            <button type="button" onClick={onClose} style={{ ...softButtonStyle('ghost'), flex: 1 }}>取消</button>
            <button type="button" onClick={handleSubmit} disabled={loading} style={{ ...softButtonStyle('primary', loading), flex: 2 }}>
              {loading ? '创建中...' : '创建分身'}
            </button>
          </div>
        </div>

        <div style={{
          borderRadius: 22,
          padding: 18,
          background: 'rgba(12,24,49,0.04)',
          border: '1px solid rgba(12,24,49,0.06)',
        }}>
          <div style={{ fontSize: 12, letterSpacing: '0.08em', textTransform: 'uppercase', color: '#0DBF9B', fontWeight: 700 }}>
            Disease preview
          </div>
          <div style={{ fontSize: 22, fontWeight: 800, color: '#0C1831', marginTop: 10 }}>
            {form.disease_type || '先填写疾病类型'}
          </div>
          <p style={{ fontSize: 13, color: '#44506A', lineHeight: 1.8, marginTop: 10 }}>
            {lookupLoading
              ? '正在整理疾病背景、常见症状和推荐病友圈…'
              : diseasePreview?.disease?.treatment_summary || '填写疾病名称后，这里会出现疾病介绍、常见信号和推荐病友圈。'}
          </p>

          {diseasePreview?.research_signals?.length > 0 && (
            <div style={{ display: 'grid', gap: 10, marginTop: 14 }}>
              {diseasePreview.research_signals.map((item) => (
                <div key={item.label} style={{ display: 'flex', justifyContent: 'space-between', gap: 12 }}>
                  <span style={{ color: '#7D879A', fontSize: 13 }}>{item.label}</span>
                  <strong style={{ color: '#0C1831' }}>{item.value}</strong>
                </div>
              ))}
            </div>
          )}

          {diseasePreview?.disease?.symptoms?.length > 0 && (
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginTop: 14 }}>
              {diseasePreview.disease.symptoms.slice(0, 6).map((item) => (
                <span key={item} style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  padding: '8px 12px',
                  borderRadius: 999,
                  background: 'rgba(255,255,255,0.86)',
                  border: '1px solid rgba(12,24,49,0.08)',
                  color: '#44506A',
                  fontSize: 12,
                }}>
                  {item}
                </span>
              ))}
            </div>
          )}

          {circlePreview.length > 0 && (
            <div style={{ marginTop: 16 }}>
              <div style={{ fontSize: 13, fontWeight: 700, color: '#0C1831' }}>预计加入的病友圈</div>
              <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginTop: 10 }}>
                {circlePreview.slice(0, 4).map((item) => (
                  <span key={item.id} style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    padding: '8px 12px',
                    borderRadius: 999,
                    background: 'rgba(13,191,155,0.12)',
                    color: '#08886F',
                    fontSize: 12,
                    fontWeight: 700,
                  }}>
                    {item.name}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </ModalFrame>
  );
}


function CreatePostModal({ communityId, avatarId, nickname, initialContent, initialPostType, linkedProfile, onClose, onSuccess }) {
  const [content, setContent] = useState(initialContent || '');
  const [postType, setPostType] = useState(initialPostType || '经验分享');
  const [loading, setLoading] = useState(false);

  const handlePost = async () => {
    if (!content.trim()) return;
    setLoading(true);
    try {
      const data = await fetchJson('/api/v1/community/post', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          community_id: communityId,
          avatar_id: avatarId,
          nickname,
          content,
          post_type: postType,
        }),
      });
      if (data.ok) onSuccess();
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <ModalFrame title="发布你的第一条社群动态" subtitle="模式已经预选好，你可以继续润色，再把这条内容真正发出去" onClose={onClose}>
      {linkedProfile && (
        <div style={{
          marginBottom: 14,
          padding: 12,
          borderRadius: 16,
          background: 'rgba(12,24,49,0.04)',
          border: '1px solid rgba(12,24,49,0.06)',
          fontSize: 13,
          color: '#44506A',
          lineHeight: 1.7,
        }}>
          这条动态已参考已登录的 SecondMe 资料生成。当前账号：{linkedProfile.display_name || linkedProfile.nickname || 'SecondMe 用户'}
        </div>
      )}
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginBottom: 14 }}>
        {FIRST_POST_MODES.map((mode) => (
          <button
            key={mode.key}
            type="button"
            onClick={() => setPostType(mode.key)}
            style={{
              padding: '8px 12px',
              borderRadius: 999,
              cursor: 'pointer',
              border: postType === mode.key ? `1px solid ${mode.accent}` : '1px solid rgba(12,24,49,0.08)',
              background: postType === mode.key ? mode.background : 'rgba(255,255,255,0.82)',
              color: postType === mode.key ? mode.accent : '#44506A',
              fontWeight: 700,
            }}
          >
            {mode.key}
          </button>
        ))}
      </div>
      <textarea
        rows={5}
        value={content}
        onChange={(event) => setContent(event.target.value)}
        placeholder="例如：孩子刚确诊，我们最想知道第一轮该补哪些检查、去哪家医院比较合适。"
        style={inputStyle(true)}
      />
      <div style={{ display: 'flex', gap: 10, marginTop: 18 }}>
        <button type="button" onClick={onClose} style={{ ...softButtonStyle('ghost'), flex: 1 }}>取消</button>
        <button type="button" onClick={handlePost} disabled={loading} style={{ ...softButtonStyle('primary', loading), flex: 2 }}>
          {loading ? '发布中...' : '发布帖子'}
        </button>
      </div>
    </ModalFrame>
  );
}


function ModalFrame({ title, subtitle, onClose, children, maxWidth = 520 }) {
  return (
    <div style={{
      position: 'fixed', inset: 0, zIndex: 1000, background: 'rgba(11,20,37,0.48)',
      display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 16,
    }}>
      <div style={{
        width: '100%', maxWidth, borderRadius: 28, padding: 24,
        background: 'rgba(255,253,249,0.96)', border: '1px solid rgba(255,255,255,0.4)',
        boxShadow: '0 32px 90px rgba(17,28,56,0.18)', backdropFilter: 'blur(18px)',
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', gap: 16, alignItems: 'flex-start', marginBottom: 16 }}>
          <div>
            <div style={{ fontSize: 24, fontWeight: 800, color: '#0C1831', lineHeight: 1.15 }}>{title}</div>
            <div style={{ fontSize: 13, color: '#44506A', marginTop: 8, lineHeight: 1.7 }}>{subtitle}</div>
          </div>
          <button type="button" onClick={onClose} style={softButtonStyle('ghost')}>关闭</button>
        </div>
        {children}
      </div>
    </div>
  );
}


function inputStyle(multiline = false) {
  return {
    width: '100%',
    border: '1px solid rgba(12,24,49,0.12)',
    borderRadius: 18,
    background: 'rgba(255,255,255,0.86)',
    padding: '14px 16px',
    color: '#0C1831',
    outline: 'none',
    resize: multiline ? 'vertical' : 'none',
    fontFamily: 'inherit',
    fontSize: 14,
  };
}
