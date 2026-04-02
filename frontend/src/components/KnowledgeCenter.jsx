/**
 * MediChat-RD 前端增强 - 知识库详情页
 * 包含药物重定位功能
 */

import React, { useState, useEffect } from 'react';

const KnowledgeDetail = ({ disease, onClose }) => {
  const [drugName, setDrugName] = useState('');
  const [repurposingResult, setRepurposingResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const assessDrug = async () => {
    if (!drugName.trim()) return;
    
    setLoading(true);
    try {
      const response = await fetch('/api/v1/knowledge/drug-repurposing', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          drug_name: drugName,
          disease_name: disease.name
        })
      });
      const data = await response.json();
      setRepurposingResult(data);
    } catch (error) {
      console.error('药物重定位评估失败:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="knowledge-detail-overlay">
      <div className="knowledge-detail-modal">
        <button className="close-btn" onClick={onClose}>×</button>
        
        {/* 疾病基本信息 */}
        <div className="disease-header">
          <h2>{disease.name}</h2>
          <h3>{disease.name_en}</h3>
          <div className="disease-tags">
            <span className="tag category">{disease.category}</span>
            <span className="tag gene">{disease.gene}</span>
            <span className="tag inheritance">{disease.inheritance}</span>
          </div>
        </div>

        {/* 详细信息 */}
        <div className="disease-info">
          <div className="info-section">
            <h4>📊 流行病学</h4>
            <p>{disease.prevalence}</p>
          </div>

          <div className="info-section">
            <h4>🩺 临床表现</h4>
            <ul>
              {Array.isArray(disease.symptoms) 
                ? disease.symptoms.map((s, i) => <li key={i}>{s}</li>)
                : <li>{disease.symptoms}</li>
              }
            </ul>
          </div>

          <div className="info-section">
            <h4>🔬 诊断标准</h4>
            <p>{disease.diagnosis_criteria}</p>
          </div>

          <div className="info-section">
            <h4>💊 治疗方案</h4>
            <p>{disease.treatment_summary}</p>
          </div>

          <div className="info-section">
            <h4>🏥 推荐医院</h4>
            <div className="hospitals">
              {disease.specialist_hospitals.map((h, i) => (
                <span key={i} className="hospital-tag">{h}</span>
              ))}
            </div>
          </div>
        </div>

        {/* 药物重定位模块 */}
        <div className="drug-repurposing">
          <h4>🔬 药物重定位评估</h4>
          <div className="repurposing-input">
            <input
              type="text"
              placeholder="输入药物名称 (如: metformin)"
              value={drugName}
              onChange={(e) => setDrugName(e.target.value)}
            />
            <button onClick={assessDrug} disabled={loading}>
              {loading ? '评估中...' : '开始评估'}
            </button>
          </div>

          {repurposingResult && (
            <div className="repurposing-result">
              <div className="result-header">
                <h5>{repurposingResult.drug_name} → {disease.name}</h5>
                <div className="confidence" style={{color: repurposingResult.confidence_score >= 0.7 ? '#10B981' : repurposingResult.confidence_score >= 0.5 ? '#F59E0B' : '#EF4444'}}>
                  置信度: {(repurposingResult.confidence_score * 100).toFixed(0)}%
                </div>
              </div>
              
              <div className="result-details">
                <p><strong>靶点交集:</strong> {repurposingResult.target_overlap.join(', ') || '无显著交集'}</p>
                <p><strong>相关文献:</strong> {repurposingResult.literature_count} 篇</p>
                <p><strong>专家建议:</strong> {repurposingResult.recommendation}</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

const KnowledgeCenter = () => {
  const [diseases, setDiseases] = useState([]);
  const [selectedDisease, setSelectedDisease] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('');
  const [categories, setCategories] = useState({});
  const [stats, setStats] = useState(null);

  useEffect(() => {
    loadDiseases();
    loadStats();
  }, []);

  const loadDiseases = async () => {
    try {
      const response = await fetch('/api/v1/knowledge/diseases');
      const data = await response.json();
      setDiseases(data);
    } catch (error) {
      console.error('加载疾病列表失败:', error);
    }
  };

  const loadStats = async () => {
    try {
      const response = await fetch('/api/v1/knowledge/stats');
      const data = await response.json();
      setStats(data);
      setCategories(data.categories);
    } catch (error) {
      console.error('加载统计信息失败:', error);
    }
  };

  const searchDiseases = async () => {
    if (!searchQuery.trim()) {
      loadDiseases();
      return;
    }
    
    try {
      const response = await fetch(`/api/v1/knowledge/diseases/search/${encodeURIComponent(searchQuery)}`);
      const data = await response.json();
      setDiseases(data.results || []);
    } catch (error) {
      console.error('搜索失败:', error);
    }
  };

  const filterByCategory = async (category) => {
    setSelectedCategory(category);
    if (!category) {
      loadDiseases();
      return;
    }
    
    try {
      const response = await fetch(`/api/v1/knowledge/diseases/category/${encodeURIComponent(category)}`);
      const data = await response.json();
      setDiseases(data.diseases || []);
    } catch (error) {
      console.error('筛选失败:', error);
    }
  };

  return (
    <div className="knowledge-center">
      {/* 统计概览 */}
      {stats && (
        <div className="knowledge-stats">
          <div className="stat-card">
            <div className="stat-number">{stats.total_diseases}</div>
            <div className="stat-label">罕见病种类</div>
          </div>
          <div className="stat-card">
            <div className="stat-number">{stats.total_categories}</div>
            <div className="stat-label">疾病分类</div>
          </div>
          <div className="stat-card">
            <div className="stat-number">{stats.status === 'complete' ? '✅' : '⏳'}</div>
            <div className="stat-label">知识库状态</div>
          </div>
        </div>
      )}

      {/* 搜索和筛选 */}
      <div className="knowledge-controls">
        <div className="search-box">
          <input
            type="text"
            placeholder="搜索疾病名称、基因、症状..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && searchDiseases()}
          />
          <button onClick={searchDiseases}>🔍 搜索</button>
        </div>
        
        <div className="category-filter">
          <select 
            value={selectedCategory} 
            onChange={(e) => filterByCategory(e.target.value)}
          >
            <option value="">所有分类</option>
            {Object.entries(categories).map(([cat, count]) => (
              <option key={cat} value={cat}>{cat} ({count})</option>
            ))}
          </select>
        </div>
      </div>

      {/* 疾病列表 */}
      <div className="disease-list">
        {diseases.map((disease, index) => (
          <div 
            key={index} 
            className="disease-card"
            onClick={() => setSelectedDisease(disease)}
          >
            <div className="disease-name">
              <h4>{disease.name}</h4>
              <span className="name-en">{disease.name_en}</span>
            </div>
            <div className="disease-meta">
              <span className="category">{disease.category}</span>
              <span className="gene">{disease.gene}</span>
            </div>
            <div className="disease-preview">
              {disease.symptoms 
                ? (Array.isArray(disease.symptoms) 
                    ? disease.symptoms.slice(0, 2).join(', ') 
                    : disease.symptoms.substring(0, 50))
                : '暂无症状描述'}
              ...
            </div>
          </div>
        ))}
      </div>

      {/* 详情弹窗 */}
      {selectedDisease && (
        <KnowledgeDetail 
          disease={selectedDisease}
          onClose={() => setSelectedDisease(null)}
        />
      )}
    </div>
  );
};

export default KnowledgeCenter;
