const API = "/api/v1";
const USER_ID = "demo-user";

const contextDefinitions = {
  presentation: {
    title: "Presentation",
    app: "PowerPoint",
    appIcon: "P",
    meta: "Meeting room / Laptop",
    space: "meeting_room",
    actions: [
      { intent: "NEXT_SLIDE", target: "powerpoint" },
      { intent: "PREVIOUS_SLIDE", target: "powerpoint" },
      { intent: "START_PRESENTATION", target: "powerpoint" },
    ],
  },
  music: {
    title: "Music",
    app: "Spotify",
    appIcon: "S",
    meta: "Desk / Laptop",
    space: "desk",
    actions: [
      { intent: "NEXT_TRACK", target: "media_player" },
      { intent: "PREVIOUS_TRACK", target: "media_player" },
      { intent: "TOGGLE_PLAYBACK", target: "media_player" },
    ],
  },
};

const gestureSymbols = {
  "swipe:right": "→",
  "swipe:left": "←",
  "open_palm:none": "▢",
  "circle:clockwise": "○",
};

let currentContext = "presentation";
let lastObservation = null;
let lastGestureLabel = null;
let lastGestureSymbol = null;
let lastExecution = null;
let dashboardState = null;
let dashboardRequest = null;
let suggestionSignature = null;
let lastGestureButton = null;
// Filled from /demo/bootstrap so the labels have one source of truth.
let intentLabels = {};
let autoExecutionThreshold = 0.6;
let osActionsEnabled = false;
let demoModeEnabled = true;

const byId = (id) => document.getElementById(id);
const all = (selector, root = document) => root.querySelectorAll(selector);
const intentLabel = (intent) => intentLabels[intent] || intent;

async function request(path, options = {}) {
  const response = await fetch(`${API}${path}`, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  if (!response.ok) {
    let detail = `HTTP ${response.status}`;
    try {
      detail = (await response.json()).detail || detail;
    } catch (_) {
      // Keep the HTTP status when the response body is not JSON.
    }
    throw new Error(detail);
  }
  return response.status === 204 ? null : response.json();
}

const post = (path, body = {}) => request(path, {
  method: "POST",
  body: JSON.stringify(body),
});

// Disable the given controls while `task` runs. A control the task marked with
// its own data-state (e.g. "error") keeps it.
async function withBusy(controls, task) {
  const buttons = [...controls];
  buttons.forEach((button) => {
    button.disabled = true;
    button.dataset.state = "loading";
    button.setAttribute("aria-busy", "true");
  });
  try {
    return await task();
  } finally {
    buttons.forEach((button) => {
      button.disabled = false;
      button.removeAttribute("aria-busy");
      if (button.dataset.state === "loading") button.removeAttribute("data-state");
    });
  }
}

function showToast(message) {
  const toast = byId("toast");
  toast.textContent = message;
  toast.classList.add("visible");
  window.clearTimeout(showToast.timer);
  showToast.timer = window.setTimeout(() => toast.classList.remove("visible"), 2400);
}

function setAgentState(kind, title, description) {
  const orb = byId("agentOrb");
  orb.classList.remove("listening", "success");
  if (kind) orb.classList.add(kind);
  byId("agentStatus").textContent = kind === "listening"
    ? "제스처 관찰 중"
    : kind === "success" ? "의도 실행 완료" : "공간을 이해하는 중";
  byId("stageTitle").textContent = title;
  byId("stageDescription").textContent = description;
}

function renderContext() {
  const definition = contextDefinitions[currentContext];
  byId("contextTitle").textContent = definition.title;
  byId("activeApp").textContent = definition.app;
  byId("appIcon").textContent = definition.appIcon;
  byId("contextMeta").textContent = definition.meta;
  all(".segment").forEach((button) => {
    const isActive = button.dataset.context === currentContext;
    button.classList.toggle("active", isActive);
    button.setAttribute("aria-pressed", String(isActive));
  });
  renderActionButtons();
  renderInterpretations(dashboardState?.memories || []);
}

function renderActionButtons() {
  const host = byId("actionButtons");
  if (!lastObservation) {
    host.innerHTML = "";
    return;
  }
  host.innerHTML = contextDefinitions[currentContext].actions
    .map((action) => `<button class="action-button" type="button" data-intent="${action.intent}" data-target="${action.target}">${intentLabel(action.intent)}</button>`)
    .join("");
  all(".action-button", host).forEach((button) => {
    button.addEventListener("click", () => teachAction(button.dataset.intent, button.dataset.target));
  });
}

async function observeGesture(button) {
  const motion = button.dataset.motion;
  const direction = button.dataset.direction;
  lastGestureLabel = button.dataset.label;
  lastGestureSymbol = gestureSymbols[`${motion}:${direction}`] || "?";
  lastGestureButton = button;
  all(".gesture-button").forEach((item) => item.classList.remove("active"));
  button.classList.add("active");
  setAgentState(
    "listening",
    "동작을 관찰하고 있어요",
    "모션 특징과 현재 상황만 분석합니다. 원본 프레임은 저장하지 않습니다.",
  );

  await withBusy([button], async () => {
    try {
      const context = contextDefinitions[currentContext];
      const result = await post("/observe", {
        user_id: USER_ID,
        context: {
          active_app: context.app,
          activity: currentContext,
          space: context.space,
          device: "laptop",
        },
        gesture: { motion_type: motion, direction, duration_ms: 430 },
        attempt_inference: true,
      });
      lastObservation = result.observation;

      if (result.inference.matched) {
        lastExecution = result.inference.execution;
        const failed = result.inference.execution?.status === "FAILED";
        setAgentState(
          failed ? "" : "success",
          failed ? `${intentLabel(result.inference.intent)} 실행 실패` : intentLabel(result.inference.intent),
          failed ? executionError(result.inference.execution) : result.inference.reason,
        );
        showActionOverlay(result.inference);
        lastObservation = null;
        updateTeachingCard(
          failed ? "자동 실행 실패" : "자동 실행 완료",
          failed
            ? "의도는 추론했지만 동작을 전달하지 못했습니다. 아래 사유를 확인해 주세요."
            : "Agent가 현재 맥락과 개인 기억을 바탕으로 의도를 추론했습니다.",
        );
      } else {
        setAgentState(
          "",
          "다음 행동을 알려주세요",
          "몸짓 직후 실제로 하려던 행동을 선택하면 반복 패턴을 학습합니다.",
        );
        updateTeachingCard(`${lastGestureLabel} 관찰 완료`, "이 몸짓 직후 사용자가 한 행동을 선택해 주세요.");
        renderActionButtons();
      }
      await refreshDashboard();
    } catch (error) {
      showToast(`관찰 실패: ${error.message}`);
      button.dataset.state = "error";
      setAgentState("", "다시 시도해 주세요", "API 연결 상태와 서버 로그를 확인해 주세요.");
    }
  });
}

function updateTeachingCard(title, description) {
  byId("teachingTitle").textContent = title;
  byId("teachingDescription").textContent = description;
}

async function teachAction(intent, target) {
  if (!lastObservation) return;
  await withBusy(all(".action-button"), async () => {
    try {
      const result = await post("/teach", {
        user_id: USER_ID,
        observation_id: lastObservation.id,
        action_type: intent,
        target,
        parameters: {},
      });
      const label = intentLabel(intent);
      updateTeachingCard(
        `학습 진행 ${result.progress_current}/${result.progress_required}`,
        `${lastGestureLabel} → ${label} 연결성을 관찰했습니다.`,
      );
      setAgentState(
        "",
        `패턴을 학습하고 있어요 / ${result.progress_current}/${result.progress_required}`,
        "같은 상황에서 행동이 반복되면 먼저 제안하고, 승인 후에만 자동 실행합니다.",
      );
      if (result.suggestion?.status === "PENDING") {
        showToast("새로운 패턴을 발견했습니다. 기억 여부를 확인해 주세요.");
      }
      lastObservation = null;
      renderActionButtons();
      await refreshDashboard();
    } catch (error) {
      showToast(`학습 실패: ${error.message}`);
    }
  });
}

async function respondSuggestion(id, decision, modifiedIntent = null) {
  await withBusy(all("[data-decision]"), async () => {
    try {
      await post(`/suggestions/${id}/respond`, {
        decision,
        ...(modifiedIntent ? { modified_intent: modifiedIntent } : {}),
      });
      if (decision === "ACCEPTED" || decision === "MODIFIED") {
        setAgentState(
          "success",
          "새로운 몸짓 언어를 기억했어요",
          "이제 같은 상황에서 이 몸짓을 사용하면 Agent가 자동으로 실행합니다.",
        );
      }
      await refreshDashboard();
    } catch (error) {
      showToast(`제안 처리 실패: ${error.message}`);
    }
  });
}

const executionError = (execution) => execution?.error_message
  || "동작을 전달하지 못했습니다. 대상 앱과 실행 권한을 확인해 주세요.";

function showActionOverlay(inference) {
  const overlay = byId("actionOverlay");
  const failed = inference.execution?.status === "FAILED";
  overlay.dataset.status = failed ? "failed" : "success";
  byId("overlayGesture").textContent = failed ? "!" : (lastGestureSymbol || "?");
  byId("overlayAction").textContent = failed
    ? `${intentLabel(inference.intent)} 실행 실패`
    : intentLabel(inference.intent);
  byId("overlayConfidence").textContent =
    `${currentContext} / ${Math.round(inference.confidence * 100)}%`
    + (failed ? ` / ${executionError(inference.execution)}` : "");
  // ponytail: no auto-close timer - the feedback buttons live in here, and a
  // presenter narrating the execution needs longer than any timeout we'd pick.
  // Esc and a backdrop click already dismiss it.
  if (!overlay.open) overlay.showModal();
}

function closeActionOverlay() {
  const overlay = byId("actionOverlay");
  if (overlay.open) overlay.close();
}

const TUTORIAL_HIDE_KEY = "so_tutorial_hidden_until";
const TUTORIAL_SLIDE_COUNT = all(".tutorial-slide").length;
let tutorialSlideIndex = 0;

function todayKey() {
  return new Date().toLocaleDateString("en-CA");
}

function isTutorialHiddenToday() {
  try {
    return window.localStorage.getItem(TUTORIAL_HIDE_KEY) === todayKey();
  } catch (_) {
    return false;
  }
}

function renderTutorialSlide() {
  all(".tutorial-slide").forEach((slide, index) => {
    slide.hidden = index !== tutorialSlideIndex;
  });
  const dots = byId("tutorialDots");
  dots.innerHTML = Array.from({ length: TUTORIAL_SLIDE_COUNT }, (_, index) => (
    `<button class="tutorial-dot${index === tutorialSlideIndex ? " active" : ""}" type="button" data-slide-index="${index}" aria-label="${index + 1}단계로 이동"></button>`
  )).join("");
  all("[data-slide-index]", dots).forEach((dot) => {
    dot.addEventListener("click", () => {
      tutorialSlideIndex = Number(dot.dataset.slideIndex);
      renderTutorialSlide();
    });
  });
  const isLast = tutorialSlideIndex === TUTORIAL_SLIDE_COUNT - 1;
  byId("tutorialPrev").hidden = tutorialSlideIndex === 0;
  byId("tutorialNext").textContent = isLast ? "시작하기" : "다음";
}

function openTutorial() {
  tutorialSlideIndex = 0;
  byId("tutorialHideToday").checked = false;
  renderTutorialSlide();
  const overlay = byId("tutorialOverlay");
  if (!overlay.open) overlay.showModal();
}

function closeTutorial() {
  const overlay = byId("tutorialOverlay");
  if (overlay.open) overlay.close();
}

async function submitFeedback(type) {
  if (!lastExecution) return;
  await withBusy(all("[data-feedback]"), async () => {
    try {
      await post(`/executions/${lastExecution.id}/feedback`, {
        user_id: USER_ID,
        feedback_type: type,
      });
      closeActionOverlay();
      lastExecution = null;
      await refreshDashboard();
    } catch (error) {
      showToast(`피드백 실패: ${error.message}`);
    }
  });
}

function renderSuggestions(suggestions, candidates) {
  const host = byId("suggestionContent");
  const signature = JSON.stringify([suggestions, candidates, intentLabels]);
  if (signature === suggestionSignature) return;
  suggestionSignature = signature;
  if (!suggestions.length) {
    host.dataset.state = "empty";
    host.innerHTML = `<div class="empty-state"><span aria-hidden="true">—</span><p>같은 몸짓과 후속 행동이 3회 반복되면 Agent가 기억을 제안합니다.</p></div>`;
    return;
  }
  host.dataset.state = "pending";
  const suggestion = suggestions[0];
  const confidence = Math.round(suggestion.confidence * 100);
  const pattern = candidates.find((item) => item.id === suggestion.gesture_pattern_id);
  const intents = contextDefinitions[pattern?.context_scope]?.actions.map((action) => action.intent)
    || [suggestion.suggested_intent];
  const intentOptions = intents.map((intent) => (
    `<option value="${intent}" ${intent === suggestion.suggested_intent ? "selected" : ""}>${intentLabel(intent)}</option>`
  )).join("");
  host.innerHTML = `
    <div class="suggestion-card">
      <h3>이 몸짓을 “${intentLabel(suggestion.suggested_intent)}”로 기억할까요?</h3>
      <p>${suggestion.reason}</p>
      <div class="confidence-bar"><i style="width:${confidence}%"></i></div>
      <label class="suggestion-intent-label" for="modifiedIntent">수정할 의도</label>
      <select class="suggestion-intent-input" id="modifiedIntent">${intentOptions}</select>
      <div class="suggestion-actions">
        <button class="primary-button" type="button" data-decision="ACCEPTED">기억하기</button>
        <button class="secondary-button" type="button" data-decision="MODIFIED">수정</button>
        <button class="secondary-button" type="button" data-decision="REJECTED">아니요</button>
      </div>
    </div>`;
  all("[data-decision]", host).forEach((button) => {
    button.addEventListener("click", () => {
      const decision = button.dataset.decision;
      if (decision !== "MODIFIED") return respondSuggestion(suggestion.id, decision);
      const modifiedIntent = host.querySelector("#modifiedIntent").value;
      return respondSuggestion(suggestion.id, decision, modifiedIntent);
    });
  });
}

// FR-13 (auto demotion) has no dedicated event log on the backend - a
// CANDIDATE with observation_count already past the suggestion threshold can
// only have gotten there by being ACTIVE first, so we infer "demoted" rather
// than "still forming" from that alone. Best-effort, frontend-only signal.
function inferDemotionReason(candidate) {
  return candidate.negative_feedback_count > 0
    ? "부정 피드백 누적으로 신뢰도가 낮아져 대기 상태로 전환된 것으로 추정"
    : "다른 후속 행동과 판단이 엇갈려 대기 상태로 전환된 것으로 추정";
}

function renderMemories(memories, demoted = []) {
  const host = byId("memoryList");
  byId("memoryCount").textContent = memories.length;
  const memoryHtml = memories.map((memory) => {
    const confidence = Math.round(memory.confidence * 100);
    const symbol = gestureSymbols[memory.gesture_key] || "?";
    return `<article class="memory-item">
      <div class="memory-top">
        <span class="memory-symbol">${symbol}</span>
        <div><strong>${intentLabel(memory.intent)}</strong><small>${memory.motion_type} / ${memory.direction} / ${memory.observation_count} observations</small></div>
        <span class="context-chip">${memory.context_scope}</span>
      </div>
      <div class="memory-confidence"><span>${confidence}%</span><div class="bar"><i style="width:${confidence}%"></i></div></div>
    </article>`;
  }).join("");
  const demotedHtml = demoted.length ? `
    <div class="memory-demoted-heading">자동 강등 추정 (${demoted.length})</div>
    ${demoted.map((candidate) => {
      const confidence = Math.round(candidate.confidence * 100);
      const symbol = gestureSymbols[candidate.gesture_key] || "?";
      return `<article class="memory-item demoted">
        <div class="memory-top">
          <span class="memory-symbol">${symbol}</span>
          <div><strong>${intentLabel(candidate.intent)}</strong><small>${candidate.motion_type} / ${candidate.direction} / ${candidate.observation_count} observations</small></div>
          <span class="context-chip">${candidate.context_scope}</span>
        </div>
        <div class="memory-confidence"><span>${confidence}%</span><div class="bar"><i style="width:${confidence}%"></i></div></div>
        <p class="demoted-reason">${inferDemotionReason(candidate)}</p>
      </article>`;
    }).join("")}` : "";
  host.innerHTML = memoryHtml || demotedHtml
    ? memoryHtml + demotedHtml
    : `<div class="empty-state small"><p>아직 기억된 몸짓이 없습니다.</p></div>`;
}

function renderInterpretations(memories) {
  const host = byId("interpretationList");
  const filtered = memories.filter((memory) => memory.context_scope === currentContext);
  if (!filtered.length) {
    host.innerHTML = `<div class="empty-mini">이 상황에서 학습된 몸짓이 아직 없습니다.</div>`;
    return;
  }
  host.innerHTML = filtered.map((memory) => `
    <div class="interpretation-item">
      <span class="symbol">${gestureSymbols[memory.gesture_key] || "?"}</span>
      <div><strong>${memory.motion_type} / ${memory.direction}</strong><small>→ ${intentLabel(memory.intent)}</small></div>
      <em>${Math.round(memory.confidence * 100)}%</em>
    </div>`).join("");
}

function renderEvents(events) {
  const host = byId("eventList");
  if (!events.length) {
    host.innerHTML = `<div class="empty-mini">이벤트를 기다리는 중입니다.</div>`;
    return;
  }
  host.innerHTML = events.map((event) => {
    const date = new Date(event.time);
    const time = Number.isNaN(date.getTime()) ? "" : date.toLocaleTimeString("ko-KR", { hour: "2-digit", minute: "2-digit", second: "2-digit" });
    return `<div class="event-item" data-type="${event.type}" data-status="${event.status || ""}"><span class="event-dot"></span><div><strong>${intentLabel(event.title)}</strong><small>${event.detail}</small></div><time>${time}</time></div>`;
  }).join("");
}

const feedbackLabels = {
  CORRECT: "맞아요",
  WRONG_ACTION: "아니에요",
  ACCIDENTAL_GESTURE: "의도치 않은 몸짓",
  IGNORE: "무시",
};

function renderExecutionAudit(entries = []) {
  const host = byId("auditList");
  if (!entries.length) {
    host.innerHTML = `<div class="empty-mini">자동 실행된 기록이 아직 없습니다.</div>`;
    return;
  }
  host.innerHTML = entries.map((entry) => {
    const date = new Date(entry.executed_at);
    const time = Number.isNaN(date.getTime()) ? "" : date.toLocaleTimeString("ko-KR", { hour: "2-digit", minute: "2-digit", second: "2-digit" });
    const symbol = gestureSymbols[entry.gesture_key] || "?";
    const confidence = Math.round(entry.confidence * 100);
    const reason = entry.status === "FAILED"
      ? (entry.error_message || "동작을 전달하지 못했습니다.")
      : `${entry.context_scope} · ${entry.motion_type}/${entry.direction} · ${entry.execution_mode}`;
    const feedback = entry.feedback_type
      ? `<span class="audit-feedback" data-feedback="${entry.feedback_type}">${feedbackLabels[entry.feedback_type] || entry.feedback_type}</span>`
      : `<span>피드백 대기</span>`;
    return `<article class="audit-item" data-status="${entry.status}">
      <div class="audit-top">
        <span class="audit-symbol">${symbol}</span>
        <div><strong>${intentLabel(entry.intent)}</strong><small>${reason}</small></div>
        <span class="audit-confidence">${confidence}%</span>
      </div>
      <div class="audit-meta"><span>${time}</span>${feedback}</div>
    </article>`;
  }).join("");
}

async function refreshDashboard() {
  if (dashboardRequest) return dashboardRequest;
  dashboardRequest = loadDashboard();
  try {
    return await dashboardRequest;
  } finally {
    dashboardRequest = null;
  }
}

async function loadDashboard() {
  try {
  const state = await request(`/dashboard?user_id=${encodeURIComponent(USER_ID)}`);
  dashboardState = state;
  const fromWebcam = state.context?.space === "camera_demo";
  const modePill = byId("inputModePill");
  modePill.textContent = fromWebcam ? "웹캠 실시간 감지" : "버튼 시뮬레이션";
  modePill.dataset.source = fromWebcam ? "webcam" : "button";
  byId("metricObservations").textContent = state.counts.observations;
  byId("metricMemories").textContent = state.counts.learned_memories;
  byId("metricPending").textContent = state.counts.pending_suggestions;
  renderSuggestions(state.suggestions, state.candidates);
  // Exclude candidates still awaiting their first suggestion decision - only
  // ones that reached the threshold with no pending suggestion can only have
  // gotten there via a prior ACTIVE/rejected state, i.e. an actual demotion.
  const pendingPatternIds = new Set(state.suggestions.map((suggestion) => suggestion.gesture_pattern_id));
  const demoted = state.candidates.filter((candidate) => candidate.observation_count >= state.threshold
    && !pendingPatternIds.has(candidate.id));
  renderMemories(state.memories, demoted);
  renderInterpretations(state.memories);
  renderEvents(state.events);
  renderExecutionAudit(state.execution_audit);
  const candidate = state.candidates.find((item) => item.context_scope === currentContext);
  byId("learningProgress").textContent = candidate
    ? `${Math.min(candidate.observation_count, state.threshold)}/${state.threshold}`
    : `0/${state.threshold}`;
  byId("dashboardConnection").hidden = true;
  } catch (error) {
    byId("dashboardConnection").hidden = false;
    throw error;
  }
}

// The webcam client posts to the API directly, so state can change without any
// request from this tab. Poll while the tab is visible and idle.
// ponytail: polling, not SSE - one demo user, one tab, 3s is invisible here.
function startAutoRefresh() {
  const poll = () => {
    if (document.hidden) return;
    if (byId("actionOverlay").open) return;
    if (document.querySelector("[aria-busy='true']")) return;
    refreshDashboard().catch(() => {});
  };
  window.setInterval(poll, 3000);
  // Browsers throttle timers in a background tab, so catch up the moment the
  // tab is looked at again rather than waiting out the throttled interval.
  document.addEventListener("visibilitychange", poll);
}

async function resetDemo() {
  const button = byId("resetButton");
  button.textContent = "초기화 중…";
  await withBusy([button], async () => {
    try {
      await post("/demo/reset");
      lastObservation = null;
      lastExecution = null;
      updateTeachingCard("먼저 몸짓을 발생시켜 주세요", "학습 전에는 아무 동작도 자동 실행하지 않습니다.");
      setAgentState(
        "",
        "몸짓을 자연스럽게\n사용해 보세요",
        "별도의 제스처를 외울 필요가 없습니다. AI가 반복되는 행동과 맥락을 관찰합니다.",
      );
      renderActionButtons();
      await refreshDashboard();
    } catch (error) {
      showToast(`초기화 실패: ${error.message}`);
      button.dataset.state = "error";
    }
  });
  button.textContent = "초기화";
}

async function loadPrivacy() {
  try {
    const privacy = await request("/demo/privacy");
    const items = byId("privacyChecklist").children;
    const flags = [privacy.raw_video_stored, privacy.face_recognition_used, privacy.cloud_video_uploaded];
    flags.forEach((on, index) => {
      const label = items[index].firstChild;
      const value = items[index].querySelector("strong");
      label.textContent = label.textContent.trim();
      value.textContent = on ? "ON" : "OFF";
      value.dataset.on = String(on);
    });
    byId("privacyNote").textContent = `${privacy.processing_mode} — ${privacy.note}`;
  } catch (_) {
    // Keep the static OFF/OFF/OFF defaults baked into the markup.
  }
}

function applyBootstrapConfig(bootstrap) {
  intentLabels = bootstrap.intent_labels;
  autoExecutionThreshold = bootstrap.auto_execution_threshold;
  osActionsEnabled = bootstrap.os_actions_enabled;
  demoModeEnabled = bootstrap.demo_mode;

  const thresholdPct = Math.round(autoExecutionThreshold * 100);
  byId("memoryPanelDescription").textContent = `승인된 연결만 자동 실행합니다 (신뢰도 ${thresholdPct}% 이상).`;

  const osModeBadge = byId("osModeBadge");
  osModeBadge.textContent = osActionsEnabled ? "실제 키 입력 활성" : "시뮬레이션 모드";
  osModeBadge.dataset.live = String(osActionsEnabled);

  const resetButton = byId("resetButton");
  resetButton.disabled = !demoModeEnabled;
  resetButton.title = demoModeEnabled ? "" : "데모 모드가 아니어서 초기화를 사용할 수 없습니다.";
}

async function init() {
  try {
    applyBootstrapConfig(await post("/demo/bootstrap"));
    renderContext();
    await refreshDashboard();
  } catch (error) {
    showToast(`서버 연결 실패: ${error.message}`);
    byId("dashboardConnection").hidden = false;
  }
  loadPrivacy();

  startAutoRefresh();
  byId("retryDashboard").addEventListener("click", () => refreshDashboard().catch(() => {}));

  all(".segment").forEach((button) => {
    button.addEventListener("click", () => {
      currentContext = button.dataset.context;
      lastObservation = null;
      renderContext();
      refreshDashboard().catch(() => {});
      updateTeachingCard("상황이 변경되었습니다", `${contextDefinitions[currentContext].title} 맥락에서 몸짓을 관찰합니다.`);
      setAgentState(
        "",
        `${contextDefinitions[currentContext].title} 상황을 이해하고 있어요`,
        "같은 몸짓도 현재 앱과 행동에 따라 다른 의도로 해석합니다.",
      );
    });
  });
  all(".gesture-button").forEach((button) => {
    button.addEventListener("click", () => observeGesture(button));
  });
  byId("resetButton").addEventListener("click", resetDemo);
  all("[data-feedback]").forEach((button) => {
    button.addEventListener("click", () => submitFeedback(button.dataset.feedback));
  });
  byId("actionOverlay").addEventListener("click", (event) => {
    if (event.target.id !== "actionOverlay") return;
    const rect = event.currentTarget.getBoundingClientRect();
    const isOutside = event.clientX < rect.left || event.clientX > rect.right
      || event.clientY < rect.top || event.clientY > rect.bottom;
    if (isOutside) closeActionOverlay();
  });
  byId("actionOverlay").addEventListener("close", () => {
    lastGestureButton?.focus({ preventScroll: true });
  });

  byId("tutorialButton").addEventListener("click", openTutorial);
  byId("tutorialSkip").addEventListener("click", closeTutorial);
  byId("tutorialPrev").addEventListener("click", () => {
    tutorialSlideIndex = Math.max(0, tutorialSlideIndex - 1);
    renderTutorialSlide();
  });
  byId("tutorialNext").addEventListener("click", () => {
    if (tutorialSlideIndex === TUTORIAL_SLIDE_COUNT - 1) return closeTutorial();
    tutorialSlideIndex += 1;
    renderTutorialSlide();
  });
  byId("tutorialOverlay").addEventListener("click", (event) => {
    if (event.target.id !== "tutorialOverlay") return;
    const rect = event.currentTarget.getBoundingClientRect();
    const isOutside = event.clientX < rect.left || event.clientX > rect.right
      || event.clientY < rect.top || event.clientY > rect.bottom;
    if (isOutside) closeTutorial();
  });
  // Runs on every close path (button, backdrop click, Esc) so the checkbox
  // is honored even when the native dialog closes itself on Escape.
  byId("tutorialOverlay").addEventListener("close", () => {
    if (!byId("tutorialHideToday").checked) return;
    try {
      window.localStorage.setItem(TUTORIAL_HIDE_KEY, todayKey());
    } catch (_) {
      // Storage unavailable (e.g. private browsing) - just skip persisting.
    }
  });
  if (!isTutorialHiddenToday()) openTutorial();
}

document.addEventListener("DOMContentLoaded", init);
