# SPDX-FileCopyrightText: 2021 Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from unittest.mock import patch

from fastapi.testclient import TestClient
from starlette.status import HTTP_200_OK
from starlette.status import HTTP_429_TOO_MANY_REQUESTS

from os2mint_omada.main import app


client = TestClient(app)


def test_readiness() -> None:
    r = client.get("/ready")
    assert HTTP_200_OK == r.status_code


def test_lock() -> None:
    with patch("os2mint_omada.api.lock.locked") as mock_locked:
        mock_locked.return_value = True
        r = client.post("/import/it-users")
        assert HTTP_429_TOO_MANY_REQUESTS == r.status_code
        assert r.json() == {"msg": "Already running"}
