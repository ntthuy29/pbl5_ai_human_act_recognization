from app.db.base import Base
from app.db.session import engine
from sqlalchemy import inspect, text

# Import models so SQLAlchemy metadata can discover all tables.
from app import models  # noqa: F401


def _ensure_prediction_history_user_id_column() -> None:
    inspector = inspect(engine)
    if "prediction_history" not in inspector.get_table_names():
        return

    columns = {column["name"] for column in inspector.get_columns("prediction_history")}
    foreign_keys = inspector.get_foreign_keys("prediction_history")
    has_user_id_fk = any(
        fk.get("constrained_columns") == ["user_id"] and fk.get("referred_table") == "users"
        for fk in foreign_keys
    )

    with engine.begin() as conn:
        if "user_id" not in columns:
            conn.execute(text("ALTER TABLE prediction_history ADD COLUMN user_id INTEGER NULL"))

        if "session_id" not in columns:
            conn.execute(text("ALTER TABLE prediction_history ADD COLUMN session_id INTEGER NULL"))

        if not has_user_id_fk:
            conn.execute(
                text(
                    "ALTER TABLE prediction_history "
                    "ADD CONSTRAINT fk_prediction_history_user_id "
                    "FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE SET NULL"
                )
            )

        has_session_fk = any(
            fk.get("constrained_columns") == ["session_id"] and fk.get("referred_table") == "monitoring_sessions"
            for fk in foreign_keys
        )

        if not has_session_fk:
            conn.execute(
                text(
                    "ALTER TABLE prediction_history "
                    "ADD CONSTRAINT fk_prediction_history_session_id "
                    "FOREIGN KEY (session_id) REFERENCES monitoring_sessions (id) ON DELETE SET NULL"
                )
            )


def _ensure_monitoring_sessions_table() -> None:
    inspector = inspect(engine)
    if "monitoring_sessions" in inspector.get_table_names():
        return

    with engine.begin() as conn:
        conn.execute(
            text(
                "CREATE TABLE monitoring_sessions ("
                "id SERIAL PRIMARY KEY,"
                "user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,"
                "is_active BOOLEAN NOT NULL DEFAULT TRUE,"
                "started_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),"
                "ended_at TIMESTAMP WITH TIME ZONE NULL"
                ")"
            )
        )


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    _ensure_monitoring_sessions_table()
    _ensure_prediction_history_user_id_column()
