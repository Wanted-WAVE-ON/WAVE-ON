from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select

from silent_orchestra.models import Feedback, GesturePattern
from silent_orchestra.services import action_executor
from silent_orchestra.services.context_resolver import resolve_context
from silent_orchestra.services.gesture_encoder import cosine_similarity, encode_gesture
from test_api import feedback, observe, respond, teach, train_and_accept


def measured_observation(client, *, duration=350, speed=0.3, amplitude=0.1,
                         motion="swipe", context=None, infer=True):
    response = client.post("/api/v1/observe", json={
        "user_id": "demo-user", "context": context or {"active_app": "PowerPoint"},
        "gesture": {"motion_type": motion, "direction": "right", "duration_ms": duration,
                    "speed": speed, "amplitude": amplitude},
        "attempt_inference": infer,
    })
    assert response.status_code == 200, response.text
    return response.json()


def train_measured(client):
    for _ in range(3):
        event = measured_observation(client)
        assert event["inference"]["matched"] is False
        result = teach(client, event["observation"]["id"], "NEXT_SLIDE", "powerpoint")
    return respond(client, result["suggestion"]["id"], "ACCEPTED")["pattern"]


@pytest.mark.parametrize("window,activity", [
    ("Deck - Microsoft PowerPoint", "presentation"), ("Spotify Premium", "music"),
    ("Keynote", "presentation"), ("VLC media player", "music"),
])
def test_context_uses_application_signal_without_activity(client, window, activity):
    event = measured_observation(client, context={"active_app": window})
    assert event["context"]["activity"] == activity


def test_server_reads_local_active_window_when_context_is_empty(client, monkeypatch):
    monkeypatch.setattr(action_executor, "active_window", lambda: "Spotify")
    response = client.post("/api/v1/observe", json={
        "user_id": "demo-user", "context": {}, "gesture": {"motion_type": "swipe"},
    })
    assert response.status_code == 200
    assert response.json()["context"]["activity"] == "music"


@pytest.mark.parametrize("window", [None, "Terminal", "Slides and Music"])
def test_unknown_or_ambiguous_context_writes_nothing(client, monkeypatch, window):
    monkeypatch.setattr(action_executor, "active_window", lambda: window)
    response = client.post("/api/v1/observe", json={
        "user_id": "demo-user", "context": {}, "gesture": {"motion_type": "swipe"},
    })
    assert response.status_code == 400
    state = client.get("/api/v1/dashboard?user_id=demo-user").json()
    assert state["context"] is None
    assert state["counts"]["observations"] == 0


def test_manual_simulation_override_is_explicit():
    assert resolve_context("music", "PowerPoint") == ("music", "PowerPoint")


def test_same_key_retains_distinct_personal_motion_and_affects_execution(client):
    pattern = train_measured(client)
    similar = measured_observation(client, duration=380, speed=0.35, amplitude=0.12)
    different = measured_observation(client, duration=1900, speed=1.9, amplitude=0.95)
    assert similar["observation"]["gesture_key"] == different["observation"]["gesture_key"]
    assert len(pattern["gesture_embedding"]) == 11
    assert similar["inference"]["matched"] is True
    assert different["inference"]["matched"] is False
    assert different["observation"]["gesture_embedding"] != pattern["gesture_embedding"]


def test_speed_and_amplitude_change_embedding_independent_of_duration():
    base = encode_gesture("swipe", "right", 500, 0.2, 0.1)
    assert base != encode_gesture("swipe", "right", 500, 1.8, 0.1)
    assert base != encode_gesture("swipe", "right", 500, 0.2, 0.9)
    assert cosine_similarity(base, encode_gesture("swipe", "left", 500, 0.2, 0.1)) < 0.85


def test_different_key_can_match_measured_features_but_conflicts_abstain(client, db_session):
    pattern_data = train_measured(client)
    pattern = db_session.get(GesturePattern, pattern_data["id"])
    # Model a noisy categorizer: same measured vector, different categorical key.
    pattern.gesture_key = "swipe:uncertain"
    db_session.commit()
    result = measured_observation(client)
    assert result["inference"]["matched"] is True
    assert result["inference"]["confidence"] == pytest.approx(0.696)
    db_session.add(GesturePattern(
        id="competing-pattern", user_id="demo-user", gesture_key="swipe:other",
        gesture_embedding=pattern.gesture_embedding, motion_type="swipe", direction="right",
        intent="PREVIOUS_SLIDE", target="powerpoint", context_scope="presentation",
        confidence=pattern.confidence, observation_count=3, status="ACTIVE", auto_execute=True,
    ))
    db_session.commit()
    assert measured_observation(client)["inference"]["matched"] is False


def test_legacy_memory_does_not_guess_missing_measurements(client):
    train_and_accept(client, "presentation", "PowerPoint", "NEXT_SLIDE", "powerpoint")
    assert measured_observation(client)["inference"]["matched"] is False
    assert observe(client)["inference"]["matched"] is True


@pytest.mark.parametrize("features", [
    {"speed": 1}, {"amplitude": 0.3}, {"speed": -1, "amplitude": 0.3},
    {"speed": "NaN", "amplitude": 0.3}, {"speed": 0.3, "amplitude": "Infinity"},
    {"speed": 0.3, "amplitude": 0.3, "embedding": [1, 0, 0, 0]},
    {"embedding": ["NaN", 0, 0, 0]},
])
def test_invalid_feature_contract_rejected_before_storage(client, features):
    response = client.post("/api/v1/observe", json={
        "user_id": "demo-user", "context": {"active_app": "PowerPoint"},
        "gesture": {"motion_type": "swipe", **features},
    })
    assert response.status_code == 422
    assert client.get("/api/v1/dashboard?user_id=demo-user").json()["counts"]["observations"] == 0


def test_learning_mode_remains_available_after_approval(client):
    train_measured(client)
    result = measured_observation(client, infer=False)
    assert result["inference"]["execution"] is None
    assert teach(client, result["observation"]["id"], "PREVIOUS_SLIDE", "powerpoint")["action"]


def test_scalable_intent_repeats_the_key_by_measured_amplitude(client):
    # Both amplitudes below saturate the embedding's amplitude dimension to the
    # same clipped angle (scale=1 in gesture_encoder.scalar_pair), so the two
    # observations still match the same memory - only the *raw* amplitude
    # stored on GestureObservation, not the shape used for matching, should
    # change how many times the key repeats.
    music_context = {"active_app": "Spotify", "activity": "music"}
    for _ in range(3):
        event = measured_observation(client, amplitude=1.0, context=music_context, infer=False)
        result = teach(client, event["observation"]["id"], "VOLUME_UP", "media_player")
    respond(client, result["suggestion"]["id"], "ACCEPTED")

    baseline = measured_observation(client, amplitude=1.0, context=music_context)
    assert baseline["inference"]["matched"] is True
    assert baseline["inference"]["execution"]["parameters"]["magnitude"] == 2

    bigger = measured_observation(client, amplitude=3.7, context=music_context)
    assert bigger["inference"]["matched"] is True
    assert bigger["inference"]["execution"]["parameters"]["magnitude"] == 4
    assert "4단계" in bigger["inference"]["reason"]


def test_non_scalable_intent_ignores_amplitude(client):
    # NEXT_SLIDE is not in SCALABLE_INTENTS - magnitude must stay 1 even though
    # a large, matching amplitude is present on the observation.
    for _ in range(3):
        event = measured_observation(client, amplitude=1.0, infer=False)
        result = teach(client, event["observation"]["id"], "NEXT_SLIDE", "powerpoint")
    respond(client, result["suggestion"]["id"], "ACCEPTED")

    result = measured_observation(client, amplitude=3.7)
    assert result["inference"]["matched"] is True
    assert result["inference"]["execution"]["parameters"]["magnitude"] == 1


def test_simulated_input_without_amplitude_stays_single_step(client):
    train_and_accept(client, "presentation", "PowerPoint", "NEXT_SLIDE", "powerpoint")
    result = observe(client)
    assert result["inference"]["execution"]["parameters"]["magnitude"] == 1


def test_accidental_suppression_expires_and_is_context_scoped(client, db_session):
    train_and_accept(client, "presentation", "PowerPoint", "NEXT_SLIDE", "powerpoint")
    train_and_accept(client, "music", "Spotify", "NEXT_TRACK", "media_player")
    execution = observe(client)["inference"]["execution"]
    updated = feedback(client, execution["id"], "ACCIDENTAL_GESTURE")["pattern"]
    assert updated["confidence"] == execution["confidence"]
    assert updated["negative_feedback_count"] == 0
    assert updated["status"] == "ACTIVE"
    assert observe(client)["inference"]["matched"] is False
    assert observe(client, "music", "Spotify")["inference"]["matched"] is True
    error = db_session.scalar(select(Feedback).where(Feedback.execution_id == execution["id"]))
    error.created_at = datetime.now(timezone.utc) - timedelta(minutes=6)
    db_session.commit()
    assert observe(client)["inference"]["matched"] is True
