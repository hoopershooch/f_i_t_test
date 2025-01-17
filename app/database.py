"""Модуль содержит соединение, сессию и базовую модель БД."""
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import NullPool
from app.config import settings


async_engine = create_async_engine(
    settings.postgres_url,
    future=True,
    echo=settings.postgresql_log,
    poolclass=NullPool,
)


async_session = sessionmaker(  # type: ignore
    async_engine,
    class_=AsyncSession,
)

Base: Any = declarative_base(metadata=MetaData())


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Получение текущей сессии."""
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()

db_session = asynccontextmanager(get_db)
