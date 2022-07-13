# SPDX-FileCopyrightText: 2022 Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from collections.abc import AsyncIterator
from unittest.mock import AsyncMock
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from starlette import status

from os2mint_omada.app import create_app
from os2mint_omada.config import Settings


@pytest.fixture
def app(settings: Settings) -> FastAPI:
    return create_app(**settings.dict())


@pytest.fixture
async def client(app: FastAPI) -> AsyncIterator[AsyncClient]:
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.mark.parametrize(
    ["is_mo_ready", "is_omada_ready", "is_expected_ready"],
    [
        (False, False, False),
        (False, True, False),
        (True, False, False),
        (True, True, True),
    ],
)
async def test_readiness(
    is_mo_ready: bool,
    is_omada_ready: bool,
    is_expected_ready: bool,
    app: FastAPI,
    client: AsyncClient,
) -> None:
    mo_service = MagicMock()
    mo_service.is_ready = AsyncMock(return_value=is_mo_ready)

    omada_service = MagicMock()
    omada_service.is_ready = AsyncMock(return_value=is_omada_ready)

    app.state.context = {
        "mo_service": mo_service,
        "omada_service": omada_service,
    }

    r = await client.get("/health/ready")

    mo_service.is_ready.assert_awaited_once()
    omada_service.is_ready.assert_awaited_once()
    if is_expected_ready:
        assert r.status_code == status.HTTP_204_NO_CONTENT
    else:
        assert r.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
