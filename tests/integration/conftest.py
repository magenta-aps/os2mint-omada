# SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from collections.abc import AsyncIterator
from collections.abc import Callable
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from gql.client import AsyncClientSession
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
    monkeypatch.setenv("OMADA__INTERVAL", "2")
    monkeypatch.setenv("OMADA__PERSISTENCE_FILE", str(tmp_path / "omada.json"))

    app = create_app()
    with TestClient(app) as client:
        yield client


@pytest.fixture
async def graphql_client(test_client: TestClient) -> AsyncIterator[AsyncClientSession]:
    """Authenticated GraphQL codegen client for OS2mo."""
    yield test_client.app_state["context"]["graphql_client"]
