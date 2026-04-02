import React, { useState, useRef, useEffect } from 'react';
import './App.css';

// 医生头像组件
const DoctorAvatar = ({ doctor }) => {
  const avatarColors = {
    '陈雅琴': '#FF6B6B',
    '王建国': '#4ECDC4',
    '李明辉': '#45B7D1',
    '赵晓燕': '#96CEB4',
    '林雨桐': '#FFEAA7',
    '刘志强': '#DDA0DD'
  };

  return (
    <div className="doctor-avatar" style={{ backgroundColor: avatarColors[doctor?.name] || '#667eea' }}>
      <span className="avatar-text">{doctor?.name?.charAt(0) || '医'}</span>
    </div>
  );
};

// 医生信息卡片
const DoctorInfoCard = ({ doctor }) => {
  if (!doctor) return null;
  
  return (
    <div className="doctor-info-card">
      <DoctorAvatar doctor={doctor} />
      <div className="doctor-details">
        <h3>{doctor.name}</h3>
        <p className="title">{doctor.title}</p>
        <p className="department">{doctor.department}</p>
        <p className="hospital">{doctor.hospital}</p>
      </div>
    </div>
  );
};

function App() {
  const [messages, setMessages] = useState([
    {
      role: 'agent',
      content: '您好，我是陈雅琴医生，协和医院急诊科的分诊医师。请告诉我您哪里不舒服，我会帮您分析情况，并建议您应该挂什么科室。',
      agent_name: '分诊Agent',
      doctor_name: '陈雅琴',
      doctor_title: '副主任医师',
      doctor_department: '急诊医学科',
      doctor_hospital: '协和医院'
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [currentDoctor, setCurrentDoctor] = useState({
    name: '陈雅琴',
    title: '副主任医师',
    department: '急诊医学科',
    hospital: '协和医院'
  });
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim() || loading) return;

    const userMessage = { role: 'patient', content: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const response = await fetch('/api/v1/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: input,
          session_id: sessionId
        })
      });

      const data = await response.json();
      setSessionId(data.session_id);
      
      // 更新当前医生信息
      if (data.doctor_name) {
        setCurrentDoctor({
          name: data.doctor_name,
          title: data.doctor_title,
          department: data.doctor_department,
          hospital: data.doctor_hospital
        });
      }

      setMessages(prev => [...prev, {
        role: 'agent',
        content: data.message,
        agent_name: data.agent_name,
        doctor_name: data.doctor_name,
        doctor_title: data.doctor_title,
        doctor_department: data.doctor_department,
        doctor_hospital: data.doctor_hospital,
        suggestions: data.suggestions
      }]);
    } catch (error) {
      setMessages(prev => [...prev, {
        role: 'error',
        content: '网络错误，请稍后重试'
      }]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  // 罕见病场景测试用例
  const rareDiseaseCases = [
    {
      title: '戈谢病',
      symptoms: '医生您好，我孩子5岁了，肚子越来越大，脾脏肿大，经常骨痛，血小板减少',
      description: '遗传性溶酶体贮积症'
    },
    {
      title: '庞贝病',
      symptoms: '医生您好，我最近呼吸困难，肌肉无力，爬楼梯都费劲，心脏也有些问题',
      description: '糖原贮积症II型'
    },
    {
      title: '法布雷病',
      symptoms: '医生您好，我手脚经常烧灼样疼痛，出汗少，尿里有泡沫，皮肤有暗红色皮疹',
      description: 'X连锁遗传性溶酶体贮积症'
    },
    {
      title: '渐冻症',
      symptoms: '医生您好，我最近手部肌肉萎缩，握东西没力气，说话也有些含糊',
      description: '肌萎缩侧索硬化症'
    }
  ];

  const quickSymptoms = ['头痛', '发热', '咳嗽', '腹痛', '失眠'];

  return (
    <div className="app">
      <header className="header">
        <h1>🏥 MediChat</h1>
        <p>医疗多Agent智能交互平台 - 罕见病专版</p>
      </header>

      {/* 当前医生信息 */}
      <div className="current-doctor">
        <DoctorInfoCard doctor={currentDoctor} />
      </div>

      <div className="chat-container">
        <div className="messages">
          {messages.map((msg, idx) => (
            <div key={idx} className={`message ${msg.role}`}>
              {msg.role === 'agent' && msg.doctor_name && (
                <div className="message-header">
                  <DoctorAvatar doctor={{name: msg.doctor_name}} />
                  <div className="doctor-meta">
                    <span className="doctor-name">{msg.doctor_name}医生</span>
                    <span className="doctor-title">{msg.doctor_title} | {msg.doctor_department}</span>
                    <span className="doctor-hospital">{msg.doctor_hospital}</span>
                  </div>
                </div>
              )}
              <div className="message-content">{msg.content}</div>
              {msg.suggestions && (
                <div className="suggestions">
                  {msg.suggestions.map((s, i) => (
                    <button key={i} onClick={() => setInput(s)}>{s}</button>
                  ))}
                </div>
              )}
            </div>
          ))}
          {loading && (
            <div className="message agent">
              <div className="message-header">
                <DoctorAvatar doctor={currentDoctor} />
                <div className="doctor-meta">
                  <span className="doctor-name">{currentDoctor.name}医生</span>
                  <span className="typing">正在思考中...</span>
                </div>
              </div>
              <div className="loading-indicator">
                <div className="typing-dots">
                  <span></span><span></span><span></span>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* 罕见病测试场景 */}
        <div className="rare-disease-section">
          <h3>🧬 罕见病场景测试</h3>
          <div className="rare-disease-cases">
            {rareDiseaseCases.map((caseItem, idx) => (
              <button 
                key={idx}
                className="rare-disease-btn"
                onClick={() => setInput(caseItem.symptoms)}
                title={caseItem.description}
              >
                <span className="case-title">{caseItem.title}</span>
                <span className="case-desc">{caseItem.description}</span>
              </button>
            ))}
          </div>
        </div>

        {/* 快速症状 */}
        <div className="quick-actions">
          <h4>常见症状</h4>
          <div className="quick-buttons">
            {quickSymptoms.map(symptom => (
              <button 
                key={symptom} 
                className="quick-btn"
                onClick={() => setInput(symptom)}
              >
                {symptom}
              </button>
            ))}
          </div>
        </div>

        {/* 输入区域 */}
        <div className="input-area">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="请描述您的症状..."
            rows={2}
          />
          <button onClick={sendMessage} disabled={loading || !input.trim()}>
            发送
          </button>
        </div>
      </div>

      <footer className="footer">
        <p>⚠️ 本平台仅供参考，不替代专业医疗诊断</p>
        <p>🧬 专注于罕见病AI辅助诊断</p>
      </footer>
    </div>
  );
}

export default App;
