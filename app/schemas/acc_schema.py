"""Модуль содержит схему выдачи информации об аккаунтах."""
import datetime

from pydantic import BaseModel, Field


class AccInfoSchema(BaseModel):
    """Схема выдачи данных об аккаунте."""

    acc_addr: str = Field(...)
    bandwidth: int = Field(...)
    trx_balance: int = Field(...)
    energy: int = Field(...)
    created_at: datetime.datetime = Field(...)


class AccInfoInputSchema(BaseModel):
    """Схема POST данных об аккаунте."""

    acc_addr: str = Field(...)
