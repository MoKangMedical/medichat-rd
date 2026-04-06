import {
  CINEMATIC_SCENE_DURATION_MS,
  CINEMATIC_SCENE_TRANSITION_MS,
  CINEMATIC_TOTAL_DURATION_MS,
  STORY_SCENES,
  getStorySceneAtTime,
} from './cinematicDemoStoryboard.js';

function roundRect(ctx, x, y, width, height, radius, fillStyle, strokeStyle = null, lineWidth = 1) {
  ctx.beginPath();
  ctx.moveTo(x + radius, y);
  ctx.arcTo(x + width, y, x + width, y + height, radius);
  ctx.arcTo(x + width, y + height, x, y + height, radius);
  ctx.arcTo(x, y + height, x, y, radius);
  ctx.arcTo(x, y, x + width, y, radius);
  if (fillStyle) {
    ctx.fillStyle = fillStyle;
    ctx.fill();
  }
  if (strokeStyle) {
    ctx.strokeStyle = strokeStyle;
    ctx.lineWidth = lineWidth;
    ctx.stroke();
  }
}

function drawTextBlock(ctx, lines, x, y, options = {}) {
  const {
    color = '#0c1831',
    font = '600 24px "Noto Sans SC", sans-serif',
    lineHeight = 34,
    maxWidth = 500,
    align = 'left',
  } = options;
  ctx.save();
  ctx.fillStyle = color;
  ctx.font = font;
  ctx.textAlign = align;
  ctx.textBaseline = 'top';
  lines.forEach((line, index) => {
    ctx.fillText(line, x, y + index * lineHeight, maxWidth);
  });
  ctx.restore();
}

function fitLines(ctx, text, maxWidth, maxLines = 3) {
  const words = text.split('');
  const lines = [];
  let current = '';
  words.forEach((char) => {
    const trial = current + char;
    if (ctx.measureText(trial).width > maxWidth && current) {
      lines.push(current);
      current = char;
    } else {
      current = trial;
    }
  });
  if (current) lines.push(current);
  if (lines.length <= maxLines) return lines;
  return [...lines.slice(0, maxLines - 1), `${lines[maxLines - 1].slice(0, Math.max(0, lines[maxLines - 1].length - 2))}…`];
}

function drawPill(ctx, text, x, y, background, color) {
  ctx.save();
  ctx.font = '700 18px "Noto Sans SC", sans-serif';
  const width = ctx.measureText(text).width + 28;
  roundRect(ctx, x, y, width, 34, 17, background, 'rgba(12,24,49,0.08)');
  ctx.fillStyle = color;
  ctx.textBaseline = 'middle';
  ctx.fillText(text, x + 14, y + 17);
  ctx.restore();
  return width;
}

function drawGlassCard(ctx, x, y, width, height, title, subtitle, accent) {
  roundRect(ctx, x, y, width, height, 24, 'rgba(255,255,255,0.82)', 'rgba(12,24,49,0.08)');
  ctx.fillStyle = accent;
  ctx.fillRect(x, y, 6, height);
  ctx.fillStyle = '#7d879a';
  ctx.font = '800 14px "Manrope", "Noto Sans SC", sans-serif';
  ctx.fillText(title, x + 20, y + 24);
  ctx.fillStyle = '#0c1831';
  ctx.font = '800 26px "Manrope", "Noto Sans SC", sans-serif';
  const lines = fitLines(ctx, subtitle, width - 40, 2);
  drawTextBlock(ctx, lines, x + 20, y + 40, {
    color: '#0c1831',
    font: '800 26px "Manrope", "Noto Sans SC", sans-serif',
    lineHeight: 32,
    maxWidth: width - 40,
  });
}

function drawBackground(ctx, width, height, sceneId, time) {
  const gradients = {
    welcome: ['#fff0e5', '#fde7e1', '#f8f0ff'],
    hub: ['#fff7e8', '#eef6ff', '#e7fff8'],
    deeprare: ['#f2f7ff', '#eefcff', '#fff6ea'],
    avatar: ['#fff4ec', '#f4f1ff', '#effcff'],
    community: ['#fff7ea', '#f0fcff', '#eef6ff'],
    followup: ['#fff7ef', '#f7f2ff', '#efffff'],
  };
  const colors = gradients[sceneId] || gradients.welcome;
  const gradient = ctx.createLinearGradient(0, 0, 0, height);
  gradient.addColorStop(0, colors[0]);
  gradient.addColorStop(0.5, colors[1]);
  gradient.addColorStop(1, colors[2]);
  ctx.fillStyle = gradient;
  ctx.fillRect(0, 0, width, height);

  const glowA = ctx.createRadialGradient(width * 0.16, height * 0.18, 20, width * 0.16, height * 0.18, 240);
  glowA.addColorStop(0, 'rgba(255, 208, 112, 0.42)');
  glowA.addColorStop(1, 'rgba(255, 208, 112, 0)');
  ctx.fillStyle = glowA;
  ctx.fillRect(0, 0, width, height);

  const glowB = ctx.createRadialGradient(width * 0.82, height * 0.2, 20, width * 0.82, height * 0.2, 220);
  glowB.addColorStop(0, 'rgba(76, 125, 255, 0.28)');
  glowB.addColorStop(1, 'rgba(76, 125, 255, 0)');
  ctx.fillStyle = glowB;
  ctx.fillRect(0, 0, width, height);

  const drift = Math.sin(time / 1400) * 12;
  ctx.fillStyle = 'rgba(255,255,255,0.45)';
  roundRect(ctx, 92 + drift, 88, 140, 38, 19, 'rgba(255,255,255,0.56)');
  roundRect(ctx, width - 280 - drift, 112, 130, 34, 17, 'rgba(255,255,255,0.5)');
}

function drawHeaderOverlay(ctx, width, scene) {
  roundRect(ctx, 36, 28, 390, 86, 24, 'rgba(255,255,255,0.78)', 'rgba(12,24,49,0.08)');
  ctx.fillStyle = '#7d879a';
  ctx.font = '800 14px "Manrope", "Noto Sans SC", sans-serif';
  ctx.fillText(scene.kicker, 56, 56);
  const titleLines = fitLines(ctx, scene.title, 330, 2);
  drawTextBlock(ctx, titleLines, 56, 68, {
    color: '#0c1831',
    font: '800 26px "Manrope", "Noto Sans SC", sans-serif',
    lineHeight: 30,
    maxWidth: 330,
  });
}

function drawWelcomeScene(ctx, width, height, time) {
  const bob = Math.sin(time / 520) * 8;
  ctx.fillStyle = 'rgba(255,196,116,0.2)';
  ctx.beginPath();
  ctx.arc(width - 170, 130 + bob * 0.3, 52, 0, Math.PI * 2);
  ctx.fill();
  ctx.fillStyle = '#ffe4a6';
  ctx.beginPath();
  ctx.arc(width - 170, 130 + bob * 0.3, 44, 0, Math.PI * 2);
  ctx.fill();
  ['#fff9df', '#fff1bf', '#fff9df'].forEach((color, index) => {
    ctx.fillStyle = color;
    ctx.beginPath();
    const sx = width - 260 + index * 50;
    const sy = 90 + (index % 2) * 34;
    ctx.arc(sx, sy, 4 + index, 0, Math.PI * 2);
    ctx.fill();
  });

  const baseY = height - 170;
  ctx.fillStyle = '#ffddb7';
  ctx.beginPath();
  ctx.arc(170, baseY - 110 + bob * 0.25, 26, 0, Math.PI * 2);
  ctx.fill();
  roundRect(ctx, 124, baseY - 90, 92, 148, 46, '#ff7a59');

  ctx.beginPath();
  ctx.arc(256, baseY - 92 - bob * 0.2, 20, 0, Math.PI * 2);
  ctx.fillStyle = '#ffddb7';
  ctx.fill();
  roundRect(ctx, 224, baseY - 76, 64, 112, 30, '#4c7dff');

  roundRect(ctx, 306, baseY - 10 + bob * 0.3, 78, 98, 34, '#ffb258');
  ctx.beginPath();
  ctx.arc(328, baseY - 18 + bob * 0.3, 12, 0, Math.PI * 2);
  ctx.arc(362, baseY - 18 + bob * 0.3, 12, 0, Math.PI * 2);
  ctx.fillStyle = '#ffb258';
  ctx.fill();

  drawGlassCard(ctx, width - 350, 170, 280, 120, '新确诊患者欢迎房', '病历清单 + 情绪支持 + 下一步提醒', '#ff7a59');
  roundRect(ctx, width - 330, height - 250, 240, 72, 24, 'rgba(255,255,255,0.9)', 'rgba(12,24,49,0.08)');
  drawTextBlock(ctx, ['先整理病历、检查和情绪'], width - 308, height - 226, {
    color: '#0c1831',
    font: '700 22px "Noto Sans SC", sans-serif',
    lineHeight: 28,
    maxWidth: 200,
  });
  roundRect(ctx, 52, height - 108, 300, 64, 22, 'rgba(255,255,255,0.84)', 'rgba(12,24,49,0.08)');
  drawTextBlock(ctx, ['把今晚最乱的几件事，先放进一条线里'], 72, height - 88, {
    color: '#44506a',
    font: '600 20px "Noto Sans SC", sans-serif',
    lineHeight: 26,
    maxWidth: 260,
  });
}

function drawHubScene(ctx, width, height, time) {
  roundRect(ctx, 86, 152, width - 172, height - 214, 32, 'rgba(255,255,255,0.78)', 'rgba(12,24,49,0.08)');
  ['#ff7a59', '#0dbf9b', '#ffd16f'].forEach((color, index) => {
    ctx.fillStyle = color;
    ctx.beginPath();
    ctx.arc(122 + index * 18, 182, 5, 0, Math.PI * 2);
    ctx.fill();
  });
  drawGlassCard(ctx, 118, 216, 360, 176, '今天的患者旅程', '病历整理 · 症状结构化 · 病友支持入口', '#0dbf9b');
  drawGlassCard(ctx, 498, 216, 300, 176, '检查与病程', '骨痛加重 · 脾大/贫血 · 待确认基因', '#4c7dff');
  drawGlassCard(ctx, 118, 412, 680, 94, '今天最重要', '先把问医生的 3 个问题写下来，明天进入就诊时就不会再乱。', '#ffd16f');
  roundRect(ctx, width - 290, height - 118 + Math.sin(time / 680) * 4, 230, 62, 22, 'rgba(255,255,255,0.86)', 'rgba(12,24,49,0.08)');
  drawTextBlock(ctx, ['患者中枢把多个入口收成一页'], width - 266, height - 98 + Math.sin(time / 680) * 4, {
    color: '#44506a',
    font: '700 19px "Noto Sans SC", sans-serif',
    lineHeight: 24,
    maxWidth: 192,
  });
}

function drawDeepRareScene(ctx, width, height, time) {
  roundRect(ctx, 120, 160, width - 240, height - 240, 34, '#0d1830');
  ctx.fillStyle = 'rgba(255,255,255,0.82)';
  ctx.font = '700 17px "Manrope", "Noto Sans SC", sans-serif';
  ctx.fillText('DeepRare AI', 148, 190);
  ctx.fillStyle = '#0dbf9b';
  ctx.beginPath();
  ctx.arc(width - 158, 186, 7 + Math.sin(time / 220) * 1.6, 0, Math.PI * 2);
  ctx.fill();
  ['脾大', '骨痛', '贫血', '乏力'].forEach((text, index) => {
    drawPill(ctx, text, 148 + index * 118, 224, 'rgba(255,255,255,0.1)', '#ffffff');
  });
  drawGlassCard(ctx, 148, 282, 300, 118, '首位候选', '戈谢病 · GBA · 溶酶体病', '#0dbf9b');
  drawGlassCard(ctx, 472, 282, 300, 118, '鉴别诊断', '法布雷病 · GLA · 继续排查', '#4c7dff');
  roundRect(ctx, 148, 426, 624, 92, 24, 'rgba(255,255,255,0.1)', 'rgba(255,255,255,0.08)');
  drawTextBlock(ctx, ['HPO', '脾肿大 / 骨痛 / 血红蛋白下降'], 176, 450, {
    color: '#ffffff',
    font: '700 18px "Noto Sans SC", sans-serif',
    lineHeight: 28,
    maxWidth: 580,
  });
  roundRect(ctx, width - 320, height - 108, 250, 66, 22, 'rgba(255,255,255,0.9)', 'rgba(12,24,49,0.08)');
  drawTextBlock(ctx, ['从自然语言到候选诊断和检查建议'], width - 296, height - 88, {
    color: '#0c1831',
    font: '700 20px "Noto Sans SC", sans-serif',
    lineHeight: 26,
    maxWidth: 210,
  });
}

function drawAvatarScene(ctx, width, height, time) {
  const cx = 274;
  const cy = 344;
  ctx.save();
  ctx.translate(cx, cy);
  ctx.rotate(time / 3200);
  ctx.strokeStyle = 'rgba(12,24,49,0.16)';
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.ellipse(0, 0, 132, 116, 0.4, 0, Math.PI * 2);
  ctx.stroke();
  ctx.rotate(-time / 2200);
  ctx.setLineDash([10, 10]);
  ctx.beginPath();
  ctx.ellipse(0, 0, 96, 84, -0.24, 0, Math.PI * 2);
  ctx.stroke();
  ctx.setLineDash([]);
  ctx.restore();
  const coreGradient = ctx.createRadialGradient(cx - 20, cy - 28, 10, cx, cy, 88);
  coreGradient.addColorStop(0, '#ffffff');
  coreGradient.addColorStop(1, '#ffb58c');
  ctx.fillStyle = coreGradient;
  ctx.beginPath();
  ctx.arc(cx, cy, 76, 0, Math.PI * 2);
  ctx.fill();
  drawTextBlock(ctx, ['SecondMe', '患者分身'], cx - 44, cy - 24, {
    color: '#0c1831',
    font: '800 20px "Manrope", "Noto Sans SC", sans-serif',
    lineHeight: 26,
    maxWidth: 90,
    align: 'center',
  });
  drawGlassCard(ctx, width - 350, 178, 280, 124, '分身资料卡', '小羽 · 戈谢病 · 想先找到相似骨痛经历的病友', '#ff7a59');
  drawGlassCard(ctx, width - 380, height - 194, 320, 120, '首条动态草稿', '有没有人在等基因结果时，也这样焦虑过？', '#7a5af8');
}

function drawCommunityScene(ctx, width, height, time) {
  roundRect(ctx, 132, 182, 260, 186, 28, 'rgba(255,238,229,0.92)', 'rgba(12,24,49,0.08)');
  roundRect(ctx, 420, 182, 260, 186, 28, 'rgba(231,255,247,0.92)', 'rgba(12,24,49,0.08)');
  roundRect(ctx, 708, 182, 260, 186, 28, 'rgba(235,242,255,0.92)', 'rgba(12,24,49,0.08)');
  drawTextBlock(ctx, ['欢迎房', '第一周先整理病历和情绪'], 160, 240, {
    color: '#0c1831',
    font: '800 28px "Manrope", "Noto Sans SC", sans-serif',
    lineHeight: 34,
    maxWidth: 210,
  });
  drawTextBlock(ctx, ['家长圆桌', '营养、学校和长期依从性'], 448, 240, {
    color: '#0c1831',
    font: '800 28px "Manrope", "Noto Sans SC", sans-serif',
    lineHeight: 34,
    maxWidth: 210,
  });
  drawTextBlock(ctx, ['临床试验机会', '新药动态与入组准备'], 736, 240, {
    color: '#0c1831',
    font: '800 28px "Manrope", "Noto Sans SC", sans-serif',
    lineHeight: 34,
    maxWidth: 210,
  });
  drawPill(ctx, 'Live rooms', 136, 134, 'rgba(255,255,255,0.86)', '#ff7a59');
  const pulse = 1 + Math.sin(time / 400) * 0.08;
  [[390, 370], [640, 340], [872, 380]].forEach(([x, y], index) => {
    ctx.fillStyle = '#ffffff';
    ctx.beginPath();
    ctx.arc(x, y, 10 * pulse, 0, Math.PI * 2);
    ctx.fill();
    ctx.strokeStyle = 'rgba(12,24,49,0.12)';
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(x, y);
    const next = [[640, 340], [872, 380], [640, 340]][index];
    ctx.lineTo(next[0], next[1]);
    ctx.strokeStyle = 'rgba(12,24,49,0.12)';
    ctx.stroke();
  });
}

function drawFollowupScene(ctx, width, height, time) {
  const bob = Math.sin(time / 600) * 6;
  const toyColors = ['#ffb061', '#ff9bc2', '#ff7a59'];
  [0, 1, 2].forEach((index) => {
    const x = 140 + index * 116;
    const y = height - 200 + bob * (index === 1 ? -0.5 : 1);
    roundRect(ctx, x, y, 86, 112, 40, toyColors[index]);
    ctx.beginPath();
    ctx.arc(x + 22, y - 12, 12, 0, Math.PI * 2);
    ctx.arc(x + 64, y - 12, 12, 0, Math.PI * 2);
    ctx.fillStyle = toyColors[index];
    ctx.fill();
  });
  roundRect(ctx, width - 370, 164, 280, 320, 34, 'rgba(255,255,255,0.84)', 'rgba(12,24,49,0.08)');
  roundRect(ctx, width - 344, 194, 228, 124, 26, '#173a68');
  drawTextBlock(ctx, ['语音随访中', '今天哪里不舒服？'], width - 318, 224, {
    color: '#ffffff',
    font: '800 22px "Manrope", "Noto Sans SC", sans-serif',
    lineHeight: 30,
    maxWidth: 180,
  });
  [0, 1].forEach((index) => {
    ctx.beginPath();
    ctx.arc(width - 230, 404, 66 + index * 28 + Math.sin(time / 600 + index) * 4, 0, Math.PI * 2);
    ctx.strokeStyle = `rgba(76,125,255,${0.18 - index * 0.06})`;
    ctx.lineWidth = 2;
    ctx.stroke();
  });
  roundRect(ctx, 78, height - 110, width - 156, 68, 22, 'rgba(255,255,255,0.86)', 'rgba(12,24,49,0.08)');
  ['每日打卡', '复诊提醒', '长期管理'].forEach((item, index) => {
    drawTextBlock(ctx, [item], 122 + index * 280, height - 88, {
      color: '#0c1831',
      font: '700 20px "Noto Sans SC", sans-serif',
      lineHeight: 24,
      maxWidth: 180,
    });
  });
}

function drawFooterStrip(ctx, width, scene) {
  roundRect(ctx, 34, 632, width - 68, 54, 20, 'rgba(255,255,255,0.78)', 'rgba(12,24,49,0.08)');
  let cursor = 56;
  scene.tags.forEach((tag, index) => {
    cursor += drawPill(ctx, tag, cursor, 642, index % 2 === 0 ? 'rgba(255,255,255,0.92)' : 'rgba(241,247,255,0.92)', '#0c1831') + 10;
  });
}

export function drawCinematicFrame(ctx, width, height, timeMs) {
  ctx.clearRect(0, 0, width, height);
  const { scene, sceneTime, progress } = getStorySceneAtTime(timeMs);
  drawBackground(ctx, width, height, scene.id, timeMs);

  switch (scene.id) {
    case 'welcome':
      drawWelcomeScene(ctx, width, height, sceneTime);
      break;
    case 'hub':
      drawHubScene(ctx, width, height, sceneTime);
      break;
    case 'deeprare':
      drawDeepRareScene(ctx, width, height, sceneTime);
      break;
    case 'avatar':
      drawAvatarScene(ctx, width, height, sceneTime);
      break;
    case 'community':
      drawCommunityScene(ctx, width, height, sceneTime);
      break;
    case 'followup':
      drawFollowupScene(ctx, width, height, sceneTime);
      break;
    default:
      break;
  }

  drawHeaderOverlay(ctx, width, scene);
  drawFooterStrip(ctx, width, scene);

  const transitionAlpha = Math.min(1, sceneTime / CINEMATIC_SCENE_TRANSITION_MS, (CINEMATIC_SCENE_DURATION_MS - sceneTime) / CINEMATIC_SCENE_TRANSITION_MS);
  ctx.fillStyle = `rgba(255,255,255,${0.08 * (1 - Math.max(0, transitionAlpha))})`;
  ctx.fillRect(0, 0, width, height);

  roundRect(ctx, width - 214, 36, 162, 44, 18, 'rgba(12,24,49,0.82)');
  drawTextBlock(ctx, [`${scene.chapter} / ${STORY_SCENES.length}`, `${Math.round(progress * 100)}%`], width - 188, 48, {
    color: '#ffffff',
    font: '700 16px "Manrope", "Noto Sans SC", sans-serif',
    lineHeight: 18,
    maxWidth: 120,
  });
}

export async function exportCinematicWebM(onProgress) {
  if (typeof window === 'undefined' || typeof MediaRecorder === 'undefined') {
    throw new Error('当前浏览器不支持视频导出');
  }

  const canvas = document.createElement('canvas');
  canvas.width = 1280;
  canvas.height = 720;
  const ctx = canvas.getContext('2d');
  if (!ctx) {
    throw new Error('无法创建视频画布');
  }

  const chunks = [];
  const stream = canvas.captureStream(24);
  const mimeType = MediaRecorder.isTypeSupported('video/webm;codecs=vp9')
    ? 'video/webm;codecs=vp9'
    : 'video/webm';
  const recorder = new MediaRecorder(stream, { mimeType });

  recorder.ondataavailable = (event) => {
    if (event.data && event.data.size > 0) chunks.push(event.data);
  };

  const startedAt = performance.now();
  const duration = CINEMATIC_TOTAL_DURATION_MS;
  recorder.start();

  await new Promise((resolve) => {
    function renderFrame(now) {
      const elapsed = now - startedAt;
      const safeElapsed = Math.min(elapsed, duration);
      drawCinematicFrame(ctx, canvas.width, canvas.height, safeElapsed);
      onProgress?.(safeElapsed / duration);
      if (safeElapsed < duration) {
        window.requestAnimationFrame(renderFrame);
      } else {
        recorder.onstop = resolve;
        recorder.stop();
      }
    }
    window.requestAnimationFrame(renderFrame);
  });

  return new Blob(chunks, { type: mimeType });
}

export function createCinematicStoryboardPayload() {
  return {
    title: 'MediChat-RD 首页剧情 Demo',
    durationMs: CINEMATIC_TOTAL_DURATION_MS,
    sceneDurationMs: CINEMATIC_SCENE_DURATION_MS,
    transitionDurationMs: CINEMATIC_SCENE_TRANSITION_MS,
    scenes: STORY_SCENES,
  };
}
