from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from config import settings

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {},
    pool_pre_ping=True,
    pool_recycle=300,
)


if settings.DATABASE_URL.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def _sqlite_on_connect(dbapi_conn, _):
        # Enforce FK constraints (needed for ON DELETE SET NULL) + WAL for better
        # concurrent reads while a writer is active.
        cur = dbapi_conn.cursor()
        cur.execute("PRAGMA foreign_keys=ON")
        cur.execute("PRAGMA journal_mode=WAL")
        cur.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    from db import models  # noqa: F401
    from sqlalchemy import inspect, text

    Base.metadata.create_all(bind=engine)

    # Phase 19.4 — lightweight in-place migration for new columns.
    # Alembic is overkill here; just ALTER TABLE when a new column is missing.
    insp = inspect(engine)
    if "analyses" in insp.get_table_names():
        existing = {c["name"] for c in insp.get_columns("analyses")}
        with engine.begin() as conn:
            if "media_hash" not in existing:
                conn.execute(text("ALTER TABLE analyses ADD COLUMN media_hash VARCHAR(64)"))
            if "media_path" not in existing:
                conn.execute(text("ALTER TABLE analyses ADD COLUMN media_path VARCHAR(512)"))
            if "thumbnail_url" not in existing:
                conn.execute(text("ALTER TABLE analyses ADD COLUMN thumbnail_url VARCHAR(512)"))
            # Indices (CREATE INDEX IF NOT EXISTS is SQLite+Postgres safe)
            for ddl in (
                "CREATE INDEX IF NOT EXISTS ix_analyses_media_hash ON analyses (media_hash)",
                "CREATE INDEX IF NOT EXISTS ix_record_user_created ON analyses (user_id, created_at)",
                "CREATE INDEX IF NOT EXISTS ix_report_analysis ON reports (analysis_id)",
            ):
                try:
                    conn.execute(text(ddl))
                except Exception:  # noqa: BLE001
                    pass
