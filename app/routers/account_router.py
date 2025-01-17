"""Модуль содержит роутеры работы с аккаунтом."""
from fastapi import Query, Depends
from fastapi.routing import APIRouter
from app.classes.acc_worker import AccountWorker
from app.database import db_session
from app.schemas.acc_schema import AccInfoSchema, AccInfoInputSchema


account_router = APIRouter(tags=['Работа с акканутами'])


@account_router.post('/api/v1/create_account_info')
async def create_account_info(
    input_data: AccInfoInputSchema,
    db=Depends(db_session),
) -> str:
    """Эндпоинт принимает адрес, получает инфу и складывает в БД."""
    return await AccountWorker.create_account_info(input_data.acc_addr, db)


@account_router.get('/api/v1/get_accounts_info')
async def get_accounts_info(
    page: int = Query(1, gt=0),
    page_size: int | None = Query(20, gt=0, le=300),
    db=Depends(db_session),
) -> list[AccInfoSchema]:
    """Эндпоинт выдает инфу по аккаунтам из БД."""
    return await AccountWorker.get_accounts_info(page, page_size, db)
