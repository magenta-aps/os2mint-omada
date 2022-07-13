# SPDX-FileCopyrightText: 2022 Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from uuid import UUID

import pytest
from more_itertools import one

from os2mint_omada.backing.mo.service import MOService
from os2mint_omada.config import MoSettings


@pytest.fixture
def employee_uuid() -> UUID:
    return UUID("051857ab-cfe4-456b-b4b7-02db1d47fe9f")


@pytest.fixture
def address_type_uuid() -> UUID:
    return UUID("e75f74f5-cbc4-4661-b9f4-e6a9e05abb2d")


@pytest.fixture
def org_unit_uuid() -> UUID:
    return UUID("23a2ace2-52ca-458d-bead-d1a42080579f")


@pytest.fixture
def it_system_uuid() -> UUID:
    return UUID("db519bfd-0fdd-4e5d-9337-518d1dbdbfc9")


@pytest.fixture
def graphql_employee(
    employee_uuid: UUID,
    address_type_uuid: UUID,
    org_unit_uuid: UUID,
    it_system_uuid: UUID,
) -> dict:
    engagement = {
        "uuid": "94c8601a-1d2c-4c5c-857c-460c3c979725",
        "user_key": "lol",
        "org_unit_uuid": org_unit_uuid,
        "person": [{"uuid": employee_uuid}],
        "job_function": {"uuid": "f0e22017-58a0-43fb-9662-f4847e466e85"},
        "engagement_type": {"uuid": "8acc5743-044b-4c82-9bb9-4e572d82b524"},
        "primary": {"uuid": "0644cd06-b84b-42e0-95fe-ce131c21fbe6"},
        "validity": {
            "from": "2022-06-30T00:00:00+02:00",
            "to": None,
        },
    }
    address = {
        "uuid": "0e67ccdf-dfc9-49ce-8a91-4fa42092cb8c",
        "value": "9ff3ce5f-c657-496b-8d63-2d8860abcfe7",
        "address_type": {"uuid": address_type_uuid},
        "person": [{"uuid": employee_uuid}],
        "visibility": None,
        "validity": {
            "from": "2009-08-11T00:00:00+02:00",
            "to": None,
        },
    }
    it_user = {
        "uuid": "17ede715-5216-4c15-b692-e023c07fcf8a",
        "user_key": "ww",
        "itsystem_uuid": it_system_uuid,
        "person": [{"uuid": employee_uuid}],
        "validity": {
            "from": "2022-06-24T00:00:00+02:00",
            "to": None,
        },
    }
    return {
        "employees": [
            {
                "objects": [
                    {
                        "uuid": employee_uuid,
                        "engagements": [engagement],
                        "addresses": [address],
                        "itusers": [it_user],
                    },
                ],
            },
        ],
    }


async def test_get_employee(
    mo_settings: MoSettings,
    graphql_employee: dict,
    employee_uuid: UUID,
    address_type_uuid: UUID,
    org_unit_uuid: UUID,
    it_system_uuid: UUID,
) -> None:
    amqp_system = MagicMock()
    async with MOService(settings=mo_settings, amqp_system=amqp_system) as mo_service:
        mo_service.graphql.execute = AsyncMock(return_value=graphql_employee)
        employee = await mo_service.get_employee_data(
            uuid=employee_uuid,
            address_types=[address_type_uuid],
            it_systems=[it_system_uuid],
        )

        assert employee is not None
        assert one(employee.addresses).person is not None
        assert one(employee.addresses).person.uuid == employee_uuid
        assert one(employee.engagements).person.uuid == employee_uuid
        assert one(employee.engagements).org_unit.uuid == org_unit_uuid
        assert one(employee.itusers).person.uuid == employee_uuid
        assert one(employee.itusers).itsystem.uuid == it_system_uuid
