from collections import Counter
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import settings
from ..models import Action, AgentSuggestion, Context, GestureObservation, GesturePattern
from ..schemas import TeachRequest
from .action_catalog import action_label
from .gesture_encoder import running_average


def _id() -> str:
    return str(uuid4())


def _confidence(winner_count: int, total_count: int) -> float:
    consistency = winner_count / total_count
    score = 0.35 + (0.10 * min(winner_count, 5)) + (0.22 * consistency)
    return round(min(0.99, score), 3)


def record_user_action(
    db: Session,
    request: TeachRequest,
) -> tuple[Action, GesturePattern, AgentSuggestion | None]:
    observation = db.get(GestureObservation, request.observation_id)
    if observation is None or observation.user_id != request.user_id:
        raise ValueError("Observation not found for this user")
    if observation.action is not None:
        raise ValueError("This observation already has a linked action")

    action = Action(
        id=_id(),
        user_id=request.user_id,
        observation_id=observation.id,
        action_type=request.action_type,
        target=request.target,
        parameters=request.parameters,
        executed_by="USER",
    )
    db.add(action)
    db.flush()

    context = db.get(Context, observation.context_id)
    if context is None:
        raise ValueError("Context not found")

    rows = db.execute(
        select(Action.action_type, Action.target, GestureObservation.gesture_embedding)
        .join(GestureObservation, Action.observation_id == GestureObservation.id)
        .join(Context, GestureObservation.context_id == Context.id)
        .where(
            Action.user_id == request.user_id,
            GestureObservation.gesture_key == observation.gesture_key,
            Context.activity == context.activity,
        )
    ).all()

    action_counts = Counter(row.action_type for row in rows)
    ranked_actions = action_counts.most_common(2)
    winning_intent, winning_count = ranked_actions[0]
    has_unique_winner = len(ranked_actions) == 1 or winning_count > ranked_actions[1][1]
    total_count = len(rows)
    confidence = _confidence(winning_count, total_count)
    winning_target = next(row.target for row in rows if row.action_type == winning_intent)

    pattern = db.scalar(
        select(GesturePattern).where(
            GesturePattern.user_id == request.user_id,
            GesturePattern.gesture_key == observation.gesture_key,
            GesturePattern.context_scope == context.activity,
            GesturePattern.intent == winning_intent,
        )
    )

    if pattern is None:
        pattern = GesturePattern(
            id=_id(),
            user_id=request.user_id,
            gesture_key=observation.gesture_key,
            gesture_embedding=observation.gesture_embedding,
            motion_type=observation.motion_type,
            direction=observation.direction,
            intent=winning_intent,
            context_scope=context.activity,
            target=winning_target,
            confidence=confidence,
            observation_count=winning_count,
            auto_execute=False,
            status="CANDIDATE",
        )
        db.add(pattern)
    else:
        previous_count = pattern.observation_count
        pattern.gesture_embedding = running_average(
            pattern.gesture_embedding,
            observation.gesture_embedding,
            previous_count,
        )
        pattern.target = winning_target
        pattern.confidence = confidence
        pattern.observation_count = winning_count
        if pattern.status == "REJECTED":
            pattern.status = "CANDIDATE"
        pattern.updated_at = datetime.now(timezone.utc)

    db.flush()

    suggestion: AgentSuggestion | None = None
    if has_unique_winner and winning_count >= settings.suggestion_threshold:
        suggestion = db.scalar(
            select(AgentSuggestion).where(
                AgentSuggestion.gesture_pattern_id == pattern.id,
                AgentSuggestion.status.in_(["PENDING", "ACCEPTED", "MODIFIED"]),
            )
        )
        if suggestion is None:
            suggestion = AgentSuggestion(
                id=_id(),
                user_id=request.user_id,
                gesture_pattern_id=pattern.id,
                suggested_intent=winning_intent,
                reason=(
                    f"{context.activity} 상황에서 유사한 동작 후 "
                    f"'{action_label(winning_intent)}' 행동이 {winning_count}회 관찰되었습니다."
                ),
                confidence=confidence,
                status="PENDING",
            )
            db.add(suggestion)

    db.commit()
    return action, pattern, suggestion


def respond_to_suggestion(
    db: Session,
    suggestion: AgentSuggestion,
    decision: str,
    modified_intent: str | None,
) -> tuple[AgentSuggestion, GesturePattern]:
    if suggestion.status != "PENDING":
        raise ValueError("Only pending suggestions can be answered")

    pattern = db.get(GesturePattern, suggestion.gesture_pattern_id)
    if pattern is None:
        raise ValueError("Gesture pattern not found")

    now = datetime.now(timezone.utc)
    suggestion.status = decision
    suggestion.responded_at = now

    if decision in {"ACCEPTED", "MODIFIED"}:
        if decision == "MODIFIED":
            if not modified_intent:
                raise ValueError("modified_intent is required for MODIFIED")
            suggestion.modified_intent = modified_intent
            pattern.intent = modified_intent
        pattern.status = "ACTIVE"
        pattern.auto_execute = True
        pattern.confidence = max(pattern.confidence, settings.auto_execution_threshold)
    elif decision == "REJECTED":
        pattern.status = "REJECTED"
        pattern.auto_execute = False
        pattern.confidence = max(0.0, round(pattern.confidence - 0.20, 3))
    else:
        raise ValueError(f"Unsupported decision: {decision}")

    pattern.updated_at = now
    db.commit()
    return suggestion, pattern
