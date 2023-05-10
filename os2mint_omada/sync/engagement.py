# SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

import asyncio
from contextlib import suppress
from uuid import UUID

import structlog
from more_itertools import only
from pydantic import parse_obj_as
from ramodels.mo import Validity
from ramodels.mo._shared import EngagementType
from ramodels.mo._shared import JobFunction
from ramodels.mo._shared import OrgUnitRef
from ramodels.mo._shared import PersonRef
from ramodels.mo._shared import Primary
from ramodels.mo.details import Engagement
from ramqp.utils import handle_exclusively
from ramqp.utils import sleep_on_error

from os2mint_omada.backing.omada.models import ManualOmadaUser
from os2mint_omada.backing.omada.models import OmadaUser
from os2mint_omada.sync.base import ComparableMixin
from os2mint_omada.sync.base import Syncer
from os2mint_omada.util import validity_intersection

logger = structlog.get_logger(__name__)


class ComparableEngagement(ComparableMixin, Engagement):
    @classmethod
    def from_omada(
        cls,
        omada_user: ManualOmadaUser,
        person_uuid: UUID,
        org_unit_uuid: UUID,
        org_unit_validity: Validity,
        job_functions: dict[str, UUID],
        engagement_type_uuid_for_visibility: dict[bool, UUID],
        primary_type_uuid: UUID,
    ) -> ComparableEngagement:
        """Construct (comparable) MO engagement from a manual omada user.

        Args:
            omada_user: Manual omada user.
            person_uuid: Employee of the engagement.
            org_unit_uuid: Org unit of the engagement.
            org_unit_validity: Validity of the org unit of the engagement. This is
             needed because the Omada user's validity sometimes lies outside the
             interval of the org unit, which is not accepted by MO.
            job_functions: Map of all engagement job functions in MO.
            engagement_type_uuid_for_visibility: Engagement type for visible/hidden
             engagements.
            primary_type_uuid: Primary class of the engagement.

        Returns: Comparable MO engagement.
        """
        try:
            job_function_uuid = job_functions[omada_user.job_title]
        except KeyError:
            # Fallback job function for engagements created for manual users if the
            # job title from Omada does not exist in MO.
            job_function_uuid = job_functions["not_applicable"]

        engagement_type_uuid = engagement_type_uuid_for_visibility[
            omada_user.is_visible
        ]

        return cls(  # type: ignore[call-arg]
            user_key=omada_user.service_number,
            person=PersonRef(uuid=person_uuid),
            org_unit=OrgUnitRef(uuid=org_unit_uuid),
            job_function=JobFunction(uuid=job_function_uuid),
            engagement_type=EngagementType(uuid=engagement_type_uuid),
            primary=Primary(uuid=primary_type_uuid),
            validity=validity_intersection(omada_user.validity, org_unit_validity),
        )


class EngagementSyncer(Syncer):
    @handle_exclusively(key=lambda self, employee_uuid: employee_uuid)
    @sleep_on_error()
    async def sync(self, employee_uuid: UUID) -> None:
        """Synchronise Omada engagements to MO.

        Args:
            employee_uuid: UUID of MO employee to synchronise.

        Returns: None.
        """
        logger.info("Synchronising manual engagements", employee_uuid=employee_uuid)

        # Get current user data from MO
        employee_states = await self.mo_service.get_employee_states(employee_uuid)
        assert employee_states
        cpr_number = only({e.cpr_no for e in employee_states})

        if cpr_number is None:
            logger.warning(
                "Cannot synchronise employee without CPR number",
                employee_uuid=employee_uuid,
            )
            return

        mo_engagements = await self.mo_service.get_employee_engagements(
            uuid=employee_uuid
        )

        # Get current user data from Omada
        raw_omada_users = await self.omada_service.api.get_users_by_cpr_number(
            cpr_number
        )
        omada_users = parse_obj_as(list[ManualOmadaUser | OmadaUser], raw_omada_users)
        manual_omada_users = [u for u in omada_users if isinstance(u, ManualOmadaUser)]

        # Get MO classes configuration
        job_functions = await self.mo_service.get_classes("engagement_job_function")

        # Primary class for engagements created for manual users
        primary_types = await self.mo_service.get_classes("primary_type")
        primary_type_uuid = primary_types["primary"]

        engagement_types = await self.mo_service.get_classes("engagement_type")
        # Maps from Omada visibility (boolean) to engagement type (class) user key in MO
        # for manual users. Only these engagements types are touched by the integration.
        omada_engagement_type_for_visibility = {
            True: engagement_types["omada_manually_created"],
            False: engagement_types["omada_manually_created_hidden"],
        }

        # Only process engagements we know Omada is authoritative for (created by us)
        # to avoid deleting those that have nothing to do with Omada.
        omada_engagements = [
            e
            for e in mo_engagements
            if e.engagement_type.uuid in omada_engagement_type_for_visibility.values()
        ]

        # Synchronise engagements to MO
        logger.info("Ensuring engagements", employee_uuid=employee_uuid)

        # Actual engagements in MO
        actual: dict[ComparableEngagement, Engagement] = {
            ComparableEngagement(**engagement.dict()): engagement
            for engagement in omada_engagements
        }

        # Expected engagements from Omada
        async def build_comparable_engagement(
            omada_user: ManualOmadaUser,
        ) -> ComparableEngagement:
            org_unit_uuid = await self._get_org_unit_uuid_for_user(omada_user)
            # The org unit's validity is needed to ensure the engagement's validity
            # does not lie outside this interval.
            org_unit_validity = await self.mo_service.get_org_unit_validity(
                org_unit_uuid
            )
            return ComparableEngagement.from_omada(
                omada_user=omada_user,
                person_uuid=employee_uuid,
                org_unit_uuid=org_unit_uuid,
                org_unit_validity=org_unit_validity,
                job_functions=job_functions,
                engagement_type_uuid_for_visibility=omada_engagement_type_for_visibility,
                primary_type_uuid=primary_type_uuid,
            )

        expected_tasks = (
            build_comparable_engagement(omada_user) for omada_user in manual_omada_users
        )
        expected_tuples = await asyncio.gather(*expected_tasks)
        expected: set[ComparableEngagement] = set(expected_tuples)

        # Delete excess existing
        excess_engagements = actual.keys() - expected
        if excess_engagements:
            excess_mo_engagements = [actual[e] for e in excess_engagements]
            logger.info(
                "Deleting excess engagements", engagements=excess_mo_engagements
            )
            delete = (self.mo_service.delete(e) for e in excess_mo_engagements)
            await asyncio.gather(*delete)

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

    async def _get_org_unit_uuid_for_user(self, omada_user: ManualOmadaUser) -> UUID:
        """Get the org unit UUID a manual Omada user's engagement should be created in.

        Args:
            omada_user: Manual Omada user.

        Returns: UUID of the org unit if found, otherwise raises KeyError.
        """
        # By default, engagements for manual Omada users are linked to the org unit
        # which has an IT system with user key equal to the 'org_unit' field on the
        # user.
        with suppress(KeyError):
            return await self.mo_service.get_org_unit_with_it_system_user_key(
                str(omada_user.org_unit)
            )

        # Unfortunately, some org units are imported into MO with the UUID from the
        # system we are integrating with, so as a fallback, we check for an org unit
        # with the UUID directly. The KeyError of this lookup isn't caught.
        return await self.mo_service.get_org_unit_with_uuid(omada_user.org_unit)
