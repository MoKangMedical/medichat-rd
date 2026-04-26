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
