# SPDX-FileCopyrightText: 2022 Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from pathlib import Path
from typing import Collection
from typing import Iterable
from unittest.mock import AsyncMock
from uuid import UUID

import pytest
from pytest import Item
from ramodels.mo import Employee
from ramqp import AMQPSystem
from ramqp.mo import MOAMQPSystem

from os2mint_omada.backing.mo.models import EmployeeData
from os2mint_omada.backing.mo.service import ITSystems
from os2mint_omada.backing.mo.service import MOService
from os2mint_omada.backing.omada.api import OmadaAPI
from os2mint_omada.backing.omada.models import OmadaUser
from os2mint_omada.backing.omada.models import RawOmadaUser
from os2mint_omada.backing.omada.service import OmadaService
from os2mint_omada.config import MoSettings
from os2mint_omada.config import OmadaSettings
from os2mint_omada.config import Settings

pytestmark = pytest.mark.respx(assert_all_called=True)


def pytest_collection_modifyitems(items: list[Item]) -> None:
    """Always assert all respx mocks are called on all tests."""
    for item in items:
        item.add_marker(pytest.mark.respx(assert_all_called=True))


@pytest.fixture
def mo_settings() -> MoSettings:
    """Fixed settings so tests work without specific environment variables."""
    return MoSettings(
        client_secret="hunter2",
    )


@pytest.fixture
def omada_settings(tmp_path: Path) -> OmadaSettings:
    """Fixed settings so tests work without specific environment variables."""
    return OmadaSettings(
        url="http://omada.example.com/odata.json",
        persistence_file=tmp_path.joinpath("omada.json"),
    )


@pytest.fixture
def settings(mo_settings: MoSettings, omada_settings: OmadaSettings) -> Settings:
    """Fixed settings so tests work without specific environment variables."""
    return Settings(
        mo=mo_settings,
        omada=omada_settings,
    )


@pytest.fixture
def address_types() -> dict[str, UUID]:
    """Hard-coded dict of address type user_key/uuids."""
    return {
        "EmailEmployee": UUID("3b07bd80-ddee-4806-95b4-0252cc2e5ab1"),
        "PhoneEmployee": UUID("782a2f6e-e826-44ae-970c-151590fc49b7"),
        "MobilePhoneEmployee": UUID("d60c9e42-d4c8-4730-9404-da54fbe296a3"),
        "InstitutionPhoneEmployee": UUID("722b2527-79f6-411f-97f8-1c9b8c581061"),
    }


@pytest.fixture
def job_functions() -> dict[str, UUID]:
    """Hard-coded dict of job function user_key/uuids."""
    return {
        "not_applicable": UUID("64474390-a378-4d47-8f7a-9ddb82819d36"),
        "cryptographer": UUID("ad5b482d-a649-486d-930d-50406214edcc"),
    }


@pytest.fixture
def engagement_types() -> dict[str, UUID]:
    """Hard-coded dict of engagement types user_key/uuids."""
    return {
        "manually_created": UUID("3d76ae3e-5a74-46b9-9e51-508903d17606"),
    }


@pytest.fixture
def primary_types() -> dict[str, UUID]:
    """Hard-coded dict of primary type user_key/uuids"""
    return {
        "primary": UUID("fde517e6-0355-4456-bafc-0030b586c0e0"),
    }


@pytest.fixture
def visibilities() -> dict[str, UUID]:
    """Hard-coded dict of visibility type user_key/uuids."""
    return {
        "Intern": UUID("70beca48-6520-4af9-9bf8-a8a70880e6d2"),
    }


# @pytest.fixture
# def facets(
#     address_types: dict[str, UUID],
#     job_functions: dict[str, UUID],
#     engagement_types: dict[str, UUID],
#     primary_types: dict[str, UUID],
#     visibilities: dict[str, UUID],
# ) -> dict[str, dict[str, UUID]]:
#     return {
#         "employee_address_type": address_types,
#         "engagement_job_function": job_functions,
#         "engagement_type": engagement_types,
#         "primary_type": primary_types,
#         "visibility": visibilities,
#     }


# @pytest.fixture
# def it_systems() -> dict[str, UUID]:
#     return {
#         "omada_ad_guid": UUID("b2a1d7e7-ca14-4617-92e3-5910492b70db"),
#         "omada_login": UUID("a6ad5c2c-e109-44ed-a149-b870ca18bfb9"),
#     }


@pytest.fixture
def org_units() -> dict[str, UUID]:
    """Hard-coded dict of organisational unit user_key/uuids."""
    return {
        "org_unit_a": UUID("b3110a35-ade9-40a4-93d1-09517e8f3ee4"),
        "org_unit_b": UUID("4b57fc2e-d757-406d-ac61-129871f33447"),
    }


@pytest.fixture
def org_unit_it_systems(org_units: dict[str, UUID]) -> dict[str, UUID]:
    """Hard-coded dict of org unit user_key / it system user_key.

    Engagements for manual Omada users are created in the organisational unit which has
    an IT system with user_key equal to the org_unit/C_ORGANISATIONSKODE field on the
    Omada user.
    """
    return {
        "org_unit_a": org_units["org_unit_a"],
    }


@pytest.fixture
def raw_omada_user() -> dict:
    """Raw normal Omada user, as returned by the API."""
    return {
        "IDENTITYCATEGORY": {
            "Id": 560,
            "UId": "ac0c67fc-5f47-4112-94e6-446bfb68326a",
        },
        "C_TJENESTENR": "DRV2639",
        "C_OBJECTGUID_I_AD": "9e5aee86-1461-4072-9883-ed43c82db42c",
        "C_LOGIN": "DR00777",
        "EMAIL": "bob@example.com",
        "EMAIL2": "",
        "C_DIREKTE_TLF": "12341234",
        "CELLPHONE": "",
        "C_INST_PHONE": "",
        "VALIDFROM": "2016-06-15T00:00:00+02:00",
        "VALIDTO": "2022-12-03T00:00:00+01:00",
    }


@pytest.fixture
def raw_omada_user_manual(raw_omada_user: dict) -> dict:
    """Raw manual Omada user, as returned by the API."""
    manual_fields = {
        "IDENTITYCATEGORY": {
            "Id": 561,
            "UId": "270a1807-95ca-40b4-9ce5-475d8961f31b",
        },
        "C_FORNAVNE": "Anders W.",
        "LASTNAME": "Lemming",
        "C_CPRNR": "1707821597",
        "JOBTITLE": "Worker",
        "C_ORGANISATIONSKODE": "5a23d722-1be4-4f00-a200-000001500001",
    }
    return raw_omada_user | manual_fields


class FakeMOService(MOService):
    """Fake MOService with all external dependencies mocked."""

    def __init__(
        self,
        settings: MoSettings,
        amqp_system: MOAMQPSystem,
        org_unit_it_systems: dict[str, UUID],
    ) -> None:
        super().__init__(settings, amqp_system)
        self.employees: list[Employee] = []
        self.org_unit_it_systems = org_unit_it_systems
        self.model = AsyncMock()

    async def get_it_systems(self) -> ITSystems:
        raise NotImplementedError
        # return ITSystems(it_systems)

    async def get_classes(self, facet_user_key: str) -> dict[str, UUID]:
        raise NotImplementedError
        # return facets[facet_user_key]

    async def get_employee_uuid_from_service_number(
        self, service_number: str
    ) -> UUID | None:
        # TODO
        raise NotImplementedError
        # for employee in EMPLOYEES:
        #     for engagement in employee.todo:
        #         pass
        # return None

    async def get_employee_uuid_from_cpr(self, cpr: str) -> UUID | None:
        # TODO
        raise NotImplementedError
        # for employee in EMPLOYEES:
        #     if employee.cpr_no == cpr:
        #         return employee.uuid
        # return None

    async def get_employee(self, uuid: UUID) -> Employee | None:
        # TODO
        raise NotImplementedError
        # for employee in EMPLOYEES:
        #     if employee.uuid == uuid:
        #         return employee
        # return None

    async def get_employee_data(
        self,
        uuid: UUID,
        address_types: Iterable[UUID],
        it_systems: Collection[UUID],
    ) -> EmployeeData | None:
        raise NotImplementedError  # TODO

    async def get_org_unit_with_it_system_user_key(self, user_key: str) -> UUID | None:
        for it_system_uuid in self.org_unit_it_systems.values():
            if str(it_system_uuid) == user_key:
                return it_system_uuid
        return None


@pytest.fixture
def fake_mo_service(
    mo_settings: MoSettings, org_unit_it_systems: dict[str, UUID]
) -> FakeMOService:
    """Fake MOService, returning values from the defined fixtures."""
    return FakeMOService(
        settings=mo_settings,
        amqp_system=AsyncMock(),
        org_unit_it_systems=org_unit_it_systems,
    )


class FakeOmadaAPI(OmadaAPI):
    """Fake OmadaAPI with all external services mocked."""

    def __init__(self, settings: OmadaSettings) -> None:
        super().__init__(settings)
        self.users: list[OmadaUser] = []

    async def get_users(self, params: dict | None = None) -> list[RawOmadaUser]:
        return [RawOmadaUser(u.dict()) for u in self.users]

    async def get_users_by_service_numbers(
        self, service_numbers: Iterable[str]
    ) -> list[RawOmadaUser]:
        return [
            u
            for u in await self.get_users()
            if u.get("service_number") in service_numbers
        ]

    async def get_users_by_cpr_numbers(
        self, cpr_numbers: Iterable[str]
    ) -> list[RawOmadaUser]:
        return [u for u in await self.get_users() if u.get("cpr_number") in cpr_numbers]


class FakeOmadaService(OmadaService):
    """Fake OmadaService, using the fake API."""

    def __init__(self, settings: OmadaSettings, amqp_system: AMQPSystem) -> None:
        super().__init__(settings, amqp_system)
        self.api: FakeOmadaAPI = FakeOmadaAPI(settings=settings)


@pytest.fixture
def fake_omada_service(omada_settings: OmadaSettings) -> FakeOmadaService:
    """Fake OmadaService, returning values from the defined fixtures."""
    service = FakeOmadaService(settings=omada_settings, amqp_system=AsyncMock())
    return service
