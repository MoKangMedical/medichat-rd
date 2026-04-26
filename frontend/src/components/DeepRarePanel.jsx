import React, { useState } from 'react';

const API_BASE = import.meta.env.VITE_API_URL || '';

const QUICK_CASES = [
  {
    label: '神经肌肉',
    text: '反复肌无力，下午明显加重，最近出现眼睑下垂和吞咽困难，休息后稍微好转。',
    age: '28',
    gender: 'female',
  },
  {
    label: '溶酶体病',
    text: '孩子反复出现脾大、骨痛和贫血，活动耐力差，最近还有生长发育偏慢的情况。',
    age: '12',
    gender: 'male',
  },
  {
    label: '骨骼系统',
    text: '从小容易骨折，巩膜发蓝，近期关节疼痛明显，家里有人也有类似骨骼问题。',
    age: '17',
    gender: 'female',
  },
];

const ANONYMIZED_CASES = [
  {
    label: '匿名案例 A',
    title: '复发性早孕期胎儿水肿',
    phenotype: 'NT 增厚 / 胎儿水肿 / 颈部水囊瘤样改变',
    privacy: '已去除样本号、机构、日期、精确孕周和家系可识别信息',
    question: '多次早孕期出现相似异常，常规遗传检测未解释，核心问题是偶发胎停还是存在可验证的遗传或母胎机制。',
    evidence: [
      '常规 CMA、外显子和相关筛查未给出直接解释。',
      'Trio-WGS 未直接支持胎儿单基因病作为主因。',
      'WGS 阴性不能排除抗体介导的母胎免疫机制。',
    ],
    turn: '诊断路径从“继续寻找胎儿单基因病”转向“母胎免疫机制专项验证”。',
    next: [
      '母体血小板/单核细胞 CD36 表达检测。',
      '抗 CD36 抗体专项检测。',
      '父亲与胎儿 CD36 抗原状态验证。',
      '复核胎儿血小板、贫血、溶血和水肿证据。',
    ],
    preset: {
      text: '早孕期反复出现胎儿 NT 增厚、胎儿水肿和颈部水囊瘤样改变，常规染色体微阵列、外显子检测和相关筛查未能解释。请帮助梳理可能的遗传机制、母胎免疫机制和下一步验证路径。',
      age: '',
      gender: 'female',
    },
  },
  {
    label: '匿名案例 B',
    title: '进行性肌无力伴内分泌线索',
    phenotype: '肌无力 / 肌萎缩 / 男性乳房发育 / 轴索性周围神经病',
    privacy: '已去除样本号、年龄段细节、医院、检查日期和原始报告编号',
    question: '临床表型高度接近 Kennedy 病，但关键重复序列检测处于正常范围，需要重新定位诊断方向。',
    evidence: [
      '经典 Kennedy 病暂不支持，不能把临床相似等同于确诊。',
      '需保留其他重复扩增、拷贝数变异和神经肌肉 mimic 的可能性。',
      '基因阴性不是终点，可治疗疾病必须同步排查。',
    ],
    turn: '诊断路径从“单病种确认”转向“AR-CAG 阴性 SBMA-like 综合征和可治疗 mimic 并行排查”。',
    next: [
      '独立方法复核关键重复序列检测结果。',
      '完整 EMG/NCS 复核，确认病变层级。',
      '专项验证 PMP22、ATXN2、C9orf72、RFC1 等线索。',
      '同步排查 CIDP/MMN、POEMS、ATTR/AL、IBM 等可治疗或可干预方向。',
    ],
    preset: {
      text: '成年男性出现进行性肌无力、肌萎缩、男性乳房发育和激素异常，肌电图提示轴索性运动感觉周围神经病。临床表现类似 Kennedy 病，但关键重复序列检测在正常范围。请帮助重定位诊断并列出下一步验证路径。',
      age: '',
      gender: 'male',
    },
  },
  {
    label: '匿名案例 C',
    title: '神经发育异常伴癫痫',
    phenotype: '发育迟缓 / 智力发育受累 / 癫痫 / 肢体发育异常',
    privacy: '已去除原病例编号、队伍成员信息、精确位点坐标、转录本号、检查日期和机构地点',
    question: '多系统神经发育表型与测序结果之间存在候选变异，核心问题是如何把 VUS 级线索升级成可复核的诊断证据。',
    evidence: [
      '三联体分析提示某神经发育相关候选为新发错义变异，但公开展示不暴露具体坐标。',
      '表型、遗传模式、低频证据和计算预测共同支持优先级上调。',
      '另一个复合杂合候选仍需保留，但因人群频率和证据强度限制，不应过早确诊。',
    ],
    turn: '诊断路径从“候选变异列表”转向“ACMG 证据矩阵 + 表型匹配 + 家系来源”的可追溯升级判断。',
    next: [
      '复核新发来源和亲子关系质量控制。',
      '补充表型-疾病谱匹配证据，形成可审计的证据表。',
      '对次级候选做分离验证和功能域证据复核。',
      '输出 LP/VUS 边界判断，供临床遗传团队复核。',
    ],
    preset: {
      text: '儿童存在发育迟缓、智力发育受累、癫痫发作和肢体发育异常，三联体测序提示一个神经发育相关新发错义候选，同时还有一个证据不足的复合杂合候选。请帮助用 ACMG 证据、表型匹配和家系来源梳理诊断优先级。',
      age: '',
      gender: '',
    },
  },
  {
    label: '匿名案例 D',
    title: '面肩肱肌营养不良谱系疑案',
    phenotype: '面肩肱肌无力 / 翼状肩胛 / 足下垂 / 表观遗传线索',
    privacy: '已去除原病例编号、精确重复次数、单倍型细节、样本图像和家系可识别信息',
    question: '临床表现像 FSHD，但常规 1 型解释不足，核心问题是如何通过表观遗传机制重新定位。',
    evidence: [
      '重复区域结果不支持典型 1 型机制，不能只按单一路径结束分析。',
      '甲基化降低为 2 型或表观遗传相关机制提供方向。',
      '病程、体征和分子证据需要放在同一张时间轴和机制分流图中解释。',
    ],
    turn: '诊断路径从“是否为 FSHD1”转向“FSHD 谱系机制分型和表观遗传验证”。',
    next: [
      '复核相关重复区域、单倍型和甲基化检测质量。',
      '补充 FSHD2 相关基因和表观遗传调控线索。',
      '用病程时间轴标注肌力、步态、肩胛和呼吸功能变化。',
      '生成遗传咨询、康复评估和随访监测清单。',
    ],
    preset: {
      text: '患者存在面肩肱肌无力、翼状肩胛和足下垂，临床表现符合面肩肱肌营养不良谱系，但常规 1 型机制证据不足，甲基化结果提示可能存在表观遗传机制。请帮助建立机制分流和下一步验证路径。',
      age: '',
      gender: '',
    },
  },
];

const VISUALIZATION_MODES = [
  {
    title: 'VCF + HPO 多 Agent 工作流',
    summary: '把患者叙述、VCF/候选变异和 HPO 表型放进同一条流水线，明确每个 Agent 负责的证据层。',
    chips: ['输入层', 'HPO 标准化', '变异分诊', 'ACMG 证据', '报告输出'],
    output: '适合展示“从原始数据到可复核结论”的全过程。',
  },
  {
    title: 'ACMG 证据矩阵',
    summary: '把新发来源、功能域、人群频率、计算预测、表型特异性和文献证据拆成可审计格子。',
    chips: ['PS/PM/PP', '证据强度', '冲突证据', '升级边界', '审计备注'],
    output: '适合展示 VUS 到 LP 边界判断，避免黑箱式结论。',
  },
  {
    title: '患者病程时间轴',
    summary: '用年龄段而非精确日期展示症状、检查、治疗反应和关键诊断转向，保护身份同时保留临床逻辑。',
    chips: ['早期表现', '关键检查', '诊断转向', '验证动作', '随访节点'],
    output: '适合患者、医生和团队快速对齐“发生了什么”。',
  },
  {
    title: '机制分流图',
    summary: '把相似表型按不同机制拆开，例如单基因、重复扩增、甲基化、免疫、可治疗 mimic。',
    chips: ['分型入口', '排除依据', '支持证据', '下一验证', '临床动作'],
    output: '适合展示“为什么不是 A，而要转向 B/C”。',
  },
];

function PhenotypeTag({ hpo_id, name, confidence }) {
  const level = confidence >= 0.85 ? 'strong' : confidence >= 0.65 ? 'medium' : 'soft';
  return (
    <span className={`deeprare-phenotype ${level}`}>
      <strong>{hpo_id}</strong>
      <span>{name}</span>
      <small>{Math.round(confidence * 100)}%</small>
    </span>
  );
}

function DiagnosisCard({ diagnosis }) {
  return (
    <div className={`deeprare-diagnosis-card ${diagnosis.rank === 1 ? 'top' : ''}`}>
      <div className="deeprare-diagnosis-head">
        <div className="deeprare-diagnosis-rank">0{diagnosis.rank}</div>
        <div>
          <h3>{diagnosis.disease}</h3>
          <p>{diagnosis.reasoning}</p>
        </div>
      </div>
      <div className="deeprare-diagnosis-score">{diagnosis.confidence}</div>
    </div>
  );
}

export default function DeepRarePanel() {
  const [input, setInput] = useState('');
  const [age, setAge] = useState('');
  const [gender, setGender] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [showChain, setShowChain] = useState(false);

  const reasoningLines = result?.reasoning_chain
    ? result.reasoning_chain.split('\n').map((line) => line.trim()).filter(Boolean)
    : [];

  const handleDiagnose = async () => {
    if (!input.trim() || loading) return;
    setLoading(true);
    setResult(null);

    try {
      const response = await fetch(`${API_BASE}/api/v1/deeprare/diagnose`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: input,
          age: age ? parseInt(age, 10) : null,
          gender: gender || null,
        }),
      });
      const data = await response.json();
      setResult(data);
    } catch (error) {
      setResult({ error: `诊断请求失败: ${error.message}` });
    } finally {
      setLoading(false);
    }
  };

  const handlePromptFill = (preset) => {
    setInput(preset.text);
    setAge(preset.age);
    setGender(preset.gender);
  };

  return (
    <div className="utility-page deeprare-page">
      <div className="utility-shell deeprare-shell">
        <section className="deeprare-hero">
          <div className="deeprare-hero-copy">
            <div className="page-eyebrow">DeepRare intelligence desk</div>
            <h2>DeepRare 智能诊断</h2>
            <p>
              把自由文本症状、HPO 表型、差异诊断、下一步检查和可追溯推理链放在同一张工作台里。
            </p>
            <div className="deeprare-hero-actions">
              <button type="button" className="primary-btn" onClick={handleDiagnose} disabled={loading || !input.trim()}>
                <span>{loading ? '正在分析' : '开始 DeepRare 诊断'}</span>
              </button>
              <button type="button" className="ghost-btn" onClick={() => handlePromptFill(QUICK_CASES[0])}>
                <span>加载示例病例</span>
              </button>
            </div>
          </div>

          <div className="deeprare-hero-panel">
            <div className="deeprare-kicker">三层推理</div>
            <div className="deeprare-panel-title">表型标准化 → 差异诊断 → 解释与下一步</div>
            <div className="deeprare-panel-metrics">
              <div>
                <small>可追溯链路</small>
                <strong>HPO + 研究证据</strong>
              </div>
              <div>
                <small>输出重点</small>
                <strong>诊断排序与动作建议</strong>
              </div>
              <div>
                <small>适合场景</small>
                <strong>初筛、复盘、就诊前准备</strong>
              </div>
            </div>
          </div>
        </section>

        <section className="result-panel deeprare-case-showcase">
          <div className="section-head">
            <span>匿名实战案例展示</span>
            <span className="section-note">来自 48 小时基因组侦探案例复盘，已做公开展示脱敏</span>
          </div>
          <div className="deeprare-case-grid">
            {ANONYMIZED_CASES.map((item) => (
              <article key={item.label} className="deeprare-case-card">
                <div className="deeprare-case-top">
                  <span>{item.label}</span>
                  <small>身份脱敏</small>
                </div>
                <h3>{item.title}</h3>
                <p className="deeprare-case-phenotype">{item.phenotype}</p>
                <div className="deeprare-case-privacy">{item.privacy}</div>
                <div className="deeprare-case-block">
                  <strong>核心矛盾</strong>
                  <p>{item.question}</p>
                </div>
                <div className="deeprare-case-block">
                  <strong>证据链</strong>
                  <ul>
                    {item.evidence.map((line) => (
                      <li key={line}>{line}</li>
                    ))}
                  </ul>
                </div>
                <div className="deeprare-case-block">
                  <strong>诊断转向</strong>
                  <p>{item.turn}</p>
                </div>
                <div className="deeprare-case-block">
                  <strong>下一步动作</strong>
                  <ul>
                    {item.next.map((line) => (
                      <li key={line}>{line}</li>
                    ))}
                  </ul>
                </div>
                <button type="button" className="ghost-btn" onClick={() => handlePromptFill(item.preset)}>
                  <span>加载到工作台</span>
                </button>
              </article>
            ))}
          </div>
          <p className="deeprare-case-disclaimer">
            展示内容仅用于说明 RareDBridge / RareProfiler 的推理路径，不包含原始病例编号、个人身份、机构、日期或可回溯原始报告的信息，不能替代临床诊断。
          </p>
        </section>

        <section className="result-panel deeprare-visual-showcase">
          <div className="section-head">
            <span>脱敏可视化呈现模式</span>
            <span className="section-note">参考 RareProfiler 的汇报结构，转成平台可复用组件</span>
          </div>
          <div className="deeprare-visual-board">
            {VISUALIZATION_MODES.map((mode, index) => (
              <article key={mode.title} className="deeprare-visual-card">
                <div className="deeprare-visual-index">{String(index + 1).padStart(2, '0')}</div>
                <div>
                  <h3>{mode.title}</h3>
                  <p>{mode.summary}</p>
                  <div className="deeprare-visual-chip-row">
                    {mode.chips.map((chip) => (
                      <span key={chip}>{chip}</span>
                    ))}
                  </div>
                  <div className="deeprare-visual-output">{mode.output}</div>
                </div>
              </article>
            ))}
          </div>
          <div className="deeprare-visual-flow" aria-label="脱敏展示流程">
            {['病例脱敏', '表型抽象', '证据矩阵', '机制分流', '下一步动作'].map((step, index) => (
              <div key={step} className="deeprare-visual-flow-step">
                <span>{String(index + 1).padStart(2, '0')}</span>
                <strong>{step}</strong>
              </div>
            ))}
          </div>
        </section>

        <section className="deeprare-workbench">
          <div className="deeprare-input-panel">
            <div className="section-head">
              <span>诊断输入</span>
              <span className="section-note">支持患者自由文本，不需要先写成医学术语</span>
            </div>
            <div className="field-grid two">
              <label className="field">
                <span>年龄</span>
                <input
                  type="number"
                  placeholder="可选"
                  value={age}
                  onChange={(event) => setAge(event.target.value)}
                />
              </label>
              <label className="field">
                <span>性别</span>
                <select value={gender} onChange={(event) => setGender(event.target.value)}>
                  <option value="">可选</option>
                  <option value="male">男</option>
                  <option value="female">女</option>
                </select>
              </label>
            </div>
            <label className="field">
              <span>症状描述</span>
              <textarea
                rows={6}
                value={input}
                onChange={(event) => setInput(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === 'Enter' && !event.shiftKey) {
                    event.preventDefault();
                    handleDiagnose();
                  }
                }}
                placeholder="例如：反复肌无力、下午加重、吞咽困难，最近还出现眼睑下垂。"
              />
            </label>
            <button type="button" className="primary-btn deeprare-submit" onClick={handleDiagnose} disabled={loading || !input.trim()}>
              <span>{loading ? 'DeepRare 正在解析' : '开始智能诊断'}</span>
            </button>
          </div>

          <div className="deeprare-side-panel">
            <div className="section-head">
              <span>常见病例模板</span>
              <span className="section-note">一键代入，先看效果</span>
            </div>
            <div className="deeprare-prompt-grid">
              {QUICK_CASES.map((preset) => (
                <button key={preset.label} type="button" className="deeprare-prompt-card" onClick={() => handlePromptFill(preset)}>
                  <div className="deeprare-prompt-top">
                    <strong>{preset.label}</strong>
                    <span>{preset.gender === 'male' ? '男' : '女'} · {preset.age} 岁</span>
                  </div>
                  <p>{preset.text}</p>
                </button>
              ))}
            </div>
          </div>
        </section>

        {loading && (
          <section className="result-panel accent">
            <div className="section-head">
              <span>DeepRare 正在推理</span>
              <span className="section-note">HPO 表型提取、候选排序和证据整理中</span>
            </div>
            <div className="bullet-list">
              {[
                '把自由文本症状转换成标准化 HPO 表型',
                '结合知识库与差异诊断线索做首轮排序',
                '生成下一步检查和就诊建议',
              ].map((item) => (
                <div key={item} className="bullet-row">
                  <span className="reason-mark" />
                  <span>{item}</span>
                </div>
              ))}
            </div>
          </section>
        )}

        {result?.error && <div className="inline-error">{result.error}</div>}

        {result && !result.error && (
          <div className="result-stack deeprare-results">
            <section className="result-panel accent deeprare-summary-panel">
              <div className="section-head">
                <span>诊断摘要</span>
                <span className="section-note">{result.systems_involved?.join(' / ') || '单系统表现'}</span>
              </div>
              <p className="summary-text">{result.summary}</p>
              <div className="signal-grid">
                <div className="signal-cell">
                  <small>候选诊断</small>
                  <strong>{result.differential_diagnosis?.length || 0}</strong>
                </div>
                <div className="signal-cell">
                  <small>HPO 表型</small>
                  <strong>{result.phenotypes?.length || 0}</strong>
                </div>
                <div className="signal-cell">
                  <small>推荐动作</small>
                  <strong>{result.recommendations?.length || 0}</strong>
                </div>
                <div className="signal-cell">
                  <small>推理链</small>
                  <strong>{reasoningLines.length}</strong>
                </div>
              </div>
            </section>

            {result.phenotypes?.length > 0 && (
              <section className="result-panel">
                <div className="section-head">
                  <span>HPO 表型提取</span>
                  <span className="section-note">把患者表达转换成结构化表型</span>
                </div>
                <div className="tag-row">
                  {result.phenotypes.map((item) => (
                    <PhenotypeTag key={`${item.hpo_id}-${item.name}`} {...item} />
                  ))}
                </div>
              </section>
            )}

            {result.differential_diagnosis?.length > 0 && (
              <section className="result-panel">
                <div className="section-head">
                  <span>鉴别诊断排序</span>
                  <span className="section-note">不是最终诊断，而是值得优先排查的方向</span>
                </div>
                <div className="deeprare-diagnosis-list">
                  {result.differential_diagnosis.map((diagnosis) => (
                    <DiagnosisCard key={`${diagnosis.rank}-${diagnosis.disease}`} diagnosis={diagnosis} />
                  ))}
                </div>
              </section>
            )}

            {result.recommendations?.length > 0 && (
              <section className="result-panel">
                <div className="section-head">
                  <span>下一步动作</span>
                  <span className="section-note">最适合带着去问医生或病友的部分</span>
                </div>
                <div className="deeprare-action-grid">
                  {result.recommendations.map((item) => (
                    <div key={item} className="deeprare-action-card">
                      <span className="reason-mark" />
                      <p>{item}</p>
                    </div>
                  ))}
                </div>
                {result.reasoning_preview && (
                  <div className="preview-box">
                    <span className="preview-title">推理预览</span>
                    <pre>{result.reasoning_preview}</pre>
                  </div>
                )}
              </section>
            )}

            {result.workflow_phase_status?.length > 0 && (
              <section className="result-panel">
                <div className="section-head">
                  <span>论文五阶段工作流</span>
                  <span className="section-note">保留原工作台结构，仅补充 DeepRare 方法状态</span>
                </div>
                <div className="deeprare-action-grid">
                  {result.workflow_phase_status.map((item) => (
                    <div key={item.phase} className="deeprare-action-card">
                      <span className="reason-mark" />
                      <p><strong>{item.phase}</strong> · {item.status}</p>
                      <p>{item.detail}</p>
                    </div>
                  ))}
                </div>
              </section>
            )}

            {result.github_module_mapping?.length > 0 && (
              <section className="result-panel">
                <div className="section-head">
                  <span>DeepRare GitHub 开源模块映射</span>
                  <span className="section-note">参考 MAGIC-AI4Med/DeepRare，不复制其源码</span>
                </div>
                <div className="deeprare-action-grid">
                  {result.github_module_mapping.map((item) => (
                    <div key={item.module} className="deeprare-action-card">
                      <span className="reason-mark" />
                      <p><strong>{item.module}</strong></p>
                      <p>{item.capability}</p>
                      <p>{item.medichat_mapping}</p>
                    </div>
                  ))}
                </div>
              </section>
            )}

            {reasoningLines.length > 0 && (
              <section className="result-panel">
                <div className="section-head">
                  <span>可追溯推理链</span>
                  <button type="button" onClick={() => setShowChain((value) => !value)}>
                    {showChain ? '收起' : '展开'}
                  </button>
                </div>
                {showChain && (
                  <div className="deeprare-chain">
                    {reasoningLines.map((line, index) => (
                      <div key={`${index}-${line}`} className="deeprare-chain-row">
                        <div className="deeprare-chain-index">{index + 1}</div>
                        <p>{line}</p>
                      </div>
                    ))}
                  </div>
                )}
              </section>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
