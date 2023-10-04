# SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
import asyncio
from asyncio import CancelledError
from asyncio import create_task
from collections.abc import AsyncIterator
from collections.abc import Callable
from contextlib import suppress
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient
from gql import gql
from gql.client import AsyncClientSession
from httpx import AsyncClient
from pydantic import AnyHttpUrl
from pydantic import parse_obj_as
from pytest import MonkeyPatch
from raclients.graph.client import GraphQLClient
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

    return _omada_mock


@pytest.fixture
def get_test_client(
    monkeypatch: MonkeyPatch, tmp_path: Path
) -> Callable[[], TestClient]:
    """Create ASGI test app."""
    # These connection strings should correspond to the CI job, NOT docker compose
    monkeypatch.setenv("FASTRAMQPI__MO_URL", "http://mo:5000")
    monkeypatch.setenv("FASTRAMQPI__CLIENT_ID", "dipex")
    monkeypatch.setenv(
        "FASTRAMQPI__CLIENT_SECRET", "603f1c82-d012-4d04-9382-dbe659c533fb"
    )
    monkeypatch.setenv("FASTRAMQPI__AUTH_SERVER", "http://keycloak:8080/auth")
    monkeypatch.setenv("FASTRAMQPI__AUTH_REALM", "mo")
    monkeypatch.setenv("FASTRAMQPI__AMQP__URL", "amqp://guest:guest@msg-broker:5672/")

    monkeypatch.setenv("OMADA__URL", "http://fake-omada-api/")
    monkeypatch.setenv("OMADA__AMQP__URL", "amqp://guest:guest@msg-broker:5672/")
    monkeypatch.setenv("OMADA__INTERVAL", "5")
    monkeypatch.setenv("OMADA__PERSISTENCE_FILE", str(tmp_path / "omada.json"))

    # It is not possible to start a FastAPI app multiple times, so we return a factory
    return lambda: TestClient(app=create_app())


@pytest.fixture
async def mo_graphql_session() -> AsyncIterator[AsyncClientSession]:
    """Authenticated GraphQL session for OS2mo."""
    client = GraphQLClient(
        url="http://mo:5000/graphql/v14",
        client_id="dipex",
        client_secret="603f1c82-d012-4d04-9382-dbe659c533fb",
        auth_realm="mo",
        auth_server=parse_obj_as(AnyHttpUrl, "http://keycloak:8080/auth"),
    )
    async with client as session:
        yield session


ASSERT_QUERY = gql(
    """
    query AssertQuery($cpr_number: CPR!) {
      employees(filter: {cpr_numbers: [$cpr_number], from_date: null, to_date: null}) {
        objects {
          objects {
            ...employeeFields
            engagements(filter: {from_date: null, to_date: null}) {
              ...engagementFields
            }
            addresses(filter: {from_date: null, to_date: null}) {
              ...addressFields
            }
            itusers(filter: {from_date: null, to_date: null}) {
              ...ituserFields
            }
          }
        }
      }
    }

    fragment employeeFields on Employee {
      cpr_number
      given_name
      surname
      validity {
        from
        to
      }
    }

    fragment engagementFields on Engagement {
      user_key
      org_unit {
        user_key
      }
      job_function {
        user_key
      }
      engagement_type {
        user_key
      }
      primary {
        user_key
      }
      validity {
        from
        to
      }
    }

    fragment addressFields on Address {
      value
      address_type {
        user_key
      }
      engagement {
        user_key
      }
      visibility {
        user_key
      }
      validity {
        from
        to
      }
    }

    fragment ituserFields on ITUser {
      user_key
      itsystem {
        user_key
      }
      engagement {
        user_key
      }
      validity {
        from
        to
      }
    }
    """
)
