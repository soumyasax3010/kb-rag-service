"""Async SQLAlchemy engine + session factory.

``build_connect_args`` centralizes asyncpg settings so the app engine and the
Alembic runner stay in sync. ``statement_cache_size=0`` avoids the prepared-
statement cache mismatch that breaks asyncpg behind PgBouncer-style poolers;
SSL is enabled when ``DATABASE_SSL=true`` (managed Postgres like Supabase).
"""

import ssl
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings


class Base(DeclarativeBase):
    pass


def build_connect_args() -> dict:
    args: dict = {"statement_cache_size": 0}
    if settings.database_ssl:
        args["ssl"] = ssl.create_default_context()
    return args


engine = create_async_engine(
    settings.database_url,
    pool_pre_ping=True,
    connect_args=build_connect_args(),
)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session
