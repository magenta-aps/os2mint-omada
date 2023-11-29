# SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
import asyncio
from asyncio import CancelledError
from asyncio import create_task
from collections.abc import AsyncIterator
from collections.abc import Callable
from collections.abc import Iterator
from contextlib import suppress
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient
from gql.client import AsyncClientSession
from httpx import AsyncClient
from pytest import MonkeyPatch
from respx import ASGIHandler
from respx import MockRouter

from os2mint_omada.app import create_app
from tests.fakes import fake_omada_api


@pytest.fixture
async def mo_client() -> AsyncIterator[AsyncClient]:
    """HTTPX client with the OS2mo URL preconfigured."""
    # TODO: This should be moved out of Omada to a shared codebase (FastRAMQPI?)
    # https://docs.pytest.org/en/6.2.x/fixture.html#fixtures-from-third-party-plugins

    async with httpx.AsyncClient(base_url="http://mo:5000") as client:
        yield client


@pytest.fixture(autouse=True)
async def amqp_event_emitter(mo_client: AsyncClient) -> AsyncIterator[None]:
    """Continuously, and quickly, emit OS2mo AMQP events during tests.

    Normally, OS2mo emits AMQP events periodically, but very slowly. Even though there
    are no guarantees as to message delivery speed, and we therefore should not design
    our system around such expectation, waiting a long time for tests to pass in the
    pipelines - or to fail during development - is a very poor development experience.
    """
    # TODO: This should be moved out of Omada to a shared codebase (FastRAMQPI?)
    # https://docs.pytest.org/en/6.2.x/fixture.html#fixtures-from-third-party-plugins

    async def emitter():
        while True:
            await asyncio.sleep(3)
            r = await mo_client.post("/testing/amqp/emit")
            r.raise_for_status()

    task = create_task(emitter())
    yield
    task.cancel()
    with suppress(CancelledError):
        # Await the task to ensure potential errors in the fixture itself, such as a
        # wrong URL or misconfigured OS2mo, are returned to the user.
        await task


@pytest.fixture(autouse=True)
async def database_snapshot_and_restore(mo_client: AsyncClient) -> AsyncIterator[None]:
    """Ensure test isolation by resetting the OS2mo database between tests."""
    # TODO: This should be moved out of Omada to a shared codebase (FastRAMQPI?)
    # https://docs.pytest.org/en/6.2.x/fixture.html#fixtures-from-third-party-plugins

    r = await mo_client.post("/testing/database/snapshot")
    r.raise_for_status()
    yield
    r = await mo_client.post("/testing/database/restore")
    r.raise_for_status()


@pytest.fixture(autouse=True)
def passthrough_backing_services(respx_mock: MockRouter) -> None:
    """Allow calls to the backing services to bypass the RESPX mocking."""
    respx_mock.route(name="keycloak", host="keycloak").pass_through()
    respx_mock.route(name="mo", host="mo").pass_through()


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
    """Create ASGI test client."""
    monkeypatch.setenv("OMADA__URL", "http://fake-omada-api/")
    monkeypatch.setenv("OMADA__INTERVAL", "2")
    monkeypatch.setenv("OMADA__PERSISTENCE_FILE", str(tmp_path / "omada.json"))

    app = create_app()
    with TestClient(app) as client:
        yield client


@pytest.fixture
async def graphql_client(test_client: TestClient) -> AsyncIterator[AsyncClientSession]:
    """Authenticated GraphQL client for OS2mo."""
    yield test_client.app_state["context"]["graphql_client"]
