from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..schemas import DemoBootstrapResponse
from ..services.demo_service import ensure_demo_user, reset_demo_user

router = APIRouter(prefix="/demo", tags=["demo"])


def _demo_state(user) -> dict:
    return {
        "user": user,
        "suggestion_threshold": settings.suggestion_threshold,
        "auto_execution_threshold": settings.auto_execution_threshold,
        "os_actions_enabled": settings.enable_os_actions,
    }


@router.post("/bootstrap", response_model=DemoBootstrapResponse)
def bootstrap(db: Session = Depends(get_db)) -> dict:
    return _demo_state(ensure_demo_user(db))


@router.post("/reset", response_model=DemoBootstrapResponse)
def reset(db: Session = Depends(get_db)) -> dict:
    return _demo_state(reset_demo_user(db))


@router.get("/privacy")
def privacy() -> dict:
    return {
        "raw_video_stored": False,
        "face_recognition_used": False,
        "cloud_video_uploaded": False,
        "motion_features_stored": True,
        "processing_mode": "on-device / local-first",
        "note": "The optional webcam client keeps frames in memory and never writes them to disk.",
    }
