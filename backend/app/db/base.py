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
    _micro_migrate()


def _micro_migrate() -> None:
    """create_all never alters existing tables; add late columns here.
    (Replace with Alembic if the schema starts moving often.)"""
    from sqlalchemy import inspect, text

    added = {
        "listings": {"price_negotiable": "BOOLEAN NOT NULL DEFAULT 0"},
        "users": {"last_payment_session": "VARCHAR(80)"},
    }
    insp = inspect(engine)
    with engine.begin() as conn:
        for table, cols in added.items():
            if table not in insp.get_table_names():
                continue
            existing = {c["name"] for c in insp.get_columns(table)}
            for name, ddl in cols.items():
                if name not in existing:
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {ddl}"))
