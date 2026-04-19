from app.db.base import Base
from app.db.session import engine

# Import models so SQLAlchemy metadata can discover all tables.
from app import models  # noqa: F401


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
