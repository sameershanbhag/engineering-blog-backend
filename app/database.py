from collections.abc import Generator

from sqlmodel import Session, SQLModel, create_engine

from .config import settings


def _normalize(url: str) -> str:
    """Hosted Postgres providers hand out `postgres://` (or `postgresql://`);
    SQLAlchemy + psycopg3 needs the `postgresql+psycopg://` dialect."""
    if url.startswith("postgres://"):
        return "postgresql+psycopg://" + url[len("postgres://"):]
    if url.startswith("postgresql://"):
        return "postgresql+psycopg://" + url[len("postgresql://"):]
    return url


_db_url = _normalize(settings.database_url)

# SQLite needs check_same_thread=False for FastAPI's threaded request handling.
connect_args = {"check_same_thread": False} if _db_url.startswith("sqlite") else {}

# pool_pre_ping avoids stale connections on hosted Postgres.
engine = create_engine(
    _db_url,
    echo=False,
    connect_args=connect_args,
    pool_pre_ping=not _db_url.startswith("sqlite"),
)


def init_db() -> None:
    # Import models so SQLModel registers the tables before create_all.
    from . import models  # noqa: F401

    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
