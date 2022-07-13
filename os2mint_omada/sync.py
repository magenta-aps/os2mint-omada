# SPDX-FileCopyrightText: 2022 Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

import asyncio
from typing import Any
from typing import cast
from uuid import UUID

import structlog
from pydantic import BaseModel
from pydantic import parse_obj_as
from pydantic import validator
from ramodels.mo import Employee
from ramodels.mo import Validity
from ramodels.mo._shared import AddressType
from ramodels.mo._shared import EngagementType
from ramodels.mo._shared import ITSystemRef
from ramodels.mo._shared import JobFunction
from ramodels.mo._shared import OrgUnitRef
from ramodels.mo._shared import PersonRef
from ramodels.mo._shared import Primary
from ramodels.mo._shared import Visibility
from ramodels.mo.details import Address
from ramodels.mo.details import Engagement
from ramodels.mo.details import ITUser

from os2mint_omada.backing.mo.models import MOEmployee
from os2mint_omada.backing.mo.service import ITSystems
from os2mint_omada.backing.mo.service import MOService
from os2mint_omada.backing.omada.models import ManualOmadaUser
from os2mint_omada.backing.omada.models import OmadaUser
from os2mint_omada.backing.omada.service import OmadaService
from os2mint_omada.config import MoSettings
from os2mint_omada.util import as_terminated
from os2mint_omada.util import at_midnight

logger = structlog.get_logger(__name__)


class ComparableMixin(BaseModel):
    @validator("uuid", check_fields=False)
    def strip_uuid(cls, uuid: UUID) -> None:
        return None

    @validator("validity", check_fields=False)
    def validity_at_midnight(cls, validity: Validity) -> Validity:
        return Validity(
            from_date=at_midnight(validity.from_date),
            to_date=at_midnight(validity.to_date),
        )


class StripUserKeyMixin(BaseModel):
    @validator("user_key", check_fields=False)
    def strip_user_key(cls, user_key: Any | None) -> None:
        return None


class ComparableEmployee(StripUserKeyMixin, ComparableMixin, Employee):
    @classmethod
    def from_omada(cls, omada_user: ManualOmadaUser) -> ComparableEmployee:
        return cls(
            givenname=omada_user.first_name,
            surname=omada_user.last_name,
            cpr_no=omada_user.cpr_number,
        )


class ComparableEngagement(ComparableMixin, Engagement):
    @classmethod
    def from_omada(
        cls,
        omada_user: ManualOmadaUser,
        person_uuid: UUID,
        org_unit_uuid: UUID,
        job_functions: dict[str, UUID],
        job_function_default: str,
        engagement_type_uuid: UUID,
        primary_type_uuid: UUID,
    ) -> ComparableEngagement:
        try:
            job_function_uuid = job_functions[omada_user.job_title]
        except KeyError:
            job_function_uuid = job_functions[job_function_default]
        return cls(
            user_key=omada_user.service_number,
            person=PersonRef(uuid=person_uuid),
            org_unit=OrgUnitRef(uuid=org_unit_uuid),
            job_function=JobFunction(uuid=job_function_uuid),
            engagement_type=EngagementType(uuid=engagement_type_uuid),
            primary=Primary(uuid=primary_type_uuid),
            validity=Validity(
                from_date=omada_user.valid_from,
                to_date=omada_user.valid_to,
            ),
        )


class ComparableAddress(StripUserKeyMixin, ComparableMixin, Address):
    @classmethod
    def from_omada(
        cls,
        omada_user: OmadaUser,
        omada_attr: str,
        mo_employee: MOEmployee,
        address_type_uuid: UUID,
        visibility_uuid: UUID,
    ) -> ComparableAddress | None:
        # Omada often returns empty strings for non-existent attributes, which is
        # falsy - and therefore also ignored, like None values.
        omada_value = getattr(omada_user, omada_attr)
        if not omada_value:
            return None
        return cls(
            value=omada_value,
            address_type=AddressType(uuid=address_type_uuid),
            person=PersonRef(uuid=mo_employee.uuid),
            visibility=Visibility(uuid=visibility_uuid),
            validity=Validity(
                from_date=omada_user.valid_from,
                to_date=omada_user.valid_to,
            ),
        )


class ComparableITUser(ComparableMixin, ITUser):
    @classmethod
    def from_omada(
        cls,
        omada_user: OmadaUser,
        omada_attr: str,
        it_system_uuid: UUID,
        mo_employee: MOEmployee,
    ) -> ComparableITUser:
        return cls(
            user_key=str(getattr(omada_user, omada_attr)),
            itsystem=ITSystemRef(uuid=it_system_uuid),
            person=PersonRef(uuid=mo_employee.uuid),
            validity=Validity(
                from_date=omada_user.valid_from,
                to_date=omada_user.valid_to,
            ),
        )


class Syncer:
    def __init__(
        self, settings: MoSettings, mo_service: MOService, omada_service: OmadaService
    ) -> None:
        self.settings = settings
        self.mo_service = mo_service
        self.omada_service = omada_service

    async def sync_manual_employee(self, omada_user: ManualOmadaUser) -> None:
        logger.info("Synchronising manual employee", omada_user=omada_user)
        # Setup MO prerequisites
        address_types = await self.mo_service.get_classes("employee_address_type")
        it_systems = await self.mo_service.get_it_systems()
        job_functions = await self.mo_service.get_classes("engagement_job_function")
        engagement_types = await self.mo_service.get_classes("engagement_type")
        engagement_type_uuid = engagement_types[self.settings.manual_engagement_type]
        primary_types = await self.mo_service.get_classes("primary_type")
        primary_type_uuid = primary_types[self.settings.manual_primary_class]

        # Get current user data from MO
        employee_uuid = await self.mo_service.get_employee_uuid_from_cpr(
            cpr=omada_user.cpr_number
        )
        employee: Employee | None = None
        if employee_uuid is not None:
            employee = await self.mo_service.get_employee(uuid=employee_uuid)

        # Get current user data from Omada
        omada_users_raw = await self.omada_service.api.get_users_by_cpr_numbers(
            cpr_numbers=[omada_user.cpr_number]
        )
        omada_users = parse_obj_as(list[ManualOmadaUser], omada_users_raw)

        # Synchronise to MO
        employee = await self.ensure_employee(omada_user=omada_user, employee=employee)
        mo_employee = await self.mo_service.get_employee_data(
            uuid=employee.uuid,  # uuid from the (possibly) newly-created employee
            address_types=address_types.values(),
            it_systems=it_systems.values(),
        )
        assert mo_employee is not None
        await self.ensure_engagements(
            omada_users=omada_users,
            mo_employee=mo_employee,
            job_functions=job_functions,
            job_function_default=self.settings.manual_job_function_default,
            engagement_type_uuid=engagement_type_uuid,
            primary_type_uuid=primary_type_uuid,
        )

    async def ensure_employee(
        self, omada_user: ManualOmadaUser, employee: Employee | None
    ) -> Employee:
        logger.info("Ensuring employee", omada_user=omada_user, employee=employee)
        # Actual employee in MO
        if employee is not None:
            actual = ComparableEmployee(**employee.dict())
            uuid = employee.uuid
        else:
            actual = None
            uuid = None

        # Expected employee from Omada
        expected = ComparableEmployee.from_omada(omada_user)

        # Update if outdated
        if actual != expected:
            updated_employee = Employee(uuid=uuid, **expected.dict(exclude={"uuid"}))
            logger.info("Uploading employee", employee=updated_employee)
            await self.mo_service.model.upload([updated_employee])
            return updated_employee
        assert employee is not None
        return employee

    async def ensure_engagements(
        self,
        omada_users: list[ManualOmadaUser],
        mo_employee: MOEmployee,
        job_functions: dict[str, UUID],
        job_function_default: str,
        engagement_type_uuid: UUID,
        primary_type_uuid: UUID,
    ) -> None:
        logger.info("Ensuring engagement")

        # Actual engagements in MO
        actual: dict[ComparableEngagement, Engagement] = {
            ComparableEngagement(**engagement.dict()): engagement
            for engagement in mo_employee.engagements
        }

        # Expected engagements from Omada
        async def build_comparable_engagement(
            omada_user: ManualOmadaUser,
        ) -> ComparableEngagement:
            # Engagements are linked to org units through an IT system on the unit
            # containing the UUID of the C_ORGANISATIONSKODE from Omada.
            try:
                org_unit_uuid = (
                    await self.mo_service.get_org_unit_with_it_system_user_key(
                        str(omada_user.org_unit)
                    )
                )
            except KeyError:
                # Ugly fallback in case the org unit IT system does not exist
                org_unit_uuid = await self.mo_service.get_org_unit_with_uuid(
                    omada_user.org_unit
                )

            return ComparableEngagement.from_omada(
                omada_user=omada_user,
                person_uuid=mo_employee.uuid,
                org_unit_uuid=org_unit_uuid,
                job_functions=job_functions,
                job_function_default=job_function_default,
                engagement_type_uuid=engagement_type_uuid,
                primary_type_uuid=primary_type_uuid,
            )

        expected_tasks = (
            build_comparable_engagement(omada_user) for omada_user in omada_users
        )
        expected_tuples = await asyncio.gather(*expected_tasks)
        expected: set[ComparableEngagement] = set(expected_tuples)

        # Terminate excess existing
        excess_engagements = actual.keys() - expected
        if excess_engagements:
            excess_mo_engagements = [actual[e] for e in excess_engagements]
            logger.info(
                "Terminating excess engagements", engagements=excess_mo_engagements
            )
            terminated_mo_engagements = (
                as_terminated(e) for e in excess_mo_engagements
            )
            await self.mo_service.model.upload(terminated_mo_engagements)

        # Create missing
        missing_engagements = expected - actual.keys()
        if missing_engagements:
            missing_mo_engagements = [
                Engagement(**engagement.dict()) for engagement in missing_engagements
            ]
            logger.info(
                "Creating missing engagements", engagements=missing_mo_engagements
            )
            await self.mo_service.model.upload(missing_mo_engagements)

    async def sync_employee_data(self, uuid: UUID) -> None:
        logger.info("Synchronising user", uuid=uuid)
        # Get current user data from MO
        address_types = await self.mo_service.get_classes("employee_address_type")
        visibility_classes = await self.mo_service.get_classes("visibility")
        visibility_uuid = visibility_classes[self.settings.address_visibility]
        it_systems = await self.mo_service.get_it_systems()
        mo_employee = await self.mo_service.get_employee_data(
            uuid=uuid,
            address_types=address_types.values(),
            it_systems=it_systems.values(),
        )
        if mo_employee is None:
            logger.info("No employee in MO: skipping", uuid=uuid)
            return

        # Get current user data from Omada. Note that we are fetching Omada users for
        # ALL engagements to avoid deleting too many addresses and IT systems.
        service_numbers = (e.user_key for e in mo_employee.engagements)
        omada_users_raw = await self.omada_service.api.get_users_by_service_numbers(
            service_numbers
        )
        omada_users = parse_obj_as(list[OmadaUser], omada_users_raw)

        # Synchronise to MO
        await self.ensure_addresses(
            omada_users=omada_users,
            mo_employee=mo_employee,
            address_types=address_types,
            visibility_uuid=visibility_uuid,
        )
        await self.ensure_it_users(
            omada_users=omada_users,
            mo_employee=mo_employee,
            it_systems=it_systems,
        )

    async def ensure_addresses(
        self,
        omada_users: list[OmadaUser],
        mo_employee: MOEmployee,
        address_types: dict[str, UUID],
        visibility_uuid: UUID,
    ) -> None:
        logger.info("Ensuring addresses", employee_uuid=mo_employee.uuid)
        # Actual addresses in MO
        actual: dict[ComparableAddress, Address] = {
            ComparableAddress(**address.dict()): address
            for address in mo_employee.addresses
        }

        # Expected addresses from Omada
        expected_with_none: set[ComparableAddress | None] = {
            ComparableAddress.from_omada(
                omada_user=omada_user,
                omada_attr=omada_attr,
                mo_employee=mo_employee,
                address_type_uuid=address_types[mo_address_user_key],
                visibility_uuid=visibility_uuid,
            )
            for omada_user in omada_users
            for omada_attr, mo_address_user_key in self.settings.address_map.items()
        }
        expected: set[ComparableAddress] = cast(
            set[ComparableAddress], expected_with_none - {None}
        )

        # Terminate excess existing
        excess_addresses = actual.keys() - expected
        if excess_addresses:
            excess_mo_addresses = [actual[a] for a in excess_addresses]  # with UUID
            logger.info("Terminating excess addresses", addresses=excess_mo_addresses)
            terminated_mo_addresses = (as_terminated(a) for a in excess_mo_addresses)
            await self.mo_service.model.upload(terminated_mo_addresses)

        # Create missing
        missing_addresses = expected - actual.keys()
        if missing_addresses:
            missing_mo_addresses = [
                Address(**address.dict()) for address in missing_addresses  # with UUID
            ]
            logger.info("Creating missing addresses", addresses=missing_mo_addresses)
            await self.mo_service.model.upload(missing_mo_addresses)

    async def ensure_it_users(
        self,
        omada_users: list[OmadaUser],
        mo_employee: MOEmployee,
        it_systems: ITSystems,
    ) -> None:
        logger.info("Ensuring IT users", employee_uuid=mo_employee.uuid)
        # Actual IT users in MO
        actual: dict[ComparableITUser, ITUser] = {
            ComparableITUser(**it_user.dict()): it_user
            for it_user in mo_employee.itusers
        }

        # Expected IT users from Omada
        expected: set[ComparableITUser] = {
            ComparableITUser.from_omada(
                omada_user=omada_user,
                omada_attr=omada_attr,
                it_system_uuid=it_systems[mo_it_system_user_key],
                mo_employee=mo_employee,
            )
            for omada_user in omada_users
            for omada_attr, mo_it_system_user_key in self.settings.it_user_map.items()
        }

        # Terminate excess existing
        excess_it_users = actual.keys() - expected
        if excess_it_users:
            excess_mo_users = [actual[u] for u in excess_it_users]  # with UUID
            logger.info("Terminating excess IT users", users=excess_mo_users)
            terminated_mo_it_users = (as_terminated(u) for u in excess_mo_users)
            await self.mo_service.model.upload(terminated_mo_it_users)

        # Create missing
        missing_it_users = expected - actual.keys()
        if missing_it_users:
            missing_mo_it_users = [
                ITUser(**it_user.dict()) for it_user in missing_it_users
            ]
            logger.info("Creating missing IT users", users=missing_mo_it_users)
            await self.mo_service.model.upload(missing_mo_it_users)
