from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import Engine, create_engine, event, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings


class Base(DeclarativeBase):
    pass


engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if settings.database_url.startswith("sqlite") else {},
)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, expire_on_commit=False)


@event.listens_for(Engine, "connect")
def configure_sqlite(dbapi_connection: object, _connection_record: object) -> None:
    if settings.database_url.startswith("sqlite"):
        cursor = dbapi_connection.cursor()  # type: ignore[attr-defined]
        cursor.execute("PRAGMA foreign_keys = ON")
        cursor.close()


def initialize_database() -> None:
    """Create the MVP schema for local development and ensure search infrastructure exists."""
    from app import models  # noqa: F401 - registers models before create_all

    Base.metadata.create_all(bind=engine)
    if not settings.database_url.startswith("sqlite"):
        return

    with engine.begin() as connection:
        connection.execute(text("PRAGMA journal_mode = WAL"))
        connection.execute(
            text(
                """
                CREATE VIRTUAL TABLE IF NOT EXISTS tools_fts USING fts5(
                    name, aliases, summary, why_saved, use_cases, notes,
                    content='tools', content_rowid='id', tokenize='trigram'
                )
                """
            )
        )
        connection.execute(
            text(
                """
                CREATE TRIGGER IF NOT EXISTS tools_ai AFTER INSERT ON tools BEGIN
                    INSERT INTO tools_fts(rowid, name, aliases, summary, why_saved, use_cases, notes)
                    VALUES (new.id, new.name, new.aliases, new.summary, new.why_saved, new.use_cases, new.notes);
                END
                """
            )
        )
        connection.execute(
            text(
                """
                CREATE TRIGGER IF NOT EXISTS tools_ad AFTER DELETE ON tools BEGIN
                    INSERT INTO tools_fts(tools_fts, rowid, name, aliases, summary, why_saved, use_cases, notes)
                    VALUES ('delete', old.id, old.name, old.aliases, old.summary, old.why_saved, old.use_cases, old.notes);
                END
                """
            )
        )
        connection.execute(
            text(
                """
                CREATE TRIGGER IF NOT EXISTS tools_au AFTER UPDATE ON tools BEGIN
                    INSERT INTO tools_fts(tools_fts, rowid, name, aliases, summary, why_saved, use_cases, notes)
                    VALUES ('delete', old.id, old.name, old.aliases, old.summary, old.why_saved, old.use_cases, old.notes);
                    INSERT INTO tools_fts(rowid, name, aliases, summary, why_saved, use_cases, notes)
                    VALUES (new.id, new.name, new.aliases, new.summary, new.why_saved, new.use_cases, new.notes);
                END
                """
            )
        )
        connection.execute(text("INSERT INTO tools_fts(tools_fts) VALUES ('rebuild')"))


def get_session() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
