# SPDX-FileCopyrightText: 2021 Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from typing import Callable
from unittest.mock import ANY
from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import Mock
from unittest.mock import patch

import httpx
import pytest
import respx
from hypothesis import given
from hypothesis import strategies as st
from hypothesis.strategies import composite
from respx import MockRouter

from os2mint_omada import omada
from os2mint_omada.config import settings
from os2mint_omada.omada import client


@composite
def it_users(draw: Callable) -> list[dict]:
    required = {
        "C_TJENESTENR": st.text(),
        "C_OBJECTGUID_I_AD": st.uuids().map(str),
        "C_LOGIN": st.text(),
        "EMAIL": st.text(),
        "C_DIREKTE_TLF": st.text(),
        "CELLPHONE": st.text(),
        "C_INST_PHONE": st.text(),
    }
    optional = {
        "Id": st.integers(),
        "UId": st.text(),
        "EMAIL2": st.text(),
    }
    return draw(
        st.lists(
            st.fixed_dictionaries(
                required,
                optional=optional,  # type: ignore [arg-type]
            )
        )
    )


@pytest.mark.asyncio
@given(it_users())
async def test_get_it_users(it_users: list[dict]) -> None:
    with respx.mock as respx_mock:
        respx_mock.get(settings.odata_url).respond(json={"value": it_users})
        await omada.get_it_users(settings.odata_url)


@pytest.mark.asyncio
@patch.object(client, "get", wraps=client.get)
async def test_get_it_users_with_host_header(
    get_mock: AsyncMock, respx_mock: MockRouter
) -> None:
    respx_mock.get(
        settings.odata_url,
        headers={"Host": "example.net"},
    ).respond(json={"value": []})
    await omada.get_it_users(settings.odata_url, host_header="example.net")
    get_mock.assert_awaited_once_with(  # ANYs checked through respx above
        ANY, headers=ANY, auth=httpx.USE_CLIENT_DEFAULT, timeout=30
    )


@pytest.mark.asyncio
@patch.object(client, "get", return_value=Mock(**{"json.return_value": {"value": []}}))
@patch("os2mint_omada.omada.HttpNtlmAuth")
async def test_get_it_users_ntlm_auth(
    auth_mock: MagicMock, get_mock: AsyncMock
) -> None:
    await omada.get_it_users(
        settings.odata_url,
        ntlm_username="AzureDiamond",
        ntlm_password="hunter2",
    )
    auth_mock.assert_called_with(username="AzureDiamond", password="hunter2")


@pytest.mark.asyncio
@patch.object(client, "get", return_value=Mock(**{"json.return_value": {"value": []}}))
@patch("os2mint_omada.omada.HttpNtlmAuth")
async def test_get_it_users_with_ntlm_auth(
    auth_mock: MagicMock, get_mock: AsyncMock
) -> None:
    await omada.get_it_users(
        settings.odata_url,
        ntlm_username="AzureDiamond",
        ntlm_password="hunter2",
    )
    assert get_mock.call_args.kwargs["auth"] == auth_mock.return_value
