import React, { useEffect, useMemo, useRef, useState } from 'react';
import {
  drawCinematicFrame,
  exportCinematicWebM,
  createCinematicStoryboardPayload,
} from './cinematicVideoRenderer.js';
import {
  CINEMATIC_EXPORT_HEIGHT,
  CINEMATIC_EXPORT_WIDTH,
  CINEMATIC_SCENE_DURATION_MS,
  STORY_SCENES,
  getStorySceneAtTime,
} from './cinematicDemoStoryboard.js';

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

function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}

export default function CinematicDemoSection({
  onNavigate,
  onOpenWelcomeRoom,
  onOpenVoiceFollowup,
}) {
  const [activeIndex, setActiveIndex] = useState(0);
  const [paused, setPaused] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [exportProgress, setExportProgress] = useState(0);
  const [exportMessage, setExportMessage] = useState('');
  const previewCanvasRef = useRef(null);
  const playheadRef = useRef(0);
  const frameRef = useRef(null);
  const lastTickRef = useRef(0);

  const activeScene = useMemo(() => STORY_SCENES[activeIndex], [activeIndex]);

  useEffect(() => {
    const canvas = previewCanvasRef.current;
    if (!canvas) return undefined;
    const ctx = canvas.getContext('2d');
    if (!ctx) return undefined;

    const render = (timestamp) => {
      if (!lastTickRef.current) {
        lastTickRef.current = timestamp;
      }
      const delta = timestamp - lastTickRef.current;
      lastTickRef.current = timestamp;

      if (!paused) {
        playheadRef.current += delta;
      }

      const { index } = getStorySceneAtTime(playheadRef.current);
      if (index !== activeIndex) {
        setActiveIndex(index);
      }

      drawCinematicFrame(ctx, canvas.width, canvas.height, playheadRef.current);
      frameRef.current = window.requestAnimationFrame(render);
    };

    frameRef.current = window.requestAnimationFrame(render);
    return () => {
      if (frameRef.current) {
        window.cancelAnimationFrame(frameRef.current);
      }
    };
  }, [activeIndex, paused]);

  const jumpToScene = (index) => {
    playheadRef.current = index * CINEMATIC_SCENE_DURATION_MS;
    setActiveIndex(index);
  };

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

  const handleExportWebM = async () => {
    if (exporting) return;
    setExporting(true);
    setExportProgress(0);
    setExportMessage('正在渲染 WebM 成片...');
    try {
      const blob = await exportCinematicWebM((progress) => setExportProgress(progress));
      downloadBlob(blob, 'medichatrd-homepage-demo.webm');
      setExportMessage('WebM 成片已导出。');
    } catch (error) {
      console.error(error);
      setExportMessage(error.message || '导出失败');
    } finally {
      setExporting(false);
    }
  };

  const handleExportStoryboard = () => {
    const payload = createCinematicStoryboardPayload();
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
    downloadBlob(blob, 'medichatrd-homepage-demo.storyboard.json');
    setExportMessage('分镜脚本已下载。');
  };

  return (
    <section className="cinematic-demo-section">
      <div className="cinematic-demo-copy">
        <div className="cinematic-demo-kicker">Homepage demo film</div>
        <h2>把首页剧情直接做成可导出的成片，患者看见什么，导出的就是什么</h2>
        <p>
          这段 demo 现在已经是可导出的剧情短片。首页里看到的是实时预览，同一套画布还能直接导出成 WebM，
          后续只需要继续加配音、真人素材或品牌字幕，就能做成对外展示用的正式成片。
        </p>

        <div className="cinematic-demo-meta">
          <StoryStat label="故事章节" value={`${STORY_SCENES.length} 段`} tone="warm" />
          <StoryStat label="输出格式" value="WebM 成片 + JSON 分镜" tone="mint" />
          <StoryStat label="后续可扩展" value="配音 / 转场 / 素材替换" tone="sky" />
        </div>

        <div className="cinematic-demo-storyline">
          <span className="cinematic-demo-chapter">Chapter {activeScene.chapter}</span>
          <strong>{activeScene.label}</strong>
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

      <div
        className="cinematic-demo-stage"
        onMouseEnter={() => setPaused(true)}
        onMouseLeave={() => setPaused(false)}
      >
        <div className="cinematic-demo-frame">
          <div className="cinematic-demo-frame-bar">
            <div className="cinematic-demo-frame-badge">
              <span className="record-dot" />
              <strong>首页剧情 Demo</strong>
            </div>
            <span>{exporting ? `导出中 ${Math.round(exportProgress * 100)}%` : paused ? '已暂停 · 可逐段查看' : '自动播放中'}</span>
          </div>

          <div className="cinematic-demo-progress">
            {STORY_SCENES.map((scene, index) => (
              <button
                key={scene.id}
                type="button"
                className={`cinematic-progress-segment ${index === activeIndex ? 'active' : index < activeIndex ? 'past' : ''}`}
                onClick={() => jumpToScene(index)}
                aria-label={`切换到${scene.label}`}
              />
            ))}
          </div>

          <div className={`cinematic-scene-shell scene-${activeScene.id}`}>
            <canvas
              ref={previewCanvasRef}
              className="cinematic-demo-canvas"
              width={CINEMATIC_EXPORT_WIDTH}
              height={CINEMATIC_EXPORT_HEIGHT}
            />
          </div>
        </div>

        <div className="cinematic-demo-stage-controls">
          <button
            type="button"
            className="cinematic-demo-btn primary"
            onClick={handleExportWebM}
            disabled={exporting}
          >
            {exporting ? '正在导出 WebM 成片…' : '导出 WebM 成片'}
          </button>
          <button
            type="button"
            className="cinematic-demo-btn ghost"
            onClick={handleExportStoryboard}
          >
            下载分镜脚本 JSON
          </button>
        </div>

        {exportMessage && <div className="cinematic-demo-export-note">{exportMessage}</div>}

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
