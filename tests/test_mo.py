# SPDX-FileCopyrightText: 2021 Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from unittest.mock import MagicMock
from unittest.mock import patch
from uuid import UUID

import pytest
from ramodels.mo import FacetClass
from ramodels.mo._shared import AddressType
from ramodels.mo._shared import EngagementRef
from ramodels.mo._shared import ITSystemRef
from ramodels.mo._shared import OrgUnitRef
from ramodels.mo._shared import PersonRef
from ramodels.mo._shared import Validity
from ramodels.mo._shared import Visibility
from ramodels.mo.details import Address
from ramodels.mo.details import ITSystemBinding
from respx import MockRouter

from os2mint_omada import mo
from os2mint_omada.config import settings


@pytest.fixture
def mo_root_org(respx_mock: MockRouter, root_org_uuid: UUID) -> UUID:
    respx_mock.post(
        url=f"{settings.mo_url}/graphql",
        json={"query": "query RootOrgQuery {\n  org {\n    uuid\n  }\n}\n"},
    ).respond(
        json={
            "data": {
                "org": {
                    "uuid": str(root_org_uuid),
                },
            },
        }
    )

    return root_org_uuid


@pytest.fixture
def mo_employee_address_type_facet(respx_mock: MockRouter, root_org_uuid: UUID) -> UUID:
    employee_address_type_uuid = UUID("71f2170d-247a-4269-b300-a8d979f2ee97")

    respx_mock.get(
        url=f"{settings.mo_url}/service/o/{root_org_uuid}/f/employee_address_type/"
    ).respond(
        json={
            "uuid": str(employee_address_type_uuid),
            "data": {
                "items": [
                    {
                        "uuid": "b74acef9-6ec1-4056-9a20-0b5dcb807715",
                        "name": "Telefon",
                        "user_key": "PhoneEmployee",
                        "scope": "PHONE",
                    },
                    {
                        "uuid": "966151f2-e9d8-40b8-9cde-07078fb3d2d0",
                        "name": "Postadresse",
                        "user_key": "AdressePostEmployee",
                        "scope": "DAR",
                    },
                    {
                        "uuid": "63c42e3b-8454-4aa4-8f27-d838cb92bc76",
                        "name": "Email",
                        "user_key": "EmailEmployee",
                        "scope": "EMAIL",
                    },
                ],
            },
        }
    )
    return employee_address_type_uuid


@pytest.fixture
def mock_mo_it_bindings(respx_mock: MockRouter, it_system_uuid: UUID) -> None:
    omada_it_system = {
        "uuid": str(it_system_uuid),
        "name": "Omada",
        "user_key": "OMADA_AD_GUID",
        "validity": {"from": "1900-01-01T00:00:00+01:00", "to": None},
    }
    active_directory_it_system = {
        "uuid": "1b0f3584-228e-46e1-a360-feea91541229",
        "name": "Active Directory",
        "user_key": "AD",
        "validity": {"from": "1900-01-01T00:00:00+01:00", "to": None},
    }
    louis_heinisch_person = {"uuid": "1703636c-3017-46df-8219-d026b26649a4"}
    peder_aspman_person = {"uuid": "c9a8dc60-b4ec-46de-b5fc-f4e491a4967c"}
    respx_mock.get(url=f"{settings.mo_url}/api/v1/it").respond(
        json=[
            {  # Omada IT user
                "uuid": "0016e2e3-76ae-454c-a2a5-588b521a9ec0",
                "user_key": "LouisL-Omada",
                "validity": {"from": "1975-10-09T00:00:00+01:00", "to": None},
                "itsystem": omada_it_system,
                "person": louis_heinisch_person,
            },
            {  # Omada IT user 2
                "uuid": "873528b9-1b02-4be8-98d9-659b897dd4db",
                "user_key": "PederR-Omada",
                "validity": {"from": "1984-09-21T00:00:00+02:00", "to": None},
                "itsystem": omada_it_system,
                "person": peder_aspman_person,
            },
            {  # Omada IT user - but no person. Should be ignored.
                "uuid": "0016e2e3-76ae-454c-a2a5-588b521a9ec0",
                "user_key": "None-Omada",
                "validity": {"from": "1975-10-09T00:00:00+01:00", "to": None},
                "itsystem": omada_it_system,
                "person": None,
            },
            {  # AD IT user. Should be ignored.
                "uuid": "0016e2e3-76ae-454c-a2a5-588b521a9ec0",
                "user_key": "LouisL-AD",
                "validity": {"from": "1975-10-09T00:00:00+01:00", "to": None},
                "itsystem": active_directory_it_system,
                "person": louis_heinisch_person,
            },
        ]
    )


@pytest.fixture
def mock_mo_engagements(respx_mock: MockRouter) -> None:
    respx_mock.get(url=f"{settings.mo_url}/api/v1/engagement").respond(
        json=[
            {
                "uuid": "57945e0e-e622-430e-9474-de31b17a840c",
                "user_key": "user1",
                "person": {"uuid": "17e345f8-1e3e-4f59-8321-d83a49d9d4c0"},
            },
            {
                "uuid": "20a094fa-45e0-4f09-924d-70c34586c613",
                "user_key": "user2",
                "person": {"uuid": "6d64bc4b-c9ed-49d5-9f49-4f3a744ba89e"},
            },
        ]
    )


@pytest.fixture
def mock_mo_addresses(respx_mock: MockRouter) -> None:
    respx_mock.get(url=f"{settings.mo_url}/api/v1/address").respond(
        json=[
            {
                "uuid": "8c2ccf09-b549-4ff1-9154-f7abf2abd450",
                "address_type": {
                    "uuid": "da873fbb-053e-479b-950f-d34b93b88f85",
                    "user_key": "InstitutionPhoneEmployee",
                },
                "value": "my value",
                "value2": None,
                "visibility": None,
                "person": None,
                "org_unit": None,
                "engagement": None,
                "validity": {"from": "1983-10-27T00:00:00+01:00", "to": None},
            },
            {
                "uuid": "8c2ccf09-b549-4ff1-9154-f7abf2abd450",
                "address_type": {
                    "uuid": "da873fbb-053e-479b-950f-d34b93b88f85",
                    "user_key": "EmailEmployee",
                },
                "value": "the value",
                "value2": "the second value",
                "visibility": {"uuid": "58bdf4fc-75bd-469c-9c8d-663349ab55bc"},
                "person": {"uuid": "aa5df095-82ca-46e2-8d92-049c35469de1"},
                "org_unit": {"uuid": "f34fa693-37a3-443b-ad63-3d3a48956097"},
                "engagement": {"uuid": "e0481c44-4fad-43ad-be01-100bf58629a2"},
                "validity": {
                    "from": "1965-04-04T00:00:00+01:00",
                    "to": "1999-12-02T00:00:00+01:00",
                },
            },
            {  # Same person as above, but phone
                "uuid": "8a57c6b7-e082-4e2d-820b-65d83f4af536",
                "address_type": {
                    "uuid": "37c3e0bf-dc13-4191-aefe-d2204672c4fe",
                    "user_key": "PhoneEmployee",
                },
                "value": "+45 12 34 56 78",
                "value2": None,
                "visibility": None,
                "person": {"uuid": "aa5df095-82ca-46e2-8d92-049c35469de1"},
                "org_unit": None,
                "engagement": None,
                "validity": {"from": "2019-03-22T00:00:00+01:00", "to": None},
            },
            {  # Another phone for the same person
                "uuid": "a9828e40-10de-4697-8963-0384733efb02",
                "address_type": {
                    "uuid": "37c3e0bf-dc13-4191-aefe-d2204672c4fe",
                    "user_key": "PhoneEmployee",
                },
                "value": "+45 11 22 33 44",
                "value2": None,
                "visibility": None,
                "person": {"uuid": "aa5df095-82ca-46e2-8d92-049c35469de1"},
                "org_unit": None,
                "engagement": None,
                "validity": {"from": "1999-12-13T00:00:00+01:00", "to": None},
            },
        ]
    )


@pytest.mark.asyncio
async def test_get_root_org(mo_root_org: UUID) -> None:
    assert await mo.get_root_org() == mo_root_org


@pytest.mark.asyncio
@patch(
    "ramodels.mo._shared.uuid4",
    return_value=UUID("61769f87-fbf4-4a7e-a59a-e03eb2ce895b"),
)
@patch("raclients.mo.modelclient.ModelClient.context")
async def test_ensure_address_classes(
    uuid_mock: MagicMock,
    context_mock: MagicMock,
    root_org_uuid: UUID,
    mo_employee_address_type_facet: UUID,
) -> None:
    with patch("raclients.mo.modelclient.ModelClient.load_mo_objs") as load_mock:
        await mo.ensure_address_classes(root_org=root_org_uuid)

    load_mock.assert_called_once()
    created_objs = load_mock.call_args.args[0]
    expected = {
        FacetClass(
            facet_uuid=mo_employee_address_type_facet,
            name="Institutionstelefonnummer",
            user_key="InstitutionPhoneEmployee",
            scope="PHONE",
            org_uuid=root_org_uuid,
        ),
        FacetClass(
            facet_uuid=mo_employee_address_type_facet,
            name="Mobiltelefon",
            user_key="MobilePhoneEmployee",
            scope="PHONE",
            org_uuid=root_org_uuid,
        ),
    }
    assert set(created_objs) == expected


@pytest.mark.asyncio
async def test_get_it_bindings(it_system_uuid: UUID, mock_mo_it_bindings: None) -> None:
    expected = {
        UUID("1703636c-3017-46df-8219-d026b26649a4"): ITSystemBinding(
            uuid=UUID("0016e2e3-76ae-454c-a2a5-588b521a9ec0"),
            user_key="LouisL-Omada",
            itsystem=ITSystemRef(uuid=it_system_uuid),
            person=PersonRef(uuid=UUID("1703636c-3017-46df-8219-d026b26649a4")),
            validity=Validity(from_date="1975-10-09T00:00:00+01:00", to_date=None),
        ),
        UUID("c9a8dc60-b4ec-46de-b5fc-f4e491a4967c"): ITSystemBinding(
            uuid=UUID("873528b9-1b02-4be8-98d9-659b897dd4db"),
            user_key="PederR-Omada",
            itsystem=ITSystemRef(uuid=it_system_uuid),
            person=PersonRef(uuid=UUID("c9a8dc60-b4ec-46de-b5fc-f4e491a4967c")),
            validity=Validity(from_date="1984-09-21T00:00:00+02:00", to_date=None),
        ),
    }
    assert await mo.get_it_bindings(it_system=it_system_uuid) == expected


@pytest.mark.asyncio
async def test_get_engagements(mock_mo_engagements: None) -> None:
    expected = [
        {
            "uuid": "57945e0e-e622-430e-9474-de31b17a840c",
            "user_key": "user1",
            "person": {"uuid": "17e345f8-1e3e-4f59-8321-d83a49d9d4c0"},
        },
        {
            "uuid": "20a094fa-45e0-4f09-924d-70c34586c613",
            "user_key": "user2",
            "person": {"uuid": "6d64bc4b-c9ed-49d5-9f49-4f3a744ba89e"},
        },
    ]
    assert await mo.get_engagements() == expected


@pytest.mark.asyncio
async def test_get_user_addresses(mock_mo_addresses: None) -> None:
    expected = {
        UUID("aa5df095-82ca-46e2-8d92-049c35469de1"): {
            "EmailEmployee": [
                Address(
                    uuid=UUID("8c2ccf09-b549-4ff1-9154-f7abf2abd450"),
                    address_type=AddressType(
                        uuid=UUID("da873fbb-053e-479b-950f-d34b93b88f85")
                    ),
                    value="the value",
                    value2="the second value",
                    visibility=Visibility(
                        uuid=UUID("58bdf4fc-75bd-469c-9c8d-663349ab55bc")
                    ),
                    person=PersonRef(uuid=UUID("aa5df095-82ca-46e2-8d92-049c35469de1")),
                    org_unit=OrgUnitRef(uuid="f34fa693-37a3-443b-ad63-3d3a48956097"),
                    engagement=EngagementRef(
                        uuid=UUID("e0481c44-4fad-43ad-be01-100bf58629a2")
                    ),
                    validity=Validity(
                        from_date="1965-04-04T00:00:00+01:00",
                        to_date="1999-12-02T00:00:00+01:00",
                    ),
                )
            ],
            "PhoneEmployee": [
                Address(
                    uuid=UUID("8a57c6b7-e082-4e2d-820b-65d83f4af536"),
                    address_type=AddressType(
                        uuid=UUID("37c3e0bf-dc13-4191-aefe-d2204672c4fe")
                    ),
                    value="+45 12 34 56 78",
                    value2=None,
                    visibility=None,
                    person=PersonRef(uuid=UUID("aa5df095-82ca-46e2-8d92-049c35469de1")),
                    org_unit=None,
                    engagement=None,
                    validity=Validity(
                        from_date="2019-03-22T00:00:00+01:00", to_date=None
                    ),
                ),
                Address(
                    uuid=UUID("a9828e40-10de-4697-8963-0384733efb02"),
                    address_type=AddressType(
                        uuid=UUID("37c3e0bf-dc13-4191-aefe-d2204672c4fe")
                    ),
                    value="+45 11 22 33 44",
                    value2=None,
                    visibility=None,
                    person=PersonRef(uuid=UUID("aa5df095-82ca-46e2-8d92-049c35469de1")),
                    org_unit=None,
                    engagement=None,
                    validity=Validity(
                        from_date="1999-12-13T00:00:00+01:00", to_date=None
                    ),
                ),
            ],
        }
    }
    assert await mo.get_user_addresses() == expected
