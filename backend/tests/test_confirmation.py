from test_api import USER, observe, train_and_accept, train_until_suggested


def confirm(client, positive, activity="presentation", app="PowerPoint"):
    motion, direction = ("open_palm", "none") if positive else ("circle", "clockwise")
    response = client.post(
        "/api/v1/observe",
        json={
            "user_id": USER,
            "context": {"active_app": app, "activity": activity},
            "gesture": {"motion_type": motion, "direction": direction},
            "attempt_inference": True,
        },
    )
    assert response.status_code == 200, response.text
    return response.json()


def pending_count(client):
    return client.get("/api/v1/dashboard", params={"user_id": USER}).json()["counts"][
        "pending_suggestions"
    ]


def test_confirm_gesture_accepts_pending_suggestion_hands_free(client):
    train_until_suggested(client, "presentation", "PowerPoint", "NEXT_SLIDE", "powerpoint")
    result = confirm(client, True)
    assert result["inference"]["matched"] is True
    assert result["inference"]["intent"] == "NEXT_SLIDE"
    assert pending_count(client) == 0
    memories = client.get("/api/v1/memories", params={"user_id": USER}).json()
    assert any(item["intent"] == "NEXT_SLIDE" and item["status"] == "ACTIVE" for item in memories)


def test_confirm_gesture_rejects_pending_suggestion_hands_free(client):
    train_until_suggested(client, "presentation", "PowerPoint", "NEXT_SLIDE", "powerpoint")
    result = confirm(client, False)
    assert result["inference"]["matched"] is False
    assert "거절" in result["inference"]["reason"]
    assert pending_count(client) == 0
    assert client.get("/api/v1/memories", params={"user_id": USER}).json() == []


def test_confirm_gesture_itself_is_never_taught_as_a_new_candidate(client):
    train_until_suggested(client, "presentation", "PowerPoint", "NEXT_SLIDE", "powerpoint")
    confirm(client, True)
    candidates = client.get("/api/v1/dashboard", params={"user_id": USER}).json()["candidates"]
    assert all(item["gesture_key"] != "open_palm:none" for item in candidates)


def test_confirm_gesture_gives_feedback_on_recent_execution_when_nothing_pending(client):
    train_and_accept(client, "presentation", "PowerPoint", "NEXT_SLIDE", "powerpoint")
    observe(client)  # auto-executes NEXT_SLIDE, leaving one un-fed-back execution
    result = confirm(client, True)
    assert result["inference"]["matched"] is True
    assert "맞다는" in result["inference"]["reason"]

    # Feedback already recorded for that execution - nothing left to confirm.
    again = confirm(client, True)
    assert again["inference"]["matched"] is False


def test_confirm_gesture_is_scoped_to_its_own_activity(client):
    train_until_suggested(client, "music", "Spotify", "NEXT_TRACK", "media_player")
    result = confirm(client, True, activity="presentation", app="PowerPoint")
    assert result["inference"]["matched"] is False
    assert pending_count(client) == 1
