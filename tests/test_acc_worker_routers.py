"""Модуль с тестами роутеров приложения."""
import datetime
import unittest.mock

import fastapi.testclient
import pytest

from main import app as main_app
import app.routers.account_router as acc_rtr
from app.schemas.acc_schema import AccInfoSchema

test_client = fastapi.testclient.TestClient(main_app)


class MockedAccountWorker:

    async def create_account_info(*args, **kwargs):
        pass

    async def get_accounts_info(*args, **kwargs):
        pass


async def mocked_get_acc(*args, **kwargs):
    return [
        AccInfoSchema(
            acc_addr='TEST ADDR', bandwidth=1, energy=1,
            trx_balance=1, created_at=datetime.datetime.now()
        )
    ]


@pytest.fixture()
def mock_acc_worker_class(monkeypatch):
    monkeypatch.setattr(acc_rtr, 'AccountWorker', MockedAccountWorker)


@pytest.fixture()
def mock_acc_worker_get_method(mock_acc_worker_class, monkeypatch):
    get_acc_mock = unittest.mock.create_autospec(
        MockedAccountWorker.get_accounts_info,
        side_effect=mocked_get_acc
    )
    monkeypatch.setattr(
        MockedAccountWorker, 'get_accounts_info', get_acc_mock
    )
    return get_acc_mock


@pytest.mark.parametrize(
    'params, expected_code', [
        ({}, 200), (None, 200),
        ({'page': 25, 'page_size': 50}, 200),
        ({'page': None, 'page_size': 'asdas'}, 422),
    ]
)
def test_get_accs_router(mock_acc_worker_get_method, params, expected_code):
    get_acc_meth_mock = mock_acc_worker_get_method
    res = test_client.get('/api/v1/get_accounts_info', params=params)
    assert res.status_code == expected_code
    if expected_code == 200:
        assert len(res.json()) == 1
        get_acc_meth_calls = get_acc_meth_mock.await_args_list
        assert len(get_acc_meth_calls) == 1
        first_call_args = get_acc_meth_calls[0].args
        assert len(first_call_args) == 3
        if isinstance(params, dict):
            if 'page' in params:
                assert first_call_args[0] == params['page']
            if 'page_size' in params:
                assert first_call_args[1] == params['page_size']
    else:
        get_acc_meth_mock.assert_not_awaited()


async def mocked_create_acc(*args, **kwargs):
    return '!!!!'


@pytest.fixture()
def mock_acc_worker_create_method(mock_acc_worker_class, monkeypatch):
    create_acc_mock = unittest.mock.create_autospec(
        MockedAccountWorker.create_account_info,
        side_effect=mocked_create_acc
    )
    monkeypatch.setattr(
        MockedAccountWorker, 'create_account_info', create_acc_mock
    )
    return create_acc_mock


@pytest.mark.parametrize(
    'params, expected_code', [
        ({}, 422), ({'acc_addr': 'asdsad'}, 200), ({'acc_addr': None}, 422),
    ]
)
def test_create_acc_router(
    mock_acc_worker_create_method, params, expected_code
):
    create_acc_mock = mock_acc_worker_create_method
    res = test_client.post(
        '/api/v1/create_account_info', json=params,
    )
    assert res.status_code == expected_code
    if expected_code == 200:
        create_acc_meth_calls = create_acc_mock.await_args_list
        assert len(create_acc_meth_calls) == 1
        first_call_args = create_acc_meth_calls[0].args
        assert len(first_call_args) == 2
        if isinstance(params, dict):
            if 'acc_addr' in params:
                assert first_call_args[0] == params['acc_addr']
    else:
        create_acc_mock.assert_not_awaited()
