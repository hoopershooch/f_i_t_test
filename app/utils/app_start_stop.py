"""Модуль содержит лайфспан функцию инициализаци-финализации приложения."""
from contextlib import asynccontextmanager
import typing

import app.config as config
import app.utils.tron_client as tc
import fastapi
import tronpy

app_settings = config.get_settings()


@asynccontextmanager
async def app_lifespan(app: fastapi.FastAPI) -> typing.AsyncGenerator:
    """Лайфспан функция для старта-стопа приложения(по новому образцу)."""
    try:
        tc.tron_client = tronpy.AsyncTron(network='nile')
        yield
    finally:
        pass
