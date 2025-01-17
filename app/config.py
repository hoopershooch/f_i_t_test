"""Модуль настроек приложения."""
import functools

import pydantic_settings


class AppSettings(pydantic_settings.BaseSettings):
    postgres_url: str = (
        'postgresql+asyncpg://postgres:postgres@localhost:5432/tron_t'
    )
    postgresql_log: bool = True


@functools.lru_cache()
def get_settings() -> AppSettings:
    """Кеш для предотвращения пересоздания экземпляра Settings."""
    return AppSettings()  # type: ignore


settings = get_settings()
