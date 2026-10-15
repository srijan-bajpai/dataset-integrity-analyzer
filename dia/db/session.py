"""
DIA 2.0 Database session management.
"""

from contextlib import contextmanager
from dia.config import settings
from dia.db.models import get_engine, get_session_factory, init_db

# Module-level engine and session factory — lazily initialised
_engine = None
_SessionFactory = None


def _ensure_init():
    global _engine, _SessionFactory
    if _engine is None:
        _engine = init_db(settings.database_url)
        _SessionFactory = get_session_factory(_engine)


def get_db():
    """FastAPI dependency that yields a DB session."""
    _ensure_init()
    session = _SessionFactory()
    try:
        yield session
    finally:
        session.close()


@contextmanager
def get_db_session():
    """Context manager for use outside of FastAPI request cycle (e.g. worker)."""
    _ensure_init()
    session = _SessionFactory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def reset_session_factory_for_tests(database_url: str):
    """Replace the process database with an isolated test database."""
    global _engine, _SessionFactory
    if _engine is not None:
        _engine.dispose()
    _engine = init_db(database_url)
    _SessionFactory = get_session_factory(_engine)
