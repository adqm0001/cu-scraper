import pytest
from fastapi.testclient import TestClient

from server import app, get_current_user_id


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def _reset_app_state():
    yield
    app.dependency_overrides.clear()
    app.state.limiter.reset()


@pytest.fixture
def as_user():
    def _as(user_id: str = "1"):
        app.dependency_overrides[get_current_user_id] = lambda: user_id
        return user_id
    return _as


async def _async_return(value):
    return value


@pytest.fixture
def async_return():
    return _async_return


@pytest.fixture
def async_mock():
    def _make(return_value=None):
        async def _fn(*args, **kwargs):
            return return_value
        return _fn
    return _make
