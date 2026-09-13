ACTION_LABELS = {
    "NEXT_SLIDE": "다음 슬라이드",
    "PREVIOUS_SLIDE": "이전 슬라이드",
    "START_PRESENTATION": "발표 시작",
    "END_PRESENTATION": "발표 종료",
    "NEXT_TRACK": "다음 트랙",
    "PREVIOUS_TRACK": "이전 트랙",
    "TOGGLE_PLAYBACK": "재생/일시정지",
    "VOLUME_UP": "볼륨 올리기",
    "VOLUME_DOWN": "볼륨 낮추기",
    "ZOOM_IN": "확대",
    "ZOOM_OUT": "축소",
}

# Intents where "how much", not just "which one", is meaningful - the only
# ones a gesture's measured amplitude is allowed to scale (SPEC C-5 gap: a
# single discrete intent per (gesture, context) can't otherwise carry a
# magnitude). NEXT/PREVIOUS_SLIDE stay single-step so navigation stays predictable.
SCALABLE_INTENTS = {"VOLUME_UP", "VOLUME_DOWN", "ZOOM_IN", "ZOOM_OUT"}

CONTEXT_INTENTS = {
    "presentation": {
        "NEXT_SLIDE",
        "PREVIOUS_SLIDE",
        "START_PRESENTATION",
        "END_PRESENTATION",
        "ZOOM_IN",
        "ZOOM_OUT",
    },
    "music": {
        "NEXT_TRACK",
        "PREVIOUS_TRACK",
        "TOGGLE_PLAYBACK",
        "VOLUME_UP",
        "VOLUME_DOWN",
    },
}


def action_label(intent: str) -> str:
    return ACTION_LABELS.get(intent, intent.replace("_", " ").title())
