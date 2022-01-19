# SPDX-FileCopyrightText: 2021 Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from uuid import UUID
from uuid import uuid4

import pytest
from respx import MockRouter

from os2mint_omada import mo
from os2mint_omada.config import settings


@pytest.fixture
def alice() -> UUID:
    return UUID("1703636c-3017-46df-8219-d026b26649a4")


@pytest.fixture
def bob() -> UUID:
    return UUID("c9a8dc60-b4ec-46de-b5fc-f4e491a4967c")


@pytest.mark.asyncio
async def test_get_it_system_uuid(
    root_org_uuid: UUID, it_system_uuid: UUID, respx_mock: MockRouter
) -> None:
    respx_mock.get(url=f"{settings.mo_url}/service/o/{root_org_uuid}/it/").respond(
        json=[
            {"uuid": str(it_system_uuid), "user_key": "needle"},
            {"uuid": str(uuid4()), "user_key": "haystack"},
        ]
    )

    actual = await mo.get_it_system_uuid(
        organisation_uuid=root_org_uuid,
        user_key="needle",
    )

    assert actual == it_system_uuid


@pytest.mark.asyncio
async def test_get_it_system_uuid_no_exist(
    root_org_uuid: UUID, respx_mock: MockRouter
) -> None:
    respx_mock.get(url=f"{settings.mo_url}/service/o/{root_org_uuid}/it/").respond(
        json=[
            {"uuid": str(uuid4()), "user_key": "haystack"},
        ]
    )

    with pytest.raises(KeyError):
        await mo.get_it_system_uuid(
            organisation_uuid=root_org_uuid,
            user_key="needle",
        )


@pytest.mark.asyncio
async def test_get_it_users(
    alice: UUID, bob: UUID, it_system_uuid: UUID, respx_mock: MockRouter
) -> None:
    validity = {"from": "1900-01-01T00:00:00+01:00", "to": None}
    omada = {
        "uuid": str(it_system_uuid),
        "name": "Omada",
        "user_key": "omada_ad_guid",
        "validity": validity,
    }
    active_directory = {
        "uuid": str(uuid4()),
        "name": "Active Directory",
        "user_key": "AD",
        "validity": validity,
    }
    respx_mock.get(url=f"{settings.mo_url}/api/v1/it").respond(
        json=[
            {  # Omada IT user
                "uuid": str(uuid4()),
                "user_key": "Omada IT user",
                "validity": validity,
                "itsystem": omada,
                "person": {"uuid": str(alice)},
            },
            {  # Omada IT user 2
                "uuid": str(uuid4()),
                "user_key": "Omada IT user 2",
                "validity": validity,
                "itsystem": omada,
                "person": {"uuid": str(bob)},
            },
            {  # Omada IT user - but no person. Should be ignored.
                "uuid": str(uuid4()),
                "user_key": "No Person",
                "validity": validity,
                "itsystem": omada,
                "person": None,
            },
            {  # AD IT user. Should be ignored.
                "uuid": str(uuid4()),
                "user_key": "AD IT user",
                "validity": validity,
                "itsystem": active_directory,
                "person": {"uuid": str(bob)},
            },
        ]
    )

    actual = await mo.get_it_users(it_system=it_system_uuid)

    assert actual.keys() == {alice, bob}
    assert all(it_user.itsystem.uuid == it_system_uuid for it_user in actual.values())


@pytest.mark.asyncio
async def test_get_user_addresses(alice: UUID, respx_mock: MockRouter) -> None:
    validity = {"from": "1999-12-13T00:00:00+01:00", "to": None}
    email = {"uuid": str(uuid4()), "user_key": "EmailEmployee"}
    phone = {"uuid": str(uuid4()), "user_key": "PhoneEmployee"}
    respx_mock.get(url=f"{settings.mo_url}/api/v1/address").respond(
        json=[
            {
                "uuid": str(uuid4()),
                "person": {"uuid": str(alice)},
                "address_type": email,
                "value": "email",
                "value2": "email2",
                "visibility": {"uuid": str(uuid4())},
                "org_unit": {"uuid": str(uuid4())},
                "engagement": {"uuid": str(uuid4())},
                "validity": validity,
            },
            {
                "uuid": str(uuid4()),
                "person": {"uuid": str(alice)},
                "address_type": phone,
                "value": "phone",
                "value2": None,
                "visibility": None,
                "org_unit": None,
                "engagement": None,
                "validity": validity,
            },
            {
                "uuid": str(uuid4()),
                "person": {"uuid": str(alice)},
                "address_type": phone,
                "value": "another phone",
                "value2": None,
                "visibility": None,
                "org_unit": None,
                "engagement": None,
                "validity": validity,
            },
            {
                "uuid": str(uuid4()),
                "person": None,
                "address_type": phone,
                "value": "no owner",
                "value2": None,
                "visibility": None,
                "org_unit": None,
                "engagement": None,
                "validity": validity,
            },
        ]
    )

    actual = await mo.get_user_addresses()

    assert actual.keys() == {alice}
    assert actual[alice].keys() == {"EmailEmployee", "PhoneEmployee"}
