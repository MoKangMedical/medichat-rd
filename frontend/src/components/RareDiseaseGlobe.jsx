import React, { useDeferredValue, useEffect, useRef, useState } from 'react';

const API_BASE = import.meta.env.VITE_API_URL || '';
const PREFILLED_DISEASE_STORAGE_KEY = 'medichat_selected_disease';
const ALL_CATEGORY = '全部';
const STICKERS = [
  { label: '陪伴', tone: 'mint' },
  { label: '希望', tone: 'peach' },
  { label: '行动', tone: 'gold' },
  { label: '连接', tone: 'sky' },
];
const ACTION_BANNERS = [
  { title: '行动陪伴', subtitle: '一步步看病种、症状和管理路径', position: 'left' },
  { title: '希望链接', subtitle: '直接连到病友圈与支持入口', position: 'right' },
];
const KEYWORD_PLACEHOLDERS = ['待详细补充', '未知', '待明确', '未明确', '未详', 'unknown', 'n/a', 'na'];

async function fetchJson(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, options);
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.detail || data.message || '请求失败');
  }
  return data;
}

function createSpherePoints(total) {
  const points = [];
  const goldenAngle = Math.PI * (3 - Math.sqrt(5));

  for (let index = 0; index < total; index += 1) {
    const y = 1 - (index / Math.max(total - 1, 1)) * 2;
    const radius = Math.sqrt(Math.max(0, 1 - y * y));
    const theta = goldenAngle * index;
    const x = Math.cos(theta) * radius;
    const z = Math.sin(theta) * radius;
    points.push({ x, y, z });
  }

  return points;
}

function rotatePoint(point, angleX, angleY) {
  const cosY = Math.cos(angleY);
  const sinY = Math.sin(angleY);
  const cosX = Math.cos(angleX);
  const sinX = Math.sin(angleX);

  const x1 = point.x * cosY - point.z * sinY;
  const z1 = point.x * sinY + point.z * cosY;
  const y1 = point.y * cosX - z1 * sinX;
  const z2 = point.y * sinX + z1 * cosX;

  return { x: x1, y: y1, z: z2 };
}

function normalizeText(value) {
  return String(value || '').trim().toLowerCase();
}

function isMeaningfulKeyword(value) {
  const normalized = normalizeText(value);
  if (!normalized) return false;
  return !KEYWORD_PLACEHOLDERS.includes(normalized);
}

function parseGeneTokens(rawGene) {
  const normalized = String(rawGene || '')
    .replace(/[()]/g, ' ')
    .replace(/未知|待明确|unknown/gi, ' ')
    .trim();
  if (!normalized) return [];
  return normalized
    .split(/[\s,，;/、]+/)
    .map((token) => token.trim().toUpperCase())
    .filter((token) => token && token.length <= 16 && /[A-Z0-9-]/.test(token));
}

function matchesSearch(item, query) {
  if (!query) return true;
  const haystack = [
    item.name,
    item.name_en,
    item.category,
    item.gene,
    item.prevalence,
    item.prevalence_tier,
    item.treatment_excerpt,
    item.community_hint,
    ...(item.symptoms || []),
  ]
    .map((value) => normalizeText(value))
    .join(' ');
  return haystack.includes(normalizeText(query));
}

function buildKeywordStats(items) {
  const geneStats = {};
  const symptomStats = {};

  items.forEach((item) => {
    parseGeneTokens(item.gene).forEach((gene) => {
      geneStats[gene] = (geneStats[gene] || 0) + 1;
    });
    (item.symptoms || []).forEach((symptom) => {
      if (!isMeaningfulKeyword(symptom)) return;
      symptomStats[symptom] = (symptomStats[symptom] || 0) + 1;
    });
  });

  const genes = Object.entries(geneStats)
    .sort((left, right) => right[1] - left[1])
    .map(([label, count]) => ({ label, count }));
  const symptoms = Object.entries(symptomStats)
    .sort((left, right) => right[1] - left[1])
    .map(([label, count]) => ({ label, count }));

  return { genes, symptoms };
}

export default function RareDiseaseGlobe({ onOpenDisease, onOpenCommunity, embedded = false }) {
  const [data, setData] = useState(null);
  const [error, setError] = useState('');
  const [selectedSlug, setSelectedSlug] = useState('');
  const [spotlightIndex, setSpotlightIndex] = useState(0);
  const [dragging, setDragging] = useState(false);
  const [hovering, setHovering] = useState(false);
  const [searchValue, setSearchValue] = useState('');
  const [activeCategory, setActiveCategory] = useState(ALL_CATEGORY);
  const [detailPulse, setDetailPulse] = useState(false);
  const deferredSearch = useDeferredValue(searchValue.trim());
  const stageRef = useRef(null);
  const itemRefs = useRef([]);
  const pointerRef = useRef({
    active: false,
    moved: false,
    lastX: 0,
    lastY: 0,
  });
  const anglesRef = useRef({ x: 0.72, y: 0.18 });
  const velocityRef = useRef({ x: -0.0015, y: 0.0024 });

  useEffect(() => {
    let cancelled = false;
    fetchJson('/api/v1/platform/disease-cloud')
      .then((payload) => {
        if (!cancelled) {
          setData(payload);
          if (payload.items?.length > 0) {
            setSelectedSlug(payload.items[0].slug);
          }
        }
      })
      .catch((fetchError) => {
        if (!cancelled) setError(fetchError.message);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const allItems = data?.items || [];
  const categories = [ALL_CATEGORY, ...new Set(allItems.map((item) => item.category).filter(Boolean))];
  const filteredItems = allItems.filter((item) => {
    if (activeCategory !== ALL_CATEGORY && item.category !== activeCategory) {
      return false;
    }
    return matchesSearch(item, deferredSearch);
  });
  const spotlightSlug = filteredItems[spotlightIndex]?.slug || '';

  useEffect(() => {
    const selectedStillVisible = filteredItems.some((item) => item.slug === selectedSlug);
    if (!selectedStillVisible) {
      setSelectedSlug(filteredItems[0]?.slug || '');
    }
  }, [filteredItems, selectedSlug]);

  useEffect(() => {
    if (!selectedSlug) return undefined;
    setDetailPulse(true);
    const timeoutId = window.setTimeout(() => setDetailPulse(false), 480);
    return () => window.clearTimeout(timeoutId);
  }, [selectedSlug]);

  useEffect(() => {
    if (filteredItems.length <= 1) return undefined;
    const timer = window.setInterval(() => {
      if (pointerRef.current.active || dragging) return;
      setSpotlightIndex((current) => (current + 1) % filteredItems.length);
    }, 2800);
    return () => window.clearInterval(timer);
  }, [filteredItems, dragging]);

  useEffect(() => {
    if (spotlightIndex >= filteredItems.length) {
      setSpotlightIndex(0);
    }
  }, [filteredItems.length, spotlightIndex]);

  useEffect(() => {
    const stage = stageRef.current;
    const items = filteredItems;
    if (!stage || items.length === 0) return undefined;

    const points = createSpherePoints(items.length);
    let frameId = 0;

    const paint = () => {
      const bounds = stage.getBoundingClientRect();
      const radius = Math.min(bounds.width, bounds.height) * 0.34;
      const perspective = radius * 2.8;
      const centerX = bounds.width / 2;
      const centerY = bounds.height / 2;

      if (!pointerRef.current.active) {
        const driftFactor = hovering ? 0.46 : 1;
        const damping = hovering ? 0.989 : 0.994;
        const baseX = hovering ? -0.00035 : -0.00065;
        const baseY = hovering ? 0.00095 : 0.00165;

        anglesRef.current.x += velocityRef.current.x * driftFactor;
        anglesRef.current.y += velocityRef.current.y * driftFactor;
        velocityRef.current.x = (velocityRef.current.x * damping) + baseX;
        velocityRef.current.y = (velocityRef.current.y * damping) + baseY;
      }

      items.forEach((item, index) => {
        const node = itemRefs.current[index];
        if (!node) return;
        const rotated = rotatePoint(points[index], anglesRef.current.x, anglesRef.current.y);
        const scale = perspective / (perspective + (rotated.z + 1.4) * radius);
        const posX = centerX + rotated.x * radius * scale;
        const posY = centerY + rotated.y * radius * scale;
        const isSelected = selectedSlug === item.slug;
        const isSpotlight = item.slug === spotlightSlug;
        const expanded = isSelected || isSpotlight || (rotated.z > 0.48 && index % 3 === 0);
        const size = expanded
          ? 10 + (item.weight * 9) + Math.max(0, rotated.z) * 3
          : 8.5 + (item.weight * 3.5) + Math.max(0, rotated.z) * 1.4;
        const opacity = 0.28 + ((rotated.z + 1) / 2) * 0.72;

        node.style.left = `${posX}px`;
        node.style.top = `${posY}px`;
        node.style.opacity = `${opacity}`;
        node.style.fontSize = `${size}px`;
        node.style.zIndex = `${Math.round((rotated.z + 1) * 100)}`;
        node.dataset.expanded = expanded ? 'true' : 'false';
        node.dataset.spotlight = isSpotlight ? 'true' : 'false';
        node.style.transform = `translate(-50%, -50%) scale(${isSelected ? 1.16 : isSpotlight ? 1.07 : 1})`;
        node.style.color = item.care_status.accent;
        node.style.textShadow = expanded ? `0 10px 28px ${item.care_status.accent}22` : 'none';
      });

      frameId = window.requestAnimationFrame(paint);
    };

    frameId = window.requestAnimationFrame(paint);
    return () => window.cancelAnimationFrame(frameId);
  }, [filteredItems, hovering, selectedSlug, spotlightSlug]);

  const selected = filteredItems.find((item) => item.slug === selectedSlug) || filteredItems[0] || null;
  const spotlight = filteredItems[spotlightIndex] || filteredItems[0] || null;
  const hasFilters = Boolean(deferredSearch) || activeCategory !== ALL_CATEGORY;
  const featuredDiseases = [...allItems]
    .sort((left, right) => (right.weight || 0) - (left.weight || 0))
    .slice(0, 12);
  const { genes: allGenes, symptoms: allSymptoms } = buildKeywordStats(allItems);
  const featuredGenes = allGenes.slice(0, 12);
  const featuredSymptoms = allSymptoms.slice(0, 12);
  const hottestDisease = [...filteredItems].sort((left, right) => (right.weight || 0) - (left.weight || 0))[0] || null;
  const { genes: visibleGenes, symptoms: visibleSymptoms } = buildKeywordStats(filteredItems);
  const hottestGene = visibleGenes[0] || null;
  const hottestSymptom = visibleSymptoms[0] || null;
  const selectedGenes = parseGeneTokens(selected?.gene || '').filter(isMeaningfulKeyword).slice(0, 3);
  const selectedSymptoms = (selected?.symptoms || []).filter(isMeaningfulKeyword).slice(0, 4);
  const spotlightSymptoms = (spotlight?.symptoms || []).filter(isMeaningfulKeyword).slice(0, 3);

  const handlePointerDown = (event) => {
    pointerRef.current.active = true;
    pointerRef.current.moved = false;
    pointerRef.current.lastX = event.clientX;
    pointerRef.current.lastY = event.clientY;
    setDragging(true);
  };

  const handlePointerMove = (event) => {
    if (!pointerRef.current.active) return;
    const dx = event.clientX - pointerRef.current.lastX;
    const dy = event.clientY - pointerRef.current.lastY;
    if (Math.abs(dx) > 2 || Math.abs(dy) > 2) {
      pointerRef.current.moved = true;
    }
    pointerRef.current.lastX = event.clientX;
    pointerRef.current.lastY = event.clientY;
    anglesRef.current.y += dx * 0.0055;
    anglesRef.current.x += dy * 0.0055;
    velocityRef.current.y = dx * 0.00032;
    velocityRef.current.x = dy * 0.00032;
  };

  const handlePointerUp = () => {
    pointerRef.current.active = false;
    setDragging(false);
  };

  const handleSelectItem = (slug) => {
    setSelectedSlug(slug);
    velocityRef.current.x *= 0.84;
    velocityRef.current.y *= 0.84;
  };

  const openDisease = () => {
    if (!selected) return;
    window.localStorage.setItem(PREFILLED_DISEASE_STORAGE_KEY, selected.name);
    onOpenDisease?.(selected);
  };

  const openCommunity = () => {
    if (!selected) return;
    onOpenCommunity?.(selected);
  };

  const handleKeywordDisease = (disease) => {
    setActiveCategory(ALL_CATEGORY);
    setSearchValue('');
    setSelectedSlug(disease.slug);
  };

  const handleKeywordSearch = (keyword) => {
    setActiveCategory(ALL_CATEGORY);
    setSearchValue(keyword);
  };

  const overlayLabel = dragging
    ? '拖动中 · 惯性已锁定'
    : hasFilters
      ? `已聚焦 ${filteredItems.length} 个病种`
      : hovering
        ? '自动旋转减速中'
        : '自动旋转中 · 按住拖动';

  const renderKeywordBelt = ({ title, hint, type, items, getKey, getLabel, getCount, onSelect, isActive, direction }) => (
    <div className="disease-orbit-keyword-card">
      <div className="disease-orbit-keyword-head">
        <strong>{title}</strong>
        <span>{hint}</span>
      </div>
      <div className="disease-orbit-keyword-belt">
        <div className={`disease-orbit-keyword-track ${direction === 'reverse' ? 'reverse' : ''}`}>
          {[0, 1].flatMap((copyIndex) => items.map((item) => (
            <button
              key={`${getKey(item)}-${copyIndex}`}
              type="button"
              className={`disease-orbit-keyword ${type} ${isActive(item) ? 'active' : ''}`}
              onClick={() => onSelect(item)}
              title={getLabel(item)}
            >
              <span>{getLabel(item)}</span>
              {typeof getCount === 'function' && <small>{getCount(item)}</small>}
            </button>
          )))}
        </div>
      </div>
    </div>
  );

  return (
    <section className={`disease-orbit-section${embedded ? ' disease-orbit-section-embedded' : ''}`}>
      <div className="section-head">
        <span>{data?.title || 'Rare disease orbit'}</span>
        <span className="section-note">
          {filteredItems.length || 0} / {data?.stats?.total_diseases || 0} 个病种 · {data?.stats?.categories || 0} 类疾病
        </span>
      </div>
      <p className="disease-orbit-intro">
        {data?.subtitle || '把全部病种放进一个可拖拽的动态球体里。字越大，说明在人群里相对更常见；颜色则提示更偏向治疗、长期管理还是研究推进。'}
      </p>

      <div className="disease-orbit-keyword-deck">
        {renderKeywordBelt({
          title: '关键病种',
          hint: '自动滚动的病种热词，点一下直接聚焦',
          type: 'disease',
          items: featuredDiseases,
          getKey: (item) => item.slug,
          getLabel: (item) => item.name,
          onSelect: handleKeywordDisease,
          isActive: (item) => selectedSlug === item.slug,
          direction: 'forward',
        })}

        {renderKeywordBelt({
          title: '关键基因',
          hint: '自动滚动的基因热词，点一下直接抓取相关病种',
          type: 'gene',
          items: featuredGenes,
          getKey: (item) => item.label,
          getLabel: (item) => item.label,
          getCount: (item) => item.count,
          onSelect: (item) => handleKeywordSearch(item.label),
          isActive: (item) => normalizeText(searchValue) === normalizeText(item.label),
          direction: 'reverse',
        })}

        {renderKeywordBelt({
          title: '关键症状',
          hint: '自动滚动的症状热词，点一下直接筛出相关症状群',
          type: 'symptom',
          items: featuredSymptoms,
          getKey: (item) => item.label,
          getLabel: (item) => item.label,
          getCount: (item) => item.count,
          onSelect: (item) => handleKeywordSearch(item.label),
          isActive: (item) => normalizeText(searchValue) === normalizeText(item.label),
          direction: 'forward',
        })}
      </div>

      <div className="disease-orbit-flowbar">
        <div className="disease-orbit-flowbar-head">
          <strong>当前最热病流</strong>
          <span>{hasFilters ? '跟随当前筛选实时刷新' : '基于首页当前可见病种实时聚合'}</span>
        </div>
        <div className="disease-orbit-flowbar-track">
          <button
            type="button"
            className="disease-orbit-flow-pill disease"
            onClick={() => hottestDisease && handleKeywordDisease(hottestDisease)}
            disabled={!hottestDisease}
          >
            <small>最热病种</small>
            <strong>{hottestDisease?.name || '暂无'}</strong>
          </button>
          <button
            type="button"
            className="disease-orbit-flow-pill gene"
            onClick={() => hottestGene && handleKeywordSearch(hottestGene.label)}
            disabled={!hottestGene}
          >
            <small>最热基因</small>
            <strong>{hottestGene?.label || '暂无'}</strong>
          </button>
          <button
            type="button"
            className="disease-orbit-flow-pill symptom"
            onClick={() => hottestSymptom && handleKeywordSearch(hottestSymptom.label)}
            disabled={!hottestSymptom}
          >
            <small>最热症状</small>
            <strong>{hottestSymptom?.label || '暂无'}</strong>
          </button>
        </div>
        <div className="disease-orbit-flowbar-caption">
          {hottestDisease && hottestGene && hottestSymptom
            ? `现在大家最容易先点进 ${hottestDisease.name}，再追踪 ${hottestGene.label}，并继续围绕“${hottestSymptom.label}”展开互动。`
            : '当前可见病流不足，先尝试切换病种分类或输入一个基因/症状关键词。'}
        </div>
      </div>

      <div className="disease-orbit-variable-grid">
        <button
          type="button"
          className="disease-orbit-variable-card disease"
          onClick={() => selected && handleKeywordDisease(selected)}
          disabled={!selected}
        >
          <small>当前病种</small>
          <strong>{selected?.name || '等待病种聚焦'}</strong>
          <span>{selected?.category || '点击左侧病流即可聚焦详情'}</span>
        </button>

        <button
          type="button"
          className="disease-orbit-variable-card gene"
          onClick={() => selectedGenes[0] && handleKeywordSearch(selectedGenes[0])}
          disabled={!selectedGenes.length}
        >
          <small>关键基因</small>
          <strong>{selectedGenes[0] || '等待基因浮现'}</strong>
          <span>{selectedGenes.slice(1).join(' / ') || (selected?.gene || '从病种详情自动抓取')}</span>
        </button>

        <div className="disease-orbit-variable-card symptom">
          <small>症状关键词</small>
          <strong>{selectedSymptoms[0] || hottestSymptom?.label || '等待症状聚焦'}</strong>
          <div className="disease-orbit-variable-tags">
            {(selectedSymptoms.length ? selectedSymptoms : visibleSymptoms.slice(0, 4).map((item) => item.label)).map((symptom) => (
              <button
                key={symptom}
                type="button"
                className="disease-orbit-variable-tag"
                onClick={() => handleKeywordSearch(symptom)}
              >
                {symptom}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="disease-orbit-spotlight-strip">
        <div className="disease-orbit-spotlight-head">
          <strong>病流轮播</strong>
          <span>{spotlight ? `${spotlightIndex + 1} / ${filteredItems.length}` : '等待病种'}</span>
        </div>
        {spotlight && (
          <button
            type="button"
            className="disease-orbit-spotlight-card"
            onClick={() => handleSelectItem(spotlight.slug)}
          >
            <div className="disease-orbit-spotlight-copy">
              <small>{spotlight.category} · {spotlight.prevalence}</small>
              <strong>{spotlight.name}</strong>
              <p>{spotlight.treatment_excerpt}</p>
              <div className="disease-orbit-spotlight-tags">
                {spotlightSymptoms.map((symptom) => (
                  <span key={symptom}>{symptom}</span>
                ))}
              </div>
            </div>
            <div className="disease-orbit-spotlight-meta">
              <span>{spotlight.gene}</span>
              <span>{spotlight.care_status.label}</span>
              <span>点击查看症状变化</span>
            </div>
          </button>
        )}
      </div>

      <div className="disease-orbit-toolbar">
        <label className="disease-orbit-search">
          <span>搜索病种 / 基因 / 症状</span>
          <input
            type="text"
            value={searchValue}
            onChange={(event) => setSearchValue(event.target.value)}
            placeholder="例如：法布雷病、GBA、肌无力"
          />
        </label>
        <div className="disease-orbit-toolbar-meta">
          <strong>{filteredItems.length}</strong>
          <span>当前可见病种</span>
        </div>
      </div>

      <div className="disease-orbit-filter-row">
        {categories.map((category) => (
          <button
            key={category}
            type="button"
            className={`disease-orbit-filter ${activeCategory === category ? 'active' : ''}`}
            onClick={() => setActiveCategory(category)}
          >
            {category}
          </button>
        ))}
      </div>

      <div className={`disease-orbit-shell${embedded ? ' embedded' : ''}`}>
        <div
          ref={stageRef}
          className={`disease-orbit-stage ${dragging ? 'dragging' : ''}${embedded ? ' embedded' : ''}`}
          style={{ '--selected-accent': selected?.care_status?.accent || '#0DBF9B' }}
          onPointerDown={handlePointerDown}
          onPointerMove={handlePointerMove}
          onPointerUp={handlePointerUp}
          onPointerCancel={handlePointerUp}
          onPointerLeave={() => {
            handlePointerUp();
            setHovering(false);
          }}
          onPointerEnter={() => setHovering(true)}
        >
          <div className="disease-orbit-sky">
            {STICKERS.map((sticker, index) => (
              <span
                key={sticker.label}
                className={`disease-orbit-sticker tone-${sticker.tone} sticker-${index + 1}`}
              >
                {sticker.label}
              </span>
            ))}
          </div>
          {ACTION_BANNERS.map((banner) => (
            <div
              key={banner.title}
              className={`disease-orbit-hope-ribbon ribbon-${banner.position}`}
              aria-hidden="true"
            >
              <strong>{banner.title}</strong>
              <span>{banner.subtitle}</span>
            </div>
          ))}
          <div className="disease-orbit-companion-scene scene-left" aria-hidden="true">
            <div className="disease-orbit-companion-caption">妈妈陪着孩子一起认识病流</div>
            <div className="disease-orbit-family">
              <div className="disease-orbit-character mother">
                <span className="character-hair" />
                <span className="character-head" />
                <span className="character-body" />
                <span className="character-arm arm-left" />
                <span className="character-arm arm-right" />
              </div>
              <div className="disease-orbit-character child">
                <span className="character-head" />
                <span className="character-body" />
                <span className="character-arm arm-left" />
                <span className="character-arm arm-right" />
              </div>
              <span className="disease-orbit-scene-heart heart-left" />
              <span className="disease-orbit-scene-heart heart-right" />
            </div>
          </div>
          <div className="disease-orbit-companion-scene scene-right" aria-hidden="true">
            <div className="disease-orbit-companion-caption">孩子和玩偶一起进入希望链接</div>
            <div className="disease-orbit-family family-right">
              <div className="disease-orbit-character child buddy">
                <span className="character-head" />
                <span className="character-body" />
                <span className="character-arm arm-left" />
                <span className="character-arm arm-right" />
              </div>
              <div className="disease-orbit-plush bunny">
                <span className="plush-ear ear-left" />
                <span className="plush-ear ear-right" />
                <span className="plush-head" />
                <span className="plush-body" />
              </div>
              <span className="disease-orbit-scene-spark spark-one" />
              <span className="disease-orbit-scene-spark spark-two" />
            </div>
          </div>
          <div className="disease-orbit-core" />
          <div className="disease-orbit-ring disease-orbit-ring-one" />
          <div className="disease-orbit-ring disease-orbit-ring-two" />
          {filteredItems.length === 0 && (
            <div className="disease-orbit-empty">
              没找到匹配病种，试试输入疾病名、基因或症状关键词。
            </div>
          )}
          {filteredItems.map((item, index) => (
            <button
              key={item.slug}
              ref={(node) => {
                itemRefs.current[index] = node;
              }}
              type="button"
              className={`disease-orbit-word ${selectedSlug === item.slug ? 'active' : ''}`}
              onClick={() => handleSelectItem(item.slug)}
              title={`${item.name} · ${item.prevalence}`}
            >
              <span className="disease-orbit-word-dot" />
              <span className="disease-orbit-word-label">{item.name}</span>
            </button>
          ))}
          <div className="disease-orbit-overlay">
            <span>{overlayLabel}</span>
          </div>
        </div>

        <div className={`disease-orbit-detail${embedded ? ' embedded' : ''}`}>
          {selected ? (
            <div
              key={selected.slug}
              className={`disease-orbit-detail-card ${detailPulse ? 'spotlight' : ''}`}
              style={{ '--accent': selected.care_status.accent }}
            >
              <div className="disease-orbit-detail-kicker">
                <div className="disease-orbit-badge">{selected.care_status.label}</div>
                <span className="disease-orbit-detail-chip">{selected.community_hint}</span>
              </div>
              <h3 className="disease-orbit-detail-title">{selected.name}</h3>
              <div className="disease-orbit-meta">
                <span>{selected.category}</span>
                <span>{selected.gene}</span>
                <span>{selected.prevalence}</span>
              </div>

              <div className="disease-orbit-route">
                <strong>管理与治疗路径</strong>
                <p>{selected.treatment_excerpt}</p>
              </div>

              <div className="disease-orbit-highlights">
                <div className="disease-orbit-highlight">
                  <small>流行度层级</small>
                  <strong>{selected.prevalence_tier}</strong>
                </div>
                <div className="disease-orbit-highlight">
                  <small>照护提示</small>
                  <strong>{selected.care_status.description}</strong>
                </div>
                <div className="disease-orbit-highlight">
                  <small>病友连接</small>
                  <strong>{selected.community_hint}</strong>
                </div>
              </div>

              {selected.symptoms?.length > 0 && (
                <div className="disease-orbit-tags">
                  {selected.symptoms.map((symptom) => (
                    <span key={symptom}>{symptom}</span>
                  ))}
                </div>
              )}

              <div className="disease-orbit-actions">
                <button type="button" className="primary-btn disease-orbit-action-cta disease-orbit-action-primary" onClick={openDisease}>
                  <small>行动陪伴</small>
                  <span>飞入疾病介绍</span>
                </button>
                <button type="button" className="ghost-btn disease-orbit-action-cta disease-orbit-action-secondary" onClick={openCommunity}>
                  <small>希望链接</small>
                  <span>进入相关病友圈</span>
                </button>
              </div>

              <div className="disease-orbit-legend">
                {(data?.legend || []).map((item) => (
                  <div key={item.key} className="disease-orbit-legend-row">
                    <span className="disease-orbit-dot" style={{ background: item.accent }} />
                    <div>
                      <strong>{item.label}</strong>
                      <p>{item.description}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="disease-orbit-empty-panel">
              试着换一个分类或搜索词，挑一个病种后会在这里飞入详情。
            </div>
          )}
        </div>
      </div>

      {error && <div className="inline-error">{error}</div>}
    </section>
  );
}
