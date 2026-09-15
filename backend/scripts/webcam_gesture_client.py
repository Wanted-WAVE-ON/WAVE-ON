import argparse
import math
import platform
import sys
import time
from typing import Any

import requests


def post_json(url: str, payload: dict[str, Any]) -> dict[str, Any]:
    response = requests.post(url, json=payload, timeout=5)
    response.raise_for_status()
    return response.json()


KEY_ACTIONS = {
    ("n", "presentation"): ("NEXT_SLIDE", "powerpoint"),
    ("n", "music"): ("NEXT_TRACK", "media_player"),
    ("b", "presentation"): ("PREVIOUS_SLIDE", "powerpoint"),
    ("b", "music"): ("PREVIOUS_TRACK", "media_player"),
    (" ", "music"): ("TOGGLE_PLAYBACK", "media_player"),
}

TEACH_WINDOW_SECONDS = 5.0
CAMERA_WARMUP_READS = 10

# open_palm: how much of the ROI the background subtractor must flag as
# foreground, and how little further change is allowed, before a held-up
# palm (not a swipe in progress) counts as detected; re-arms once lowered.
PALM_COVERAGE_RATIO = 0.35
PALM_STILL_ENERGY = 1.5
PALM_RESET_RATIO = 0.15
PALM_STABLE_FRAMES = 5

# circle: the foreground centroid must stay in a plausible "one hand moving"
# coverage band, and its trajectory must sweep most of a full turn within a
# bounded window, before a loop counts as detected.
CIRCLE_MIN_RATIO = 0.02
CIRCLE_MAX_RATIO = 0.5
CIRCLE_WINDOW_SECONDS = 2.6
CIRCLE_GAP_SECONDS = 0.5
CIRCLE_MIN_RADIUS_RATIO = 0.04
CIRCLE_MIN_ROTATION = math.pi * 1.6


class CameraOpenError(RuntimeError):
    """No requested capture backend delivered a usable frame."""


def valid_camera_frame(frame) -> bool:
    import numpy as np

    return (
        isinstance(frame, np.ndarray)
        and frame.size > 0
        and frame.ndim == 3
        and frame.shape[2] in (3, 4)
    )


def open_camera(cv2, index: int = 0, backend: str = "auto"):
    """Return the capture, its first usable frame, and the selected backend.

    Opening a device is not enough: some Windows backends report success but
    never deliver an image. Release each failed candidate before trying another.
    Reads are bounded in number; a stalled native driver can still block a read.
    """
    candidates = [backend]
    if backend == "auto":
        candidates = ["dshow", "msmf"] if platform.system() == "Windows" else ["default"]
    failures = []
    for candidate in candidates:
        capture = None
        ready = False
        reason = "device could not be opened"
        try:
            if candidate == "default":
                capture = cv2.VideoCapture(index)
            else:
                backend_id = getattr(cv2, f"CAP_{candidate.upper()}", None)
                if backend_id is None:
                    failures.append(f"{candidate}: backend is unavailable in this OpenCV build")
                    continue
                capture = cv2.VideoCapture(index, backend_id)
            if capture.isOpened():
                for attempt in range(CAMERA_WARMUP_READS):
                    ok, frame = capture.read()
                    if ok and valid_camera_frame(frame):
                        ready = True
                        return capture, frame, index, candidate
                    if attempt + 1 < CAMERA_WARMUP_READS:
                        time.sleep(0.05)
                reason = f"frame read failed after {CAMERA_WARMUP_READS} attempts"
        except (cv2.error, OSError) as error:
            reason = f"capture failed ({error})"
        finally:
            if capture is not None and not ready:
                try:
                    capture.release()
                except (cv2.error, OSError) as error:
                    reason += f"; release failed ({error})"
        failures.append(f"{candidate}: {reason}")
    raise CameraOpenError(f"camera {index}: " + "; ".join(failures))


def action_for_key(key: int, activity: str) -> tuple[str, str] | None:
    return KEY_ACTIONS.get((chr(key), activity))


def make_input_observer():
    """Isolated so tests inject a fake and never install a real keyboard hook."""
    from silent_orchestra.services.input_observer import WindowsInputObserver

    return WindowsInputObserver()


def horizontal_motion(flow, foreground_mask, threshold=1.0, min_motion_ratio=0.01):
    """Aggregate only moving foreground pixels; never retain image data.

    Returns ``(direction, moving_ratio, mean_dx)`` so the caller can accumulate
    the swipe amplitude without touching pixel data a second time.
    """
    import numpy as np

    dx, dy = flow[..., 0], flow[..., 1]
    mask = (np.abs(dx) > threshold) & foreground_mask & np.isfinite(dx) & np.isfinite(dy)
    ratio = float(np.mean(mask))
    if ratio <= min_motion_ratio:
        return None, ratio, 0.0
    mean_dx, mean_dy = float(np.mean(dx[mask])), float(np.mean(dy[mask]))
    if abs(mean_dx) <= 0.3 or abs(mean_dx) <= abs(mean_dy):
        return None, ratio, mean_dx
    return ("right" if mean_dx > 0 else "left"), ratio, mean_dx


def foreground_centroid(mask) -> tuple[float, float] | None:
    """Unweighted centroid of the foreground mask, in ROI pixel coordinates."""
    import numpy as np

    ys, xs = np.nonzero(mask)
    if xs.size == 0:
        return None
    return float(np.mean(xs)), float(np.mean(ys))


def foreground_motion_energy(dx, dy, mask) -> float:
    """Mean optical-flow magnitude restricted to the foreground: near zero
    means whatever tripped the background subtractor is currently held still."""
    import numpy as np

    if not np.any(mask):
        return 0.0
    return float(np.mean(np.abs(dx[mask])) + np.mean(np.abs(dy[mask])))


def track_open_palm(coverage_ratio: float, motion_energy: float,
                     stable_count: int, active: bool) -> tuple[bool, int, bool]:
    """A palm filling the ROI shows as (a) large background-subtractor coverage
    and (b) little further change once it is held still. Returns
    (detected, next_stable_count, next_active); ``active`` must round-trip
    through the caller so a held palm does not keep re-firing every frame,
    and only re-arms once coverage drops (the hand is lowered)."""
    filling = coverage_ratio >= PALM_COVERAGE_RATIO
    still = motion_energy <= PALM_STILL_ENERGY
    stable_count = stable_count + 1 if filling and still else 0
    if coverage_ratio < PALM_RESET_RATIO:
        active = False
    if active or stable_count < PALM_STABLE_FRAMES:
        return False, stable_count, active
    return True, stable_count, True


def compute_circle_rotation(samples: list[tuple[float, float, float]]) -> tuple[float, float]:
    """Sum the signed angle a moving blob's centroid sweeps around its own
    trajectory's centre; a full loop (either sense) means "circle". ``samples``
    are (x, y, t) in ROI pixel coordinates; returns (rotation_radians, mean_radius)."""
    if len(samples) < 4:
        return 0.0, 0.0
    cx = sum(x for x, _, _ in samples) / len(samples)
    cy = sum(y for _, y, _ in samples) / len(samples)
    rotation = 0.0
    radius_sum = 0.0
    previous_angle = None
    for x, y, _ in samples:
        px, py = x - cx, y - cy
        radius_sum += math.hypot(px, py)
        angle = math.atan2(py, px)
        if previous_angle is not None:
            delta = angle - previous_angle
            if delta > math.pi:
                delta -= 2 * math.pi
            if delta < -math.pi:
                delta += 2 * math.pi
            rotation += delta
        previous_angle = angle
    return rotation, radius_sum / len(samples)


def circle_features(radius: float, rotation: float, duration_s: float, roi_width: int) -> tuple[float, float]:
    """ROI-relative radius (amplitude) and rotation rate in rad/s (speed), clamped to the API range."""
    amplitude = min(radius / max(roi_width, 1), 10.0)
    speed = min(abs(rotation) / duration_s, 10.0) if duration_s > 0 else 0.0
    return round(speed, 4), round(amplitude, 4)


def measured_features(dx_pixels: float, duration_seconds: float, roi_width: int) -> tuple[float, float]:
    """ROI-relative amplitude (widths) and speed (widths/second), clamped to the API range."""
    span = max(roi_width, 1)
    amplitude = min(abs(dx_pixels) / span, 10.0)
    speed = min(amplitude / duration_seconds, 10.0) if duration_seconds > 0 else 0.0
    return round(speed, 4), round(amplitude, 4)


def select_observed_teach(events, pending):
    """First real key in the same activity inside the window; None once it expires.

    ``events`` arrive in observation order, so a first event past the window means
    every later one is too. Only the first match is linked (SPEC L-9).
    """
    _, obs_activity, obs_ts = pending
    for event in events:
        if event.observed_at - obs_ts > TEACH_WINDOW_SECONDS:
            return None
        if event.activity == obs_activity:
            return event
    return None


# Mirrors the browser client's CONFIRM_GESTURES vocabulary (frontend/app.js) so
# both real-input paths teach and match against the same gesture_key space.
GESTURE_DIRECTIONS = {
    "swipe": {"left", "right"},
    "open_palm": {"none"},
    "circle": {"clockwise"},
}


def observation_payload(user_id, activity, active_app, direction, *,
                        motion_type="swipe", duration_ms=430, speed=None, amplitude=None,
                        attempt_inference=True):
    if direction not in GESTURE_DIRECTIONS.get(motion_type, ()):
        raise ValueError(f"Unsupported direction {direction!r} for motion_type {motion_type!r}")
    if (speed is None) != (amplitude is None):
        raise ValueError("speed and amplitude must be provided together")
    context: dict[str, Any] = {"space": "camera_demo", "device": "laptop"}
    if activity is not None:
        context["activity"] = activity
    if active_app is not None:
        context["active_app"] = active_app
    gesture: dict[str, Any] = {
        "motion_type": motion_type, "direction": direction, "duration_ms": duration_ms,
    }
    if speed is not None:
        gesture["speed"] = speed
        gesture["amplitude"] = amplitude
    return {
        "user_id": user_id,
        "context": context,
        "gesture": gesture,
        "attempt_inference": attempt_inference,
    }


def _teach(api_url, user_id, observation_id, action_type, target) -> str:
    result = post_json(
        f"{api_url}/teach",
        {"user_id": user_id, "observation_id": observation_id,
         "action_type": action_type, "target": target, "parameters": {}},
    )
    overlay = f"Learning {action_type}: {result['progress_current']}/{result['progress_required']}"
    if result.get("suggestion"):
        overlay += " - suggestion ready in web UI"
    return overlay


def _detect_and_report(api_url, user_id, request_activity, active_app, motion_type, direction,
                       duration_ms, speed, amplitude, input_mode, learn, now) -> tuple[str, tuple | None]:
    """POST one detected gesture, shared by the swipe/open_palm/circle branches.

    Returns (overlay_text, pending_teach); pending_teach is None once the
    Agent already matched a memory, otherwise it is armed for select_observed_teach
    or the labels-mode key handler, anchored at ``now`` (detection time, not
    response time).
    """
    payload = observation_payload(
        user_id, request_activity, active_app, direction,
        motion_type=motion_type, duration_ms=duration_ms, speed=speed, amplitude=amplitude,
        attempt_inference=not learn,
    )
    result = post_json(f"{api_url}/observe", payload)
    observation_id = result["observation"]["id"]
    resolved_activity = result["context"]["activity"]
    inference = result["inference"]
    label = f"{motion_type}:{direction}"
    if inference["matched"]:
        return f"{label} -> {inference['intent']} ({inference['confidence']:.0%})", None
    if input_mode == "observe":
        return (
            f"Observed {label} in {resolved_activity}. "
            f"Use your usual key in the app within {int(TEACH_WINDOW_SECONDS)}s."
        ), (observation_id, resolved_activity, now)
    teach_keys = "N/B/Space" if resolved_activity == "music" else "N/B"
    return f"Observed {label}. Press {teach_keys} to teach the next action.", (observation_id, resolved_activity, now)


def main() -> int:

    parser = argparse.ArgumentParser(description="Local optical-flow gesture client")
    parser.add_argument("--api-url", default="http://127.0.0.1:8000/api/v1")
    parser.add_argument("--user-id", default="demo-user")
    parser.add_argument("--input-mode", choices=["observe", "labels"], default="observe",
                        help="observe real app keys (Windows) or label the next action by hand")
    parser.add_argument("--activity", choices=["auto", "presentation", "music"], default="auto",
                        help="auto resolves the activity from the active app; a value is a manual override")
    parser.add_argument("--learn", action="store_true",
                        help="disable inference so approved memories do not auto-execute while (re)learning")
    parser.add_argument("--active-app", default=None,
                        help="labels mode only: metadata override for the recorded app name")
    parser.add_argument("--camera", type=int, default=0,
                        help="camera index (default: 0); choose the physical camera explicitly if needed")
    parser.add_argument("--camera-backend", choices=["auto", "dshow", "msmf", "default"], default="auto",
                        help="auto tries DirectShow then Media Foundation on Windows; default elsewhere")
    parser.add_argument("--check-camera", action="store_true",
                        help="check the first camera frame without the API server, keyboard hook, or preview")
    parser.add_argument("--threshold", type=float, default=1.0,
                        help="per-pixel horizontal flow magnitude that counts as motion")
    parser.add_argument("--min-motion-ratio", type=float, default=0.01,
                        help="fraction of ROI pixels in motion required to trigger a detection")
    parser.add_argument("--stable-frames", type=int, default=3,
                        help="consecutive frames that must agree on direction")
    args = parser.parse_args()

    if not math.isfinite(args.threshold) or args.threshold <= 0:
        parser.error("--threshold must be finite and greater than zero")
    if not 0 < args.min_motion_ratio <= 1:
        parser.error("--min-motion-ratio must be in (0, 1]")
    if args.stable_frames < 1:
        parser.error("--stable-frames must be at least 1")
    if args.camera < 0:
        parser.error("--camera must be zero or greater")
    if not args.check_camera and args.input_mode == "labels" and args.activity == "auto":
        parser.error("--input-mode labels needs an explicit --activity (presentation or music)")
    if not args.check_camera and args.input_mode == "observe" and platform.system() != "Windows":
        parser.error("--input-mode observe needs Windows; use --input-mode labels on this platform")
    if not args.check_camera and args.input_mode == "observe" and args.active_app:
        parser.error("--input-mode observe reads the real active window; --active-app is labels only")

    simulation_url = args.api_url.split("/api/")[0]
    if not args.check_camera:
        print(f"Stable Simulation: open {simulation_url} in your browser. Q exits the camera.")
    try:
        import cv2
        import numpy as np
    except ImportError:
        print('Camera dependencies missing. Install: python -m pip install -e "./backend[camera]"', file=sys.stderr)
        return 1

    request_activity = None if args.activity == "auto" else args.activity
    if args.input_mode == "labels":
        # Labels mode never reads the OS; the recorded app name is metadata only.
        active_app = args.active_app or ("PowerPoint" if args.activity == "presentation" else "Spotify")
        key_help = "Q quit | N next | B previous"
        if args.activity == "music":
            key_help += " | Space play/pause"
    else:
        # Observe mode: the server reads its own active window, and the real keys
        # you press in the app are what get linked. No spoofing here.
        active_app = None
        key_help = "Q quit | use your usual keys in the app"

    capture = None
    observer = None
    preview_started = False
    previous_gray = None
    direction_history: list[str] = []
    last_detection = 0.0
    detection_count = 0
    pending_teach: tuple[str, str, float] | None = None
    segment_start = 0.0
    segment_dx = 0.0
    palm_stable_count = 0
    palm_active = False
    palm_started_at = 0.0
    circle_samples: list[tuple[float, float, float]] = []
    overlay = "Move one hand horizontally, hold your palm open, or draw a circle inside the guide"

    try:
        capture, first_frame, selected_index, selected_backend = open_camera(cv2, args.camera, args.camera_backend)
        height, width = first_frame.shape[:2]
        print(f"Camera frame received: index={selected_index}, backend={selected_backend}, frame={width}x{height}.")
        if args.check_camera:
            return 0
        if args.input_mode == "observe":
            try:
                observer = make_input_observer()
                observer.start()
            except OSError as error:
                print(f"Real input observation could not start ({error}). Use --input-mode labels. Stable Simulation above.", file=sys.stderr)
                return 1
        background_model = cv2.createBackgroundSubtractorMOG2(
            history=120, varThreshold=25, detectShadows=False
        )
        post_json(f"{args.api_url}/demo/bootstrap", {})
        while True:
            if first_frame is not None:
                frame, first_frame = first_frame, None
            else:
                ok, frame = capture.read()
                if not ok or not valid_camera_frame(frame):
                    print("Camera frame read failed. Use --check-camera to recheck the device. Stable Simulation above.", file=sys.stderr)
                    return 1
            frame = cv2.flip(frame, 1)
            height, width = frame.shape[:2]
            x1, y1 = int(width * 0.18), int(height * 0.20)
            x2, y2 = int(width * 0.82), int(height * 0.82)
            roi_width = x2 - x1
            roi = frame[y1:y2, x1:x2]
            gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(gray, (7, 7), 0)

            if previous_gray is not None:
                flow = cv2.calcOpticalFlowFarneback(
                    previous_gray, gray, None, 0.5, 3, 21, 3, 5, 1.2, 0
                )
                # A moving hand only occupies a fraction of the ROI, so a median
                # over every pixel washes out to ~0. Look at the pixels that are
                # actually in motion instead.
                dx = flow[..., 0]
                dy = flow[..., 1]
                foreground_mask = background_model.apply(gray) > 0
                direction, moving_ratio, mean_dx = horizontal_motion(
                    flow, foreground_mask, args.threshold, args.min_motion_ratio
                )
                now = time.monotonic()
                ready = now - last_detection >= 1.2

                if direction and ready:
                    if not direction_history:
                        # Start of a swipe segment: time it and its amplitude.
                        segment_start = now
                        segment_dx = 0.0
                    direction_history.append(direction)
                    direction_history = direction_history[-args.stable_frames:]
                    segment_dx += abs(mean_dx)
                else:
                    direction_history.clear()

                # open_palm and circle share the cooldown gate with swipe so the
                # three detectors never fire on the same instant; checked first,
                # like the browser client, since both are multi-frame holds/loops
                # a mid-swipe hand should not accidentally complete.
                palm_hit = False
                if ready:
                    coverage_ratio = float(np.mean(foreground_mask))
                    was_stable = palm_stable_count > 0
                    palm_stable_count, palm_active, palm_hit = track_open_palm(
                        coverage_ratio, foreground_motion_energy(dx, dy, foreground_mask),
                        palm_stable_count, palm_active,
                    )
                    if palm_stable_count == 1 and not was_stable:
                        palm_started_at = now
                else:
                    palm_stable_count = 0

                circle_hit = None
                if ready and not palm_hit:
                    centroid = foreground_centroid(foreground_mask)
                    if centroid is not None and CIRCLE_MIN_RATIO <= coverage_ratio <= CIRCLE_MAX_RATIO:
                        circle_samples.append((centroid[0], centroid[1], now))
                    elif circle_samples and now - circle_samples[-1][2] > CIRCLE_GAP_SECONDS:
                        circle_samples = []
                    circle_samples = [s for s in circle_samples if now - s[2] <= CIRCLE_WINDOW_SECONDS]
                    rotation, radius = compute_circle_rotation(circle_samples)
                    if radius / max(roi_width, 1) >= CIRCLE_MIN_RADIUS_RATIO and abs(rotation) >= CIRCLE_MIN_ROTATION:
                        circle_hit = (rotation, radius, now - circle_samples[0][2])
                elif not ready:
                    circle_samples = []

                if palm_hit:
                    detection_count += 1
                    duration_ms = max(1, int(min(now - palm_started_at, 10.0) * 1000))
                    print(f"DETECTED: open_palm (coverage={coverage_ratio:.2f}) #{detection_count}")
                    overlay, pending_teach = _detect_and_report(
                        args.api_url, args.user_id, request_activity, active_app,
                        "open_palm", "none", duration_ms, None, None,
                        args.input_mode, args.learn, now,
                    )
                    print(overlay)
                    last_detection = now
                    direction_history.clear()
                    circle_samples = []
                elif circle_hit:
                    rotation, radius, duration_s = circle_hit
                    speed, amplitude = circle_features(radius, rotation, duration_s, roi_width)
                    duration_ms = max(1, int(min(duration_s, 10.0) * 1000))
                    detection_count += 1
                    print(
                        f"DETECTED: circle:clockwise (radius={radius:.1f}px, "
                        f"rotation={math.degrees(rotation):.0f}deg, speed={speed:.2f}rad/s) #{detection_count}"
                    )
                    overlay, pending_teach = _detect_and_report(
                        args.api_url, args.user_id, request_activity, active_app,
                        "circle", "clockwise", duration_ms, speed, amplitude,
                        args.input_mode, args.learn, now,
                    )
                    print(overlay)
                    last_detection = now
                    direction_history.clear()
                    circle_samples = []
                    palm_stable_count = 0
                elif (
                    len(direction_history) == args.stable_frames
                    and len(set(direction_history)) == 1
                ):
                    max_abs_dx = float(np.max(np.abs(dx)))
                    direction = direction_history[-1]
                    direction_history.clear()
                    detection_count += 1
                    duration_s = max(now - segment_start, 1e-3)
                    duration_ms = int(min(duration_s, 10.0) * 1000)
                    speed, amplitude = measured_features(segment_dx, duration_s, roi_width)
                    print(
                        f"DETECTED: {direction} "
                        f"(max|dx|={max_abs_dx:.2f}, moving_ratio={moving_ratio:.1%}, "
                        f"speed={speed:.2f}w/s, amp={amplitude:.2f}w) #{detection_count}"
                    )
                    overlay, pending_teach = _detect_and_report(
                        args.api_url, args.user_id, request_activity, active_app,
                        "swipe", direction, duration_ms, speed, amplitude,
                        args.input_mode, args.learn, now,
                    )
                    print(overlay)
                    last_detection = now
                    circle_samples = []
                    palm_stable_count = 0

            previous_gray = gray

            if observer is not None and pending_teach is not None:
                try:
                    events = observer.drain()
                except OSError as error:
                    print(f"Real input observer stopped ({error}). Use --input-mode labels. Stable Simulation above.", file=sys.stderr)
                    return 1
                chosen = select_observed_teach(events, pending_teach)
                if chosen is not None:
                    overlay = _teach(
                        args.api_url, args.user_id, pending_teach[0],
                        chosen.action_type, chosen.target,
                    )
                    print(overlay)
                    pending_teach = None
            if pending_teach is not None and time.monotonic() - pending_teach[2] > TEACH_WINDOW_SECONDS:
                pending_teach = None

            cv2.rectangle(frame, (x1, y1), (x2, y2), (104, 224, 255), 2)
            cv2.putText(frame, overlay[:85], (24, 38), cv2.FONT_HERSHEY_SIMPLEX, 0.62, (255, 255, 255), 2)
            cv2.putText(frame, f"detections: {detection_count}", (24, 66), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (104, 224, 255), 2)
            cv2.putText(frame, key_help, (24, height - 24), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (220, 220, 220), 1)
            preview_started = True
            cv2.imshow("SilentOrchestra 2.0 - Local Optical Flow", frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break
            if args.input_mode == "labels" and pending_teach is not None:
                teaching = action_for_key(key, pending_teach[1])
                if teaching:
                    intent, target = teaching
                    overlay = _teach(args.api_url, args.user_id, pending_teach[0], intent, target)
                    print(overlay)
                    pending_teach = None
    except CameraOpenError as error:
        print(
            f"Camera could not be opened: {error}. Select the physical camera with --camera INDEX; check camera permissions and other camera apps. "
            "Browser label simulation is the stable fallback: open the browser UI and use Stable Simulation above.",
            file=sys.stderr,
        )
        return 1
    except (requests.RequestException, ValueError, KeyError, TypeError) as error:
        print(f"API request/response failed ({type(error).__name__}). No frames saved. Check the API server; --check-camera tests the camera separately. Use Stable Simulation above.", file=sys.stderr)
        return 1
    except cv2.error:
        print("Camera processing/display failed. Check camera permissions and display support. Use Stable Simulation above.", file=sys.stderr)
        return 1
    finally:
        if observer is not None:
            try:
                observer.stop()
            except OSError as error:
                print(f"Real input observer cleanup failed ({error}).", file=sys.stderr)
        if capture is not None:
            try:
                capture.release()
            except (cv2.error, OSError) as error:
                print(f"Camera cleanup failed ({error}).", file=sys.stderr)
        if preview_started:
            try:
                cv2.destroyAllWindows()
            except cv2.error as error:
                print(f"Camera display cleanup failed ({error}).", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
