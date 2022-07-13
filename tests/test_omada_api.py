# SPDX-FileCopyrightText: 2022 Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
import pytest
from httpx_ntlm import HttpNtlmAuth
from respx import MockRouter
from starlette import status

from os2mint_omada.backing.omada.api import OmadaAPI
from os2mint_omada.config import OmadaSettings


@pytest.fixture
async def omada_api(omada_settings: OmadaSettings) -> OmadaAPI:
    async with OmadaAPI(settings=omada_settings) as api:
        yield api


@pytest.fixture
def omada_users_raw() -> list[dict]:
    return [
        {
            "Id": 100456,
            "UId": "559996fd-5608-466d-a462-79b946573c0a",
            "C_TJENESTENR": "00123",
            "C_OBJECTGUID_I_AD": "256277c7-cfa8-490d-a404-9c1f3669e02a",
            "C_LOGIN": "DR00234",
            "EMAIL": "alice@example.com",
            "EMAIL2": None,
            "C_DIREKTE_TLF": "",
            "CELLPHONE": "12345678",
            "C_INST_PHONE": "",
        },
        {
            "Id": 100789,
            "UId": "02a92931-077f-4348-a9cc-3bbb9bb37563",
            "C_TJENESTENR": "00999",
            "C_OBJECTGUID_I_AD": "c858b5fe-895e-4da8-ac30-15d6573ee985",
            "C_LOGIN": "DR00777",
            "EMAIL": "bob@example.com",
            "EMAIL2": "bob.backup@example.net",
            "C_DIREKTE_TLF": "11223344",
            "CELLPHONE": "12345678",
            "C_INST_PHONE": "12345678",
        },
    ]


@pytest.fixture
def mock_omada_users(
    omada_users_raw: list[dict], omada_settings: OmadaSettings, respx_mock: MockRouter
) -> list[dict]:
    respx_mock.get(url=omada_settings.url).respond(json={"value": omada_users_raw})
    return omada_users_raw


async def test_client(omada_api: OmadaAPI) -> None:
    assert "host" not in omada_api.client.headers
    assert omada_api.client.auth is None


async def test_client_host_header(omada_settings: OmadaSettings) -> None:
    omada_settings.host_header = "foo"
    async with OmadaAPI(settings=omada_settings) as api:
        assert api.client.headers["host"] == "foo"


async def test_client_ntlm_auth(omada_settings: OmadaSettings) -> None:
    omada_settings.ntlm_username = "AzureDiamond"
    omada_settings.ntlm_password = "hunter2"
    async with OmadaAPI(settings=omada_settings) as api:
        assert isinstance(api.client.auth, HttpNtlmAuth)
        assert api.client.auth.username == "AzureDiamond"
        assert api.client.auth.password == "hunter2"


async def test_is_ready(
    omada_api: OmadaAPI, omada_settings: OmadaSettings, respx_mock: MockRouter
) -> None:
    respx_mock.head(url=omada_settings.url)
    is_ready = await omada_api.is_ready()
    assert is_ready is True


async def test_is_not_ready(
    omada_api: OmadaAPI, omada_settings: OmadaSettings, respx_mock: MockRouter
) -> None:
    respx_mock.head(url=omada_settings.url).respond(
        status_code=status.HTTP_401_UNAUTHORIZED
    )
    is_ready = await omada_api.is_ready()
    assert is_ready is False


async def test_get_users(omada_api: OmadaAPI, mock_omada_users: list[dict]) -> None:
    assert await omada_api.get_users() == mock_omada_users


async def test_get_users_by_service_numbers(
    omada_api: OmadaAPI,
    omada_settings: OmadaSettings,
    respx_mock: MockRouter,
) -> None:
    respx_mock.get(
        url=omada_settings.url,
        params={"$filter": "C_TJENESTENR eq 'a'"},
    ).respond(json={"value": ["x"]})
    respx_mock.get(
        url=omada_settings.url,
        params={"$filter": "C_TJENESTENR eq 'b'"},
    ).respond(json={"value": ["y"]})

    assert await omada_api.get_users_by_service_numbers(["a", "b"]) == ["x", "y"]
