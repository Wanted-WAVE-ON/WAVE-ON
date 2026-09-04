from collections.abc import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import StaticPool

from .config import settings


class Base(DeclarativeBase):
    pass


def build_engine(database_url: str):
    kwargs: dict = {}
    if database_url.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False}
        if database_url in {"sqlite://", "sqlite:///:memory:"}:
            kwargs["poolclass"] = StaticPool
    engine = create_engine(database_url, **kwargs)

    if database_url.startswith("sqlite"):
        @event.listens_for(engine, "connect")
        def _set_sqlite_pragma(dbapi_connection, _connection_record):  # type: ignore[no-untyped-def]
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    return engine


engine = build_engine(settings.database_url)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, class_=Session)

SQLITE_COMPATIBILITY_GUARDS = (
    """CREATE TRIGGER IF NOT EXISTS guard_context_activity_insert
       BEFORE INSERT ON contexts
       WHEN NEW.activity NOT IN ('presentation','music')
       BEGIN SELECT RAISE(ABORT, 'activity is not supported'); END""",
    """CREATE TRIGGER IF NOT EXISTS guard_context_activity_update
       BEFORE UPDATE OF activity ON contexts
       WHEN NEW.activity NOT IN ('presentation','music')
       BEGIN SELECT RAISE(ABORT, 'activity is not supported'); END""",
    """CREATE TRIGGER IF NOT EXISTS guard_pattern_context_insert
       BEFORE INSERT ON gesture_patterns
       WHEN NEW.context_scope NOT IN ('presentation','music')
       BEGIN SELECT RAISE(ABORT, 'context_scope is not supported'); END""",
    """CREATE TRIGGER IF NOT EXISTS guard_pattern_context_update
       BEFORE UPDATE OF context_scope ON gesture_patterns
       WHEN NEW.context_scope NOT IN ('presentation','music')
       BEGIN SELECT RAISE(ABORT, 'context_scope is not supported'); END""",
    """CREATE TRIGGER IF NOT EXISTS guard_feedback_execution_insert
       BEFORE INSERT ON feedback
       WHEN EXISTS (SELECT 1 FROM feedback WHERE execution_id = NEW.execution_id)
       BEGIN SELECT RAISE(ABORT, 'feedback already exists for this execution'); END""",
    """CREATE TRIGGER IF NOT EXISTS guard_feedback_execution_update
       BEFORE UPDATE OF execution_id ON feedback
       WHEN EXISTS (
           SELECT 1 FROM feedback
           WHERE execution_id = NEW.execution_id AND id != OLD.id
       )
       BEGIN SELECT RAISE(ABORT, 'feedback already exists for this execution'); END""",
)


def get_db() -> Generator[Session, None, None]:
    with SessionLocal() as db:
        yield db


def init_db(database_engine=engine) -> None:
    # Models are imported by main.py before this function runs.
    Base.metadata.create_all(bind=database_engine)
    if database_engine.dialect.name == "sqlite":
        with database_engine.begin() as connection:
            for statement in SQLITE_COMPATIBILITY_GUARDS:
                connection.exec_driver_sql(statement)
