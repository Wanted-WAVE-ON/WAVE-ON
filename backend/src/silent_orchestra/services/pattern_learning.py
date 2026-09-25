import math
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from ..config import settings
from ..models import Action, AgentSuggestion, Context, GestureObservation, GesturePattern
from ..schemas import TeachRequest
from .action_catalog import CONTEXT_INTENTS, action_label

LEARNING_WINDOW = timedelta(days=30)
MAX_LEARNING_ACTIONS = 20


@dataclass(frozen=True)
class _LearningEvidence:
    intent: str
    count: int
    rows: list
    has_unique_winner: bool
    confidence: float
    target: str
    latest_observation: GestureObservation
    embedding: list[float]


def _utc(value: datetime) -> datetime:
    # SQLite returns naive values even for DateTime(timezone=True).
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)


def _recency_weight(executed_at: datetime, now: datetime) -> float:
    """Exponential decay so a habit built from old evidence stays less certain
    than the same count built from recent evidence, even inside the 30-day
    learning window (SPEC C-2 gap: raw counts alone treat both the same)."""
    age_days = (now - _utc(executed_at)).total_seconds() / 86400
    return 0.5 ** (max(age_days, 0.0) / settings.recency_half_life_days)


def _confidence(winner_count: int, total_count: int, recency_factor: float) -> float:
    consistency = winner_count / total_count
    score = 0.35 + (0.10 * min(winner_count, 5)) + (0.22 * consistency)
    return round(min(0.99, score * recency_factor), 3)


def _ranked_by_recency(rows, now: datetime) -> list[tuple[str, float]]:
    """Vote per intent weighted by how recent each supporting action is, most
    weight first (SPEC C-2 residual): a raw count alone lets an intent that was
    dominant early in the 30-day window keep outranking a newer, smaller but
    more recent run of a different intent for as long as the window holds
    both. ``_recency_weight`` already discounts old evidence in confidence;
    this reuses the same weight to decide *who* is currently the habit."""
    scores: dict[str, float] = {}
    for row in rows:
        scores[row.Action.action_type] = (
            scores.get(row.Action.action_type, 0.0) + _recency_weight(row.Action.executed_at, now)
        )
    return sorted(scores.items(), key=lambda item: item[1], reverse=True)


def _summarize_evidence(rows, now: datetime) -> _LearningEvidence:
    """Reduce recent action rows to the current winning habit."""
    raw_counts = Counter(row.Action.action_type for row in rows)
    ranked = _ranked_by_recency(rows, now)
    intent, score = ranked[0]
    winning_rows = [row for row in rows if row.Action.action_type == intent]
    count = raw_counts[intent]
    has_unique_winner = len(ranked) == 1 or not math.isclose(
        score, ranked[1][1], rel_tol=1e-6, abs_tol=1e-6
    )
    recency_factor = sum(
        _recency_weight(row.Action.executed_at, now) for row in winning_rows
    ) / len(winning_rows)
    latest_observation = winning_rows[0].GestureObservation
    embedding_size = len(latest_observation.gesture_embedding)
    embeddings = [
        row.GestureObservation.gesture_embedding
        for row in winning_rows
        if len(row.GestureObservation.gesture_embedding) == embedding_size
    ]
    return _LearningEvidence(
        intent=intent,
        count=count,
        rows=winning_rows,
        has_unique_winner=has_unique_winner,
        confidence=_confidence(count, len(rows), recency_factor),
        # Rows are newest first, so Counter's insertion order breaks target
        # ties using the most recent target.
        target=Counter(row.Action.target for row in winning_rows).most_common(1)[0][0],
        latest_observation=latest_observation,
        embedding=[
            round(sum(values) / len(embeddings), 6)
            for values in zip(*embeddings, strict=True)
        ],
    )


def check_intent_change(db: Session, pattern: GesturePattern, intent: str, field: str) -> None:
    """Reject an intent the context forbids or that another memory already owns."""
    if intent not in CONTEXT_INTENTS.get(pattern.context_scope, ()):
        raise ValueError(f"{field} is not allowed for this context")
    duplicate = db.scalar(
        select(GesturePattern).where(
            GesturePattern.user_id == pattern.user_id,
            GesturePattern.gesture_key == pattern.gesture_key,
            GesturePattern.context_scope == pattern.context_scope,
            GesturePattern.intent == intent,
            GesturePattern.id != pattern.id,
        )
    )
    if duplicate is not None:
        raise ValueError("A gesture memory with this intent already exists")


def record_user_action(
    db: Session,
    request: TeachRequest,
) -> tuple[Action, GesturePattern, AgentSuggestion | None]:
    observation = db.get(GestureObservation, request.observation_id)
    if observation is None or observation.user_id != request.user_id:
        raise ValueError("Observation not found for this user")
    if observation.action is not None:
        raise ValueError("This observation already has a linked action")
    context = db.get(Context, observation.context_id)
    if context is None:
        raise ValueError("Context not found")
    if request.action_type not in CONTEXT_INTENTS.get(context.activity, ()):
        raise ValueError("action_type is not allowed for this context")

    now = datetime.now(timezone.utc)
    action = Action(
        id=str(uuid4()),
        user_id=request.user_id,
        observation_id=observation.id,
        action_type=request.action_type,
        target=request.target,
        parameters=request.parameters,
        executed_by="USER",
        executed_at=now,
    )
    db.add(action)
    db.flush()

    # Bound the evidence so a long-established habit can still change. Agent
    # executions are never votes for the mapping that produced them.
    rows = db.execute(
        select(Action, GestureObservation)
        .join(GestureObservation, Action.observation_id == GestureObservation.id)
        .join(Context, GestureObservation.context_id == Context.id)
        .where(
            Action.user_id == request.user_id,
            Action.executed_by == "USER",
            Action.executed_at >= now - LEARNING_WINDOW,
            Action.executed_at <= now,
            GestureObservation.gesture_key == observation.gesture_key,
            Context.activity == context.activity,
        )
        .order_by(Action.executed_at.desc(), Action.id.desc())
        .limit(MAX_LEARNING_ACTIONS)
    ).all()

    evidence = _summarize_evidence(rows, now)

    last_rejected_at = db.scalar(
        select(func.max(AgentSuggestion.responded_at))
        .join(GesturePattern, AgentSuggestion.gesture_pattern_id == GesturePattern.id)
        .where(
            GesturePattern.user_id == request.user_id,
            GesturePattern.gesture_key == observation.gesture_key,
            GesturePattern.context_scope == context.activity,
            AgentSuggestion.suggested_intent == evidence.intent,
            AgentSuggestion.status == "REJECTED",
        )
    )
    fresh_count = sum(
        last_rejected_at is None or _utc(row.Action.executed_at) > _utc(last_rejected_at)
        for row in evidence.rows
    )
    rejection_cleared = last_rejected_at is None or fresh_count >= settings.suggestion_threshold

    pattern = db.scalar(
        select(GesturePattern).where(
            GesturePattern.user_id == request.user_id,
            GesturePattern.gesture_key == observation.gesture_key,
            GesturePattern.context_scope == context.activity,
            GesturePattern.intent == evidence.intent,
        )
    )

    if pattern is None:
        pattern = GesturePattern(
            id=str(uuid4()),
            user_id=request.user_id,
            gesture_key=observation.gesture_key,
            gesture_embedding=evidence.embedding,
            motion_type=evidence.latest_observation.motion_type,
            direction=evidence.latest_observation.direction,
            intent=evidence.intent,
            context_scope=context.activity,
            target=evidence.target,
            confidence=evidence.confidence,
            observation_count=evidence.count,
            auto_execute=False,
            status="CANDIDATE" if rejection_cleared else "REJECTED",
        )
        db.add(pattern)
    else:
        pattern.gesture_embedding = evidence.embedding
        pattern.target = evidence.target
        pattern.confidence = evidence.confidence
        pattern.observation_count = evidence.count
        if pattern.status == "REJECTED" and rejection_cleared:
            pattern.status = "CANDIDATE"

    db.flush()

    scope_patterns = db.scalars(
        select(GesturePattern).where(
            GesturePattern.user_id == request.user_id,
            GesturePattern.gesture_key == observation.gesture_key,
            GesturePattern.context_scope == context.activity,
        )
    ).all()
    for item in scope_patterns:
        if item.status == "ACTIVE" and (
            not evidence.has_unique_winner or item.id != pattern.id
        ):
            item.status = "CANDIDATE"
            item.auto_execute = False

    eligible = (
        evidence.has_unique_winner
        and evidence.count >= settings.suggestion_threshold
        and rejection_cleared
        and pattern.status != "ACTIVE"
    )
    suggestion: AgentSuggestion | None = None
    for pending in db.scalars(
        select(AgentSuggestion).where(
            AgentSuggestion.gesture_pattern_id.in_([item.id for item in scope_patterns]),
            AgentSuggestion.status == "PENDING",
        )
    ):
        if eligible and pending.gesture_pattern_id == pattern.id and suggestion is None:
            suggestion = pending
        else:
            db.delete(pending)

    if eligible:
        reason = (
            f"{context.activity} 상황에서 최근 30일 내 최대 20건의 조작 중 "
            f"유사한 동작 후 '{action_label(evidence.intent)}' 행동이 "
            f"{evidence.count}회 관찰되었습니다."
        )
        if suggestion is None:
            suggestion = AgentSuggestion(
                id=str(uuid4()),
                user_id=request.user_id,
                gesture_pattern_id=pattern.id,
                suggested_intent=evidence.intent,
                reason=reason,
                confidence=evidence.confidence,
                status="PENDING",
            )
            db.add(suggestion)
        else:
            suggestion.suggested_intent = evidence.intent
            suggestion.reason = reason
            suggestion.confidence = evidence.confidence

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
    if decision not in {"ACCEPTED", "MODIFIED", "REJECTED"}:
        raise ValueError(f"Unsupported decision: {decision}")

    pattern = db.get(GesturePattern, suggestion.gesture_pattern_id)
    if pattern is None:
        raise ValueError("Gesture pattern not found")

    if decision == "MODIFIED":
        if not modified_intent:
            raise ValueError("modified_intent is required for MODIFIED")
        check_intent_change(db, pattern, modified_intent, "modified_intent")

    suggestion.status = decision
    suggestion.responded_at = datetime.now(timezone.utc)

    if decision == "REJECTED":
        pattern.status = "REJECTED"
        pattern.auto_execute = False
        pattern.confidence = max(0.0, round(pattern.confidence - 0.20, 3))
    else:
        if decision == "MODIFIED":
            suggestion.modified_intent = modified_intent
            pattern.intent = modified_intent
        # Only one memory per gesture may auto-execute in a given context.
        db.execute(
            update(GesturePattern)
            .where(
                GesturePattern.user_id == pattern.user_id,
                GesturePattern.gesture_key == pattern.gesture_key,
                GesturePattern.context_scope == pattern.context_scope,
                GesturePattern.id != pattern.id,
                GesturePattern.status == "ACTIVE",
            )
            .values(status="CANDIDATE", auto_execute=False)
        )
        pattern.status = "ACTIVE"
        pattern.auto_execute = True
        pattern.confidence = max(pattern.confidence, settings.auto_execution_threshold)

    db.commit()
    return suggestion, pattern
