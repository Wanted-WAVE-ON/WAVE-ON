from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..config import settings


@dataclass(slots=True)
class ExecutionResult:
    mode: str
    status: str
    error_message: str | None = None


KEY_MAP = {
    "NEXT_SLIDE": "right",
    "PREVIOUS_SLIDE": "left",
    "START_PRESENTATION": "f5",
    "END_PRESENTATION": "esc",
    "NEXT_TRACK": "nexttrack",
    "PREVIOUS_TRACK": "prevtrack",
    "TOGGLE_PLAYBACK": "playpause",
    "VOLUME_UP": "volumeup",
    "VOLUME_DOWN": "volumedown",
    "ZOOM_IN": "+",
    "ZOOM_OUT": "-",
}


def execute_action(intent: str, _target: str, _parameters: dict[str, Any]) -> ExecutionResult:
    if not settings.enable_os_actions:
        return ExecutionResult(mode="DRY_RUN", status="SIMULATED")

    key = KEY_MAP.get(intent)
    if key is None:
        return ExecutionResult(
            mode="OS",
            status="FAILED",
            error_message=f"No operating-system key mapping for intent: {intent}",
        )

    try:
        import pyautogui  # type: ignore[import-not-found]

        pyautogui.press(key)
        return ExecutionResult(mode="OS", status="SUCCEEDED")
    except Exception as exc:  # pragma: no cover - hardware/OS dependent
        return ExecutionResult(mode="OS", status="FAILED", error_message=str(exc))
