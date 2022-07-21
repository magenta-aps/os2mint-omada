# SPDX-FileCopyrightText: 2022 Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

import asyncio
from uuid import UUID

import structlog
from pydantic import parse_obj_as
from ramodels.mo import Validity
from ramodels.mo._shared import EngagementType
from ramodels.mo._shared import JobFunction
from ramodels.mo._shared import OrgUnitRef
from ramodels.mo._shared import PersonRef
from ramodels.mo._shared import Primary
from ramodels.mo.details import Engagement

from os2mint_omada.backing.omada.models import ManualOmadaUser
from os2mint_omada.backing.omada.models import OmadaUser
from os2mint_omada.sync.base import ComparableMixin
from os2mint_omada.sync.base import Syncer

logger = structlog.get_logger(__name__)


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
        """Construct (comparable) MO engagement from a manual omada user.

        Args:
            omada_user: Manual omada user.
            person_uuid: Employee of the engagement.
            org_unit_uuid: Org unit of the engagement.
            job_functions: Map of all engagement job functions in MO.
            job_function_default: Fallback job function used if the one defined on the
             Omada user does not exist in MO.
            engagement_type_uuid: Engagement type of the engagement.
            primary_type_uuid: Primary class of the engagement.

        Returns: Comparable MO engagement.
        """
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


class EngagementSyncer(Syncer):
    async def sync(self, employee_uuid: UUID) -> None:
        """Synchronise Omada engagements to MO.

        Args:
            employee_uuid: UUID of MO employee to synchronise.

        Returns: None.
        """
        logger.info("Synchronising manual engagements", employee_uuid=employee_uuid)

        # Get current user data from MO
        mo_employee = await self.mo_service.get_employee(employee_uuid)
        assert mo_employee is not None
        if mo_employee.cpr_no is None:
            logger.warning(
                "Cannot to synchronise employee without CPR number",
                employee_uuid=employee_uuid,
            )
            return

        mo_engagements = await self.mo_service.get_employee_engagements(
            uuid=employee_uuid
        )

        # Get current user data from Omada
        raw_omada_users = await self.omada_service.api.get_users_by_cpr_numbers(
            cpr_numbers=[mo_employee.cpr_no]
        )
        omada_users = parse_obj_as(list[ManualOmadaUser | OmadaUser], raw_omada_users)
        manual_omada_users = [u for u in omada_users if isinstance(u, ManualOmadaUser)]

        # Get MO classes configuration
        job_functions = await self.mo_service.get_classes("engagement_job_function")
        engagement_types = await self.mo_service.get_classes("engagement_type")
        manual_engagement_type_uuid = engagement_types[
            self.settings.manual_engagement_type
        ]
        primary_types = await self.mo_service.get_classes("primary_type")
        primary_type_uuid = primary_types[self.settings.manual_primary_class]

        # Only process engagements we know Omada is authoritative for (created by us)
        # to avoid deleting those that have nothing to do with Omada.
        omada_engagements = [
            e
            for e in mo_engagements
            if e.engagement_type.uuid == manual_engagement_type_uuid
        ]

        # Synchronise engagements to MO
        await self.ensure_engagements(
            omada_users=manual_omada_users,
            employee_uuid=employee_uuid,
            engagements=omada_engagements,
            job_functions=job_functions,
            job_function_default=self.settings.manual_job_function_default,
            engagement_type_uuid=manual_engagement_type_uuid,
            primary_type_uuid=primary_type_uuid,
        )

    async def ensure_engagements(
        self,
        omada_users: list[ManualOmadaUser],
        employee_uuid: UUID,
        engagements: list[Engagement],
        job_functions: dict[str, UUID],
        job_function_default: str,
        engagement_type_uuid: UUID,
        primary_type_uuid: UUID,
    ) -> None:
        """Ensure that the MO engagements are synchronised with the Omada users.

        Synchronisation is done on ALL Omada user entries for the employee, since total
        knowledge of all of a user's Omada entries is needed to avoid potentially
        terminating engagements related to a different Omada user entry.

        Args:
            omada_users: List of Omada users to synchronise.
            employee_uuid: MO employee UUID.
            engagements: Existing MO engagements.
            job_functions: Map of all engagement job functions in MO.
            job_function_default: Fallback job function used if the one defined on a
             Omada user does not exist in MO.
            engagement_type_uuid: Engagement type of the engagements.
            primary_type_uuid: Primary class of the engagements.

        Returns: None.
        """
        logger.debug("Ensuring engagements", employee_uuid=employee_uuid)

        # Actual engagements in MO
        actual: dict[ComparableEngagement, Engagement] = {
            ComparableEngagement(**engagement.dict()): engagement
            for engagement in engagements
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
                person_uuid=employee_uuid,
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
            terminate = (self.mo_service.terminate(e) for e in excess_mo_engagements)
            await asyncio.gather(*terminate)

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
