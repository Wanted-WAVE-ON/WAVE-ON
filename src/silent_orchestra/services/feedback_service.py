from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Execution, Feedback, GesturePattern
from .action_catalog import CONTEXT_INTENTS

DELTAS = {
    "CORRECT": 0.03,
    "WRONG_ACTION": -0.15,
    "ACCIDENTAL_GESTURE": -0.10,
    "IGNORE": -0.05,
}


def record_feedback(
    db: Session,
    execution: Execution,
    user_id: str,
    feedback_type: str,
    corrected_intent: str | None,
) -> tuple[Feedback, GesturePattern]:
    if execution.user_id != user_id:
        raise ValueError("Execution not found for this user")
    pattern = db.get(GesturePattern, execution.gesture_pattern_id)
    if pattern is None:
        raise ValueError("Gesture pattern not found")
    if db.scalar(select(Feedback).where(Feedback.execution_id == execution.id)) is not None:
        raise ValueError("Feedback already recorded for this execution")
    if corrected_intent and feedback_type == "WRONG_ACTION":
        if corrected_intent not in CONTEXT_INTENTS.get(pattern.context_scope, ()):
            raise ValueError("corrected_intent is not allowed for this context")
        duplicate = db.scalar(
            select(GesturePattern).where(
                GesturePattern.user_id == pattern.user_id,
                GesturePattern.gesture_key == pattern.gesture_key,
                GesturePattern.context_scope == pattern.context_scope,
                GesturePattern.intent == corrected_intent,
                GesturePattern.id != pattern.id,
            )
        )
        if duplicate is not None:
            raise ValueError("A gesture memory with this intent already exists")

    feedback = Feedback(
        id=str(uuid4()),
        user_id=user_id,
        gesture_pattern_id=pattern.id,
        execution_id=execution.id,
        feedback_type=feedback_type,
        corrected_intent=corrected_intent,
    )
    db.add(feedback)

    delta = DELTAS[feedback_type]
    pattern.confidence = round(min(0.99, max(0.0, pattern.confidence + delta)), 3)
    if feedback_type == "CORRECT":
        pattern.positive_feedback_count += 1
    else:
        pattern.negative_feedback_count += 1
    if corrected_intent and feedback_type == "WRONG_ACTION":
        pattern.intent = corrected_intent
    if pattern.confidence < 0.60:
        pattern.auto_execute = False
        pattern.status = "CANDIDATE"
    pattern.updated_at = datetime.now(timezone.utc)

    db.commit()
    return feedback, pattern
