import React, { useEffect, useRef, useState } from 'react';
import './App.css';
import DeepRarePanel from './components/DeepRarePanel';
import CommunityPanel from './components/CommunityPanel';
import DoctorPanel from './components/DoctorPanel';

const API_BASE = import.meta.env.VITE_API_URL || '';
const REGISTRY_STORAGE_KEY = 'medichat_registry_id';
const PREFILLED_DISEASE_STORAGE_KEY = 'medichat_selected_disease';

const COMMON_DISEASE_LIBRARY = [
  { name: '戈谢病', gene: 'GBA', category: '溶酶体病', summary: '常见线索是脾大、骨痛、贫血。' },
  { name: '法布雷病', gene: 'GLA', category: '溶酶体病', summary: '肢端疼痛、肾脏和心脏受累较常见。' },
  { name: '脊髓性肌萎缩症', gene: 'SMN1', category: '神经肌肉病', summary: '肌无力、发育迟缓和运动功能下降。' },
  { name: '重症肌无力', gene: 'CHRNE', category: '神经肌肉病', summary: '疲劳性无力、眼睑下垂和吞咽困难。' },
  { name: '杜氏肌营养不良', gene: 'DMD', category: '神经肌肉病', summary: '儿童期进行性肌无力和步态异常。' },
  { name: '成骨不全症', gene: 'COL1A1', category: '骨骼系统', summary: '反复骨折、蓝巩膜、骨量降低。' },
];

const COMMON_DRUG_SPOTLIGHTS = [
  { disease: '戈谢病', drugs: ['Imiglucerase', 'Eliglustat'], tag: '酶替代 / 底物减少' },
  { disease: '法布雷病', drugs: ['Agalsidase beta', 'Migalastat'], tag: '酶替代 / 分子伴侣' },
  { disease: '脊髓性肌萎缩症', drugs: ['Nusinersen', 'Risdiplam'], tag: 'SMN 通路调节' },
  { disease: '杜氏肌营养不良', drugs: ['Ataluren', 'Exon-skipping 方案'], tag: '精准突变策略' },
  { disease: '重症肌无力', drugs: ['Pyridostigmine', 'Eculizumab'], tag: '症状控制 / 补体通路' },
  { disease: '成骨不全症', drugs: ['Bisphosphonates', 'Teriparatide'], tag: '骨代谢调节' },
];

const PAGE_GUIDE = {
  community: {
    title: '互助社群',
    hint: '欢迎房、病友圈、AI 分身和持续互动都从这里开始。',
    tags: ['欢迎房', '病友圈', 'AI 分身'],
  },
  hub: {
    title: '患者中枢',
    hint: '用一页看清患者旅程、能力地图和今天最值得打开的入口。',
    tags: ['旅程总览', '能力地图', '今日入口'],
  },
  deeprare: {
    title: 'DeepRare 诊断',
    hint: '把症状快速整理成候选诊断、检查建议和下一步动作。',
    tags: ['候选诊断', '检查建议', '推理链'],
  },
  doctor: {
    title: '医生助手',
    hint: '帮助医生和患者把病史、风险点和随访问题说清楚。',
    tags: ['医生沟通', '风险提示', '随访提问'],
  },
  'ai-chat': {
    title: 'AI 陪诊',
    hint: '更适合把复杂病情用自然语言讲清楚，再整理成下一步问题。',
    tags: ['自然语言', '问诊梳理', '陪伴对话'],
  },
  'symptom-check': {
    title: '症状筛查',
    hint: '快速输入症状，先拿到一个结构化初筛结果。',
    tags: ['症状输入', '结构化初筛', '快速开始'],
  },
  'genomic-hub': {
    title: '基因与登记',
    hint: '把基因线索、Phenopacket 和患者登记放到同一条链路。',
    tags: ['基因分诊', 'Phenopacket', '登记入库'],
  },
  'care-loop': {
    title: '长期管理',
    hint: '把陪伴、随访、病友支持和时间线真正闭合起来。',
    tags: ['时间线', '随访', '陪伴闭环'],
  },
  'scientific-skills': {
    title: '科研加速',
    hint: '查看科研执行层是否就绪，并把重型工作流接入平台。',
    tags: ['科研 Runtime', '工作流', '执行层'],
  },
  'disease-research': {
    title: '疾病研究',
    hint: '一页看疾病介绍、关键基因、医院线索和患者常见问题。',
    tags: ['疾病介绍', '关键基因', '医院线索'],
  },
  'drug-research': {
    title: '药物线索',
    hint: '把患者最关心的药物、研究动态和结构线索直接前置。',
    tags: ['药物线索', '研究动态', '虚拟筛选'],
  },
  'platform-ops': {
    title: '治理评估',
    hint: '查看控制面、分身 runtime 和平台治理边界。',
    tags: ['控制面', 'Runtime', '治理边界'],
  },
};

function getStoredRegistryId() {
  if (typeof window === 'undefined') return '';
  return window.localStorage.getItem(REGISTRY_STORAGE_KEY) || '';
}

function storeRegistryId(registryId) {
  if (typeof window === 'undefined' || !registryId) return;
  window.localStorage.setItem(REGISTRY_STORAGE_KEY, registryId);
}

const Icons = {
  spark: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round">
      <path d="M12 3l1.8 4.7L18.5 9l-4.7 1.8L12 15.5l-1.8-4.7L5.5 9l4.7-1.3L12 3Z" />
      <path d="M19 16l.8 2.2L22 19l-2.2.8L19 22l-.8-2.2L16 19l2.2-.8L19 16Z" />
    </svg>
  ),
  dna: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round">
      <path d="M3 16c6-5 12 1 18-4M3 8c6 5 12-1 18 4M7 4v4M17 4v4M7 16v4M17 16v4" />
    </svg>
  ),
  brain: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round">
      <path d="M12 2a4.5 4.5 0 0 1 4.5 4.5c0 .7-.2 1.4-.5 2a4.4 4.4 0 0 1 2 3.7 4.8 4.8 0 0 1-3 4.4V22h-6v-5.4A4.8 4.8 0 0 1 6 12.2a4.4 4.4 0 0 1 2-3.7 4.8 4.8 0 0 1-.5-2A4.5 4.5 0 0 1 12 2Z" />
      <path d="M12 2v20" />
    </svg>
  ),
  users: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round">
      <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
      <circle cx="9" cy="7" r="4" />
      <path d="M23 21v-2a4 4 0 0 0-3-3.9" />
      <path d="M16 3.1a4 4 0 0 1 0 7.8" />
    </svg>
  ),
  search: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
      <circle cx="11" cy="11" r="8" />
      <path d="m21 21-4.3-4.3" />
    </svg>
  ),
  file: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round">
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8Z" />
      <path d="M14 2v6h6" />
      <path d="M8 13h8M8 17h6" />
    </svg>
  ),
  pill: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round">
      <path d="m10.5 20.5 10-10a5 5 0 0 0-7-7l-10 10a5 5 0 1 0 7 7Z" />
      <path d="m8.5 8.5 7 7" />
    </svg>
  ),
  chat: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round">
      <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2Z" />
    </svg>
  ),
  home: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round">
      <path d="m3 10 9-7 9 7" />
      <path d="M5 10v10h14V10" />
      <path d="M10 20v-6h4v6" />
    </svg>
  ),
  activity: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round">
      <path d="M22 12h-4l-3 8-6-16-3 8H2" />
    </svg>
  ),
  arrow: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
      <path d="M5 12h14" />
      <path d="m13 5 7 7-7 7" />
    </svg>
  ),
  menu: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
      <path d="M3 6h18M3 12h18M3 18h18" />
    </svg>
  ),
  close: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
      <path d="m18 6-12 12M6 6l12 12" />
    </svg>
  ),
  check: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
      <path d="m20 6-11 11-5-5" />
    </svg>
  ),
};

async function fetchJson(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, options);
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.detail || data.message || '请求失败');
  }
  return data;
}

function MultilineText({ text }) {
  if (!text) return null;
  return text.split('\n').map((line, index) => <p key={index}>{line || <br />}</p>);
}

function PageShowcaseArt({ scene, poster = {} }) {
  const bubbles = poster.bubbles || [];
  const stats = poster.stats || [];

  return (
    <div className={`page-showcase-stage scene-${scene}`}>
      <div className="page-showcase-illustration">
        <span className="page-showcase-cloud cloud-a" />
        <span className="page-showcase-cloud cloud-b" />
        <span className="page-showcase-orb orb-a" />
        <span className="page-showcase-orb orb-b" />
        <span className="page-showcase-ribbon ribbon-a" />
        <span className="page-showcase-ribbon ribbon-b" />
        <span className="page-showcase-buddy buddy-a" />
        <span className="page-showcase-buddy buddy-b" />
        <span className="page-showcase-device device-a" />
        <span className="page-showcase-spark spark-a" />
        <span className="page-showcase-spark spark-b" />
      </div>

      <div className="page-showcase-poster">
        <div className="page-showcase-poster-top">
          <span className="page-showcase-poster-kicker">{poster.kicker}</span>
          {poster.badge && <span className="page-showcase-poster-badge">{poster.badge}</span>}
        </div>
        <div className="page-showcase-poster-title">{poster.title}</div>
        {poster.summary && <p className="page-showcase-poster-summary">{poster.summary}</p>}
        {bubbles.length > 0 && (
          <div className="page-showcase-bubbles">
            {bubbles.map((bubble) => (
              <span key={bubble} className="page-showcase-bubble">
                {bubble}
              </span>
            ))}
          </div>
        )}
        {stats.length > 0 && (
          <div className="page-showcase-stat-grid">
            {stats.map((item) => (
              <div key={`${item.label}-${item.value}`} className="page-showcase-stat">
                <small>{item.label}</small>
                <strong>{item.value}</strong>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function PageShowcase({ scene, eyebrow, title, description, tags = [], actions = [], highlights = [], poster }) {
  return (
    <section className={`page-showcase scene-${scene}`}>
      <div className="page-showcase-copy">
        <div className="page-eyebrow">{eyebrow}</div>
        <h2>{title}</h2>
        <p>{description}</p>
        {actions.length > 0 && (
          <div className="page-showcase-actions">
            {actions.map((action) => {
              const Icon = Icons[action.icon] || Icons.spark;
              const buttonClassName = action.variant === 'ghost' ? 'ghost-btn' : 'primary-btn';
              return (
                <button key={action.label} type="button" className={buttonClassName} onClick={action.onClick}>
                  <Icon />
                  <span>{action.label}</span>
                </button>
              );
            })}
          </div>
        )}
        {tags.length > 0 && (
          <div className="page-showcase-tags">
            {tags.map((tag) => (
              <span key={tag} className="page-showcase-tag">{tag}</span>
            ))}
          </div>
        )}
      </div>

      <PageShowcaseArt scene={scene} poster={poster} />

      {highlights.length > 0 && (
        <div className="page-showcase-feature-grid">
          {highlights.map((item) => {
            const Icon = Icons[item.icon] || Icons.spark;
            return (
              <div key={item.title} className="page-showcase-feature-card">
                <div className="page-showcase-feature-icon">
                  <Icon />
                </div>
                <div>
                  <strong>{item.title}</strong>
                  <p>{item.text}</p>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </section>
  );
}

function PageTitleRail({ page, navItems, onNavigate }) {
  const activeGuide = PAGE_GUIDE[page] || PAGE_GUIDE.hub;

  return (
    <section className="page-title-rail">
      <div className="page-title-summary">
        <div className="page-title-kicker">患者快速入口</div>
        <div className="page-title-mainline">
          <h2>{activeGuide.title}</h2>
          <p>{activeGuide.hint}</p>
        </div>
        <div className="page-title-tags">
          {(activeGuide.tags || []).map((tag) => (
            <span key={tag}>{tag}</span>
          ))}
        </div>
      </div>

      <div className="page-title-track" role="navigation" aria-label="页面快速切换">
        {navItems.map((item) => {
          const Icon = Icons[item.icon];
          const guide = PAGE_GUIDE[item.id] || { title: item.label, hint: '' };
          return (
            <button
              key={item.id}
              type="button"
              className={`page-title-chip ${page === item.id ? 'active' : ''}`}
              onClick={() => onNavigate(item.id)}
              aria-current={page === item.id ? 'page' : undefined}
            >
              <div className="page-title-chip-icon">
                <Icon />
              </div>
              <div className="page-title-chip-copy">
                <strong>{guide.title}</strong>
                <span>{guide.hint}</span>
              </div>
            </button>
          );
        })}
      </div>
    </section>
  );
}

function HomePage({ onNavigate }) {
  const [overview, setOverview] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    let cancelled = false;
    fetchJson('/api/v1/platform/overview')
      .then((data) => {
        if (!cancelled) setOverview(data);
      })
      .catch((err) => {
        if (!cancelled) setError(err.message);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const stats = overview?.stats || [];
  const journeys = overview?.journeys || [];
  const modules = overview?.capability_modules || [];
  const communities = overview?.featured_communities || [];
  const posts = overview?.trending_posts || [];
  const careModes = overview?.care_modes || [];

  return (
    <div className="hub-page">
      <section className="hub-hero">
        <div className="hub-hero-copy">
          <div className="eyebrow">
            <Icons.spark />
            <span>{overview?.hero?.eyebrow || 'Rare disease patient operating system'}</span>
          </div>
          <h1>{overview?.hero?.title || '让患者愿意反复打开的罕见病平台'}</h1>
          <p className="hero-text">
            {overview?.hero?.subtitle || '把诊断、研究、SecondMe 分身和病友互助组织成一个持续陪伴的患者中枢。'}
          </p>
          <div className="hero-actions">
            <button className="primary-btn" onClick={() => onNavigate('deeprare')}>
              <Icons.brain />
              <span>{overview?.hero?.primary_cta?.label || '开始 DeepRare 诊断'}</span>
            </button>
            <button className="ghost-btn" onClick={() => onNavigate('community')}>
              <Icons.users />
              <span>{overview?.hero?.secondary_cta?.label || '进入互助社群'}</span>
            </button>
          </div>
          <div className="hero-modes">
            {careModes.map((mode) => (
              <span key={mode} className="mode-pill">{mode}</span>
            ))}
          </div>
        </div>

        <div className="hero-board">
          <div className="hero-board-panel">
            <div className="board-kicker">患者工作台</div>
            <div className="board-title">从“我哪里不对劲”到“我该找谁、问什么、怎么坚持下去”</div>
            <div className="board-list">
              {[
                '自由文本症状输入 -> HPO 表型标准化',
                'DeepRare 给出差异诊断和下一步检查',
                '基因分诊 + 患者登记 + Phenopacket 一键整理',
                'SecondMe 分身进入病友圈、建立支持连接',
                '研究中心持续追踪药物网络、虚拟筛选和用药线索',
              ].map((item) => (
                <div key={item} className="board-item">
                  <Icons.check />
                  <span>{item}</span>
                </div>
              ))}
            </div>
          </div>
          <div className="hero-board-glow" />
        </div>
      </section>

      <section className="metric-ribbon">
        {stats.map((stat) => (
          <div key={stat.label} className="metric-block">
            <span className="metric-value">{stat.value}</span>
            <span className="metric-label">{stat.label}</span>
          </div>
        ))}
      </section>

      <section className="story-grid">
        <div className="story-panel">
          <div className="section-head">
            <span>患者旅程</span>
            <button type="button" onClick={() => onNavigate('symptom-check')}>
              立即开始
            </button>
          </div>
          <div className="journey-rail">
            {journeys.map((journey, index) => (
              <button
                type="button"
                key={journey.title}
                className="journey-step"
                onClick={() => onNavigate(journey.action)}
              >
                <div className="journey-index">0{index + 1}</div>
                <div>
                  <h3>{journey.title}</h3>
                  <p>{journey.summary}</p>
                </div>
                <Icons.arrow />
              </button>
            ))}
          </div>
        </div>

        <div className="story-panel">
          <div className="section-head">
            <span>今天值得打开的原因</span>
            <span className="section-note">持续互动，而不是一次性问答</span>
          </div>
          <div className="reasons-list">
            {[
              '把你的病程摘要同步到 SecondMe，让分身替你完成自我介绍。',
              '进入同病种社群，先看别人怎么整理就诊路径和化验单。',
              '把 DeepRare 的候选诊断带回研究中心，继续查基因、登记、医院和药物线索。',
            ].map((reason) => (
              <div key={reason} className="reason-row">
                <span className="reason-mark" />
                <p>{reason}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="showcase-grid">
        <div className="showcase-column">
          <div className="section-head">
            <span>能力地图</span>
            <span className="section-note">GitHub 当前默认分支可见能力</span>
          </div>
          <div className="module-list">
            {modules.map((module) => (
              <div key={`${module.path}-${module.title}`} className="module-row">
                <div>
                  <div className="module-title">{module.title}</div>
                  <div className="module-summary">{module.summary}</div>
                </div>
                <span className="module-tag">{module.category}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="showcase-column">
          <div className="section-head">
            <span>社区热度</span>
            <button type="button" onClick={() => onNavigate('community')}>
              前往社群
            </button>
          </div>
          <div className="community-list">
            {communities.map((community) => (
              <button
                key={community.id}
                type="button"
                className="community-card"
                onClick={() => onNavigate('community')}
              >
                <div>
                  <h3>{community.name}</h3>
                  <p>{community.description}</p>
                </div>
                <div className="community-meta">
                  <span>{community.member_count} 成员</span>
                  <span>{community.post_count} 帖子</span>
                </div>
              </button>
            ))}
          </div>
        </div>
      </section>

      <section className="signal-strip">
        <div className="section-head">
          <span>患者真实讨论</span>
          <span className="section-note">把社群内容变成平台活性，而不是静态目录</span>
        </div>
        <div className="post-grid">
          {posts.map((post) => (
            <article key={post.id} className="post-card">
              <div className="post-meta">
                <span>{post.community_name}</span>
                <span>{post.likes} 喜欢</span>
              </div>
              <h3>{post.author}</h3>
              <p>{post.content}</p>
            </article>
          ))}
        </div>
        {error && <div className="inline-error">{error}</div>}
      </section>
    </div>
  );
}

function AIChatPage() {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: '我是 MediChat-RD 的患者陪诊助手。你可以先描述当前最困扰的症状、诊断阶段，或者你想问医生/病友的具体问题。',
    },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState('');
  const [lastDoctor, setLastDoctor] = useState(null);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const quickPrompts = [
    '我该怎么把病历整理给医生看？',
    'DeepRare 给了我 3 个候选诊断，下一步先查什么？',
    '如何向病友介绍自己的病程，不让人一上来就被信息量压住？',
  ];

  const sendMessage = async (draft = input) => {
    const text = draft.trim();
    if (!text || loading) return;

    const userMessage = { role: 'user', content: text };
    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const data = await fetchJson('/api/v1/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: text,
          session_id: sessionId || null,
        }),
      });
      setSessionId(data.session_id);
      setLastDoctor({
        doctor_name: data.doctor_name,
        doctor_title: data.doctor_title,
        doctor_department: data.doctor_department,
        doctor_hospital: data.doctor_hospital,
        suggestions: data.suggestions || [],
      });
      setMessages((prev) => [...prev, { role: 'assistant', content: data.message }]);
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: `抱歉，这次没有成功响应：${error.message}` },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="utility-page">
      <div className="utility-shell lively-shell theme-chat">
        <PageShowcase
          scene="chat"
          eyebrow="AI patient companion"
          title="AI 陪诊助手"
          description="用更柔和、更有陪伴感的方式，把你的病历、问题和情绪先整理成可以说给医生和病友听的话。"
          tags={['病历整理', '医生提问翻译', '病友表达排练', 'SecondMe 连接前置']}
          actions={[
            { label: '先整理病历开场', icon: 'file', onClick: () => sendMessage(quickPrompts[0]) },
            { label: '继续追问检查顺序', icon: 'chat', variant: 'ghost', onClick: () => sendMessage(quickPrompts[1]) },
          ]}
          highlights={[
            { icon: 'file', title: '病历整理', text: '把零散经历变成就诊时能快速抓住重点的摘要。' },
            { icon: 'brain', title: '问题重写', text: '把“我很乱”翻成医生和病友都愿意继续回应的问题。' },
            { icon: 'users', title: '表达陪练', text: '先练习怎么介绍自己，再更自然地进入病友互动。' },
          ]}
          poster={{
            kicker: '陪诊画布',
            badge: lastDoctor ? '医生角色已就绪' : '等待第一条问题',
            title: lastDoctor ? `${lastDoctor.doctor_name} 正在待命` : '让第一句话更容易说出口',
            summary: lastDoctor
              ? `${lastDoctor.doctor_hospital} · ${lastDoctor.doctor_department}。先把问题说清，再决定下一步问谁。`
              : '先和 AI 排练一遍，再把更清楚的问题带去医生门诊、DeepRare 或病友圈。',
            bubbles: ['病历整理', '检查追问', '病友表达'],
            stats: [
              { label: '当前会话', value: sessionId ? '已建立' : '待开始' },
              { label: '医生角色', value: lastDoctor?.doctor_name || '通用陪诊' },
              { label: '继续追问', value: `${lastDoctor?.suggestions?.length || quickPrompts.length} 条` },
            ],
          }}
        />

        {lastDoctor && (
          <div className="doctor-badge">
            <span>{lastDoctor.doctor_name}</span>
            <small>{lastDoctor.doctor_hospital} · {lastDoctor.doctor_department}</small>
          </div>
        )}

        <div className="prompt-row">
          {quickPrompts.map((prompt) => (
            <button key={prompt} type="button" className="prompt-chip" onClick={() => sendMessage(prompt)}>
              {prompt}
            </button>
          ))}
        </div>

        <div className="chat-shell">
          <div className="chat-stream">
            {messages.map((message, index) => (
              <div key={`${message.role}-${index}`} className={`message-row ${message.role}`}>
                <div className="message-avatar">{message.role === 'assistant' ? 'AI' : '你'}</div>
                <div className="message-bubble">
                  <MultilineText text={message.content} />
                </div>
              </div>
            ))}
            {loading && (
              <div className="message-row assistant">
                <div className="message-avatar">AI</div>
                <div className="message-bubble">
                  <div className="typing-dots"><span /><span /><span /></div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {lastDoctor?.suggestions?.length > 0 && (
            <div className="suggestion-box">
              <span className="suggestion-title">继续追问</span>
              <div className="prompt-row compact">
                {lastDoctor.suggestions.map((suggestion) => (
                  <button key={suggestion} type="button" className="prompt-chip" onClick={() => sendMessage(suggestion)}>
                    {suggestion}
                  </button>
                ))}
              </div>
            </div>
          )}

          <div className="composer">
            <textarea
              value={input}
              onChange={(event) => setInput(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === 'Enter' && !event.shiftKey) {
                  event.preventDefault();
                  sendMessage();
                }
              }}
              placeholder="描述你目前的症状、检查结果或最困扰的问题"
              rows={3}
            />
            <button type="button" className="primary-btn" onClick={() => sendMessage()} disabled={loading || !input.trim()}>
              <Icons.chat />
              <span>{loading ? '处理中' : '发送问题'}</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

function SymptomCheckPage() {
  const [text, setText] = useState('');
  const [age, setAge] = useState('');
  const [gender, setGender] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');

  const applyPreset = ({ presetText, presetAge, presetGender }) => {
    setText(presetText);
    setAge(presetAge);
    setGender(presetGender);
  };

  const submit = async () => {
    if (!text.trim() || loading) return;
    setLoading(true);
    setError('');
    try {
      const data = await fetchJson('/api/v1/platform/symptom-check', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text,
          age: age ? Number(age) : null,
          gender: gender || null,
        }),
      });
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="utility-page">
      <div className="utility-shell lively-shell theme-intake">
        <PageShowcase
          scene="intake"
          eyebrow="Patient-first intake"
          title="智能症状筛查"
          description="从患者自己的自然语言开始，先帮你抓住关键病种、关键基因和关键症状，再决定接下来该做什么。"
          tags={['自然语言输入', 'HPO 表型', '差异诊断', '下一步动作']}
          actions={[
            {
              label: '填入肌无力案例',
              icon: 'activity',
              onClick: () => applyPreset({
                presetText: '反复肌无力、下午明显加重，伴有眼睑下垂和吞咽困难，最近说话久了也容易含糊。',
                presetAge: '24',
                presetGender: '女',
              }),
            },
            {
              label: '填入脾大骨痛案例',
              icon: 'dna',
              variant: 'ghost',
              onClick: () => applyPreset({
                presetText: '儿童期开始反复脾大、贫血和骨痛，近半年活动耐量下降，偶尔腿部酸痛明显。',
                presetAge: '12',
                presetGender: '男',
              }),
            },
          ]}
          highlights={[
            { icon: 'search', title: '症状抓取', text: '直接识别口语描述里的重点表型，不要求患者先懂医学术语。' },
            { icon: 'dna', title: 'HPO 标准化', text: '把散乱症状归并成可继续用于诊断和基因分析的标准表型。' },
            { icon: 'check', title: '下一步动作', text: '把最该先问、先查、先准备的事项摆在前面。' },
          ]}
          poster={{
            kicker: '首轮分诊',
            badge: result ? '已生成摘要' : '等待症状输入',
            title: result ? `${result.top_diagnoses?.[0]?.disease || '候选方向'} 正在上浮` : '先把症状讲清楚',
            summary: result?.summary || '患者不需要先学会医学语言，平台会先帮你把症状翻译成诊断和就诊可用的结构。',
            bubbles: ['HPO', '鉴别诊断', '就诊准备'],
            stats: [
              { label: '表型数量', value: `${result?.phenotypes?.length || 0}` },
              { label: '候选方向', value: `${result?.top_diagnoses?.length || 3}` },
              { label: '涉及系统', value: `${result?.systems_involved?.length || 1}` },
            ],
          }}
        />

        <div className="form-panel">
          <div className="field-grid two">
            <label className="field">
              <span>年龄</span>
              <input type="number" value={age} onChange={(event) => setAge(event.target.value)} placeholder="选填" />
            </label>
            <label className="field">
              <span>性别</span>
              <select value={gender} onChange={(event) => setGender(event.target.value)}>
                <option value="">选填</option>
                <option value="男">男</option>
                <option value="女">女</option>
              </select>
            </label>
          </div>
          <label className="field">
            <span>症状描述</span>
            <textarea
              rows={5}
              value={text}
              onChange={(event) => setText(event.target.value)}
              placeholder="例如：反复肌无力、下午加重、吞咽困难，最近还出现眼睑下垂"
            />
          </label>
          <button type="button" className="primary-btn" onClick={submit} disabled={loading || !text.trim()}>
            <Icons.search />
            <span>{loading ? '正在解析症状' : '开始筛查'}</span>
          </button>
          {error && <div className="inline-error">{error}</div>}
        </div>

        {result && (
          <div className="result-stack">
            <section className="result-panel accent">
              <div className="section-head">
                <span>筛查摘要</span>
                <span className="section-note">{result.systems_involved?.join(' / ') || '单系统表现'}</span>
              </div>
              <p className="summary-text">{result.summary}</p>
              <div className="tag-row">
                {(result.phenotypes || []).map((phenotype) => (
                  <span key={`${phenotype.hpo_id}-${phenotype.matched}`} className="phenotype-pill">
                    {phenotype.hpo_id} · {phenotype.matched}
                  </span>
                ))}
              </div>
            </section>

            <section className="result-panel">
              <div className="section-head">
                <span>优先排查方向</span>
                <span className="section-note">不是最终诊断，只是首轮排序</span>
              </div>
              <div className="diagnosis-list">
                {(result.top_diagnoses || []).map((diagnosis) => (
                  <div key={`${diagnosis.rank}-${diagnosis.disease}`} className="diagnosis-row">
                    <div className="diagnosis-rank">0{diagnosis.rank}</div>
                    <div className="diagnosis-body">
                      <h3>{diagnosis.disease}</h3>
                      <p>{diagnosis.reasoning}</p>
                    </div>
                    <div className="diagnosis-score">{diagnosis.confidence}</div>
                  </div>
                ))}
              </div>
            </section>

            <section className="result-panel">
              <div className="section-head">
                <span>下一步动作</span>
                <span className="section-note">把这部分直接带去就诊或发给病友求助</span>
              </div>
              <div className="bullet-list">
                {(result.recommendations || []).map((item) => (
                  <div key={item} className="bullet-row">
                    <Icons.check />
                    <span>{item}</span>
                  </div>
                ))}
              </div>
              <div className="preview-box">
                <span className="preview-title">推理预览</span>
                <pre>{result.reasoning_preview}</pre>
              </div>
            </section>
          </div>
        )}
      </div>
    </div>
  );
}

function DiseaseResearchPage() {
  const [disease, setDisease] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');

  const runResearch = async (diseaseName) => {
    if (!diseaseName.trim() || loading) return;
    setLoading(true);
    setError('');
    try {
      const data = await fetchJson('/api/v1/platform/research', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ disease_name: diseaseName }),
      });
      setResult(data);
    } catch (err) {
      setError(err.message);
      setResult(null);
    } finally {
      setLoading(false);
    }
  };

  const submit = async () => {
    await runResearch(disease);
  };

  useEffect(() => {
    const prefilled = window.localStorage.getItem(PREFILLED_DISEASE_STORAGE_KEY);
    if (!prefilled) return;
    setDisease(prefilled);
    runResearch(prefilled);
    window.localStorage.removeItem(PREFILLED_DISEASE_STORAGE_KEY);
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div className="utility-page">
      <div className="utility-shell lively-shell theme-research">
        <PageShowcase
          scene="research"
          eyebrow="Rare disease research desk"
          title="疾病研究中心"
          description="把疾病介绍、相关基因、专病医院、长期管理要点和患者最常问的问题，一次整理成能读、能点、能继续深入的知识工作台。"
          tags={['疾病介绍', '专病医院', '知识图谱', '患者问题清单']}
          actions={[
            { label: '查看戈谢病', icon: 'file', onClick: () => { setDisease('戈谢病'); runResearch('戈谢病'); } },
            { label: '查看法布雷病', icon: 'spark', variant: 'ghost', onClick: () => { setDisease('法布雷病'); runResearch('法布雷病'); } },
          ]}
          highlights={[
            { icon: 'file', title: '疾病介绍', text: '把复杂病种先讲成人能读懂的全景摘要。' },
            { icon: 'dna', title: '基因与图谱', text: '把基因、表型和相关病种连成清晰的知识上下文。' },
            { icon: 'home', title: '就诊动作', text: '直接前置专病医院、长期管理要点和下一步研究动作。' },
          ]}
          poster={{
            kicker: '研究工作台',
            badge: result ? '研究摘要已生成' : '等待病种输入',
            title: result?.disease?.name || result?.disease?.name_en || '从病种开始组织信息',
            summary: result?.disease?.treatment_summary || '这里不是生硬的资料库，而是一个能把疾病解释、医院、问题和行动放在一起的页面。',
            bubbles: ['疾病介绍', '医院地图', '问题清单'],
            stats: [
              { label: '研究信号', value: `${result?.research_signals?.length || 3}` },
              { label: '相关病种', value: `${result?.related_conditions?.length || 0}` },
              { label: '医院线索', value: `${result?.disease?.specialist_hospitals?.length || 0}` },
            ],
          }}
        />

        <div className="search-shell">
          <input
            value={disease}
            onChange={(event) => setDisease(event.target.value)}
            onKeyDown={(event) => event.key === 'Enter' && submit()}
            placeholder="输入疾病名称，例如 戈谢病 / Fabry disease"
          />
          <button type="button" className="primary-btn" onClick={submit} disabled={loading || !disease.trim()}>
            <Icons.file />
            <span>{loading ? '整理中' : '生成研究摘要'}</span>
          </button>
        </div>

        <section className="quick-access-shell">
          <div className="section-head">
            <span>常见病种快捷入口</span>
            <span className="section-note">患者可直接点选查看疾病介绍</span>
          </div>
          <div className="quick-card-grid">
            {COMMON_DISEASE_LIBRARY.map((item) => (
              <button
                key={item.name}
                type="button"
                className="quick-card"
                onClick={() => {
                  setDisease(item.name);
                  runResearch(item.name);
                }}
              >
                <div className="quick-card-top">
                  <strong>{item.name}</strong>
                  <span>{item.category}</span>
                </div>
                <p>{item.summary}</p>
                <div className="quick-card-footer">
                  <span>{item.gene}</span>
                  <span>点击查看</span>
                </div>
              </button>
            ))}
          </div>
        </section>

        {error && <div className="inline-error">{error}</div>}

        {result && (
          <div className="result-stack">
            <section className="result-panel accent">
              <div className="section-head">
                <span>{result.disease.name || result.disease.name_en}</span>
                <span className="section-note">{result.disease.category}</span>
              </div>
              <p className="summary-text">{result.disease.treatment_summary}</p>
              <div className="signal-grid">
                {result.research_signals.map((signal) => (
                  <div key={signal.label} className="signal-cell">
                    <small>{signal.label}</small>
                    <strong>{signal.value}</strong>
                  </div>
                ))}
              </div>
            </section>

            <section className="result-panel">
              <div className="section-head">
                <span>患者当前最该问的问题</span>
              </div>
              <div className="bullet-list">
                {result.patient_questions.map((question) => (
                  <div key={question} className="bullet-row">
                    <Icons.spark />
                    <span>{question}</span>
                  </div>
                ))}
              </div>
            </section>

            <section className="result-panel">
              <div className="section-head">
                <span>就诊与研究动作</span>
              </div>
              <div className="bullet-list">
                {result.care_points.map((point) => (
                  <div key={point} className="bullet-row">
                    <Icons.check />
                    <span>{point}</span>
                  </div>
                ))}
              </div>
              {result.disease.specialist_hospitals?.length > 0 && (
                <div className="hospital-rack">
                  {result.disease.specialist_hospitals.map((hospital) => (
                    <span key={hospital} className="mode-pill">{hospital}</span>
                  ))}
                </div>
              )}
            </section>

            <section className="result-panel">
              <div className="section-head">
                <span>相关疾病线索</span>
              </div>
              <div className="related-grid">
                {result.related_conditions.map((item) => (
                  <div key={`${item.name_en}-${item.gene}`} className="related-card">
                    <h3>{item.name || item.name_en}</h3>
                    <p>{item.gene} · {item.inheritance}</p>
                  </div>
                ))}
              </div>
            </section>

            {result.knowledge_map?.center && (
              <section className="result-panel">
                <div className="section-head">
                  <span>知识图谱上下文</span>
                  <span className="section-note">{result.knowledge_map.center.label}</span>
                </div>
                <div className="bullet-list">
                  {(result.knowledge_map.related.genes || []).slice(0, 3).map((item) => (
                    <div key={`${item.id}-${item.label}`} className="bullet-row">
                      <Icons.dna />
                      <span>关联基因：{item.label}</span>
                    </div>
                  ))}
                  {(result.knowledge_map.related.drugs || []).slice(0, 3).map((item) => (
                    <div key={`${item.id}-${item.label}`} className="bullet-row">
                      <Icons.pill />
                      <span>相关药物：{item.label}</span>
                    </div>
                  ))}
                  {(result.knowledge_map.related.phenotypes || []).slice(0, 3).map((item) => (
                    <div key={`${item.id}-${item.label}`} className="bullet-row">
                      <Icons.activity />
                      <span>关键表型：{item.label}</span>
                    </div>
                  ))}
                </div>
              </section>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function GenomicHubPage() {
  const [form, setForm] = useState({
    disease_name: '',
    symptoms_text: '',
    gene: '',
    hgvs_c: '',
    pathogenicity: 'VUS',
    allele_frequency: '0.0001',
    age_of_onset: '',
    gender: '',
    ethnicity: '',
    location: '',
  });
  const [analysis, setAnalysis] = useState(null);
  const [matchResult, setMatchResult] = useState(null);
  const [enrollment, setEnrollment] = useState(null);
  const [cohortResult, setCohortResult] = useState(null);
  const [cohortLoading, setCohortLoading] = useState(false);
  const [loading, setLoading] = useState(false);
  const [matching, setMatching] = useState(false);
  const [registering, setRegistering] = useState(false);
  const [error, setError] = useState('');

  const applyGenomicPreset = (preset) => {
    setForm((current) => ({
      ...current,
      disease_name: preset.disease_name,
      symptoms_text: preset.symptoms_text,
      gene: preset.gene,
      hgvs_c: preset.hgvs_c,
      pathogenicity: preset.pathogenicity,
      allele_frequency: preset.allele_frequency,
      age_of_onset: preset.age_of_onset,
      gender: preset.gender,
      ethnicity: preset.ethnicity,
      location: preset.location,
    }));
  };

  const buildVariants = () => {
    if (!form.gene.trim()) return [];
    return [
      {
        gene: form.gene.trim(),
        chromosome: 'NA',
        position: 0,
        ref: 'N',
        alt: 'N',
        variant_type: 'SNV',
        hgvs_c: form.hgvs_c.trim(),
        pathogenicity: form.pathogenicity,
        allele_frequency: form.allele_frequency ? Number(form.allele_frequency) : 0,
      },
    ];
  };

  const analyze = async () => {
    if (!form.symptoms_text.trim() || loading) return;
    setLoading(true);
    setError('');
    setMatchResult(null);
    setEnrollment(null);
    setCohortResult(null);
    try {
      const data = await fetchJson('/api/v1/platform/genomic-triage', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          disease_name: form.disease_name || null,
          symptoms_text: form.symptoms_text,
          variants: buildVariants(),
          age_of_onset: form.age_of_onset ? Number(form.age_of_onset) : null,
          gender: form.gender || null,
        }),
      });
      setAnalysis(data);
    } catch (err) {
      setError(err.message);
      setAnalysis(null);
    } finally {
      setLoading(false);
    }
  };

  const findMatches = async () => {
    if (!form.symptoms_text.trim() || matching) return;
    setMatching(true);
    setError('');
    try {
      const diseaseName = form.disease_name
        || analysis?.disease_context?.name
        || analysis?.gene_rankings?.[0]?.disease
        || '待确认疾病';
      const data = await fetchJson('/api/v1/platform/community-match', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          disease_name: diseaseName,
          symptoms_text: form.symptoms_text,
          age: form.age_of_onset ? Number(form.age_of_onset) : null,
          gender: form.gender || null,
          location: form.location || null,
        }),
      });
      setMatchResult(data);
    } catch (err) {
      setError(err.message);
      setMatchResult(null);
    } finally {
      setMatching(false);
    }
  };

  const enroll = async () => {
    if (!form.symptoms_text.trim() || registering) return;
    setRegistering(true);
    setError('');
    try {
      const diseaseName = form.disease_name
        || analysis?.disease_context?.name
        || analysis?.gene_rankings?.[0]?.disease
        || '待确认疾病';
      const data = await fetchJson('/api/v1/platform/registry-enroll', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          disease_name: diseaseName,
          symptoms_text: form.symptoms_text,
          variants: buildVariants(),
          diagnosis_status: analysis?.gene_rankings?.length ? 'under_review' : 'suspected',
          age_of_onset: form.age_of_onset ? Number(form.age_of_onset) : null,
          gender: form.gender || null,
          ethnicity: form.ethnicity || null,
          consent_research: true,
          consent_matching: true,
        }),
      });
      setEnrollment(data);
      storeRegistryId(data?.registration?.registry_id);
    } catch (err) {
      setError(err.message);
      setEnrollment(null);
    } finally {
      setRegistering(false);
    }
  };

  const createCohort = async () => {
    const registryId = enrollment?.registration?.registry_id;
    const diseaseName = enrollment?.registration?.disease || form.disease_name || analysis?.disease_context?.name;
    if (!registryId || !diseaseName || cohortLoading) return;
    setCohortLoading(true);
    setError('');
    try {
      const data = await fetchJson('/api/v1/platform/cohorts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: `${diseaseName} 初始队列`,
          disease: diseaseName,
          criteria: '由平台登记对象自动创建的研究准备队列',
          registry_ids: [registryId],
        }),
      });
      setCohortResult(data);
    } catch (err) {
      setError(err.message);
      setCohortResult(null);
    } finally {
      setCohortLoading(false);
    }
  };

  return (
    <div className="utility-page">
      <div className="utility-shell lively-shell theme-genomic">
        <PageShowcase
          scene="genomic"
          eyebrow="Genomics, registry and patient matching"
          title="基因与登记中心"
          description="把患者叙述、基因线索、Phenopacket、患者登记和病友匹配连成一条真正连续的工作流，不再让每一步都重新开始。"
          tags={['基因分诊', 'Phenopacket', '患者登记', '病友匹配']}
          actions={[
            {
              label: '填入代谢病案例',
              icon: 'dna',
              onClick: () => applyGenomicPreset({
                disease_name: '戈谢病',
                symptoms_text: '儿童期起病，反复脾大、贫血、骨痛和乏力，最近出现活动耐量下降。',
                gene: 'GBA1',
                hgvs_c: 'c.1226A>G',
                pathogenicity: 'pathogenic',
                allele_frequency: '0.0001',
                age_of_onset: '10',
                gender: '男',
                ethnicity: '汉族',
                location: '上海',
              }),
            },
            {
              label: '填入神经肌肉案例',
              icon: 'activity',
              variant: 'ghost',
              onClick: () => applyGenomicPreset({
                disease_name: '脊髓性肌萎缩症',
                symptoms_text: '婴幼儿期出现肌张力低、翻身抬头困难和进行性近端肌无力，近期吞咽也较吃力。',
                gene: 'SMN1',
                hgvs_c: 'exon7del',
                pathogenicity: 'likely_pathogenic',
                allele_frequency: '0.0002',
                age_of_onset: '1',
                gender: '女',
                ethnicity: '汉族',
                location: '杭州',
              }),
            },
          ]}
          highlights={[
            { icon: 'dna', title: '基因分诊', text: '把表型和变异一起排序，让候选基因和疾病更快浮出来。' },
            { icon: 'file', title: '登记入库', text: '直接生成登记对象、患者编码和可继续使用的 Phenopacket。' },
            { icon: 'users', title: '同阶段病友', text: '把相近病程的人更早连接起来，而不是登记完就结束。' },
            { icon: 'spark', title: '研究队列', text: '从单个患者自然回流到研究准备队列和后续研究。' },
          ]}
          poster={{
            kicker: '从线索到登记',
            badge: enrollment?.registration ? '已完成登记' : analysis ? '已完成分诊' : '等待病例输入',
            title: enrollment?.registration?.patient_code || analysis?.disease_context?.name || '先把病例放上来',
            summary: analysis?.summary || '先抓住候选基因和病种，再决定是去找病友、登记入库还是继续做研究准备。',
            bubbles: ['分诊排序', '登记编码', '病友连接'],
            stats: [
              { label: '候选基因', value: `${analysis?.gene_rankings?.length || 0}` },
              { label: '病友匹配', value: `${matchResult?.matches?.length || 0}` },
              { label: '登记状态', value: enrollment?.registration ? '已登记' : '待登记' },
            ],
          }}
        />

        <div className="form-panel">
          <div className="field-grid two">
            <label className="field">
              <span>怀疑疾病</span>
              <input
                value={form.disease_name}
                onChange={(event) => setForm({ ...form, disease_name: event.target.value })}
                placeholder="例如：戈谢病 / 法布雷病"
              />
            </label>
            <label className="field">
              <span>基因提示</span>
              <input
                value={form.gene}
                onChange={(event) => setForm({ ...form, gene: event.target.value })}
                placeholder="例如：GBA1 / GLA / SMN1"
              />
            </label>
          </div>

          <label className="field">
            <span>症状与病程</span>
            <textarea
              rows={5}
              value={form.symptoms_text}
              onChange={(event) => setForm({ ...form, symptoms_text: event.target.value })}
              placeholder="例如：儿童起病，反复脾大、贫血、骨痛，最近还出现乏力和活动耐量下降"
            />
          </label>

          <div className="field-grid two">
            <label className="field">
              <span>HGVS 位点</span>
              <input
                value={form.hgvs_c}
                onChange={(event) => setForm({ ...form, hgvs_c: event.target.value })}
                placeholder="例如：c.1226A>G"
              />
            </label>
            <label className="field">
              <span>致病性</span>
              <select value={form.pathogenicity} onChange={(event) => setForm({ ...form, pathogenicity: event.target.value })}>
                <option value="pathogenic">pathogenic</option>
                <option value="likely_pathogenic">likely_pathogenic</option>
                <option value="VUS">VUS</option>
                <option value="likely_benign">likely_benign</option>
                <option value="benign">benign</option>
              </select>
            </label>
          </div>

          <div className="field-grid two">
            <label className="field">
              <span>等位基因频率</span>
              <input
                value={form.allele_frequency}
                onChange={(event) => setForm({ ...form, allele_frequency: event.target.value })}
                placeholder="例如：0.0001"
              />
            </label>
            <label className="field">
              <span>起病年龄</span>
              <input
                type="number"
                value={form.age_of_onset}
                onChange={(event) => setForm({ ...form, age_of_onset: event.target.value })}
                placeholder="选填"
              />
            </label>
          </div>

          <div className="field-grid two">
            <label className="field">
              <span>性别</span>
              <select value={form.gender} onChange={(event) => setForm({ ...form, gender: event.target.value })}>
                <option value="">选填</option>
                <option value="男">男</option>
                <option value="女">女</option>
              </select>
            </label>
            <label className="field">
              <span>地区 / 人群</span>
              <input
                value={form.location}
                onChange={(event) => setForm({ ...form, location: event.target.value })}
                placeholder="例如：上海 / 华东"
              />
            </label>
          </div>

          <label className="field">
            <span>补充人群信息</span>
            <input
              value={form.ethnicity}
              onChange={(event) => setForm({ ...form, ethnicity: event.target.value })}
              placeholder="例如：汉族 / 儿科起病 / 家族史阳性"
            />
          </label>

          <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
            <button type="button" className="primary-btn" onClick={analyze} disabled={loading || !form.symptoms_text.trim()}>
              <Icons.dna />
              <span>{loading ? '正在做基因分诊' : '开始基因分诊'}</span>
            </button>
            <button type="button" className="ghost-btn" onClick={findMatches} disabled={matching || !form.symptoms_text.trim()}>
              <Icons.users />
              <span>{matching ? '正在匹配病友' : '查找同阶段病友'}</span>
            </button>
            <button type="button" className="ghost-btn" onClick={enroll} disabled={registering || !form.symptoms_text.trim()}>
              <Icons.file />
              <span>{registering ? '登记中' : '登记进入患者库'}</span>
            </button>
          </div>
          {error && <div className="inline-error">{error}</div>}
        </div>

        {analysis && (
          <div className="result-stack">
            <section className="result-panel accent">
              <div className="section-head">
                <span>分诊摘要</span>
                <span className="section-note">{analysis.analysis_mode}</span>
              </div>
              <p className="summary-text">{analysis.summary}</p>
              <div className="tag-row">
                {(analysis.phenotypes || []).map((phenotype) => (
                  <span key={`${phenotype.hpo_id}-${phenotype.matched}`} className="phenotype-pill">
                    {phenotype.matched}
                  </span>
                ))}
              </div>
            </section>

            <section className="result-panel">
              <div className="section-head">
                <span>候选基因 / 疾病排序</span>
                <span className="section-note">表型分数 + 变异分数综合</span>
              </div>
              <div className="diagnosis-list">
                {(analysis.gene_rankings || []).map((item, index) => (
                  <div key={`${item.gene}-${item.disease}`} className="diagnosis-row">
                    <div className="diagnosis-rank">0{index + 1}</div>
                    <div className="diagnosis-body">
                      <h3>{item.gene} · {item.disease}</h3>
                      <p>{item.omim_id} · {item.inheritance} · 表型 {item.phenotype_score} / 变异 {item.variant_score}</p>
                    </div>
                    <div className="diagnosis-score">{item.combined_score}</div>
                  </div>
                ))}
              </div>
            </section>

            <section className="result-panel">
              <div className="section-head">
                <span>病历摘要与 Phenopacket 预览</span>
              </div>
              <div className="bullet-list">
                <div className="bullet-row">
                  <Icons.chat />
                  <span>{analysis.clinical_note?.summary || '暂无自动摘要'}</span>
                </div>
                <div className="bullet-row">
                  <Icons.activity />
                  <span>识别到 {analysis.clinical_note?.total_entities || 0} 个医学实体，涉及 {analysis.systems_involved?.join(' / ') || '单系统'}。</span>
                </div>
              </div>
              <div className="preview-box">
                <span className="preview-title">Phenopacket Preview</span>
                <pre>{JSON.stringify(analysis.phenopacket_preview, null, 2)}</pre>
              </div>
            </section>
          </div>
        )}

        {matchResult?.matches?.length > 0 && (
          <section className="result-panel" style={{ marginTop: 24 }}>
            <div className="section-head">
              <span>推荐病友连接</span>
              <span className="section-note">当前支持组规模 {matchResult.support_group_size}</span>
            </div>
            <div className="related-grid">
              {matchResult.matches.map((item) => (
                <div key={item.patient_id} className="related-card">
                  <h3>{item.disease}</h3>
                  <p>{item.match_reason}</p>
                  <p>相似度 {Math.round(item.similarity * 100)}% · {item.location || '地区待补充'}</p>
                </div>
              ))}
            </div>
          </section>
        )}

        {enrollment?.registration && (
          <section className="result-panel" style={{ marginTop: 24 }}>
            <div className="section-head">
              <span>登记成功</span>
              <span className="section-note">{enrollment.registration.patient_code}</span>
            </div>
            <div className="signal-grid">
              <div className="signal-cell">
                <small>Registry ID</small>
                <strong>{enrollment.registration.registry_id}</strong>
              </div>
              <div className="signal-cell">
                <small>总登记数</small>
                <strong>{enrollment.stats.total_patients}</strong>
              </div>
              <div className="signal-cell">
                <small>总队列数</small>
                <strong>{enrollment.stats.total_cohorts}</strong>
              </div>
            </div>
            <div className="preview-box">
              <span className="preview-title">已登记 Phenopacket</span>
              <pre>{JSON.stringify(enrollment.phenopacket, null, 2)}</pre>
            </div>
            <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginTop: 18 }}>
              <button type="button" className="ghost-btn" onClick={createCohort} disabled={cohortLoading}>
                <Icons.file />
                <span>{cohortLoading ? '创建中' : '创建研究队列'}</span>
              </button>
            </div>
            {cohortResult?.cohort && (
              <div className="preview-box" style={{ marginTop: 18 }}>
                <span className="preview-title">Cohort</span>
                <pre>{JSON.stringify(cohortResult, null, 2)}</pre>
              </div>
            )}
          </section>
        )}
      </div>
    </div>
  );
}

function ScientificSkillsPage({ onNavigate }) {
  const [data, setData] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    let cancelled = false;
    fetchJson('/api/v1/platform/scientific-skills')
      .then((payload) => {
        if (!cancelled) setData(payload);
      })
      .catch((err) => {
        if (!cancelled) setError(err.message);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const skills = data?.skills || [];
  const workflows = data?.workflows || [];
  const runtime = data?.runtime || {};
  const runtimeProfiles = runtime.profiles || [];
  const bootstrapCommands = runtime.bootstrap_commands || [];
  const runExamples = runtime.run_examples || [];
  const runtimeReady = Boolean(runtime.ready);
  const runtimePython = runtime.venv?.version || runtime.system_python?.version || '未检测到 Python 3.12';
  const uvLabel = runtime.uv?.installed
    ? (runtime.uv?.version || '已安装')
    : '未安装';

  return (
    <div className="utility-page">
      <div className="utility-shell lively-shell theme-science">
        <PageShowcase
          scene="science"
          eyebrow="Scientific accelerator layer"
          title="科研加速层"
          description="把文献综述、药物发现、临床研究文档和 Python 3.12 科研运行时，变成平台随时能点开的研究引擎。"
          tags={['文献综述', 'RDKit / MedChem', '治疗计划', 'Python 3.12 + uv']}
          actions={[
            { label: '去做疾病研究', icon: 'file', onClick: () => onNavigate('disease-research') },
            { label: '去看药物线索', icon: 'pill', variant: 'ghost', onClick: () => onNavigate('drug-research') },
          ]}
          highlights={[
            { icon: 'spark', title: '技能集合', text: '把多项科研技能前置成可组合的研究能力，而不是零散脚本。' },
            { icon: 'pill', title: '药物发现', text: '把 RDKit、MedChem、虚拟筛选和研究包整理到一条线上。' },
            { icon: 'file', title: '临床文档', text: '把综述、治疗计划和研究摘要做成可继续交付的产物。' },
            { icon: 'dna', title: '独立运行时', text: '用 Python 3.12 + uv 承接重型科学包，不拖慢主站。' },
          ]}
          poster={{
            kicker: '科研执行层',
            badge: runtimeReady ? '运行时已就绪' : '等待 bootstrap',
            title: data?.repo?.name || 'claude-scientific-skills',
            summary: '不只是装技能，而是把这些技能真正变成 Rare Disease 平台里的研究工作流和产出能力。',
            bubbles: ['文献', '药物', '临床', '写作'],
            stats: [
              { label: '已安装技能', value: `${data?.installed_count || 0}` },
              { label: '科研 Python', value: runtimePython },
              { label: 'uv', value: uvLabel },
            ],
          }}
        />

        <div className="result-stack">
          <section className="result-panel accent">
            <div className="section-head">
              <span>{data?.repo?.name || 'claude-scientific-skills'}</span>
              <span className="section-note">{data?.installed_count || 0} / {data?.total_curated || 0} 已安装</span>
            </div>
            <p className="summary-text">
              当前已把与罕见病平台最相关的科研技能装入 Codex：数据库检索、RDKit、DiffDock、MedChem、PyHealth、临床决策支持、治疗计划、文献综述和科学写作。
            </p>
            <div className="signal-grid">
              <div className="signal-cell">
                <small>源码仓库</small>
                <strong>{data?.repo?.url || 'K-Dense-AI/claude-scientific-skills'}</strong>
              </div>
              <div className="signal-cell">
                <small>App Python</small>
                <strong>{data?.environment?.app_python_version || '检测中'}</strong>
              </div>
              <div className="signal-cell">
                <small>uv</small>
                <strong>{uvLabel}</strong>
              </div>
              <div className="signal-cell">
                <small>科研运行时</small>
                <strong>{runtime.state_label || '检测中'}</strong>
              </div>
            </div>
            {data?.environment?.codex_restart_required && (
              <div className="inline-error" style={{ marginTop: 16 }}>
                新技能已安装到 Codex。本地平台可立即展示，但要让 Codex 在新会话中稳定自动调用这些技能，需要重启 Codex。
              </div>
            )}
          </section>

          <section className="result-panel">
            <div className="section-head">
              <span>科研执行环境</span>
              <span className="section-note">{runtimeReady ? '已可执行重型工作流' : '还未完成 bootstrap'}</span>
            </div>
            <p className="summary-text">
              平台的 Web 服务继续保持轻量运行；更重的 RDKit、PyHealth、科研绘图与文档输出，被拆进独立的 Python 3.12 + uv 环境。
            </p>
            <div className="signal-grid">
              <div className="signal-cell">
                <small>目标 Python</small>
                <strong>{runtime.required_python || '3.12'}</strong>
              </div>
              <div className="signal-cell">
                <small>科研 Python</small>
                <strong>{runtimePython}</strong>
              </div>
              <div className="signal-cell">
                <small>Venv</small>
                <strong>{runtime.venv?.exists ? '已创建' : '未创建'}</strong>
              </div>
              <div className="signal-cell">
                <small>已启用 Profile</small>
                <strong>{(runtime.installed_profiles || []).join(' / ') || '无'}</strong>
              </div>
            </div>
            {runtime.error && <div className="inline-error" style={{ marginTop: 16 }}>{runtime.error}</div>}
            {!runtimeReady && bootstrapCommands.length > 0 && (
              <div className="preview-box" style={{ marginTop: 18 }}>
                <span className="preview-title">Bootstrap 命令</span>
                <pre>{bootstrapCommands.map((item) => `${item.label}\n${item.command}`).join('\n\n')}</pre>
              </div>
            )}
            {runExamples.length > 0 && (
              <div className="preview-box" style={{ marginTop: 18 }}>
                <span className="preview-title">运行示例</span>
                <pre>{runExamples.join('\n')}</pre>
              </div>
            )}
          </section>

          <section className="result-panel">
            <div className="section-head">
              <span>推荐研究工作流</span>
              <span className="section-note">直接映射到平台已有入口</span>
            </div>
            <div className="program-grid">
              {workflows.map((workflow) => (
                <div key={workflow.title} className="program-card">
                  <div className="program-stage">{workflow.skills.join(' · ')}</div>
                  <h3>{workflow.title}</h3>
                  <p>{workflow.description}</p>
                  <button type="button" className="ghost-btn" onClick={() => onNavigate(workflow.target)}>
                    <Icons.arrow />
                    <span>打开对应入口</span>
                  </button>
                </div>
              ))}
            </div>
          </section>

          <section className="result-panel">
            <div className="section-head">
              <span>已安装技能</span>
              <span className="section-note">优先服务 Rare Disease / Drug Discovery / Clinical Research</span>
            </div>
            <div className="related-grid">
              {skills.map((skill) => (
                <div key={skill.slug} className="related-card">
                  <h3>{skill.title}</h3>
                  <p>{skill.focus}</p>
                  <p>{skill.category} · {skill.installed ? '已安装' : '未安装'}</p>
                </div>
              ))}
            </div>
          </section>

          <section className="result-panel">
            <div className="section-head">
              <span>Runtime Profiles</span>
              <span className="section-note">按工作流分层启用，不再把所有科学包塞进主服务</span>
            </div>
            <div className="related-grid">
              {runtimeProfiles.map((profile) => (
                <div key={profile.slug} className="related-card">
                  <h3>{profile.label}</h3>
                  <p>{profile.description}</p>
                  <p>{profile.installed ? '已就绪' : '待安装'} · {profile.packages.join(', ')}</p>
                </div>
              ))}
            </div>
          </section>

          <section className="result-panel">
            <div className="section-head">
              <span>平台里的具体用途</span>
            </div>
            <div className="bullet-list">
              {[
                '在“疾病研究”里扩展 OMIM、ClinVar、HPO、ClinicalTrials.gov 等跨库证据检索。',
                '在“药物线索”里用 RDKit、MedChem、DiffDock 把候选通路推到结构与对接层。',
                '在“基因与登记”里把登记患者与临床研究文档、决策摘要和治疗计划串起来。',
                '把 Python 3.12 + uv 的科研环境与 Web 服务隔离，避免主站被重型科学依赖拖慢或污染。',
              ].map((item) => (
                <div key={item} className="bullet-row">
                  <Icons.spark />
                  <span>{item}</span>
                </div>
              ))}
            </div>
          </section>
        </div>

        {error && <div className="inline-error">{error}</div>}
      </div>
    </div>
  );
}

function DrugResearchPage() {
  const [disease, setDisease] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [screening, setScreening] = useState(null);
  const [researchPackage, setResearchPackage] = useState(null);
  const [packageLoading, setPackageLoading] = useState(false);
  const [packageError, setPackageError] = useState('');
  const [screeningLoading, setScreeningLoading] = useState(false);
  const [screeningError, setScreeningError] = useState('');
  const [error, setError] = useState('');

  const runDrugClues = async (diseaseName) => {
    if (!diseaseName.trim() || loading) return;
    setLoading(true);
    setError('');
    setScreening(null);
    setResearchPackage(null);
    setPackageError('');
    setScreeningError('');
    try {
      const data = await fetchJson('/api/v1/platform/drug-clues', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ disease_name: diseaseName }),
      });
      setResult(data);
    } catch (err) {
      setError(err.message);
      setResult(null);
    } finally {
      setLoading(false);
    }
  };

  const submit = async () => {
    await runDrugClues(disease);
  };

  const generateResearchPackage = async () => {
    if (!disease.trim() || packageLoading) return;
    setPackageLoading(true);
    setPackageError('');
    try {
      const data = await fetchJson('/api/v1/platform/research-package', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          disease_name: disease,
          registry_id: getStoredRegistryId() || null,
          gene_hint: result?.gene || null,
          include_virtual_screening: true,
        }),
      });
      setResearchPackage(data.research_package);
    } catch (err) {
      setPackageError(err.message);
      setResearchPackage(null);
    } finally {
      setPackageLoading(false);
    }
  };

  const runScreening = async () => {
    if (!disease.trim() || screeningLoading) return;
    setScreeningLoading(true);
    setScreeningError('');
    try {
      const data = await fetchJson('/api/v1/platform/virtual-screening', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          disease_name: disease,
          gene: result?.gene || null,
          target_name: result?.gene ? `${result.gene} target` : null,
          library: 'chembl',
        }),
      });
      setScreening(data);
    } catch (err) {
      setScreeningError(err.message);
      setScreening(null);
    } finally {
      setScreeningLoading(false);
    }
  };

  return (
    <div className="utility-page">
      <div className="utility-shell lively-shell theme-drug">
        <PageShowcase
          scene="drug"
          eyebrow="Therapy opportunity board"
          title="药物线索与重定位"
          description="把常见药物、当前治疗网络、再定位候选、虚拟筛选和研究包放进一个更加直观、可继续深入的药物工作台。"
          tags={['当前治疗网络', '再定位候选', '虚拟筛选', '研究包']}
          actions={[
            { label: '查看戈谢病线索', icon: 'pill', onClick: () => { setDisease('戈谢病'); runDrugClues('戈谢病'); } },
            { label: '查看重症肌无力线索', icon: 'activity', variant: 'ghost', onClick: () => { setDisease('重症肌无力'); runDrugClues('重症肌无力'); } },
          ]}
          highlights={[
            { icon: 'pill', title: '常见药物线索', text: '把患者最常问到的药物和治疗方向直接前置出来。' },
            { icon: 'dna', title: '网络上下文', text: '把药物、靶点、基因和疾病的连接关系讲清楚。' },
            { icon: 'activity', title: '虚拟筛选', text: '把更深一步的筛选能力直接接到当前病种。' },
            { icon: 'file', title: '研究包输出', text: '把候选线索沉淀成医生、研究者和合作方都能继续使用的结构化资料。' },
          ]}
          poster={{
            kicker: '治疗机会板',
            badge: researchPackage ? '研究包已生成' : screening ? '筛选已完成' : result ? '线索已加载' : '等待病种输入',
            title: result?.disease || '先选择一个病种',
            summary: result?.candidate_programs?.[0]?.rationale || '先从患者最常关心的药物和治疗问题开始，再决定要不要进入更深的研究层。',
            bubbles: ['药物网络', '重定位', '虚拟筛选'],
            stats: [
              { label: '候选项目', value: `${result?.candidate_programs?.length || 0}` },
              { label: '当前治疗', value: `${result?.current_therapies?.length || 0}` },
              { label: '筛选命中', value: `${screening?.screening_summary?.hits_found || 0}` },
            ],
          }}
        />

        <div className="search-shell">
          <input
            value={disease}
            onChange={(event) => setDisease(event.target.value)}
            onKeyDown={(event) => event.key === 'Enter' && submit()}
            placeholder="输入疾病名称，例如 戈谢病"
          />
          <button type="button" className="primary-btn" onClick={submit} disabled={loading || !disease.trim()}>
            <Icons.pill />
            <span>{loading ? '分析中' : '查看线索'}</span>
          </button>
        </div>

        <section className="quick-access-shell">
          <div className="section-head">
            <span>常见病种与药物线索</span>
            <span className="section-note">直接点选，查看最常被问到的治疗方向</span>
          </div>
          <div className="quick-card-grid">
            {COMMON_DRUG_SPOTLIGHTS.map((item) => (
              <button
                key={`${item.disease}-${item.tag}`}
                type="button"
                className="quick-card therapy-card"
                onClick={() => {
                  setDisease(item.disease);
                  runDrugClues(item.disease);
                }}
              >
                <div className="quick-card-top">
                  <strong>{item.disease}</strong>
                  <span>{item.tag}</span>
                </div>
                <p>{item.drugs.join(' / ')}</p>
                <div className="quick-card-footer">
                  <span>常见线索</span>
                  <span>点击查看</span>
                </div>
              </button>
            ))}
          </div>
        </section>

        {error && <div className="inline-error">{error}</div>}

        {result && (
          <div className="result-stack">
            <section className="result-panel accent">
              <div className="section-head">
                <span>{result.disease}</span>
                <span className="section-note">{result.gene || '基因待补充'}</span>
              </div>
              <p className="summary-text">这些是当前更适合继续深挖的药物与机制方向，不是直接给患者的用药建议。</p>
            </section>

            <section className="result-panel">
              <div className="section-head">
                <span>候选项目</span>
                <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
                  <button type="button" className="ghost-btn" onClick={generateResearchPackage} disabled={packageLoading}>
                    <Icons.file />
                    <span>{packageLoading ? '生成中' : '生成研究包'}</span>
                  </button>
                  <button type="button" className="ghost-btn" onClick={runScreening} disabled={screeningLoading}>
                    <Icons.activity />
                    <span>{screeningLoading ? '筛选中' : '启动虚拟筛选'}</span>
                  </button>
                </div>
              </div>
              <div className="program-grid">
                {result.candidate_programs.map((program) => (
                  <div key={`${program.candidate}-${program.stage}`} className="program-card">
                    <div className="program-stage">{program.stage}</div>
                    <h3>{program.candidate}</h3>
                    <p>{program.rationale}</p>
                  </div>
                ))}
              </div>
            </section>

            {result.current_therapies?.length > 0 && (
              <section className="result-panel">
                <div className="section-head">
                  <span>当前可见治疗网络</span>
                  <span className="section-note">药物 {result.network_stats?.nodes?.drugs} / 靶点 {result.network_stats?.nodes?.targets}</span>
                </div>
                <div className="program-grid">
                  {result.current_therapies.map((therapy) => (
                    <div key={therapy.drug_id} className="program-card">
                      <div className="program-stage">{therapy.status}</div>
                      <h3>{therapy.name}</h3>
                      <p>{therapy.type} · {(therapy.targets || []).map((item) => item.name).join(' / ') || '靶点整理中'}</p>
                    </div>
                  ))}
                </div>
              </section>
            )}

            {result.repurposing_candidates?.length > 0 && (
              <section className="result-panel">
                <div className="section-head">
                  <span>再定位候选</span>
                </div>
                <div className="related-grid">
                  {result.repurposing_candidates.map((candidate) => (
                    <div key={`${candidate.drug_id}-${candidate.target_gene}`} className="related-card">
                      <h3>{candidate.drug_name}</h3>
                      <p>{candidate.reason}</p>
                      <p>{candidate.target} · {candidate.target_gene}</p>
                    </div>
                  ))}
                </div>
              </section>
            )}

            <section className="result-panel">
              <div className="section-head">
                <span>下一步研究动作</span>
              </div>
              <div className="bullet-list">
                {result.next_steps.map((step) => (
                  <div key={step} className="bullet-row">
                    <Icons.activity />
                    <span>{step}</span>
                  </div>
                ))}
              </div>
            </section>

            {result.knowledge_map?.center && (
              <section className="result-panel">
                <div className="section-head">
                  <span>知识图谱上下文</span>
                </div>
                <div className="bullet-list">
                  {(result.knowledge_map.related.drugs || []).slice(0, 3).map((item) => (
                    <div key={`${item.id}-${item.label}`} className="bullet-row">
                      <Icons.pill />
                      <span>图谱药物：{item.label}</span>
                    </div>
                  ))}
                  {(result.knowledge_map.related.genes || []).slice(0, 3).map((item) => (
                    <div key={`${item.id}-${item.label}`} className="bullet-row">
                      <Icons.dna />
                      <span>图谱基因：{item.label}</span>
                    </div>
                  ))}
                </div>
              </section>
            )}

            {screening && (
              <section className="result-panel accent">
                <div className="section-head">
                  <span>虚拟筛选结果</span>
                  <span className="section-note">{screening.context?.gene} · {screening.screening_summary?.hit_rate}</span>
                </div>
                <div className="signal-grid">
                  <div className="signal-cell">
                    <small>筛选化合物</small>
                    <strong>{screening.screening_summary?.total_screened}</strong>
                  </div>
                  <div className="signal-cell">
                    <small>命中数量</small>
                    <strong>{screening.screening_summary?.hits_found}</strong>
                  </div>
                  <div className="signal-cell">
                    <small>完成阶段</small>
                    <strong>{screening.screening_summary?.stage_count}</strong>
                  </div>
                </div>
                <div className="program-grid">
                  {(screening.report?.hits || []).map((hit) => (
                    <div key={hit.id} className="program-card">
                      <div className="program-stage">{hit.confidence}</div>
                      <h3>{hit.name}</h3>
                      <p>亲和力 {hit.affinity} kcal/mol</p>
                    </div>
                  ))}
                </div>
              </section>
            )}
            {screeningError && <div className="inline-error">{screeningError}</div>}

            {researchPackage && (
              <section className="result-panel">
                <div className="section-head">
                  <span>研究包</span>
                  <span className="section-note">{researchPackage.package_id}</span>
                </div>
                <p className="summary-text">
                  这不是“一个药名”，而是一套可继续给医生、研究者或合作方使用的结构化资料包。
                </p>
                <div className="signal-grid">
                  <div className="signal-cell">
                    <small>疾病对象</small>
                    <strong>{researchPackage.disease?.name || disease}</strong>
                  </div>
                  <div className="signal-cell">
                    <small>证据层</small>
                    <strong>{researchPackage.evidence_bundle?.length || 0}</strong>
                  </div>
                  <div className="signal-cell">
                    <small>候选层</small>
                    <strong>{researchPackage.repurposing_candidates?.length || 0}</strong>
                  </div>
                  <div className="signal-cell">
                    <small>筛选命中</small>
                    <strong>{researchPackage.screening_summary?.hits_found || 0}</strong>
                  </div>
                </div>

                <div className="bullet-list" style={{ marginTop: 20 }}>
                  {(researchPackage.evidence_bundle || []).map((item) => (
                    <div key={item.evidence_id} className="bullet-row">
                      <Icons.spark />
                      <span>{item.title} · {item.summary}</span>
                    </div>
                  ))}
                </div>

                {(researchPackage.scientific_workflows || []).length > 0 && (
                  <div className="program-grid" style={{ marginTop: 20 }}>
                    {researchPackage.scientific_workflows.slice(0, 3).map((workflow) => (
                      <div key={workflow.title} className="program-card">
                        <div className="program-stage">{workflow.skills.join(' · ')}</div>
                        <h3>{workflow.title}</h3>
                        <p>{workflow.description}</p>
                      </div>
                    ))}
                  </div>
                )}

                {(researchPackage.artifacts || []).length > 0 && (
                  <div className="related-grid" style={{ marginTop: 20 }}>
                    {researchPackage.artifacts.map((artifact) => (
                      <div key={artifact.title} className="related-card">
                        <h3>{artifact.title}</h3>
                        <p>{artifact.description}</p>
                        <p>{artifact.ready ? '已就绪' : '待补条件'} · {artifact.action}</p>
                      </div>
                    ))}
                  </div>
                )}

                <div className="preview-box" style={{ marginTop: 20 }}>
                  <span className="preview-title">下一步动作</span>
                  <pre>{(researchPackage.next_steps || []).join('\n')}</pre>
                </div>
              </section>
            )}
            {packageError && <div className="inline-error">{packageError}</div>}
          </div>
        )}
      </div>
    </div>
  );
}

function CareLoopPage() {
  const [registryId, setRegistryId] = useState(getStoredRegistryId());
  const [stage, setStage] = useState('newly_diagnosed');
  const [note, setNote] = useState('');
  const [symptomsText, setSymptomsText] = useState('');
  const [goals, setGoals] = useState('');
  const [loading, setLoading] = useState(false);
  const [snapshotLoading, setSnapshotLoading] = useState(false);
  const [data, setData] = useState(null);
  const [error, setError] = useState('');

  const applyFollowupPreset = () => {
    const storedId = getStoredRegistryId();
    if (storedId) {
      setRegistryId(storedId);
    }
    setStage('stable_followup');
    setNote('这周已经完成复诊和检查整理，情绪比刚确诊时稳定，正在和家人讨论下一步长期治疗安排。');
    setSymptomsText('近期乏力有所波动，但疼痛频率下降，睡眠较前好转。');
    setGoals('整理复诊资料给医生\n加入同阶段病友圈\n准备下一次治疗沟通重点');
  };

  const loadSnapshot = async (targetId = registryId) => {
    if (!targetId || snapshotLoading) return;
    setSnapshotLoading(true);
    setError('');
    try {
      const payload = await fetchJson(`/api/v1/platform/longitudinal-care/${targetId}`);
      setData(payload);
    } catch (err) {
      setError(err.message);
      setData(null);
    } finally {
      setSnapshotLoading(false);
    }
  };

  const submitUpdate = async () => {
    if (!registryId.trim() || !note.trim() || loading) return;
    setLoading(true);
    setError('');
    try {
      const payload = await fetchJson('/api/v1/platform/longitudinal-care', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          registry_id: registryId,
          current_stage: stage,
          note,
          symptoms_text: symptomsText || null,
          goals: goals.split('\n').map((item) => item.trim()).filter(Boolean),
          update_type: 'follow_up',
        }),
      });
      setData(payload);
      storeRegistryId(registryId);
      setNote('');
      setSymptomsText('');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (registryId) {
      loadSnapshot(registryId);
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div className="utility-page">
      <div className="utility-shell lively-shell theme-care">
        <PageShowcase
          scene="care"
          eyebrow="Longitudinal care loop"
          title="长期管理闭环"
          description="把随访、病友支持、研究回流和阶段目标持续串起来，让患者不是一次诊断后就被丢回空白里。"
          tags={['随访记录', '病友信号', '阶段目标', '研究回流']}
          actions={[
            { label: '填入随访示例', icon: 'activity', onClick: applyFollowupPreset },
            { label: '读取当前闭环', icon: 'file', variant: 'ghost', onClick: () => loadSnapshot(getStoredRegistryId() || registryId) },
          ]}
          highlights={[
            { icon: 'activity', title: '随访事件', text: '把每一次更新都沉淀到长期对象里，不再反复重讲。' },
            { icon: 'users', title: '病友支持', text: '把同阶段病友信号直接带回到长期管理视角。' },
            { icon: 'spark', title: '回流触发', text: '在该回到诊断、研究或登记的时候自动给出提醒。' },
            { icon: 'check', title: '阶段目标', text: '把 7 天和 30 天动作拆给患者和家属。' },
          ]}
          poster={{
            kicker: '随访画布',
            badge: data?.timeline?.length ? '闭环已加载' : '等待随访记录',
            title: data?.patient?.disease || '让长期管理变得可见',
            summary: data?.care_plan?.current_stage
              ? `当前阶段：${data.care_plan.current_stage}。把下一步动作、病友支持和研究回流都收进一个连续对象。`
              : '首页展示陪伴，长期管理页负责把陪伴真正变成时间线、动作和回流机制。',
            bubbles: ['随访', '支持', '研究回流'],
            stats: [
              { label: '时间线事件', value: `${data?.timeline?.length || 0}` },
              { label: '病友信号', value: `${data?.community_signals?.length || 0}` },
              { label: '回流入口', value: `${data?.reentry_routes?.length || 0}` },
            ],
          }}
        />

        <div className="form-panel">
          <div className="field-grid two">
            <label className="field">
              <span>Registry ID</span>
              <input value={registryId} onChange={(event) => setRegistryId(event.target.value)} placeholder="例如：reg_xxxxxxxx" />
            </label>
            <label className="field">
              <span>当前阶段</span>
              <select value={stage} onChange={(event) => setStage(event.target.value)}>
                <option value="newly_diagnosed">新确诊</option>
                <option value="workup">检查中</option>
                <option value="treatment">治疗期</option>
                <option value="stable_followup">稳定随访</option>
                <option value="research_ready">研究准备</option>
              </select>
            </label>
          </div>

          <label className="field">
            <span>本次更新</span>
            <textarea rows={4} value={note} onChange={(event) => setNote(event.target.value)} placeholder="例如：本周完成酶学检测，准备下周复诊，情绪比刚确诊时稳定一些。" />
          </label>

          <label className="field">
            <span>补充症状或病程变化</span>
            <textarea rows={3} value={symptomsText} onChange={(event) => setSymptomsText(event.target.value)} placeholder="例如：最近乏力明显、活动耐量下降、夜间疼痛加重" />
          </label>

          <label className="field">
            <span>当前目标（每行一条）</span>
            <textarea rows={3} value={goals} onChange={(event) => setGoals(event.target.value)} placeholder={'例如：\n把最近检查整理给医生\n找到同阶段病友交流治疗经验'} />
          </label>

          <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
            <button type="button" className="primary-btn" onClick={submitUpdate} disabled={loading || !registryId.trim() || !note.trim()}>
              <Icons.activity />
              <span>{loading ? '写入中' : '记录随访并刷新闭环'}</span>
            </button>
            <button type="button" className="ghost-btn" onClick={() => loadSnapshot()} disabled={snapshotLoading || !registryId.trim()}>
              <Icons.file />
              <span>{snapshotLoading ? '加载中' : '读取当前闭环'}</span>
            </button>
          </div>
          {error && <div className="inline-error">{error}</div>}
        </div>

        {data && (
          <div className="result-stack">
            <section className="result-panel accent">
              <div className="section-head">
                <span>{data.patient?.disease || '患者长期管理对象'}</span>
                <span className="section-note">{data.patient?.patient_code || data.patient?.registry_id}</span>
              </div>
              <p className="summary-text">
                当前阶段：{data.care_plan?.current_stage || '未配置'}。这份对象会把诊断、登记、社群和研究层重新串起来，而不是让患者每次从头讲述。
              </p>
              <div className="tag-row">
                {(data.patient?.phenotypes || []).slice(0, 8).map((item) => (
                  <span key={item} className="phenotype-pill">{item}</span>
                ))}
              </div>
            </section>

            <section className="result-panel">
              <div className="section-head">
                <span>7 天 / 30 天动作</span>
                <span className="section-note">{data.care_plan?.disease_group}</span>
              </div>
              <div className="bullet-list">
                {(data.care_plan?.next_7_days || []).map((item) => (
                  <div key={`7-${item}`} className="bullet-row">
                    <Icons.check />
                    <span>{item}</span>
                  </div>
                ))}
                {(data.care_plan?.next_30_days || []).map((item) => (
                  <div key={`30-${item}`} className="bullet-row">
                    <Icons.spark />
                    <span>{item}</span>
                  </div>
                ))}
              </div>
            </section>

            <section className="result-panel">
              <div className="section-head">
                <span>回流触发条件</span>
              </div>
              <div className="bullet-list">
                {(data.care_plan?.reentry_triggers || []).map((item) => (
                  <div key={item} className="bullet-row">
                    <Icons.activity />
                    <span>{item}</span>
                  </div>
                ))}
              </div>
            </section>

            <section className="result-panel">
              <div className="section-head">
                <span>病友与研究信号</span>
              </div>
              <div className="program-grid">
                {(data.community_signals || []).map((item) => (
                  <div key={item.patient_id} className="program-card">
                    <div className="program-stage">相似度 {Math.round((item.similarity || 0) * 100)}%</div>
                    <h3>{item.disease}</h3>
                    <p>{item.match_reason}</p>
                  </div>
                ))}
              </div>
            </section>

            <section className="result-panel">
              <div className="section-head">
                <span>时间线</span>
              </div>
              <div className="bullet-list">
                {(data.timeline || []).map((event) => (
                  <div key={event.event_id} className="bullet-row">
                    <Icons.file />
                    <span>{event.created_at} · {event.title} · {event.detail}</span>
                  </div>
                ))}
              </div>
            </section>

            {(data.reentry_routes || []).length > 0 && (
              <section className="result-panel">
                <div className="section-head">
                  <span>重新进入其他场景</span>
                </div>
                <div className="related-grid">
                  {data.reentry_routes.map((item) => (
                    <div key={item.scene} className="related-card">
                      <h3>{item.scene}</h3>
                      <p>{item.action}</p>
                    </div>
                  ))}
                </div>
              </section>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function PlatformControlPage() {
  const [data, setData] = useState(null);
  const [error, setError] = useState('');
  const [adminToken, setAdminToken] = useState('');
  const [switching, setSwitching] = useState('');

  const loadControlPlane = async () => {
    const [objectModel, templates, governance, evaluation, avatarRuntime] = await Promise.all([
      fetchJson('/api/v1/platform/object-model'),
      fetchJson('/api/v1/platform/disease-group-templates'),
      fetchJson('/api/v1/platform/governance'),
      fetchJson('/api/v1/platform/evaluation'),
      fetchJson('/api/v1/platform/avatar-runtime'),
    ]);
    return { objectModel, templates, governance, evaluation, avatarRuntime };
  };

  useEffect(() => {
    let cancelled = false;
    try {
      const savedToken = window.sessionStorage.getItem('medichat_admin_token') || '';
      if (savedToken) {
        setAdminToken(savedToken);
      }
    } catch (storageError) {
      console.error(storageError);
    }

    loadControlPlane()
      .then((nextData) => {
        if (!cancelled) {
          setData(nextData);
        }
      })
      .catch((err) => {
        if (!cancelled) setError(err.message);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const handleRuntimeSwitch = async (primaryProvider, fallbackProvider) => {
    setSwitching(primaryProvider);
    try {
      const runtimeResponse = await fetchJson('/api/v1/platform/avatar-runtime', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(adminToken ? { 'X-Admin-Token': adminToken } : {}),
        },
        body: JSON.stringify({
          primary_provider: primaryProvider,
          fallback_provider: fallbackProvider,
        }),
      });
      const nextData = await loadControlPlane();
      setData({ ...nextData, avatarRuntime: runtimeResponse });
      setError('');
      try {
        window.sessionStorage.setItem('medichat_admin_token', adminToken);
      } catch (storageError) {
        console.error(storageError);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setSwitching('');
    }
  };

  return (
    <div className="utility-page">
      <div className="utility-shell lively-shell theme-governance">
        <PageShowcase
          scene="governance"
          eyebrow="Platform contracts, governance and evaluation"
          title="治理与评估"
          description="把统一对象模型、病组模板、合规边界和跨场景 KPI 直接摆在台面上，让平台不仅好看，也真正可控、可审计、可持续扩展。"
          tags={['对象模型', '病组模板', '治理边界', '跨场景 KPI']}
          highlights={[
            { icon: 'file', title: '统一对象', text: '让患者、疾病、变异、研究包和社群对象都遵循同一套平台契约。' },
            { icon: 'dna', title: '病组模板', text: '把病种差异落成可复用的随访和检查模板，而不是靠人工记忆。' },
            { icon: 'check', title: '治理边界', text: '把合规、审计和敏感数据边界做成真实的控制面。' },
            { icon: 'activity', title: '成熟度评估', text: '持续看到各条业务链当前做到了哪里，还差什么。' },
          ]}
          poster={{
            kicker: '控制平面',
            badge: data ? '治理数据已加载' : '等待平台快照',
            title: data?.evaluation?.overall_maturity || '把平台规则可视化',
            summary: '患者端的温暖体验需要有坚实的治理底座支撑，这个页面负责把底座直接展示出来。',
            bubbles: ['对象模型', '模板', 'KPI'],
            stats: [
              { label: '核心对象', value: `${data?.objectModel?.objects?.length || 0}` },
              { label: '病组模板', value: `${data?.templates?.count || 0}` },
              { label: '场景得分', value: `${data?.evaluation?.scene_scores?.length || 0}` },
            ],
          }}
        />

        {data && (
          <div className="result-stack">
            <section className="result-panel accent">
              <div className="section-head">
                <span>统一对象模型</span>
                <span className="section-note">{data.objectModel.objects?.length || 0} 类核心对象</span>
              </div>
              <div className="related-grid">
                {(data.objectModel.objects || []).map((item) => (
                  <div key={item.slug} className="related-card">
                    <h3>{item.title}</h3>
                    <p>{item.description}</p>
                    <p>{item.fields.join(' / ')}</p>
                  </div>
                ))}
              </div>
            </section>

            <section className="result-panel">
              <div className="section-head">
                <span>病组模板</span>
                <span className="section-note">{data.templates.count} 个模板</span>
              </div>
              <div className="program-grid">
                {(data.templates.templates || []).map((template) => (
                  <div key={template.template_id} className="program-card">
                    <div className="program-stage">{template.follow_up_schedule}</div>
                    <h3>{template.title}</h3>
                    <p>优先基因：{template.priority_genes.join(' / ') || '待补充'}</p>
                    <p>建议检查：{template.recommended_tests.join(' / ')}</p>
                  </div>
                ))}
              </div>
            </section>

            <section className="result-panel">
              <div className="section-head">
                <span>治理边界</span>
              </div>
              <div className="bullet-list">
                {(data.governance.safeguards || []).map((item) => (
                  <div key={item} className="bullet-row">
                    <Icons.check />
                    <span>{item}</span>
                  </div>
                ))}
              </div>
              <div className="signal-grid" style={{ marginTop: 20 }}>
                <div className="signal-cell">
                  <small>数据分类</small>
                  <strong>{(data.governance.data_classification || []).join(' / ')}</strong>
                </div>
                <div className="signal-cell">
                  <small>审计事件</small>
                  <strong>{data.governance.audit?.event_count || 0}</strong>
                </div>
                <div className="signal-cell">
                  <small>运行时治理</small>
                  <strong>{data.governance.runtime_split?.scientific_runtime?.state || 'unknown'}</strong>
                </div>
                <div className="signal-cell">
                  <small>分身主运行时</small>
                  <strong>{data.avatarRuntime?.runtime?.primary_provider || 'local'}</strong>
                </div>
                <div className="signal-cell">
                  <small>登记样本</small>
                  <strong>{data.governance.registry_snapshot?.total_patients || 0}</strong>
                </div>
              </div>
            </section>

            <AvatarRuntimeAdminSection
              runtime={data.avatarRuntime?.runtime}
              adminToken={adminToken}
              switching={switching}
              onAdminTokenChange={setAdminToken}
              onSwitch={handleRuntimeSwitch}
            />

            <section className="result-panel">
              <div className="section-head">
                <span>跨场景评估</span>
                <span className="section-note">{data.evaluation.overall_maturity}</span>
              </div>
              <div className="program-grid">
                {(data.evaluation.scene_scores || []).map((scene) => (
                  <div key={scene.scene} className="program-card">
                    <div className="program-stage">{scene.maturity}</div>
                    <h3>{scene.title}</h3>
                    <p>综合得分：{scene.score}</p>
                    <p>{Object.entries(scene.metrics || {}).map(([key, value]) => `${key}=${value}`).join(' · ')}</p>
                  </div>
                ))}
              </div>
            </section>

            <section className="result-panel">
              <div className="section-head">
                <span>标准对齐</span>
              </div>
              <div className="related-grid">
                {(data.objectModel.standards_alignment || []).map((item) => (
                  <div key={item.standard} className="related-card">
                    <h3>{item.standard}</h3>
                    <p>{item.scope} · {item.status}</p>
                    <p>{item.implementation}</p>
                  </div>
                ))}
              </div>
            </section>
          </div>
        )}

        {error && <div className="inline-error">{error}</div>}
      </div>
    </div>
  );
}

function AvatarRuntimeAdminSection({
  runtime,
  adminToken,
  switching,
  onAdminTokenChange,
  onSwitch,
}) {
  const providers = runtime?.providers || [];
  const switchEnabled = Boolean(runtime?.switch_enabled);
  const primaryProvider = runtime?.primary_provider;
  const fallbackProvider = runtime?.fallback_provider;

  return (
    <section className="result-panel accent">
      <div className="section-head">
        <span>分身 Runtime 控制面</span>
        <span className="section-note">
          {primaryProvider ? `${primaryProvider} → ${fallbackProvider}` : '等待运行时快照'}
        </span>
      </div>

      <div className="signal-grid">
        <div className="signal-cell">
          <small>Primary</small>
          <strong>{primaryProvider || 'unknown'}</strong>
        </div>
        <div className="signal-cell">
          <small>Fallback</small>
          <strong>{fallbackProvider || 'unknown'}</strong>
        </div>
        <div className="signal-cell">
          <small>已创建分身</small>
          <strong>{runtime?.avatars_count || 0}</strong>
        </div>
        <div className="signal-cell">
          <small>后台切换</small>
          <strong>{switchEnabled ? '已开启' : '未配置口令'}</strong>
        </div>
      </div>

      <div className="related-grid" style={{ marginTop: 20 }}>
        {providers.map((provider) => (
          <div key={provider.key} className="related-card">
            <h3>{provider.label}</h3>
            <p>{provider.description}</p>
            <p>
              健康状态：{provider.healthy ? 'healthy' : 'offline'}
              {' · '}
              {provider.is_primary ? '当前主运行时' : provider.is_fallback ? '当前兜底运行时' : '备用'}
            </p>
            <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginTop: 14 }}>
              <button
                type="button"
                className="hero-action primary"
                disabled={!switchEnabled || switching === provider.key}
                onClick={() => onSwitch(provider.key, provider.key === 'local' ? 'local' : 'local')}
              >
                {switching === provider.key ? '切换中...' : `切到 ${provider.label}`}
              </button>
            </div>
          </div>
        ))}
      </div>

      <div style={{ marginTop: 20 }}>
        <label style={{ display: 'block', fontSize: 13, fontWeight: 700, color: '#0C1831', marginBottom: 8 }}>
          后台切换口令
        </label>
        <input
          type="password"
          value={adminToken}
          onChange={(event) => onAdminTokenChange(event.target.value)}
          placeholder={switchEnabled ? '输入 PLATFORM_ADMIN_TOKEN' : '服务端尚未配置 PLATFORM_ADMIN_TOKEN'}
          autoComplete="off"
          style={{
            width: '100%',
            borderRadius: 16,
            border: '1px solid rgba(12,24,49,0.12)',
            padding: '12px 14px',
            fontSize: 14,
            color: '#0C1831',
            background: 'rgba(255,255,255,0.88)',
          }}
        />
        <div className="section-note" style={{ marginTop: 10 }}>
          这个口令只保存在当前浏览器 sessionStorage，用于调用运行时切换 API，不会写进仓库。
        </div>
      </div>
    </section>
  );
}

function App() {
  const [page, setPage] = useState('community');
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [pageFocusPulse, setPageFocusPulse] = useState(false);
  const [pageFocusLabel, setPageFocusLabel] = useState('');
  const mainContentRef = useRef(null);
  const isFirstRender = useRef(true);

  const navItems = [
    { id: 'community', label: '互助社群', icon: 'users' },
    { id: 'hub', label: '患者中枢', icon: 'home' },
    { id: 'deeprare', label: 'DeepRare 诊断', icon: 'brain' },
    { id: 'doctor', label: '医生助手', icon: 'activity' },
    { id: 'ai-chat', label: 'AI 陪诊', icon: 'chat' },
    { id: 'symptom-check', label: '症状筛查', icon: 'search' },
    { id: 'genomic-hub', label: '基因与登记', icon: 'dna' },
    { id: 'care-loop', label: '长期管理', icon: 'activity' },
    { id: 'scientific-skills', label: '科研加速', icon: 'spark' },
    { id: 'disease-research', label: '疾病研究', icon: 'file' },
    { id: 'drug-research', label: '药物线索', icon: 'pill' },
    { id: 'platform-ops', label: '治理评估', icon: 'check' },
  ];

  const scrollToActiveModule = () => {
    if (typeof window === 'undefined') return;
    const targetTop = mainContentRef.current
      ? window.scrollY + mainContentRef.current.getBoundingClientRect().top - 10
      : 0;
    window.scrollTo({
      top: Math.max(0, targetTop),
      behavior: 'smooth',
    });
  };

  const triggerPageFocus = (pageId) => {
    const guide = PAGE_GUIDE[pageId] || PAGE_GUIDE.hub;
    setPageFocusLabel(guide.title);
    setPageFocusPulse(false);
    requestAnimationFrame(() => {
      setPageFocusPulse(true);
      scrollToActiveModule();
    });
  };

  useEffect(() => {
    if (isFirstRender.current) {
      isFirstRender.current = false;
      return;
    }
    triggerPageFocus(page);
  }, [page]);

  useEffect(() => {
    if (!pageFocusPulse) return undefined;
    const timeout = window.setTimeout(() => setPageFocusPulse(false), 920);
    return () => window.clearTimeout(timeout);
  }, [pageFocusPulse]);

  const handleNavigate = (nextPage) => {
    setSidebarOpen(false);
    if (nextPage === page) {
      triggerPageFocus(nextPage);
      return;
    }
    setPage(nextPage);
  };

  const renderPage = () => {
    switch (page) {
      case 'deeprare':
        return <DeepRarePanel />;
      case 'community':
        return <CommunityPanel onNavigate={handleNavigate} />;
      case 'doctor':
        return <DoctorPanel />;
      case 'ai-chat':
        return <AIChatPage />;
      case 'symptom-check':
        return <SymptomCheckPage />;
      case 'genomic-hub':
        return <GenomicHubPage />;
      case 'care-loop':
        return <CareLoopPage />;
      case 'scientific-skills':
        return <ScientificSkillsPage onNavigate={handleNavigate} />;
      case 'disease-research':
        return <DiseaseResearchPage />;
      case 'drug-research':
        return <DrugResearchPage />;
      case 'platform-ops':
        return <PlatformControlPage />;
      default:
        return <HomePage onNavigate={handleNavigate} />;
    }
  };

  return (
    <div className="app-shell">
      <div className="ambient ambient-one" />
      <div className="ambient ambient-two" />

      <header className="topnav">
        <button type="button" className="menu-btn" onClick={() => setSidebarOpen((value) => !value)}>
          {sidebarOpen ? <Icons.close /> : <Icons.menu />}
        </button>
        <button type="button" className="nav-brand" onClick={() => handleNavigate('community')}>
          <Icons.dna />
          <div>
            <span>MediChat-RD</span>
            <small>SecondMe patient platform</small>
          </div>
        </button>
        <button type="button" className="nav-cta" onClick={() => handleNavigate('deeprare')}>
          <Icons.brain />
          <span>开始 DeepRare</span>
        </button>
      </header>

      <aside className={`sidebar ${sidebarOpen ? 'open' : ''}`}>
        {navItems.map((item) => {
          const Icon = Icons[item.icon];
          return (
            <button
              key={item.id}
              type="button"
              className={`nav-item ${page === item.id ? 'active' : ''}`}
              onClick={() => handleNavigate(item.id)}
            >
              <Icon />
              <span>{item.label}</span>
            </button>
          );
        })}
      </aside>

      <main ref={mainContentRef} className="main-content">
        <PageTitleRail page={page} navItems={navItems} onNavigate={handleNavigate} />
        <div className={`page-module-shell ${pageFocusPulse ? 'page-module-shell-highlight' : ''}`}>
          {pageFocusLabel && pageFocusPulse && (
            <div className="page-module-toast" aria-live="polite">
              已定位到 {pageFocusLabel}
            </div>
          )}
          {renderPage()}
        </div>
      </main>
    </div>
  );
}

export default App;
