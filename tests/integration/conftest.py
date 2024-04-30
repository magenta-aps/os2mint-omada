# SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from collections.abc import AsyncIterator
from collections.abc import Callable
from collections.abc import Iterator
from pathlib import Path
from typing import Awaitable

import pytest
from fastapi.testclient import TestClient
from fastramqpi.ramqp.depends import rate_limit
from gql.client import AsyncClientSession
from httpx import AsyncClient
from pytest import MonkeyPatch
from respx import ASGIHandler
from respx import MockRouter

from os2mint_omada.app import create_app
from tests.fakes import fake_omada_api


@pytest.fixture
def omada_mock(respx_mock: MockRouter) -> Callable[[list], None]:
    """Allow tests to fake the Omada API."""

    def _omada_mock(values: list) -> None:
        app = fake_omada_api.create_app(values=values)
        respx_mock.route(host="fake-omada-api").mock(side_effect=ASGIHandler(app))

    # Start mocking an empty Omada view immediately in case the integration makes calls
    # before the test configures its mock users through the callback.
    _omada_mock([])
    return _omada_mock


@pytest.fixture
def test_client(monkeypatch: MonkeyPatch, tmp_path: Path) -> Iterator[TestClient]:
    """Create ASGI test client with associated lifecycles."""
    monkeypatch.setenv("OMADA__URL", "http://fake-omada-api/")
    monkeypatch.setenv("OMADA__INTERVAL", "1")
    monkeypatch.setenv("OMADA__PERSISTENCE_FILE", str(tmp_path / "omada.json"))

    app = create_app()

    # Decrease rate-limit to avoid tests (and developers) timing out
    app.dependency_overrides[rate_limit()] = rate_limit(1)

    with TestClient(app) as client:
        yield client


@pytest.fixture
async def graphql_client(test_client: TestClient) -> AsyncIterator[AsyncClientSession]:
    """Authenticated GraphQL codegen client for OS2mo."""
    yield test_client.app_state["context"]["graphql_client"]


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
