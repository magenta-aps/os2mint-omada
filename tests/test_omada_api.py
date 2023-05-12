# SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
import pytest
from httpx import AsyncClient
from httpx import Request
from pydantic import AnyHttpUrl
from pydantic import parse_obj_as
from raclients.auth import AuthenticatedAsyncHTTPXClient
from respx import MockRouter

from os2mint_omada.config import OmadaBasicAuthSettings
from os2mint_omada.config import OmadaOIDCSettings
from os2mint_omada.config import OmadaSettings
from os2mint_omada.omada.api import create_client
from os2mint_omada.omada.api import OmadaAPI


async def test_create_client_oidc_auth(omada_settings: OmadaSettings) -> None:
    """Test that OIDC auth settings are passed through."""
    omada_settings.oidc = OmadaOIDCSettings(
        client_id="AzureDiamond",
        client_secret="hunter2",
        token_endpoint=parse_obj_as(AnyHttpUrl, "https://oidc.example.net"),
        scope="all",
    )
    client = create_client(omada_settings)
    assert isinstance(client, AuthenticatedAsyncHTTPXClient)
    assert client.client_id == omada_settings.oidc.client_id
    assert client.client_secret == omada_settings.oidc.client_secret
    assert client.token_endpoint == omada_settings.oidc.token_endpoint
    assert client.scope == omada_settings.oidc.scope


async def test_create_client_basic_auth(omada_settings: OmadaSettings) -> None:
    """Test that basic auth settings are passed through."""
    omada_settings.basic_auth = OmadaBasicAuthSettings(
        username="AzureDiamond",
        password="hunter2",
    )
    client = create_client(omada_settings)
    assert isinstance(client, AsyncClient)
    request = next(client.auth.auth_flow(Request("GET", "example.com")))
    # base64("AzureDiamond:hunter2") == "QXp1cmVEaWFtb25kOmh1bnRlcjI="
    assert request.headers["Authorization"] == "Basic QXp1cmVEaWFtb25kOmh1bnRlcjI="


@pytest.fixture
async def omada_api(omada_settings: OmadaSettings) -> OmadaAPI:
    """Omada API."""
    client = create_client(settings=omada_settings)
    async with client:
        yield OmadaAPI(url=omada_settings.url, client=client)


async def test_get_users(
    omada_api: OmadaAPI,
    omada_settings: OmadaSettings,
    respx_mock: MockRouter,
) -> None:
    """Test that the API unpacks the Omada response correctly."""
    omada_users = [1, 2]
    respx_mock.get(url=omada_settings.url).respond(json={"value": omada_users})
    assert await omada_api.get_users() == omada_users


async def test_get_users_by_filter(
    omada_api: OmadaAPI,
    omada_settings: OmadaSettings,
    respx_mock: MockRouter,
) -> None:
    """Test that filtering parameters are sent properly."""
    respx_mock.get(
        url=omada_settings.url, params={"$filter": "key eq 'value1'"}
    ).respond(json={"value": [1]})
    respx_mock.get(
        url=omada_settings.url, params={"$filter": "key eq 'value2'"}
    ).respond(json={"value": [2]})
    assert await omada_api.get_users_by("key", ["value1", "value2"]) == [1, 2]
