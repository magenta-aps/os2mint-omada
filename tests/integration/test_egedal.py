# SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
# mypy: disable-error-code="no-redef"
import unittest
from collections.abc import Callable

import pytest
from fastapi.testclient import TestClient
from gql import gql
from gql.client import AsyncClientSession
from more_itertools import one
from pytest import MonkeyPatch

from tests.integration.conftest import ASSERT_QUERY
from tests.integration.util import retry


# TODO: Test moving org unit


@pytest.fixture(autouse=True)
def set_customer(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("CUSTOMER", "egedal")


@pytest.fixture
async def org_unit(mo_graphql_session: AsyncClientSession) -> str:
    # Get org unit type
    query = gql(
        """
        query GetOrgUnitType {
          classes(filter: {facet_user_keys: "org_unit_type", user_keys: "Afdeling"}) {
            objects {
              uuid
            }
          }
        }
        """
    )
    result = await mo_graphql_session.execute(query)
    org_unit_type_uuid = one(result["classes"]["objects"])["uuid"]

    # Create org unit
    user_key = "Egedal Kommune"
    query = gql(
        """
        mutation CreateOrgUnit($user_key: String!, $org_unit_type: UUID!) {
          org_unit_create(
            input: {
              name: "Egedal Kommune",
              user_key: $user_key,
              org_unit_type: $org_unit_type,
              validity: {from: "2010-02-03"},
            },
          ) {
            uuid
          }
        }
        """
    )
    await mo_graphql_session.execute(
        query,
        variable_values=dict(
            user_key=user_key,
            org_unit_type=org_unit_type_uuid,
        ),
    )

    return user_key


@pytest.mark.integration_test
async def test_egedal_manual(
    omada_mock: Callable[[list], None],
    get_test_client: Callable[[], TestClient],
    mo_graphql_session: AsyncClientSession,
    org_unit: str,
) -> None:
    # Precondition: The person does not already exist
    cpr_number = "0902104607"
    result = await mo_graphql_session.execute(
        ASSERT_QUERY,
        variable_values=dict(cpr_number=cpr_number),
    )
    assert result == {"employees": {"objects": []}}

    # CREATE
    omada_user = {
        # Omada
        "Id": 1001307,
        "UId": "93f93362-3cb4-450a-a48a-ef975675b232",
        "VALIDFROM": "2010-02-09T00:00:00+01:00",
        "VALIDTO": "2010-03-26T00:00:00+01:00",
        "IDENTITYCATEGORY": {
            "Id": 561,
            "UId": "270a1807-95ca-40b4-9ce5-475d8961f31b",
            "Value": "Contractor",
        },
        # Employee
        "C_EMPLOYEEID": cpr_number,
        "C_OIS_FIRSTNAME": "The Lich",
        "C_OIS_LASTNAME": "King",
        # Employee (manual)
        "FIRSTNAME": "Arthas",
        "LASTNAME": "Menethil",
        # Engagements (manual)
        "EMPLOYMENTS": [
            {
                "Id": 1251824,
                "UId": "0e39ce2d-39a5-42b0-befb-f8380f9c789c",
                "KeyValue": None,
                "KeyProperty": None,
                "DisplayName": f"Prince ({org_unit} [LORDAERON]) ID:(00001337) ;",
            },
        ],
        # Addresses
        "EMAIL": "arthas@egepost.dk",
        "PHONE": "22334455",
        # IT Users
        "OBJECTGUID": "36-C9-80-88-A5-68-8A-47-BC-2C-2A-36-2C-AF-4E-7B",
    }
    omada_mock([omada_user])

    # TODO: Hard to work with dicts and sets. Will probably get better with codegen
    test_case = unittest.TestCase()
    test_case.maxDiff = None

    @retry()
    async def verify() -> None:
        result = await mo_graphql_session.execute(
            ASSERT_QUERY,
            variable_values=dict(cpr_number=cpr_number),
        )

        # Employee
        employee_states = one(result["employees"]["objects"])
        employee = one(employee_states["objects"])
        assert employee["cpr_number"] == cpr_number
        assert employee["given_name"] == "Arthas"
        assert employee["surname"] == "Menethil"
        assert employee["nickname_given_name"] == "The Lich"
        assert employee["nickname_surname"] == "King"
        assert employee["validity"] == {
            "from": "2010-02-09T00:00:00+01:00",
            "to": None,
        }

        # Engagement
        assert employee["engagements"] == [
            {
                "user_key": "1337",
                "org_unit": [{"user_key": "Egedal Kommune"}],
                "job_function": {"user_key": "not_applicable"},
                "engagement_type": {"user_key": "omada_manually_created"},
                "primary": {"user_key": "primary"},
                "validity": {
                    "from": "2010-02-09T00:00:00+01:00",
                    "to": "2010-03-26T00:00:00+01:00",
                },
            },
        ]

        # Addresses
        test_case.assertCountEqual(
            employee["addresses"],
            [
                {
                    "value": "arthas@egepost.dk",
                    "address_type": {"user_key": "OmadaEmailEmployee"},
                    "engagement": None,
                    "visibility": {"user_key": "Public"},
                    "validity": {
                        "from": "2010-02-09T00:00:00+01:00",
                        "to": "2010-03-26T00:00:00+01:00",
                    },
                },
                {
                    "value": "22334455",
                    "address_type": {"user_key": "OmadaPhoneEmployee"},
                    "engagement": None,
                    "visibility": {"user_key": "Public"},
                    "validity": {
                        "from": "2010-02-09T00:00:00+01:00",
                        "to": "2010-03-26T00:00:00+01:00",
                    },
                },
            ],
        )

        # IT Users
        assert employee["itusers"] == [
            {
                "user_key": "36c98088-a568-8a47-bc2c-2a362caf4e7b",
                "itsystem": {"user_key": "omada_ad_guid"},
                "engagement": None,
                "validity": {
                    "from": "2010-02-09T00:00:00+01:00",
                    "to": "2010-03-26T00:00:00+01:00",
                },
            }
        ]

    with get_test_client():
        await verify()

    # EDIT
    updated_omada_user = {
        **omada_user,
        # Employee
        "C_OIS_FIRSTNAME": "Mr M.",
        # Employee (manual)
        "FIRSTNAME": "The King",
        # Engagements (manual)
        "EMPLOYMENTS": omada_user["EMPLOYMENTS"]
        + [  # type: ignore[operator]
            {
                "Id": 6849240,
                "UId": "7884a4f1-948c-460a-9cc7-47bdc031d841",
                "KeyValue": None,
                "KeyProperty": None,
                "DisplayName": f"Sygeplejerske ({org_unit} [SYGEPLEJE (V)]) ID:(00001234) ;",
            },
        ],
        # Addresses
        "EMAIL": "thelichking@egepost.dk",
        "PHONE": None,  # deleted
        "CELLPHONE": "55443322",
        # IT Users
        "OBJECTGUID": "11-22-33-44-55-66-77-88-99-00-AA-BB-CC-DD-EE-FF",
        "C_ADUSERNAME": "LK1337",
    }
    omada_mock([updated_omada_user])

    @retry()
    async def verify() -> None:
        result = await mo_graphql_session.execute(
            ASSERT_QUERY,
            variable_values=dict(cpr_number=cpr_number),
        )

        # Employee
        employee_states = one(result["employees"]["objects"])
        employee = one(employee_states["objects"])
        assert employee["given_name"] == "The King"
        assert employee["nickname_given_name"] == "Mr M."

        # Engagement
        test_case.assertCountEqual(
            employee["engagements"],
            [
                {
                    "user_key": "1337",
                    "org_unit": [{"user_key": "Egedal Kommune"}],
                    "job_function": {"user_key": "not_applicable"},
                    "engagement_type": {"user_key": "omada_manually_created"},
                    "primary": {"user_key": "primary"},
                    "validity": {
                        "from": "2010-02-09T00:00:00+01:00",
                        "to": "2010-03-26T00:00:00+01:00",
                    },
                },
                {
                    "user_key": "1234",
                    "org_unit": [{"user_key": "Egedal Kommune"}],
                    "job_function": {"user_key": "Sygeplejerske"},
                    "engagement_type": {"user_key": "omada_manually_created"},
                    "primary": {"user_key": "primary"},
                    "validity": {
                        "from": "2010-02-09T00:00:00+01:00",
                        "to": "2010-03-26T00:00:00+01:00",
                    },
                },
            ],
        )

        # Addresses
        assert {a["value"] for a in employee["addresses"]} == {
            "thelichking@egepost.dk",
            "55443322",
        }

        # IT Users
        assert {u["user_key"] for u in employee["itusers"]} == {
            "11223344-5566-7788-9900-aabbccddeeff",
            "LK1337",
        }

    with get_test_client():
        await verify()

    # DELETE
    omada_mock([])

    @retry()
    async def verify() -> None:
        result = await mo_graphql_session.execute(
            ASSERT_QUERY,
            variable_values=dict(cpr_number=cpr_number),
        )
        employee_states = one(result["employees"]["objects"])
        employee = one(employee_states["objects"])
        assert employee["engagements"] == []
        assert employee["addresses"] == []
        assert employee["itusers"] == []

    with get_test_client():
        await verify()
