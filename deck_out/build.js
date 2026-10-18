const pptxgen = require("pptxgenjs");
const { applyTheme } = require("/root/.claude/skills/synced/d6ebe57e-1105-4919-9f8e-ec1f7584807c_e80e0132-bc42-4654-b5c0-8f32a02558b7/pptx/scripts/apply_theme.js");

const FONT = "Malgun Gothic";
const THEME = {
  name: "AI2041 Night",
  headFontFace: FONT,
  bodyFontFace: FONT,
  colors: {
    dk1: "0B1230", lt1: "FFFFFF", dk2: "1B2559", lt2: "E8ECFF",
    accent1: "2EF2C0", accent2: "8B5CF6", accent3: "4C6FFF",
    accent4: "FFB84D", accent5: "FF6B8A", accent6: "9AA4D6",
    hlink: "2EF2C0", folHlink: "9AA4D6",
  },
};

const pres = new pptxgen();
pres.layout = "LAYOUT_16x9"; // 10 x 5.625
pres.title = "AI 2041 - 소설 속 기술의 원리";
pres.author = "발표자";
pres.theme = { headFontFace: FONT, bodyFontFace: FONT };
const C = pres.SchemeColor;

const BG = "0B1230";
const FOOT = "AI 2041 · 통합과학2 Ⅲ. 과학과 미래 사회";

pres.defineSlideMaster({
  title: "TITLE_DARK",
  background: { color: BG },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.7, y: 1.5, w: 8.6, h: 1.6, fontSize: 40, bold: true, color: C.background1, align: "left", valign: "top", margin: 0 }, text: "" } },
  ],
});

pres.defineSlideMaster({
  title: "CONTENT_DARK",
  background: { color: BG },
  slideNumber: { x: 9.0, y: 5.15, w: 0.5, h: 0.3, fontSize: 10, color: C.accent6, align: "right" },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.5, y: 0.35, w: 9.0, h: 0.8, fontSize: 28, bold: true, color: C.background1, align: "left", valign: "middle", margin: 0 }, text: "" } },
    { text: { text: FOOT, options: { x: 0.5, y: 5.15, w: 6, h: 0.3, fontSize: 10, color: C.accent6, margin: 0, isTextBox: true } } },
  ],
});

// ---------- helpers ----------
const txt = (s, text, o) => s.addText(text, Object.assign({ isTextBox: true, fontFace: FONT, color: C.background1, margin: 0, valign: "top" }, o));

function card(s, x, y, w, h, name) {
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x, y, w, h, rectRadius: 0.12, fill: { color: C.text2 }, line: { color: C.text2, width: 0 }, objectName: name || "card",
  });
}
function badge(s, x, y, d, label, color, name) {
  s.addShape(pres.shapes.OVAL, { x, y, w: d, h: d, fill: { color }, line: { color, width: 0 }, objectName: name || "badge" });
  txt(s, label, { x, y, w: d, h: d, align: "center", valign: "middle", bold: true, fontSize: 14, color: C.text1 });
}
function line(s, x1, y1, x2, y2, color, width, name) {
  s.addShape(pres.shapes.LINE, {
    x: Math.min(x1, x2), y: Math.min(y1, y2), w: Math.abs(x2 - x1), h: Math.abs(y2 - y1),
    flipV: y2 < y1, line: { color, width }, objectName: name || "line",
  });
}
function arrow(s, x, y, w, h, color) {
  s.addShape(pres.shapes.RIGHT_ARROW, { x, y, w, h, fill: { color }, line: { color, width: 0 }, objectName: "arrow" });
}

const content = (title, section, notes) => {
  const s = pres.addSlide({ masterName: "CONTENT_DARK", sectionTitle: section });
  s.addText(title, { placeholder: "title" });
  if (notes) s.addNotes(notes);
  return s;
};

// ================= 1. 표지 =================
pres.addSection({ title: "도입" });
{
  const s = pres.addSlide({ masterName: "TITLE_DARK", sectionTitle: "도입" });
  txt(s, "#인공지능   #자율주행   #감염병 진단", { x: 0.7, y: 0.8, w: 8.6, h: 0.4, fontSize: 16, color: C.accent1, bold: true });
  s.addText("AI 2041, 소설 속 기술의\n원리를 파헤치다", { placeholder: "title" });
  txt(s, "카이푸 리 · 천치판 지음", { x: 0.7, y: 3.55, w: 8.6, h: 0.4, fontSize: 18, color: C.accent6 });
  txt(s, "통합과학2 Ⅲ. 과학과 미래 사회 연계 도서 소개  |  발표자: (이름)", { x: 0.7, y: 4.1, w: 8.6, h: 0.4, fontSize: 14, color: C.accent6 });
  // 회로 모티프: 오른쪽 아래 노드
  const pts = [[8.0, 4.7], [8.6, 4.35], [9.2, 4.7], [8.6, 5.1]];
  line(s, 8.0, 4.7, 8.6, 4.35, C.accent2, 1.5); line(s, 8.6, 4.35, 9.2, 4.7, C.accent2, 1.5);
  line(s, 8.0, 4.7, 8.6, 5.1, C.accent2, 1.5); line(s, 8.6, 5.1, 9.2, 4.7, C.accent2, 1.5);
  pts.forEach(([px, py]) => s.addShape(pres.shapes.OVAL, { x: px - 0.09, y: py - 0.09, w: 0.18, h: 0.18, fill: { color: C.accent1 }, line: { color: C.accent1, width: 0 }, objectName: "node" }));
  s.addNotes("안녕하세요. 오늘은 『AI 2041』을 소개하겠습니다. 소설로 읽는 책이지만, 오늘은 소설 속 기술이 '어떤 원리로 작동하는지'에 집중해서 설명하겠습니다.");
}

// ================= 2. 질문 도입 =================
{
  const s = content("2041년의 AI는 어떤 원리로 작동할까?", "도입",
    "이 책은 2041년을 배경으로 한 단편소설 10편과, 각 소설 뒤에 붙은 실제 기술 해설로 이루어져 있습니다. 저자 카이푸 리는 AI 분야 전문가, 천치판은 SF 작가입니다. 소설은 '가능한 시나리오'이고, 해설 부분은 실제 연구를 바탕으로 합니다.");
  card(s, 0.5, 1.4, 4.2, 3.4, "card-stat1");
  txt(s, "10편", { x: 0.8, y: 1.65, w: 3.6, h: 1.1, fontSize: 60, bold: true, color: C.accent1 });
  txt(s, "2041년을 배경으로 한 단편소설", { x: 0.8, y: 2.85, w: 3.6, h: 0.4, fontSize: 16 });
  txt(s, "각 편마다 실제 기술 해설이 붙어 있어 '소설 → 원리 → 현실'로 읽을 수 있다", { x: 0.8, y: 3.4, w: 3.6, h: 1.1, fontSize: 14, color: C.accent6 });

  card(s, 5.0, 1.4, 4.5, 1.55, "card-author1");
  badge(s, 5.25, 1.65, 0.5, "AI", C.accent3, "badge-author1");
  txt(s, "카이푸 리", { x: 5.95, y: 1.6, w: 3.4, h: 0.4, fontSize: 18, bold: true });
  txt(s, "AI 전문가 (구글 차이나 사장 출신)\n기술 해설 담당", { x: 5.95, y: 2.05, w: 3.4, h: 0.8, fontSize: 14, color: C.accent6 });

  card(s, 5.0, 3.25, 4.5, 1.55, "card-author2");
  badge(s, 5.25, 3.5, 0.5, "SF", C.accent2, "badge-author2");
  txt(s, "천치판", { x: 5.95, y: 3.45, w: 3.4, h: 0.4, fontSize: 18, bold: true });
  txt(s, "SF 소설가\n단편소설 담당", { x: 5.95, y: 3.9, w: 3.4, h: 0.8, fontSize: 14, color: C.accent6 });
}

// ================= 3. 책 선정 이유 =================
{
  const s = content("교과서 소단원 3개 × 단편 3편", "도입",
    "10편을 다 다루면 시간이 부족해서, 통합과학2 Ⅲ단원과 가장 잘 맞는 3편만 골랐습니다. 소단원 이름은 교과서마다 조금 다르니 본인 교과서 목차에 맞춰 수정하세요. 단편 제목도 번역본에 따라 다를 수 있습니다.");
  const cols = [
    { tag: "소단원 ①", unit: "인공지능과 빅데이터", story: "「황금 코끼리」", core: "딥러닝은 데이터에서 패턴을 스스로 학습한다", color: C.accent1 },
    { tag: "소단원 ②", unit: "센서와 자율 시스템", story: "「성스러운 운전사」", core: "센서로 수집한 정보를 컴퓨터가 판단해 제어한다", color: C.accent3 },
    { tag: "소단원 ③", unit: "감염병 진단과 예방", story: "「무접촉 사랑」", core: "검사 원리와 데이터 분석으로 진단·예방한다", color: C.accent4 },
  ];
  cols.forEach((c, i) => {
    const x = 0.5 + i * 3.05;
    card(s, x, 1.4, 2.9, 3.4, "card-unit" + (i + 1));
    txt(s, c.tag, { x: x + 0.25, y: 1.6, w: 2.4, h: 0.3, fontSize: 12, bold: true, color: c.color });
    txt(s, c.unit, { x: x + 0.25, y: 1.95, w: 2.4, h: 0.7, fontSize: 18, bold: true });
    s.addShape(pres.shapes.DOWN_ARROW, { x: x + 1.3, y: 2.7, w: 0.3, h: 0.35, fill: { color: c.color }, line: { color: c.color, width: 0 }, objectName: "arrow-down" + (i + 1) });
    txt(s, c.story, { x: x + 0.25, y: 3.15, w: 2.4, h: 0.4, fontSize: 16, bold: true, color: c.color });
    txt(s, c.core, { x: x + 0.25, y: 3.65, w: 2.4, h: 1.0, fontSize: 14, color: C.accent6 });
  });
}

// ================= 4. 공통 틀 =================
pres.addSection({ title: "원리" });
{
  const s = content("세 기술의 공통 원리: 입력 → 처리 → 출력", "원리",
    "세 가지 기술은 모두 '입력 → 처리 → 출력'이라는 같은 틀로 설명할 수 있습니다. 이 틀을 기억하면 뒤의 세 원리가 하나로 이어집니다.");
  const steps = [
    { h: "입력", sub: "데이터·센서 신호", items: ["학습 데이터", "카메라·레이더·라이다", "검체·이동 데이터"], color: C.accent1 },
    { h: "처리", sub: "알고리즘이 계산", items: ["신경망 학습", "인식·판단 알고리즘", "검사·예측 모델"], color: C.accent3 },
    { h: "출력", sub: "판단·제어·결정", items: ["예측·판단", "가속·제동·조향", "진단·방역 결정"], color: C.accent4 },
  ];
  steps.forEach((st, i) => {
    const x = 0.5 + i * 3.3;
    card(s, x, 1.4, 2.4, 1.3, "card-step" + (i + 1));
    txt(s, st.h, { x, y: 1.55, w: 2.4, h: 0.55, fontSize: 28, bold: true, align: "center", color: st.color });
    txt(s, st.sub, { x, y: 2.15, w: 2.4, h: 0.4, fontSize: 14, align: "center", color: C.accent6 });
    if (i < 2) arrow(s, x + 2.5, 1.9, 0.7, 0.3, C.accent2);
    txt(s, st.items.map((t, k) => ({ text: t, options: { bullet: true, breakLine: k < st.items.length - 1 } })), {
      x: x + 0.15, y: 3.1, w: 2.3, h: 1.4, fontSize: 14, paraSpaceAfter: 6,
    });
  });
  txt(s, "위에서부터 ① 인공지능  ② 자율주행  ③ 감염병 진단 순서", { x: 0.5, y: 4.65, w: 9.0, h: 0.3, fontSize: 12, color: C.accent6 });
}

// ================= 5. 딥러닝 =================
{
  const s = content("원리 ① 딥러닝은 오차를 줄이며 학습한다", "원리",
    "「황금 코끼리」에서 보험 앱의 AI는 '보험료 최소화'라는 목표 하나만 최적화하다가 사용자의 행동을 조종하고 차별까지 일으킵니다. 딥러닝은 입력층-은닉층-출력층으로 이루어진 인공신경망입니다. 예측이 틀리면 오차를 계산하고, 오차가 줄어드는 방향으로 연결 강도(가중치)를 조금씩 고칩니다(경사하강법·역전파). 이걸 수없이 반복하면 패턴을 학습합니다. 편향: 학습 데이터가 치우치면 결과도 치우칩니다. AI는 사람처럼 '생각'하는 게 아니라 데이터 속 통계적 패턴을 찾는 것입니다.");
  txt(s, "교과서 개념: 인공지능, 빅데이터", { x: 0.5, y: 1.2, w: 5, h: 0.3, fontSize: 12, bold: true, color: C.accent1 });
  // 신경망 도식
  const layers = [
    { x: 0.9, n: 3, label: "입력층" },
    { x: 2.5, n: 4, label: "은닉층" },
    { x: 4.1, n: 2, label: "출력층" },
  ];
  const top = 1.65, span = 2.1;
  const ys = (n) => Array.from({ length: n }, (_, k) => top + (span * (k + 0.5)) / n);
  for (let l = 0; l < 2; l++) {
    ys(layers[l].n).forEach((y1) => ys(layers[l + 1].n).forEach((y2) => line(s, layers[l].x, y1, layers[l + 1].x, y2, C.accent6, 0.75, "edge")));
  }
  const colors = [C.accent1, C.accent2, C.accent4];
  layers.forEach((L, li) => {
    ys(L.n).forEach((y) => s.addShape(pres.shapes.OVAL, { x: L.x - 0.16, y: y - 0.16, w: 0.32, h: 0.32, fill: { color: colors[li] }, line: { color: C.text1, width: 1 }, objectName: "neuron" }));
    txt(s, L.label, { x: L.x - 0.5, y: 3.8, w: 1.0, h: 0.3, fontSize: 12, align: "center", color: C.accent6 });
  });
  // 학습 4단계
  const rows = [
    ["1", "입력 데이터로 예측값을 만든다"],
    ["2", "정답과 비교해 오차(손실)를 계산한다"],
    ["3", "오차가 줄어드는 방향으로 가중치를 고친다"],
    ["4", "수없이 반복하면 패턴을 학습한다"],
  ];
  rows.forEach((r, i) => {
    const y = 1.6 + i * 0.58;
    badge(s, 5.4, y, 0.42, r[0], C.accent1, "step-badge" + r[0]);
    txt(s, r[1], { x: 6.0, y: y, w: 3.5, h: 0.42, fontSize: 14, valign: "middle" });
  });
  // 편향 콜아웃
  card(s, 0.5, 4.2, 9.0, 0.75, "callout-bias");
  txt(s, [
    { text: "편향의 원인  ", options: { bold: true, color: C.accent4 } },
    { text: "데이터가 치우치면 결과도 치우친다. 소설 속 AI는 '보험료 최소화' 하나만 최적화했다.", options: {} },
  ], { x: 0.75, y: 4.2, w: 8.5, h: 0.75, fontSize: 14, valign: "middle" });
}

// ================= 6. 자율주행 =================
{
  const s = content("원리 ② 자율주행은 센서로 보고 판단해 제어한다", "원리",
    "「성스러운 운전사」는 AI가 운전하는 세상을 그립니다. 자율주행은 센서로 주변을 인식하고, 컴퓨터가 경로와 행동을 판단한 뒤, 가속·제동·조향을 제어하는 과정입니다. 카메라는 빛으로 영상을 얻어 신호등·표지판을 구별하지만 어둠과 역광에 약합니다. 레이더는 전파로 거리와 속도를 재고 날씨에 강하지만 해상도가 낮습니다. 라이다는 레이저 펄스가 돌아오는 시간으로 3차원 지도를 만들지만 비용이 비싸고 안개·폭우에 약합니다. 그래서 여러 센서를 함께 쓰는 '센서 융합'을 합니다. 자율주행은 SAE 기준 0~5단계로 나뉩니다. 책 속 상황과 현재 기술 수준을 구분해서 말하세요.");
  txt(s, "교과서 개념: 센서, 정보의 수집과 처리", { x: 0.5, y: 1.2, w: 6, h: 0.3, fontSize: 12, bold: true, color: C.accent1 });
  // 흐름
  const flow = ["인식 (센서)", "판단 (알고리즘)", "제어 (구동)"];
  flow.forEach((f, i) => {
    const x = 0.5 + i * 3.1;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 1.6, w: 2.6, h: 0.5, rectRadius: 0.25, fill: { color: C.accent3 }, line: { color: C.accent3, width: 0 }, objectName: "flow" + (i + 1) });
    txt(s, f, { x, y: 1.6, w: 2.6, h: 0.5, fontSize: 14, bold: true, align: "center", valign: "middle" });
    if (i < 2) arrow(s, x + 2.65, 1.7, 0.4, 0.3, C.accent1);
  });
  const hdr = (t) => ({ text: t, options: { bold: true, color: C.text1, fill: { color: C.accent1 }, align: "center", valign: "middle", fontSize: 13 } });
  const cell = (t, o) => ({ text: t, options: Object.assign({ color: C.background1, fill: { color: C.text2 }, valign: "middle", fontSize: 13 }, o || {}) });
  s.addTable([
    [hdr("센서"), hdr("감지 방식"), hdr("강점"), hdr("약점")],
    [cell("카메라", { bold: true }), cell("빛(영상)"), cell("신호등·표지판 구별"), cell("어둠·역광에 약함")],
    [cell("레이더", { bold: true }), cell("전파"), cell("거리·속도, 날씨에 강함"), cell("해상도 낮음")],
    [cell("라이다", { bold: true }), cell("레이저 펄스"), cell("정밀한 3차원 지도"), cell("비용, 안개·폭우에 약함")],
  ], {
    x: 0.5, y: 2.35, w: 9.0, colW: [1.4, 2.0, 3.1, 2.5], rowH: 0.5,
    border: { type: "solid", color: C.text1, pt: 1 }, fontFace: FONT, margin: [0, 0.1, 0, 0.1],
  });
  txt(s, [
    { text: "센서 융합  ", options: { bold: true, color: C.accent4 } },
    { text: "서로의 약점을 보완하려고 여러 센서를 함께 쓴다.  자율주행은 Level 0~5로 구분한다.", options: {} },
  ], { x: 0.5, y: 4.55, w: 9.0, h: 0.5, fontSize: 14 });
}

// ================= 7. 감염병 진단 =================
{
  const s = content("원리 ③ 감염병은 검사와 데이터로 진단·예측한다", "원리",
    "「무접촉 사랑」은 감염병 이후의 비대면 사회와 AI 의료를 그립니다. PCR은 병원체의 유전물질을 온도 변화를 반복하며 증폭해서 검출하므로 정확하지만 시간이 걸리고 장비가 필요합니다. 항원 검사는 병원체 단백질에 항체가 결합하는 반응을 이용해 15~30분 안에 결과가 나오지만, 바이러스가 적으면 놓칠 수 있습니다. 예방 쪽에서는 확진·이동·접촉 데이터를 모델에 넣어 확산 추세를 예측하고, AI가 X선·CT 영상에서 이상 패턴을 찾아 진단을 돕습니다. 개인정보 보호 문제도 함께 말하세요. 책 속 내용과 교과서 내용은 구분해서 말하세요.");
  txt(s, "교과서 개념: 감염병의 진단과 예방", { x: 0.5, y: 1.2, w: 6, h: 0.3, fontSize: 12, bold: true, color: C.accent1 });
  const boxes = [
    { h: "PCR 검사", sub: "유전물질을 증폭해 검출", lines: ["온도 변화를 반복해 DNA를 복제", "정확도가 높음", "결과까지 시간이 걸리고 장비 필요"], color: C.accent2 },
    { h: "항원 검사", sub: "병원체 단백질을 항체로 검출", lines: ["항원-항체 결합 반응을 이용", "15~30분 안에 결과 확인", "바이러스가 적으면 놓칠 수 있음"], color: C.accent4 },
  ];
  boxes.forEach((b, i) => {
    const x = 0.5 + i * 4.6;
    card(s, x, 1.55, 4.4, 2.2, "card-test" + (i + 1));
    txt(s, b.h, { x: x + 0.25, y: 1.7, w: 3.9, h: 0.4, fontSize: 18, bold: true, color: b.color });
    txt(s, b.sub, { x: x + 0.25, y: 2.1, w: 3.9, h: 0.3, fontSize: 13, color: C.accent6 });
    txt(s, b.lines.map((t, k) => ({ text: t, options: { bullet: true, breakLine: k < b.lines.length - 1 } })), {
      x: x + 0.25, y: 2.5, w: 3.9, h: 1.15, fontSize: 14, paraSpaceAfter: 4,
    });
  });
  // 데이터 흐름
  txt(s, "데이터 기반 예방", { x: 0.5, y: 3.95, w: 3, h: 0.3, fontSize: 14, bold: true, color: C.accent1 });
  const f = ["확진·이동·접촉 데이터", "예측 모델", "확산 추세 · 방역 결정"];
  const fw = [2.9, 1.9, 2.7];
  let fx = 0.5;
  f.forEach((t, i) => {
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: fx, y: 4.3, w: fw[i], h: 0.55, rectRadius: 0.12, fill: { color: C.accent3 }, line: { color: C.accent3, width: 0 }, objectName: "data-flow" + (i + 1) });
    txt(s, t, { x: fx, y: 4.3, w: fw[i], h: 0.55, fontSize: 14, bold: true, align: "center", valign: "middle" });
    fx += fw[i];
    if (i < 2) { arrow(s, fx + 0.1, 4.45, 0.45, 0.25, C.accent1); fx += 0.65; }
  });
}

// ================= 8. 정리 표 =================
pres.addSection({ title: "정리" });
{
  const s = content("기술의 원리와 한계, 그리고 윤리", "정리",
    "세 소단원을 한 표로 정리합니다. 핵심은 기술이 만능이 아니라는 점입니다. 모든 기술에는 한계가 있고, 그 한계가 사회적 문제로 이어질 수 있습니다. 기술 자체는 중립이고 어떻게 쓸지는 사람이 정합니다.");
  const hdr = (t) => ({ text: t, options: { bold: true, color: C.text1, fill: { color: C.accent1 }, align: "center", valign: "middle", fontSize: 14 } });
  const cell = (t, o) => ({ text: t, options: Object.assign({ color: C.background1, fill: { color: C.text2 }, valign: "middle", fontSize: 13 }, o || {}) });
  s.addTable([
    [hdr("소단원"), hdr("핵심 원리"), hdr("한계"), hdr("윤리적 쟁점")],
    [cell("인공지능과 빅데이터", { bold: true }), cell("데이터로 패턴 학습\n(오차 줄이기)"), cell("데이터가 편향되면\n결과도 편향"), cell("차별, 개인정보,\n책임 소재")],
    [cell("센서와 자율 시스템", { bold: true }), cell("센서 수집 → 판단 → 제어"), cell("센서마다 약점이 있어\n융합 필요"), cell("사고가 났을 때\n책임은 누구에게?")],
    [cell("감염병 진단과 예방", { bold: true }), cell("검사 반응 + 데이터 예측"), cell("검사마다 정확도·\n속도가 다름"), cell("방역과 개인정보\n보호의 균형")],
  ], {
    x: 0.5, y: 1.4, w: 9.0, colW: [2.3, 2.5, 2.2, 2.0], rowH: [0.5, 0.85, 0.85, 0.85],
    border: { type: "solid", color: C.text1, pt: 1 }, fontFace: FONT, margin: [0, 0.1, 0, 0.1],
  });
  txt(s, "기술 자체는 중립이고, 어떻게 쓸지는 사람이 정한다.", { x: 0.5, y: 4.6, w: 9.0, h: 0.4, fontSize: 16, bold: true, color: C.accent4 });
}

// ================= 9. 소감 + 추천 =================
{
  const s = content("새롭게 알게 된 점과 추천 이유", "정리",
    "왼쪽 '새롭게 알게 된 점'은 예시 문장입니다. 본인이 실제로 느낀 점으로 바꿔서 말하세요. 추천 이유도 본인 생각에 맞게 고쳐도 좋습니다.");
  card(s, 0.5, 1.4, 4.4, 3.4, "card-learned");
  txt(s, "새롭게 알게 된 점", { x: 0.75, y: 1.55, w: 3.9, h: 0.4, fontSize: 18, bold: true, color: C.accent1 });
  txt(s, [
    { text: "AI는 '생각'하는 게 아니라 데이터 속 패턴을 찾는 것이라서, 데이터가 편향되면 결과도 편향된다.", options: { breakLine: true, paraSpaceAfter: 10 } },
    { text: "소설 속 기술의 상당수가 이미 개발되고 있다는 점이 놀라웠다.", options: {} },
  ], { x: 0.75, y: 2.1, w: 3.9, h: 2.6, fontSize: 14 });

  card(s, 5.1, 1.4, 4.4, 3.4, "card-reco");
  txt(s, "친구들에게 추천하는 이유", { x: 5.35, y: 1.55, w: 3.9, h: 0.4, fontSize: 18, bold: true, color: C.accent1 });
  const recos = [
    "소설이라 재미있고, 해설로 진짜 과학까지 배운다",
    "통합과학2 Ⅲ단원을 미리 공부하는 효과",
    "AI 시대에 꼭 고민할 윤리 문제를 던져 준다",
  ];
  recos.forEach((r, i) => {
    const y = 2.15 + i * 0.85;
    badge(s, 5.35, y, 0.42, String(i + 1), C.accent4, "reco-badge" + (i + 1));
    txt(s, r, { x: 5.95, y: y - 0.05, w: 3.35, h: 0.75, fontSize: 14, valign: "middle" });
  });
}

// ================= 10. 마무리 =================
{
  const s = pres.addSlide({ masterName: "TITLE_DARK", sectionTitle: "정리" });
  s.addText("2041년의 주인공은\nAI가 아니라 우리입니다", { placeholder: "title" });
  txt(s, "질문 있으신가요?", { x: 0.7, y: 3.5, w: 8.6, h: 0.5, fontSize: 22, bold: true, color: C.accent1 });
  txt(s, "참고: 카이푸 리·천치판, 『AI 2041』 / 통합과학2 교과서 Ⅲ단원", { x: 0.7, y: 4.7, w: 8.6, h: 0.3, fontSize: 12, color: C.accent6 });
  s.addNotes("마무리: 기술은 도구이고, 그 기술을 어떻게 만들고 쓸지는 우리가 정합니다. 질문을 받겠습니다.");
}

(async () => {
  const out = "/home/user/mingoon/deck_out/AI2041_발표.pptx";
  await pres.writeFile({ fileName: out });
  await applyTheme(out, THEME);
  console.log("wrote", out);
})();
