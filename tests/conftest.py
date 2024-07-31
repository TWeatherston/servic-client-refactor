import time

import pytest
from pytest_httpx import HTTPXMock


@pytest.fixture()
def client_responses(httpx_mock: HTTPXMock) -> HTTPXMock:
    httpx_mock.add_response(
        url="https://test.auth0.com/oauth/token",
        method="POST",
        json={
            "access_token": "test_access_token",
            "expires_in": 86400,
            "token_type": "Bearer",
            "expires_at": time.time() + 86400,
        },
    )
    return httpx_mock

