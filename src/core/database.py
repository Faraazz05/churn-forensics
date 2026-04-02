"""
core/database.py
================
SQLAlchemy async engine + session factory.
Supports SQLite (dev) and PostgreSQL (prod) via DATABASE_URL.
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from core.config import get_settings

settings = get_settings()

# Convert sync URLs to async drivers
_url = settings.DATABASE_URL
if _url.startswith("sqlite:///"):
    _url = _url.replace("sqlite:///", "sqlite+aiosqlite:///")
elif _url.startswith("postgresql://"):
    _url = _url.replace("postgresql://", "postgresql+asyncpg://")
elif _url.startswith("postgresql+psycopg2://"):
    _url = _url.replace("postgresql+psycopg2://", "postgresql+asyncpg://")

_connect_args = {"check_same_thread": False} if "sqlite" in _url else {}

engine = create_async_engine(
    _url,
    echo        = settings.DEBUG,
    connect_args = _connect_args,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_         = AsyncSession,
    expire_on_commit = False,
    autocommit     = False,
    autoflush      = False,
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    """FastAPI dependency — yields an async DB session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """Create all tables (called at startup)."""
    async with engine.begin() as conn:
        from db import models as _  # noqa: ensure models are imported
        await conn.run_sync(Base.metadata.create_all)
