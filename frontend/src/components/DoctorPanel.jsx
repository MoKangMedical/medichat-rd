import React, { useState, useRef, useEffect } from 'react';

// ═══════════════════════════════════════════════════
// 医生AI助手面板 — Jarvis模式
// ═══════════════════════════════════════════════════

function DoctorPanel() {
  const [session, setSession] = useState(null);
  const [transcript, setTranscript] = useState([]);
  const [inputText, setInputText] = useState('');
  const [speaker, setSpeaker] = useState('patient');
  const [supportResult, setSupportResult] = useState(null);
  const [note, setNote] = useState('');
  const [loading, setLoading] = useState(false);
  const [chiefComplaint, setChiefComplaint] = useState('');
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(scrollToBottom, [transcript]);

  // 开始诊疗
  const startConsultation = async () => {
    if (!chiefComplaint.trim()) return;
    setLoading(true);
    try {
      const res = await fetch('/api/doctor/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          patient_id: 'p_' + Date.now(),
          doctor_id: 'd_001',
          chief_complaint: chiefComplaint,
        }),
      });
      const data = await res.json();
      if (data.ok) {
        setSession(data.data);
        setTranscript([{
          role: 'system',
          text: `📋 诊疗会话已开始\n会话ID: ${data.data.session_id}\n\n💡 AI建议:\n鉴别诊断: ${data.data.ai_suggestions?.differential?.join('、') || '—'}\n建议检查: ${data.data.ai_suggestions?.tests?.join('、') || '—'}\n推荐专科: ${data.data.ai_suggestions?.specialty || '—'}`,
          time: new Date().toLocaleTimeString(),
        }]);
        setSupportResult(data.data);
      }
    } catch (err) {
      console.error(err);
    }
    setLoading(false);
  };

  // 添加转写记录
  const addTranscript = async () => {
    if (!inputText.trim() || !session) return;
    setLoading(true);
    try {
      const res = await fetch('/api/doctor/transcript', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: session.session_id,
          speaker: speaker,
          text: inputText,
        }),
      });
      const data = await res.json();
      if (data.ok) {
        const entry = data.data.entry;
        setTranscript(prev => [...prev, {
          role: entry.speaker,
          text: entry.text,
          time: entry.timestamp,
        }]);
        
        // AI实时警报
        if (data.data.ai_alert) {
          const analysis = data.data.analysis;
          const suggestion = data.data.suggestion;
          let alertText = '🚨 AI实时警报\n';
          if (analysis?.phenotype_count > 0) {
            alertText += `检测到 ${analysis.phenotype_count} 个HPO表型\n`;
          }
          if (suggestion?.differential?.length > 0) {
            alertText += `鉴别诊断: ${suggestion.differential.join('、')}\n`;
          }
          if (suggestion?.tests?.length > 0) {
            alertText += `建议检查: ${suggestion.tests.join('、')}\n`;
          }
          setTranscript(prev => [...prev, {
            role: 'ai_alert',
            text: alertText,
            time: new Date().toLocaleTimeString(),
          }]);
        }
      }
    } catch (err) {
      console.error(err);
    }
    setInputText('');
    setLoading(false);
  };

  // 获取诊断支持
  const getSupport = async () => {
    if (!inputText.trim()) return;
    setLoading(true);
    try {
      const res = await fetch('/api/doctor/support', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: inputText }),
      });
      const data = await res.json();
      if (data.ok) {
        setSupportResult(data.data);
      }
    } catch (err) {
      console.error(err);
    }
    setLoading(false);
  };

  // 生成病历
  const generateNote = async () => {
    if (!session) return;
    setLoading(true);
    try {
      const res = await fetch(`/api/doctor/note/${session.session_id}`);
      const data = await res.json();
      if (data.ok) {
        setNote(data.data.note);
      }
    } catch (err) {
      console.error(err);
    }
    setLoading(false);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* Header */}
      <div style={{
        background: 'linear-gradient(135deg, #1B3A5C 0%, #3498DB 100%)',
        padding: '20px',
        borderRadius: '12px 12px 0 0',
        color: 'white',
      }}>
        <h2 style={{ margin: 0, fontSize: '20px' }}>🤖 医生AI助手 — Jarvis模式</h2>
        <p style={{ margin: '5px 0 0', opacity: 0.8, fontSize: '13px' }}>
          参考HealthBridge AI JarvisMD · 实时语音转写 · AI诊断建议 · 病历生成
        </p>
      </div>

      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        {/* 左侧：诊疗面板 */}
        <div style={{ flex: 2, display: 'flex', flexDirection: 'column', borderRight: '1px solid #eee' }}>
          {/* 开始会话 */}
          {!session && (
            <div style={{ padding: '20px' }}>
              <h3>开始新诊疗</h3>
              <textarea
                value={chiefComplaint}
                onChange={e => setChiefComplaint(e.target.value)}
                placeholder="输入主诉，例如：&#10;患者眼睑下垂、吞咽困难3个月&#10;CK 850 U/L，ALT 45 U/L"
                rows={4}
                style={{ width: '100%', padding: '10px', borderRadius: '8px', border: '1px solid #ddd', fontSize: '14px' }}
              />
              <button
                onClick={startConsultation}
                disabled={loading || !chiefComplaint.trim()}
                style={{
                  marginTop: '10px', padding: '10px 24px', background: '#1B3A5C', color: 'white',
                  border: 'none', borderRadius: '8px', cursor: 'pointer', fontSize: '14px',
                }}
              >
                {loading ? '分析中...' : '开始诊疗'}
              </button>
            </div>
          )}

          {/* 转写记录 */}
          {session && (
            <>
              <div style={{ flex: 1, overflow: 'auto', padding: '15px' }}>
                {transcript.map((entry, i) => (
                  <div key={i} style={{
                    marginBottom: '12px',
                    padding: '10px 14px',
                    borderRadius: '8px',
                    background: entry.role === 'patient' ? '#E3F2FD' :
                               entry.role === 'doctor' ? '#E8F5E9' :
                               entry.role === 'ai_alert' ? '#FFF3E0' : '#F5F5F5',
                    borderLeft: entry.role === 'ai_alert' ? '4px solid #FF9800' :
                               entry.role === 'system' ? '4px solid #1B3A5C' : 'none',
                  }}>
                    <div style={{ fontSize: '11px', color: '#888', marginBottom: '4px' }}>
                      {entry.role === 'patient' ? '👤 患者' :
                       entry.role === 'doctor' ? '🩺 医生' :
                       entry.role === 'ai_alert' ? '🚨 AI警报' : '📋 系统'}
                      {' · '}{entry.time}
                    </div>
                    <div style={{ fontSize: '13px', whiteSpace: 'pre-line' }}>{entry.text}</div>
                  </div>
                ))}
                <div ref={messagesEndRef} />
              </div>

              {/* 输入区 */}
              <div style={{ padding: '10px 15px', borderTop: '1px solid #eee' }}>
                <div style={{ display: 'flex', gap: '8px', marginBottom: '8px' }}>
                  <select value={speaker} onChange={e => setSpeaker(e.target.value)}
                    style={{ padding: '6px 10px', borderRadius: '6px', border: '1px solid #ddd' }}>
                    <option value="patient">👤 患者</option>
                    <option value="doctor">🩺 医生</option>
                  </select>
                </div>
                <div style={{ display: 'flex', gap: '8px' }}>
                  <input
                    value={inputText}
                    onChange={e => setInputText(e.target.value)}
                    onKeyDown={e => e.key === 'Enter' && addTranscript()}
                    placeholder="输入会话内容..."
                    style={{ flex: 1, padding: '10px', borderRadius: '8px', border: '1px solid #ddd' }}
                  />
                  <button onClick={addTranscript} disabled={loading}
                    style={{ padding: '10px 16px', background: '#1B3A5C', color: 'white', border: 'none', borderRadius: '8px', cursor: 'pointer' }}>
                    记录
                  </button>
                  <button onClick={getSupport} disabled={loading}
                    style={{ padding: '10px 16px', background: '#3498DB', color: 'white', border: 'none', borderRadius: '8px', cursor: 'pointer' }}>
                    AI诊断
                  </button>
                  <button onClick={generateNote} disabled={loading}
                    style={{ padding: '10px 16px', background: '#27AE60', color: 'white', border: 'none', borderRadius: '8px', cursor: 'pointer' }}>
                    生成病历
                  </button>
                </div>
              </div>
            </>
          )}
        </div>

        {/* 右侧：AI分析面板 */}
        <div style={{ flex: 1, overflow: 'auto', padding: '15px', background: '#FAFAFA' }}>
          <h3 style={{ marginTop: 0, fontSize: '15px', color: '#1B3A5C' }}>📊 AI分析</h3>

          {supportResult?.ai_suggestions && (
            <div style={{ marginBottom: '15px' }}>
              <h4 style={{ fontSize: '13px', color: '#666' }}>💡 鉴别诊断</h4>
              {supportResult.ai_suggestions.differential?.map((d, i) => (
                <div key={i} style={{
                  padding: '6px 10px', marginBottom: '4px', borderRadius: '6px',
                  background: i === 0 ? '#E3F2FD' : '#F5F5F5', fontSize: '13px',
                }}>
                  {i === 0 ? '🥇' : i === 1 ? '🥈' : '🥉'} {d}
                </div>
              ))}
            </div>
          )}

          {supportResult?.ai_suggestions?.tests && (
            <div style={{ marginBottom: '15px' }}>
              <h4 style={{ fontSize: '13px', color: '#666' }}>🔬 建议检查</h4>
              {supportResult.ai_suggestions.tests.map((t, i) => (
                <div key={i} style={{
                  padding: '4px 8px', marginBottom: '3px', borderRadius: '4px',
                  background: '#FFF8E1', fontSize: '12px',
                }}>
                  ▸ {t}
                </div>
              ))}
            </div>
          )}

          {supportResult?.ai_suggestions?.specialty && (
            <div style={{ marginBottom: '15px' }}>
              <h4 style={{ fontSize: '13px', color: '#666' }}>🏥 推荐专科</h4>
              <div style={{ padding: '8px 12px', background: '#E8F5E9', borderRadius: '6px', fontSize: '13px' }}>
                {supportResult.ai_suggestions.specialty}
              </div>
            </div>
          )}

          {supportResult?.orchestrator?.stages?.analysis?.differential_diagnosis && (
            <div style={{ marginBottom: '15px' }}>
              <h4 style={{ fontSize: '13px', color: '#666' }}>🛡️ 幻觉防护验证</h4>
              {supportResult.orchestrator.stages.analysis.differential_diagnosis.slice(0, 3).map((d, i) => (
                <div key={i} style={{
                  padding: '6px 10px', marginBottom: '4px', borderRadius: '6px',
                  background: d.score >= 70 ? '#E8F5E9' : d.score >= 40 ? '#FFF3E0' : '#FFEBEE',
                  fontSize: '12px',
                }}>
                  {d.disease}: {d.score}%
                  {d.layer_results?.map((e, j) => <div key={j} style={{ marginLeft: '12px', fontSize: '11px', color: '#666' }}>{e}</div>)}
                </div>
              ))}
            </div>
          )}

          {supportResult?.orchestrator?.stages?.clinical_trials?.matched_trials?.length > 0 && (
            <div style={{ marginBottom: '15px' }}>
              <h4 style={{ fontSize: '13px', color: '#666' }}>🧪 临床试验</h4>
              {supportResult.orchestrator.stages.clinical_trials.matched_trials.slice(0, 3).map((t, i) => (
                <div key={i} style={{ padding: '4px 8px', marginBottom: '3px', borderRadius: '4px', background: '#F3E5F5', fontSize: '11px' }}>
                  {t.nct_id}: {t.title}<br/>
                  <span style={{ color: '#888' }}>阶段: {t.phase} | 状态: {t.status}</span>
                </div>
              ))}
            </div>
          )}

          {supportResult?.orchestrator?.stages?.specialists?.matched_specialists?.length > 0 && (
            <div style={{ marginBottom: '15px' }}>
              <h4 style={{ fontSize: '13px', color: '#666' }}>🏥 专科推荐</h4>
              {supportResult.orchestrator.stages.specialists.matched_specialists.slice(0, 3).map((s, i) => (
                <div key={i} style={{ padding: '4px 8px', marginBottom: '3px', borderRadius: '4px', background: '#E0F2F1', fontSize: '12px' }}>
                  {s.name} - {s.department}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* 病历弹窗 */}
      {note && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
          background: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000,
        }} onClick={() => setNote('')}>
          <div style={{
            background: 'white', borderRadius: '12px', padding: '24px', maxWidth: '700px',
            width: '90%', maxHeight: '80vh', overflow: 'auto',
          }} onClick={e => e.stopPropagation()}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '15px' }}>
              <h3 style={{ margin: 0 }}>📝 门诊病历</h3>
              <button onClick={() => setNote('')} style={{ background: 'none', border: 'none', fontSize: '20px', cursor: 'pointer' }}>×</button>
            </div>
            <pre style={{ whiteSpace: 'pre-wrap', fontSize: '13px', lineHeight: '1.8', fontFamily: 'inherit' }}>{note}</pre>
          </div>
        </div>
      )}
    </div>
  );
}

export default DoctorPanel;
