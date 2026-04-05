import React, { useState, useEffect } from 'react';

const API_BASE = import.meta.env.VITE_API_URL || '';

// ========== 社群首页 ==========
export default function CommunityPanel() {
  const [communities, setCommunities] = useState([]);
  const [selectedComm, setSelectedComm] = useState(null);
  const [posts, setPosts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showCreateAvatar, setShowCreateAvatar] = useState(false);
  const [showCreatePost, setShowCreatePost] = useState(false);
  const [myAvatar, setMyAvatar] = useState(null);

  useEffect(() => { loadCommunities(); }, []);

  const loadCommunities = async () => {
    try {
      const resp = await fetch(`${API_BASE}/api/v1/community/list`);
      const data = await resp.json();
      if (data.ok) setCommunities(data.communities);
    } catch (e) { console.error(e); }
  };

  const loadPosts = async (commId) => {
    setLoading(true);
    try {
      const resp = await fetch(`${API_BASE}/api/v1/community/${commId}/posts`);
      const data = await resp.json();
      if (data.ok) setPosts(data.posts);
    } catch (e) { console.error(e); }
    setLoading(false);
  };

  const handleSelectComm = (comm) => {
    setSelectedComm(comm);
    loadPosts(comm.id);
  };

  return (
    <div style={{
      maxWidth: 800, margin: '0 auto', padding: '20px 16px',
      fontFamily: '-apple-system, "PingFang SC", sans-serif',
    }}>
      {/* 标题 */}
      <div style={{
        textAlign: 'center', marginBottom: 24,
        background: 'linear-gradient(135deg, #07C160 0%, #059B48 100%)',
        borderRadius: 20, padding: '32px 24px', color: '#fff',
      }}>
        <div style={{ fontSize: 36, marginBottom: 8 }}>🤝</div>
        <h1 style={{ fontSize: 24, fontWeight: 800, margin: 0 }}>
          罕见病互助社群
        </h1>
        <p style={{ fontSize: 14, opacity: 0.85, marginTop: 8 }}>
          Second Me驱动 · AI数字分身 · Bridge智能配对
        </p>
      </div>

      {/* 我的分身 */}
      {myAvatar ? (
        <div style={{
          background: '#fff', borderRadius: 16, padding: 16, marginBottom: 16,
          boxShadow: '0 2px 12px rgba(0,0,0,.06)',
          display: 'flex', alignItems: 'center', gap: 12,
        }}>
          <div style={{
            width: 48, height: 48, borderRadius: '50%',
            background: 'linear-gradient(135deg, #07C160, #059B48)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: 20, color: '#fff',
          }}>👤</div>
          <div>
            <div style={{ fontWeight: 700, fontSize: 15 }}>{myAvatar.nickname}</div>
            <div style={{ fontSize: 12, color: '#666' }}>{myAvatar.disease_type} · AI分身在线</div>
          </div>
          <button onClick={() => setShowCreatePost(true)} style={{
            marginLeft: 'auto', padding: '8px 16px', borderRadius: 20,
            background: '#07C160', color: '#fff', border: 'none',
            fontSize: 13, fontWeight: 600, cursor: 'pointer',
          }}>📝 发帖</button>
        </div>
      ) : (
        <button onClick={() => setShowCreateAvatar(true)} style={{
          width: '100%', padding: 16, borderRadius: 16,
          background: '#fff', border: '2px dashed #07C160',
          color: '#07C160', fontSize: 15, fontWeight: 600,
          cursor: 'pointer', marginBottom: 16,
        }}>
          ➕ 创建我的AI分身，加入社群
        </button>
      )}

      {/* 社群列表 / 帖子列表 */}
      {!selectedComm ? (
        <div>
          <h3 style={{ fontSize: 16, fontWeight: 700, marginBottom: 12 }}>📋 社群列表</h3>
          <div style={{ display: 'grid', gap: 12 }}>
            {communities.map(comm => (
              <div key={comm.id} onClick={() => handleSelectComm(comm)} style={{
                background: '#fff', borderRadius: 14, padding: 16,
                boxShadow: '0 1px 8px rgba(0,0,0,.04)',
                cursor: 'pointer', transition: 'transform 0.15s',
                border: '1px solid #f0f0f0',
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <div style={{ fontWeight: 700, fontSize: 15 }}>
                      {comm.type === '按疾病' ? '💜' : '💬'} {comm.name}
                    </div>
                    <div style={{ fontSize: 12, color: '#888', marginTop: 4 }}>{comm.description}</div>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <div style={{ fontSize: 12, color: '#07C160', fontWeight: 600 }}>
                      {comm.post_count} 帖子
                    </div>
                    <div style={{ fontSize: 11, color: '#999' }}>
                      {comm.member_count} 成员
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : (
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
            <button onClick={() => { setSelectedComm(null); setPosts([]); }} style={{
              padding: '6px 12px', borderRadius: 8, border: '1px solid #eee',
              background: '#fff', fontSize: 13, cursor: 'pointer',
            }}>← 返回</button>
            <h3 style={{ fontSize: 16, fontWeight: 700, margin: 0 }}>{selectedComm.name}</h3>
          </div>

          {loading ? (
            <div style={{ textAlign: 'center', padding: 40, color: '#999' }}>加载中...</div>
          ) : posts.length === 0 ? (
            <div style={{ textAlign: 'center', padding: 40, color: '#999' }}>
              暂无帖子，发第一条吧！
            </div>
          ) : (
            <div style={{ display: 'grid', gap: 12 }}>
              {posts.map(post => (
                <div key={post.id} style={{
                  background: '#fff', borderRadius: 14, padding: 16,
                  boxShadow: '0 1px 8px rgba(0,0,0,.04)',
                  border: '1px solid #f0f0f0',
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <div style={{
                        width: 32, height: 32, borderRadius: '50%',
                        background: '#E8F5E9', display: 'flex',
                        alignItems: 'center', justifyContent: 'center', fontSize: 14,
                      }}>👤</div>
                      <div>
                        <div style={{ fontWeight: 600, fontSize: 14 }}>{post.author}</div>
                        <div style={{ fontSize: 11, color: '#999' }}>{post.created_at}</div>
                      </div>
                    </div>
                    <span style={{
                      padding: '2px 10px', borderRadius: 12, fontSize: 11,
                      background: post.type === '求助提问' ? '#FFF3E0' :
                                  post.type === '经验分享' ? '#E8F5E9' :
                                  post.type === '心理支持' ? '#F3E5F5' : '#E3F2FD',
                      color: post.type === '求助提问' ? '#E65100' :
                             post.type === '经验分享' ? '#2E7D32' :
                             post.type === '心理支持' ? '#6A1B9A' : '#1565C0',
                    }}>{post.type}</span>
                  </div>
                  <div style={{ fontSize: 14, lineHeight: 1.7, color: '#333' }}>
                    {post.content}
                  </div>
                  <div style={{ marginTop: 10, display: 'flex', gap: 16, fontSize: 12, color: '#999' }}>
                    <span>❤️ {post.likes}</span>
                    <span>💬 回复</span>
                    <span>🔗 Bridge连接</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* 创建分身弹窗 */}
      {showCreateAvatar && (
        <CreateAvatarModal
          onClose={() => setShowCreateAvatar(false)}
          onSuccess={(avatar) => { setMyAvatar(avatar); setShowCreateAvatar(false); }}
        />
      )}

      {/* 发帖弹窗 */}
      {showCreatePost && myAvatar && selectedComm && (
        <CreatePostModal
          communityId={selectedComm.id}
          avatarId={myAvatar.id}
          nickname={myAvatar.nickname}
          onClose={() => setShowCreatePost(false)}
          onSuccess={() => { setShowCreatePost(false); loadPosts(selectedComm.id); }}
        />
      )}
    </div>
  );
}


// ========== 创建分身弹窗 ==========
function CreateAvatarModal({ onClose, onSuccess }) {
  const [form, setForm] = useState({ nickname: '', disease_type: '', age: '', symptoms: '', diagnosis: '' });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    if (!form.nickname || !form.disease_type) return;
    setLoading(true);
    try {
      const resp = await fetch(`${API_BASE}/api/v1/community/avatar/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form),
      });
      const data = await resp.json();
      if (data.ok) onSuccess(data.avatar);
    } catch (e) { console.error(e); }
    setLoading(false);
  };

  return (
    <div style={{
      position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
      background: 'rgba(0,0,0,.5)', display: 'flex', alignItems: 'center',
      justifyContent: 'center', zIndex: 1000, padding: 16,
    }}>
      <div style={{
        background: '#fff', borderRadius: 20, padding: 24, width: '100%', maxWidth: 400,
      }}>
        <h3 style={{ fontSize: 18, fontWeight: 700, marginBottom: 16, textAlign: 'center' }}>
          🤖 创建AI分身
        </h3>
        <p style={{ fontSize: 12, color: '#888', textAlign: 'center', marginBottom: 16 }}>
          Second Me将为你创建一个数字分身，代表你在社群中交流
        </p>
        {[
          { key: 'nickname', label: '昵称', placeholder: '例如：小明妈妈' },
          { key: 'disease_type', label: '疾病类型', placeholder: '例如：戈谢病' },
          { key: 'age', label: '年龄', placeholder: '选填', type: 'number' },
          { key: 'symptoms', label: '主要症状', placeholder: '选填' },
          { key: 'diagnosis', label: '诊断结果', placeholder: '选填' },
        ].map(f => (
          <div key={f.key} style={{ marginBottom: 12 }}>
            <label style={{ fontSize: 13, color: '#666', fontWeight: 600 }}>{f.label}</label>
            <input
              type={f.type || 'text'}
              placeholder={f.placeholder}
              value={form[f.key]}
              onChange={e => setForm({ ...form, [f.key]: e.target.value })}
              style={{
                width: '100%', padding: '10px 14px', border: '2px solid #eee',
                borderRadius: 10, fontSize: 14, marginTop: 4, outline: 'none',
              }}
            />
          </div>
        ))}
        <div style={{ display: 'flex', gap: 10, marginTop: 16 }}>
          <button onClick={onClose} style={{
            flex: 1, padding: 12, borderRadius: 12, border: '1px solid #eee',
            background: '#fff', fontSize: 14, cursor: 'pointer',
          }}>取消</button>
          <button onClick={handleSubmit} disabled={loading} style={{
            flex: 2, padding: 12, borderRadius: 12, border: 'none',
            background: '#07C160', color: '#fff', fontSize: 14, fontWeight: 600,
            cursor: loading ? 'not-allowed' : 'pointer',
          }}>{loading ? '创建中...' : '创建分身'}</button>
        </div>
      </div>
    </div>
  );
}


// ========== 发帖弹窗 ==========
function CreatePostModal({ communityId, avatarId, nickname, onClose, onSuccess }) {
  const [content, setContent] = useState('');
  const [postType, setPostType] = useState('经验分享');
  const [loading, setLoading] = useState(false);

  const handlePost = async () => {
    if (!content.trim()) return;
    setLoading(true);
    try {
      const resp = await fetch(`${API_BASE}/api/v1/community/post`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          community_id: communityId,
          avatar_id: avatarId,
          nickname: nickname,
          content: content,
          post_type: postType,
        }),
      });
      const data = await resp.json();
      if (data.ok) onSuccess();
    } catch (e) { console.error(e); }
    setLoading(false);
  };

  return (
    <div style={{
      position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
      background: 'rgba(0,0,0,.5)', display: 'flex', alignItems: 'center',
      justifyContent: 'center', zIndex: 1000, padding: 16,
    }}>
      <div style={{
        background: '#fff', borderRadius: 20, padding: 24, width: '100%', maxWidth: 400,
      }}>
        <h3 style={{ fontSize: 18, fontWeight: 700, marginBottom: 16, textAlign: 'center' }}>
          📝 发帖
        </h3>
        <div style={{ marginBottom: 12 }}>
          <label style={{ fontSize: 13, color: '#666', fontWeight: 600 }}>帖子类型</label>
          <div style={{ display: 'flex', gap: 8, marginTop: 8 }}>
            {['经验分享', '求助提问', '心理支持', '科普信息'].map(t => (
              <button key={t} onClick={() => setPostType(t)} style={{
                padding: '6px 12px', borderRadius: 16, fontSize: 12,
                border: postType === t ? '2px solid #07C160' : '1px solid #eee',
                background: postType === t ? '#E8F5E9' : '#fff',
                color: postType === t ? '#07C160' : '#666',
                cursor: 'pointer',
              }}>{t}</button>
            ))}
          </div>
        </div>
        <div style={{ marginBottom: 12 }}>
          <label style={{ fontSize: 13, color: '#666', fontWeight: 600 }}>内容</label>
          <textarea
            placeholder="分享你的经历或提出问题..."
            value={content}
            onChange={e => setContent(e.target.value)}
            rows={4}
            style={{
              width: '100%', padding: '12px 14px', border: '2px solid #eee',
              borderRadius: 10, fontSize: 14, marginTop: 4, outline: 'none',
              resize: 'vertical', fontFamily: 'inherit',
            }}
          />
        </div>
        <div style={{ display: 'flex', gap: 10 }}>
          <button onClick={onClose} style={{
            flex: 1, padding: 12, borderRadius: 12, border: '1px solid #eee',
            background: '#fff', fontSize: 14, cursor: 'pointer',
          }}>取消</button>
          <button onClick={handlePost} disabled={loading} style={{
            flex: 2, padding: 12, borderRadius: 12, border: 'none',
            background: '#07C160', color: '#fff', fontSize: 14, fontWeight: 600,
            cursor: loading ? 'not-allowed' : 'pointer',
          }}>{loading ? '发送中...' : '发布'}</button>
        </div>
      </div>
    </div>
  );
}
