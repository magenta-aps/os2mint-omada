# SPDX-FileCopyrightText: 2022 Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from datetime import datetime
from unittest.mock import AsyncMock
from uuid import UUID

import pytest
from more_itertools import one
from ramodels.mo import Validity

from os2mint_omada.backing.mo.service import MOService
from os2mint_omada.config import MoSettings


@pytest.fixture
def employee_uuid() -> UUID:
    return UUID("051857ab-cfe4-456b-b4b7-02db1d47fe9f")


async def test_get_employee_addresses(
    mo_settings: MoSettings, employee_uuid: UUID, address_types: dict[str, UUID]
) -> None:
    """Test retrieval and parsing of MO employee addresses."""
    async with MOService(settings=mo_settings, amqp_system=AsyncMock()) as mo_service:
        addresses = [
            {
                "uuid": "1641ab55-3d92-427b-957c-df2285ed0211",
                "value": "14640440",
                "address_type": {"uuid": address_types["EmailEmployee"]},
                "person": [{"uuid": employee_uuid}],
                "visibility": {"uuid": "6efe732e-daf3-463d-a5c0-519867b2c27b"},
                "validity": {
                    "from": "2005-09-01T00:00:00+02:00",
                    "to": None,
                },
            }
        ]
        response = {
            "employees": [
                {
                    "objects": [
                        {
                            "addresses": addresses,
                        },
                    ],
                },
            ],
        }
        mo_service.graphql.execute = AsyncMock(return_value=response)

        employee_addresses = await mo_service.get_employee_addresses(
            uuid=employee_uuid,
            address_types=address_types.values(),
        )

    assert one(employee_addresses).person.uuid == employee_uuid


async def test_get_employee_addresses_no_employee(
    mo_settings: MoSettings, employee_uuid: UUID, address_types: dict[str, UUID]
) -> None:
    """Test retrieval and parsing of MO addresses for non-existent employee."""
    async with MOService(settings=mo_settings, amqp_system=AsyncMock()) as mo_service:
        response = {
            "employees": [],
        }
        mo_service.graphql.execute = AsyncMock(return_value=response)

        employee_addresses = await mo_service.get_employee_addresses(
            uuid=employee_uuid,
            address_types=address_types.values(),
        )

    assert employee_addresses == []


async def test_get_employee_engagements(
    mo_settings: MoSettings,
    employee_uuid: UUID,
    org_units: dict[str, UUID],
    job_functions: dict[str, UUID],
    engagement_types: dict[str, UUID],
    primary_types: dict[str, UUID],
) -> None:
    """Test retrieval and parsing of MO IT engagements."""
    async with MOService(settings=mo_settings, amqp_system=AsyncMock()) as mo_service:
        engagements = [
            {
                "uuid": "3da985cc-140a-4e7c-b8f7-23ab60aa42e2",
                "user_key": "Foo",
                "org_unit_uuid": org_units["org_unit_a"],
                "person": [{"uuid": employee_uuid}],
                "job_function": {"uuid": job_functions["not_applicable"]},
                "engagement_type": {"uuid": engagement_types["omada_manually_created"]},
                "primary": {"uuid": primary_types["primary"]},
                "validity": {"from": "2013-09-01T00:00:00+02:00", "to": None},
            }
        ]
        response = {
            "employees": [
                {
                    "objects": [
                        {
                            "engagements": engagements,
                        },
                    ],
                },
            ],
        }
        mo_service.graphql.execute = AsyncMock(return_value=response)

        employee_engagements = await mo_service.get_employee_engagements(
            uuid=employee_uuid,
        )

    assert one(employee_engagements).person.uuid == employee_uuid
    assert one(employee_engagements).org_unit.uuid == org_units["org_unit_a"]


async def test_get_employee_engagements_no_employee(
    mo_settings: MoSettings, employee_uuid: UUID
) -> None:
    """Test retrieval and parsing of MO engagements for non-existent employee."""
    async with MOService(settings=mo_settings, amqp_system=AsyncMock()) as mo_service:
        response = {
            "employees": [],
        }
        mo_service.graphql.execute = AsyncMock(return_value=response)

        employee_engagements = await mo_service.get_employee_engagements(
            uuid=employee_uuid,
        )

    assert employee_engagements == []


async def test_get_employee_it_users(
    mo_settings: MoSettings, employee_uuid: UUID, it_systems: dict[str, UUID]
) -> None:
    """Test retrieval and parsing of MO IT users."""
    async with MOService(settings=mo_settings, amqp_system=AsyncMock()) as mo_service:
        it_users = [
            {
                "uuid": "54e707a5-e70e-4269-9c6b-efc93fc67d01",
                "user_key": "Foo",
                "itsystem_uuid": it_systems["Omada"],
                "person": [{"uuid": employee_uuid}],
                "validity": {"from": "2005-09-01T00:00:00+02:00", "to": None},
            },
            {
                "uuid": "7b5a94d9-7781-4ba0-b63a-527803247702",
                "user_key": "Bar",
                "itsystem_uuid": it_systems["AD"],
                "person": [{"uuid": employee_uuid}],
                "validity": {"from": "2007-09-01T00:00:00+02:00", "to": None},
            },
        ]
        response = {
            "employees": [
                {
                    "objects": [
                        {
                            "itusers": it_users,
                        },
                    ],
                },
            ],
        }
        mo_service.graphql.execute = AsyncMock(return_value=response)

        relevant_it_systems = [it_systems["Omada"]]  # filter AD
        employee_it_users = await mo_service.get_employee_it_users(
            uuid=employee_uuid,
            it_systems=relevant_it_systems,
        )

    assert one(employee_it_users).person.uuid == employee_uuid
    assert one(employee_it_users).itsystem.uuid == it_systems["Omada"]


async def test_get_employee_it_users_no_employee(
    mo_settings: MoSettings, employee_uuid: UUID, it_systems: dict[str, UUID]
) -> None:
    """Test retrieval and parsing of MO IT users for non-existent employee."""
    async with MOService(settings=mo_settings, amqp_system=AsyncMock()) as mo_service:
        response = {
            "employees": [],
        }
        mo_service.graphql.execute = AsyncMock(return_value=response)

        employee_it_users = await mo_service.get_employee_it_users(
            uuid=employee_uuid,
            it_systems=it_systems.values(),
        )

    assert employee_it_users == []


async def test_get_org_unit_validity(
    mo_settings: MoSettings, org_units: dict[str, UUID]
) -> None:
    """Test retrieval of org unit validity."""
    async with MOService(settings=mo_settings, amqp_system=AsyncMock()) as mo_service:
        response = {
            "org_units": [
                {
                    "objects": [
                        {
                            "validity": {
                                "from_date": "1960-01-01T12:23:56+01:00",
                                "to_date": "1996-07-29T00:00:00",
                            }
                        },
                        {
                            "validity": {
                                "from_date": "1999-04-06T00:00:00",
                                "to_date": None,
                            }
                        },
                    ],
                },
            ],
        }
        mo_service.graphql.execute = AsyncMock(return_value=response)

        validity = await mo_service.get_org_unit_validity(
            uuid=org_units["org_unit_a"],
        )

    assert validity == Validity(
        from_date=datetime(1960, 1, 1, 12, 23, 56),
        to_date=None,
    )
