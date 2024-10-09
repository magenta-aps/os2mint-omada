# SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from collections.abc import AsyncIterator
from collections.abc import Callable
from pathlib import Path
from typing import Awaitable

import pytest
from asgi_lifespan import LifespanManager
from asgi_lifespan._types import ASGIApp
from fastapi import FastAPI
from fastramqpi.ramqp.depends import rate_limit
from gql.client import AsyncClientSession
from httpx import ASGITransport
from httpx import AsyncClient
from pytest import MonkeyPatch
from respx import ASGIHandler
from respx import MockRouter

from os2mint_omada.app import create_app
from tests.fakes import fake_omada_api


@pytest.fixture
async def omada_mock(respx_mock: MockRouter) -> Callable[[list], None]:
    """Allow tests to fake the Omada API."""

    def _omada_mock(values: list) -> None:
        app = fake_omada_api.create_app(values=values)
        respx_mock.route(host="fake-omada-api").mock(side_effect=ASGIHandler(app))

    # Start mocking an empty Omada view immediately in case the integration makes calls
    # before the test configures its mock users through the callback.
    _omada_mock([])
    return _omada_mock


@pytest.fixture
async def _app(monkeypatch: MonkeyPatch, tmp_path: Path) -> FastAPI:
    monkeypatch.setenv("OMADA__URL", "http://fake-omada-api/")
    monkeypatch.setenv("OMADA__INTERVAL", "1")
    monkeypatch.setenv("OMADA__PERSISTENCE_FILE", str(tmp_path / "omada.json"))

    app = create_app()

    # Decrease rate-limit to avoid tests (and developers) timing out
    app.dependency_overrides[rate_limit()] = rate_limit(1)

    return app


@pytest.fixture
async def asgiapp(_app: FastAPI) -> AsyncIterator[ASGIApp]:
    """ASGI app with lifespan run."""
    async with LifespanManager(_app) as manager:
        yield manager.app


@pytest.fixture
async def app(_app: FastAPI, asgiapp: ASGIApp) -> FastAPI:
    """FastAPI app with lifespan run."""
    return _app


@pytest.fixture
async def test_client(asgiapp: ASGIApp) -> AsyncIterator[AsyncClient]:
    """Create test client with associated lifecycles."""
    transport = ASGITransport(app=asgiapp, client=("1.2.3.4", 123))  # type: ignore
    async with AsyncClient(
        transport=transport, base_url="http://example.com"
    ) as client:
        yield client


@pytest.fixture
async def graphql_client(app: FastAPI) -> AsyncClientSession:
    """Authenticated GraphQL codegen client for OS2mo."""
    return app.state.context["graphql_client"]


@pytest.fixture
def get_num_queued_messages(
    rabbitmq_management_client: AsyncClient,
) -> Callable[[], Awaitable[int]]:
    """Get number of queued messages in RabbitMQ AMQP."""

    async def _get_num_queued_messages() -> int:
        queues = (await rabbitmq_management_client.get("queues")).json()
        return sum(
            queue.get("messages_ready", 0) + queue.get("messages_unacknowledged", 0)
            for queue in queues
        )

    return _get_num_queued_messages
