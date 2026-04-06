import React, { useEffect, useMemo, useState } from 'react';

const STORY_SCENES = [
  {
    id: 'welcome',
    chapter: '01',
    label: '新确诊的夜晚',
    title: '先让一个家庭被接住，再让产品开始工作',
    summary:
      '妈妈抱着孩子和一摞检查单，最先需要的不是更多术语，而是一个愿意慢下来、陪她把病历和情绪放进同一条线里的入口。',
    voice:
      '“今晚不用把所有结果都看懂，我们先把最重要的症状、检查和情绪整理出来，明天就不会再乱。”',
    tags: ['欢迎房', '病历整理', '情绪安放'],
    kicker: '今晚 20:00 · 新确诊患者欢迎房',
    cta: { label: '进入欢迎房', kind: 'welcome' },
    secondaryCta: { label: '打开患者中枢', kind: 'page', target: 'hub' },
  },
  {
    id: 'hub',
    chapter: '02',
    label: '把慌张变成路径',
    title: '患者中枢把病历、检查、症状和下一步安排成可执行旅程',
    summary:
      '患者不用在多个页面里来回找入口，平台会把今天最该做的事排在眼前，从登记、就诊、到病程整理都能顺着走。',
    voice:
      '“你现在最重要的是先把检查、主要不舒服和想问医生的问题放进同一页里。”',
    tags: ['患者中枢', '旅程总览', '一页进入'],
    kicker: '今天的第一条路径',
    cta: { label: '查看患者中枢', kind: 'page', target: 'hub' },
    secondaryCta: { label: '去做症状筛查', kind: 'page', target: 'symptom-check' },
  },
  {
    id: 'deeprare',
    chapter: '03',
    label: '诊断不再散乱',
    title: 'DeepRare 把零散的描述整理成候选诊断和下一步检查',
    summary:
      '患者只要讲出自己的感受，系统就能把症状、HPO 表型、候选疾病和建议检查放成一条看得懂的推理链。',
    voice:
      '“先把孩子最近三个月最明显的变化说出来，我来帮你把症状翻译成医生能直接继续用的信息。”',
    tags: ['DeepRare', 'HPO 表型', '检查建议'],
    kicker: 'DeepRare 诊断工作台',
    cta: { label: '打开 DeepRare', kind: 'page', target: 'deeprare' },
    secondaryCta: { label: '查看疾病研究', kind: 'page', target: 'disease-research' },
  },
  {
    id: 'avatar',
    chapter: '04',
    label: '让分身替你开口',
    title: 'SecondMe 分身把患者身份、病程和第一条动态连接在一起',
    summary:
      '授权、建分身、写第一条动态，平台会帮患者先把“我是谁、我现在最需要什么帮助”说得更真、更稳。',
    voice:
      '“我不是来发一段标准答案，我只是想问问，有没有人也经历过同样的骨痛和检查等待。”',
    tags: ['SecondMe', 'AI 分身', '首条动态'],
    kicker: '人格卡与首帖草稿',
    cta: { label: '去创建分身', kind: 'page', target: 'community' },
    secondaryCta: { label: '连接 SecondMe', kind: 'page', target: 'platform-ops' },
  },
  {
    id: 'community',
    chapter: '05',
    label: '让病友真正说上话',
    title: '欢迎房、家长圆桌和试验追踪，把支持、经验和机会聚到一个现场',
    summary:
      '患者和家属可以从欢迎房走进病友圈，从提问走向回应，再从回应走到临床试验和长期支持。',
    voice:
      '“有人真的回我了，也有人告诉我检查前一天怎么准备，感觉终于不是自己一个人了。”',
    tags: ['病友圈', 'Live rooms', '临床试验机会'],
    kicker: '公开社群现场',
    cta: { label: '进入互助社群', kind: 'page', target: 'community' },
    secondaryCta: { label: '查看药物线索', kind: 'page', target: 'drug-research' },
  },
  {
    id: 'followup',
    chapter: '06',
    label: '陪伴留到日常里',
    title: '陪伴玩偶和语音随访设备，让长期管理变得更温柔',
    summary:
      '孩子可以和玩偶说今天哪里不舒服，家属可以用语音随访盒记录变化，平台则把这些细碎的感受接回长期管理。',
    voice:
      '“它每天都提醒我说一句今天的感受，原来随访也可以不是一件压抑的事情。”',
    tags: ['陪伴硬件', '语音随访', '长期管理'],
    kicker: '陪伴与随访闭环',
    cta: { label: '打开长期管理', kind: 'page', target: 'care-loop' },
    secondaryCta: { label: '体验语音陪诊', kind: 'voice' },
  },
];

function StoryStat({ label, value, tone = 'warm' }) {
  return (
    <div className={`cinematic-demo-stat tone-${tone}`}>
      <small>{label}</small>
      <strong>{value}</strong>
    </div>
  );
}

function StoryActionButton({ action, variant = 'primary', onAction }) {
  if (!action) return null;
  return (
    <button
      type="button"
      className={`cinematic-demo-btn ${variant}`}
      onClick={() => onAction(action)}
    >
      {action.label}
    </button>
  );
}

function WelcomeScene() {
  return (
    <div className="cinematic-scene cinematic-scene-welcome">
      <div className="cinematic-scene-sky">
        <span className="scene-moon" />
        <span className="scene-star star-a" />
        <span className="scene-star star-b" />
        <span className="scene-star star-c" />
      </div>
      <div className="cinematic-family-group">
        <div className="cinematic-person mom">
          <span className="head" />
          <span className="body" />
        </div>
        <div className="cinematic-person child">
          <span className="head" />
          <span className="body" />
        </div>
        <div className="cinematic-plush cinematic-plush-bear" />
      </div>
      <div className="cinematic-bubble welcome-bubble">先整理病历、检查和情绪</div>
      <div className="cinematic-scene-card welcome-card">
        <span>新确诊患者欢迎房</span>
        <strong>病历清单 + 情绪支持 + 下一步提醒</strong>
      </div>
      <div className="cinematic-scene-note">把今晚最乱的几件事，先放进一条线里</div>
    </div>
  );
}

function HubScene() {
  return (
    <div className="cinematic-scene cinematic-scene-hub">
      <div className="cinematic-hub-board">
        <div className="hub-window">
          <span className="hub-dot coral" />
          <span className="hub-dot mint" />
          <span className="hub-dot gold" />
        </div>
        <div className="hub-grid">
          <div className="hub-panel timeline">
            <strong>今天的患者旅程</strong>
            <span>病历整理</span>
            <span>症状结构化</span>
            <span>病友支持入口</span>
          </div>
          <div className="hub-panel records">
            <strong>检查与病程</strong>
            <span>骨痛加重</span>
            <span>脾大 / 贫血</span>
            <span>待确认基因</span>
          </div>
          <div className="hub-panel focus">
            <strong>今天最重要</strong>
            <span>问医生 3 个问题</span>
          </div>
        </div>
      </div>
      <div className="cinematic-mini-card hub-mini-card">患者中枢把多个入口收成一页</div>
    </div>
  );
}

function DeepRareScene() {
  return (
    <div className="cinematic-scene cinematic-scene-deeprare">
      <div className="deeprare-console">
        <div className="deeprare-console-bar">
          <span>DeepRare AI</span>
          <span className="deeprare-pulse" />
        </div>
        <div className="deeprare-console-body">
          <div className="deeprare-chip-row">
            <span>脾大</span>
            <span>骨痛</span>
            <span>贫血</span>
            <span>乏力</span>
          </div>
          <div className="deeprare-candidate-list">
            <div className="candidate active">
              <strong>戈谢病</strong>
              <small>GBA · 溶酶体病</small>
            </div>
            <div className="candidate">
              <strong>法布雷病</strong>
              <small>GLA · 鉴别诊断</small>
            </div>
          </div>
          <div className="deeprare-hpo-card">
            <span>HPO</span>
            <strong>脾肿大 / 骨痛 / 血红蛋白下降</strong>
          </div>
        </div>
      </div>
      <div className="cinematic-bubble deeprare-bubble">从自然语言到候选诊断和检查建议</div>
    </div>
  );
}

function AvatarScene() {
  return (
    <div className="cinematic-scene cinematic-scene-avatar">
      <div className="avatar-orbital">
        <div className="avatar-ring ring-a" />
        <div className="avatar-ring ring-b" />
        <div className="avatar-core">
          <span>SecondMe</span>
          <strong>患者分身</strong>
        </div>
      </div>
      <div className="avatar-profile-card">
        <small>分身资料卡</small>
        <strong>小羽 · 戈谢病</strong>
        <span>想先找到有类似骨痛经历的病友</span>
      </div>
      <div className="avatar-post-card">
        <small>首条动态草稿</small>
        <strong>有没有人在等基因结果时也这样焦虑过？</strong>
      </div>
    </div>
  );
}

function CommunityScene() {
  return (
    <div className="cinematic-scene cinematic-scene-community">
      <div className="community-stage">
        <div className="community-live-sign">Live rooms</div>
        <div className="community-room-card newcomer">
          <strong>欢迎房</strong>
          <span>第一周先整理病历和情绪</span>
        </div>
        <div className="community-room-card parents">
          <strong>家长圆桌</strong>
          <span>营养、学校和长期依从性</span>
        </div>
        <div className="community-room-card trials">
          <strong>临床试验机会</strong>
          <span>新药动态与入组准备</span>
        </div>
      </div>
      <div className="community-bridge-lines">
        <span className="bridge-node node-a" />
        <span className="bridge-node node-b" />
        <span className="bridge-node node-c" />
      </div>
    </div>
  );
}

function FollowupScene() {
  return (
    <div className="cinematic-scene cinematic-scene-followup">
      <div className="followup-plush-row">
        <div className="followup-toy bear" />
        <div className="followup-toy rabbit" />
        <div className="followup-toy fox" />
      </div>
      <div className="followup-device">
        <div className="followup-screen">
          <span>语音随访中</span>
          <strong>今天哪里不舒服？</strong>
        </div>
        <div className="followup-wave wave-a" />
        <div className="followup-wave wave-b" />
      </div>
      <div className="followup-timeline">
        <span>每日打卡</span>
        <span>复诊提醒</span>
        <span>长期管理</span>
      </div>
    </div>
  );
}

function renderScene(sceneId) {
  switch (sceneId) {
    case 'welcome':
      return <WelcomeScene />;
    case 'hub':
      return <HubScene />;
    case 'deeprare':
      return <DeepRareScene />;
    case 'avatar':
      return <AvatarScene />;
    case 'community':
      return <CommunityScene />;
    case 'followup':
      return <FollowupScene />;
    default:
      return null;
  }
}

export default function CinematicDemoSection({
  onNavigate,
  onOpenWelcomeRoom,
  onOpenVoiceFollowup,
}) {
  const [activeIndex, setActiveIndex] = useState(0);
  const [paused, setPaused] = useState(false);

  useEffect(() => {
    if (paused) return undefined;
    const timerId = window.setInterval(() => {
      setActiveIndex((current) => (current + 1) % STORY_SCENES.length);
    }, 5200);
    return () => window.clearInterval(timerId);
  }, [paused]);

  const activeScene = useMemo(() => STORY_SCENES[activeIndex], [activeIndex]);

  const handleAction = (action) => {
    if (!action) return;
    if (action.kind === 'page') {
      onNavigate?.(action.target);
      return;
    }
    if (action.kind === 'welcome') {
      onOpenWelcomeRoom?.({ id: 'room_newcomer' });
      return;
    }
    if (action.kind === 'voice') {
      onOpenVoiceFollowup?.();
    }
  };

  return (
    <section className="cinematic-demo-section">
      <div className="cinematic-demo-copy">
        <div className="cinematic-demo-kicker">Homepage demo film</div>
        <h2>用一段会自己讲故事的动画，把产品的温度和能力一起放进首页</h2>
        <p>
          这不是一块静态海报，而是一段自动播放的产品剧情。患者和家属一进来，就能看懂从欢迎房、患者中枢、
          DeepRare、SecondMe 分身到长期随访的整条路径。
        </p>

        <div className="cinematic-demo-meta">
          <StoryStat label="故事章节" value={`${STORY_SCENES.length} 段`} tone="warm" />
          <StoryStat label="默认节奏" value="5.2 秒 / 段" tone="mint" />
          <StoryStat label="体现能力" value="欢迎房 + 分身 + 诊断 + 随访" tone="sky" />
        </div>

        <div className="cinematic-demo-storyline">
          <span className="cinematic-demo-chapter">Chapter {activeScene.chapter}</span>
          <strong>{activeScene.label}</strong>
          <h3>{activeScene.title}</h3>
          <p>{activeScene.summary}</p>
          <blockquote>{activeScene.voice}</blockquote>
        </div>

        <div className="cinematic-demo-tags">
          {activeScene.tags.map((tag) => (
            <span key={tag}>{tag}</span>
          ))}
        </div>

        <div className="cinematic-demo-actions">
          <StoryActionButton action={activeScene.cta} onAction={handleAction} />
          <StoryActionButton action={activeScene.secondaryCta} variant="ghost" onAction={handleAction} />
        </div>
      </div>

      <div
        className="cinematic-demo-stage"
        onMouseEnter={() => setPaused(true)}
        onMouseLeave={() => setPaused(false)}
      >
        <div className="cinematic-demo-frame">
          <div className="cinematic-demo-frame-bar">
            <div className="cinematic-demo-frame-badge">
              <span className="record-dot" />
              <strong>首页剧情 Demo</strong>
            </div>
            <span>{paused ? '已暂停 · 悬停查看' : '自动播放中'}</span>
          </div>

          <div className="cinematic-demo-progress">
            {STORY_SCENES.map((scene, index) => (
              <button
                key={scene.id}
                type="button"
                className={`cinematic-progress-segment ${index === activeIndex ? 'active' : index < activeIndex ? 'past' : ''}`}
                onClick={() => setActiveIndex(index)}
                aria-label={`切换到${scene.label}`}
              />
            ))}
          </div>

          <div key={activeScene.id} className={`cinematic-scene-shell scene-${activeScene.id}`}>
            <div className="cinematic-scene-overlay">
              <span>{activeScene.kicker}</span>
              <strong>{activeScene.title}</strong>
            </div>
            {renderScene(activeScene.id)}
          </div>
        </div>

        <div className="cinematic-demo-rail">
          {STORY_SCENES.map((scene, index) => (
            <button
              key={scene.id}
              type="button"
              className={`cinematic-demo-rail-item ${index === activeIndex ? 'active' : ''}`}
              onClick={() => setActiveIndex(index)}
            >
              <small>{scene.chapter}</small>
              <strong>{scene.label}</strong>
              <span>{scene.kicker}</span>
            </button>
          ))}
        </div>
      </div>
    </section>
  );
}
