import React, { useEffect, useMemo, useRef, useState } from 'react';
import './App.css';

const GITHUB_URL = 'https://github.com/MoKangMedical/medichat-rd';
const A2A_REFERENCE_URL = 'https://mokangmedical.github.io/medroundtable/';
const LIVE_PLATFORM_URL = 'http://43.128.114.201:8000';

const platformMetrics = [
  { value: '121+', label: '覆盖罕见病知识包', note: '围绕患者问题持续扩展' },
  { value: '14+', label: '全球医学数据源', note: '靶点、文献、临床试验联动' },
  { value: '5', label: '核心应用入口', note: '从问诊到试验匹配闭环' },
  { value: 'A2A', label: '多智能体协作模式', note: '一句问题即可拉起工作流' },
];

const coreCapabilities = [
  {
    id: 'ai-chat',
    badge: '01',
    title: 'AI 对话',
    subtitle: 'Rare Disease Copilot',
    desc: '面向患者、医生、研究者的统一对话入口，支持知识问答、病例讨论和任务引导。',
    accent: 'cyan',
  },
  {
    id: 'symptom-check',
    badge: '02',
    title: '症状自查',
    subtitle: 'Phenotype Intake',
    desc: '把自然语言病情描述整理为结构化线索，帮助后续表型分析与问题归因。',
    accent: 'emerald',
  },
  {
    id: 'disease-research',
    badge: '03',
    title: '疾病研究',
    subtitle: 'Evidence Atlas',
    desc: '整合疾病、靶点、药物、文献与试验信息，快速形成一份研究级概览。',
    accent: 'violet',
  },
  {
    id: 'drug-repurposing',
    badge: '04',
    title: '药物重定位',
    subtitle: 'Repurposing Engine',
    desc: '从疾病靶点和既有药物出发，识别值得验证的再利用候选和关键假设。',
    accent: 'amber',
  },
  {
    id: 'trial-matching',
    badge: '05',
    title: '临床试验匹配',
    subtitle: 'Trial Navigator',
    desc: '基于疾病和研究重点筛选 ClinicalTrials 机会，形成下一步联络清单。',
    accent: 'rose',
  },
];

const a2aModes = [
  {
    id: 'auto',
    title: 'Auto Orchestrator',
    label: '一句问题自动编排',
    desc: '用户只描述问题，平台自动走 Intake → Evidence → Report 的默认链路。',
    chain: ['患者入口 Agent', '表型 Agent', '证据 Agent', '报告 Agent'],
  },
  {
    id: 'lead-agent',
    title: 'Lead Agent First',
    label: '先选首位 Agent',
    desc: '借鉴 MedRoundTable 的首位介入逻辑，先选最适合当前阶段的 Agent，再扩展后续节点。',
    chain: ['首位 Agent', '研究 Agent', '工具 Agent', '协作 Agent'],
  },
  {
    id: 'roundtable',
    title: 'A2A Roundtable',
    label: '患者社群圆桌模式',
    desc: '把患者、家属、医生、研究者与 AI 工具放进同一协作回路，形成真正的罕见病社区工作台。',
    chain: ['患者社群', '临床 Agent', '研究 Agent', '试验 Agent', '社群回访'],
  },
];

const a2aLeadAgents = [
  { id: 'patient_intake_agent', label: '患者入口 Agent' },
  { id: 'phenotype_agent', label: '表型 Agent' },
  { id: 'evidence_agent', label: '证据 Agent' },
  { id: 'repurposing_agent', label: '药物重定位 Agent' },
  { id: 'trial_agent', label: '临床试验 Agent' },
  { id: 'community_agent', label: '患者社群 Agent' },
];

const a2aAgentLabelMap = {
  patient_intake_agent: '患者入口 Agent',
  phenotype_agent: '表型 Agent',
  evidence_agent: '证据 Agent',
  repurposing_agent: '药物重定位 Agent',
  trial_agent: '临床试验 Agent',
  community_agent: '患者社群 Agent',
  report_agent: '报告 Agent',
};

const a2aNodes = [
  {
    name: 'Patient Intake Agent',
    role: '患者入口',
    desc: '收集主诉、病程、既往检查和家族史，统一为可分析输入。',
  },
  {
    name: 'Phenotype Agent',
    role: '表型结构化',
    desc: '把症状语言映射成疾病线索、重点表型和候选问题列表。',
  },
  {
    name: 'Evidence Agent',
    role: '证据汇聚',
    desc: '整合 OpenTargets、PubMed、OMIM 等多源证据，产出可读摘要。',
  },
  {
    name: 'Repurposing Agent',
    role: '药物再利用',
    desc: '识别可重定位药物、潜在靶点重叠和待验证机制假说。',
  },
  {
    name: 'Trial Agent',
    role: '试验导航',
    desc: '把疾病阶段与 ClinicalTrials 条目对应起来，筛选值得跟进的机会。',
  },
  {
    name: 'Community Agent',
    role: '患者社群',
    desc: '把生成的解释、教育内容和行动清单回流到患者社群与随访场景。',
  },
];

const flowSteps = [
  {
    step: '01',
    title: '描述问题',
    desc: '输入症状、疑似疾病或研究目标，系统自动识别当前属于问诊、研究还是试验匹配任务。',
  },
  {
    step: '02',
    title: 'AI 分析',
    desc: 'A2A 编排层决定由哪些 Agent 先介入，并串联 MIMO、MCP 与多源数据库完成分析。',
  },
  {
    step: '03',
    title: '获取报告',
    desc: '输出患者友好版结论、研究摘要、候选药物和试验清单，便于继续推进下一步。',
  },
];

const dataSources = [
  { name: 'OpenTargets', type: '靶点与疾病关联' },
  { name: 'ChEMBL', type: '药物与化合物' },
  { name: 'ClinicalTrials', type: '临床试验登记' },
  { name: 'PubMed', type: '文献证据' },
  { name: 'OMIM', type: '遗传病知识' },
  { name: 'KEGG', type: '通路与机制' },
  { name: 'Orphanet', type: '罕见病目录' },
  { name: 'GeneReviews', type: '临床综述' },
  { name: 'HPO', type: '表型词表' },
  { name: 'UniProt', type: '蛋白与功能' },
  { name: 'ClinVar', type: '变异证据' },
  { name: 'DrugBank', type: '药物知识' },
  { name: 'NCBI', type: '基础生物信息' },
  { name: 'Guidelines', type: '指南与共识' },
];

const architectureBlocks = [
  {
    name: 'MIMO',
    desc: '对话推理与报告生成核心，承担患者解释和研究型摘要输出。',
  },
  {
    name: 'FastAPI',
    desc: '统一承载 `/api/v2` 服务接口，负责前后端之间的工作流中枢。',
  },
  {
    name: 'React',
    desc: '构建平台工作台和顶级入口页，让 5 大能力在一个界面里完成切换。',
  },
  {
    name: 'MCP',
    desc: '以工具协议方式接入多源数据检索与分析能力，避免把数据库耦死在单一模块中。',
  },
  {
    name: 'ToolUniverse',
    desc: '作为工具编排层，把 OpenTargets、ChEMBL、ClinicalTrials 等检索统一起来。',
  },
  {
    name: 'CrewAI',
    desc: '延续多 Agent 协作基础，为后续真正的患者社群 A2A 体系保留执行层。',
  },
];

const starterPrompts = [
  '我有长期肌无力和吞咽困难，想先做罕见病方向判断。',
  '请帮我快速研究 Duchenne muscular dystrophy 的靶点和药物。',
  '想看 Fabry disease 还有哪些在招募的临床试验。',
];

const workspaceRecommendations = {
  auto: '默认从患者入口开始，由平台自动调度症状、证据和报告链路。',
  'lead-agent': '优先指定首位 Agent 介入，适合已经明确当前问题阶段的用户。',
  roundtable: '适合要把患者、医生、研究者和社群放进一个协同回路的任务。',
};

const workspaceLeadAgents = {
  'symptom-check': 'phenotype_agent',
  'disease-research': 'evidence_agent',
  'drug-repurposing': 'repurposing_agent',
  'trial-matching': 'trial_agent',
};

function Icon({ name }) {
  const common = {
    fill: 'none',
    stroke: 'currentColor',
    strokeWidth: '1.8',
    strokeLinecap: 'round',
    strokeLinejoin: 'round',
  };

  const paths = {
    spark: (
      <>
        <path {...common} d="M12 3l1.9 4.6L18.5 9l-4.6 1.4L12 15l-1.9-4.6L5.5 9l4.6-1.4L12 3Z" />
        <path {...common} d="M18 15l.8 1.9L21 17.7l-2.2.8L18 20.5l-.8-2-2.2-.8 2.2-.8L18 15Z" />
      </>
    ),
    dna: (
      <>
        <path {...common} d="M4 5c5 4 11 10 16 14" />
        <path {...common} d="M20 5C15 9 9 15 4 19" />
        <path {...common} d="M8 3v4M16 17v4M16 3v4M8 17v4" />
      </>
    ),
    chat: (
      <>
        <path {...common} d="M5 5h14a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H9l-4 4V7a2 2 0 0 1 2-2Z" />
        <path {...common} d="M9 10h6M9 14h4" />
      </>
    ),
    search: (
      <>
        <circle {...common} cx="11" cy="11" r="6.5" />
        <path {...common} d="m20 20-4.5-4.5" />
      </>
    ),
    pill: (
      <>
        <path {...common} d="m8.5 8.5 7 7" />
        <path {...common} d="m9.2 20.2 10-10a4.7 4.7 0 1 0-6.6-6.6l-10 10a4.7 4.7 0 1 0 6.6 6.6Z" />
      </>
    ),
    report: (
      <>
        <path {...common} d="M8 3h6l4 4v14H8a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2Z" />
        <path {...common} d="M14 3v4h4M10 12h6M10 16h6" />
      </>
    ),
    nodes: (
      <>
        <circle {...common} cx="6" cy="6" r="2.5" />
        <circle {...common} cx="18" cy="6" r="2.5" />
        <circle {...common} cx="12" cy="18" r="2.5" />
        <path {...common} d="M8.5 7.2 10.6 15M15.5 7.2 13.4 15M8.4 6h7.2" />
      </>
    ),
    database: (
      <>
        <ellipse {...common} cx="12" cy="5.5" rx="7" ry="2.8" />
        <path {...common} d="M5 5.5v6c0 1.5 3.1 2.8 7 2.8s7-1.3 7-2.8v-6" />
        <path {...common} d="M5 11.5v6c0 1.5 3.1 2.8 7 2.8s7-1.3 7-2.8v-6" />
      </>
    ),
    github: (
      <>
        <path {...common} d="M9 18c-4 1.5-4-2-6-2m12 4v-3.8a3.3 3.3 0 0 0-.9-2.6c3-.3 6.1-1.4 6.1-6.4A5 5 0 0 0 19 3.7 4.7 4.7 0 0 0 18.9 1S17.7.6 15 2.5a13 13 0 0 0-6 0C6.3.6 5.1 1 5.1 1A4.7 4.7 0 0 0 5 3.7 5 5 0 0 0 3.8 7.2c0 5 3.1 6.1 6.1 6.4a3.3 3.3 0 0 0-.9 2.6V20" />
      </>
    ),
    arrow: <path {...common} d="M5 12h14M13 6l6 6-6 6" />,
    workflow: (
      <>
        <rect {...common} x="3" y="4" width="6" height="5" rx="1.5" />
        <rect {...common} x="15" y="4" width="6" height="5" rx="1.5" />
        <rect {...common} x="9" y="15" width="6" height="5" rx="1.5" />
        <path {...common} d="M9 6.5h6M12 9v6" />
      </>
    ),
    target: (
      <>
        <circle {...common} cx="12" cy="12" r="7.5" />
        <circle {...common} cx="12" cy="12" r="3.5" />
        <path {...common} d="M12 2v3M12 19v3M2 12h3M19 12h3" />
      </>
    ),
  };

  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      {paths[name] || paths.spark}
    </svg>
  );
}

function SectionHeader({ eyebrow, title, description, align = 'left' }) {
  return (
    <div className={`section-header ${align === 'center' ? 'centered' : ''}`}>
      {eyebrow ? <div className="section-eyebrow">{eyebrow}</div> : null}
      <h2>{title}</h2>
      {description ? <p>{description}</p> : null}
    </div>
  );
}

function TextBlock({ text }) {
  return (
    <>
      {String(text || '')
        .split('\n')
        .map((line, index) => (
          <p key={`${line}-${index}`}>{line || <br />}</p>
        ))}
    </>
  );
}

async function parseJson(response) {
  const contentType = response.headers.get('content-type') || '';
  const isJson = contentType.includes('application/json');
  const payload = isJson ? await response.json() : await response.text();

  if (!response.ok) {
    if (typeof payload === 'string' && payload) {
      throw new Error(payload);
    }
    if (payload?.detail) {
      throw new Error(typeof payload.detail === 'string' ? payload.detail : JSON.stringify(payload.detail));
    }
    if (payload?.error) {
      throw new Error(payload.error);
    }
    throw new Error(`请求失败 (${response.status})`);
  }

  return payload;
}

function formatA2ATimestamp(value) {
  if (!value) return '刚刚';
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return value;
  return parsed.toLocaleString('zh-CN', { hour12: false });
}

function normalizeA2ASessionState(data) {
  const session = data?.session;
  if (!session) return null;

  return {
    sessionId: session.session_id,
    title: session.title,
    mode: session.mode,
    updatedAt: session.updated_at,
    executedAgents: data.executed_agents || [],
    latestReport: data.latest_report || null,
    artifacts: session.artifacts || [],
    events: (session.events || []).slice(-6).reverse(),
  };
}

async function runA2ASession({
  sessionId,
  mode,
  leadAgent,
  diseaseContext,
  patientProfile,
  source,
  message,
}) {
  const request = sessionId
    ? fetch(`/api/v2/a2a/sessions/${sessionId}/messages`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          content: message,
          disease_context: diseaseContext || undefined,
        }),
      })
    : fetch('/api/v2/a2a/sessions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          mode,
          lead_agent: mode === 'lead-agent' ? leadAgent || undefined : undefined,
          disease_context: diseaseContext || undefined,
          patient_profile: patientProfile || undefined,
          metadata: source ? { source } : undefined,
          initial_message: message,
        }),
      });

  const data = await parseJson(await request);
  return { data, sessionState: normalizeA2ASessionState(data) };
}

function getArtifactContent(sessionState, agentId) {
  const artifact = [...(sessionState?.artifacts || [])]
    .reverse()
    .find((item) => item.agent_id === agentId && item.status === 'completed');
  return artifact?.content || null;
}

function A2ACompactSummary({ sessionState, modeTitle, title = 'A2A 编排结果' }) {
  if (!sessionState) return null;

  return (
    <div className="result-card">
      <div className="card-topline">{title}</div>
      <div className="summary-grid">
        <article className="summary-card">
          <span>Session</span>
          <strong>{sessionState.title || '未命名会话'}</strong>
          <p>{sessionState.sessionId}</p>
        </article>
        <article className="summary-card">
          <span>模式</span>
          <strong>{modeTitle}</strong>
          <p>{sessionState.mode}</p>
        </article>
        <article className="summary-card">
          <span>已执行 Agent</span>
          <strong>{sessionState.executedAgents.length}</strong>
          <p>当前专用工作台已接入真实 orchestration</p>
        </article>
        <article className="summary-card">
          <span>更新时间</span>
          <strong>{formatA2ATimestamp(sessionState.updatedAt)}</strong>
          <p>后端 session 最近一次收敛时间</p>
        </article>
      </div>

      <div className="command-chain session-agent-chain">
        {sessionState.executedAgents.map((agentId) => (
          <span key={agentId}>{a2aAgentLabelMap[agentId] || agentId}</span>
        ))}
      </div>

      {sessionState.latestReport?.summary ? (
        <div className="prose-card">
          <div className="card-topline">汇总摘要</div>
          <TextBlock text={sessionState.latestReport.summary} />
        </div>
      ) : null}
    </div>
  );
}

function AIChatWorkspace({ a2aMode }) {
  const mode = useMemo(() => a2aModes.find((item) => item.id === a2aMode) || a2aModes[0], [a2aMode]);
  const initialMessage = useMemo(
    () => ({
      role: 'assistant',
      content: `已进入 ${mode.label}。\n\n接下来发送的每一条消息都会创建或续写真实的 A2A session，由后端编排多个 Agent 执行，而不是普通单轮聊天。`,
    }),
    [mode.label],
  );
  const [messages, setMessages] = useState([initialMessage]);
  const [input, setInput] = useState('');
  const [diseaseContext, setDiseaseContext] = useState('');
  const [leadAgent, setLeadAgent] = useState('patient_intake_agent');
  const [patientNickname, setPatientNickname] = useState('');
  const [sessionState, setSessionState] = useState(null);
  const [requestError, setRequestError] = useState('');
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' });
  }, [messages, loading]);

  useEffect(() => {
    setMessages([initialMessage]);
    setSessionState(null);
    setInput('');
    setRequestError('');
    setLeadAgent(a2aMode === 'lead-agent' ? 'patient_intake_agent' : '');
  }, [a2aMode, initialMessage]);

  const updateSessionState = (data) => {
    const session = data?.session;
    if (!session) return;

    setSessionState({
      sessionId: session.session_id,
      title: session.title,
      mode: session.mode,
      updatedAt: session.updated_at,
      executedAgents: data.executed_agents || [],
      latestReport: data.latest_report || null,
      events: (session.events || []).slice(-6).reverse(),
    });
  };

  const formatTimestamp = (value) => {
    if (!value) return '刚刚';
    const parsed = new Date(value);
    if (Number.isNaN(parsed.getTime())) return value;
    return parsed.toLocaleString('zh-CN', { hour12: false });
  };

  const sendMessage = async (preset) => {
    const nextContent = typeof preset === 'string' ? preset : input;
    if (!nextContent.trim() || loading) return;

    const userMessage = { role: 'user', content: nextContent.trim() };
    const nextMessages = [...messages, userMessage];
    setMessages(nextMessages);
    setInput('');
    setRequestError('');
    setLoading(true);

    try {
      const trimmedDisease = diseaseContext.trim();
      const trimmedNickname = patientNickname.trim();
      const request = sessionState?.sessionId
        ? fetch(`/api/v2/a2a/sessions/${sessionState.sessionId}/messages`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              content: nextContent.trim(),
              disease_context: trimmedDisease || undefined,
            }),
          })
        : fetch('/api/v2/a2a/sessions', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              mode: a2aMode,
              lead_agent: a2aMode === 'lead-agent' ? leadAgent || undefined : undefined,
              disease_context: trimmedDisease || undefined,
              patient_profile: trimmedNickname
                ? {
                    nickname: trimmedNickname,
                    disease_type: trimmedDisease || undefined,
                  }
                : undefined,
              metadata: {
                source: 'ai-chat-workspace',
              },
              initial_message: nextContent.trim(),
            }),
          });

      const data = await parseJson(await request);
      updateSessionState(data);

      const assistantContent =
        data.assistant_message || data.latest_report?.summary || 'A2A session 已更新，但当前没有返回文本摘要。';

      setMessages((prev) => [...prev, { role: 'assistant', content: assistantContent }]);
    } catch (error) {
      setRequestError(error.message);
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: `当前无法完成 A2A 编排请求。\n\n原因：${error.message}\n\n你可以稍后重试，或改用下方专用工作台继续操作。`,
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="workspace-stack">
      <div className="workspace-banner">
        <div>
          <span className="workspace-banner-kicker">当前协作模式</span>
          <strong>{mode.label}</strong>
        </div>
        <p>{workspaceRecommendations[mode.id]}</p>
      </div>

      <div className="field-grid split">
        <label className="field">
          <span>疾病上下文</span>
          <input
            value={diseaseContext}
            onChange={(event) => setDiseaseContext(event.target.value)}
            placeholder="可选，如：Pompe disease / SMA / Fabry disease"
          />
        </label>
        {a2aMode === 'lead-agent' ? (
          <label className="field">
            <span>首位 Agent</span>
            <select value={leadAgent} onChange={(event) => setLeadAgent(event.target.value)}>
              {a2aLeadAgents.map((agent) => (
                <option key={agent.id} value={agent.id}>
                  {agent.label}
                </option>
              ))}
            </select>
          </label>
        ) : null}
        {a2aMode === 'roundtable' ? (
          <label className="field">
            <span>患者昵称</span>
            <input
              value={patientNickname}
              onChange={(event) => setPatientNickname(event.target.value)}
              placeholder="可选，用于生成患者社群分身"
            />
          </label>
        ) : null}
      </div>

      <div className="prompt-row">
        {starterPrompts.map((prompt) => (
          <button key={prompt} type="button" className="ghost-chip" onClick={() => sendMessage(prompt)}>
            {prompt}
          </button>
        ))}
      </div>

      {requestError ? <div className="error-card">{requestError}</div> : null}

      {sessionState ? (
        <>
          <div className="summary-grid">
            <article className="summary-card">
              <span>A2A Session</span>
              <strong>{sessionState.title || '未命名会话'}</strong>
              <p>{sessionState.sessionId}</p>
            </article>
            <article className="summary-card">
              <span>协作模式</span>
              <strong>{mode.title}</strong>
              <p>{sessionState.mode}</p>
            </article>
            <article className="summary-card">
              <span>已执行 Agent</span>
              <strong>{sessionState.executedAgents.length}</strong>
              <p>每条消息都会续写同一个 orchestration session</p>
            </article>
            <article className="summary-card">
              <span>最近更新时间</span>
              <strong>{formatTimestamp(sessionState.updatedAt)}</strong>
              <p>后端返回的最新 session 时间戳</p>
            </article>
          </div>

          <div className="result-layout">
            <div className="result-card">
              <div className="card-topline">执行链路</div>
              <div className="command-chain session-agent-chain">
                {sessionState.executedAgents.map((agentId) => (
                  <span key={agentId}>{a2aAgentLabelMap[agentId] || agentId}</span>
                ))}
              </div>
              {sessionState.latestReport?.next_steps?.length ? (
                <div className="chain-list">
                  {sessionState.latestReport.next_steps.map((step, index) => (
                    <div key={`${step}-${index}`} className="chain-item">
                      <span>{String(index + 1).padStart(2, '0')}</span>
                      <div>
                        <strong>下一步行动</strong>
                        <p>{step}</p>
                      </div>
                    </div>
                  ))}
                </div>
              ) : null}
            </div>

            <div className="result-card prose-card">
              <div className="card-topline">最新汇总报告</div>
              <TextBlock text={sessionState.latestReport?.summary || '当前还没有生成报告摘要。'} />
            </div>

            <div className="result-card wide-card">
              <div className="card-topline">最近事件</div>
              <div className="list-stack">
                {sessionState.events.map((event) => (
                  <article key={event.event_id} className="list-card">
                    <div className="list-card-top">
                      <code>{a2aAgentLabelMap[event.agent_id] || event.agent_id}</code>
                      <span>{event.status || 'completed'}</span>
                    </div>
                    <strong>{event.headline}</strong>
                    <p>{event.detail}</p>
                  </article>
                ))}
              </div>
            </div>
          </div>
        </>
      ) : null}

      <div className="chat-shell">
        <div className="chat-messages">
          {messages.map((message, index) => (
            <article key={`${message.role}-${index}`} className={`chat-card ${message.role}`}>
              <div className="chat-avatar">{message.role === 'assistant' ? 'AI' : '你'}</div>
              <div className="chat-copy">
                <TextBlock text={message.content} />
              </div>
            </article>
          ))}
          {loading ? (
            <article className="chat-card assistant">
              <div className="chat-avatar">AI</div>
              <div className="chat-copy">
                <div className="typing-dots">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            </article>
          ) : null}
          <div ref={bottomRef} />
        </div>

        <div className="chat-compose">
          <textarea
            value={input}
            onChange={(event) => setInput(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === 'Enter' && !event.shiftKey) {
                event.preventDefault();
                sendMessage();
              }
            }}
            placeholder="输入你的病例线索、研究目标或社群问题。按 Enter 发送，Shift + Enter 换行。"
            rows={4}
          />
          <button type="button" className="primary-button" disabled={loading || !input.trim()} onClick={() => sendMessage()}>
            <Icon name="arrow" />
            发送到 A2A 总线
          </button>
        </div>
      </div>
    </div>
  );
}

function SymptomCheckWorkspace({ a2aMode }) {
  const mode = useMemo(() => a2aModes.find((item) => item.id === a2aMode) || a2aModes[0], [a2aMode]);
  const [symptoms, setSymptoms] = useState('');
  const [age, setAge] = useState('');
  const [gender, setGender] = useState('');
  const [sessionState, setSessionState] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const phenotypeReport = getArtifactContent(sessionState, 'phenotype_agent');
  const evidenceReport = getArtifactContent(sessionState, 'evidence_agent');

  useEffect(() => {
    setSessionState(null);
    setError('');
  }, [a2aMode]);

  const analyze = async () => {
    if (!symptoms.trim() || loading) return;
    setLoading(true);
    setError('');

    try {
      const profile = age || gender
        ? {
            age: age ? Number(age) : undefined,
            gender: gender || undefined,
          }
        : undefined;
      const message = [
        '请从罕见病视角做一次症状分诊和表型分析。',
        `症状描述：${symptoms.trim()}`,
        age ? `年龄：${age}` : null,
        gender ? `性别：${gender}` : null,
        '请优先输出候选疾病、推荐检查、下一步行动，并在需要时衔接证据与试验方向。',
      ]
        .filter(Boolean)
        .join('\n');

      const { sessionState: nextSessionState } = await runA2ASession({
        sessionId: sessionState?.sessionId,
        mode: a2aMode,
        leadAgent: workspaceLeadAgents['symptom-check'],
        diseaseContext: '',
        patientProfile: profile,
        source: 'symptom-check-workspace',
        message,
      });
      setSessionState(nextSessionState);
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="workspace-stack">
      <div className="field-grid">
        <label className="field field-large">
          <span>症状描述</span>
          <textarea
            rows={7}
            value={symptoms}
            onChange={(event) => setSymptoms(event.target.value)}
            placeholder="示例：近半年逐渐加重的肌无力，下午更明显，伴吞咽困难和上睑下垂。"
          />
        </label>

        <div className="field-column">
          <label className="field">
            <span>年龄</span>
            <input value={age} onChange={(event) => setAge(event.target.value)} placeholder="选填，如 16" type="number" />
          </label>
          <label className="field">
            <span>性别</span>
            <select value={gender} onChange={(event) => setGender(event.target.value)}>
              <option value="">选填</option>
              <option value="男">男</option>
              <option value="女">女</option>
            </select>
          </label>
          <div className="mini-note">
            <strong>{mode.label}</strong>
            <p>当前工作台会直接创建或续写真实 A2A session，并以表型 Agent 作为症状入口。</p>
          </div>
          <button type="button" className="primary-button full-width" disabled={loading || !symptoms.trim()} onClick={analyze}>
            <Icon name="search" />
            {loading ? 'A2A 分析中...' : '开始症状分析'}
          </button>
        </div>
      </div>

      {error ? <div className="error-card">{error}</div> : null}

      {sessionState ? (
        <div className="result-layout">
          <div className="result-card prose-card">
            <div className="card-topline">分析结果</div>
            <TextBlock text={sessionState.latestReport?.summary || '当前 session 尚未返回最终摘要。'} />
          </div>
          <div className="result-card">
            <div className="card-topline">候选疾病与检查建议</div>
            {phenotypeReport?.candidate_diseases?.length ? (
              <div className="list-stack">
                {phenotypeReport.candidate_diseases.map((candidate) => (
                  <article key={`${candidate.name_en}-${candidate.omim_id}`} className="list-card">
                    <div className="list-card-top">
                      <code>{candidate.omim_id || 'OMIM 待补充'}</code>
                      <span>{candidate.confidence}%</span>
                    </div>
                    <strong>{candidate.name_cn}</strong>
                    <p>{candidate.name_en}</p>
                    <p>基因：{candidate.gene || '待确认'}</p>
                    {candidate.matched_symptoms?.length ? <p>匹配症状：{candidate.matched_symptoms.join('、')}</p> : null}
                  </article>
                ))}
              </div>
            ) : (
              <div className="empty-card">当前没有产出明确候选疾病，建议补充更完整的病程和检查信息。</div>
            )}
          </div>
          <div className="result-card">
            <div className="card-topline">A2A 下一步</div>
            <div className="chain-list">
              {(phenotypeReport?.recommended_tests || []).map((test, index) => (
                <div key={`${test}-${index}`} className="chain-item">
                  <span>{String(index + 1).padStart(2, '0')}</span>
                  <div>
                    <strong>推荐检查</strong>
                    <p>{test}</p>
                  </div>
                </div>
              ))}
              {!(phenotypeReport?.recommended_tests || []).length ? (
                <div className="chain-item">
                  <span>01</span>
                  <div>
                    <strong>继续补充表型</strong>
                    <p>当前没有结构化检查建议，建议补充病程、家族史和既往检查结果。</p>
                  </div>
                </div>
              ) : null}
            </div>
            {evidenceReport?.resolved_disease ? (
              <div className="warning-box">
                当前证据链已进一步锁定为 {evidenceReport.resolved_disease.display_name}，可以继续转入研究或试验匹配。
              </div>
            ) : (
              <div className="warning-box">本分析仅供参考，不构成医疗诊断。如有疑虑，请咨询专业医生。</div>
            )}
          </div>
          <A2ACompactSummary sessionState={sessionState} modeTitle={mode.title} title="本次症状分析对应的 A2A Session" />
        </div>
      ) : null}
    </div>
  );
}

function DiseaseResearchWorkspace({ a2aMode }) {
  const mode = useMemo(() => a2aModes.find((item) => item.id === a2aMode) || a2aModes[0], [a2aMode]);
  const [disease, setDisease] = useState('');
  const [sessionState, setSessionState] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState('overview');

  const evidenceReport = getArtifactContent(sessionState, 'evidence_agent');
  const repurposingReport = getArtifactContent(sessionState, 'repurposing_agent');
  const trialReport = getArtifactContent(sessionState, 'trial_agent');

  useEffect(() => {
    setSessionState(null);
    setError('');
  }, [a2aMode]);

  const research = async () => {
    if (!disease.trim() || loading) return;
    setLoading(true);
    setError('');

    try {
      const { sessionState: nextSessionState } = await runA2ASession({
        sessionId: sessionState?.sessionId,
        mode: a2aMode,
        leadAgent: workspaceLeadAgents['disease-research'],
        diseaseContext: disease.trim(),
        source: 'disease-research-workspace',
        message: `请对 ${disease.trim()} 做一轮罕见病研究，重点整合疾病概览、靶点、文献、药物重定位与临床试验。`,
      });

      setSessionState(nextSessionState);
      setActiveTab('overview');
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setLoading(false);
    }
  };

  const tabs = [
    { id: 'overview', label: '疾病概览' },
    { id: 'targets', label: `靶点 ${evidenceReport?.targets?.length || 0}` },
    { id: 'literature', label: `文献 ${evidenceReport?.literature?.length || 0}` },
    { id: 'drugs', label: `药物 ${repurposingReport?.candidate_drugs?.length || 0}` },
    { id: 'trials', label: `试验 ${trialReport?.trials?.length || 0}` },
    { id: 'analysis', label: 'AI 报告' },
  ];

  return (
    <div className="workspace-stack">
      <div className="search-strip">
        <input
          value={disease}
          onChange={(event) => setDisease(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === 'Enter') {
              event.preventDefault();
              research();
            }
          }}
          placeholder="输入疾病名称，如 Duchenne muscular dystrophy / Pompe disease"
        />
        <button type="button" className="primary-button" disabled={loading || !disease.trim()} onClick={research}>
          <Icon name="target" />
          {loading ? '研究中...' : '生成研究图谱'}
        </button>
      </div>

      {error ? <div className="error-card">{error}</div> : null}
      {loading ? <div className="loading-card">正在通过真实 A2A session 整合疾病、靶点、文献、药物和试验数据...</div> : null}

      {sessionState ? (
        <>
          <div className="summary-grid">
            <article className="summary-card">
              <span>疾病</span>
              <strong>{evidenceReport?.resolved_disease?.display_name || disease}</strong>
              <p>{evidenceReport?.resolved_disease?.disease_id || '等待补充 ID'}</p>
            </article>
            <article className="summary-card">
              <span>靶点候选</span>
              <strong>{evidenceReport?.targets?.length || 0}</strong>
              <p>当前来自 A2A 证据 Agent 的靶点汇聚</p>
            </article>
            <article className="summary-card">
              <span>药物候选</span>
              <strong>{repurposingReport?.candidate_drugs?.length || 0}</strong>
              <p>当前来自药物重定位 Agent 的候选池</p>
            </article>
            <article className="summary-card">
              <span>临床试验</span>
              <strong>{trialReport?.trials?.length || 0}</strong>
              <p>当前来自 Trial Agent 的试验导航结果</p>
            </article>
          </div>

          <div className="tab-row">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                type="button"
                className={`tab-pill ${activeTab === tab.id ? 'active' : ''}`}
                onClick={() => setActiveTab(tab.id)}
              >
                {tab.label}
              </button>
            ))}
          </div>

          <div className="result-card">
            {activeTab === 'overview' ? (
              <div className="prose-card">
                <div className="card-topline">疾病概览</div>
                <h3>{evidenceReport?.resolved_disease?.display_name || disease}</h3>
                <p>疾病查询：{evidenceReport?.resolved_disease?.query || disease}</p>
                <p>Disease ID：{evidenceReport?.resolved_disease?.disease_id || '待补充'}</p>
                <p>OMIM：{evidenceReport?.resolved_disease?.omim_id || '待补充'}</p>
                <p>关键基因：{evidenceReport?.resolved_disease?.gene || '待补充'}</p>
                <TextBlock text={sessionState.latestReport?.summary || '当前未生成最终汇总，可继续查看结构化研究结果。'} />
              </div>
            ) : null}

            {activeTab === 'targets' ? (
              <div className="card-grid">
                {(evidenceReport?.targets || []).map((target) => (
                  <article key={target.gene_id} className="mini-card">
                    <div className="mini-card-top">
                      <code>{target.gene_id?.split(':').pop()}</code>
                      <span>{target.score}</span>
                    </div>
                    <strong>{target.gene_name}</strong>
                    <p>当前为 A2A 证据图谱中的关联靶点。</p>
                  </article>
                ))}
              </div>
            ) : null}

            {activeTab === 'literature' ? (
              <div className="list-stack">
                {(evidenceReport?.literature || []).map((article) => (
                  <article key={`${article.pmid}-${article.title}`} className="list-card">
                    <div className="list-card-top">
                      <code>{article.pmid || 'PMID'}</code>
                      <span>{article.journal || 'PubMed'}</span>
                    </div>
                    <strong>{article.title}</strong>
                    {article.summary ? <p>{article.summary}</p> : null}
                  </article>
                ))}
              </div>
            ) : null}

            {activeTab === 'drugs' ? (
              <div className="card-grid">
                {(repurposingReport?.candidate_drugs || []).map((drug) => (
                  <article key={`${drug.chembl_id}-${drug.mesh_heading}`} className="mini-card">
                    <div className="mini-card-top">
                      <code>{drug.chembl_id}</code>
                      <span>{drug.max_phase ?? '阶段未知'}</span>
                    </div>
                    <strong>{drug.mesh_heading}</strong>
                    <p>最高临床阶段：{drug.max_phase ?? '-'}</p>
                  </article>
                ))}
              </div>
            ) : null}

            {activeTab === 'trials' ? (
              <div className="list-stack">
                {(trialReport?.trials || []).map((trial) => (
                  <article key={trial.nct_id} className="list-card">
                    <div className="list-card-top">
                      <code>{trial.nct_id}</code>
                      <span>{trial.status}</span>
                    </div>
                    <strong>{trial.title}</strong>
                    <p>{trial.sponsor}</p>
                    {trial.summary ? <p>{trial.summary}</p> : null}
                  </article>
                ))}
              </div>
            ) : null}

            {activeTab === 'analysis' ? (
              <div className="prose-card">
                <div className="card-topline">AI 研究报告</div>
                <TextBlock text={sessionState.latestReport?.summary || '当前未生成 A2A 汇总报告。'} />
              </div>
            ) : null}
          </div>

          <A2ACompactSummary sessionState={sessionState} modeTitle={mode.title} title="本次疾病研究对应的 A2A Session" />
        </>
      ) : null}
    </div>
  );
}

function DrugRepurposingWorkspace({ a2aMode }) {
  const mode = useMemo(() => a2aModes.find((item) => item.id === a2aMode) || a2aModes[0], [a2aMode]);
  const [disease, setDisease] = useState('');
  const [sessionState, setSessionState] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const evidenceReport = getArtifactContent(sessionState, 'evidence_agent');
  const repurposingReport = getArtifactContent(sessionState, 'repurposing_agent');

  useEffect(() => {
    setSessionState(null);
    setError('');
  }, [a2aMode]);

  const analyze = async () => {
    if (!disease.trim() || loading) return;
    setLoading(true);
    setError('');

    try {
      const { sessionState: nextSessionState } = await runA2ASession({
        sessionId: sessionState?.sessionId,
        mode: a2aMode,
        leadAgent: workspaceLeadAgents['drug-repurposing'],
        diseaseContext: disease.trim(),
        source: 'drug-repurposing-workspace',
        message: `请对 ${disease.trim()} 进行药物重定位分析，输出候选药物、靶点线索、验证假设和风险提示。`,
      });
      setSessionState(nextSessionState);
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="workspace-stack">
      <div className="search-strip">
        <input
          value={disease}
          onChange={(event) => setDisease(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === 'Enter') {
              event.preventDefault();
              analyze();
            }
          }}
          placeholder="输入待分析疾病，如 Fabry disease / ALS / Gaucher disease"
        />
        <button type="button" className="primary-button" disabled={loading || !disease.trim()} onClick={analyze}>
          <Icon name="pill" />
          {loading ? 'A2A 分析中...' : '生成重定位候选'}
        </button>
      </div>

      {error ? <div className="error-card">{error}</div> : null}
      {loading ? <div className="loading-card">正在通过 A2A session 比对疾病靶点、既有药物和再利用机会...</div> : null}

      {sessionState ? (
        <div className="result-layout">
          <div className="result-card">
            <div className="card-topline">候选靶点</div>
            <div className="card-grid">
              {(evidenceReport?.targets || []).map((target) => (
                <article key={target.gene_id} className="mini-card">
                  <div className="mini-card-top">
                    <code>{target.gene_id?.split(':').pop()}</code>
                    <span>{target.score}</span>
                  </div>
                  <strong>{target.gene_name}</strong>
                  <p>当前来自 Evidence Agent 的候选靶点。</p>
                </article>
              ))}
            </div>
          </div>

          <div className="result-card">
            <div className="card-topline">已知药物池</div>
            <div className="card-grid">
              {(repurposingReport?.candidate_drugs || []).slice(0, 8).map((drug) => (
                <article key={`${drug.chembl_id}-${drug.mesh_heading}`} className="mini-card">
                  <div className="mini-card-top">
                    <code>{drug.chembl_id}</code>
                    <span>{drug.max_phase ?? '阶段未知'}</span>
                  </div>
                  <strong>{drug.mesh_heading}</strong>
                  <p>最大临床阶段：{drug.max_phase ?? '-'}</p>
                </article>
              ))}
            </div>
          </div>

          <div className="result-card prose-card wide-card">
            <div className="card-topline">重定位分析报告</div>
            <TextBlock text={sessionState.latestReport?.summary || '当前未生成 A2A 汇总报告。'} />
            {repurposingReport?.target_hints?.length ? (
              <>
                <div className="card-topline">靶点线索</div>
                <div className="command-chain session-agent-chain">
                  {repurposingReport.target_hints.map((target) => (
                    <span key={target}>{target}</span>
                  ))}
                </div>
              </>
            ) : null}
            {repurposingReport?.recommendation?.length ? (
              <div className="chain-list">
                {repurposingReport.recommendation.map((item, index) => (
                  <div key={`${item}-${index}`} className="chain-item">
                    <span>{String(index + 1).padStart(2, '0')}</span>
                    <div>
                      <strong>验证建议</strong>
                      <p>{item}</p>
                    </div>
                  </div>
                ))}
              </div>
            ) : null}
          </div>

          <A2ACompactSummary sessionState={sessionState} modeTitle={mode.title} title="本次药物重定位对应的 A2A Session" />
        </div>
      ) : null}
    </div>
  );
}

function TrialMatchingWorkspace({ a2aMode }) {
  const mode = useMemo(() => a2aModes.find((item) => item.id === a2aMode) || a2aModes[0], [a2aMode]);
  const [disease, setDisease] = useState('');
  const [focus, setFocus] = useState('');
  const [recruitingOnly, setRecruitingOnly] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [sessionState, setSessionState] = useState(null);

  const trialReport = getArtifactContent(sessionState, 'trial_agent');

  useEffect(() => {
    setSessionState(null);
    setError('');
  }, [a2aMode]);

  const matchTrials = async () => {
    if (!disease.trim() || loading) return;
    setLoading(true);
    setError('');

    try {
      const focusText = focus.trim();
      const { sessionState: nextSessionState } = await runA2ASession({
        sessionId: sessionState?.sessionId,
        mode: a2aMode,
        leadAgent: workspaceLeadAgents['trial-matching'],
        diseaseContext: disease.trim(),
        source: 'trial-matching-workspace',
        message: [
          `请为 ${disease.trim()} 匹配临床试验。`,
          focusText ? `匹配重点：${focusText}` : null,
          recruitingOnly ? '优先保留正在招募中的试验。' : '请返回所有关键试验并说明状态。',
        ]
          .filter(Boolean)
          .join('\n'),
      });
      setSessionState(nextSessionState);
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setLoading(false);
    }
  };

  const filteredTrials = useMemo(() => {
    const trials = trialReport?.trials || [];
    const keyword = focus.trim().toLowerCase();
    return trials.filter((trial) => {
      const matchesStatus = recruitingOnly ? trial.status?.toLowerCase() === 'recruiting' : true;
      const haystack = `${trial.title || ''} ${trial.summary || ''} ${trial.sponsor || ''}`.toLowerCase();
      const matchesKeyword = keyword ? haystack.includes(keyword) : true;
      return matchesStatus && matchesKeyword;
    });
  }, [focus, recruitingOnly, trialReport]);

  return (
    <div className="workspace-stack">
      <div className="field-grid compact-grid">
        <label className="field">
          <span>疾病</span>
          <input
            value={disease}
            onChange={(event) => setDisease(event.target.value)}
            placeholder="如 SMA / Pompe disease"
          />
        </label>
        <label className="field">
          <span>匹配重点</span>
          <input
            value={focus}
            onChange={(event) => setFocus(event.target.value)}
            placeholder="可选，如 gene therapy / pediatric / respiratory"
          />
        </label>
        <label className="field checkbox-field">
          <span>状态过滤</span>
          <div className="checkbox-chip">
            <input
              id="recruitingOnly"
              type="checkbox"
              checked={recruitingOnly}
              onChange={(event) => setRecruitingOnly(event.target.checked)}
            />
            <label htmlFor="recruitingOnly">仅看招募中试验</label>
          </div>
        </label>
      </div>

      <button type="button" className="primary-button fit-button" disabled={loading || !disease.trim()} onClick={matchTrials}>
        <Icon name="workflow" />
        {loading ? '匹配中...' : '开始试验匹配'}
      </button>

      {error ? <div className="error-card">{error}</div> : null}
      {loading ? <div className="loading-card">正在通过 A2A session 检索 ClinicalTrials 条目并按当前重点筛选...</div> : null}

      {sessionState ? (
        <>
          <div className="summary-grid">
            <article className="summary-card">
              <span>疾病</span>
              <strong>{disease}</strong>
              <p>当前匹配以疾病维度进行试验筛选</p>
            </article>
            <article className="summary-card">
              <span>总试验数</span>
              <strong>{trialReport?.trials?.length || 0}</strong>
              <p>Trial Agent 返回的原始试验数</p>
            </article>
            <article className="summary-card">
              <span>筛选后</span>
              <strong>{filteredTrials.length}</strong>
              <p>按关键词与状态过滤后的候选</p>
            </article>
          </div>

          <div className="list-stack">
            {filteredTrials.length ? (
              filteredTrials.map((trial) => (
                <article key={trial.nct_id} className="list-card">
                  <div className="list-card-top">
                    <code>{trial.nct_id}</code>
                    <span>{trial.status_cn || trial.status}</span>
                  </div>
                  <strong>{trial.title}</strong>
                  <p>{trial.sponsor}</p>
                  {trial.summary ? <p>{trial.summary}</p> : null}
                </article>
              ))
            ) : (
              <div className="empty-card">当前过滤条件下没有匹配试验，建议取消“仅看招募中”或换一个关键词。</div>
            )}
          </div>

          {trialReport?.next_steps?.length ? (
            <div className="result-card">
              <div className="card-topline">试验跟进建议</div>
              <div className="chain-list">
                {trialReport.next_steps.map((step, index) => (
                  <div key={`${step}-${index}`} className="chain-item">
                    <span>{String(index + 1).padStart(2, '0')}</span>
                    <div>
                      <strong>下一步</strong>
                      <p>{step}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : null}

          <A2ACompactSummary sessionState={sessionState} modeTitle={mode.title} title="本次试验匹配对应的 A2A Session" />
        </>
      ) : null}
    </div>
  );
}

function App() {
  const [activeCapability, setActiveCapability] = useState('ai-chat');
  const [a2aMode, setA2AMode] = useState('auto');
  const [health, setHealth] = useState({ state: 'loading', detail: '连接平台中...' });
  const workbenchRef = useRef(null);

  useEffect(() => {
    let cancelled = false;

    const loadHealth = async () => {
      try {
        const data = await parseJson(await fetch('/api/health'));
        if (cancelled) return;
        setHealth({
          state: 'healthy',
          detail: data.a2a_available
            ? data.mimo_configured
              ? 'API 在线，A2A 与 MIMO 已就绪'
              : 'API 在线，A2A 已就绪，等待模型配置'
            : 'API 在线，A2A 尚未接通',
        });
      } catch (error) {
        if (cancelled) return;
        setHealth({
          state: 'degraded',
          detail: 'API 状态未知，界面仍可继续使用',
        });
      }
    };

    loadHealth();
    return () => {
      cancelled = true;
    };
  }, []);

  const activeCapabilityMeta = useMemo(
    () => coreCapabilities.find((item) => item.id === activeCapability) || coreCapabilities[0],
    [activeCapability],
  );
  const activeMode = useMemo(() => a2aModes.find((item) => item.id === a2aMode) || a2aModes[0], [a2aMode]);

  const openWorkbench = (capabilityId = 'ai-chat') => {
    setActiveCapability(capabilityId);
    requestAnimationFrame(() => {
      workbenchRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    });
  };

  const activateMode = (modeId, capabilityId = activeCapability) => {
    setA2AMode(modeId);
    openWorkbench(capabilityId);
  };

  const renderWorkspace = () => {
    switch (activeCapability) {
      case 'symptom-check':
        return <SymptomCheckWorkspace a2aMode={a2aMode} />;
      case 'disease-research':
        return <DiseaseResearchWorkspace a2aMode={a2aMode} />;
      case 'drug-repurposing':
        return <DrugRepurposingWorkspace a2aMode={a2aMode} />;
      case 'trial-matching':
        return <TrialMatchingWorkspace a2aMode={a2aMode} />;
      case 'ai-chat':
      default:
        return <AIChatWorkspace a2aMode={a2aMode} />;
    }
  };

  return (
    <div className="platform-shell">
      <header className="platform-nav">
        <a href="#top" className="brand-mark">
          <span className="brand-icon">
            <Icon name="dna" />
          </span>
          <span>
            <strong>MediChat-RD</strong>
            <small>Rare Disease A2A Platform</small>
          </span>
        </a>

        <nav className="nav-links">
          <a href="#capabilities">核心能力</a>
          <a href="#a2a">A2A 模式</a>
          <a href="#sources">数据源</a>
          <a href="#architecture">技术架构</a>
          <a href="#workbench">工作台</a>
        </nav>

        <div className="nav-actions">
          <a className="nav-link-button" href="/landing">
            介绍页
          </a>
          <a className="nav-link-button" href={GITHUB_URL} target="_blank" rel="noreferrer">
            GitHub
          </a>
        </div>
      </header>

      <main>
        <section id="top" className="hero-panel">
          <div className="hero-copy">
            <div className="hero-kicker">
              <span className={`status-dot ${health.state}`}></span>
              {health.detail}
            </div>
            <h1>
              顶级罕见病平台
              <span>把患者入口、A2A 协作和研究工作台放在同一个界面里</span>
            </h1>
            <p className="hero-description">
              这是一个面向患者、医生、研究者与患者社群的罕见病智能平台。它既保留 MediChat-RD 的研究能力，
              也吸收 MedRoundTable 的 A2A 入口逻辑，让你可以一句问题直接开始，或先选首位 Agent 再启动完整流程。
            </p>

            <div className="hero-actions">
              <button type="button" className="primary-button" onClick={() => openWorkbench('ai-chat')}>
                <Icon name="chat" />
                进入工作台
              </button>
              <button type="button" className="secondary-button" onClick={() => activateMode('roundtable', 'symptom-check')}>
                <Icon name="nodes" />
                启动 A2A 圆桌模式
              </button>
            </div>

            <div className="hero-links">
              <a href={LIVE_PLATFORM_URL} target="_blank" rel="noreferrer">
                在线平台
              </a>
              <a href={A2A_REFERENCE_URL} target="_blank" rel="noreferrer">
                MedRoundTable A2A 参考
              </a>
              <a href={GITHUB_URL} target="_blank" rel="noreferrer">
                仓库源码
              </a>
            </div>
          </div>

          <aside className="hero-command-card">
            <div className="command-topline">
              <span>平台主控台</span>
              <strong>{activeMode.label}</strong>
            </div>
            <div className="mode-grid">
              {a2aModes.map((mode) => (
                <button
                  key={mode.id}
                  type="button"
                  className={`mode-card ${a2aMode === mode.id ? 'active' : ''}`}
                  onClick={() => activateMode(mode.id)}
                >
                  <strong>{mode.title}</strong>
                  <p>{mode.desc}</p>
                </button>
              ))}
            </div>
            <div className="command-chain">
              {activeMode.chain.map((item) => (
                <span key={item}>{item}</span>
              ))}
            </div>
          </aside>
        </section>

        <section className="metric-strip">
          {platformMetrics.map((metric) => (
            <article key={metric.label} className="metric-card">
              <strong>{metric.value}</strong>
              <span>{metric.label}</span>
              <p>{metric.note}</p>
            </article>
          ))}
        </section>

        <section id="capabilities" className="content-section">
          <SectionHeader
            eyebrow="5 大核心能力"
            title="从一条主诉到一份可执行报告，全部落在同一个平台工作台里"
            description="平台保留对话、症状、研究、重定位和试验匹配 5 个入口。每个入口都能被 A2A 编排层接管，而不是孤立的单点工具。"
            align="center"
          />

          <div className="capability-grid">
            {coreCapabilities.map((capability) => (
              <button
                key={capability.id}
                type="button"
                className={`capability-card accent-${capability.accent} ${activeCapability === capability.id ? 'selected' : ''}`}
                onClick={() => openWorkbench(capability.id)}
              >
                <div className="capability-badge">{capability.badge}</div>
                <strong>{capability.title}</strong>
                <span>{capability.subtitle}</span>
                <p>{capability.desc}</p>
              </button>
            ))}
          </div>
        </section>

        <section id="a2a" className="content-section section-contrast">
          <SectionHeader
            eyebrow="A2A 模式"
            title="把 MedRoundTable 的 A2A 入口逻辑真正并入罕见病平台"
            description="这里不只是加一个“多人模式”按钮，而是让平台支持三种启动方式：自动编排、先选首位 Agent、患者社群圆桌。"
            align="center"
          />

          <div className="a2a-layout">
            <div className="node-grid">
              {a2aNodes.map((node, index) => (
                <article key={node.name} className="node-card">
                  <span className="node-index">0{index + 1}</span>
                  <strong>{node.role}</strong>
                  <h3>{node.name}</h3>
                  <p>{node.desc}</p>
                </article>
              ))}
            </div>

            <div className="a2a-summary">
              <div className="summary-panel">
                <span className="summary-kicker">协作解释</span>
                <h3>一句话就能开始，或先指定谁来带队</h3>
                <p>
                  这套 A2A 模式复用了 MedRoundTable 的关键思想：入口先服务于“问题如何被接住”，而不是先让用户学习整个平台。
                  对罕见病平台来说，这意味着患者也能从社群入口进入，而医生和研究者则可以从首位 Agent 入口切入。
                </p>
              </div>
              <div className="summary-panel">
                <span className="summary-kicker">当前工作台建议</span>
                <h3>{activeCapabilityMeta.title}</h3>
                <p>{activeCapabilityMeta.desc}</p>
                <button type="button" className="secondary-button full-width" onClick={() => openWorkbench(activeCapabilityMeta.id)}>
                  打开当前能力
                </button>
              </div>
            </div>
          </div>
        </section>

        <section className="content-section">
          <SectionHeader
            eyebrow="3 步使用流程"
            title="描述问题 → AI 分析 → 获取报告"
            description="无论是患者问题、疾病研究还是试验匹配，统一使用三段式交互，确保平台对外有一致的操作心智。"
            align="center"
          />

          <div className="flow-grid">
            {flowSteps.map((step) => (
              <article key={step.step} className="flow-card">
                <span>{step.step}</span>
                <strong>{step.title}</strong>
                <p>{step.desc}</p>
              </article>
            ))}
          </div>
        </section>

        <section id="sources" className="content-section">
          <SectionHeader
            eyebrow="14+ 数据源"
            title="不只写名字，而是把数据源清楚地挂到能力与流程上"
            description="OpenTargets、ChEMBL、ClinicalTrials、PubMed、OMIM、KEGG 等会分别进入靶点、药物、文献和试验不同节点，而不是统一丢给一个黑盒。"
            align="center"
          />

          <div className="source-grid">
            {dataSources.map((source) => (
              <article key={source.name} className="source-card">
                <strong>{source.name}</strong>
                <p>{source.type}</p>
              </article>
            ))}
          </div>
        </section>

        <section id="architecture" className="content-section section-contrast">
          <SectionHeader
            eyebrow="技术架构"
            title="MIMO / FastAPI / React / MCP / ToolUniverse / CrewAI，再往上叠一层 A2A Orchestrator"
            description="平台的关键升级不是单独再加几个工具，而是把这些底座统一放进 A2A 协作层，让功能入口、数据工具和社群流程成为一套体系。"
            align="center"
          />

          <div className="architecture-shell">
            <div className="architecture-orbit">
              <div className="orbit-core">
                <Icon name="nodes" />
                <strong>A2A Orchestrator</strong>
                <p>编排入口、Agent、数据库和最终交付</p>
              </div>
              <div className="orbit-tags">
                <span>患者入口</span>
                <span>研究入口</span>
                <span>试验入口</span>
                <span>社群入口</span>
              </div>
            </div>

            <div className="architecture-grid">
              {architectureBlocks.map((block) => (
                <article key={block.name} className="architecture-card">
                  <strong>{block.name}</strong>
                  <p>{block.desc}</p>
                </article>
              ))}
            </div>
          </div>
        </section>

        <section id="workbench" ref={workbenchRef} className="content-section">
          <SectionHeader
            eyebrow="平台工作台"
            title="现在就用同一个前端，接住 5 个核心能力"
            description="这里开始是实际可操作区域。你可以切换 A2A 模式，再选择具体能力。"
          />

          <div className="workbench-shell">
            <aside className="workbench-sidebar">
              <div className="sidebar-panel">
                <span className="sidebar-kicker">A2A 模式</span>
                <div className="sidebar-mode-list">
                  {a2aModes.map((mode) => (
                    <button
                      key={mode.id}
                      type="button"
                      className={`sidebar-mode ${a2aMode === mode.id ? 'active' : ''}`}
                      onClick={() => setA2AMode(mode.id)}
                    >
                      <strong>{mode.label}</strong>
                      <p>{mode.desc}</p>
                    </button>
                  ))}
                </div>
              </div>

              <div className="sidebar-panel">
                <span className="sidebar-kicker">功能入口</span>
                <div className="sidebar-cap-list">
                  {coreCapabilities.map((capability) => (
                    <button
                      key={capability.id}
                      type="button"
                      className={`sidebar-cap ${activeCapability === capability.id ? 'active' : ''}`}
                      onClick={() => setActiveCapability(capability.id)}
                    >
                      <strong>{capability.title}</strong>
                      <p>{capability.subtitle}</p>
                    </button>
                  ))}
                </div>
              </div>
            </aside>

            <div className="workbench-main">
              <div className="workbench-topbar">
                <div>
                  <span className="workbench-kicker">{activeMode.label}</span>
                  <h3>{activeCapabilityMeta.title}</h3>
                </div>
                <p>{activeCapabilityMeta.desc}</p>
              </div>

              {renderWorkspace()}
            </div>
          </div>
        </section>

        <section className="content-section section-contrast">
          <SectionHeader
            eyebrow="行动入口"
            title="介绍主页、平台应用、GitHub 仓库和 A2A 参考页都保留为一级入口"
            description="这保证对外展示、实际使用和后续开源协作是同一套叙事，而不是分散在多个不一致页面里。"
            align="center"
          />

          <div className="action-grid">
            <a className="action-card" href="/landing">
              <strong>介绍主页</strong>
              <p>{`${LIVE_PLATFORM_URL}/landing`}</p>
            </a>
            <a className="action-card" href={LIVE_PLATFORM_URL} target="_blank" rel="noreferrer">
              <strong>平台应用</strong>
              <p>{LIVE_PLATFORM_URL}</p>
            </a>
            <a className="action-card" href={GITHUB_URL} target="_blank" rel="noreferrer">
              <strong>GitHub 仓库</strong>
              <p>{GITHUB_URL}</p>
            </a>
            <a className="action-card" href={A2A_REFERENCE_URL} target="_blank" rel="noreferrer">
              <strong>A2A 参考页</strong>
              <p>{A2A_REFERENCE_URL}</p>
            </a>
          </div>
        </section>
      </main>

      <footer className="platform-footer">
        <p>MediChat-RD Rare Disease Platform</p>
        <p>AI 输出仅供研究与交流参考，不替代专业医疗诊断与治疗决策。</p>
      </footer>
    </div>
  );
}

export default App;
