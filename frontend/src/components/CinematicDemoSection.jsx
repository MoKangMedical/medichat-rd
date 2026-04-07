import React, { useEffect, useMemo, useRef, useState } from 'react';
import { STORY_SCENES } from './cinematicDemoStoryboard.js';

const PREVIEW_VARIANTS = {
  landscape: {
    id: 'landscape',
    label: '横屏品牌片',
    kicker: '官网演示 / 路演大屏',
    description: '更适合官网首页、会议展示和横屏路演。',
    src: '/demo/medichatrd_brand_story_landscape_preview.mp4',
    poster: '/demo/medichatrd_brand_story_landscape_poster.jpg',
    downloadName: 'medichatrd-brand-story-landscape.mp4',
  },
  portrait: {
    id: 'portrait',
    label: '竖屏短视频',
    kicker: '视频号 / 朋友圈 / 公众号',
    description: '1080x1920，可直接用于视频号、朋友圈和社交转发。',
    src: '/demo/medichatrd_brand_story_portrait_preview.mp4',
    poster: '/demo/medichatrd_brand_story_portrait_poster.jpg',
    downloadName: 'medichatrd-brand-story-portrait.mp4',
  },
};

function StoryStat({ label, value, tone = 'warm' }) {
  return (
    <div className={`cinematic-demo-stat tone-${tone}`}>
      <small>{label}</small>
      <strong>{value}</strong>
    </div>
  );
}

function StoryActionButton({ action, variant = 'primary', onAction }) {
  if (!action) return null;
  return (
    <button
      type="button"
      className={`cinematic-demo-btn ${variant}`}
      onClick={() => onAction(action)}
    >
      {action.label}
    </button>
  );
}

function StoryVariantButton({ option, active, onClick }) {
  return (
    <button
      type="button"
      className={`cinematic-variant-chip ${active ? 'active' : ''}`}
      onClick={() => onClick(option.id)}
    >
      <small>{option.kicker}</small>
      <strong>{option.label}</strong>
      <span>{option.description}</span>
    </button>
  );
}

function downloadFile(url, filename) {
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
}

export default function CinematicDemoSection({
  onNavigate,
  onOpenWelcomeRoom,
  onOpenVoiceFollowup,
}) {
  const [activeIndex, setActiveIndex] = useState(0);
  const [variantId, setVariantId] = useState('landscape');
  const [statusMessage, setStatusMessage] = useState('首页已切到新版品牌片预览。');
  const videoRef = useRef(null);

  const activeScene = useMemo(() => STORY_SCENES[activeIndex], [activeIndex]);
  const activeVariant = PREVIEW_VARIANTS[variantId];

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;
    video.load();
    const playPromise = video.play();
    if (playPromise && typeof playPromise.catch === 'function') {
      playPromise.catch(() => {});
    }
  }, [variantId]);

  const handleAction = (action) => {
    if (!action) return;
    if (action.kind === 'page') {
      onNavigate?.(action.target);
      return;
    }
    if (action.kind === 'welcome') {
      onOpenWelcomeRoom?.({ id: 'room_newcomer' });
      return;
    }
    if (action.kind === 'voice') {
      onOpenVoiceFollowup?.();
    }
  };

  const jumpToScene = (index) => {
    const scene = STORY_SCENES[index];
    setActiveIndex(index);
    const video = videoRef.current;
    if (video && scene) {
      video.currentTime = scene.startSec ?? 0;
      const playPromise = video.play();
      if (playPromise && typeof playPromise.catch === 'function') {
        playPromise.catch(() => {});
      }
    }
  };

  const handleTimeUpdate = () => {
    const video = videoRef.current;
    if (!video) return;
    const time = video.currentTime;
    const nextIndex = STORY_SCENES.findIndex((scene, index) => {
      const start = scene.startSec ?? 0;
      const end = scene.endSec ?? (STORY_SCENES[index + 1]?.startSec ?? Number.POSITIVE_INFINITY);
      return time >= start && time < end;
    });
    if (nextIndex >= 0 && nextIndex !== activeIndex) {
      setActiveIndex(nextIndex);
    }
  };

  const handleDownloadCurrent = () => {
    downloadFile(activeVariant.src, activeVariant.downloadName);
    setStatusMessage(`已准备下载${activeVariant.label}。`);
  };

  const handleDownloadStoryboard = () => {
    const payload = {
      generatedAt: new Date().toISOString(),
      variants: Object.values(PREVIEW_VARIANTS).map(({ id, label, kicker }) => ({ id, label, kicker })),
      scenes: STORY_SCENES.map((scene) => ({
        chapter: scene.chapter,
        label: scene.label,
        title: scene.title,
        summary: scene.summary,
        voice: scene.voice,
        startSec: scene.startSec,
        endSec: scene.endSec,
      })),
    };
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    downloadFile(url, 'medichatrd-brand-storyboard.json');
    URL.revokeObjectURL(url);
    setStatusMessage('分镜脚本已下载。');
  };

  return (
    <section className="cinematic-demo-section">
      <div className="cinematic-demo-copy">
        <div className="cinematic-demo-kicker">Brand film demo</div>
        <h2>把首页 demo 直接升级成品牌宣传片，横屏讲故事，竖屏可以直接发。</h2>
        <p>
          这块现在不是旧版导出器，而是已经换成新版品牌片预览。首页里直接看得到真实成片，
          横屏用于官网和路演，竖屏用于视频号、朋友圈和公众号。
        </p>

        <div className="cinematic-demo-meta">
          <StoryStat label="叙事节奏" value="更像真人品牌旁白" tone="warm" />
          <StoryStat label="竖屏规格" value="1080 × 1920" tone="mint" />
          <StoryStat label="当前状态" value="主页已切到新版成片" tone="sky" />
        </div>

        <div className="cinematic-demo-variant-grid">
          {Object.values(PREVIEW_VARIANTS).map((option) => (
            <StoryVariantButton
              key={option.id}
              option={option}
              active={variantId === option.id}
              onClick={(nextId) => {
                setVariantId(nextId);
                setStatusMessage(`已切换到${PREVIEW_VARIANTS[nextId].label}。`);
              }}
            />
          ))}
        </div>

        <div className="cinematic-demo-storyline">
          <span className="cinematic-demo-chapter">Chapter {activeScene.chapter}</span>
          <strong>{activeScene.kicker}</strong>
          <h3>{activeScene.title}</h3>
          <p>{activeScene.summary}</p>
          <blockquote>{activeScene.voice}</blockquote>
        </div>

        <div className="cinematic-demo-tags">
          {activeScene.tags.map((tag) => (
            <span key={tag}>{tag}</span>
          ))}
        </div>

        <div className="cinematic-demo-actions">
          <StoryActionButton action={activeScene.cta} onAction={handleAction} />
          <StoryActionButton action={activeScene.secondaryCta} variant="ghost" onAction={handleAction} />
        </div>
      </div>

      <div className="cinematic-demo-stage">
        <div className={`cinematic-demo-frame video-mode ${variantId}`}>
          <div className="cinematic-demo-frame-bar">
            <div className="cinematic-demo-frame-badge">
              <span className="record-dot" />
              <strong>{activeVariant.label}</strong>
            </div>
            <span>{activeVariant.description}</span>
          </div>

          <div className="cinematic-video-shell">
            <video
              ref={videoRef}
              className={`cinematic-demo-video ${variantId}`}
              src={activeVariant.src}
              poster={activeVariant.poster}
              controls
              autoPlay
              muted
              loop
              playsInline
              preload="metadata"
              onTimeUpdate={handleTimeUpdate}
            />
          </div>
        </div>

        <div className="cinematic-demo-stage-controls">
          <button
            type="button"
            className="cinematic-demo-btn primary"
            onClick={handleDownloadCurrent}
          >
            下载当前版本 MP4
          </button>
          <button
            type="button"
            className="cinematic-demo-btn ghost"
            onClick={handleDownloadStoryboard}
          >
            下载分镜脚本 JSON
          </button>
        </div>

        {statusMessage && <div className="cinematic-demo-export-note">{statusMessage}</div>}

        <div className="cinematic-demo-rail">
          {STORY_SCENES.map((scene, index) => (
            <button
              key={scene.id}
              type="button"
              className={`cinematic-demo-rail-item ${index === activeIndex ? 'active' : ''}`}
              onClick={() => jumpToScene(index)}
            >
              <small>{scene.chapter}</small>
              <strong>{scene.label}</strong>
              <span>{scene.kicker}</span>
            </button>
          ))}
        </div>
      </div>
    </section>
  );
}
