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
    monkeypatch.setenv("CUSTOMER", "silkeborg")


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
    query = gql(
        """
        mutation CreateOrgUnit($org_unit_type: UUID!) {
          org_unit_create(
            input: {
              name: "Silkeborg Kommune",
              user_key: "Silkeborg Kommune",
              org_unit_type: $org_unit_type,
              validity: {from: "2010-02-03"},
            },
          ) {
            uuid
          }
        }
        """
    )
    result = await mo_graphql_session.execute(
        query,
        variable_values=dict(
            org_unit_type=org_unit_type_uuid,
        ),
    )
    org_unit_uuid = result["org_unit_create"]["uuid"]

    # Get it-system uuid
    query = gql(
        """
        query GetITSystem {
          itsystems(filter: {user_keys: "FK-ORG-UUID"}) {
            objects {
              uuid
            }
          }
        }
        """
    )
    result = await mo_graphql_session.execute(query)
    it_system_uuid = one(result["itsystems"]["objects"])["uuid"]

    # Create IT-user with FK-org UUID for the org unit
    it_user_user_key = "f06ee470-9f17-566f-acbe-e938112d46d9"
    query = gql(
        """
        mutation CreateOrgUnitITUser(
          $user_key: String!,
          $it_system: UUID!,
          $org_unit: UUID!
        ) {
          ituser_create(
            input: {
              user_key: $user_key,
              itsystem: $it_system,
              org_unit: $org_unit,
              validity: {from: "2010-02-03"},
            }
          ) {
            uuid
          }
        }
        """
    )
    await mo_graphql_session.execute(
        query,
        variable_values=dict(
            user_key=it_user_user_key,
            it_system=it_system_uuid,
            org_unit=org_unit_uuid,
        ),
    )

    return it_user_user_key


@pytest.mark.integration_test
async def test_silkeborg_manual(
    omada_mock: Callable[[list], None],
    get_test_client: Callable[[], TestClient],
    mo_graphql_session: AsyncClientSession,
    org_unit: str,
) -> None:
    # Precondition: The person does not already exist
    cpr_number = "1709933104"
    result = await mo_graphql_session.execute(
        ASSERT_QUERY,
        variable_values=dict(cpr_number=cpr_number),
    )
    assert result == {"employees": {"objects": []}}

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
        assert employee["given_name"] == "Mia"
        assert employee["surname"] == "Hansen"
        assert employee["validity"] == {
            "from": "1993-09-17T00:00:00+02:00",
            "to": None,
        }

        # Engagement
        assert employee["engagements"] == [
            {
                "user_key": "v1216",
                "org_unit": [{"user_key": "Silkeborg Kommune"}],
                "job_function": {"user_key": "Medarbejder"},
                "engagement_type": {"user_key": "omada_manually_created_hidden"},
                "primary": {"user_key": "primary"},
                "validity": {
                    "from": "2012-08-27T00:00:00+02:00",
                    "to": "2022-12-01T00:00:00+01:00",
                },
            }
        ]

        # Addresses
        test_case.assertCountEqual(
            employee["addresses"],
            [
                {
                    "value": "Mia.Hansen@silkeborg.dk",
                    "address_type": {"user_key": "EmailEmployee"},
                    "engagement": [{"user_key": "v1216"}],
                    "visibility": {"user_key": "Public"},
                    "validity": {
                        "from": "2012-08-27T00:00:00+02:00",
                        "to": "2022-12-01T00:00:00+01:00",
                    },
                },
                {
                    "value": "12345678",
                    "address_type": {"user_key": "MobilePhoneEmployee"},
                    "engagement": [{"user_key": "v1216"}],
                    "visibility": {"user_key": "Public"},
                    "validity": {
                        "from": "2012-08-27T00:00:00+02:00",
                        "to": "2022-12-01T00:00:00+01:00",
                    },
                },
            ],
        )

        # IT Users
        assert employee["itusers"] == [
            {
                "user_key": "74dea272-d90b-47c7-8d99-c8efa372fa03",
                "itsystem": {"user_key": "omada_ad_guid"},
                "engagement": [{"user_key": "v1216"}],
                "validity": {
                    "from": "2012-08-27T00:00:00+02:00",
                    "to": "2022-12-01T00:00:00+01:00",
                },
            }
        ]

    with get_test_client():
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
        result = await mo_graphql_session.execute(
            ASSERT_QUERY,
            variable_values=dict(cpr_number=cpr_number),
        )

        # Employee
        employee_states = one(result["employees"]["objects"])
        employee = one(employee_states["objects"])
        # Existing employees in Silkeborg must never be modified, so the name should be
        # unchanged.
        assert employee["given_name"] == "Mia"

        # Engagement
        engagement = one(employee["engagements"])
        assert engagement["job_function"]["user_key"] == "not_applicable"
        assert engagement["engagement_type"]["user_key"] == "omada_manually_created"

        # Addresses
        assert {a["value"] for a in employee["addresses"]} == {
            "Alice@silkeborg.dk",
            "19890604",
        }

        # IT Users
        assert {u["user_key"] for u in employee["itusers"]} == {
            "74dea272-d90b-47c7-8d99-c8efa372fa03",
            "DRV1216",
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
