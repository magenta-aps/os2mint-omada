# SPDX-FileCopyrightText: 2021 Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from uuid import UUID

import pytest
from respx import MockRouter

from os2mint_omada import lora
from os2mint_omada.config import settings


@pytest.mark.asyncio
async def test_ensure_it_system(
    respx_mock: MockRouter, root_org_uuid: UUID, it_system_uuid: UUID
) -> None:
    # We don't check that the PUT was made with the expected parameters, since doing so
    # would basically just involve copy-pasting the actual function under test. Instead,
    # we assume that if the PUT was dispatched, it was done so properly.
    respx_mock.put(
        url=f"{settings.lora_url}/organisation/itsystem/{it_system_uuid}",
    ).respond(
        json={"uuid": str(it_system_uuid)},
    )
    assert await lora.ensure_it_system(
        uuid=it_system_uuid,
        user_key="OMADA",
        name="Omada",
        organisation_uuid=root_org_uuid,
    )
