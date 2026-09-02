from __future__ import annotations

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

TARGET_DEFAULTS = {
    "presentation": "powerpoint",
    "music": "media_player",
    "browser": "browser",
    "other": "local_device",
}


def action_label(intent: str) -> str:
    return ACTION_LABELS.get(intent, intent.replace("_", " ").title())
