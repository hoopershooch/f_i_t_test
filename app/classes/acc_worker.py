"""Модуль содержит класс логики работы с данными аккаунтов."""
import asyncio
import datetime

import app.models.acc_model as acc_bd_mdl
from app.schemas.acc_schema import AccInfoSchema
import app.utils.tron_client as tr
import sqlalchemy as sa
import sqlalchemy.exc as se


class AccountWorker:

    @staticmethod
    async def create_account_info(acc_addr: str, bd) -> str:
        """Метод получает инфу из TRON и создаёт запись в БД."""
        messages = []
        if tr.tron_client.is_address(acc_addr):
            try:
                (
                    acc_energy, acc_balance, acc_bandwidth
                ) = await AccountWorker.get_data_from_tron(acc_addr)
                if (acc_balance is not None) and (acc_energy is not None):
                    data = {
                        'acc_addr': acc_addr,
                        'energy': str(acc_energy),
                        'trx_balance': str(acc_balance),
                        'bandwidth': str(acc_bandwidth),
                        'created_at': datetime.datetime.now(),
                    }
                    try:
                        inserted = await AccountWorker.insert_data_in_bd(
                            data, bd
                        )
                        if not inserted:
                            messages.append('Не удалось вставить данные в БД')
                    except (se.SQLAlchemyError, Exception):
                        messages.append('Произошла ошибка вставки в БД')
                else:
                    messages.append(
                        f'Клиент TRON выдал некорректные значения '
                        f'энергии:{acc_energy} и баланса:{acc_balance}'
                    )
            except (ValueError, Exception):
                messages.append(
                    'Произошла ошибка при получении данных от TRON'
                )
        else:
            messages.append(f'Указанный адрес {acc_addr} - некорректен')
        return '; '.join(messages)

    @staticmethod
    async def get_accounts_info(
        page: int, page_size: int, db,
    ) -> list[AccInfoSchema]:
        """Метод выбирает из БД данные об аккаунте с пагинацией."""
        async with db as pg_session:
            sub_stmt = sa.select(
                sa.func.max(acc_bd_mdl.AccDataModel.id).label('m_id')
            ).group_by(acc_bd_mdl.AccDataModel.acc_addr).limit(
                page_size
            ).offset(
                (page - 1) * page_size
            ).order_by('m_id')

            stmt = sa.select(
                acc_bd_mdl.AccDataModel.acc_addr,
                acc_bd_mdl.AccDataModel.bandwidth,
                acc_bd_mdl.AccDataModel.trx_balance,
                acc_bd_mdl.AccDataModel.energy,
                acc_bd_mdl.AccDataModel.created_at,
            ).where(acc_bd_mdl.AccDataModel.id.in_(sub_stmt))

            curs = await pg_session.execute(stmt)
            rows = curs.fetchall()
        return [
            AccInfoSchema(
                acc_addr=row[0], bandwidth=row[1], trx_balance=row[2],
                energy=row[3], created_at=row[4],
            )
            for row in rows
        ]

    @staticmethod
    async def insert_data_in_bd(data: dict, bd) -> list:
        """Метод вставки в БД."""
        ids = []
        async with bd as pg_session:
            ins_cursor = await pg_session.execute(
                sa.insert(acc_bd_mdl.AccDataModel).returning(
                    acc_bd_mdl.AccDataModel.id
                ),
                data
            )
            await pg_session.commit()
            ids = ins_cursor.fetchall()
        return ids

    @staticmethod
    async def get_data_from_tron(acc_addr: str) -> tuple:
        """Метод получения данных из TRON."""
        acc_data_task = asyncio.create_task(
            tr.tron_client.get_account(acc_addr)
        )
        acc_bandwidth_task = asyncio.create_task(
            tr.tron_client.get_bandwidth(acc_addr)
        )
        account_data, acc_bandwidth = await asyncio.gather(
            acc_data_task, acc_bandwidth_task
        )
        acc_balance = account_data.get('balance')
        acc_energy = account_data.get(
            'account_resource', {}
        ).get('energy_window_size')
        return acc_energy, acc_balance, acc_bandwidth
