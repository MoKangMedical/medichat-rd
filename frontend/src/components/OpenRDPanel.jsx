import React, { useEffect, useMemo, useState } from 'react';

const API_BASE = import.meta.env.VITE_API_URL || '';

const TRACK_LABELS = {
  'patient-community': '患者连接',
  'mdt-collaboration': '诊疗协作',
  'drug-rd-engine': '药物研发',
};

const STATUS_LABELS = {
  unclaimed: '未认领',
  'in-progress': '开发中',
  completed: '已完成',
};

const PRIORITY_LABELS = {
  high: '高优先级',
  medium: '中优先级',
  low: '低优先级',
};

async function fetchJson(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, options);
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.detail || data.message || '请求失败');
  }
  return data;
}

function today() {
  return new Date().toISOString().slice(0, 10);
}

function EmptyState({ children }) {
  return <div className="openrd-empty">{children}</div>;
}

export default function OpenRDPanel() {
  const [overview, setOverview] = useState(null);
  const [requirements, setRequirements] = useState([]);
  const [projects, setProjects] = useState([]);
  const [messages, setMessages] = useState([]);
  const [cohorts, setCohorts] = useState([]);
  const [ledger, setLedger] = useState([]);
  const [activeTrack, setActiveTrack] = useState('all');
  const [selectedRequirement, setSelectedRequirement] = useState('');
  const [loading, setLoading] = useState(true);
  const [notice, setNotice] = useState('');
  const [error, setError] = useState('');
  const [requirementDraft, setRequirementDraft] = useState({
    title: '',
    description: '',
    priority: 'medium',
    track: 'patient-community',
    disease_area: '全病种',
    tags: 'AI, 罕见病',
    created_by: 'OpenRD 共建者',
  });
  const [joinDraft, setJoinDraft] = useState({
    name: '',
    role: '',
    affiliation: '',
    github: '',
    contact: '',
    participant_type: 'volunteer',
    message: '',
  });
  const [messageDraft, setMessageDraft] = useState({
    room: 'general',
    author_alias: '匿名共建者',
    role: 'volunteer',
    content: '',
  });
  const [cohortDraft, setCohortDraft] = useState({
    name: '',
    disease_area: '',
    criteria: '',
    data_sources: 'HPO, Phenopacket-lite, RWD',
    target_size: 50,
    owner: '转化研究组',
  });
  const [consentDraft, setConsentDraft] = useState({
    subject_alias: '',
    scope: '匿名队列研究与试验匹配',
    action: 'grant',
    actor: 'MediChat-RD OpenRD Bridge',
    note: '',
  });

  const filteredRequirements = useMemo(() => {
    if (activeTrack === 'all') return requirements;
    return requirements.filter((item) => item.track === activeTrack);
  }, [requirements, activeTrack]);

  const selectedRequirementObject = useMemo(
    () => requirements.find((item) => item.id === selectedRequirement) || requirements[0],
    [requirements, selectedRequirement],
  );

  const loadAll = async () => {
    setLoading(true);
    setError('');
    try {
      const [overviewData, requirementsData, projectsData, messageData, cohortData, ledgerData] = await Promise.all([
        fetchJson('/api/v1/openrd/overview'),
        fetchJson('/api/v1/openrd/requirements'),
        fetchJson('/api/v1/openrd/projects'),
        fetchJson('/api/v1/openrd/messages?room=general&limit=20'),
        fetchJson('/api/v1/openrd/virtual-cohorts'),
        fetchJson('/api/v1/openrd/consent-ledger?limit=12'),
      ]);
      setOverview(overviewData);
      setRequirements(requirementsData.items || []);
      setProjects(projectsData.items || []);
      setMessages(messageData.items || []);
      setCohorts(cohortData.items || []);
      setLedger(ledgerData.items || []);
      if (!selectedRequirement && requirementsData.items?.[0]) {
        setSelectedRequirement(requirementsData.items[0].id);
      }
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAll();
  }, []);

  const showNotice = (text) => {
    setNotice(text);
    window.setTimeout(() => setNotice(''), 3200);
  };

  const submitRequirement = async () => {
    if (!requirementDraft.title.trim() || !requirementDraft.description.trim()) {
      setError('请填写需求标题和描述。');
      return;
    }
    setError('');
    await fetchJson('/api/v1/openrd/requirements', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        ...requirementDraft,
        tags: requirementDraft.tags.split(/[,，、\s]+/).map((item) => item.trim()).filter(Boolean),
      }),
    });
    setRequirementDraft({
      ...requirementDraft,
      title: '',
      description: '',
      tags: 'AI, 罕见病',
    });
    await loadAll();
    showNotice('需求已进入 OpenRD 共建池。');
  };

  const submitJoin = async () => {
    const targetId = selectedRequirementObject?.id;
    if (!targetId || !joinDraft.name.trim() || !joinDraft.role.trim()) {
      setError('请选择需求，并填写姓名/角色。');
      return;
    }
    setError('');
    await fetchJson(`/api/v1/openrd/requirements/${encodeURIComponent(targetId)}/join`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(joinDraft),
    });
    setJoinDraft({
      name: '',
      role: '',
      affiliation: '',
      github: '',
      contact: '',
      participant_type: 'volunteer',
      message: '',
    });
    await loadAll();
    showNotice('加入申请已提交，已进入需求协作记录。');
  };

  const submitMessage = async () => {
    if (!messageDraft.content.trim()) {
      setError('请填写匿名协作消息。');
      return;
    }
    setError('');
    await fetchJson('/api/v1/openrd/messages', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(messageDraft),
    });
    setMessageDraft({ ...messageDraft, content: '' });
    await loadAll();
    showNotice('匿名消息已发布。');
  };

  const submitCohort = async () => {
    if (!cohortDraft.name.trim() || !cohortDraft.disease_area.trim() || !cohortDraft.criteria.trim()) {
      setError('请填写虚拟队列名称、疾病方向和纳入标准。');
      return;
    }
    setError('');
    await fetchJson('/api/v1/openrd/virtual-cohorts', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        ...cohortDraft,
        target_size: Number(cohortDraft.target_size) || 20,
        data_sources: cohortDraft.data_sources.split(/[,，、\s]+/).map((item) => item.trim()).filter(Boolean),
      }),
    });
    setCohortDraft({
      name: '',
      disease_area: '',
      criteria: '',
      data_sources: 'HPO, Phenopacket-lite, RWD',
      target_size: 50,
      owner: '转化研究组',
    });
    await loadAll();
    showNotice('虚拟队列已创建。');
  };

  const submitConsent = async () => {
    if (!consentDraft.subject_alias.trim() || !consentDraft.scope.trim()) {
      setError('请填写授权主体别名和授权范围。');
      return;
    }
    setError('');
    await fetchJson('/api/v1/openrd/consent-ledger', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(consentDraft),
    });
    setConsentDraft({ ...consentDraft, subject_alias: '', note: '' });
    await loadAll();
    showNotice('授权事件已写入 hash-chain 台账。');
  };

  return (
    <div className="utility-page openrd-page">
      <div className="utility-shell openrd-shell">
        <section className="openrd-hero">
          <div className="openrd-hero-copy">
            <div className="page-eyebrow">OpenRD collaboration bridge</div>
            <h2>{overview?.short_name || 'MediChat-RD OpenRD Bridge'}</h2>
            <p>{overview?.summary || '连接患者、医生、科研和药企的罕见病共建工作台。'}</p>
            <div className="openrd-hero-actions">
              <button type="button" className="primary-btn" onClick={loadAll}>
                <span>{loading ? '同步中' : '刷新共建数据'}</span>
              </button>
              <a className="ghost-btn" href="https://github.com/MoKangMedical/medichat-rd" target="_blank" rel="noreferrer">
                <span>查看 GitHub</span>
              </a>
            </div>
          </div>
          <div className="openrd-hero-card">
            <span>平台愿景</span>
            <strong>全球罕见病生态系统的数字中枢</strong>
            <p>{overview?.slogan}</p>
            <div className="openrd-hero-meta">
              <div><small>需求</small><b>{overview?.stats?.total_requirements || 0}</b></div>
              <div><small>共建者</small><b>{overview?.stats?.contributors || 0}</b></div>
              <div><small>虚拟队列</small><b>{overview?.stats?.virtual_cohorts || 0}</b></div>
            </div>
          </div>
        </section>

        {notice && <div className="inline-success">{notice}</div>}
        {error && <div className="inline-error">{error}</div>}

        <section className="result-panel openrd-module-panel">
          <div className="section-head">
            <span>三大核心痛点与功能模块</span>
            <span className="section-note">在现有平台能力上新增 OpenRD 共建入口</span>
          </div>
          <div className="openrd-module-grid">
            {(overview?.core_modules || []).map((module) => (
              <article key={module.id} className="openrd-module-card">
                <small>{TRACK_LABELS[module.id]}</small>
                <h3>{module.title}</h3>
                <p>{module.outcome}</p>
                <div className="openrd-chip-row">
                  {module.capabilities.map((item) => <span key={item}>{item}</span>)}
                </div>
              </article>
            ))}
          </div>
        </section>

        <section className="result-panel">
          <div className="section-head">
            <span>OpenRD 需求池</span>
            <span className="section-note">患者、医生、科研和药企都可以把问题转成可协作需求</span>
          </div>
          <div className="openrd-track-tabs">
            {['all', 'patient-community', 'mdt-collaboration', 'drug-rd-engine'].map((track) => (
              <button
                key={track}
                type="button"
                className={activeTrack === track ? 'active' : ''}
                onClick={() => setActiveTrack(track)}
              >
                {track === 'all' ? '全部' : TRACK_LABELS[track]}
              </button>
            ))}
          </div>
          <div className="openrd-requirement-grid">
            {filteredRequirements.map((item) => (
              <article
                key={item.id}
                className={`openrd-requirement-card ${selectedRequirementObject?.id === item.id ? 'selected' : ''}`}
                onClick={() => setSelectedRequirement(item.id)}
              >
                <div className="openrd-card-top">
                  <span>{STATUS_LABELS[item.status] || item.status}</span>
                  <small>{PRIORITY_LABELS[item.priority] || item.priority}</small>
                </div>
                <h3>{item.title}</h3>
                <p>{item.description}</p>
                <div className="openrd-progress">
                  <div><span style={{ width: `${item.progress || 0}%` }} /></div>
                  <b>{item.progress || 0}%</b>
                </div>
                <div className="openrd-chip-row">
                  {(item.tags || []).slice(0, 4).map((tag) => <span key={tag}>{tag}</span>)}
                </div>
                <div className="openrd-card-foot">
                  <span>{TRACK_LABELS[item.track] || item.track}</span>
                  <span>{item.team?.length || 0} 位共建者</span>
                </div>
              </article>
            ))}
          </div>
        </section>

        <section className="openrd-action-grid">
          <div className="result-panel">
            <div className="section-head">
              <span>提交新需求</span>
              <span className="section-note">参考 OpenRD 需求池模式</span>
            </div>
            <div className="field-grid two">
              <label className="field">
                <span>需求标题</span>
                <input value={requirementDraft.title} onChange={(event) => setRequirementDraft({ ...requirementDraft, title: event.target.value })} placeholder="例如：FSHD 甲基化检测路径可视化" />
              </label>
              <label className="field">
                <span>优先级</span>
                <select value={requirementDraft.priority} onChange={(event) => setRequirementDraft({ ...requirementDraft, priority: event.target.value })}>
                  <option value="high">高</option>
                  <option value="medium">中</option>
                  <option value="low">低</option>
                </select>
              </label>
            </div>
            <div className="field-grid two">
              <label className="field">
                <span>协作轨道</span>
                <select value={requirementDraft.track} onChange={(event) => setRequirementDraft({ ...requirementDraft, track: event.target.value })}>
                  <option value="patient-community">患者连接</option>
                  <option value="mdt-collaboration">诊疗协作</option>
                  <option value="drug-rd-engine">药物研发</option>
                </select>
              </label>
              <label className="field">
                <span>疾病方向</span>
                <input value={requirementDraft.disease_area} onChange={(event) => setRequirementDraft({ ...requirementDraft, disease_area: event.target.value })} />
              </label>
            </div>
            <label className="field">
              <span>需求描述</span>
              <textarea rows={4} value={requirementDraft.description} onChange={(event) => setRequirementDraft({ ...requirementDraft, description: event.target.value })} placeholder="请描述患者/医生/科研/药企协作中最需要解决的问题。" />
            </label>
            <label className="field">
              <span>标签</span>
              <input value={requirementDraft.tags} onChange={(event) => setRequirementDraft({ ...requirementDraft, tags: event.target.value })} />
            </label>
            <button type="button" className="primary-btn" onClick={submitRequirement}>提交到共建池</button>
          </div>

          <div className="result-panel">
            <div className="section-head">
              <span>加入协作</span>
              <span className="section-note">志愿者/医生/科研/药企可申请加入</span>
            </div>
            <label className="field">
              <span>选择需求</span>
              <select value={selectedRequirementObject?.id || ''} onChange={(event) => setSelectedRequirement(event.target.value)}>
                {requirements.map((item) => <option key={item.id} value={item.id}>{item.title}</option>)}
              </select>
            </label>
            <div className="field-grid two">
              <label className="field">
                <span>姓名/昵称</span>
                <input value={joinDraft.name} onChange={(event) => setJoinDraft({ ...joinDraft, name: event.target.value })} />
              </label>
              <label className="field">
                <span>角色</span>
                <input value={joinDraft.role} onChange={(event) => setJoinDraft({ ...joinDraft, role: event.target.value })} placeholder="前端 / 医生 / 研究员 / 患者代表" />
              </label>
            </div>
            <div className="field-grid two">
              <label className="field">
                <span>单位/来源</span>
                <input value={joinDraft.affiliation} onChange={(event) => setJoinDraft({ ...joinDraft, affiliation: event.target.value })} />
              </label>
              <label className="field">
                <span>GitHub</span>
                <input value={joinDraft.github} onChange={(event) => setJoinDraft({ ...joinDraft, github: event.target.value })} />
              </label>
            </div>
            <label className="field">
              <span>加入说明</span>
              <textarea rows={3} value={joinDraft.message} onChange={(event) => setJoinDraft({ ...joinDraft, message: event.target.value })} placeholder="说明你能贡献的时间、能力或资源。" />
            </label>
            <button type="button" className="primary-btn" onClick={submitJoin}>申请加入</button>
          </div>
        </section>

        <section className="result-panel">
          <div className="section-head">
            <span>项目进度</span>
            <span className="section-note">对齐 OpenRD 的 Project Progress 模式</span>
          </div>
          <div className="openrd-project-grid">
            {projects.length ? projects.map((project) => (
              <article key={project.id} className="openrd-project-card">
                <div className="openrd-card-top">
                  <span>{project.start_date}</span>
                  <small>目标 {project.target_date}</small>
                </div>
                <h3>{project.name}</h3>
                <p>{project.description}</p>
                <div className="openrd-progress">
                  <div><span style={{ width: `${project.progress || 0}%` }} /></div>
                  <b>{project.progress || 0}%</b>
                </div>
                <small>{project.contribution_guide}</small>
              </article>
            )) : <EmptyState>暂无项目进入开发阶段。</EmptyState>}
          </div>
        </section>

        <section className="openrd-action-grid">
          <div className="result-panel">
            <div className="section-head">
              <span>匿名协作房间</span>
              <span className="section-note">参考 OpenRD-web-server 的 chat group/message 结构</span>
            </div>
            <label className="field">
              <span>消息</span>
              <textarea rows={3} value={messageDraft.content} onChange={(event) => setMessageDraft({ ...messageDraft, content: event.target.value })} placeholder="发起一个匿名协作问题，例如：这个病例需要补哪类检查？" />
            </label>
            <button type="button" className="primary-btn" onClick={submitMessage}>发布匿名消息</button>
            <div className="openrd-message-list">
              {messages.length ? messages.map((message) => (
                <div key={message.id} className="openrd-message">
                  <strong>{message.author_alias}</strong>
                  <span>{message.role} · {message.created_at?.slice(0, 10) || today()}</span>
                  <p>{message.content}</p>
                </div>
              )) : <EmptyState>暂无协作消息。</EmptyState>}
            </div>
          </div>

          <div className="result-panel">
            <div className="section-head">
              <span>授权台账</span>
              <span className="section-note">hash-chain 记录，原始身份不落库</span>
            </div>
            <div className="field-grid two">
              <label className="field">
                <span>患者别名</span>
                <input value={consentDraft.subject_alias} onChange={(event) => setConsentDraft({ ...consentDraft, subject_alias: event.target.value })} placeholder="例如：anon-family-001" />
              </label>
              <label className="field">
                <span>动作</span>
                <select value={consentDraft.action} onChange={(event) => setConsentDraft({ ...consentDraft, action: event.target.value })}>
                  <option value="grant">授权</option>
                  <option value="revoke">撤回</option>
                  <option value="review">复核</option>
                  <option value="share">共享</option>
                </select>
              </label>
            </div>
            <label className="field">
              <span>授权范围</span>
              <input value={consentDraft.scope} onChange={(event) => setConsentDraft({ ...consentDraft, scope: event.target.value })} />
            </label>
            <button type="button" className="primary-btn" onClick={submitConsent}>写入授权事件</button>
            <div className="openrd-ledger-list">
              {ledger.length ? ledger.slice(0, 5).map((item) => (
                <div key={item.event_id} className="openrd-ledger-row">
                  <span>{item.action}</span>
                  <strong>{item.scope}</strong>
                  <small>{item.event_hash?.slice(0, 14)}...</small>
                </div>
              )) : <EmptyState>暂无授权事件。</EmptyState>}
            </div>
          </div>
        </section>

        <section className="result-panel">
          <div className="section-head">
            <span>虚拟患者队列</span>
            <span className="section-note">服务自然史研究、药物重定位和临床试验招募</span>
          </div>
          <div className="openrd-cohort-layout">
            <div className="openrd-cohort-form">
              <div className="field-grid two">
                <label className="field">
                  <span>队列名称</span>
                  <input value={cohortDraft.name} onChange={(event) => setCohortDraft({ ...cohortDraft, name: event.target.value })} placeholder="例如：FSHD 表观遗传疑似队列" />
                </label>
                <label className="field">
                  <span>疾病方向</span>
                  <input value={cohortDraft.disease_area} onChange={(event) => setCohortDraft({ ...cohortDraft, disease_area: event.target.value })} />
                </label>
              </div>
              <label className="field">
                <span>纳入标准</span>
                <textarea rows={3} value={cohortDraft.criteria} onChange={(event) => setCohortDraft({ ...cohortDraft, criteria: event.target.value })} placeholder="例如：儿童期起病 + HPO 神经发育表型 + 授权进入匿名研究队列。" />
              </label>
              <div className="field-grid two">
                <label className="field">
                  <span>数据源</span>
                  <input value={cohortDraft.data_sources} onChange={(event) => setCohortDraft({ ...cohortDraft, data_sources: event.target.value })} />
                </label>
                <label className="field">
                  <span>目标规模</span>
                  <input type="number" value={cohortDraft.target_size} onChange={(event) => setCohortDraft({ ...cohortDraft, target_size: event.target.value })} />
                </label>
              </div>
              <button type="button" className="primary-btn" onClick={submitCohort}>创建虚拟队列</button>
            </div>
            <div className="openrd-cohort-list">
              {cohorts.length ? cohorts.map((cohort) => (
                <article key={cohort.id} className="openrd-cohort-card">
                  <span>{cohort.status}</span>
                  <h3>{cohort.name}</h3>
                  <p>{cohort.criteria}</p>
                  <div className="openrd-card-foot">
                    <small>{cohort.disease_area}</small>
                    <small>目标 {cohort.target_size} 人</small>
                  </div>
                </article>
              )) : <EmptyState>暂未创建虚拟队列。</EmptyState>}
            </div>
          </div>
        </section>

        <section className="result-panel openrd-tech-panel">
          <div className="section-head">
            <span>技术与合规底座</span>
            <span className="section-note">把愿景拆成可交付的工程边界</span>
          </div>
          <div className="openrd-tech-grid">
            {(overview?.technology || []).map((item) => (
              <article key={item.name} className="openrd-tech-card">
                <span>{item.status}</span>
                <strong>{item.name}</strong>
                <p>{item.description}</p>
              </article>
            ))}
          </div>
          <div className="openrd-source-note">
            {(overview?.source_references || []).map((source) => (
              <a key={source.url} href={source.url} target="_blank" rel="noreferrer">
                {source.name} · {source.mapped_capability}
              </a>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}
