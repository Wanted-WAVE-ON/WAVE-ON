from __future__ import annotations

from sqlalchemy.orm import Session

from ..models import User

DEMO_USER_ID = "demo-user"
DEMO_USER_NAME = "수영"


def ensure_demo_user(db: Session) -> User:
    user = db.get(User, DEMO_USER_ID)
    if user is None:
        user = User(id=DEMO_USER_ID, name=DEMO_USER_NAME)
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


def reset_demo_user(db: Session) -> User:
    user = db.get(User, DEMO_USER_ID)
    if user is not None:
        db.delete(user)
        db.commit()
    return ensure_demo_user(db)
