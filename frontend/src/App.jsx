import React, { useState, useRef, useEffect } from 'react';
import './App.css';

// ========== 数据 ==========
const DISEASES = [
  { name: '戈谢病', icon: '🫁', icd: 'E75.22', type: '溶酶体贮积症', gene: 'GBA', rate: '1/50,000', symptoms: ['脾脏肿大','骨痛','血小板减少','贫血','生长迟缓'] },
  { name: '庞贝病', icon: '💪', icd: 'E74.02', type: '糖原贮积症', gene: 'GAA', rate: '1/40,000', symptoms: ['肌无力','呼吸困难','心脏肥大','运动发育迟缓'] },
  { name: '法布雷病', icon: '🔥', icd: 'E75.21', type: '溶酶体贮积症', gene: 'GLA', rate: '1/40,000', symptoms: ['肢端疼痛','少汗','肾功能异常','心肌肥厚'] },
  { name: '渐冻症', icon: '🧊', icd: 'G12.21', type: '运动神经元病', gene: 'SOD1', rate: '1/50,000', symptoms: ['肌肉萎缩','肌无力','吞咽困难','言语不清'] },
  { name: '血友病', icon: '🩸', icd: 'D66/D67', type: '凝血障碍', gene: 'F8/F9', rate: '1/10,000', symptoms: ['出血不止','关节血肿','术后出血','牙龈出血'] },
  { name: '多发性硬化', icon: '🧠', icd: 'G35', type: '自身免疫', gene: '多基因', rate: '1/2,000', symptoms: ['视力下降','肢体麻木','行走困难','疲劳'] },
  { name: '白化病', icon: '👤', icd: 'E70.3', type: '遗传代谢', gene: 'TYR', rate: '1/20,000', symptoms: ['皮肤白化','视力下降','眼球震颤','畏光'] },
  { name: '苯丙酮尿症', icon: '🧪', icd: 'E70.0', type: '氨基酸代谢', gene: 'PAH', rate: '1/10,000', symptoms: ['智力障碍','发育迟缓','湿疹','尿液异味'] },
];

const DISEASE_CATEGORIES = [
  { icon: '🧬', label: '遗传病', count: 45 },
  { icon: '⚗️', label: '代谢病', count: 32 },
  { icon: '🧠', label: '神经系统', count: 18 },
  { icon: '🛡️', label: '免疫病', count: 12 },
  { icon: '🩸', label: '血液病', count: 8 },
  { icon: '❤️', label: '心血管', count: 6 },
  { icon: '🦴', label: '骨骼病', count: 5 },
  { icon: '👁️', label: '眼科病', count: 4 },
];

const DOCTORS = {
  triage: { name: '陈雅琴', title: '副主任医师', dept: '急诊医学科', hospital: '协和医院', color: '#2563EB' },
  diagnosis: { name: '王建国', title: '主任医师', dept: '内科', hospital: '协和医院', color: '#10B981' },
  medicine: { name: '李明辉', title: '主任药师', dept: '药学部', hospital: '协和医院', color: '#F59E0B' },
  mental: { name: '赵晓燕', title: '副主任医师', dept: '心理科', hospital: '北大六院', color: '#8B5CF6' },
  rehab: { name: '林雨桐', title: '康复医师', dept: '康复医学科', hospital: '博爱医院', color: '#EC4899' },
  followup: { name: '刘志强', title: '全科医师', dept: '全科医学科', hospital: '协和医院', color: '#06B6D4' },
};

const COMMUNITIES = [
  { icon: '🫁', name: '戈谢病互助群', count: 2341, activity: '127条新消息' },
  { icon: '💪', name: '庞贝病交流群', count: 1856, activity: '89条新消息' },
  { icon: '🔥', name: '法布雷病关爱群', count: 987, activity: '45条新消息' },
  { icon: '🧊', name: '渐冻症关怀群', count: 3456, activity: '234条新消息' },
  { icon: '🧠', name: '罕见神经疾病群', count: 4567, activity: '312条新消息' },
  { icon: '🏃', name: '运动与康复', count: 5678, activity: '567条新消息' },
  { icon: '🧘', name: '心理健康互助', count: 3456, activity: '189条新消息' },
  { icon: '🥗', name: '营养与饮食', count: 2345, activity: '98条新消息' },
];

// ========== 组件 ==========
function TopBar() {
  return (
    <div className="top-bar">
      <div className="logo">
        <div className="logo-icon">🧬</div>
        <div>
          <div>MediChat-RD</div>
          <div className="subtitle">罕见病AI诊疗平台</div>
        </div>
      </div>
    </div>
  );
}

function TabBar({ active, onChange }) {
  const tabs = [
    { key: 'home', icon: '🏠', label: '首页' },
    { key: 'consult', icon: '💬', label: '问诊' },
    { key: 'knowledge', icon: '📚', label: '知识' },
    { key: 'community', icon: '👥', label: '社群' },
    { key: 'profile', icon: '👤', label: '我的' },
  ];
  return (
    <div className="tab-bar">
      {tabs.map(t => (
        <button key={t.key} className={`tab-item ${active === t.key ? 'active' : ''}`} onClick={() => onChange(t.key)}>
          <span className="tab-icon">{t.icon}</span>
          <span className="tab-label">{t.label}</span>
        </button>
      ))}
    </div>
  );
}

// ===== 首页 =====
function HomePage({ onNavigate }) {
  return (
    <div className="page">
      <div className="hero-banner">
        <h2>🧬 4C 诊疗体系</h2>
        <p>Connect → Consult → Care → Community</p>
      </div>
      <div className="grid-4c">
        <div className="c-card connect" onClick={() => onNavigate('consult')}>
          <span className="c-icon">🔍</span>
          <div className="c-title">智能分诊</div>
          <div className="c-desc">症状初筛，匹配专科</div>
        </div>
        <div className="c-card consult" onClick={() => onNavigate('consult')}>
          <span className="c-icon">💬</span>
          <div className="c-title">AI问诊</div>
          <div className="c-desc">6个专科Agent在线</div>
        </div>
        <div className="c-card care" onClick={() => onNavigate('knowledge')}>
          <span className="c-icon">📋</span>
          <div className="c-title">全程照护</div>
          <div className="c-desc">随访管理·用药提醒</div>
        </div>
        <div className="c-card community" onClick={() => onNavigate('community')}>
          <span className="c-icon">👥</span>
          <div className="c-title">患者社群</div>
          <div className="c-desc">数字分身·病友互助</div>
        </div>
      </div>
      <div className="stat-bar">
        <div className="stat-item">
          <div className="stat-num">121</div>
          <div className="stat-label">罕见病种</div>
        </div>
        <div className="stat-item">
          <div className="stat-num">6</div>
          <div className="stat-label">专科Agent</div>
        </div>
        <div className="stat-item">
          <div className="stat-num">2000万</div>
          <div className="stat-label">覆盖患者</div>
        </div>
      </div>
      <div className="card">
        <div className="card-header">
          <span className="card-title">🏷️ 疾病分类</span>
          <button className="card-more" onClick={() => onNavigate('knowledge')}>查看全部 →</button>
        </div>
        <div className="disease-grid">
          {DISEASE_CATEGORIES.slice(0, 4).map((cat, i) => (
            <div key={i} className="disease-chip" onClick={() => onNavigate('knowledge')}>
              <span className="chip-icon">{cat.icon}</span>
              <span className="chip-label">{cat.label}</span>
              <span className="chip-count">{cat.count}种</span>
            </div>
          ))}
        </div>
      </div>
      <div className="card">
        <div className="card-header">
          <span className="card-title">⚡ 快捷问诊</span>
        </div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
          {['头痛', '发热', '咳嗽', '腹痛', '关节痛', '疲劳', '皮疹', '视力下降'].map(s => (
            <button key={s} className="quick-chip" onClick={() => onNavigate('consult', s)}>{s}</button>
          ))}
        </div>
      </div>
      <div className="insurance-card">
        <h4>💊 罕见病用药医保</h4>
        <div className="ins-grid">
          <div className="ins-item"><div className="label">目录内药物</div><div className="value">45种</div></div>
          <div className="ins-item"><div className="label">各省覆盖</div><div className="value">31省市</div></div>
          <div className="ins-item"><div className="label">平均报销比</div><div className="value">70%</div></div>
          <div className="ins-item"><div className="label">慈善援助</div><div className="value">28项目</div></div>
        </div>
      </div>
      <div className="disclaimer">⚠️ 本平台仅供参考，不替代专业医疗诊断<br/>🧬 中国首个AI驱动罕见病诊疗平台</div>
    </div>
  );
}

// ===== 问诊页 =====
function ConsultPage({ initialSymptom }) {
  const [messages, setMessages] = useState([{
    role: 'agent',
    content: '您好，我是陈雅琴医生，协和医院急诊科的分诊医师。请告诉我您或家人的症状，我会帮您分析情况，并推荐最合适的专科方向。',
    doctor: DOCTORS.triage,
  }]);
  const [input, setInput] = useState(initialSymptom || '');
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [currentDoctor, setCurrentDoctor] = useState(DOCTORS.triage);
  const messagesEndRef = useRef(null);

  useEffect(() => { messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages]);
  useEffect(() => { if (initialSymptom) setInput(initialSymptom); }, [initialSymptom]);

  const sendMessage = async () => {
    if (!input.trim() || loading) return;
    const userMsg = { role: 'patient', content: input };
    setMessages(prev => [...prev, userMsg]);
    const msg = input;
    setInput('');
    setLoading(true);
    try {
      const resp = await fetch('/api/v1/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: msg, session_id: sessionId })
      });
      const data = await resp.json();
      setSessionId(data.session_id);
      const agentKey = data.agent_name?.includes('分诊') ? 'triage' : data.agent_name?.includes('诊断') ? 'diagnosis' : data.agent_name?.includes('用药') ? 'medicine' : data.agent_name?.includes('心理') ? 'mental' : data.agent_name?.includes('康复') ? 'rehab' : 'followup';
      const doctor = DOCTORS[agentKey];
      setCurrentDoctor(doctor);
      setMessages(prev => [...prev, { role: 'agent', content: data.message, doctor, suggestions: data.suggestions }]);
    } catch (e) {
      setMessages(prev => [...prev, { role: 'error', content: '网络错误，请稍后重试' }]);
    } finally { setLoading(false); }
  };

  const rareCases = [
    { title: '戈谢病', symptoms: '我孩子5岁了，肚子越来越大，脾脏肿大，经常骨痛，血小板减少' },
    { title: '庞贝病', symptoms: '我最近呼吸困难，肌肉无力，爬楼梯都费劲，心脏也有些问题' },
    { title: '法布雷病', symptoms: '我手脚经常烧灼样疼痛，出汗少，尿里有泡沫' },
    { title: '渐冻症', symptoms: '我最近手部肌肉萎缩，握东西没力气，说话有些含糊' },
  ];

  return (
    <div className="chat-page">
      <div className="doctor-bar">
        <div className="avatar" style={{ background: currentDoctor.color }}>{currentDoctor.name.charAt(0)}</div>
        <div className="info">
          <h3>{currentDoctor.name}医生</h3>
          <p>{currentDoctor.title} · {currentDoctor.dept} · {currentDoctor.hospital}</p>
        </div>
      </div>
      <div className="quick-bar">
        {['头痛', '发热', '咳嗽', '腹痛', '关节痛', '皮疹'].map(s => (
          <button key={s} className="quick-chip" onClick={() => setInput(s)}>{s}</button>
        ))}
      </div>
      <div className="messages-area">
        {messages.map((msg, idx) => (
          <div key={idx} className={`msg ${msg.role}`}>
            {msg.role === 'agent' && msg.doctor && (
              <div className="msg-meta">
                <div className="msg-avatar" style={{ background: msg.doctor.color }}>{msg.doctor.name.charAt(0)}</div>
                <span className="msg-name">{msg.doctor.name}医生</span>
              </div>
            )}
            <div className="msg-bubble">{msg.content}</div>
            {msg.suggestions && (
              <div className="suggestions">
                {msg.suggestions.map((s, i) => (
                  <button key={i} className="suggestion-btn" onClick={() => { setInput(s); }}>{s}</button>
                ))}
              </div>
            )}
          </div>
        ))}
        {loading && (
          <div className="msg agent">
            <div className="msg-meta">
              <div className="msg-avatar" style={{ background: currentDoctor.color }}>{currentDoctor.name.charAt(0)}</div>
              <span className="msg-name">{currentDoctor.name}医生 正在思考...</span>
            </div>
            <div className="loading-dots"><span></span><span></span><span></span></div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>
      <div className="quick-bar">
        {rareCases.map((c, i) => (
          <button key={i} className="quick-chip" onClick={() => setInput(c.symptoms)} title={c.symptoms}>🧬 {c.title}</button>
        ))}
      </div>
      <div className="input-area">
        <textarea value={input} onChange={e => setInput(e.target.value)} onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); } }} placeholder="请描述您的症状..." rows={1} />
        <button className="send-btn" onClick={sendMessage} disabled={loading || !input.trim()}>↑</button>
      </div>
    </div>
  );
}

// ===== 知识中心 =====
function KnowledgePage() {
  const [search, setSearch] = useState('');
  const [selected, setSelected] = useState(null);
  const filtered = DISEASES.filter(d => d.name.includes(search) || d.symptoms.some(s => s.includes(search)) || d.type.includes(search));

  return (
    <div className="page">
      <div className="search-bar">
        <span className="search-icon">🔍</span>
        <input placeholder="搜索疾病名称、症状、基因..." value={search} onChange={e => setSearch(e.target.value)} />
      </div>
      <div className="card">
        <div className="card-header">
          <span className="card-title">📊 罕见病知识库</span>
          <span style={{ fontSize: 12, color: 'var(--text-light)' }}>121种疾病</span>
        </div>
        <div className="disease-grid">
          {DISEASE_CATEGORIES.slice(0, 4).map((cat, i) => (
            <div key={i} className="disease-chip">
              <span className="chip-icon">{cat.icon}</span>
              <span className="chip-label">{cat.label}</span>
              <span className="chip-count">{cat.count}种</span>
            </div>
          ))}
        </div>
      </div>
      <div className="section-title">🧬 疾病列表</div>
      <div className="disease-list">
        {filtered.map((d, i) => (
          <div key={i} className="disease-item" onClick={() => setSelected(d)}>
            <h4>{d.icon} {d.name}</h4>
            <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>{d.symptoms.slice(0, 3).join(' · ')}</div>
            <div className="disease-tags">
              <span className="tag type">{d.type}</span>
              <span className="tag gene">{d.gene}</span>
              <span className="tag">发病率 {d.rate}</span>
            </div>
          </div>
        ))}
      </div>
      <div className="card" style={{ marginTop: 16 }}>
        <div className="card-header">
          <span className="card-title">🗺️ 全国专家医院</span>
          <button className="card-more">查看地图 →</button>
        </div>
        {['📍 北京协和医院', '📍 上海瑞金医院', '📍 广州中山一院', '📍 四川华西医院'].map((h, i) => (
          <div key={i} style={{ padding: '8px 0', borderBottom: i < 3 ? '1px solid var(--border)' : 'none', fontSize: 13 }}>{h}</div>
        ))}
      </div>
      {selected && (
        <div className="disease-detail-overlay" onClick={() => setSelected(null)}>
          <div className="disease-detail" onClick={e => e.stopPropagation()}>
            <h2>{selected.icon} {selected.name}</h2>
            <div className="icd">ICD-10: {selected.icd}</div>
            <div className="info-grid">
              <div className="info-item"><div className="label">发病率</div><div className="value">{selected.rate}</div></div>
              <div className="info-item"><div className="label">疾病类型</div><div className="value">{selected.type}</div></div>
              <div className="info-item"><div className="label">关键基因</div><div className="value">{selected.gene}</div></div>
              <div className="info-item"><div className="label">遗传模式</div><div className="value">常隐/常显</div></div>
            </div>
            <div className="symptoms">
              <h4>🔍 典型症状</h4>
              {selected.symptoms.map((s, i) => (<span key={i} className="symptom-tag">{s}</span>))}
            </div>
            <div className="action-btns">
              <button className="action-btn primary" onClick={() => setSelected(null)}>AI问诊</button>
              <button className="action-btn secondary" onClick={() => setSelected(null)}>找专家</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// ===== 社群页 =====
function CommunityPage() {
  const [tab, setTab] = useState('disease');
  return (
    <div className="page">
      <div className="avatar-card">
        <h3>🤖 我的数字分身</h3>
        <p>已就绪，随时帮您在社群中交流</p>
        <div className="btn-row">
          <button className="btn btn-primary">管理分身</button>
          <button className="btn btn-secondary">Bridge匹配</button>
        </div>
      </div>
      <div className="community-tabs">
        {[{ key: 'mine', label: '我的社群' }, { key: 'disease', label: '疾病社群' }, { key: 'topic', label: '主题社群' }].map(t => (
          <button key={t.key} className={`community-tab ${tab === t.key ? 'active' : ''}`} onClick={() => setTab(t.key)}>{t.label}</button>
        ))}
      </div>
      {COMMUNITIES.map((g, i) => (
        <div key={i} className="group-card">
          <div className="group-row">
            <div className="group-avatar">{g.icon}</div>
            <div className="group-info">
              <div className="group-header">
                <span className="group-name">{g.name}</span>
                <span className="group-count">👥 {g.count.toLocaleString()}</span>
              </div>
              <div className="group-activity">今日活跃：{g.activity}</div>
            </div>
          </div>
        </div>
      ))}
      <div className="card" style={{ marginTop: 16 }}>
        <div className="card-header"><span className="card-title">🔥 热门帖子</span></div>
        {[{ title: '确诊3年，分享我的治疗经历', likes: 234, comments: 56 }, { title: '新药临床试验招募信息', likes: 189, comments: 34 }, { title: '康复训练日记分享', likes: 156, comments: 28 }].map((p, i) => (
          <div key={i} style={{ padding: '10px 0', borderBottom: i < 2 ? '1px solid var(--border)' : 'none' }}>
            <div style={{ fontSize: 13, fontWeight: 500, marginBottom: 4 }}>💬 {p.title}</div>
            <div style={{ fontSize: 11, color: 'var(--text-light)' }}>👍 {p.likes} · 💬 {p.comments}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ===== 个人中心 =====
function ProfilePage() {
  const menus = [
    { icon: '📋', label: '健康档案' }, { icon: '👨‍👩‍👧', label: '家庭成员管理' },
    { icon: '💊', label: '用药记录' }, { icon: '📅', label: '复诊日历' },
    { icon: '💰', label: '医保信息' }, { icon: '🤖', label: '数字分身设置' },
    { icon: '🔒', label: '隐私与合规' }, { icon: '⚙️', label: '系统设置' },
  ];
  return (
    <div className="page">
      <div className="profile-header">
        <div className="profile-avatar">🧑‍⚕️</div>
        <h2>小林医生</h2>
        <p>患者 · 罕见病关注者</p>
      </div>
      <div className="card">
        <div className="card-header"><span className="card-title">📊 健康概览</span></div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 12, textAlign: 'center' }}>
          <div><div style={{ fontSize: 20, fontWeight: 700, color: 'var(--primary)' }}>12</div><div style={{ fontSize: 11, color: 'var(--text-secondary)' }}>问诊次数</div></div>
          <div><div style={{ fontSize: 20, fontWeight: 700, color: 'var(--accent)' }}>3</div><div style={{ fontSize: 11, color: 'var(--text-secondary)' }}>加入社群</div></div>
          <div><div style={{ fontSize: 20, fontWeight: 700, color: 'var(--warn)' }}>5</div><div style={{ fontSize: 11, color: 'var(--text-secondary)' }}>用药提醒</div></div>
        </div>
      </div>
      <div className="menu-list">
        {menus.map((m, i) => (
          <div key={i} className="menu-item">
            <div className="menu-left"><span className="menu-icon">{m.icon}</span><span>{m.label}</span></div>
            <span className="menu-arrow">›</span>
          </div>
        ))}
      </div>
      <div className="disclaimer">MediChat-RD v1.0 · 中国首个AI驱动罕见病诊疗平台<br/>数据安全 · HIPAA合规 · 端到端加密</div>
    </div>
  );
}

// ========== 主应用 ==========
function App() {
  const [page, setPage] = useState('home');
  const [consultSymptom, setConsultSymptom] = useState('');
  const handleNavigate = (p, symptom) => { if (symptom) setConsultSymptom(symptom); else setConsultSymptom(''); setPage(p); };

  return (
    <div className="app">
      <TopBar />
      {page === 'home' && <HomePage onNavigate={handleNavigate} />}
      {page === 'consult' && <ConsultPage initialSymptom={consultSymptom} />}
      {page === 'knowledge' && <KnowledgePage />}
      {page === 'community' && <CommunityPage />}
      {page === 'profile' && <ProfilePage />}
      <TabBar active={page} onChange={handleNavigate} />
    </div>
  );
}

export default App;
