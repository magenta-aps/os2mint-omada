# SPDX-FileCopyrightText: 2021 Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from fastapi.testclient import TestClient
from starlette.status import HTTP_200_OK

from os2mint_omada.main import app


client = TestClient(app)


def test_readiness() -> None:
    r = client.get("/ready")
    assert HTTP_200_OK == r.status_code
