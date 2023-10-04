# SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
# mypy: disable-error-code=assignment
from unittest import TestCase
from unittest.mock import ANY
from unittest.mock import AsyncMock
from uuid import UUID
from uuid import uuid4

import pytest
from ramodels.mo import Employee
from ramodels.mo.details import ITUser

from os2mint_omada.mo import MO


@pytest.fixture
async def mo_api() -> MO:
    """MO API."""
    mo_api = MO(graphql_session=AsyncMock())
    return mo_api


async def test_get_it_systems(mo_api: MO) -> None:
    graphql_response = {
        "itsystems": [
            {
                "uuid": "1760947e-0496-1483-fba8-98af2b98ef4f",
                "user_key": "omada_ad_guid",
            },
        ]
    }
    mo_api.graphql_session.execute = AsyncMock(return_value=graphql_response)
    actual = await mo_api.get_it_systems(user_keys=["foo"])
    assert actual == {
        "omada_ad_guid": UUID("1760947e-0496-1483-fba8-98af2b98ef4f"),
    }


async def test_get_classes(mo_api: MO) -> None:
    graphql_response = {
        "facets": [
            {
                "classes": [
                    {
                        "uuid": "4eae3fc5-7307-4ede-911f-90bf383aebcc",
                        "user_key": "omada_manually_created",
                    },
                ]
            },
        ]
    }
    mo_api.graphql_session.execute = AsyncMock(return_value=graphql_response)
    actual = await mo_api.get_classes(facet_user_key="foo")
    assert actual == {
        "omada_manually_created": UUID("4eae3fc5-7307-4ede-911f-90bf383aebcc"),
    }


async def test_get_employee_uuid_from_user_key(mo_api: MO) -> None:
    graphql_response = {
        "engagements": [
            {
                "objects": [
                    {
                        "employee": [
                            {"uuid": "57561cc7-5e07-4a7b-b2bb-af5a22fa1f65"},
                            {"uuid": "57561cc7-5e07-4a7b-b2bb-af5a22fa1f65"},
                        ]
                    },
                    {
                        "employee": [
                            {"uuid": "57561cc7-5e07-4a7b-b2bb-af5a22fa1f65"},
                        ]
                    },
                ]
            },
            {
                "objects": [
                    {
                        "employee": [
                            {"uuid": "57561cc7-5e07-4a7b-b2bb-af5a22fa1f65"},
                        ]
                    },
                ]
            },
        ]
    }
    mo_api.graphql_session.execute = AsyncMock(return_value=graphql_response)
    actual = await mo_api.get_employee_uuid_from_user_key(user_key="foo")
    assert actual == UUID("57561cc7-5e07-4a7b-b2bb-af5a22fa1f65")


async def test_get_employee_uuid_from_cpr(mo_api: MO) -> None:
    graphql_response = {
        "employees": [
            {"uuid": "0004b952-a513-430b-b696-8d393d7eb2bb"},
            {"uuid": "0004b952-a513-430b-b696-8d393d7eb2bb"},
        ],
    }
    mo_api.graphql_session.execute = AsyncMock(return_value=graphql_response)
    actual = await mo_api.get_employee_uuid_from_cpr(cpr="foo")
    assert actual == UUID("0004b952-a513-430b-b696-8d393d7eb2bb")


async def test_get_employee_states(mo_api: MO) -> None:
    graphql_response = {
        "employees": [
            {
                "objects": [
                    {
                        "uuid": "0004b952-a513-430b-b696-8d393d7eb2bb",
                        "givenname": "Birgitta FOO",
                        "surname": "Duschek",
                        "cpr_no": "1011482720",
                    },
                    {
                        "uuid": "0004b952-a513-430b-b696-8d393d7eb2bb",
                        "givenname": "Birgitta BAR",
                        "surname": "Duschek",
                        "cpr_no": "1011482720",
                    },
                ]
            },
        ]
    }
    mo_api.graphql_session.execute = AsyncMock(return_value=graphql_response)
    actual = await mo_api.get_employee_states(uuid=uuid4())
    expected = {
        Employee(
            uuid=UUID("0004b952-a513-430b-b696-8d393d7eb2bb"),
            givenname="Birgitta FOO",
            surname="Duschek",
            cpr_no="1011482720",
        ),
        Employee(
            uuid=UUID("0004b952-a513-430b-b696-8d393d7eb2bb"),
            givenname="Birgitta BAR",
            surname="Duschek",
            cpr_no="1011482720",
        ),
    }
    assert actual == expected


async def test_get_employee_addresses(mo_api: MO) -> None:
    address_1 = {
        "uuid": "97d1d3e0-3d27-418d-8e87-35c4eb6ad660",
        "value": "12345678",
        "address_type": {"uuid": "87e64001-5669-56a1-69ae-26ba50357fe8"},
        "person": [
            {"uuid": "0004b952-a513-430b-b696-8d393d7eb2bb"},
        ],
        "engagement": [
            {"uuid": "81c9e1ac-f78f-407c-aea1-7ff7c1064a56"},
        ],
        "visibility": {"uuid": "6efe732e-daf3-463d-a5c0-519867b2c27b"},
        "validity": {
            "from": "2030-06-15T00:00:00+02:00",
            "to": "2040-12-03T00:00:00+01:00",
        },
    }
    address_2 = {
        "uuid": "97d1d3e0-3d27-418d-8e87-35c4eb6ad660",
        "value": "12345678",
        "address_type": {"uuid": "87e64001-5669-56a1-69ae-26ba50357fe8"},
        "person": [
            {"uuid": "0004b952-a513-430b-b696-8d393d7eb2bb"},
            {"uuid": "0004b952-a513-430b-b696-8d393d7eb2bb"},
        ],
        "engagement": [],
        "visibility": None,
        "validity": {
            "from": "1985-05-19T00:00:00+02:00",
            "to": "2009-09-10T00:00:00+02:00",
        },
    }
    address_3 = {
        "uuid": "6063bd2a-905d-4089-a7de-e511f8f24edb",
        "value": "birgittad@kolding.dk",
        "address_type": {"uuid": "f376deb8-4743-4ca6-a047-3241de8fe9d2"},
        "person": [
            {"uuid": "0004b952-a513-430b-b696-8d393d7eb2bb"},
            {"uuid": "0004b952-a513-430b-b696-8d393d7eb2bb"},
        ],
        "engagement": None,
        "visibility": None,
        "validity": {
            "from": "1985-05-19T00:00:00+02:00",
            "to": "2009-09-10T00:00:00+02:00",
        },
    }
    address_4 = address_3.copy()
    graphql_response = {
        "employees": [
            {
                "objects": [
                    {"addresses": [address_1, address_3]},
                    {"addresses": [address_2, address_4]},
                ]
            }
        ]
    }
    mo_api.graphql_session.execute = AsyncMock(return_value=graphql_response)
    actual = await mo_api.get_employee_addresses(uuid=uuid4(), address_types=())
    actual_uuids = [a.uuid for a in actual]
    expected_uuids = [
        UUID("97d1d3e0-3d27-418d-8e87-35c4eb6ad660"),
        UUID("97d1d3e0-3d27-418d-8e87-35c4eb6ad660"),
        UUID("6063bd2a-905d-4089-a7de-e511f8f24edb"),
    ]
    TestCase().assertCountEqual(actual_uuids, expected_uuids)


async def test_get_employee_engagements(mo_api: MO) -> None:
    engagement_1 = {
        "uuid": "70b3d446-f4d9-4389-a5f8-c2111841cc11",
        "user_key": "foo",
        "org_unit_uuid": "b75740c3-86d3-4bbf-8831-120880371e94",
        "person": [
            {"uuid": "0004b952-a513-430b-b696-8d393d7eb2bb"},
            {"uuid": "0004b952-a513-430b-b696-8d393d7eb2bb"},
        ],
        "job_function": {"uuid": "b11e6033-bd1e-06a6-a653-d58810ecbffd"},
        "engagement_type": {"uuid": "4eae3fc5-7307-4ede-911f-90bf383aebcc"},
        "primary": {"uuid": "0644cd06-b84b-42e0-95fe-ce131c21fbe6"},
        "validity": {
            "from": "2030-06-15T00:00:00+02:00",
            "to": "2040-12-03T00:00:00+01:00",
        },
    }
    engagement_2 = {
        "uuid": "e854e044-4c7c-4501-909a-be2484a1c6d3",
        "user_key": "bar",
        "org_unit_uuid": "7764d0c7-e776-5f07-8a9d-5ee6f5b717b0",
        "person": [
            {"uuid": "0004b952-a513-430b-b696-8d393d7eb2bb"},
            {"uuid": "0004b952-a513-430b-b696-8d393d7eb2bb"},
        ],
        "job_function": {"uuid": "dadd4f24-9075-4b8c-a9ff-55d683381a76"},
        "engagement_type": {"uuid": "8acc5743-044b-4c82-9bb9-4e572d82b524"},
        "primary": {"uuid": "0644cd06-b84b-42e0-95fe-ce131c21fbe6"},
        "validity": {
            "from": "1985-05-19T00:00:00+02:00",
            "to": "2009-09-10T00:00:00+02:00",
        },
    }
    engagement_3 = {
        "uuid": "e854e044-4c7c-4501-909a-be2484a1c6d3",
        "user_key": "foo",
        "org_unit_uuid": "7764d0c7-e776-5f07-8a9d-5ee6f5b717b0",
        "person": [
            {"uuid": "0004b952-a513-430b-b696-8d393d7eb2bb"},
        ],
        "job_function": {"uuid": "dadd4f24-9075-4b8c-a9ff-55d683381a76"},
        "engagement_type": {"uuid": "8acc5743-044b-4c82-9bb9-4e572d82b524"},
        "primary": {"uuid": "0644cd06-b84b-42e0-95fe-ce131c21fbe6"},
        "validity": {
            "from": "1985-05-19T00:00:00+02:00",
            "to": "2009-09-10T00:00:00+02:00",
        },
    }
    engagement_4 = engagement_3.copy()
    graphql_response = {
        "employees": [
            {
                "objects": [
                    {"engagements": [engagement_1, engagement_3]},
                    {"engagements": [engagement_2, engagement_4]},
                ]
            }
        ]
    }
    mo_api.graphql_session.execute = AsyncMock(return_value=graphql_response)
    actual = await mo_api.get_employee_engagements(uuid=uuid4())
    actual_uuids = [a.uuid for a in actual]
    expected_uuids = [
        UUID("70b3d446-f4d9-4389-a5f8-c2111841cc11"),
        UUID("e854e044-4c7c-4501-909a-be2484a1c6d3"),
        UUID("e854e044-4c7c-4501-909a-be2484a1c6d3"),
    ]
    TestCase().assertCountEqual(actual_uuids, expected_uuids)


async def test_get_employee_it_users(mo_api: MO) -> None:
    it_system_1 = "a1608e69-c422-404f-a6cc-b873c50af111"
    it_system_2 = "1760947e-0496-1483-fba8-98af2b98ef4f"
    it_user_1 = {
        "uuid": "0b1607ac-50b5-449b-a83c-08f3f302d3d5",
        "user_key": "foo",
        "itsystem_uuid": it_system_1,
        "person": [
            {"uuid": "0004b952-a513-430b-b696-8d393d7eb2bb"},
            {"uuid": "0004b952-a513-430b-b696-8d393d7eb2bb"},
        ],
        "engagement": [
            {"uuid": "08823b92-5b12-4f99-aace-0dfd9018b885"},
        ],
        "validity": {
            "from": "1985-05-19T00:00:00+02:00",
            "to": "2009-09-10T00:00:00+02:00",
        },
    }
    it_user_2 = {
        "uuid": "0b1607ac-50b5-449b-a83c-08f3f302d3d5",
        "user_key": "bar",
        "itsystem_uuid": it_system_1,
        "person": [
            {"uuid": "0004b952-a513-430b-b696-8d393d7eb2bb"},
            {"uuid": "0004b952-a513-430b-b696-8d393d7eb2bb"},
        ],
        "engagement": [],
        "validity": {
            "from": "2030-06-15T00:00:00+02:00",
            "to": "2040-12-03T00:00:00+01:00",
        },
    }
    it_user_3 = {
        "uuid": "41ccf8e7-ebaf-4f1a-bf57-08c1c1ece92b",
        "user_key": "haz",
        "itsystem_uuid": it_system_2,
        "person": [
            {"uuid": "0004b952-a513-430b-b696-8d393d7eb2bb"},
        ],
        "engagement": None,
        "validity": {
            "from": "2030-06-15T00:00:00+02:00",
            "to": "2040-12-03T00:00:00+01:00",
        },
    }
    it_user_4 = it_user_3.copy()
    graphql_response = {
        "employees": [
            {
                "objects": [
                    {"itusers": [it_user_1, it_user_3]},
                    {"itusers": [it_user_2, it_user_4]},
                ]
            }
        ]
    }
    mo_api.graphql_session.execute = AsyncMock(return_value=graphql_response)
    actual = await mo_api.get_employee_it_users(
        uuid=uuid4(),
        it_systems=(UUID(it_system_1), UUID(it_system_2)),
    )
    actual_uuids = [a.uuid for a in actual]
    expected_uuids = [
        UUID("0b1607ac-50b5-449b-a83c-08f3f302d3d5"),
        UUID("0b1607ac-50b5-449b-a83c-08f3f302d3d5"),
        UUID("41ccf8e7-ebaf-4f1a-bf57-08c1c1ece92b"),
    ]
    TestCase().assertCountEqual(actual_uuids, expected_uuids)


async def test_get_org_unit_with_it_system_user_key(mo_api: MO) -> None:
    graphql_response = {
        "itusers": [
            {"objects": [{"org_unit_uuid": "f06ee470-9f17-566f-acbe-e938112d46d9"}]},
            {"objects": [{"org_unit_uuid": "f06ee470-9f17-566f-acbe-e938112d46d9"}]},
        ]
    }
    mo_api.graphql_session.execute = AsyncMock(return_value=graphql_response)
    actual = await mo_api.get_org_unit_with_it_system_user_key("foo")
    assert actual == UUID("f06ee470-9f17-566f-acbe-e938112d46d9")


async def test_get_org_unit_with_uuid(mo_api: MO) -> None:
    graphql_response = {"org_units": [{"uuid": "f06ee470-9f17-566f-acbe-e938112d46d9"}]}
    mo_api.graphql_session.execute = AsyncMock(return_value=graphql_response)
    actual = await mo_api.get_org_unit_with_uuid(uuid4())
    assert actual == UUID("f06ee470-9f17-566f-acbe-e938112d46d9")


async def test_get_org_unit_with_user_key(mo_api: MO) -> None:
    graphql_response = {"org_units": [{"uuid": "f06ee470-9f17-566f-acbe-e938112d46d9"}]}
    mo_api.graphql_session.execute = AsyncMock(return_value=graphql_response)
    actual = await mo_api.get_org_unit_with_user_key("foo")
    assert actual == UUID("f06ee470-9f17-566f-acbe-e938112d46d9")


async def test_get_org_unit_validity(mo_api: MO) -> None:
    graphql_response = {"org_units": [{"uuid": "f06ee470-9f17-566f-acbe-e938112d46d9"}]}
    mo_api.graphql_session.execute = AsyncMock(return_value=graphql_response)
    actual = await mo_api.get_org_unit_with_user_key("foo")
    assert actual == UUID("f06ee470-9f17-566f-acbe-e938112d46d9")


async def test_delete(mo_api: MO) -> None:
    mo_api.graphql_session.execute = AsyncMock()
    it_user = ITUser.from_simplified_fields(
        user_key="foo",
        itsystem_uuid=uuid4(),
        from_date="2012-01-01",
    )
    await mo_api.delete(it_user)
    mo_api.graphql_session.execute.assert_awaited_once_with(
        ANY, variable_values={"uuid": str(it_user.uuid)}
    )
