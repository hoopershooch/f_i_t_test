"""Модуль с тестами класса логики работы с аккаунтом."""
import contextlib
import datetime
import unittest.mock

import app.classes.acc_worker as acc_w
import app.models.acc_model as acc_bd_mdl
import pytest
import sqlalchemy as sa

TEST_ADDR = 'TEST ADDR'


class MockedTRONClient:

    def is_address(self, addr: str):
        pass

    async def get_account(self, addr: str):
        pass

    async def get_bandwidth(self, addr: str):
        pass


mocked_tron_client = MockedTRONClient()


class MockedBDCursor:

    def fetchall(self):
        pass


mocked_bd_cursor = MockedBDCursor()


class MockedBDSession:

    async def execute(self, *args, **kwargs) -> None:
        pass

    async def commit(self):
        pass


mocked_bd_session = MockedBDSession()


@contextlib.asynccontextmanager
async def mocked_async_session():
    yield mocked_bd_session


@pytest.fixture()
def mock_tron_client(monkeypatch):
    monkeypatch.setattr(acc_w.tr, 'tron_client', mocked_tron_client)


def mocked_is_addr_false(*args, **kwargs):
    return False


def mocked_is_addr_true(*args, **kwargs):
    return True


def mocked_get_tron_data_good(*args, **kwargs):
    return 1, 2, 3


def mocked_get_tron_data_empty(*args, **kwargs):
    return None, 2, 3


def mocked_get_tron_data_exception(*args, **kwargs):
    raise Exception('TEST EXCEPTION')


def mocked_insert_in_bd_good(*args, **kwargs):
    return [1]


def mocked_insert_in_bd_exception(*args, **kwargs):
    raise Exception('TEST EXCEPTION')


@pytest.fixture(params=[
    (
        mocked_is_addr_false, mocked_get_tron_data_good,
        mocked_insert_in_bd_good
    ),
    (
        mocked_is_addr_true, mocked_get_tron_data_good,
        mocked_insert_in_bd_good
    ),
    (
        mocked_is_addr_true, mocked_get_tron_data_empty,
        mocked_insert_in_bd_good
    ),
    (
        mocked_is_addr_true, mocked_get_tron_data_exception,
        mocked_insert_in_bd_good
    ),
    (
        mocked_is_addr_true, mocked_get_tron_data_good,
        mocked_insert_in_bd_exception
    ),
])
def mock_methods_for_create(mock_tron_client, monkeypatch, request):
    is_addr_mock = unittest.mock.create_autospec(
        MockedTRONClient.is_address,
        side_effect=request.param[0],
    )
    monkeypatch.setattr(
        MockedTRONClient, 'is_address', is_addr_mock
    )
    # ------------------------
    get_tron_data_mock = unittest.mock.create_autospec(
        acc_w.AccountWorker.get_data_from_tron,
        side_effect=request.param[1],
    )
    monkeypatch.setattr(
        acc_w.AccountWorker, 'get_data_from_tron', get_tron_data_mock,
    )
    # ------------------------
    insert_in_bd_mock = unittest.mock.create_autospec(
        acc_w.AccountWorker.insert_data_in_bd,
        side_effect=request.param[2],
    )
    monkeypatch.setattr(
        acc_w.AccountWorker, 'insert_data_in_bd', insert_in_bd_mock,
    )
    return is_addr_mock, get_tron_data_mock, insert_in_bd_mock,


@pytest.mark.asyncio
async def test_create_account_info(mock_methods_for_create) -> None:
    """Тест основного метода создания записи в БД."""
    (
        is_addr_mock, get_tron_data_mock, insert_in_bd_mock
    ) = mock_methods_for_create
    mess = await acc_w.AccountWorker.create_account_info(TEST_ADDR, 'd')
    is_addr_mock.assert_called_once_with(mocked_tron_client, TEST_ADDR)
    if is_addr_mock.side_effect == mocked_is_addr_true:
        get_tron_data_mock.assert_awaited_once_with(TEST_ADDR)
        if get_tron_data_mock.side_effect == mocked_get_tron_data_good:
            insert_calls = insert_in_bd_mock.await_args_list
            assert len(insert_calls) == 1
            first_ins_call = insert_calls[0].args
            assert len(first_ins_call) == 2
            assert isinstance(first_ins_call[0], dict)
            assert {
                'acc_addr', 'energy', 'trx_balance',
                'bandwidth', 'created_at'
            }.issubset(first_ins_call[0])
            assert first_ins_call[1] == 'd'
            assert first_ins_call[0]['acc_addr'] == TEST_ADDR
            assert first_ins_call[0]['energy'] == '1'
            assert first_ins_call[0]['trx_balance'] == '2'
            assert first_ins_call[0]['bandwidth'] == '3'
            if insert_in_bd_mock.side_effect == mocked_insert_in_bd_good:
                assert mess == ''
            else:
                assert len(mess) > 0
        else:
            assert len(mess) > 0
            insert_in_bd_mock.assert_not_awaited()
    else:
        assert len(mess) > 0
        get_tron_data_mock.assert_not_awaited()
        insert_in_bd_mock.assert_not_awaited()


def mocked_fetchall_good(*args, **kwargs):
    return [('ADDR1', '1', '2', '3', datetime.datetime.now())]


async def mocked_execute_good(*args, **kwargs):
    return mocked_bd_cursor


@pytest.fixture(params=[
    (mocked_fetchall_good, mocked_execute_good),
])
def mock_methods_for_get_accounts(monkeypatch, request):
    sess_execute_mock = unittest.mock.create_autospec(
        MockedBDSession.execute,
        side_effect=request.param[1],
    )
    monkeypatch.setattr(
        MockedBDSession, 'execute', sess_execute_mock
    )
    # ------------------------
    fetchall_mock = unittest.mock.create_autospec(
        MockedBDCursor.fetchall,
        side_effect=request.param[0],
    )
    monkeypatch.setattr(
        MockedBDCursor, 'fetchall', fetchall_mock,
    )
    # ------------------------
    return sess_execute_mock, fetchall_mock,


@pytest.mark.asyncio
async def test_get_accounts_info(mock_methods_for_get_accounts: tuple) -> None:
    """Тест метода выборки из БД."""
    sess_execute_mock, fetchall_mock = mock_methods_for_get_accounts
    sub_stmt = sa.select(
        sa.func.max(acc_bd_mdl.AccDataModel.id).label('m_id')
    ).group_by(
        acc_bd_mdl.AccDataModel.acc_addr
    ).limit(20).offset(0).order_by('m_id')
    stmt = sa.select(
        acc_bd_mdl.AccDataModel.acc_addr,
        acc_bd_mdl.AccDataModel.bandwidth,
        acc_bd_mdl.AccDataModel.trx_balance,
        acc_bd_mdl.AccDataModel.energy,
        acc_bd_mdl.AccDataModel.created_at,
    ).where(acc_bd_mdl.AccDataModel.id.in_(sub_stmt))

    res = await acc_w.AccountWorker.get_accounts_info(
        1, 20, mocked_async_session()
    )
    execute_calls = sess_execute_mock.await_args_list
    assert len(execute_calls) == 1
    first_execute_call_args = execute_calls[0].args
    assert len(first_execute_call_args) == 2
    assert stmt.compare(first_execute_call_args[1])
    fetchall_mock.assert_called_once()
    assert len(res) == 1


async def mocked_commit(*args, **kwargs):
    pass


@pytest.fixture()
def mock_methods_for_insert(mock_methods_for_get_accounts, monkeypatch):
    sess_execute_mock, fetchall_mock = mock_methods_for_get_accounts
    sess_commit_mock = unittest.mock.create_autospec(
        MockedBDSession.commit,
        side_effect=mocked_commit,
    )
    monkeypatch.setattr(
        MockedBDSession, 'commit', sess_commit_mock
    )
    # ------------------------
    return sess_execute_mock, fetchall_mock, sess_commit_mock


@pytest.mark.asyncio
async def test_insert_data_in_bd(mock_methods_for_insert: tuple) -> None:
    """Тест метода вставки в БД."""
    sess_execute_mock, fetchall_mock, commit_mock = mock_methods_for_insert
    stmt = sa.insert(acc_bd_mdl.AccDataModel).returning(
        acc_bd_mdl.AccDataModel.id
    )
    res = await acc_w.AccountWorker.insert_data_in_bd(
        {1: 1, 2: 2, 3: 3}, mocked_async_session()
    )
    execute_calls = sess_execute_mock.await_args_list
    assert len(execute_calls) == 1
    first_execute_call_args = execute_calls[0].args
    assert len(first_execute_call_args) == 3
    assert stmt.compare(first_execute_call_args[1])
    fetchall_mock.assert_called_once()
    assert len(res) == 1
    commit_mock.assert_awaited_once()


async def mocked_get_bandwidth_good(*args, **kwargs):
    return 600


async def mocked_get_account_good(*args, **kwargs):
    return {'balance': 500, 'account_resource': {'energy_window_size': 400}}


async def mocked_get_account_empty(*args, **kwargs):
    return {}


@pytest.fixture(params=[
    (mocked_get_account_good, mocked_get_bandwidth_good),
    (mocked_get_account_empty, mocked_get_bandwidth_good),
])
def mock_methods_for_get_tr_data(mock_tron_client, monkeypatch, request):
    # ------------------------
    gbw_mock = unittest.mock.create_autospec(
        MockedTRONClient.get_bandwidth,
        side_effect=request.param[1],
    )
    monkeypatch.setattr(
        MockedTRONClient, 'get_bandwidth', gbw_mock,
    )
    # ------------------------
    ga_mock = unittest.mock.create_autospec(
        MockedTRONClient.get_account,
        side_effect=request.param[0],
    )
    monkeypatch.setattr(
        MockedTRONClient, 'get_account', ga_mock,
    )
    # ------------------------
    return gbw_mock, ga_mock,


@pytest.mark.asyncio
async def test_get_data_from_tron(mock_methods_for_get_tr_data: tuple) -> None:
    """Тест метода получения данных из TRON."""
    gbw_mock, ga_mock = mock_methods_for_get_tr_data
    res = await acc_w.AccountWorker.get_data_from_tron(TEST_ADDR)
    gbw_mock.assert_awaited_once_with(mocked_tron_client, TEST_ADDR)
    ga_mock.assert_awaited_once_with(mocked_tron_client, TEST_ADDR)
    if gbw_mock.side_effect == mocked_get_bandwidth_good:
        if ga_mock.side_effect == mocked_get_account_good:
            assert res == (400, 500, 600)
    else:
        assert res == (None, None, 600)
