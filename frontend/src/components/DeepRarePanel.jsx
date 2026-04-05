import React, { useState, useRef, useEffect } from 'react';

const API_BASE = import.meta.env.VITE_API_URL || '';

// ========== 图标 ==========
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
  book: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
      <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>
    </svg>
  ),
  send: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
      <line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/>
    </svg>
  ),
};

// ========== HPO表型标签 ==========
function PhenotypeTag({ hpo_id, name, confidence }) {
  const color = confidence >= 0.9 ? '#07C160' : confidence >= 0.7 ? '#FF9500' : '#999';
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: 6,
      padding: '4px 12px', borderRadius: 20, fontSize: 13,
      background: `${color}15`, color: color, border: `1px solid ${color}40`,
      marginRight: 8, marginBottom: 6,
    }}>
      <span style={{ fontWeight: 600 }}>{hpo_id}</span>
      <span>{name}</span>
      <span style={{ fontSize: 11, opacity: 0.8 }}>{Math.round(confidence * 100)}%</span>
    </span>
  );
}

// ========== 推理链步骤 ==========
function ReasoningStep({ step, isLast }) {
  const typeConfig = {
    observation: { emoji: '👁️', color: '#3B82F6', bg: '#EFF6FF' },
    hypothesis: { emoji: '💡', color: '#F59E0B', bg: '#FFFBEB' },
    evidence: { emoji: '📚', color: '#8B5CF6', bg: '#F5F3FF' },
    validation: { emoji: '✅', color: '#07C160', bg: '#F0FFF4' },
    conclusion: { emoji: '🎯', color: '#EF4444', bg: '#FEF2F2' },
    reflection: { emoji: '🔄', color: '#6366F1', bg: '#EEF2FF' },
  };
  const config = typeConfig[step.type] || typeConfig.observation;

  return (
    <div style={{
      display: 'flex', gap: 12, marginBottom: 2,
      position: 'relative',
    }}>
      {/* 连接线 */}
      {!isLast && (
        <div style={{
          position: 'absolute', left: 17, top: 36, bottom: -2,
          width: 2, background: '#E5E7EB',
        }} />
      )}
      {/* 节点 */}
      <div style={{
        width: 36, height: 36, borderRadius: '50%',
        background: config.bg, display: 'flex', alignItems: 'center',
        justifyContent: 'center', fontSize: 18, flexShrink: 0,
        border: `2px solid ${config.color}30`,
      }}>
        {config.emoji}
      </div>
      {/* 内容 */}
      <div style={{
        flex: 1, padding: '8px 14px', borderRadius: 12,
        background: config.bg, marginBottom: 8,
      }}>
        <div style={{ fontSize: 14, color: '#1a1a1a', lineHeight: 1.5 }}>
          {step.content}
        </div>
        {step.evidence && (
          <div style={{ fontSize: 12, color: '#666', marginTop: 4 }}>
            📎 {step.evidence}
          </div>
        )}
        {step.confidence && (
          <div style={{ fontSize: 12, color: config.color, marginTop: 2, fontWeight: 600 }}>
            📊 {step.confidence}
          </div>
        )}
      </div>
    </div>
  );
}

// ========== 诊断结果卡片 ==========
function DiagnosisCard({ diagnosis, rank }) {
  const isTop = rank === 1;
  return (
    <div style={{
      padding: '16px 20px', borderRadius: 16,
      background: isTop ? 'linear-gradient(135deg, #07C16010, #059B4810)' : '#fff',
      border: isTop ? '2px solid #07C160' : '1px solid #eee',
      marginBottom: 12,
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <span style={{
            width: 28, height: 28, borderRadius: '50%',
            background: isTop ? '#07C160' : '#E5E7EB',
            color: isTop ? '#fff' : '#666',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: 14, fontWeight: 700,
          }}>{rank}</span>
          <span style={{ fontSize: 16, fontWeight: 700, color: isTop ? '#059B48' : '#1a1a1a' }}>
            {diagnosis.disease}
          </span>
        </div>
        <span style={{
          padding: '4px 12px', borderRadius: 20, fontSize: 13, fontWeight: 600,
          background: isTop ? '#07C160' : '#F5F5F5',
          color: isTop ? '#fff' : '#666',
        }}>
          {diagnosis.confidence}
        </span>
      </div>
      <div style={{ fontSize: 13, color: '#666', marginTop: 8, paddingLeft: 38 }}>
        {diagnosis.reasoning}
      </div>
    </div>
  );
}

// ========== 主组件 ==========
export default function DeepRarePanel() {
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [showChain, setShowChain] = useState(false);
  const [age, setAge] = useState('');
  const [gender, setGender] = useState('');
  const textareaRef = useRef(null);

  const handleDiagnose = async () => {
    if (!input.trim() || loading) return;
    setLoading(true);
    setResult(null);

    try {
      const resp = await fetch(`${API_BASE}/api/v1/deeprare/diagnose`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: input,
          age: age ? parseInt(age) : null,
          gender: gender || null,
        }),
      });
      const data = await resp.json();
      setResult(data);
    } catch (err) {
      setResult({ error: '诊断请求失败: ' + err.message });
    }
    setLoading(false);
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleDiagnose();
    }
  };

  return (
    <div style={{
      maxWidth: 800, margin: '0 auto', padding: '20px 16px',
      fontFamily: '-apple-system, "PingFang SC", sans-serif',
    }}>
      {/* 标题区 */}
      <div style={{
        textAlign: 'center', marginBottom: 24,
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        borderRadius: 20, padding: '32px 24px', color: '#fff',
      }}>
        <div style={{ fontSize: 36, marginBottom: 8 }}>🧠</div>
        <h1 style={{ fontSize: 24, fontWeight: 800, margin: 0 }}>
          DeepRare 智能诊断
        </h1>
        <p style={{ fontSize: 14, opacity: 0.85, marginTop: 8 }}>
          Nature 2026 · Agentic AI · 可追溯推理 · HPO标准化
        </p>
        <div style={{
          display: 'flex', gap: 16, justifyContent: 'center', marginTop: 16,
          fontSize: 12, opacity: 0.8,
        }}>
          <span>🧬 HPO表型提取</span>
          <span>📚 多源知识检索</span>
          <span>🔄 自反思验证</span>
        </div>
      </div>

      {/* 输入区 */}
      <div style={{
        background: '#fff', borderRadius: 16, padding: 20,
        boxShadow: '0 2px 12px rgba(0,0,0,.06)', marginBottom: 20,
      }}>
        <div style={{ display: 'flex', gap: 12, marginBottom: 12 }}>
          <div style={{ flex: 1 }}>
            <label style={{ fontSize: 13, color: '#666', fontWeight: 600 }}>年龄</label>
            <input
              type="number" placeholder="可选" value={age}
              onChange={e => setAge(e.target.value)}
              style={{
                width: '100%', padding: '10px 14px', border: '2px solid #eee',
                borderRadius: 10, fontSize: 14, outline: 'none', marginTop: 4,
              }}
            />
          </div>
          <div style={{ flex: 1 }}>
            <label style={{ fontSize: 13, color: '#666', fontWeight: 600 }}>性别</label>
            <select value={gender} onChange={e => setGender(e.target.value)}
              style={{
                width: '100%', padding: '10px 14px', border: '2px solid #eee',
                borderRadius: 10, fontSize: 14, outline: 'none', marginTop: 4,
                background: '#fff',
              }}>
              <option value="">可选</option>
              <option value="male">男</option>
              <option value="female">女</option>
            </select>
          </div>
        </div>

        <label style={{ fontSize: 13, color: '#666', fontWeight: 600 }}>
          症状描述（自由文本）
        </label>
        <textarea
          ref={textareaRef}
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="请描述患者症状，例如：眼睑下垂，吞咽困难，全身无力，下午特别明显..."
          rows={3}
          style={{
            width: '100%', padding: '12px 14px', border: '2px solid #eee',
            borderRadius: 12, fontSize: 15, outline: 'none', marginTop: 4,
            resize: 'vertical', lineHeight: 1.6, fontFamily: 'inherit',
          }}
        />

        <button
          onClick={handleDiagnose}
          disabled={!input.trim() || loading}
          style={{
            width: '100%', marginTop: 12, padding: '14px 0',
            background: loading ? '#ccc' : 'linear-gradient(135deg, #667eea, #764ba2)',
            color: '#fff', border: 'none', borderRadius: 12,
            fontSize: 16, fontWeight: 700, cursor: loading ? 'not-allowed' : 'pointer',
            display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
          }}>
          {loading ? '🔄 分析中...' : '🧠 开始智能诊断'}
        </button>
      </div>

      {/* 结果区 */}
      {result && !result.error && (
        <>
          {/* 表型提取 */}
          {result.phenotypes && result.phenotypes.length > 0 && (
            <div style={{
              background: '#fff', borderRadius: 16, padding: 20,
              boxShadow: '0 2px 12px rgba(0,0,0,.06)', marginBottom: 20,
            }}>
              <h3 style={{ fontSize: 16, fontWeight: 700, marginBottom: 12, color: '#1a1a1a' }}>
                🧬 HPO表型提取 ({result.phenotypes.length}个)
              </h3>
              <div>
                {result.phenotypes.map((p, i) => (
                  <PhenotypeTag key={i} {...p} />
                ))}
              </div>
              {result.systems_involved && result.systems_involved.length > 0 && (
                <div style={{ fontSize: 13, color: '#666', marginTop: 10 }}>
                  涉及系统: {result.systems_involved.join('、')}
                </div>
              )}
            </div>
          )}

          {/* 鉴别诊断 */}
          {result.differential_diagnosis && result.differential_diagnosis.length > 0 && (
            <div style={{
              background: '#fff', borderRadius: 16, padding: 20,
              boxShadow: '0 2px 12px rgba(0,0,0,.06)', marginBottom: 20,
            }}>
              <h3 style={{ fontSize: 16, fontWeight: 700, marginBottom: 12, color: '#1a1a1a' }}>
                💡 鉴别诊断
              </h3>
              {result.differential_diagnosis.map((d, i) => (
                <DiagnosisCard key={i} diagnosis={d} rank={d.rank} />
              ))}
            </div>
          )}

          {/* 建议 */}
          {result.recommendations && result.recommendations.length > 0 && (
            <div style={{
              background: '#fff', borderRadius: 16, padding: 20,
              boxShadow: '0 2px 12px rgba(0,0,0,.06)', marginBottom: 20,
            }}>
              <h3 style={{ fontSize: 16, fontWeight: 700, marginBottom: 12, color: '#1a1a1a' }}>
                📌 建议
              </h3>
              {result.recommendations.map((r, i) => (
                <div key={i} style={{
                  padding: '10px 14px', background: '#F0FFF4', borderRadius: 10,
                  marginBottom: 8, fontSize: 14, color: '#059B48',
                }}>
                  {r}
                </div>
              ))}
            </div>
          )}

          {/* 可追溯推理链 */}
          <div style={{
            background: '#fff', borderRadius: 16, padding: 20,
            boxShadow: '0 2px 12px rgba(0,0,0,.06)', marginBottom: 20,
          }}>
            <div
              onClick={() => setShowChain(!showChain)}
              style={{
                display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                cursor: 'pointer',
              }}>
              <h3 style={{ fontSize: 16, fontWeight: 700, color: '#1a1a1a', margin: 0 }}>
                🔗 可追溯推理链
              </h3>
              <span style={{ fontSize: 13, color: '#667eea' }}>
                {showChain ? '收起 ▲' : '展开 ▼'}
              </span>
            </div>
            {showChain && (
              <div style={{ marginTop: 16 }}>
                {/* 解析推理链文本为步骤 */}
                {result.reasoning_chain && result.reasoning_chain.split('\n').filter(l => l.trim()).map((line, i) => (
                  <div key={i} style={{
                    padding: '6px 12px', fontSize: 13, color: '#444',
                    borderLeft: '3px solid #E5E7EB', marginBottom: 4, lineHeight: 1.6,
                    marginLeft: line.startsWith('   ') ? 20 : 0,
                  }}>
                    {line}
                  </div>
                ))}
              </div>
            )}
          </div>
        </>
      )}

      {/* 错误 */}
      {result?.error && (
        <div style={{
          background: '#FEF2F2', borderRadius: 16, padding: 20,
          border: '1px solid #FECACA', textAlign: 'center',
        }}>
          <div style={{ fontSize: 18, marginBottom: 8 }}>❌</div>
          <div style={{ color: '#DC2626', fontSize: 14 }}>{result.error}</div>
        </div>
      )}

      {/* 底部信息 */}
      <div style={{
        textAlign: 'center', padding: '20px 0', fontSize: 12, color: '#999',
      }}>
        基于 Nature 2026 DeepRare 论文架构 · 可追溯推理 · 自反思验证
        <br/>
        ⚠️ 仅供辅助参考，不能替代专业医生诊断
      </div>
    </div>
  );
}
