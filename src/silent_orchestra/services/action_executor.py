from ..config import settings


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


def execute_action(intent: str) -> tuple[str, str, str | None]:
    if not settings.enable_os_actions:
        return "DRY_RUN", "SIMULATED", None

    key = KEY_MAP.get(intent)
    if key is None:
        return "OS", "FAILED", f"No operating-system key mapping for intent: {intent}"

    try:
        import pyautogui  # type: ignore[import-not-found]

        pyautogui.press(key)
        return "OS", "SUCCEEDED", None
    except Exception as exc:  # pragma: no cover - hardware/OS dependent
        return "OS", "FAILED", str(exc)
