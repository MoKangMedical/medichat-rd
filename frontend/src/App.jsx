import React, { useState, useRef, useEffect } from 'react';
import './App.css';
import DeepRarePanel from './components/DeepRarePanel';
import CommunityPanel from './components/CommunityPanel';
import DoctorPanel from './components/DoctorPanel';

// ═══════════════════════════════════════════════════
// 图标组件
// ═══════════════════════════════════════════════════
const Icons = {
  brain: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round">
      <path d="M12 2a5 5 0 0 1 5 5c0 .7-.2 1.4-.5 2A5 5 0 0 1 19 14a5 5 0 0 1-3 4.6V22h-4v-3.4A5 5 0 0 1 9 14a5 5 0 0 1 2.5-4.4A5 5 0 0 1 7 7a5 5 0 0 1 5-5z"/>
      <path d="M12 2v20"/>
    </svg>
  ),
  dna: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round">
      <path d="M2 15c6.667-6 13.333 0 20-6M2 9c6.667 6 13.333 0 20 6M7 3v4M17 3v4M7 17v4M17 17v4"/>
    </svg>
  ),
  search: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
      <circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/>
    </svg>
  ),
  chat: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
      <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
    </svg>
  ),
  pill: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
      <path d="m10.5 20.5 10-10a4.95 4.95 0 1 0-7-7l-10 10a4.95 4.95 0 1 0 7 7Z"/>
      <path d="m8.5 8.5 7 7"/>
    </svg>
  ),
  file: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/>
    </svg>
  ),
  activity: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
      <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
    </svg>
  ),
  users: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
      <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/>
      <path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>
    </svg>
  ),
  send: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
      <line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/>
    </svg>
  ),
  menu: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
      <line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="18" x2="21" y2="18"/>
    </svg>
  ),
  x: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
      <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
    </svg>
  ),
  home: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
      <path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/>
    </svg>
  ),
  check: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
      <polyline points="20 6 9 17 4 12"/>
    </svg>
  ),
  alert: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
      <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
      <line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>
    </svg>
  ),
};

// ═══════════════════════════════════════════════════
// 首页组件
// ═══════════════════════════════════════════════════
function HomePage({ onNavigate }) {
  const stats = [
    { label: '覆盖罕见病', value: '121+', icon: 'dna' },
    { label: '药物数据', value: '47万+', icon: 'pill' },
    { label: '临床试验', value: '48万+', icon: 'activity' },
    { label: 'AI分析能力', value: 'MIMO驱动', icon: 'chat' },
  ];

  const features = [
    {
      icon: 'brain',
      title: 'DeepRare智能诊断',
      desc: 'Nature 2026 · Agentic AI · HPO表型提取 · 可追溯推理 · 自反思验证',
      action: 'deeprare',
      highlight: true,
    },
    {
      icon: 'search',
      title: '智能症状自查',
      desc: '描述症状，AI分析可能的罕见病方向，建议进一步检查',
      action: 'symptom-check',
    },
    {
      icon: 'pill',
      title: '药物重定位研究',
      desc: '整合OpenTargets、ChEMBL数据，发现老药新用的机会',
      action: 'drug-research',
    },
    {
      icon: 'file',
      title: '疾病研究一站通',
      desc: '靶点、药物、临床试验、文献，一键生成完整研究报告',
      action: 'disease-research',
    },
    {
      icon: 'chat',
      title: 'AI医学助手',
      desc: '罕见病专业知识问答，患者教育，诊疗方案讨论',
      action: 'ai-chat',
    },
    {
      icon: 'users',
      title: '罕见病互助社群',
      desc: 'Second Me AI分身 · Bridge智能配对 · 同病相怜互助',
      action: 'community',
    },
  ];

  return (
    <div className="home-page">
      {/* Hero Section */}
      <section className="hero">
        <div className="hero-bg">
          <div className="hero-gradient"></div>
          <div className="hero-dna">
            <Icons.dna />
          </div>
        </div>
        <div className="hero-content">
          <div className="hero-badge">MediChat-RD v4.0</div>
          <h1>罕见病在线诊疗平台</h1>
          <p className="hero-subtitle">
            AI驱动的罕见病研究与诊疗，连接患者、医生与全球最新医学知识
          </p>
          <div className="hero-actions">
            <button className="btn-primary" onClick={() => onNavigate('ai-chat')}>
              <Icons.chat /> 开始咨询
            </button>
            <button className="btn-secondary" onClick={() => onNavigate('symptom-check')}>
              <Icons.search /> 症状自查
            </button>
          </div>
        </div>
      </section>

      {/* Stats */}
      <section className="stats-section">
        <div className="stats-grid">
          {stats.map((stat, i) => {
            const Icon = Icons[stat.icon];
            return (
              <div key={i} className="stat-card">
                <div className="stat-icon"><Icon /></div>
                <div className="stat-value">{stat.value}</div>
                <div className="stat-label">{stat.label}</div>
              </div>
            );
          })}
        </div>
      </section>

      {/* Features */}
      <section className="features-section">
        <h2>核心功能</h2>
        <p className="section-desc">四大功能模块，覆盖罕见病诊疗全流程</p>
        <div className="features-grid">
          {features.map((feat, i) => {
            const Icon = Icons[feat.icon];
            return (
              <div key={i} className="feature-card" onClick={() => onNavigate(feat.action)}>
                <div className="feature-icon"><Icon /></div>
                <h3>{feat.title}</h3>
                <p>{feat.desc}</p>
                <span className="feature-link">立即使用 →</span>
              </div>
            );
          })}
        </div>
      </section>

      {/* Data Sources */}
      <section className="sources-section">
        <h2>数据来源</h2>
        <div className="sources-grid">
          {['OpenTargets', 'ChEMBL', 'ClinicalTrials.gov', 'PubMed', 'OMIM', 'DrugBank'].map((src, i) => (
            <div key={i} className="source-tag">{src}</div>
          ))}
        </div>
      </section>

      {/* Footer */}
      <footer className="footer">
        <p>MediChat-RD 罕见病在线诊疗平台 | 数据仅供参考，不构成医疗建议</p>
        <p>Powered by MIMO AI + ToolUniverse</p>
      </footer>
    </div>
  );
}

// ═══════════════════════════════════════════════════
// AI 对话组件
// ═══════════════════════════════════════════════════
function AIChatPage() {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: '您好！我是 MediChat-RD 的AI助手，专注于罕见病领域。我可以帮您：\n\n- 解答罕见病相关问题\n- 解释医学检查结果\n- 提供疾病管理建议\n- 讨论治疗方案\n\n请问有什么可以帮您的？'
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(scrollToBottom, [messages]);

  const sendMessage = async () => {
    if (!input.trim() || loading) return;
    
    const userMsg = { role: 'user', content: input };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    try {
      const res = await fetch('/api/v2/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          messages: [...messages, userMsg].map(m => ({ role: m.role, content: m.content })),
        }),
      });
      const data = await res.json();
      setMessages(prev => [...prev, { role: 'assistant', content: data.response }]);
    } catch (err) {
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: '抱歉，暂时无法连接到AI服务。请稍后再试。' 
      }]);
    }
    setLoading(false);
  };

  return (
    <div className="chat-page">
      <div className="chat-header">
        <Icons.chat />
        <h2>AI医学助手</h2>
        <span className="chat-badge">MIMO驱动</span>
      </div>
      <div className="chat-messages">
        {messages.map((msg, i) => (
          <div key={i} className={`message ${msg.role}`}>
            <div className="message-avatar">
              {msg.role === 'assistant' ? 'AI' : '您'}
            </div>
            <div className="message-content">
              {msg.content.split('\n').map((line, j) => (
                <p key={j}>{line || <br />}</p>
              ))}
            </div>
          </div>
        ))}
        {loading && (
          <div className="message assistant">
            <div className="message-avatar">AI</div>
            <div className="message-content">
              <div className="typing-indicator">
                <span></span><span></span><span></span>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>
      <div className="chat-input">
        <input
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && sendMessage()}
          placeholder="输入您的问题..."
          disabled={loading}
        />
        <button onClick={sendMessage} disabled={loading || !input.trim()}>
          <Icons.send />
        </button>
      </div>
      <div className="chat-disclaimer">
        AI回复仅供参考，不构成医疗诊断。如有紧急情况，请立即就医。
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════
// 症状自查组件
// ═══════════════════════════════════════════════════
function SymptomCheckPage() {
  const [symptoms, setSymptoms] = useState('');
  const [age, setAge] = useState('');
  const [gender, setGender] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const check = async () => {
    if (!symptoms.trim()) return;
    setLoading(true);
    try {
      const res = await fetch('/api/v2/symptom-check', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          symptoms,
          age: age ? parseInt(age) : null,
          gender: gender || null,
        }),
      });
      setResult(await res.json());
    } catch (err) {
      setResult({ error: '服务暂时不可用，请稍后再试' });
    }
    setLoading(false);
  };

  return (
    <div className="symptom-page">
      <div className="page-header">
        <h2>智能症状自查</h2>
        <p>描述您的症状，AI将分析可能的罕见病方向</p>
      </div>
      
      <div className="symptom-form">
        <div className="form-row">
          <div className="form-group">
            <label>年龄（选填）</label>
            <input type="number" value={age} onChange={e => setAge(e.target.value)} placeholder="如：35" />
          </div>
          <div className="form-group">
            <label>性别（选填）</label>
            <select value={gender} onChange={e => setGender(e.target.value)}>
              <option value="">请选择</option>
              <option value="男">男</option>
              <option value="女">女</option>
            </select>
          </div>
        </div>
        <div className="form-group">
          <label>症状描述</label>
          <textarea
            value={symptoms}
            onChange={e => setSymptoms(e.target.value)}
            placeholder="请详细描述您的症状，例如：&#10;- 双眼皮下垂3个月&#10;- 下午疲劳加重&#10;- 吞咽困难"
            rows={5}
          />
        </div>
        <button className="btn-primary" onClick={check} disabled={loading || !symptoms.trim()}>
          {loading ? '分析中...' : '开始自查'}
        </button>
      </div>

      {result && !result.error && (
        <div className="result-card">
          <h3>自查结果</h3>
          <div className="result-content">
            {result.analysis?.split('\n').map((line, i) => (
              <p key={i}>{line || <br />}</p>
            ))}
          </div>
          <div className="disclaimer-box">
            <Icons.alert />
            <span>{result.disclaimer}</span>
          </div>
        </div>
      )}
    </div>
  );
}

// ═══════════════════════════════════════════════════
// 疾病研究组件
// ═══════════════════════════════════════════════════
function DiseaseResearchPage() {
  const [disease, setDisease] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('overview');

  const research = async () => {
    if (!disease.trim()) return;
    setLoading(true);
    setResult(null);
    try {
      const res = await fetch('/api/v2/research', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ disease_name: disease }),
      });
      setResult(await res.json());
    } catch (err) {
      setResult({ error: '研究服务暂时不可用' });
    }
    setLoading(false);
  };

  const tabs = [
    { id: 'overview', label: '疾病概述' },
    { id: 'targets', label: '靶点' },
    { id: 'drugs', label: '药物' },
    { id: 'trials', label: '临床试验' },
    { id: 'analysis', label: 'AI分析' },
  ];

  return (
    <div className="research-page">
      <div className="page-header">
        <h2>疾病研究一站通</h2>
        <p>靶点、药物、临床试验、AI分析，一键生成完整报告</p>
      </div>

      <div className="search-bar">
        <input
          value={disease}
          onChange={e => setDisease(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && research()}
          placeholder="输入疾病名称，如：Myasthenia Gravis"
        />
        <button className="btn-primary" onClick={research} disabled={loading}>
          {loading ? '研究中...' : '开始研究'}
        </button>
      </div>

      {loading && (
        <div className="loading-state">
          <div className="spinner"></div>
          <p>正在整合多源数据并生成分析报告...</p>
        </div>
      )}

      {result && !result.error && (
        <div className="research-result">
          <div className="tabs">
            {tabs.map(tab => (
              <button
                key={tab.id}
                className={`tab ${activeTab === tab.id ? 'active' : ''}`}
                onClick={() => setActiveTab(tab.id)}
              >
                {tab.label}
              </button>
            ))}
          </div>

          <div className="tab-content">
            {activeTab === 'overview' && result.stages?.disease_info && (
              <div className="overview-card">
                <h3>{result.stages.disease_info.name}</h3>
                <p>{result.stages.disease_info.description}</p>
                <div className="meta">
                  <span>ID: {result.stages.disease_info.id}</span>
                </div>
              </div>
            )}

            {activeTab === 'targets' && result.stages?.targets && (
              <div className="table-container">
                <table>
                  <thead>
                    <tr>
                      <th>基因</th>
                      <th>名称</th>
                      <th>关联分数</th>
                      <th>遗传关联</th>
                      <th>临床证据</th>
                    </tr>
                  </thead>
                  <tbody>
                    {result.stages.targets.map((t, i) => (
                      <tr key={i}>
                        <td><code>{t.gene_id.split(':').pop()}</code></td>
                        <td>{t.gene_name}</td>
                        <td><span className="score">{t.score}</span></td>
                        <td>{t.genetic_association ? t.genetic_association.toFixed(3) : '-'}</td>
                        <td>{t.clinical ? t.clinical.toFixed(3) : '-'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {activeTab === 'drugs' && result.stages?.drugs && (
              <div className="drugs-grid">
                {result.stages.drugs.map((d, i) => (
                  <div key={i} className="drug-card">
                    <div className="drug-phase">
                      <span className={`phase-badge phase-${d.max_phase?.replace('.', '')}`}>
                        {d.phase_label}
                      </span>
                    </div>
                    <div className="drug-id"><code>{d.chembl_id}</code></div>
                    <div className="drug-name">{d.mesh_heading}</div>
                  </div>
                ))}
              </div>
            )}

            {activeTab === 'trials' && result.stages?.clinical_trials && (
              <div className="trials-list">
                {result.stages.clinical_trials.map((t, i) => (
                  <div key={i} className="trial-card">
                    <div className="trial-header">
                      <code className="nct-id">{t.nct_id}</code>
                      <span className={`status-badge status-${t.status?.toLowerCase()}`}>
                        {t.status_cn}
                      </span>
                    </div>
                    <h4>{t.title}</h4>
                    <p className="trial-sponsor">{t.sponsor}</p>
                    {t.summary && <p className="trial-summary">{t.summary}</p>}
                  </div>
                ))}
              </div>
            )}

            {activeTab === 'analysis' && result.stages?.analysis && (
              <div className="analysis-card">
                <div className="analysis-content">
                  {result.stages.analysis.split('\n').map((line, i) => (
                    <p key={i}>{line || <br />}</p>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

// ═══════════════════════════════════════════════════
// 药物重定位组件
// ═══════════════════════════════════════════════════
function DrugResearchPage() {
  const [disease, setDisease] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const research = async () => {
    if (!disease.trim()) return;
    setLoading(true);
    try {
      const res = await fetch(`/api/v2/drug-repurposing?disease_name=${encodeURIComponent(disease)}`, {
        method: 'POST',
      });
      setResult(await res.json());
    } catch (err) {
      setResult({ error: '服务暂时不可用' });
    }
    setLoading(false);
  };

  return (
    <div className="drug-page">
      <div className="page-header">
        <h2>药物重定位研究</h2>
        <p>发现老药新用的机会，加速罕见病治疗进展</p>
      </div>

      <div className="search-bar">
        <input
          value={disease}
          onChange={e => setDisease(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && research()}
          placeholder="输入疾病名称"
        />
        <button className="btn-primary" onClick={research} disabled={loading}>
          {loading ? '分析中...' : '开始分析'}
        </button>
      </div>

      {loading && (
        <div className="loading-state">
          <div className="spinner"></div>
          <p>正在分析药物重定位机会...</p>
        </div>
      )}

      {result && !result.error && (
        <div className="drug-result">
          <h3>{result.disease} - 药物重定位分析</h3>
          <div className="analysis-card">
            <div className="analysis-content">
              {result.repurposing_analysis?.split('\n').map((line, i) => (
                <p key={i}>{line || <br />}</p>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// ═══════════════════════════════════════════════════
// 主应用
// ═══════════════════════════════════════════════════
function App() {
  const [page, setPage] = useState('home');
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const navItems = [
    { id: 'home', label: '首页', icon: 'home' },
    { id: 'deeprare', label: 'DeepRare诊断', icon: 'brain' },
    { id: 'community', label: '互助社群', icon: 'users' },
    { id: 'doctor', label: '医生助手', icon: 'activity' },
    { id: 'ai-chat', label: 'AI助手', icon: 'chat' },
    { id: 'symptom-check', label: '症状自查', icon: 'search' },
    { id: 'disease-research', label: '疾病研究', icon: 'file' },
    { id: 'drug-research', label: '药物重定位', icon: 'pill' },
  ];

  const renderPage = () => {
    switch (page) {
      case 'deeprare': return <DeepRarePanel />;
      case 'community': return <CommunityPanel />
      case 'doctor': return <DoctorPanel />;
      case 'ai-chat': return <AIChatPage />;
      case 'symptom-check': return <SymptomCheckPage />;
      case 'disease-research': return <DiseaseResearchPage />;
      case 'drug-research': return <DrugResearchPage />;
      default: return <HomePage onNavigate={setPage} />;
    }
  };

  return (
    <div className="app">
      {/* Top Nav */}
      <nav className="topnav">
        <button className="menu-btn" onClick={() => setSidebarOpen(!sidebarOpen)}>
          {sidebarOpen ? <Icons.x /> : <Icons.menu />}
        </button>
        <div className="nav-brand" onClick={() => setPage('home')}>
          <Icons.dna />
          <span>MediChat-RD</span>
        </div>
        <div className="nav-right">
          <span className="nav-version">v4.0</span>
        </div>
      </nav>

      {/* Sidebar */}
      <aside className={`sidebar ${sidebarOpen ? 'open' : ''}`}>
        {navItems.map(item => {
          const Icon = Icons[item.icon];
          return (
            <button
              key={item.id}
              className={`nav-item ${page === item.id ? 'active' : ''}`}
              onClick={() => { setPage(item.id); setSidebarOpen(false); }}
            >
              <Icon />
              <span>{item.label}</span>
            </button>
          );
        })}
      </aside>

      {/* Main Content */}
      <main className="main-content">
        {renderPage()}
      </main>
    </div>
  );
}

export default App;
