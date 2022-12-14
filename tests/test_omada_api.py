# SPDX-FileCopyrightText: 2022 Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
import pytest
from httpx import AsyncClient
from httpx import Request
from pydantic import AnyHttpUrl
from pydantic import parse_obj_as
from raclients.auth import AuthenticatedAsyncHTTPXClient
from respx import MockRouter
from starlette import status

from os2mint_omada.backing.omada.api import OmadaAPI
from os2mint_omada.config import OmadaBasicAuthSettings
from os2mint_omada.config import OmadaOIDCSettings
from os2mint_omada.config import OmadaSettings


@pytest.fixture
async def omada_api(omada_settings: OmadaSettings) -> OmadaAPI:
    """OmadaAPI with settings from fixtures."""
    async with OmadaAPI(settings=omada_settings) as api:
        yield api


async def test_client_oidc_auth(omada_settings: OmadaSettings) -> None:
    """Test that OIDC auth settings are passed through."""
    omada_settings.oidc = OmadaOIDCSettings(
        client_id="AzureDiamond",
        client_secret="hunter2",
        token_endpoint=parse_obj_as(AnyHttpUrl, "https://oidc.example.net"),
        scope="all",
    )
    async with OmadaAPI(settings=omada_settings) as api:
        assert isinstance(api.client, AuthenticatedAsyncHTTPXClient)
        assert api.client.client_id == omada_settings.oidc.client_id
        assert api.client.client_secret == omada_settings.oidc.client_secret
        assert api.client.token_endpoint == omada_settings.oidc.token_endpoint
        assert api.client.scope == omada_settings.oidc.scope


async def test_client_basic_auth(omada_settings: OmadaSettings) -> None:
    """Test that basic auth settings are passed through."""
    omada_settings.basic_auth = OmadaBasicAuthSettings(
        username="AzureDiamond",
        password="hunter2",
    )
    async with OmadaAPI(settings=omada_settings) as api:
        assert isinstance(api.client, AsyncClient)
        request = next(api.client.auth.auth_flow(Request("GET", "example.com")))
        # base64("AzureDiamond:hunter2") == "QXp1cmVEaWFtb25kOmh1bnRlcjI="
        assert request.headers["Authorization"] == "Basic QXp1cmVEaWFtb25kOmh1bnRlcjI="


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


async def test_get_user_by_cpr_number(
    omada_api: OmadaAPI,
    omada_settings: OmadaSettings,
    respx_mock: MockRouter,
) -> None:
    """Test that filtering parameters are sent and handled correctly."""
    respx_mock.get(
        url=omada_settings.url,
        params={"$filter": "C_CPRNR eq 'a'"},
    ).respond(json={"value": ["x"]})
    assert await omada_api.get_users_by_cpr_number("a") == ["x"]
