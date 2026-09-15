from scripts.webcam_gesture_client import action_for_key


def test_space_only_teaches_playback_in_music_context():
    assert action_for_key(ord(" "), "music") == ("TOGGLE_PLAYBACK", "media_player")
    assert action_for_key(ord(" "), "presentation") is None


import math
import sys
from types import SimpleNamespace

import pytest
import requests
from scripts import webcam_gesture_client as webcam
from silent_orchestra.services.input_observer import ObservedAction


@pytest.fixture
def np():
    return pytest.importorskip("numpy")


@pytest.mark.parametrize("direction,dx", [("right", 2), ("left", -2)])
def test_only_moving_pixels_determine_direction(direction, dx, np):
    flow = np.zeros((100, 100, 2))
    flow[:2, :, 0] = dx
    assert webcam.horizontal_motion(flow, np.ones((100, 100), dtype=bool)) == (direction, 0.02, float(dx))


@pytest.mark.parametrize("dx,dy,foreground", [(0, 0, True), (2, 3, True), (2, 0, False)])
def test_static_vertical_and_background_motion_are_ignored(dx, dy, foreground, np):
    flow = np.empty((10, 10, 2))
    flow[:] = (dx, dy)
    assert webcam.horizontal_motion(flow, np.full((10, 10), foreground))[0] is None


def test_small_motion_is_ignored(np):
    flow = np.zeros((100, 100, 2))
    flow[0, 0, 0] = 5
    assert webcam.horizontal_motion(flow, np.ones((100, 100), dtype=bool))[0] is None


def test_measured_features_are_roi_relative_and_clamped():
    assert webcam.measured_features(320, 0.5, 640) == (1.0, 0.5)
    fast, big = webcam.measured_features(100_000, 0.001, 640)
    assert fast == 10.0 and big == 10.0
    assert webcam.measured_features(0.0, 0.0, 640) == (0.0, 0.0)


def test_foreground_centroid_and_motion_energy_ignore_empty_masks(np):
    mask = np.zeros((10, 10), dtype=bool)
    mask[2:4, 6:8] = True
    assert webcam.foreground_centroid(mask) == (6.5, 2.5)
    assert webcam.foreground_centroid(np.zeros((10, 10), dtype=bool)) is None

    dx = np.zeros((10, 10))
    dy = np.zeros((10, 10))
    dx[mask] = 3.0
    dy[mask] = 4.0
    assert webcam.foreground_motion_energy(dx, dy, mask) == pytest.approx(7.0)
    assert webcam.foreground_motion_energy(dx, dy, np.zeros((10, 10), dtype=bool)) == 0.0


def test_open_palm_needs_sustained_still_coverage_and_rearms_once_lowered():
    stable_count, active = 0, False
    for _ in range(webcam.PALM_STABLE_FRAMES - 1):
        detected, stable_count, active = webcam.track_open_palm(0.5, 0.1, stable_count, active)
        assert detected is False
    detected, stable_count, active = webcam.track_open_palm(0.5, 0.1, stable_count, active)
    assert detected is True and active is True
    # Holding the palm up must not keep re-firing every frame.
    detected, stable_count, active = webcam.track_open_palm(0.5, 0.1, stable_count, active)
    assert detected is False
    # Lowering the hand drops coverage below the reset ratio and re-arms detection.
    detected, stable_count, active = webcam.track_open_palm(0.05, 0.1, stable_count, active)
    assert detected is False and active is False
    for _ in range(webcam.PALM_STABLE_FRAMES - 1):
        detected, stable_count, active = webcam.track_open_palm(0.5, 0.1, stable_count, active)
    detected, stable_count, active = webcam.track_open_palm(0.5, 0.1, stable_count, active)
    assert detected is True


def test_open_palm_ignores_motion_thats_not_held_still():
    stable_count, active = 0, False
    for _ in range(10):
        detected, stable_count, active = webcam.track_open_palm(0.5, 5.0, stable_count, active)
        assert detected is False and stable_count == 0


def test_circle_rotation_recognizes_a_full_loop_but_not_a_quarter_turn():
    def point_at(fraction):
        angle = fraction * math.tau
        return (40 + (math.cos(angle) * 10), 30 + (math.sin(angle) * 10), fraction)

    quarter = [point_at(i / 12) for i in range(4)]
    rotation, radius = webcam.compute_circle_rotation(quarter)
    assert abs(rotation) < webcam.CIRCLE_MIN_ROTATION

    full_loop = [point_at(i / 12) for i in range(12)]
    rotation, radius = webcam.compute_circle_rotation(full_loop)
    assert abs(rotation) >= webcam.CIRCLE_MIN_ROTATION
    assert radius == pytest.approx(10.0, abs=0.5)


def test_circle_features_are_roi_relative_and_clamped():
    speed, amplitude = webcam.circle_features(radius=64, rotation=math.pi, duration_s=1.0, roi_width=640)
    assert amplitude == pytest.approx(0.1)
    assert speed == pytest.approx(math.pi, abs=1e-4)
    assert webcam.circle_features(radius=0, rotation=0, duration_s=0, roi_width=640) == (0.0, 0.0)
    fast, big = webcam.circle_features(radius=100_000, rotation=100.0, duration_s=0.001, roi_width=640)
    assert fast == 10.0 and big == 10.0


def test_observation_payload_validates_direction_against_motion_type():
    palm = webcam.observation_payload("demo-user", "music", None, "none", motion_type="open_palm")
    assert palm["gesture"] == {"motion_type": "open_palm", "direction": "none", "duration_ms": 430}
    circle = webcam.observation_payload(
        "demo-user", "music", None, "clockwise", motion_type="circle", speed=1.2, amplitude=0.3
    )
    assert circle["gesture"]["motion_type"] == "circle"
    with pytest.raises(ValueError):
        webcam.observation_payload("demo-user", "music", None, "right", motion_type="open_palm")
    with pytest.raises(ValueError):
        webcam.observation_payload("demo-user", "music", None, "clockwise", motion_type="swipe")


def test_feature_payload_carries_measured_motion(client):
    client.post("/api/v1/demo/bootstrap")
    payload = webcam.observation_payload(
        "demo-user", "music", "Spotify", "right", duration_ms=380, speed=0.4, amplitude=0.15
    )
    assert payload["gesture"] == {
        "motion_type": "swipe", "direction": "right",
        "duration_ms": 380, "speed": 0.4, "amplitude": 0.15,
    }
    assert set(payload) == {"user_id", "context", "gesture", "attempt_inference"}
    response = client.post("/api/v1/observe", json=payload)
    assert response.status_code == 200
    observation = response.json()["observation"]
    assert observation["gesture_key"] == "swipe:right"
    assert observation["frame_stored"] is False
    assert len(observation["gesture_embedding"]) == 11


def test_auto_context_payload_omits_activity_and_app():
    payload = webcam.observation_payload("demo-user", None, None, "right", speed=0.4, amplitude=0.15)
    assert "activity" not in payload["context"] and "active_app" not in payload["context"]
    assert payload["attempt_inference"] is True


def _observed(activity="presentation", at=0.0, action="NEXT_SLIDE", target="powerpoint"):
    return ObservedAction(action, target, activity, "PowerPoint Slide Show", at)


def test_observe_link_takes_first_real_key_in_the_same_activity():
    pending = ("obs-1", "presentation", 100.0)
    events = [
        _observed("music", 100.4, "NEXT_TRACK", "media_player"),
        _observed("presentation", 101.0),
        _observed("presentation", 101.5, "PREVIOUS_SLIDE"),
    ]
    chosen = webcam.select_observed_teach(events, pending)
    assert (chosen.action_type, chosen.target) == ("NEXT_SLIDE", "powerpoint")


def test_observe_link_ignores_keys_after_the_window():
    pending = ("obs-1", "presentation", 100.0)
    late = _observed("presentation", 100.0 + webcam.TEACH_WINDOW_SECONDS + 0.1)
    assert webcam.select_observed_teach([late], pending) is None


def test_observe_link_requires_a_matching_activity():
    pending = ("obs-1", "presentation", 100.0)
    other = _observed("music", 100.2, "NEXT_TRACK", "media_player")
    assert webcam.select_observed_teach([other], pending) is None


@pytest.mark.parametrize("argv", [
    ["webcam", "--input-mode", "labels", "--activity", "auto"],
    ["webcam", "--input-mode", "observe", "--active-app", "PowerPoint"],
])
def test_incompatible_flag_combinations_are_rejected(monkeypatch, argv):
    monkeypatch.setattr(sys, "argv", argv)
    with pytest.raises(SystemExit) as exit_info:
        webcam.main()
    assert exit_info.value.code == 2


@pytest.mark.parametrize("opened,read_ok,api_error", [(False, False, False), (True, False, False), (True, True, True)])
def test_failure_releases_camera_and_offers_simulation(monkeypatch, capsys, opened, read_ok, api_error, np):
    released = []
    frame = np.zeros((10, 10, 3), dtype=np.uint8) if read_ok else None
    capture = SimpleNamespace(isOpened=lambda: opened, read=lambda: (read_ok, frame), release=lambda: released.append(True))
    fake_cv = SimpleNamespace(VideoCapture=lambda _: capture, createBackgroundSubtractorMOG2=lambda **_: None,
                              destroyAllWindows=lambda: None, error=RuntimeError)
    monkeypatch.setitem(sys.modules, "cv2", fake_cv)
    monkeypatch.setattr(sys, "argv", ["webcam", "--input-mode", "labels", "--activity", "presentation",
                                     "--camera", "0", "--camera-backend", "default"])
    monkeypatch.setattr(webcam.time, "sleep", lambda _: None)
    def post(*_):
        if api_error:
            raise requests.ConnectionError("offline")
        return {}
    monkeypatch.setattr(webcam, "post_json", post)
    assert webcam.main() == 1
    assert released == [True]
    output = capsys.readouterr()
    assert "Stable Simulation" in output.out
    assert "failed" in output.err or "could not be opened" in output.err


def test_open_failure_points_to_browser_label_simulation(monkeypatch, capsys, np):
    released = []
    capture = SimpleNamespace(isOpened=lambda: False, read=lambda: (False, None), release=lambda: released.append(True))
    fake_cv = SimpleNamespace(VideoCapture=lambda _: capture, createBackgroundSubtractorMOG2=lambda **_: None,
                              destroyAllWindows=lambda: None, error=RuntimeError)
    monkeypatch.setitem(sys.modules, "cv2", fake_cv)
    monkeypatch.setattr(sys, "argv", ["webcam", "--input-mode", "labels", "--activity", "presentation",
                                     "--camera", "0", "--camera-backend", "default"])
    monkeypatch.setattr(webcam, "post_json", lambda *_: {})

    assert webcam.main() == 1
    assert released == [True]
    output = capsys.readouterr()
    assert "Stable Simulation" in output.out
    assert "Browser label simulation" in output.err


@pytest.mark.parametrize("activity,next_action,previous_action", [
    ("music", "NEXT_TRACK", "PREVIOUS_TRACK"),
    ("presentation", "NEXT_SLIDE", "PREVIOUS_SLIDE"),
])
def test_context_navigation_keys(activity, next_action, previous_action):
    assert webcam.action_for_key(ord("n"), activity)[0] == next_action
    assert webcam.action_for_key(ord("b"), activity)[0] == previous_action
