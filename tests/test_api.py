from __future__ import annotations


def bootstrap(client):
    response = client.post("/api/v1/demo/bootstrap")
    assert response.status_code == 200
    return response.json()["user"]


def observe(client, activity="presentation", active_app="PowerPoint", direction="right"):
    response = client.post(
        "/api/v1/observe",
        json={
            "user_id": "demo-user",
            "context": {
                "active_app": active_app,
                "activity": activity,
                "space": "test_space",
                "device": "laptop",
            },
            "gesture": {
                "motion_type": "swipe",
                "direction": direction,
                "duration_ms": 430,
            },
            "attempt_inference": True,
        },
    )
    assert response.status_code == 200, response.text
    return response.json()


def teach(client, observation_id, intent, target):
    response = client.post(
        "/api/v1/teach",
        json={
            "user_id": "demo-user",
            "observation_id": observation_id,
            "action_type": intent,
            "target": target,
            "parameters": {},
        },
    )
    assert response.status_code == 200, response.text
    return response.json()


def train_and_accept(client, activity, app, intent, target):
    suggestion = None
    for _ in range(3):
        event = observe(client, activity=activity, active_app=app)
        result = teach(client, event["observation"]["id"], intent, target)
        suggestion = result.get("suggestion")
    assert suggestion is not None
    assert suggestion["status"] == "PENDING"
    response = client.post(
        f"/api/v1/suggestions/{suggestion['id']}/respond",
        json={"decision": "ACCEPTED"},
    )
    assert response.status_code == 200, response.text
    assert response.json()["pattern"]["status"] == "ACTIVE"
    return response.json()["pattern"]


def test_health_and_privacy(client):
    assert client.get("/health").json()["status"] == "ok"
    bootstrap(client)
    privacy = client.get("/api/v1/demo/privacy").json()
    assert privacy["raw_video_stored"] is False
    assert privacy["face_recognition_used"] is False
    assert privacy["cloud_video_uploaded"] is False


def test_learning_loop_suggest_accept_execute(client):
    bootstrap(client)
    pattern = train_and_accept(
        client,
        activity="presentation",
        app="PowerPoint",
        intent="NEXT_SLIDE",
        target="powerpoint",
    )
    assert pattern["observation_count"] == 3
    assert pattern["auto_execute"] is True
    assert pattern["confidence"] >= 0.85

    inferred = observe(client, activity="presentation", active_app="PowerPoint")
    assert inferred["inference"]["matched"] is True
    assert inferred["inference"]["intent"] == "NEXT_SLIDE"
    assert inferred["inference"]["execution"]["status"] == "SIMULATED"


def test_same_gesture_changes_with_context(client):
    bootstrap(client)
    train_and_accept(client, "presentation", "PowerPoint", "NEXT_SLIDE", "powerpoint")
    train_and_accept(client, "music", "Spotify", "NEXT_TRACK", "media_player")

    presentation = observe(client, "presentation", "PowerPoint")
    music = observe(client, "music", "Spotify")
    assert presentation["inference"]["intent"] == "NEXT_SLIDE"
    assert music["inference"]["intent"] == "NEXT_TRACK"


def test_wrong_feedback_lowers_confidence(client):
    bootstrap(client)
    train_and_accept(client, "presentation", "PowerPoint", "NEXT_SLIDE", "powerpoint")
    inferred = observe(client, "presentation", "PowerPoint")
    execution = inferred["inference"]["execution"]
    before = execution["confidence"]

    response = client.post(
        f"/api/v1/executions/{execution['id']}/feedback",
        json={"user_id": "demo-user", "feedback_type": "WRONG_ACTION"},
    )
    assert response.status_code == 200, response.text
    assert response.json()["pattern"]["confidence"] < before


def test_observation_never_accepts_or_returns_raw_frame(client):
    bootstrap(client)
    result = observe(client)
    observation = result["observation"]
    assert observation["frame_stored"] is False
    assert "frame" not in observation
    assert "image" not in observation
