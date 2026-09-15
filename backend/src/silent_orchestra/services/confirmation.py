from datetime import datetime, timedelta, timezone

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from ..config import settings
from ..models import AgentSuggestion, Execution, Feedback, GesturePattern
from .action_catalog import action_label
from .feedback_service import record_feedback
from .pattern_learning import respond_to_suggestion

# open_palm/circle carry no CONTEXT_INTENTS mapping of their own (SPEC A-6), so
# reserving them as a universal accept/reject signal costs no existing gesture
# slot. This lets approval and post-execution feedback happen without a click,
# without weakening the "no auto-execution before approval" rule (decision-log
# 2026-09-01) - it only replaces the button, not the approval step itself.
CONFIRM_GESTURES: dict[str, bool] = {
    "open_palm:none": True,
    "circle:clockwise": False,
}


def is_confirm_gesture(gesture_key: str) -> bool:
    return gesture_key in CONFIRM_GESTURES


def apply_confirmation(
    db: Session, user_id: str, activity: str, gesture_key: str
) -> tuple[bool, str, str | None]:
    """Resolve a confirm gesture against whatever is waiting for a decision.

    Preference order: a PENDING suggestion in this activity first (SPEC M-5),
    then the most recent un-fed-back execution in it. Returns
    (matched, reason, accepted_intent) - `matched` mirrors InferenceResult so
    the UI can reuse its success/idle styling.
    """
    positive = CONFIRM_GESTURES[gesture_key]

    pending = db.scalar(
        select(AgentSuggestion)
        .join(GesturePattern, AgentSuggestion.gesture_pattern_id == GesturePattern.id)
        .where(
            AgentSuggestion.user_id == user_id,
            AgentSuggestion.status == "PENDING",
            GesturePattern.context_scope == activity,
        )
        .order_by(desc(AgentSuggestion.created_at))
    )
    if pending is not None:
        decision = "ACCEPTED" if positive else "REJECTED"
        _, pattern = respond_to_suggestion(db, pending, decision, None)
        verb = "기억하기로 승인" if positive else "거절"
        reason = f"확인 몸짓으로 '{action_label(pattern.intent)}' 제안을 {verb}했습니다."
        return positive, reason, pattern.intent if positive else None

    cutoff = datetime.now(timezone.utc) - timedelta(seconds=settings.confirm_feedback_window_seconds)
    recent_execution = db.scalar(
        select(Execution)
        .join(GesturePattern, Execution.gesture_pattern_id == GesturePattern.id)
        .outerjoin(Feedback, Feedback.execution_id == Execution.id)
        .where(
            Execution.user_id == user_id,
            GesturePattern.context_scope == activity,
            Execution.executed_at >= cutoff,
            Feedback.id.is_(None),
        )
        .order_by(desc(Execution.executed_at))
    )
    if recent_execution is not None:
        feedback_type = "CORRECT" if positive else "WRONG_ACTION"
        record_feedback(db, recent_execution, user_id, feedback_type, None)
        verb = "맞다는" if positive else "틀렸다는"
        reason = f"확인 몸짓으로 방금 실행한 '{action_label(recent_execution.intent)}'에 {verb} 피드백을 남겼습니다."
        return positive, reason, None

    return False, "확인할 대기 중인 제안이나 최근 실행이 없습니다.", None
