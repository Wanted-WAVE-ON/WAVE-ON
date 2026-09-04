from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..models import (
    Action,
    AgentSuggestion,
    Context,
    Execution,
    Feedback,
    GestureObservation,
    GesturePattern,
    User,
)
from ..schemas import (
    ContextRead,
    FeedbackCreate,
    FeedbackResponse,
    ObserveRequest,
    ObserveResponse,
    PatternRead,
    SuggestionRead,
    SuggestionResponseRequest,
    TeachRequest,
    TeachResponse,
)
from ..services.feedback_service import record_feedback
from ..services.gesture_encoder import encode_gesture, gesture_key
from ..services.intent_reasoner import infer_intent
from ..services.pattern_learning import record_user_action, respond_to_suggestion

router = APIRouter(tags=["agent"])


def _ensure_user(db: Session, user_id: str) -> None:
    if db.get(User, user_id) is None:
        raise HTTPException(status_code=404, detail="User not found")


@router.post("/observe", response_model=ObserveResponse)
def observe(payload: ObserveRequest, db: Session = Depends(get_db)) -> dict:
    _ensure_user(db, payload.user_id)
    context = Context(
        id=str(uuid4()),
        user_id=payload.user_id,
        active_app=payload.context.active_app,
        activity=payload.context.activity,
        space=payload.context.space,
        device=payload.context.device,
    )
    embedding = payload.gesture.embedding or encode_gesture(
        payload.gesture.motion_type,
        payload.gesture.direction,
        payload.gesture.duration_ms,
    )
    observation = GestureObservation(
        id=str(uuid4()),
        user_id=payload.user_id,
        context_id=context.id,
        gesture_key=gesture_key(payload.gesture.motion_type, payload.gesture.direction),
        gesture_embedding=embedding,
        motion_type=payload.gesture.motion_type,
        direction=payload.gesture.direction,
        duration_ms=payload.gesture.duration_ms,
        frame_stored=False,
    )
    db.add_all([context, observation])
    db.commit()

    inference = (
        infer_intent(db, observation, context)
        if payload.attempt_inference
        else {
            "matched": False,
            "intent": None,
            "target": None,
            "confidence": 0.0,
            "reason": "추론을 요청하지 않았습니다.",
            "execution": None,
        }
    )
    return {"context": context, "observation": observation, "inference": inference}


@router.post("/teach", response_model=TeachResponse)
def teach(payload: TeachRequest, db: Session = Depends(get_db)) -> dict:
    _ensure_user(db, payload.user_id)
    try:
        action, pattern, suggestion = record_user_action(db, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        "action": action,
        "pattern": pattern,
        "suggestion": suggestion,
        "progress_current": min(pattern.observation_count, settings.suggestion_threshold),
        "progress_required": settings.suggestion_threshold,
    }


@router.get("/suggestions", response_model=list[SuggestionRead])
def list_suggestions(
    user_id: str,
    status: str | None = None,
    db: Session = Depends(get_db),
) -> list[AgentSuggestion]:
    _ensure_user(db, user_id)
    stmt = select(AgentSuggestion).where(AgentSuggestion.user_id == user_id)
    if status:
        stmt = stmt.where(AgentSuggestion.status == status.upper())
    return list(db.scalars(stmt.order_by(desc(AgentSuggestion.created_at))).all())


@router.post("/suggestions/{suggestion_id}/respond")
def respond_suggestion(
    suggestion_id: str,
    payload: SuggestionResponseRequest,
    db: Session = Depends(get_db),
) -> dict:
    suggestion = db.get(AgentSuggestion, suggestion_id)
    if suggestion is None:
        raise HTTPException(status_code=404, detail="Suggestion not found")
    try:
        updated, pattern = respond_to_suggestion(
            db,
            suggestion,
            payload.decision,
            payload.modified_intent,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        "suggestion": SuggestionRead.model_validate(updated),
        "pattern": PatternRead.model_validate(pattern),
    }


@router.get("/memories", response_model=list[PatternRead])
def list_memories(
    user_id: str,
    gesture_key: str | None = None,
    context_scope: str | None = None,
    db: Session = Depends(get_db),
) -> list[GesturePattern]:
    _ensure_user(db, user_id)
    stmt = select(GesturePattern).where(
        GesturePattern.user_id == user_id,
        GesturePattern.status == "ACTIVE",
        GesturePattern.confidence >= settings.auto_execution_threshold,
    )
    if gesture_key:
        stmt = stmt.where(GesturePattern.gesture_key == gesture_key)
    if context_scope:
        stmt = stmt.where(GesturePattern.context_scope == context_scope)
    return list(db.scalars(stmt.order_by(desc(GesturePattern.updated_at))).all())


@router.post("/executions/{execution_id}/feedback", response_model=FeedbackResponse)
def submit_feedback(
    execution_id: str,
    payload: FeedbackCreate,
    db: Session = Depends(get_db),
) -> dict:
    execution = db.get(Execution, execution_id)
    if execution is None:
        raise HTTPException(status_code=404, detail="Execution not found")
    try:
        feedback, pattern = record_feedback(
            db,
            execution,
            payload.user_id,
            payload.feedback_type,
            payload.corrected_intent,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"feedback": feedback, "pattern": pattern}


@router.get("/dashboard")
def dashboard(user_id: str, db: Session = Depends(get_db)) -> dict:
    _ensure_user(db, user_id)
    current_context = db.scalar(
        select(Context)
        .where(Context.user_id == user_id)
        .order_by(desc(Context.captured_at))
        .limit(1)
    )
    memories = db.scalars(
        select(GesturePattern)
        .where(GesturePattern.user_id == user_id, GesturePattern.status == "ACTIVE")
        .order_by(desc(GesturePattern.updated_at))
    ).all()
    candidates = db.scalars(
        select(GesturePattern)
        .where(GesturePattern.user_id == user_id, GesturePattern.status == "CANDIDATE")
        .order_by(desc(GesturePattern.updated_at))
    ).all()
    suggestions = db.scalars(
        select(AgentSuggestion)
        .where(AgentSuggestion.user_id == user_id, AgentSuggestion.status == "PENDING")
        .order_by(desc(AgentSuggestion.created_at))
    ).all()
    observations = db.scalars(
        select(GestureObservation)
        .where(GestureObservation.user_id == user_id)
        .order_by(desc(GestureObservation.detected_at))
        .limit(8)
    ).all()
    actions = db.scalars(
        select(Action)
        .where(Action.user_id == user_id)
        .order_by(desc(Action.executed_at))
        .limit(8)
    ).all()
    executions = db.scalars(
        select(Execution)
        .where(Execution.user_id == user_id)
        .order_by(desc(Execution.executed_at))
        .limit(8)
    ).all()
    observation_count = db.scalar(
        select(func.count(GestureObservation.id)).where(GestureObservation.user_id == user_id)
    ) or 0
    feedback_count = db.scalar(
        select(func.count(Feedback.id)).where(Feedback.user_id == user_id)
    ) or 0

    events = [
        {
            "time": item.detected_at,
            "type": "observation",
            "title": f"{item.motion_type} / {item.direction}",
            "detail": "원본 프레임은 저장하지 않고 특징 벡터만 기록",
        }
        for item in observations
    ]
    events += [
        {
            "time": item.executed_at,
            "type": "action",
            "title": item.action_type,
            "detail": f"사용자 후속 행동 / {item.target}",
        }
        for item in actions
    ]
    events += [
        {
            "time": item.executed_at,
            "type": "execution",
            "title": item.intent,
            "detail": f"Agent {item.status} / confidence {item.confidence:.0%}",
        }
        for item in executions
    ]
    events.sort(key=lambda event: event["time"], reverse=True)

    return {
        "context": (
            ContextRead.model_validate(current_context).model_dump(mode="json")
            if current_context
            else None
        ),
        "counts": {
            "observations": observation_count,
            "learned_memories": len(memories),
            "pending_suggestions": len(suggestions),
            "feedback": feedback_count,
        },
        "memories": [PatternRead.model_validate(item).model_dump(mode="json") for item in memories],
        "candidates": [PatternRead.model_validate(item).model_dump(mode="json") for item in candidates],
        "suggestions": [SuggestionRead.model_validate(item).model_dump(mode="json") for item in suggestions],
        "events": [
            {**event, "time": event["time"].isoformat()}
            for event in events[:12]
        ],
        "threshold": settings.suggestion_threshold,
    }
