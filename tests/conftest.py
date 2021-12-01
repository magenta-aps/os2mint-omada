# SPDX-FileCopyrightText: 2021 Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from uuid import UUID

import pytest
from respx import MockRouter

from os2mint_omada.config import settings

ROOT_ORG_UUID = UUID("1a43a976-472b-45a1-9052-2da91d4f1772")
IT_SYSTEM_UUID = UUID("ea5b8b06-0ab2-4907-a649-ce7f27b34fcf")


@pytest.fixture
def root_org_uuid() -> UUID:
    return ROOT_ORG_UUID


@pytest.fixture
def it_system_uuid() -> UUID:
    return IT_SYSTEM_UUID


@pytest.fixture(autouse=True)
def token_mock(respx_mock: MockRouter) -> None:
    respx_mock.post(url__startswith=settings.auth_server).respond(
        json={"token_type": "Bearer", "access_token": settings.client_secret}
    )
