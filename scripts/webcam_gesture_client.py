from __future__ import annotations

import argparse
import time
from typing import Any

import cv2
import numpy as np
import requests


def post_json(url: str, payload: dict[str, Any]) -> dict[str, Any]:
    response = requests.post(url, json=payload, timeout=5)
    response.raise_for_status()
    return response.json()


def action_for_key(key: int, activity: str) -> tuple[str, str] | None:
    if key == ord("n"):
        return ("NEXT_SLIDE", "powerpoint") if activity == "presentation" else ("NEXT_TRACK", "media_player")
    if key == ord("b"):
        return ("PREVIOUS_SLIDE", "powerpoint") if activity == "presentation" else ("PREVIOUS_TRACK", "media_player")
    if key == ord(" "):
        return ("TOGGLE_PLAYBACK", "media_player")
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Local optical-flow gesture client")
    parser.add_argument("--api-url", default="http://127.0.0.1:8000/api/v1")
    parser.add_argument("--user-id", default="demo-user")
    parser.add_argument("--activity", choices=["presentation", "music"], default="presentation")
    parser.add_argument("--active-app", default=None)
    parser.add_argument("--camera", type=int, default=0)
    parser.add_argument("--threshold", type=float, default=1.4)
    args = parser.parse_args()

    active_app = args.active_app or ("PowerPoint" if args.activity == "presentation" else "Spotify")
    post_json(f"{args.api_url}/demo/bootstrap", {})

    capture = cv2.VideoCapture(args.camera)
    if not capture.isOpened():
        raise SystemExit("Camera could not be opened")

    previous_gray = None
    last_detection = 0.0
    latest_observation_id: str | None = None
    overlay = "Move one hand horizontally inside the guide"

    try:
        while True:
            ok, frame = capture.read()
            if not ok:
                break
            frame = cv2.flip(frame, 1)
            height, width = frame.shape[:2]
            x1, y1 = int(width * 0.18), int(height * 0.20)
            x2, y2 = int(width * 0.82), int(height * 0.82)
            roi = frame[y1:y2, x1:x2]
            gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(gray, (7, 7), 0)

            if previous_gray is not None:
                flow = cv2.calcOpticalFlowFarneback(
                    previous_gray, gray, None, 0.5, 3, 21, 3, 5, 1.2, 0
                )
                dx = float(np.median(flow[..., 0]))
                dy = float(np.median(flow[..., 1]))
                now = time.time()
                horizontal = abs(dx) > args.threshold and abs(dx) > (abs(dy) * 1.8)
                if horizontal and now - last_detection > 1.2:
                    direction = "right" if dx > 0 else "left"
                    payload = {
                        "user_id": args.user_id,
                        "context": {
                            "active_app": active_app,
                            "activity": args.activity,
                            "space": "camera_demo",
                            "device": "laptop",
                        },
                        "gesture": {
                            "motion_type": "swipe",
                            "direction": direction,
                            "duration_ms": 430,
                        },
                        "attempt_inference": True,
                    }
                    result = post_json(f"{args.api_url}/observe", payload)
                    latest_observation_id = result["observation"]["id"]
                    inference = result["inference"]
                    if inference["matched"]:
                        overlay = f"{direction} -> {inference['intent']} ({inference['confidence']:.0%})"
                    else:
                        overlay = f"Observed {direction}. Press N/B/Space to teach the next action."
                    print(overlay)
                    last_detection = now

            previous_gray = gray
            cv2.rectangle(frame, (x1, y1), (x2, y2), (104, 224, 255), 2)
            cv2.putText(frame, overlay[:85], (24, 38), cv2.FONT_HERSHEY_SIMPLEX, 0.62, (255, 255, 255), 2)
            cv2.putText(frame, "Q quit | N next | B previous | Space play/pause", (24, height - 24), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (220, 220, 220), 1)
            cv2.imshow("SilentOrchestra 2.0 - Local Optical Flow", frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break
            teaching = action_for_key(key, args.activity)
            if teaching and latest_observation_id:
                intent, target = teaching
                result = post_json(
                    f"{args.api_url}/teach",
                    {
                        "user_id": args.user_id,
                        "observation_id": latest_observation_id,
                        "action_type": intent,
                        "target": target,
                        "parameters": {},
                    },
                )
                overlay = f"Learning {intent}: {result['progress_current']}/{result['progress_required']}"
                if result.get("suggestion"):
                    overlay += " - suggestion ready in web UI"
                print(overlay)
                latest_observation_id = None
    finally:
        capture.release()
        cv2.destroyAllWindows()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
