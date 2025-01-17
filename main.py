"""Основной модуль fastapi-приложения."""
import fastapi
import app.utils.app_start_stop as astst

from app.routers.account_router import account_router

app = fastapi.FastAPI(lifespan=astst.app_lifespan)

app.include_router(account_router)