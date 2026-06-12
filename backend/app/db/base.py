from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import VAR_DIR, settings


class Base(DeclarativeBase):
    pass


VAR_DIR.mkdir(parents=True, exist_ok=True)

_connect_args = (
    {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
)
# pool sized to FastAPI's sync-endpoint threadpool (40): the default 5+10 pool
# churns overflow connections under load (each reopen = file open + WAL pragma),
# which showed up as a 2s p95 tail at 30+ concurrent requests
engine = create_engine(
    settings.database_url,
    connect_args=_connect_args,
    pool_size=25,
    max_overflow=15,
    pool_recycle=3600,
)

if settings.database_url.startswith("sqlite"):

    @event.listens_for(engine, "connect")
    def _sqlite_pragmas(dbapi_conn, _record):
        # WAL: API reads while the worker writes; busy_timeout instead of
        # instant "database is locked"; FKs for ondelete=CASCADE
        cur = dbapi_conn.cursor()
        cur.execute("PRAGMA journal_mode=WAL")
        cur.execute("PRAGMA busy_timeout=5000")
        cur.execute("PRAGMA foreign_keys=ON")
        cur.close()


SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def init_db() -> None:
    from app.db import models  # noqa: F401  (register tables)

    Base.metadata.create_all(engine)
