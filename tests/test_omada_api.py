# SPDX-FileCopyrightText: 2022 Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
import pytest
from httpx import AsyncClient
from pydantic import AnyHttpUrl
from pydantic import parse_obj_as
from raclients.auth import AuthenticatedAsyncHTTPXClient
from respx import MockRouter
from starlette import status

from os2mint_omada.backing.omada.api import OmadaAPI
from os2mint_omada.config import OmadaSettings


@pytest.fixture
async def omada_api(omada_settings: OmadaSettings) -> OmadaAPI:
    """OmadaAPI with settings from fixtures."""
    async with OmadaAPI(settings=omada_settings) as api:
        yield api


async def test_client(omada_api: OmadaAPI) -> None:
    """Test that the client does not override headers and auth as default."""
    assert "host" not in omada_api.client.headers
    assert isinstance(omada_api.client, AsyncClient)


async def test_client_host_header(omada_settings: OmadaSettings) -> None:
    """Test that the host header setting is passed through."""
    omada_settings.host_header = "foo"
    async with OmadaAPI(settings=omada_settings) as api:
        assert api.client.headers["host"] == "foo"


async def test_client_auth(omada_settings: OmadaSettings) -> None:
    """Test that auth settings are passed through."""
    omada_settings.oidc.client_id = "AzureDiamond"
    omada_settings.oidc.client_secret = "hunter2"
    omada_settings.auth_realm = "Firemaw-EU"
    omada_settings.auth_server = parse_obj_as(AnyHttpUrl, "https://adfs.example.net")
    async with OmadaAPI(settings=omada_settings) as api:
        assert isinstance(api.client, AuthenticatedAsyncHTTPXClient)
        assert api.client.client_id == omada_settings.oidc.client_id
        assert api.client.client_secret == omada_settings.oidc.client_secret
        assert api.client.auth_realm == omada_settings.auth_realm
        assert api.client.auth_server == omada_settings.auth_server


async def test_is_ready(
    omada_api: OmadaAPI, omada_settings: OmadaSettings, respx_mock: MockRouter
) -> None:
    """Test that the API returns ready in normal circumstances."""
    respx_mock.head(url=omada_settings.url)
    is_ready = await omada_api.is_ready()
    assert is_ready is True


async def test_is_not_ready(
    omada_api: OmadaAPI, omada_settings: OmadaSettings, respx_mock: MockRouter
) -> None:
    """Test that the API does not return ready on HTTP errors."""
    respx_mock.head(url=omada_settings.url).respond(
        status_code=status.HTTP_401_UNAUTHORIZED
    )
    is_ready = await omada_api.is_ready()
    assert is_ready is False


async def test_get_users(
    omada_api: OmadaAPI,
    raw_omada_user: dict,
    raw_omada_user_manual: dict,
    omada_settings: OmadaSettings,
    respx_mock: MockRouter,
) -> None:
    """Test that the API unpacks the Omada response correctly."""
    raw_omada_users = [raw_omada_user, raw_omada_user_manual]
    respx_mock.get(url=omada_settings.url).respond(json={"value": raw_omada_users})
    assert await omada_api.get_users() == raw_omada_users


async def test_get_users_by_service_numbers(
    omada_api: OmadaAPI,
    omada_settings: OmadaSettings,
    respx_mock: MockRouter,
) -> None:
    """Test that filtering parameters are sent and handled correctly."""
    respx_mock.get(
        url=omada_settings.url,
        params={"$filter": "C_TJENESTENR eq 'a'"},
    ).respond(json={"value": ["x"]})
    respx_mock.get(
        url=omada_settings.url,
        params={"$filter": "C_TJENESTENR eq 'b'"},
    ).respond(json={"value": ["y"]})
    # The responses from the two individual requests should be flattened to one
    assert await omada_api.get_users_by_service_numbers(["a", "b"]) == ["x", "y"]
