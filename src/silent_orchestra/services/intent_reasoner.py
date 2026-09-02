from __future__ import annotations

from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import settings
from ..models import Context, Execution, GestureObservation, GesturePattern
from .action_catalog import action_label
from .action_executor import execute_action
from .gesture_encoder import cosine_similarity


def infer_intent(db: Session, observation: GestureObservation, context: Context) -> dict:
    candidates = db.scalars(
        select(GesturePattern).where(
            GesturePattern.user_id == observation.user_id,
            GesturePattern.context_scope == context.activity,
            GesturePattern.status == "ACTIVE",
            GesturePattern.auto_execute.is_(True),
        )
    ).all()

    ranked: list[tuple[float, GesturePattern, float]] = []
    for pattern in candidates:
        similarity = cosine_similarity(observation.gesture_embedding, pattern.gesture_embedding)
        key_bonus = 1.0 if observation.gesture_key == pattern.gesture_key else 0.0
        shape_score = (0.75 * key_bonus) + (0.25 * max(similarity, 0.0))
        effective_confidence = round(pattern.confidence * shape_score, 3)
        ranked.append((effective_confidence, pattern, similarity))

    if not ranked:
        return {
            "matched": False,
            "intent": None,
            "target": None,
            "confidence": 0.0,
            "reason": "현재 상황에서 활성화된 개인 제스처 기억이 없습니다.",
            "execution": None,
        }

    effective_confidence, pattern, similarity = max(ranked, key=lambda item: item[0])
    if effective_confidence < settings.auto_execution_threshold:
        return {
            "matched": False,
            "intent": pattern.intent,
            "target": pattern.target,
            "confidence": effective_confidence,
            "reason": (
                f"유사한 기억을 찾았지만 자동 실행 기준 {settings.auto_execution_threshold:.2f}보다 "
                "확신도가 낮아 실행하지 않았습니다."
            ),
            "execution": None,
        }

    result = execute_action(pattern.intent, pattern.target, {})
    execution = Execution(
        id=str(uuid4()),
        user_id=observation.user_id,
        gesture_pattern_id=pattern.id,
        observation_id=observation.id,
        intent=pattern.intent,
        target=pattern.target,
        parameters={},
        confidence=effective_confidence,
        execution_mode=result.mode,
        status=result.status,
        error_message=result.error_message,
    )
    db.add(execution)
    db.commit()
    db.refresh(execution)

    return {
        "matched": True,
        "intent": pattern.intent,
        "target": pattern.target,
        "confidence": effective_confidence,
        "reason": (
            f"{context.activity} 맥락의 개인 기억과 {similarity:.0%} 유사하여 "
            f"'{action_label(pattern.intent)}' 의도로 해석했습니다."
        ),
        "execution": execution,
    }
