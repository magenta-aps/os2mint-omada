# SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
# mypy: disable-error-code="no-redef"
import unittest
from collections.abc import Callable
from datetime import datetime
from datetime import timedelta
from datetime import timezone

import pytest
from fastapi.testclient import TestClient
from fastramqpi.pytest_util import retry
from more_itertools import one
from pytest import MonkeyPatch

from os2mint_omada.autogenerated_graphql_client import GraphQLClient


# TODO: Test moving org unit


@pytest.fixture(autouse=True)
def set_customer(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("CUSTOMER", "silkeborg")


@pytest.fixture
async def org_unit(graphql_client: GraphQLClient) -> str:
    # Get org unit type
    result = await graphql_client._testing__get_org_unit_type()
    org_unit_type_uuid = one(result.objects).uuid

    # Create org unit
    user_key = "Silkeborg Kommune"
    org_unit = await graphql_client._testing__create_org_unit(
        user_key=user_key,
        org_unit_type=org_unit_type_uuid,
    )
    org_unit_uuid = org_unit.uuid

    # Get it-system uuid
    it_systems = await graphql_client._testing__get_it_system(user_key="FK-ORG-UUID")
    it_system_uuid = one(it_systems.objects).uuid

    # Create IT-user with FK-org UUID for the org unit
    it_user_user_key = "77d2c378-92d2-462d-876d-58bb7f4e98a1"
    await graphql_client._testing__create_org_unit_it_user(
        user_key=it_user_user_key,
        it_system=it_system_uuid,
        org_unit=org_unit_uuid,
    )

    return it_user_user_key


@pytest.mark.integration_test
async def test_silkeborg_manual(
    omada_mock: Callable[[list], None],
    test_client: TestClient,
    graphql_client: GraphQLClient,
    org_unit: str,
) -> None:
    # Precondition: The person does not already exist
    cpr_number = "1709933104"
    employee = await graphql_client._testing__get_employee(cpr_number)
    assert employee.objects == []

    # CREATE
    omada_user = {
        # Omada
        "Id": "1041094",
        "UId": "38e4a0f1-1290-40e3-ad83-896abd1d3e50",
        "VALIDFROM": "2012-08-27T00:00:00+02:00",
        "VALIDTO": "2022-12-01T01:00:00+01:00",
        "IDENTITYCATEGORY": {"Id": 561, "UId": "270a1807-95ca-40b4-9ce5-475d8961f31b"},
        # Engagement
        "C_TJENESTENR": "v1216",
        # IT Users
        "C_OBJECTGUID_I_AD": "74dea272-d90b-47c7-8d99-c8efa372fa03",
        # Addresses
        "EMAIL": "Mia.Hansen@silkeborg.dk",
        "C_DIREKTE_TLF": "",
        "CELLPHONE": "12345678",
        "C_INST_PHONE": None,
        # Employee (manual)
        "C_FORNAVNE": "Mia",
        "LASTNAME": "Hansen",
        "C_CPRNR": cpr_number,
        # Engagement (manual)
        "JOBTITLE": "Medarbejder",
        "C_ORGANISATIONSKODE": org_unit,
        "C_SYNLIG_I_OS2MO": False,
    }
    omada_mock([omada_user])

    test_case = unittest.TestCase()
    test_case.maxDiff = None

    @retry()
    async def verify() -> None:
        employees = await graphql_client._testing__get_employee(cpr_number)

        # Employee
        employee_states = one(employees.objects)
        employee = one(employee_states.objects)
        assert employee.cpr_number == cpr_number
        assert employee.given_name == "Mia"
        assert employee.surname == "Hansen"
        assert employee.validity.from_ == datetime(
            1993, 9, 17, 0, 0, tzinfo=timezone(timedelta(hours=2))
        )
        assert employee.validity.to is None

        # Engagement
        test_case.assertCountEqual(
            [e.dict() for e in employee.engagements],
            [
                {
                    "user_key": "v1216",
                    "org_unit": [{"user_key": "Silkeborg Kommune"}],
                    "job_function": {"user_key": "Medarbejder"},
                    "engagement_type": {"user_key": "omada_manually_created_hidden"},
                    "primary": {"user_key": "primary"},
                    "validity": {
                        "from_": datetime(
                            2012, 8, 27, 0, 0, tzinfo=timezone(timedelta(hours=2))
                        ),
                        "to": datetime(
                            2022, 12, 1, 0, 0, tzinfo=timezone(timedelta(hours=1))
                        ),
                    },
                }
            ],
        )

        # Addresses
        test_case.assertCountEqual(
            [a.dict() for a in employee.addresses],
            [
                {
                    "value": "Mia.Hansen@silkeborg.dk",
                    "address_type": {"user_key": "EmailEmployee"},
                    "engagement": [{"user_key": "v1216"}],
                    "visibility": {"user_key": "Public"},
                    "validity": {
                        "from_": datetime(
                            2012, 8, 27, 0, 0, tzinfo=timezone(timedelta(hours=2))
                        ),
                        "to": datetime(
                            2022, 12, 1, 0, 0, tzinfo=timezone(timedelta(hours=1))
                        ),
                    },
                },
                {
                    "value": "12345678",
                    "address_type": {"user_key": "MobilePhoneEmployee"},
                    "engagement": [{"user_key": "v1216"}],
                    "visibility": {"user_key": "Public"},
                    "validity": {
                        "from_": datetime(
                            2012, 8, 27, 0, 0, tzinfo=timezone(timedelta(hours=2))
                        ),
                        "to": datetime(
                            2022, 12, 1, 0, 0, tzinfo=timezone(timedelta(hours=1))
                        ),
                    },
                },
            ],
        )

        # IT Users
        test_case.assertCountEqual(
            [u.dict() for u in employee.itusers],
            [
                {
                    "user_key": "74dea272-d90b-47c7-8d99-c8efa372fa03",
                    "itsystem": {"user_key": "omada_ad_guid"},
                    "engagement": [{"user_key": "v1216"}],
                    "validity": {
                        "from_": datetime(
                            2012, 8, 27, 0, 0, tzinfo=timezone(timedelta(hours=2))
                        ),
                        "to": datetime(
                            2022, 12, 1, 0, 0, tzinfo=timezone(timedelta(hours=1))
                        ),
                    },
                }
            ],
        )

    await verify()

    # EDIT
    updated_omada_user = {
        **omada_user,
        # Addresses
        "EMAIL": "Alice@silkeborg.dk",
        "C_DIREKTE_TLF": "19890604",
        "CELLPHONE": None,  # deleted
        # IT Users
        "C_LOGIN": "DRV1216",
        # Employee (manual)
        "C_FORNAVNE": "Alice",
        # Engagement (manual)
        "JOBTITLE": "Something That Doesn't Exist in MO",
        "C_SYNLIG_I_OS2MO": True,
    }
    omada_mock([updated_omada_user])

    @retry()
    async def verify() -> None:
        employees = await graphql_client._testing__get_employee(cpr_number)

        # Employee
        employee_states = one(employees.objects)
        employee = one(employee_states.objects)
        # Existing employees in Silkeborg must never be modified, so the name should be
        # unchanged.
        assert employee.given_name == "Mia"

        # Engagement
        test_case.assertCountEqual(
            [e.dict() for e in employee.engagements],
            [
                {
                    "user_key": "v1216",
                    "org_unit": [{"user_key": "Silkeborg Kommune"}],
                    "job_function": {"user_key": "not_applicable"},
                    "engagement_type": {"user_key": "omada_manually_created"},
                    "primary": {"user_key": "primary"},
                    "validity": {
                        "from_": datetime(
                            2012, 8, 27, 0, 0, tzinfo=timezone(timedelta(hours=2))
                        ),
                        "to": datetime(
                            2022, 12, 1, 0, 0, tzinfo=timezone(timedelta(hours=1))
                        ),
                    },
                },
            ],
        )

        # Addresses
        assert {a.value for a in employee.addresses} == {
            "Alice@silkeborg.dk",
            "19890604",
        }

        # IT Users
        assert {u.user_key for u in employee.itusers} == {
            "74dea272-d90b-47c7-8d99-c8efa372fa03",
            "DRV1216",
        }

    await verify()

    # DELETE
    omada_mock([])

    @retry()
    async def verify() -> None:
        employees = await graphql_client._testing__get_employee(cpr_number)
        employee_states = one(employees.objects)
        employee = one(employee_states.objects)
        assert employee.engagements == []
        assert employee.addresses == []
        assert employee.itusers == []

    await verify()
