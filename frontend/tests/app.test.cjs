const { test } = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const path = require('node:path');
const source = fs.readFileSync(path.join(__dirname, '../app.js'), 'utf8');
function app(fetch) {
  const elements = new Map();
  const element = id => {
    if (!elements.has(id)) elements.set(id, {textContent: '', innerHTML: '', dataset: {}, hidden: true,
      open: false, showModal() { this.open = true; }, querySelectorAll: () => []});
    return elements.get(id);
  };
  const context = vm.createContext({fetch, document: {getElementById: element, addEventListener() {}, querySelectorAll: () => []}, window: {}});
  vm.runInContext(source, context);
  return {element, run: code => vm.runInContext(code, context)};
}
const state = {counts: {observations: 2, learned_memories: 0, pending_suggestions: 0},
  suggestions: [], memories: [], events: [], threshold: 3,
  candidates: [{context_scope: 'presentation', observation_count: 2}]};
test('dashboard failure remains visible until recovery and displays external 2/3 progress', async () => {
  let failed = true;
  const ui = app(async () => { if (failed) throw Error('offline'); return {ok: true, status: 200, json: async () => state}; });
  await assert.rejects(ui.run('refreshDashboard()'));
  assert.equal(ui.element('dashboardConnection').hidden, false);
  failed = false;
  await ui.run('refreshDashboard()');
  assert.equal(ui.element('dashboardConnection').hidden, true);
  assert.equal(ui.element('learningProgress').textContent, '2/3');
});
test('concurrent refresh shares one request; unchanged suggestions preserve user edits', async () => {
  let calls = 0;
  const ui = app(async () => { calls++; return {ok: true, status: 200, json: async () => state}; });
  await Promise.all([ui.run('refreshDashboard()'), ui.run('refreshDashboard()')]);
  assert.equal(calls, 1);
  ui.element('suggestionContent').innerHTML = 'user selection';
  await ui.run('refreshDashboard()');
  assert.equal(ui.element('suggestionContent').innerHTML, 'user selection');
});
test('FAILED overlay includes error, context and confidence without success status', () => {
  const ui = app();
  ui.run(`showActionOverlay({intent:'NEXT_SLIDE', confidence:0.9, execution:{status:'FAILED', error_message:'blocked'}})`);
  assert.equal(ui.element('actionOverlay').dataset.status, 'failed');
  assert.match(ui.element('overlayConfidence').textContent, /presentation.*90%.*blocked/);
});

function syntheticFrame(width, height, blockX) {
  const frame = new Uint8ClampedArray(width * height * 4);
  for (let offset = 3; offset < frame.length; offset += 4) frame[offset] = 255;
  for (let y = 18; y < 34; y++) {
    for (let x = blockX; x < blockX + 16; x++) {
      const offset = ((y * width) + x) * 4;
      frame[offset] = frame[offset + 1] = frame[offset + 2] = 230;
    }
  }
  return frame;
}

test('browser camera motion analysis identifies horizontal movement without retaining frames', () => {
  const ui = app();
  const width = 96;
  const height = 54;
  const motion = ui.run(`detectHorizontalMotion(${JSON.stringify([...syntheticFrame(width, height, 28)])}, ${JSON.stringify([...syntheticFrame(width, height, 32)])}, ${width}, ${height})`);
  assert.equal(motion.direction, 'right');
  assert.equal(ui.run(`detectHorizontalMotion(${JSON.stringify([...syntheticFrame(width, height, 28)])}, ${JSON.stringify([...syntheticFrame(width, height, 28)])}, ${width}, ${height})`), null);
});

test('analyzeMotionField reports the ratio and centroid of the pixels that changed', () => {
  const ui = app();
  const width = 96;
  const height = 54;
  const field = ui.run(`analyzeMotionField(${JSON.stringify([...syntheticFrame(width, height, 28)])}, ${JSON.stringify([...syntheticFrame(width, height, 60)])}, ${width}, ${height}, 20)`);
  assert.ok(field.ratio > 0);
  assert.ok(field.centroidX > 27 && field.centroidX < 76);
  assert.equal(ui.run(`analyzeMotionField(null, ${JSON.stringify([...syntheticFrame(width, height, 28)])}, ${width}, ${height}, 20)`), null);
});

test('camera open-palm tracker needs a sustained still, frame-filling object and re-arms once it leaves', () => {
  const ui = app();
  const filling = { ratio: 0.5 };
  const still = { ratio: 0.01 };
  for (let i = 0; i < 4; i += 1) {
    assert.equal(ui.run(`trackOpenPalm(${JSON.stringify(filling)}, ${JSON.stringify(still)}, ${i})`), null);
  }
  const detected = ui.run(`trackOpenPalm(${JSON.stringify(filling)}, ${JSON.stringify(still)}, 4)`);
  assert.equal(detected.coverage, 0.5);
  // Continuing to hold the palm up must not keep re-firing every frame.
  assert.equal(ui.run(`trackOpenPalm(${JSON.stringify(filling)}, ${JSON.stringify(still)}, 5)`), null);
  // Lowering the hand drops background coverage and re-arms detection.
  ui.run(`trackOpenPalm(${JSON.stringify({ ratio: 0.05 })}, ${JSON.stringify(still)}, 6)`);
  for (let i = 0; i < 4; i += 1) ui.run(`trackOpenPalm(${JSON.stringify(filling)}, ${JSON.stringify(still)}, ${i})`);
  assert.ok(ui.run(`trackOpenPalm(${JSON.stringify(filling)}, ${JSON.stringify(still)}, 4)`));
});

test('camera circle tracker recognizes a full loop of the moving centroid but not a quarter turn', () => {
  const ui = app();
  const pointAt = (fraction) => ({
    ratio: 0.05,
    centroidX: 40 + (Math.cos(fraction * Math.PI * 2) * 10),
    centroidY: 30 + (Math.sin(fraction * Math.PI * 2) * 10),
  });
  let result = null;
  for (let i = 0; i <= 3; i += 1) {
    result = ui.run(`trackCircleMotion(${JSON.stringify(pointAt(i / 12))}, ${i * 100})`);
  }
  assert.equal(result, null);
  for (let i = 4; i <= 11; i += 1) {
    result = ui.run(`trackCircleMotion(${JSON.stringify(pointAt(i / 12))}, ${i * 100})`);
  }
  assert.ok(result);
  assert.equal(result.durationMs, 1100);
});
