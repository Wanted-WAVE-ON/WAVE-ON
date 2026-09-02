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
      { intent: "NEXT_SLIDE", target: "powerpoint", label: "다음 슬라이드" },
      { intent: "PREVIOUS_SLIDE", target: "powerpoint", label: "이전 슬라이드" },
      { intent: "START_PRESENTATION", target: "powerpoint", label: "발표 시작" },
    ],
  },
  music: {
    title: "Music",
    app: "Spotify",
    appIcon: "S",
    meta: "Desk / Laptop",
    space: "desk",
    actions: [
      { intent: "NEXT_TRACK", target: "media_player", label: "다음 트랙" },
      { intent: "PREVIOUS_TRACK", target: "media_player", label: "이전 트랙" },
      { intent: "TOGGLE_PLAYBACK", target: "media_player", label: "재생 / 일시정지" },
    ],
  },
};

const intentLabels = {
  NEXT_SLIDE: "다음 슬라이드",
  PREVIOUS_SLIDE: "이전 슬라이드",
  START_PRESENTATION: "발표 시작",
  END_PRESENTATION: "발표 종료",
  NEXT_TRACK: "다음 트랙",
  PREVIOUS_TRACK: "이전 트랙",
  TOGGLE_PLAYBACK: "재생 / 일시정지",
  VOLUME_UP: "볼륨 올리기",
  VOLUME_DOWN: "볼륨 낮추기",
  ZOOM_IN: "확대",
  ZOOM_OUT: "축소",
};

const gestureSymbols = {
  "swipe:right": ">>",
  "swipe:left": "<<",
  "open_palm:none": "[]",
  "circle:clockwise": "O",
};

let currentContext = "presentation";
let lastObservation = null;
let lastGestureLabel = null;
let lastGestureSymbol = null;
let lastExecution = null;
let dashboardState = null;
let overlayTimer = null;

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

function showToast(message) {
  const toast = document.getElementById("toast");
  toast.textContent = message;
  toast.classList.add("visible");
  window.clearTimeout(showToast.timer);
  showToast.timer = window.setTimeout(() => toast.classList.remove("visible"), 2400);
}

function setAgentState(kind, title, description) {
  const orb = document.getElementById("agentOrb");
  orb.classList.remove("listening", "success");
  if (kind) orb.classList.add(kind);
  document.getElementById("stageTitle").textContent = title;
  document.getElementById("stageDescription").textContent = description;
}

function renderContext() {
  const definition = contextDefinitions[currentContext];
  document.getElementById("contextTitle").textContent = definition.title;
  document.getElementById("activeApp").textContent = definition.app;
  document.getElementById("appIcon").textContent = definition.appIcon;
  document.getElementById("contextMeta").textContent = definition.meta;
  document.querySelectorAll(".segment").forEach((button) => {
    button.classList.toggle("active", button.dataset.context === currentContext);
  });
  renderActionButtons();
  renderInterpretations(dashboardState?.memories || []);
}

function renderActionButtons() {
  const host = document.getElementById("actionButtons");
  if (!lastObservation) {
    host.innerHTML = "";
    return;
  }
  host.innerHTML = contextDefinitions[currentContext].actions
    .map((action) => `<button class="action-button" type="button" data-intent="${action.intent}" data-target="${action.target}">${action.label}</button>`)
    .join("");
  host.querySelectorAll(".action-button").forEach((button) => {
    button.addEventListener("click", () => teachAction(button.dataset.intent, button.dataset.target));
  });
}

async function observeGesture(button) {
  const motion = button.dataset.motion;
  const direction = button.dataset.direction;
  lastGestureLabel = button.dataset.label;
  lastGestureSymbol = gestureSymbols[`${motion}:${direction}`] || "?";
  document.querySelectorAll(".gesture-button").forEach((item) => item.classList.remove("active"));
  button.classList.add("active");
  button.disabled = true;
  setAgentState(
    "listening",
    "동작을 관찰하고 있어요",
    "모션 특징과 현재 상황만 분석합니다. 원본 프레임은 저장하지 않습니다.",
  );

  try {
    const context = contextDefinitions[currentContext];
    const result = await request("/observe", {
      method: "POST",
      body: JSON.stringify({
        user_id: USER_ID,
        context: {
          active_app: context.app,
          activity: currentContext,
          space: context.space,
          device: "laptop",
        },
        gesture: { motion_type: motion, direction, duration_ms: 430 },
        attempt_inference: true,
      }),
    });
    lastObservation = result.observation;

    if (result.inference.matched) {
      lastExecution = result.inference.execution;
      setAgentState("success", `${intentLabels[result.inference.intent] || result.inference.intent}`, result.inference.reason);
      showActionOverlay(result.inference);
      lastObservation = null;
      updateTeachingCard("자동 실행 완료", "Agent가 현재 맥락과 개인 기억을 바탕으로 의도를 추론했습니다.");
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
    setAgentState("", "다시 시도해 주세요", "API 연결 상태와 서버 로그를 확인해 주세요.");
  } finally {
    button.disabled = false;
  }
}

function updateTeachingCard(title, description) {
  document.getElementById("teachingTitle").textContent = title;
  document.getElementById("teachingDescription").textContent = description;
}

async function teachAction(intent, target) {
  if (!lastObservation) return;
  document.querySelectorAll(".action-button").forEach((button) => {
    button.disabled = true;
  });
  try {
    const result = await request("/teach", {
      method: "POST",
      body: JSON.stringify({
        user_id: USER_ID,
        observation_id: lastObservation.id,
        action_type: intent,
        target,
        parameters: {},
      }),
    });
    const label = intentLabels[intent] || intent;
    updateTeachingCard(
      `학습 진행 ${result.progress_current}/${result.progress_required}`,
      `${lastGestureLabel} -> ${label} 연결성을 관찰했습니다.`,
    );
    setAgentState(
      "",
      `패턴을 학습하고 있어요 / ${result.progress_current}/${result.progress_required}`,
      "같은 상황에서 행동이 반복되면 먼저 제안하고, 승인 후에만 자동 실행합니다.",
    );
    if (result.suggestion?.status === "PENDING") {
      showToast("새로운 패턴을 발견했습니다. 기억 여부를 확인해 주세요.");
    } else {
      showToast(`${lastGestureLabel}와 ${label}의 관계를 관찰했습니다.`);
    }
    lastObservation = null;
    renderActionButtons();
    await refreshDashboard();
  } catch (error) {
    showToast(`학습 실패: ${error.message}`);
  } finally {
    document.querySelectorAll(".action-button").forEach((button) => {
      button.disabled = false;
    });
  }
}

async function respondSuggestion(id, decision) {
  try {
    const result = await request(`/suggestions/${id}/respond`, {
      method: "POST",
      body: JSON.stringify({ decision }),
    });
    if (decision === "ACCEPTED") {
      showToast("개인 제스처 기억을 저장했습니다.");
      setAgentState(
        "success",
        "새로운 몸짓 언어를 기억했어요",
        "이제 같은 상황에서 이 몸짓을 사용하면 Agent가 자동으로 실행합니다.",
      );
    } else {
      showToast("제안이 거절되었습니다. 자동 실행하지 않습니다.");
    }
    await refreshDashboard();
    return result;
  } catch (error) {
    showToast(`제안 처리 실패: ${error.message}`);
  }
}

function showActionOverlay(inference) {
  const overlay = document.getElementById("actionOverlay");
  document.getElementById("overlayGesture").textContent = lastGestureSymbol || "?";
  document.getElementById("overlayAction").textContent = intentLabels[inference.intent] || inference.intent;
  document.getElementById("overlayConfidence").textContent = `Learned gesture / ${Math.round(inference.confidence * 100)}%`;
  overlay.classList.add("visible");
  window.clearTimeout(overlayTimer);
  overlayTimer = window.setTimeout(() => overlay.classList.remove("visible"), 5200);
}

async function submitFeedback(type) {
  if (!lastExecution) return;
  try {
    const result = await request(`/executions/${lastExecution.id}/feedback`, {
      method: "POST",
      body: JSON.stringify({ user_id: USER_ID, feedback_type: type }),
    });
    document.getElementById("actionOverlay").classList.remove("visible");
    showToast(type === "CORRECT" ? "정확한 실행으로 기록했습니다." : "수정 피드백을 반영해 확신도를 낮췄습니다.");
    lastExecution = null;
    await refreshDashboard();
    return result;
  } catch (error) {
    showToast(`피드백 실패: ${error.message}`);
  }
}

function renderSuggestions(suggestions) {
  const host = document.getElementById("suggestionContent");
  if (!suggestions.length) {
    host.innerHTML = `<div class="empty-state"><span>...</span><p>같은 몸짓과 후속 행동이 3회 반복되면 Agent가 기억을 제안합니다.</p></div>`;
    return;
  }
  const suggestion = suggestions[0];
  const confidence = Math.round(suggestion.confidence * 100);
  host.innerHTML = `
    <div class="suggestion-card">
      <h4>이 몸짓을 '${intentLabels[suggestion.suggested_intent] || suggestion.suggested_intent}'로 기억할까요?</h4>
      <p>${suggestion.reason}</p>
      <div class="confidence-bar"><i style="width:${confidence}%"></i></div>
      <div class="suggestion-actions">
        <button class="primary-button" type="button" data-decision="ACCEPTED">기억하기</button>
        <button class="secondary-button" type="button" data-decision="REJECTED">아니요</button>
      </div>
    </div>`;
  host.querySelectorAll("[data-decision]").forEach((button) => {
    button.addEventListener("click", () => respondSuggestion(suggestion.id, button.dataset.decision));
  });
}

function renderMemories(memories) {
  const host = document.getElementById("memoryList");
  document.getElementById("memoryCount").textContent = memories.length;
  if (!memories.length) {
    host.innerHTML = `<div class="empty-state small"><p>아직 기억된 몸짓이 없습니다.</p></div>`;
    return;
  }
  host.innerHTML = memories.map((memory) => {
    const confidence = Math.round(memory.confidence * 100);
    const symbol = gestureSymbols[memory.gesture_key] || "?";
    return `<article class="memory-item">
      <div class="memory-top">
        <span class="memory-symbol">${symbol}</span>
        <div><strong>${intentLabels[memory.intent] || memory.intent}</strong><small>${memory.motion_type} / ${memory.direction} / ${memory.observation_count} observations</small></div>
        <span class="context-chip">${memory.context_scope}</span>
      </div>
      <div class="memory-confidence"><span>${confidence}%</span><div class="bar"><i style="width:${confidence}%"></i></div></div>
    </article>`;
  }).join("");
}

function renderInterpretations(memories) {
  const host = document.getElementById("interpretationList");
  const filtered = memories.filter((memory) => memory.context_scope === currentContext);
  if (!filtered.length) {
    host.innerHTML = `<div class="empty-mini">이 상황에서 학습된 몸짓이 아직 없습니다.</div>`;
    return;
  }
  host.innerHTML = filtered.map((memory) => `
    <div class="interpretation-item">
      <span class="symbol">${gestureSymbols[memory.gesture_key] || "?"}</span>
      <div><strong>${memory.motion_type} / ${memory.direction}</strong><small>-> ${intentLabels[memory.intent] || memory.intent}</small></div>
      <em>${Math.round(memory.confidence * 100)}%</em>
    </div>`).join("");
}

function renderEvents(events) {
  const host = document.getElementById("eventList");
  if (!events.length) {
    host.innerHTML = `<div class="empty-mini">이벤트를 기다리는 중입니다.</div>`;
    return;
  }
  host.innerHTML = events.map((event) => {
    const date = new Date(event.time);
    const time = Number.isNaN(date.getTime()) ? "" : date.toLocaleTimeString("ko-KR", { hour: "2-digit", minute: "2-digit", second: "2-digit" });
    return `<div class="event-item" data-type="${event.type}"><span class="event-dot"></span><div><strong>${intentLabels[event.title] || event.title}</strong><small>${event.detail}</small></div><time>${time}</time></div>`;
  }).join("");
}

async function refreshDashboard() {
  const state = await request(`/dashboard?user_id=${encodeURIComponent(USER_ID)}`);
  dashboardState = state;
  document.getElementById("metricObservations").textContent = state.counts.observations;
  document.getElementById("metricMemories").textContent = state.counts.learned_memories;
  document.getElementById("metricPending").textContent = state.counts.pending_suggestions;
  renderSuggestions(state.suggestions);
  renderMemories(state.memories);
  renderInterpretations(state.memories);
  renderEvents(state.events);
}

async function resetDemo() {
  const button = document.getElementById("resetButton");
  button.disabled = true;
  try {
    await request("/demo/reset", { method: "POST", body: "{}" });
    lastObservation = null;
    lastExecution = null;
    updateTeachingCard("먼저 몸짓을 발생시켜 주세요", "학습 전에는 아무 동작도 자동 실행하지 않습니다.");
    setAgentState(
      "",
      "몸짓을 자연스럽게 사용해 보세요",
      "별도의 제스처를 외울 필요가 없습니다. AI가 반복되는 행동과 맥락을 관찰합니다.",
    );
    renderActionButtons();
    await refreshDashboard();
    showToast("데모 데이터를 초기화했습니다.");
  } catch (error) {
    showToast(`초기화 실패: ${error.message}`);
  } finally {
    button.disabled = false;
  }
}

async function init() {
  try {
    await request("/demo/bootstrap", { method: "POST", body: "{}" });
    renderContext();
    await refreshDashboard();
  } catch (error) {
    showToast(`서버 연결 실패: ${error.message}`);
  }

  document.querySelectorAll(".segment").forEach((button) => {
    button.addEventListener("click", () => {
      currentContext = button.dataset.context;
      lastObservation = null;
      renderContext();
      updateTeachingCard("상황이 변경되었습니다", `${contextDefinitions[currentContext].title} 맥락에서 몸짓을 관찰합니다.`);
      setAgentState(
        "",
        `${contextDefinitions[currentContext].title} 상황을 이해하고 있어요`,
        "같은 몸짓도 현재 앱과 행동에 따라 다른 의도로 해석합니다.",
      );
    });
  });
  document.querySelectorAll(".gesture-button").forEach((button) => {
    button.addEventListener("click", () => observeGesture(button));
  });
  document.getElementById("resetButton").addEventListener("click", resetDemo);
  document.querySelectorAll("[data-feedback]").forEach((button) => {
    button.addEventListener("click", () => submitFeedback(button.dataset.feedback));
  });
  document.getElementById("actionOverlay").addEventListener("click", (event) => {
    if (event.target.id === "actionOverlay") event.currentTarget.classList.remove("visible");
  });
}

document.addEventListener("DOMContentLoaded", init);
