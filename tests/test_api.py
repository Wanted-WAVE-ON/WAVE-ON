from silent_orchestra.models import Action


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


def train_until_suggested(client, activity, app, intent, target):
    suggestion = None
    for _ in range(3):
        event = observe(client, activity=activity, active_app=app)
        result = teach(client, event["observation"]["id"], intent, target)
        suggestion = result.get("suggestion")
    assert suggestion is not None
    assert suggestion["status"] == "PENDING"
    return suggestion


def train_and_accept(client, activity, app, intent, target):
    suggestion = train_until_suggested(client, activity, app, intent, target)
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

    memories = client.get(
        "/api/v1/memories",
        params={
            "user_id": "demo-user",
            "gesture_key": "swipe:right",
            "context_scope": "music",
        },
    ).json()
    assert [memory["intent"] for memory in memories] == ["NEXT_TRACK"]
    dashboard = client.get("/api/v1/dashboard", params={"user_id": "demo-user"}).json()
    assert dashboard["context"]["activity"] == "music"


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
    after = response.json()["pattern"]
    assert 0.60 <= after["confidence"] < before
    assert after["status"] == "ACTIVE"

    duplicate = client.post(
        f"/api/v1/executions/{execution['id']}/feedback",
        json={"user_id": "demo-user", "feedback_type": "WRONG_ACTION"},
    )
    assert duplicate.status_code == 400

    inferred_again = observe(client, activity="presentation", active_app="PowerPoint")
    assert inferred_again["inference"]["matched"] is True
    second_execution = inferred_again["inference"]["execution"]
    demoted = client.post(
        f"/api/v1/executions/{second_execution['id']}/feedback",
        json={"user_id": "demo-user", "feedback_type": "WRONG_ACTION"},
    ).json()["pattern"]
    assert demoted["confidence"] < 0.60
    assert demoted["status"] == "CANDIDATE"
    assert demoted["auto_execute"] is False
    no_execution = observe(client, activity="presentation", active_app="PowerPoint")
    assert no_execution["inference"]["matched"] is False


def test_observation_never_accepts_or_returns_raw_frame(client):
    bootstrap(client)
    result = observe(client)
    observation = result["observation"]
    assert observation["frame_stored"] is False
    assert "frame" not in observation
    assert "image" not in observation

    rejected = client.post(
        "/api/v1/observe",
        json={
            "user_id": "demo-user",
            "context": {"active_app": "PowerPoint", "activity": "presentation"},
            "gesture": {"motion_type": "swipe", "direction": "right", "image": "raw"},
            "frame": "raw",
        },
    )
    assert rejected.status_code == 422


def test_unsupported_context_is_rejected_without_creating_data(client):
    bootstrap(client)
    response = client.post(
        "/api/v1/observe",
        json={
            "user_id": "demo-user",
            "context": {"active_app": "Browser", "activity": "browser"},
            "gesture": {"motion_type": "swipe", "direction": "right"},
        },
    )
    assert response.status_code == 422
    dashboard = client.get("/api/v1/dashboard", params={"user_id": "demo-user"}).json()
    assert dashboard["context"] is None
    assert dashboard["counts"]["observations"] == 0


def test_tied_intents_do_not_create_suggestion(client, db_session):
    bootstrap(client)
    observation_ids = [observe(client)["observation"]["id"] for _ in range(6)]
    for index, observation_id in enumerate(observation_ids[:5]):
        intent = "NEXT_SLIDE" if index < 3 else "PREVIOUS_SLIDE"
        db_session.add(
            Action(
                id=f"seed-action-{index}",
                user_id="demo-user",
                observation_id=observation_id,
                action_type=intent,
                target="powerpoint",
                parameters={},
                executed_by="USER",
            )
        )
    db_session.commit()

    result = teach(client, observation_ids[-1], "PREVIOUS_SLIDE", "powerpoint")
    assert result["suggestion"] is None
    assert client.get("/api/v1/suggestions", params={"user_id": "demo-user"}).json() == []


def test_suggestion_can_be_modified(client):
    bootstrap(client)
    suggestion = train_until_suggested(
        client, "presentation", "PowerPoint", "NEXT_SLIDE", "powerpoint"
    )

    response = client.post(
        f"/api/v1/suggestions/{suggestion['id']}/respond",
        json={"decision": "MODIFIED", "modified_intent": "PREVIOUS_SLIDE"},
    )
    assert response.status_code == 200, response.text
    pattern = response.json()["pattern"]
    assert pattern["intent"] == "PREVIOUS_SLIDE"
    assert pattern["status"] == "ACTIVE"
