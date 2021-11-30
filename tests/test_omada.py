# SPDX-FileCopyrightText: 2021 Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from typing import Callable

import pytest
import respx
from hypothesis import given
from hypothesis import strategies as st
from hypothesis.strategies import composite

from os2mint_omada import omada
from os2mint_omada.config import settings


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
