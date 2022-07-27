# SPDX-FileCopyrightText: 2022 Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

import pytest
from more_itertools import one
from ramodels.mo import Employee
from ramodels.mo import Validity
from ramodels.mo._shared import AddressType
from ramodels.mo._shared import EngagementType
from ramodels.mo._shared import JobFunction
from ramodels.mo._shared import OrgUnitRef
from ramodels.mo._shared import PersonRef
from ramodels.mo._shared import Primary
from ramodels.mo._shared import Visibility
from ramodels.mo.details import Address
from ramodels.mo.details import Engagement

from os2mint_omada.backing.omada.models import IdentityCategory
from os2mint_omada.backing.omada.models import ManualOmadaUser
from os2mint_omada.backing.omada.models import OmadaUser
from os2mint_omada.config import MoSettings
from os2mint_omada.sync.base import Syncer
from tests.conftest import FakeMOService
from tests.conftest import FakeOmadaService


@dataclass
class TestUser:
    uuid: UUID
    first_name: str
    last_name: str
    cpr_number: str

    def get_omada_user(self, **kwargs: Any) -> OmadaUser:
        # Omada uses empty strings for absent values
        kwargs.setdefault("login", "")
        kwargs.setdefault("email", "")
        kwargs.setdefault("phone_direct", "")
        kwargs.setdefault("phone_cell", "")
        kwargs.setdefault("phone_institution", "")
        return OmadaUser.parse_obj(
            {
                "identity_category": IdentityCategory(
                    id=100,
                    uid="ac0c67fc-5f47-4112-94e6-446bfb68326a",
                ),
                **kwargs,
            }
        )

    def get_manual_omada_user(self, **kwargs: Any) -> ManualOmadaUser:
        omada_user = self.get_omada_user(**kwargs)
        return ManualOmadaUser.parse_obj(
            {
                **omada_user.dict(),
                "identity_category": IdentityCategory(
                    id=561,
                    uid="270a1807-95ca-40b4-9ce5-475d8961f31b",
                ),
                "first_name": self.first_name,
                "last_name": self.last_name,
                "cpr_number": self.cpr_number,
                **kwargs,
            }
        )

    def get_mo_employee(self, **kwargs: Any) -> Employee:
        return Employee.parse_obj(
            {
                "givenname": self.first_name,
                "surname": self.last_name,
                "cpr_no": self.cpr_number,
                **kwargs,
            }
        )

    def get_mo_engagement(self, **kwargs: Any) -> Engagement:
        return Engagement.parse_obj({"person": PersonRef(uuid=self.uuid), **kwargs})

    def get_mo_address(self, **kwargs: Any) -> Address:
        return Address.parse_obj({"person": PersonRef(uuid=self.uuid), **kwargs})


@pytest.fixture
def alice() -> TestUser:
    return TestUser(
        uuid=UUID("d4332525-5c1c-4a70-88fe-a87e38c5364c"),
        first_name="Alice",
        last_name="Walker",
        cpr_number="1807972118",
    )


# service_number = (todo,)
# ad_guid = (todo,)
# job_title = (todo,)
# org_unit = (todo,)


# @pytest.fixture
# def alice(
#     facets: dict[str, dict[str, UUID]],
#     it_systems: dict[str, UUID],
# ) -> tuple[Employee, EmployeeData]:
#     uuid = UUID("ec9fe65a-428d-4c70-a85f-36c2982baf2e")
#     employee_data = EmployeeData(
#         uuid=uuid,
#         engagements=[
#             Engagement(
#                 uuid=UUID("282e4b99-341f-44cf-9962-73885706944b"),
#                 user_key="alice engagement E",
#                 org_unit=OrgUnitRef(uuid=todo),
#                 person=PersonRef(uuid=uuid),
#                 job_function=JobFunction(uuid=todo),
#                 engagement_type=EngagementType(uuid=todo),
#                 primary=Primary(uuid=todo),
#                 validity=Validity(
#                     from_date=datetime(2017, 2, 3),
#                     to_date=None,
#                 ),
#             ),
#         ],
#         addresses=[
#             Address(
#                 uuid=UUID("145dcc57-fe44-4dfa-84cc-867c5817641d"),
#                 value="alice address a",
#                 address_type=AddressType(uuid=todo),
#                 person=PersonRef(uuid=uuid),
#                 visibility=Visibility(uuid=todo),
#                 validity=Validity(
#                     from_date=datetime(2017, 2, 3),
#                     to_date=None,
#                 ),
#             ),
#         ],
#         itusers=[
#             ITUser(
#                 uuid=UUID("76f6942f-e30c-4e3e-ae06-f7932fb3c6cd"),
#                 user_key="alice1",
#                 itsystem=ITSystemRef(uuid=UUID("d7559722-a20a-42cb-94a8-3afd8c5445ed")),
#                 person=PersonRef(uuid=uuid),
#                 validity=Validity(
#                     from_date=datetime(2017, 2, 3),
#                     to_date=None,
#                 ),
#             ),
#             ITUser(),
#         ],
#     )
#
#     return employee, employee_data


@pytest.fixture
def fake_syncer(
    mo_settings: MoSettings,
    fake_mo_service: FakeMOService,
    fake_omada_service: FakeOmadaService,
) -> FakeSyncer:
    return FakeSyncer(
        settings=mo_settings,
        mo_service=fake_mo_service,
        omada_service=fake_omada_service,
    )


async def test_ensure_employee_no_existing(
    fake_syncer: FakeSyncer, alice: TestUser, org_units: dict[str, UUID]
) -> None:
    omada_user = alice.get_manual_omada_user(
        service_number="alice123",
        ad_guid=UUID("d3ea59fd-6095-45b6-9d4c-3eb44c9e9f12"),
        job_title="cryptographer",
        org_unit=org_units["org_unit_a"],
        valid_from=datetime(2019, 5, 6),
    )
    fake_syncer.omada_service.api.users.append(omada_user)

    await fake_syncer.ensure_employee(
        omada_user=omada_user,
        employee=None,
    )

    uploads = fake_syncer.mo_service.model.upload.await_args.args[0]
    expected = dict(
        givenname=alice.first_name,
        surname=alice.last_name,
        cpr_no=alice.cpr_number,
    )
    assert one(uploads).dict().items() >= expected.items()


async def test_ensure_employee_existing(
    fake_syncer: FakeSyncer, alice: TestUser, org_units: dict[str, UUID]
) -> None:
    omada_user = alice.get_manual_omada_user(
        service_number="alice123",
        ad_guid=UUID("d3ea59fd-6095-45b6-9d4c-3eb44c9e9f12"),
        job_title="cryptographer",
        org_unit=org_units["org_unit_a"],
        valid_from=datetime(2019, 5, 6),
    )
    employee = alice.get_mo_employee()
    fake_syncer.omada_service.api.users.append(omada_user)
    fake_syncer.mo_service.employees.append(employee)

    await fake_syncer.ensure_employee(
        omada_user=omada_user,
        employee=employee,
    )

    fake_syncer.mo_service.model.upload.assert_not_awaited()


async def test_ensure_employee_existing_changed(
    fake_syncer: FakeSyncer, alice: TestUser, org_units: dict[str, UUID]
) -> None:
    new_name = "Bob"  # it's 2022, you got a problem?
    omada_user = alice.get_manual_omada_user(
        first_name=new_name,
        service_number="alice123",
        ad_guid=UUID("d3ea59fd-6095-45b6-9d4c-3eb44c9e9f12"),
        job_title="cryptographer",
        org_unit=org_units["org_unit_a"],
        valid_from=datetime(2019, 5, 6),
    )
    employee = alice.get_mo_employee()
    fake_syncer.omada_service.api.users.append(omada_user)
    fake_syncer.mo_service.employees.append(employee)

    await fake_syncer.ensure_employee(
        omada_user=omada_user,
        employee=employee,
    )

    uploads = fake_syncer.mo_service.model.upload.await_args.args[0]
    expected = dict(
        givenname=new_name,
        surname=alice.last_name,
        cpr_no=alice.cpr_number,
    )
    assert one(uploads).dict().items() >= expected.items()


@pytest.mark.xfail  # TODO: yolo
async def test_ensure_engagements(
    fake_syncer: FakeSyncer,
    alice: TestUser,
    address_types: dict[str, UUID],
    job_functions: dict[str, UUID],
    engagement_types: dict[str, UUID],
    primary_types: dict[str, UUID],
    visibilities: dict[str, UUID],
    org_units: dict[str, UUID],
    org_unit_it_systems: dict[str, UUID],
) -> None:
    omada_users = [
        alice.get_manual_omada_user(
            service_number="unchanged",
            ad_guid=UUID("4ca9d4f0-d6bf-42f7-a676-01ff99aee05f"),
            job_title="cryptographer",
            org_unit=org_unit_it_systems["org_unit_a"],
            valid_from=datetime(2019, 5, 6),
        ),
        alice.get_manual_omada_user(
            service_number="new",
            ad_guid=UUID("d9dc2d8c-845d-4575-92ea-7fd0d5b6c028"),
            job_title="",
            org_unit=org_unit_it_systems["org_unit_a"],
            valid_from=datetime(2022, 11, 12),
        ),
    ]
    engagements = [
        alice.get_mo_engagement(
            user_key="unchanged",
            org_unit=OrgUnitRef(uuid=org_units["org_unit_a"]),
            job_function=JobFunction(uuid=job_functions["cryptographer"]),
            engagement_type=EngagementType(
                uuid=engagement_types["omada_manually_created"]
            ),
            primary=Primary(uuid=primary_types["primary"]),
            validity=Validity(
                from_date=datetime(2019, 5, 6),
                to_date=None,
            ),
        ),
        alice.get_mo_engagement(
            user_key="old",
            org_unit=OrgUnitRef(uuid=org_units["org_unit_a"]),
            job_function=JobFunction(uuid=job_functions["cryptographer"]),
            engagement_type=EngagementType(
                uuid=engagement_types["omada_manually_created"]
            ),
            primary=Primary(uuid=primary_types["primary"]),
            validity=Validity(
                from_date=datetime(2009, 8, 9),
                to_date=None,
            ),
        ),
    ]

    employee_data = EmployeeData.construct(uuid=alice.uuid, engagements=engagements)

    await fake_syncer.ensure_engagements(
        omada_users=omada_users,
        employee_data=employee_data,
        job_functions=job_functions,
        job_function_default="not_applicable",
        engagement_type_uuid=engagement_types["omada_manually_created"],
        primary_type_uuid=primary_types["primary"],
    )

    terminated, created = fake_syncer.mo_service.model.upload.await_args_list

    expected_terminated = dict(
        user_key="old",
    )
    assert one(terminated.args[0]).dict().items() >= expected_terminated.items()

    expected_created = dict(
        user_key="new",
    )
    assert one(created.args[0]).dict().items() >= expected_created.items()


@pytest.mark.xfail  # TODO: yolo
async def test_ensure_addresses(
    fake_syncer: FakeSyncer,
    alice: TestUser,
    address_types: dict[str, UUID],
    visibilities: dict[str, UUID],
) -> None:
    omada_users = [
        alice.get_omada_user(
            service_number="alice1",
            ad_guid=UUID("4ca9d4f0-d6bf-42f7-a676-01ff99aee05f"),
            email="unchanged@example.com",
            phone_direct="new",
            valid_from=datetime(2019, 5, 6),
        ),
        alice.get_omada_user(
            service_number="alice2",
            ad_guid=UUID("9a100081-03e0-4e89-ae6f-b13001b35d06"),
            phone_direct="changed",
            valid_from=datetime(2011, 5, 6),
        ),
    ]
    addresses = [
        alice.get_mo_address(
            value="unchanged@example.com",
            address_type=AddressType(uuid=address_types["EmailEmployee"]),
            visibility=Visibility(uuid=visibilities["Intern"]),
            validity=Validity(
                from_date=datetime(2019, 5, 6),
                to_date=None,
            ),
        ),
        alice.get_mo_address(
            value="not changed yet",
            address_type=AddressType(uuid=address_types["PhoneEmployee"]),
            visibility=Visibility(uuid=visibilities["Intern"]),
            validity=Validity(
                from_date=datetime(2011, 5, 6),
                to_date=None,
            ),
        ),
        alice.get_mo_address(
            value="old - delete me!",
            address_type=AddressType(uuid=address_types["InstitutionPhoneEmployee"]),
            visibility=Visibility(uuid=visibilities["Intern"]),
            validity=Validity(
                from_date=datetime(1967, 12, 8),
                to_date=None,
            ),
        ),
    ]

    employee_data = EmployeeData.construct(uuid=alice.uuid, addresses=addresses)

    await fake_syncer.ensure_addresses(
        omada_users=omada_users,
        employee_data=employee_data,
        address_types=address_types,
        visibility_uuid=visibilities["Intern"],
    )

    terminated, created = fake_syncer.mo_service.model.upload.await_args_list

    expected_terminated = dict(
        user_key="old",
    )
    assert one(terminated.args[0]).dict().items() >= expected_terminated.items()

    expected_created = dict(
        user_key="new",
    )
    assert one(created.args[0]).dict().items() >= expected_created.items()


# async def test_lol(
#         fake_syncer: FakeSyncer,
#         alice: TestUser,
#         address_types: dict[str, UUID],
#         visibilities: dict[str, UUID],
#
# ) -> None:
#     employee_data = EmployeeData.parse_obj(
#         {
#             "uuid": "42ef556d-1b7e-4c99-a891-b61aeea44a37",
#             "engagements": [
#                 {
#                     "uuid": "6900d20a-c417-4b6e-88c1-51aa187c2d66",
#                     "user_key": "23695",
#                     "org_unit_uuid": "1432abba-1ed8-4800-9800-000001310002",
#                     "person": [{"uuid": "42ef556d-1b7e-4c99-a891-b61aeea44a37"}],
#                     "job_function": {"uuid": "68930b4f-67e7-10c8-077f-61f7a4b4ee88"},
#                     "engagement_type": {"uuid": "57f394f7-c204-64aa-5f9b-8cd4d373e626"},
#                     "primary": {"uuid": "3c57482c-66e1-3a6f-b03c-592997d789db"},
#                     "validity": {"from": "2021-08-01T00:00:00+02:00", "to": None},
#                 }
#             ],
#             "addresses": [
#                 {
#                     "uuid": "20ca3ca6-fe4e-43e1-b67a-95efe96e4438",
#                     "value": "AlberteHoy.Jensen@silkeborg.dk",
#                     "address_type": {"uuid": "db077886-9392-1caa-d41e-5415bf4efde7"},
#                     "person": [{"uuid": "42ef556d-1b7e-4c99-a891-b61aeea44a37"}],
#                     "visibility": {"uuid": "edb076dc-473f-f8c9-1e39-77a8205f2b00"},
#                     "validity": {"from": "2022-02-25T00:00:00+01:00", "to": None},
#                 }
#             ],
#             "itusers": [
#                 {
#                     "uuid": "47f3cb07-d915-4e4f-bbd2-23d86d5131c8",
#                     "user_key": "26790561-133a-4c16-8f38-79c25f6adb72",
#                     "itsystem_uuid": "1760947e-0496-1483-fba8-98af2b98ef4f",
#                     "person": [{"uuid": "42ef556d-1b7e-4c99-a891-b61aeea44a37"}],
#                     "validity": {"from": "2022-02-25T00:00:00+01:00", "to": None},
#                 }
#             ],
#         }
#     )
#     omada_users = []
#     await fake_syncer.ensure_addresses(
#         omada_users=omada_users,
#         employee_data=employee_data,
#         address_types=address_types,
#         visibility_uuid=visibilities["Intern"],
#     )
