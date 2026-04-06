export const CINEMATIC_SCENE_DURATION_MS = 5200;
export const CINEMATIC_SCENE_TRANSITION_MS = 560;
export const CINEMATIC_EXPORT_FPS = 24;
export const CINEMATIC_EXPORT_WIDTH = 1280;
export const CINEMATIC_EXPORT_HEIGHT = 720;

export const STORY_SCENES = [
  {
    id: 'welcome',
    chapter: '01',
    label: '新确诊的夜晚',
    title: '先让一个家庭被接住，再让产品开始工作',
    summary:
      '妈妈抱着孩子和一摞检查单，最先需要的不是更多术语，而是一个愿意慢下来、陪她把病历和情绪放进同一条线里的入口。',
    voice:
      '“今晚不用把所有结果都看懂，我们先把最重要的症状、检查和情绪整理出来，明天就不会再乱。”',
    tags: ['欢迎房', '病历整理', '情绪安放'],
    kicker: '今晚 20:00 · 新确诊患者欢迎房',
    cta: { label: '进入欢迎房', kind: 'welcome' },
    secondaryCta: { label: '打开患者中枢', kind: 'page', target: 'hub' },
  },
  {
    id: 'hub',
    chapter: '02',
    label: '把慌张变成路径',
    title: '患者中枢把病历、检查和下一步安排成可执行旅程',
    summary:
      '患者不用在多个页面里来回找入口，平台会把今天最该做的事排在眼前，从登记、就诊、到病程整理都能顺着走。',
    voice:
      '“你现在最重要的是先把检查、主要不舒服和想问医生的问题放进同一页里。”',
    tags: ['患者中枢', '旅程总览', '一页进入'],
    kicker: '今天的第一条路径',
    cta: { label: '查看患者中枢', kind: 'page', target: 'hub' },
    secondaryCta: { label: '去做症状筛查', kind: 'page', target: 'symptom-check' },
  },
  {
    id: 'deeprare',
    chapter: '03',
    label: '诊断不再散乱',
    title: 'DeepRare 把零散描述整理成候选诊断和下一步检查',
    summary:
      '患者只要讲出自己的感受，系统就能把症状、HPO 表型、候选疾病和建议检查放成一条看得懂的推理链。',
    voice:
      '“先把孩子最近三个月最明显的变化说出来，我来帮你把症状翻译成医生能直接继续用的信息。”',
    tags: ['DeepRare', 'HPO 表型', '检查建议'],
    kicker: 'DeepRare 诊断工作台',
    cta: { label: '打开 DeepRare', kind: 'page', target: 'deeprare' },
    secondaryCta: { label: '查看疾病研究', kind: 'page', target: 'disease-research' },
  },
  {
    id: 'avatar',
    chapter: '04',
    label: '让分身替你开口',
    title: 'SecondMe 分身把患者身份、病程和第一条动态连接在一起',
    summary:
      '授权、建分身、写第一条动态，平台会帮患者先把“我是谁、我现在最需要什么帮助”说得更真、更稳。',
    voice:
      '“我不是来发一段标准答案，我只是想问问，有没有人也经历过同样的骨痛和检查等待。”',
    tags: ['SecondMe', 'AI 分身', '首条动态'],
    kicker: '人格卡与首帖草稿',
    cta: { label: '去创建分身', kind: 'page', target: 'community' },
    secondaryCta: { label: '连接 SecondMe', kind: 'page', target: 'platform-ops' },
  },
  {
    id: 'community',
    chapter: '05',
    label: '让病友真正说上话',
    title: '欢迎房、家长圆桌和试验追踪，把支持、经验和机会聚到一个现场',
    summary:
      '患者和家属可以从欢迎房走进病友圈，从提问走向回应，再从回应走到临床试验和长期支持。',
    voice:
      '“有人真的回我了，也有人告诉我检查前一天怎么准备，感觉终于不是自己一个人了。”',
    tags: ['病友圈', 'Live rooms', '临床试验机会'],
    kicker: '公开社群现场',
    cta: { label: '进入互助社群', kind: 'page', target: 'community' },
    secondaryCta: { label: '查看药物线索', kind: 'page', target: 'drug-research' },
  },
  {
    id: 'followup',
    chapter: '06',
    label: '陪伴留到日常里',
    title: '陪伴玩偶和语音随访设备，让长期管理变得更温柔',
    summary:
      '孩子可以和玩偶说今天哪里不舒服，家属可以用语音随访盒记录变化，平台则把这些细碎的感受接回长期管理。',
    voice:
      '“它每天都提醒我说一句今天的感受，原来随访也可以不是一件压抑的事情。”',
    tags: ['陪伴硬件', '语音随访', '长期管理'],
    kicker: '陪伴与随访闭环',
    cta: { label: '打开长期管理', kind: 'page', target: 'care-loop' },
    secondaryCta: { label: '体验语音陪诊', kind: 'voice' },
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
