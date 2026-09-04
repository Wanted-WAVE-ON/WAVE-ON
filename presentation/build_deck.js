const pptxgen = require('pptxgenjs');
const {
  imageSizingCrop,
  imageSizingContain,
  safeOuterShadow,
  warnIfSlideHasOverlaps,
  warnIfSlideElementsOutOfBounds,
} = require('/home/oai/skills/slides/pptxgenjs_helpers');
const path = require('path');

const pptx = new pptxgen();
pptx.layout = 'LAYOUT_WIDE';
pptx.author = 'SilentOrchestra 2.0';
pptx.subject = 'Personalized Spatial Agent Hackathon Presentation';
pptx.title = 'SilentOrchestra 2.0 해커톤 발표자료';
pptx.company = 'SilentOrchestra';
pptx.lang = 'ko-KR';
pptx.theme = {
  headFontFace: 'Noto Sans CJK KR',
  bodyFontFace: 'Noto Sans CJK KR',
  lang: 'ko-KR',
};
pptx.defineSlideMaster({
  title: 'MASTER_DARK',
  background: { color: '070A14' },
  objects: [],
  slideNumber: { x: 12.42, y: 7.08, w: 0.45, h: 0.18, fontFace: 'Noto Sans CJK KR', fontSize: 9, color: '5D667B', align: 'right', margin: 0 },
});
const C = {
  bg: '070A14',
  card: '11172A',
  line: '26314D',
  text: 'F5F7FF',
  muted: '9AA4BD',
  muted2: '6E7891',
  cyan: '67DDF2',
  violet: '9C86FF',
  green: '75E6B3',
  amber: 'F2C96D',
  red: 'FF8FA3',
  white: 'FFFFFF',
};
const FONT = 'Noto Sans CJK KR';
const ROOT = path.resolve(__dirname, '..');
const IMG = {
  learning: path.join(ROOT, 'reports', 'ui-preview-learning.png'),
  execution: path.join(ROOT, 'reports', 'ui-preview-execution.png'),
  architecture: path.join(ROOT, 'docs', 'diagrams', 'architecture.png'),
  erd: path.join(ROOT, 'docs', 'diagrams', 'erd.png'),
  loop: path.join(ROOT, 'docs', 'diagrams', 'learning-loop.png'),
};

function addHeader(slide, title, kicker, { accent = C.cyan } = {}) {
  slide.addText(kicker.toUpperCase(), { x: 0.65, y: 0.34, w: 5.7, h: 0.22, fontFace: FONT, fontSize: 9.2, bold: true, charSpacing: 1.6, color: accent, margin: 0, breakLine: false, objectName: 'Section kicker' });
  slide.addText(title, { x: 0.65, y: 0.62, w: 11.9, h: 0.58, fontFace: FONT, fontSize: 26, bold: true, color: C.text, margin: 0, breakLine: false, objectName: 'Slide title' });
  slide.addShape(pptx.ShapeType.line, { x: 0.65, y: 1.28, w: 12.0, h: 0, line: { color: C.line, pt: 1 }, objectName: 'Header divider' });
  slide.addText('SILENTORCHESTRA 2.0', { x: 10.54, y: 0.36, w: 2.12, h: 0.18, fontFace: FONT, fontSize: 8, bold: true, color: C.muted, align: 'right', margin: 0, charSpacing: 1.0, objectName: 'Brand label' });
}

function addFooter(slide, text) {
  slide.addText(text, { x: 0.65, y: 7.05, w: 8.5, h: 0.2, fontFace: FONT, fontSize: 8.5, color: C.muted2, margin: 0, objectName: 'Footer note' });
}

function addPill(slide, text, x, y, w, { fill, color, border, fontSize }) {
  slide.addShape(pptx.ShapeType.roundRect, { x, y, w, h: 0.34, rectRadius: 0.08, fill: { color: fill }, line: { color: border, pt: 1 }, radius: 0.08, objectName: `Pill ${text}` });
  slide.addText(text, { x: x + 0.09, y: y + 0.075, w: w - 0.18, h: 0.17, fontFace: FONT, fontSize, bold: true, color, align: 'center', valign: 'mid', margin: 0, objectName: `Pill label ${text}` });
}

function addCard(slide, x, y, w, h, { fill = C.card, line = C.line, radius = 0.14, shadow = true } = {}) {
  slide.addShape(pptx.ShapeType.roundRect, {
    x, y, w, h,
    rectRadius: radius,
    fill: { color: fill },
    line: { color: line, pt: 1 },
    shadow: shadow ? safeOuterShadow('000000', 0.22, 45, 2, 1) : undefined,
    objectName: 'Card',
  });
}

function addMetric(slide, x, y, w, value, label, accent) {
  slide.addText(value, { x, y, w, h: 0.72, fontFace: FONT, fontSize: 36, bold: true, color: accent, align: 'center', margin: 0, objectName: `Metric ${label}` });
  slide.addText(label, { x, y: y + 0.78, w, h: 0.32, fontFace: FONT, fontSize: 11, bold: true, color: C.text, align: 'center', margin: 0, objectName: `Metric label ${label}` });
  slide.addText('검증 완료', { x, y: y + 1.11, w, h: 0.22, fontFace: FONT, fontSize: 8.6, color: C.muted, align: 'center', margin: 0, objectName: `Metric state ${label}` });
}

function addCheckRow(slide, x, y, text) {
  slide.addText('✓', { x, y: y - 0.005, w: 0.18, h: 0.22, fontFace: FONT, fontSize: 12, bold: true, color: C.green, align: 'center', margin: 0, objectName: 'Check icon' });
  slide.addText(text, { x: x + 0.29, y, w: 4.8, h: 0.24, fontFace: FONT, fontSize: 10.5, color: C.text, margin: 0, breakLine: false, objectName: `Check row ${text}` });
}

function addNotes(slide, script) {
  slide.addNotes(`${script}\n\n[Sources]\n- User-provided SilentOrchestra 2.0 project specification.\n- Local MVP implementation and validation artifacts in this package.`);
}

function addArrow(slide, x, y, w, color, lineWidth) {
  slide.addShape(pptx.ShapeType.line, { x, y, w, h: 0, line: { color, pt: lineWidth, beginArrowType: 'none', endArrowType: 'triangle' }, objectName: 'Flow arrow' });
}

function addStep(slide, x, y, w, num, title, body, accent) {
  addCard(slide, x, y, w, 1.18, { fill: C.card, line: C.line, shadow: false });
  slide.addShape(pptx.ShapeType.ellipse, { x: x + 0.18, y: y + 0.19, w: 0.42, h: 0.42, fill: { color: accent }, line: { color: accent, transparency: 100 }, objectName: `Step ${num} badge` });
  slide.addText(String(num), { x: x + 0.18, y: y + 0.275, w: 0.42, h: 0.18, fontFace: FONT, fontSize: 10, bold: true, color: C.bg, align: 'center', margin: 0, objectName: `Step ${num}` });
  slide.addText(title, { x: x + 0.74, y: y + 0.19, w: w - 0.9, h: 0.27, fontFace: FONT, fontSize: 13, bold: true, color: C.text, margin: 0, objectName: `Step title ${title}` });
  slide.addText(body, { x: x + 0.74, y: y + 0.54, w: w - 0.9, h: 0.44, fontFace: FONT, fontSize: 9.5, color: C.muted, margin: 0, breakLine: false, objectName: `Step body ${title}` });
}

// 1. Cover
{
  const slide = pptx.addSlide({ masterName: 'MASTER_DARK' });
  addPill(slide, 'PERSONALIZED SPATIAL AGENT', 0.72, 0.56, 2.92, { fill: '101A2D', color: C.cyan, border: '26415B', fontSize: 9.2 });
  slide.addText('SilentOrchestra 2.0', { x: 0.72, y: 1.3, w: 6.4, h: 0.72, fontFace: FONT, fontSize: 34, bold: true, color: C.text, margin: 0, objectName: 'Cover title' });
  slide.addText('AI에게 제스처를 가르치는 것이 아니라,\nAI가 나의 몸짓 언어를 배웁니다.', { x: 0.72, y: 2.24, w: 5.88, h: 1.34, fontFace: FONT, fontSize: 24, bold: true, color: C.text, breakLine: false, margin: 0, objectName: 'Cover statement' });
  slide.addText('Motion × Context × Personal Memory', { x: 0.72, y: 3.86, w: 4.85, h: 0.34, fontFace: FONT, fontSize: 13.5, bold: true, color: C.violet, margin: 0, objectName: 'Cover equation' });
  slide.addText('사용자의 자연스러운 행동을 관찰하고, 반복 패턴을 먼저 제안한 뒤 승인된 기억만 실행하는 로컬 우선 Spatial AI Agent', { x: 0.72, y: 4.42, w: 5.82, h: 0.96, fontFace: FONT, fontSize: 12, color: C.muted, margin: 0, breakLine: false, objectName: 'Cover description' });
  addCard(slide, 7.12, 0.68, 5.52, 5.96, { fill: '0D1222', line: '26345A', radius: 0.22, shadow: true });
  slide.addImage({ path: IMG.execution, ...imageSizingCrop(IMG.execution, 7.28, 0.84, 5.2, 5.64), objectName: 'MVP execution UI screenshot' });
  addPill(slide, 'LIVE MVP', 10.82, 0.98, 1.17, { fill: '15322D', color: C.green, border: '245B4A', fontSize: 8.8 });
  slide.addText('해커톤 MVP · FastAPI / SQLite / OpenCV', { x: 0.72, y: 6.54, w: 4.5, h: 0.24, fontFace: FONT, fontSize: 9.5, color: C.muted2, margin: 0, objectName: 'Cover footer' });
  addNotes(slide, 'SilentOrchestra 2.0은 정해진 제스처를 인식하는 앱이 아닙니다. 사용자의 행동과 상황을 관찰해 개인의 몸짓 언어를 스스로 학습하는 Spatial AI Agent입니다. 오늘은 이 학습 과정이 실제 MVP에서 어떻게 동작하는지 보여드리겠습니다.');
}

// 2. Problem
{
  const slide = pptx.addSlide({ masterName: 'MASTER_DARK' });
  addHeader(slide, '제스처 인터페이스의 문제는 인식률만이 아닙니다', '01 · Problem');
  slide.addText('기존 시스템은 사용자의 몸짓을 배우지 않고, 사용자가 시스템의 명령어를 외우게 합니다.', { x: 0.66, y: 1.52, w: 11.8, h: 0.42, fontFace: FONT, fontSize: 17, bold: true, color: C.text, margin: 0, objectName: 'Problem lead' });

  const cards = [
    { n: '01', title: '외워야 하는 제스처', body: 'S는 다음, O는 볼륨처럼\n미리 정한 동작을 정확히 재현', accent: C.cyan },
    { n: '02', title: '상황이 바뀌어도 고정', body: '같은 오른쪽 손짓이 발표와 음악에서\n다른 의미일 수 있다는 점을 놓침', accent: C.violet },
    { n: '03', title: '카메라에 대한 불신', body: '영상 저장 여부가 불명확하면\n사용자는 공간형 인터페이스를 꺼림', accent: C.red },
  ];
  cards.forEach((c, i) => {
    const x = 0.66 + i * 4.14;
    addCard(slide, x, 2.22, 3.72, 2.65, { fill: C.card, line: i === 0 ? '245265' : i === 1 ? '423B72' : '5A2B3A', radius: 0.16 });
    slide.addText(c.n, { x: x + 0.24, y: 2.43, w: 0.72, h: 0.35, fontFace: FONT, fontSize: 14, bold: true, color: c.accent, margin: 0, objectName: `Problem number ${c.n}` });
    slide.addText(c.title, { x: x + 0.24, y: 2.95, w: 3.16, h: 0.42, fontFace: FONT, fontSize: 18, bold: true, color: C.text, margin: 0, objectName: `Problem title ${c.title}` });
    slide.addText(c.body, { x: x + 0.24, y: 3.58, w: 3.14, h: 0.72, fontFace: FONT, fontSize: 11.2, color: C.muted, margin: 0, breakLine: false, objectName: `Problem body ${c.title}` });
    slide.addShape(pptx.ShapeType.line, { x: x + 0.24, y: 4.57, w: 0.78, h: 0, line: { color: c.accent, pt: 3 }, objectName: `Problem accent ${c.n}` });
  });

  addCard(slide, 0.66, 5.28, 12.0, 1.18, { fill: '0E1425', line: C.line, shadow: false });
  slide.addText('기존 Gesture Control', { x: 0.94, y: 5.54, w: 2.3, h: 0.3, fontFace: FONT, fontSize: 13, bold: true, color: C.muted, margin: 0, objectName: 'Old model label' });
  slide.addText('Gesture', { x: 3.37, y: 5.5, w: 1.1, h: 0.3, fontFace: FONT, fontSize: 14, bold: true, color: C.text, align: 'center', margin: 0, objectName: 'Old flow gesture' });
  addArrow(slide, 4.48, 5.67, 0.72, C.muted2, 1.5);
  slide.addText('Classifier', { x: 5.25, y: 5.5, w: 1.34, h: 0.3, fontFace: FONT, fontSize: 14, bold: true, color: C.text, align: 'center', margin: 0, objectName: 'Old flow classifier' });
  addArrow(slide, 6.64, 5.67, 0.72, C.muted2, 1.5);
  slide.addText('Fixed Command', { x: 7.43, y: 5.5, w: 1.88, h: 0.3, fontFace: FONT, fontSize: 14, bold: true, color: C.red, align: 'center', margin: 0, objectName: 'Old flow command' });
  slide.addText('사용자가 시스템의 언어에 적응', { x: 9.76, y: 5.5, w: 2.52, h: 0.34, fontFace: FONT, fontSize: 12.3, bold: true, color: C.red, align: 'right', margin: 0, objectName: 'Old model conclusion' });
  addFooter(slide, '문제의 중심: “동작을 얼마나 잘 맞히는가”가 아니라 “누구의 언어를 기준으로 하는가”');
  addNotes(slide, '기존 제스처 제어는 인식 정확도를 높이는 데 집중했습니다. 하지만 사용자는 여전히 정해진 제스처를 외워야 하고, 상황이 달라져도 의미가 고정되며, 카메라가 무엇을 저장하는지 불안합니다. 문제의 핵심은 인식률보다 인터페이스의 기준이 시스템 중심이라는 점입니다.');
}

// 3. Solution
{
  const slide = pptx.addSlide({ masterName: 'MASTER_DARK' });
  addHeader(slide, '사용자가 설정하지 않아도, Agent가 먼저 패턴을 발견합니다', '02 · Solution', { accent: C.violet });
  addCard(slide, 0.66, 1.58, 4.05, 4.9, { fill: '0D1324', line: '35406A', radius: 0.2 });
  slide.addText('SilentOrchestra의 판단식', { x: 0.97, y: 1.92, w: 3.35, h: 0.35, fontFace: FONT, fontSize: 13, bold: true, color: C.muted, margin: 0, objectName: 'Equation label' });
  slide.addText('Motion', { x: 0.97, y: 2.64, w: 3.32, h: 0.48, fontFace: FONT, fontSize: 26, bold: true, color: C.cyan, align: 'center', margin: 0, objectName: 'Equation motion' });
  slide.addText('×', { x: 2.24, y: 3.13, w: 0.8, h: 0.4, fontFace: FONT, fontSize: 22, bold: true, color: C.muted2, align: 'center', margin: 0, objectName: 'Equation multiply 1' });
  slide.addText('Context', { x: 0.97, y: 3.53, w: 3.32, h: 0.48, fontFace: FONT, fontSize: 26, bold: true, color: C.violet, align: 'center', margin: 0, objectName: 'Equation context' });
  slide.addText('×', { x: 2.24, y: 4.02, w: 0.8, h: 0.4, fontFace: FONT, fontSize: 22, bold: true, color: C.muted2, align: 'center', margin: 0, objectName: 'Equation multiply 2' });
  slide.addText('Personal Memory', { x: 0.97, y: 4.43, w: 3.32, h: 0.48, fontFace: FONT, fontSize: 24, bold: true, color: C.green, align: 'center', margin: 0, objectName: 'Equation memory' });
  slide.addShape(pptx.ShapeType.line, { x: 1.3, y: 5.21, w: 2.65, h: 0, line: { color: C.line, pt: 1 }, objectName: 'Equation line' });
  slide.addText('Intent Reasoning', { x: 0.97, y: 5.51, w: 3.32, h: 0.48, fontFace: FONT, fontSize: 24, bold: true, color: C.text, align: 'center', margin: 0, objectName: 'Equation intent' });

  const steps = [
    ['Observation', '몸짓과 현재 앱·활동을 함께 기록', C.cyan],
    ['Pattern', '직후 사용자 행동과 반복 관계 탐지', C.green],
    ['Suggestion', '“이 몸짓을 기억할까요?” 질문', C.amber],
    ['Memory', '승인된 User + Context + Intent 저장', C.violet],
    ['Feedback', '맞음·틀림으로 confidence 갱신', C.red],
  ];
  steps.forEach((s, i) => {
    const y = 1.58 + i * 1.0;
    addCard(slide, 5.12, y, 7.54, 0.78, { fill: i === 3 ? '191633' : C.card, line: i === 3 ? '5C4EA8' : C.line, shadow: false });
    slide.addShape(pptx.ShapeType.ellipse, { x: 5.38, y: y + 0.18, w: 0.42, h: 0.42, fill: { color: s[2] }, line: { color: s[2], transparency: 100 }, objectName: `Solution step ${i+1} icon` });
    slide.addText(String(i + 1), { x: 5.38, y: y + 0.27, w: 0.42, h: 0.16, fontFace: FONT, fontSize: 9.2, bold: true, color: C.bg, align: 'center', margin: 0, objectName: `Solution step ${i+1} number` });
    slide.addText(s[0], { x: 6.02, y: y + 0.16, w: 1.65, h: 0.28, fontFace: FONT, fontSize: 14, bold: true, color: C.text, margin: 0, objectName: `Solution step ${s[0]}` });
    slide.addText(s[1], { x: 7.7, y: y + 0.17, w: 4.55, h: 0.28, fontFace: FONT, fontSize: 10.7, color: C.muted, margin: 0, objectName: `Solution step detail ${s[0]}` });
    if (i < steps.length - 1) {
      slide.addShape(pptx.ShapeType.line, { x: 5.59, y: y + 0.79, w: 0, h: 0.2, line: { color: C.muted2, pt: 1, endArrowType: 'triangle' }, objectName: 'Vertical step arrow' });
    }
  });
  addPill(slide, '승인 전 자동 실행 0회', 8.98, 6.46, 2.74, { fill: '143029', color: C.green, border: '245B4A', fontSize: 10.3 });
  addFooter(slide, '차별점: Gesture → Command가 아니라 Observation → Suggestion → Memory → Feedback');
  addNotes(slide, 'SilentOrchestra는 몸짓만 보지 않습니다. 현재 앱과 활동, 그리고 이전에 사용자가 무엇을 했는지를 함께 관찰합니다. 반복 패턴을 발견하면 바로 실행하지 않고 먼저 기억 여부를 묻습니다. 승인된 패턴만 개인 기억이 되고, 이후 피드백을 통해 확신도를 조정합니다.');
}

// 4. Learning UX
{
  const slide = pptx.addSlide({ masterName: 'MASTER_DARK' });
  addHeader(slide, '핵심 경험은 “등록”이 아니라 “학습 과정”입니다', '03 · Learning UX', { accent: C.amber });
  addCard(slide, 0.66, 1.52, 8.34, 5.2, { fill: '0C1120', line: '2B3554', radius: 0.17 });
  slide.addImage({ path: IMG.learning, ...imageSizingContain(IMG.learning, 0.86, 1.7, 7.94, 4.84), objectName: 'Learning UX screenshot' });
  slide.addShape(pptx.ShapeType.roundRect, { x: 0.86, y: 1.7, w: 7.94, h: 4.84, fill: { color: C.bg, transparency: 100 }, line: { color: C.cyan, transparency: 62, pt: 1 }, rectRadius: 0.1, objectName: 'Learning screenshot frame' });

  slide.addText('3회 자연스러운 반복', { x: 9.42, y: 1.64, w: 3.15, h: 0.38, fontFace: FONT, fontSize: 18, bold: true, color: C.text, margin: 0, objectName: 'Learning count title' });
  addStep(slide, 9.38, 2.18, 3.28, 1, '관찰', '오른쪽 손짓 후 사용자가\n직접 다음 슬라이드 실행', C.cyan);
  addStep(slide, 9.38, 3.52, 3.28, 2, 'Agent 제안', '“이 몸짓을 다음 슬라이드로\n기억할까요?”', C.amber);
  addStep(slide, 9.38, 4.86, 3.28, 3, '승인 후 기억', 'Personal Gesture Memory 저장\n다음 입력부터 자동 실행', C.violet);
  addPill(slide, 'APPROVAL-FIRST', 10.1, 6.29, 1.83, { fill: '163128', color: C.green, border: '235947', fontSize: 8.8 });
  addFooter(slide, '심사 포인트: 한 번의 등록 화면이 아니라 Agent가 사용자 행동에서 의미를 발견하는 장면');
  addNotes(slide, '데모에서 가장 중요한 장면입니다. 오른쪽 손짓 후 사용자가 직접 다음 슬라이드를 세 번 실행합니다. Agent는 반복 관계를 발견하고 기억 여부를 먼저 묻습니다. 사용자가 승인하면 Personal Gesture Memory에 저장되고, 이후 같은 상황의 같은 몸짓은 자동 실행됩니다.');
}

// 5. Context reasoning
{
  const slide = pptx.addSlide({ masterName: 'MASTER_DARK' });
  addHeader(slide, '같은 몸짓도 상황이 바뀌면 다른 언어가 됩니다', '04 · Context Reasoning', { accent: C.violet });
  slide.addText('Gesture ≠ Command', { x: 0.66, y: 1.56, w: 3.1, h: 0.5, fontFace: FONT, fontSize: 22, bold: true, color: C.red, margin: 0, objectName: 'Gesture not command' });
  slide.addText('Gesture + Context + User = Intent', { x: 3.92, y: 1.56, w: 5.15, h: 0.5, fontFace: FONT, fontSize: 22, bold: true, color: C.green, margin: 0, objectName: 'Context equation' });

  addCard(slide, 0.66, 2.38, 2.42, 3.74, { fill: '0F1826', line: '245063', radius: 0.18 });
  slide.addText('→ →', { x: 0.94, y: 3.03, w: 1.86, h: 0.82, fontFace: FONT, fontSize: 40, bold: true, color: C.cyan, align: 'center', margin: 0, objectName: 'Swipe symbol' });
  slide.addText('swipe:right', { x: 0.94, y: 4.1, w: 1.86, h: 0.35, fontFace: FONT, fontSize: 15, bold: true, color: C.text, align: 'center', margin: 0, objectName: 'Swipe key' });
  slide.addText('같은 몸짓', { x: 0.94, y: 4.55, w: 1.86, h: 0.25, fontFace: FONT, fontSize: 10.5, color: C.muted, align: 'center', margin: 0, objectName: 'Same gesture label' });
  addPill(slide, 'MOTION', 1.23, 5.33, 1.28, { fill: '17313A', color: C.cyan, border: '275364', fontSize: 8.5 });

  addArrow(slide, 3.16, 3.32, 0.72, C.muted2, 1.6);
  addArrow(slide, 3.16, 5.14, 0.72, C.muted2, 1.6);

  addCard(slide, 3.95, 2.38, 3.62, 1.52, { fill: '181532', line: '4C4288', radius: 0.16 });
  slide.addText('PRESENTATION', { x: 4.24, y: 2.7, w: 2.98, h: 0.22, fontFace: FONT, fontSize: 9.2, bold: true, color: C.violet, charSpacing: 1.4, margin: 0, objectName: 'Presentation context label' });
  slide.addText('PowerPoint · 발표 중', { x: 4.24, y: 3.04, w: 2.98, h: 0.36, fontFace: FONT, fontSize: 16, bold: true, color: C.text, margin: 0, objectName: 'Presentation context' });
  addCard(slide, 3.95, 4.2, 3.62, 1.52, { fill: '14271F', line: '315E4B', radius: 0.16 });
  slide.addText('MUSIC', { x: 4.24, y: 4.52, w: 2.98, h: 0.22, fontFace: FONT, fontSize: 9.2, bold: true, color: C.green, charSpacing: 1.4, margin: 0, objectName: 'Music context label' });
  slide.addText('Spotify · 음악 감상', { x: 4.24, y: 4.86, w: 2.98, h: 0.36, fontFace: FONT, fontSize: 16, bold: true, color: C.text, margin: 0, objectName: 'Music context' });

  addArrow(slide, 7.65, 3.32, 0.78, C.muted2, 1.6);
  addArrow(slide, 7.65, 5.14, 0.78, C.muted2, 1.6);

  addCard(slide, 8.5, 2.38, 4.16, 1.52, { fill: '12251F', line: '2E654E', radius: 0.16 });
  slide.addText('NEXT_SLIDE', { x: 8.84, y: 2.83, w: 3.46, h: 0.4, fontFace: FONT, fontSize: 22, bold: true, color: C.green, align: 'center', margin: 0, objectName: 'Next slide intent' });
  slide.addText('다음 슬라이드', { x: 8.84, y: 3.3, w: 3.46, h: 0.24, fontFace: FONT, fontSize: 10.5, color: C.muted, align: 'center', margin: 0, objectName: 'Next slide Korean' });
  addCard(slide, 8.5, 4.2, 4.16, 1.52, { fill: '151C33', line: '4B4190', radius: 0.16 });
  slide.addText('NEXT_TRACK', { x: 8.84, y: 4.65, w: 3.46, h: 0.4, fontFace: FONT, fontSize: 22, bold: true, color: C.violet, align: 'center', margin: 0, objectName: 'Next track intent' });
  slide.addText('다음 곡', { x: 8.84, y: 5.12, w: 3.46, h: 0.24, fontFace: FONT, fontSize: 10.5, color: C.muted, align: 'center', margin: 0, objectName: 'Next track Korean' });
  addFooter(slide, 'Context scope가 분리되므로 하나의 동작을 여러 상황에서 자연스럽게 재사용');
  addNotes(slide, '동일한 오른쪽 손짓도 발표 중에는 다음 슬라이드, 음악 감상 중에는 다음 곡이 될 수 있습니다. SilentOrchestra는 Gesture 자체를 Command로 고정하지 않고 User, Gesture, Context의 조합으로 Intent를 기억합니다.');
}

// 6. Architecture
{
  const slide = pptx.addSlide({ masterName: 'MASTER_DARK' });
  addHeader(slide, '원본 영상이 아니라 “행동의 특징”부터 시스템에 들어옵니다', '05 · Architecture', { accent: C.cyan });
  addPill(slide, 'RAW FRAME DISCARDED', 0.66, 1.5, 2.35, { fill: '341823', color: C.red, border: '653043', fontSize: 8.8 });
  addPill(slide, 'LOCAL-FIRST MEMORY', 10.46, 1.5, 2.2, { fill: '153028', color: C.green, border: '2D624F', fontSize: 8.8 });
  addCard(slide, 0.66, 1.98, 12.0, 4.78, { fill: C.white, line: 'D8DEEA', radius: 0.14, shadow: true });
  slide.addImage({ path: IMG.architecture, ...imageSizingContain(IMG.architecture, 0.92, 2.18, 11.48, 4.36), objectName: 'System architecture diagram' });
  addFooter(slide, 'Perception → Context Engine → Agent → Memory → Action Executor');
  addNotes(slide, '카메라 입력은 Motion Feature Extractor에서 Optical Flow 특징으로 바뀌고 원본 프레임은 즉시 폐기됩니다. 이후 Gesture Encoder, Context Engine, Observation Engine이 학습 근거를 만들고, Pattern Learning과 Intent Reasoner가 제안 또는 실행을 결정합니다. 피드백은 다시 Personal Gesture Memory에 반영됩니다.');
}

// 7. Agent logic
{
  const slide = pptx.addSlide({ masterName: 'MASTER_DARK' });
  addHeader(slide, 'Agent는 확신도에 따라 “실행”과 “질문”을 나눕니다', '06 · Agent Logic', { accent: C.amber });
  addCard(slide, 0.66, 1.58, 12.0, 1.5, { fill: C.white, line: 'DCE1EC', radius: 0.14, shadow: false });
  slide.addImage({ path: IMG.loop, ...imageSizingContain(IMG.loop, 0.89, 1.83, 11.54, 0.98), objectName: 'Learning loop diagram' });

  const tiers = [
    { label: 'HIGH', title: '자동 실행', body: '활성화된 개인 기억과\n높은 유사도', color: C.green, value: '≥ 0.60' },
    { label: 'AMBIGUOUS', title: '사용자에게 질문', body: '패턴은 보이지만\n승인 또는 수정 필요', color: C.amber, value: '0.55–0.59' },
    { label: 'LOW / WRONG', title: '관찰 유지', body: '실행하지 않고 추가 관찰\n틀림 피드백 시 confidence 감소', color: C.red, value: '< 0.55' },
  ];
  tiers.forEach((t, i) => {
    const x = 0.66 + i * 4.14;
    addCard(slide, x, 3.45, 3.72, 2.48, { fill: C.card, line: i === 0 ? '2F5F4D' : i === 1 ? '66512D' : '623243', radius: 0.16 });
    slide.addText(t.label, { x: x + 0.25, y: 3.73, w: 1.8, h: 0.22, fontFace: FONT, fontSize: 9, bold: true, color: t.color, charSpacing: 1.2, margin: 0, objectName: `Confidence tier ${t.label}` });
    slide.addText(t.value, { x: x + 2.39, y: 3.71, w: 1.0, h: 0.24, fontFace: FONT, fontSize: 10, bold: true, color: t.color, align: 'right', margin: 0, objectName: `Confidence value ${t.value}` });
    slide.addText(t.title, { x: x + 0.25, y: 4.22, w: 3.18, h: 0.4, fontFace: FONT, fontSize: 19, bold: true, color: C.text, margin: 0, objectName: `Confidence title ${t.title}` });
    slide.addText(t.body, { x: x + 0.25, y: 4.85, w: 3.15, h: 0.64, fontFace: FONT, fontSize: 10.6, color: C.muted, margin: 0, breakLine: false, objectName: `Confidence body ${t.title}` });
    slide.addShape(pptx.ShapeType.line, { x: x + 0.25, y: 5.68, w: 0.78, h: 0, line: { color: t.color, pt: 3 }, objectName: `Confidence accent ${t.label}` });
  });
  addPill(slide, 'MVP RULE: 동일 패턴 3회 → 제안', 4.82, 6.24, 3.72, { fill: '1C1A31', color: C.violet, border: '4B4381', fontSize: 9.6 });
  addFooter(slide, '실행 근거를 남기는 executions 로그와 사용자 feedback으로 학습 이력 추적');
  addNotes(slide, 'MVP에서는 동일 맥락의 동일 몸짓과 후속 행동이 세 번 반복되면 제안을 생성합니다. 활성화된 기억과 유사도가 높으면 자동 실행하고, 애매하면 질문합니다. 잘못된 행동이라는 피드백은 confidence를 낮추고 추가 관찰 상태로 되돌립니다. 수치는 데모 안정성을 위한 구현 규칙입니다.');
}

// 8. ERD
{
  const slide = pptx.addSlide({ masterName: 'MASTER_DARK' });
  addHeader(slide, 'DB도 명령 매핑이 아니라 학습 이력을 저장합니다', '07 · ERD & SQL', { accent: C.violet });
  addCard(slide, 0.66, 1.52, 9.62, 5.18, { fill: C.white, line: 'DCE1EA', radius: 0.14, shadow: true });
  slide.addImage({ path: IMG.erd, ...imageSizingContain(IMG.erd, 0.86, 1.71, 9.22, 4.8), objectName: 'ERD diagram' });
  addCard(slide, 10.55, 1.52, 2.11, 5.18, { fill: '11172A', line: '35406A', radius: 0.14, shadow: false });
  slide.addText('8 TABLES', { x: 10.8, y: 1.84, w: 1.58, h: 0.25, fontFace: FONT, fontSize: 9.2, bold: true, color: C.violet, charSpacing: 1.2, align: 'center', margin: 0, objectName: 'ERD table count' });
  const tables = ['users', 'contexts', 'observations', 'actions', 'patterns', 'suggestions', 'executions', 'feedback'];
  tables.forEach((t, i) => {
    const y = 2.27 + i * 0.43;
    slide.addShape(pptx.ShapeType.ellipse, { x: 10.83, y: y + 0.04, w: 0.12, h: 0.12, fill: { color: i < 4 ? C.cyan : i < 6 ? C.violet : i === 6 ? C.green : C.red }, line: { color: C.bg, transparency: 100 }, objectName: `Table dot ${t}` });
    slide.addText(t, { x: 11.04, y, w: 1.3, h: 0.19, fontFace: FONT, fontSize: 9.5, color: C.text, margin: 0, objectName: `Table ${t}` });
  });
  slide.addShape(pptx.ShapeType.line, { x: 10.82, y: 5.89, w: 1.57, h: 0, line: { color: C.line, pt: 1 }, objectName: 'ERD side divider' });
  slide.addText('구현 보강', { x: 10.82, y: 6.04, w: 1.58, h: 0.22, fontFace: FONT, fontSize: 9, bold: true, color: C.green, align: 'center', margin: 0, objectName: 'Implementation expansion label' });
  slide.addText('executions 감사 로그', { x: 10.72, y: 6.3, w: 1.78, h: 0.26, fontFace: FONT, fontSize: 9.2, color: C.muted, align: 'center', margin: 0, objectName: 'Implementation expansion' });
  addFooter(slide, '핵심 제약조건: gesture_observations.frame_stored = 0 · User + Gesture + Context 단위 기억');
  addNotes(slide, '데이터베이스의 중심은 gesture-command 매핑이 아닙니다. 관찰, 맥락, 후속 행동, 패턴, 제안, 실행, 피드백을 모두 남겨 Agent가 왜 학습했고 어떻게 수정됐는지 추적합니다. 원문 관계도에 있었지만 상세 필드가 없던 executions는 실행 결과와 피드백을 연결하기 위한 감사 로그로 구현 보강했습니다.');
}

// 9. Privacy
{
  const slide = pptx.addSlide({ masterName: 'MASTER_DARK' });
  addHeader(slide, 'Privacy는 문구가 아니라 데이터 구조로 증명합니다', '08 · Privacy by Design', { accent: C.green });
  addCard(slide, 0.66, 1.58, 6.32, 4.88, { fill: '0E1424', line: '2C3854', radius: 0.18 });
  slide.addText('CAMERA DATA FLOW', { x: 0.98, y: 1.92, w: 2.2, h: 0.22, fontFace: FONT, fontSize: 9, bold: true, color: C.cyan, charSpacing: 1.4, margin: 0, objectName: 'Privacy flow label' });
  const flow = [
    ['Camera', '현재 프레임'],
    ['Motion Features', 'Optical Flow / Vector'],
    ['Frame Discarded', '원본 즉시 폐기'],
    ['Local Memory', '특징과 학습 이력만 저장'],
  ];
  flow.forEach((f, i) => {
    const y = 2.37 + i * 0.95;
    addCard(slide, 1.04, y, 5.55, 0.68, { fill: i === 2 ? '2B1720' : i === 3 ? '132A22' : C.card, line: i === 2 ? '683144' : i === 3 ? '2F644F' : C.line, shadow: false });
    slide.addText(String(i + 1).padStart(2, '0'), { x: 1.26, y: y + 0.2, w: 0.48, h: 0.2, fontFace: FONT, fontSize: 9.5, bold: true, color: i === 2 ? C.red : i === 3 ? C.green : C.cyan, margin: 0, objectName: `Privacy flow number ${i+1}` });
    slide.addText(f[0], { x: 1.8, y: y + 0.14, w: 1.75, h: 0.26, fontFace: FONT, fontSize: 13, bold: true, color: C.text, margin: 0, objectName: `Privacy flow ${f[0]}` });
    slide.addText(f[1], { x: 3.66, y: y + 0.17, w: 2.58, h: 0.23, fontFace: FONT, fontSize: 9.5, color: C.muted, align: 'right', margin: 0, objectName: `Privacy flow detail ${f[0]}` });
    if (i < flow.length - 1) slide.addShape(pptx.ShapeType.line, { x: 3.82, y: y + 0.69, w: 0, h: 0.25, line: { color: C.muted2, pt: 1, endArrowType: 'triangle' }, objectName: 'Privacy flow arrow' });
  });
  addPill(slide, 'DB CHECK: frame_stored = 0', 2.04, 6.0, 3.64, { fill: '1C1A31', color: C.violet, border: '4A4380', fontSize: 9.5 });

  addCard(slide, 7.28, 1.58, 5.38, 4.88, { fill: C.card, line: '32425A', radius: 0.18 });
  slide.addText('PRIVACY CONTROL', { x: 7.63, y: 1.92, w: 2.2, h: 0.22, fontFace: FONT, fontSize: 9, bold: true, color: C.green, charSpacing: 1.4, margin: 0, objectName: 'Privacy control label' });
  const toggles = [
    ['Raw video storage', 'OFF', C.red],
    ['Face recognition', 'OFF', C.red],
    ['Cloud video upload', 'OFF', C.red],
    ['On-device processing', 'ON', C.green],
  ];
  toggles.forEach((t, i) => {
    const y = 2.55 + i * 0.78;
    slide.addText(t[0], { x: 7.63, y, w: 3.16, h: 0.28, fontFace: FONT, fontSize: 13, bold: true, color: C.text, margin: 0, objectName: `Privacy toggle ${t[0]}` });
    slide.addShape(pptx.ShapeType.roundRect, { x: 11.09, y: y - 0.02, w: 1.08, h: 0.36, rectRadius: 0.16, fill: { color: t[1] === 'ON' ? '193F32' : '321923' }, line: { color: t[1] === 'ON' ? '2E755B' : '713143', pt: 1 }, objectName: `Privacy toggle control ${t[0]}` });
    slide.addText(t[1], { x: 11.09, y: y + 0.065, w: 1.08, h: 0.16, fontFace: FONT, fontSize: 9, bold: true, color: t[2], align: 'center', margin: 0, objectName: `Privacy toggle value ${t[0]}` });
  });
  slide.addShape(pptx.ShapeType.line, { x: 7.64, y: 5.82, w: 4.52, h: 0, line: { color: C.line, pt: 1 }, objectName: 'Privacy divider' });
  slide.addText('원본 프레임을 받는 API 필드 자체가 없고,\nOpenCV 클라이언트도 디스크 저장 함수를 호출하지 않습니다.', { x: 7.64, y: 6.0, w: 4.52, h: 0.46, fontFace: FONT, fontSize: 9.5, color: C.muted, margin: 0, breakLine: false, objectName: 'Privacy implementation note' });
  addFooter(slide, 'Local-first · No face recognition · No cloud video upload');
  addNotes(slide, '개인정보 보호는 단순 안내 문구가 아닙니다. 원본 프레임은 특징 추출 후 폐기되고, API 스키마에도 이미지 필드가 없습니다. 데이터베이스에는 frame_stored가 항상 0이어야 한다는 제약을 두었고, 얼굴 인식과 클라우드 영상 업로드는 범위에서 제외했습니다.');
}

// 10. MVP implementation
{
  const slide = pptx.addSlide({ masterName: 'MASTER_DARK' });
  addHeader(slide, '핵심 학습 루프를 실제 실행 가능한 MVP로 구현했습니다', '09 · Working MVP', { accent: C.cyan });
  addCard(slide, 0.66, 1.52, 7.22, 5.15, { fill: '0C1120', line: '2B3554', radius: 0.17 });
  slide.addImage({ path: IMG.execution, ...imageSizingContain(IMG.execution, 0.84, 1.72, 6.86, 4.78), objectName: 'Execution UX screenshot' });
  slide.addShape(pptx.ShapeType.roundRect, { x: 0.84, y: 1.72, w: 6.86, h: 4.78, fill: { color: C.bg, transparency: 100 }, line: { color: C.violet, transparency: 60, pt: 1 }, rectRadius: 0.1, objectName: 'Execution screenshot frame' });

  addCard(slide, 8.17, 1.52, 4.49, 2.13, { fill: C.card, line: '33405F', radius: 0.15, shadow: false });
  slide.addText('TECH STACK', { x: 8.47, y: 1.82, w: 1.65, h: 0.22, fontFace: FONT, fontSize: 9, bold: true, color: C.cyan, charSpacing: 1.3, margin: 0, objectName: 'Tech stack label' });
  const stack = [
    ['API', 'FastAPI'], ['DB', 'SQLite + SQLAlchemy'], ['UI', 'Vanilla Web'], ['Motion', 'OpenCV Optical Flow'], ['Test', 'Pytest'],
  ];
  stack.forEach((s, i) => {
    const col = i % 2;
    const row = Math.floor(i / 2);
    const x = 8.47 + col * 1.97;
    const y = 2.25 + row * 0.43;
    slide.addText(s[0], { x, y, w: 0.63, h: 0.2, fontFace: FONT, fontSize: 8.6, bold: true, color: C.violet, margin: 0, objectName: `Stack key ${s[0]}` });
    slide.addText(s[1], { x: x + 0.63, y, w: 1.2, h: 0.2, fontFace: FONT, fontSize: 8.9, color: C.text, margin: 0, objectName: `Stack value ${s[1]}` });
  });

  addCard(slide, 8.17, 3.91, 4.49, 2.76, { fill: C.card, line: '33405F', radius: 0.15, shadow: false });
  slide.addText('CORE API FLOW', { x: 8.47, y: 4.21, w: 1.85, h: 0.22, fontFace: FONT, fontSize: 9, bold: true, color: C.green, charSpacing: 1.3, margin: 0, objectName: 'Core API label' });
  const apis = [
    ['POST /observe', '몸짓·맥락 관찰 / 자동 실행'],
    ['POST /teach', '후속 행동 연결 / 반복 학습'],
    ['POST /suggestions/{id}/respond', '기억 승인·거절'],
    ['POST /executions/{id}/feedback', '맞음·틀림 피드백'],
  ];
  apis.forEach((a, i) => {
    const y = 4.63 + i * 0.43;
    slide.addText(a[0], { x: 8.48, y, w: 2.36, h: 0.19, fontFace: 'Aptos Mono', fontSize: 7.8, bold: true, color: C.cyan, margin: 0, objectName: `API ${a[0]}` });
    slide.addText(a[1], { x: 10.94, y, w: 1.39, h: 0.2, fontFace: FONT, fontSize: 8.3, color: C.muted, align: 'right', margin: 0, objectName: `API detail ${a[0]}` });
  });
  addPill(slide, 'DRY_RUN DEFAULT', 9.49, 6.22, 1.84, { fill: '2D2513', color: C.amber, border: '66532B', fontSize: 8.7 });
  addFooter(slide, 'Windows: start_demo.bat · macOS/Linux: ./start_demo.sh · Web UI: http://127.0.0.1:8000');
  addNotes(slide, 'MVP는 FastAPI와 SQLite 기반이며 브라우저에서 바로 학습 시나리오를 재현할 수 있습니다. 기본값은 안전한 DRY_RUN으로 실제 키를 보내지 않습니다. 선택적으로 OpenCV Optical Flow 클라이언트를 실행해 실시간 수평 모션을 observe API에 전달할 수 있습니다.');
}

// 11. Validation
{
  const slide = pptx.addSlide({ masterName: 'MASTER_DARK' });
  addHeader(slide, '“되는 것처럼 보이는 화면”이 아니라 핵심 흐름을 검증했습니다', '10 · Validation', { accent: C.green });
  addCard(slide, 0.66, 1.58, 5.72, 2.15, { fill: '10182A', line: '2F5D4C', radius: 0.18 });
  addMetric(slide, 0.94, 1.91, 2.22, '16 / 16', 'PYTEST', C.green);
  slide.addShape(pptx.ShapeType.line, { x: 3.43, y: 1.96, w: 0, h: 1.42, line: { color: C.line, pt: 1 }, objectName: 'Validation metric divider' });
  addMetric(slide, 3.71, 1.91, 2.22, '38', 'SQLite 문장', C.cyan);

  addCard(slide, 6.67, 1.58, 5.99, 2.15, { fill: C.card, line: '34405C', radius: 0.18 });
  slide.addText('검증한 핵심 시나리오', { x: 7.0, y: 1.91, w: 2.65, h: 0.3, fontFace: FONT, fontSize: 15, bold: true, color: C.text, margin: 0, objectName: 'Validation scenario title' });
  addCheckRow(slide, 7.0, 2.39, '3회 반복 → 제안 → 승인 → 자동 실행');
  addCheckRow(slide, 7.0, 2.77, 'Presentation / Music Context 분기');
  addCheckRow(slide, 7.0, 3.15, 'WRONG_ACTION 피드백 → confidence 감소');

  addCard(slide, 0.66, 4.03, 7.67, 2.33, { fill: '0D1324', line: '2B3653', radius: 0.16, shadow: false });
  slide.addText('TEST TRACE', { x: 0.98, y: 4.34, w: 1.4, h: 0.2, fontFace: FONT, fontSize: 8.8, bold: true, color: C.violet, charSpacing: 1.3, margin: 0, objectName: 'Test trace label' });
  const trace = [
    ['observe × 3', C.cyan], ['suggestion', C.amber], ['accept', C.violet], ['observe', C.cyan], ['execution', C.green], ['feedback', C.red],
  ];
  trace.forEach((t, i) => {
    const x = 0.98 + i * 1.16;
    addCard(slide, x, 4.85, 0.98, 0.72, { fill: '151B2F', line: C.line, radius: 0.1, shadow: false });
    slide.addText(t[0], { x: x + 0.06, y: 5.08, w: 0.86, h: 0.24, fontFace: 'Aptos Mono', fontSize: 7.8, bold: true, color: t[1], align: 'center', margin: 0, objectName: `Test trace ${t[0]}` });
    if (i < trace.length - 1) addArrow(slide, x + 0.99, 5.21, 0.15, C.muted2, 1);
  });
  slide.addText('pytest -q  →  16 passed', { x: 0.98, y: 5.85, w: 3.4, h: 0.24, fontFace: 'Aptos Mono', fontSize: 9.3, bold: true, color: C.green, margin: 0, objectName: 'Pytest result' });
  slide.addText('validate_sqlite.py  →  passed', { x: 4.39, y: 5.85, w: 3.32, h: 0.24, fontFace: 'Aptos Mono', fontSize: 9.3, bold: true, color: C.cyan, align: 'right', margin: 0, objectName: 'SQLite result' });

  addCard(slide, 8.62, 4.03, 4.04, 2.33, { fill: '281B20', line: '5B3540', radius: 0.16, shadow: false });
  slide.addText('환경 의존 미검증', { x: 8.94, y: 4.35, w: 2.22, h: 0.3, fontFace: FONT, fontSize: 14, bold: true, color: C.red, margin: 0, objectName: 'Unverified title' });
  slide.addText('• 실제 카메라 하드웨어 인식률\n• PowerPoint / Spotify OS 키 전달\n• 다중 사용자 동시성\n• 장기간 embedding drift', { x: 8.94, y: 4.91, w: 3.3, h: 1.15, fontFace: FONT, fontSize: 10.2, color: C.muted, margin: 0, breakLine: false, objectName: 'Unverified list' });
  addFooter(slide, 'API 정상·오류 경로 + SQL 외래키·제약조건 + Privacy 조건 검증');
  addNotes(slide, '핵심 Pytest 테스트 열여섯 개와 SQLite 스키마, 시드, 대표 쿼리, 무결성 검사 38개 문장을 모두 통과했습니다. 학습 루프, 상황별 의도 분기, 잘못된 행동 피드백, 원본 프레임 미저장을 검증했습니다. 다만 실제 카메라 인식률과 OS 키 전달은 현재 컨테이너 환경에서 미검증으로 남겼습니다.');
}

// 12. Demo story
{
  const slide = pptx.addSlide({ masterName: 'MASTER_DARK' });
  addHeader(slide, '90초 데모: Agent가 “배우는 순간”을 보여줍니다', '11 · Demo Story', { accent: C.amber });
  const phases = [
    ['0–15초', '발표 시작', 'Presentation Context 확인', C.cyan],
    ['15–35초', '행동 3회', '오른쪽 손짓 → 직접 다음 슬라이드', C.cyan],
    ['35–50초', '패턴 발견', 'Agent가 기억 여부 제안', C.amber],
    ['50–65초', '기억 승인', 'Personal Gesture Memory 활성화', C.violet],
    ['65–75초', '자동 실행', '같은 손짓 → Next Slide', C.green],
    ['75–90초', 'Context 변경', 'Music에서 같은 손짓 → Next Track', C.green],
  ];
  phases.forEach((p, i) => {
    const x = 0.68 + i * 2.06;
    slide.addShape(pptx.ShapeType.ellipse, { x: x + 0.74, y: 2.06, w: 0.44, h: 0.44, fill: { color: p[3] }, line: { color: p[3], transparency: 100 }, objectName: `Demo phase ${i+1} dot` });
    if (i < phases.length - 1) addArrow(slide, x + 1.18, 2.28, 1.62, C.muted2, 1.4);
    slide.addText(String(i + 1), { x: x + 0.74, y: 2.16, w: 0.44, h: 0.15, fontFace: FONT, fontSize: 8.7, bold: true, color: C.bg, align: 'center', margin: 0, objectName: `Demo phase ${i+1}` });
    slide.addText(p[0], { x, y: 2.74, w: 1.92, h: 0.22, fontFace: FONT, fontSize: 9, bold: true, color: p[3], align: 'center', margin: 0, objectName: `Demo time ${p[0]}` });
    slide.addText(p[1], { x, y: 3.15, w: 1.92, h: 0.34, fontFace: FONT, fontSize: 15, bold: true, color: C.text, align: 'center', margin: 0, objectName: `Demo phase title ${p[1]}` });
    slide.addText(p[2], { x: x + 0.09, y: 3.65, w: 1.74, h: 0.66, fontFace: FONT, fontSize: 9.4, color: C.muted, align: 'center', valign: 'mid', margin: 0, breakLine: false, objectName: `Demo phase detail ${p[1]}` });
  });
  addCard(slide, 1.05, 4.8, 11.23, 1.34, { fill: '10162A', line: '3D426B', radius: 0.17 });
  slide.addText('DEMO PAYOFF', { x: 1.4, y: 5.13, w: 1.5, h: 0.2, fontFace: FONT, fontSize: 8.8, bold: true, color: C.violet, charSpacing: 1.4, margin: 0, objectName: 'Demo payoff label' });
  slide.addText('Personalization', { x: 3.0, y: 5.07, w: 1.7, h: 0.3, fontFace: FONT, fontSize: 15, bold: true, color: C.cyan, align: 'center', margin: 0, objectName: 'Demo payoff personalization' });
  slide.addText('+', { x: 4.7, y: 5.07, w: 0.42, h: 0.3, fontFace: FONT, fontSize: 17, bold: true, color: C.muted2, align: 'center', margin: 0, objectName: 'Demo plus 1' });
  slide.addText('Memory', { x: 5.14, y: 5.07, w: 1.35, h: 0.3, fontFace: FONT, fontSize: 15, bold: true, color: C.violet, align: 'center', margin: 0, objectName: 'Demo payoff memory' });
  slide.addText('+', { x: 6.49, y: 5.07, w: 0.42, h: 0.3, fontFace: FONT, fontSize: 17, bold: true, color: C.muted2, align: 'center', margin: 0, objectName: 'Demo plus 2' });
  slide.addText('Context Reasoning', { x: 6.93, y: 5.07, w: 2.18, h: 0.3, fontFace: FONT, fontSize: 15, bold: true, color: C.green, align: 'center', margin: 0, objectName: 'Demo payoff context' });
  slide.addText('+', { x: 9.11, y: 5.07, w: 0.42, h: 0.3, fontFace: FONT, fontSize: 17, bold: true, color: C.muted2, align: 'center', margin: 0, objectName: 'Demo plus 3' });
  slide.addText('Privacy', { x: 9.54, y: 5.07, w: 1.33, h: 0.3, fontFace: FONT, fontSize: 15, bold: true, color: C.red, align: 'center', margin: 0, objectName: 'Demo payoff privacy' });
  slide.addText('한 번에 설명', { x: 10.96, y: 5.07, w: 0.99, h: 0.3, fontFace: FONT, fontSize: 11.5, bold: true, color: C.text, align: 'right', margin: 0, objectName: 'Demo payoff conclusion' });
  slide.addText('실패 대비: 카메라 대신 UI의 Stable Simulation 버튼으로 동일 API 흐름 재현', { x: 3.0, y: 5.57, w: 8.96, h: 0.23, fontFace: FONT, fontSize: 9.1, color: C.muted, align: 'right', margin: 0, objectName: 'Demo fallback' });
  addFooter(slide, '발표 시 처음부터 등록된 제스처를 보여주지 말고, 학습 과정 자체를 시연');
  addNotes(slide, '발표 시작 후 Presentation Context를 확인합니다. 오른쪽 손짓과 다음 슬라이드 행동을 세 번 반복해 제안을 띄우고, 기억하기를 누릅니다. 다시 손짓해 자동 실행을 확인한 뒤 Music으로 전환하여 같은 손짓이 Next Track으로 해석되는 장면까지 보여줍니다. 카메라가 불안정할 경우 Stable Simulation으로 같은 API 흐름을 재현합니다.');
}

// 13. Closing
{
  const slide = pptx.addSlide({ masterName: 'MASTER_DARK' });
  addPill(slide, 'FROM FIXED COMMANDS TO ADAPTIVE INTERFACES', 0.72, 0.58, 3.75, { fill: '141B2E', color: C.cyan, border: '2D3D5A', fontSize: 8.8 });
  slide.addText('사용자가 인터페이스에 적응하던 시대에서,', { x: 0.72, y: 1.46, w: 6.25, h: 0.56, fontFace: FONT, fontSize: 23, bold: true, color: C.muted, margin: 0, objectName: 'Closing line 1' });
  slide.addText('인터페이스가 사용자에게\n적응하는 시대로.', { x: 0.72, y: 2.13, w: 6.25, h: 1.06, fontFace: FONT, fontSize: 29, bold: true, color: C.text, margin: 0, objectName: 'Closing line 2' });
  slide.addText('SilentOrchestra 2.0', { x: 0.72, y: 3.42, w: 4.4, h: 0.52, fontFace: FONT, fontSize: 24, bold: true, color: C.violet, margin: 0, objectName: 'Closing brand' });
  slide.addText('개인의 몸짓 언어를 학습하는 로컬 우선 Spatial AI Agent', { x: 0.72, y: 4.02, w: 6.2, h: 0.38, fontFace: FONT, fontSize: 14, color: C.muted, margin: 0, objectName: 'Closing subtitle' });

  const road = [
    ['NOW', 'MVP', 'Presentation · Music\nPersonal Memory', C.cyan],
    ['NEXT', 'Accessibility & IoT', '비접촉 제어 · 스마트홈\n사용자별 습관 학습', C.violet],
    ['VISION', 'Spatial Agent Platform', '공간과 행동을 이해하는\n개인 인터페이스 레이어', C.green],
  ];
  road.forEach((r, i) => {
    const x = 7.25 + i * 1.83;
    addCard(slide, x, 1.24, 1.57, 4.4, { fill: i === 2 ? '12271F' : C.card, line: i === 0 ? '2C5260' : i === 1 ? '493F7F' : '2F604C', radius: 0.16, shadow: false });
    slide.addText(r[0], { x: x + 0.17, y: 1.53, w: 1.23, h: 0.2, fontFace: FONT, fontSize: 8.2, bold: true, color: r[3], charSpacing: 1.2, align: 'center', margin: 0, objectName: `Roadmap phase ${r[0]}` });
    slide.addText(r[1], { x: x + 0.12, y: 2.14, w: 1.33, h: 0.72, fontFace: FONT, fontSize: i === 1 ? 14 : 16, bold: true, color: C.text, align: 'center', valign: 'mid', margin: 0, breakLine: false, objectName: `Roadmap title ${r[1]}` });
    slide.addShape(pptx.ShapeType.line, { x: x + 0.29, y: 3.03, w: 0.99, h: 0, line: { color: C.line, pt: 1 }, objectName: 'Roadmap divider' });
    slide.addText(r[2], { x: x + 0.13, y: 3.42, w: 1.31, h: 1.04, fontFace: FONT, fontSize: 9.2, color: C.muted, align: 'center', valign: 'mid', margin: 0, breakLine: false, objectName: `Roadmap detail ${r[1]}` });
    slide.addShape(pptx.ShapeType.ellipse, { x: x + 0.63, y: 5.1, w: 0.31, h: 0.31, fill: { color: r[3] }, line: { color: r[3], transparency: 100 }, objectName: `Roadmap marker ${r[0]}` });
    if (i < road.length - 1) addArrow(slide, x + 1.57, 5.25, 0.26, C.muted2, 1.2);
  });
  addCard(slide, 0.72, 5.1, 6.02, 1.12, { fill: '10172A', line: '364469', radius: 0.14, shadow: false });
  slide.addText('핵심 한 문장', { x: 1.03, y: 5.4, w: 1.3, h: 0.24, fontFace: FONT, fontSize: 10.5, bold: true, color: C.cyan, margin: 0, objectName: 'Final statement label' });
  slide.addText('AI가 사용자의 자연스러운 행동을 관찰하고,\n승인된 몸짓 언어를 기억해 상황에 맞게 실행합니다.', { x: 2.46, y: 5.29, w: 3.91, h: 0.5, fontFace: FONT, fontSize: 12.5, bold: true, color: C.text, margin: 0, breakLine: false, objectName: 'Final statement' });
  slide.addText('Thank you', { x: 10.56, y: 6.52, w: 2.0, h: 0.34, fontFace: FONT, fontSize: 16, bold: true, color: C.text, align: 'right', margin: 0, objectName: 'Thank you' });
  slide.addText('SilentOrchestra 2.0', { x: 10.56, y: 6.9, w: 2.0, h: 0.2, fontFace: FONT, fontSize: 8.5, color: C.muted2, align: 'right', margin: 0, objectName: 'Closing footer brand' });
  addNotes(slide, 'SilentOrchestra는 사용자가 인터페이스의 언어를 외우는 방식을 뒤집습니다. 지금은 발표와 음악이라는 좁은 MVP이지만, 이후 접근성 비접촉 제어와 스마트홈을 거쳐 개인의 공간 행동을 이해하는 인터페이스 레이어로 확장할 수 있습니다. AI가 나의 몸짓 언어를 배우는 인터페이스, SilentOrchestra 2.0입니다. 감사합니다.');
}

for (const slide of pptx._slides) {
  warnIfSlideHasOverlaps(slide, pptx);
  warnIfSlideElementsOutOfBounds(slide, pptx);
}

const out = process.argv[2] || path.join(ROOT, 'SilentOrchestra_2.0_해커톤_발표자료.pptx');
pptx.writeFile({ fileName: out });
