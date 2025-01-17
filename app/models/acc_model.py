"""Модуль со схемой аккаунта в БД."""

from app.database import Base
from sqlalchemy import Column, DateTime, Integer, String


class AccDataModel(Base):
    """Модель данных аккаунта в БД."""

    __tablename__ = 'accounts'
    id = Column(Integer, nullable=False, primary_key=True)
    acc_addr: str = Column(String, nullable=False)
    bandwidth: str = Column(String)
    trx_balance: str = Column(String)
    energy: str = Column(String)
    created_at = Column(DateTime, nullable=False)
