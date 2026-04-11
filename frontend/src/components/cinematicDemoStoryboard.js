export const CINEMATIC_SCENE_DURATION_MS = 5200;
export const CINEMATIC_SCENE_TRANSITION_MS = 560;
export const CINEMATIC_EXPORT_FPS = 24;
export const CINEMATIC_EXPORT_WIDTH = 1280;
export const CINEMATIC_EXPORT_HEIGHT = 720;

export const STORY_SCENES = [
  {
    id: 'welcome',
    chapter: '01',
    label: '先接住一家人的情绪',
    title: '当一个家庭第一次听见罕见病，最需要的不是更多慌张，而是先被接住。',
    summary:
      'MediChat-RD 先让病历、检查和情绪落到一个温柔的入口里。',
    voice:
      '“当一个家庭第一次听见罕见病，最需要的不是更多慌张，而是先被接住。MediChat-RD 先把病历、检查和情绪，放进一个可以慢慢稳下来的入口里。”',
    tags: ['欢迎房', '病历整理', '情绪安放'],
    kicker: '新确诊患者欢迎房',
    cta: { label: '进入欢迎房', kind: 'welcome' },
    secondaryCta: { label: '打开患者中枢', kind: 'page', target: 'hub' },
    startSec: 0,
    endSec: 15.98,
  },
  {
    id: 'hub',
    chapter: '02',
    label: '把今天最重要的事排好',
    title: '患者中枢把病历、检查、提醒和下一步，整理成一个看得见的旅程。',
    summary:
      '患者和家属终于知道，现在要做什么，接下来又该去哪里。',
    voice:
      '“患者中枢把病历、检查、提醒和下一步，整理成一个看得见的旅程。患者和家属终于知道，现在要做什么，接下来又该去哪里。”',
    tags: ['患者中枢', '旅程总览', '一页进入'],
    kicker: '患者中枢',
    cta: { label: '查看患者中枢', kind: 'page', target: 'hub' },
    secondaryCta: { label: '去做症状筛查', kind: 'page', target: 'symptom-check' },
    startSec: 15.98,
    endSec: 29.08,
  },
  {
    id: 'deeprare',
    chapter: '03',
    label: '让症状真正被读懂',
    title: 'DeepRare 把零散描述变成候选诊断、表型线索和下一步检查建议。',
    summary:
      '从“说不清楚”到“被系统地看见”，诊断路径开始变得清晰。',
    voice:
      '“DeepRare 把零散描述变成候选诊断、表型线索和下一步检查建议。从说不清楚，到被系统地看见，诊断路径开始变得清晰。”',
    tags: ['DeepRare', 'HPO 表型', '检查建议'],
    kicker: 'DeepRare 智能诊断',
    cta: { label: '打开 DeepRare', kind: 'page', target: 'deeprare' },
    secondaryCta: { label: '查看疾病研究', kind: 'page', target: 'disease-research' },
    startSec: 29.08,
    endSec: 40.9,
  },
  {
    id: 'avatar',
    chapter: '04',
    label: '让患者更容易开口',
    title: 'SecondMe 分身把病程、身份和真实需求，变成一句能被理解的话。',
    summary:
      '不是替患者说话，而是帮患者把难以开口的话，说得更稳、更像自己。',
    voice:
      '“SecondMe 分身把病程、身份和真实需求，变成一句能被理解的话。它不是替患者说话，而是帮患者把难以开口的话，说得更稳、更像自己。”',
    tags: ['SecondMe', 'AI 分身', '首条动态'],
    kicker: 'SecondMe 分身',
    cta: { label: '去创建分身', kind: 'page', target: 'community' },
    secondaryCta: { label: '连接 SecondMe', kind: 'page', target: 'platform-ops' },
    startSec: 40.9,
    endSec: 53.68,
  },
  {
    id: 'community',
    chapter: '05',
    label: '让希望在现场流动',
    title: '欢迎房、家长圆桌和试验追踪，把支持、经验和机会聚到一个现场。',
    summary:
      '一个人不再独自面对，病友、家属和研究机会开始真正连接。',
    voice:
      '“欢迎房、家长圆桌和试验追踪，把支持、经验和机会聚到一个现场。一个人不再独自面对，病友、家属和研究机会开始真正连接。”',
    tags: ['病友圈', 'Live rooms', '临床试验机会'],
    kicker: '公开社群现场',
    cta: { label: '进入互助社群', kind: 'page', target: 'community' },
    secondaryCta: { label: '查看药物线索', kind: 'page', target: 'drug-research' },
    startSec: 53.68,
    endSec: 64.86,
  },
  {
    id: 'followup',
    chapter: '06',
    label: '把陪伴留到日常里',
    title: '陪伴玩偶和语音随访设备，让长期管理也能温柔、明亮、持续发生。',
    summary:
      '让长期管理不只是一份压力，也是一种真正被陪伴的生活方式。',
    voice:
      '“陪伴玩偶和语音随访设备，让长期管理也能温柔、明亮、持续发生。让长期管理不只是一份压力，也是一种真正被陪伴的生活方式。”',
    tags: ['陪伴硬件', '语音随访', '长期管理'],
    kicker: '陪伴与随访闭环',
    cta: { label: '打开长期管理', kind: 'page', target: 'care-loop' },
    secondaryCta: { label: '体验语音陪诊', kind: 'voice' },
    startSec: 64.86,
    endSec: 76.68,
  },
];

export const CINEMATIC_TOTAL_DURATION_MS = STORY_SCENES.length * CINEMATIC_SCENE_DURATION_MS;

export function getStorySceneAtTime(timeMs) {
  const safeTime = ((timeMs % CINEMATIC_TOTAL_DURATION_MS) + CINEMATIC_TOTAL_DURATION_MS) % CINEMATIC_TOTAL_DURATION_MS;
  const index = Math.floor(safeTime / CINEMATIC_SCENE_DURATION_MS);
  const scene = STORY_SCENES[index] || STORY_SCENES[0];
  const sceneTime = safeTime - index * CINEMATIC_SCENE_DURATION_MS;
  const progress = sceneTime / CINEMATIC_SCENE_DURATION_MS;
  return { index, scene, sceneTime, progress };
}
