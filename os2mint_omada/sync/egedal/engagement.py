# SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

import asyncio
from collections import defaultdict
from uuid import UUID

import structlog
from fastramqpi.ramqp.depends import handle_exclusively_decorator
from more_itertools import only
from pydantic import parse_obj_as
from ramodels.mo._shared import EngagementType
from ramodels.mo._shared import JobFunction
from ramodels.mo._shared import OrgUnitRef
from ramodels.mo._shared import PersonRef
from ramodels.mo._shared import Primary
from ramodels.mo.details import Engagement

from os2mint_omada.mo import MO
from os2mint_omada.omada.api import OmadaAPI
from os2mint_omada.sync.models import ComparableMixin
from os2mint_omada.util import validity_intersection

from ...autogenerated_graphql_client import EngagementCreateInput
from ...autogenerated_graphql_client import RAValidityInput
from .models import EgedalOmadaEmployment
from .models import EgedalOmadaUser
from .models import ManualEgedalOmadaUser

logger = structlog.stdlib.get_logger()


class ComparableEngagement(ComparableMixin, Engagement):
    pass


@handle_exclusively_decorator(key=lambda employee_uuid, *_, **__: employee_uuid)
async def sync_engagements(
    employee_uuid: UUID,
    mo: MO,
    omada_api: OmadaAPI,
) -> None:
    logger.info("Synchronising engagements", employee_uuid=employee_uuid)

    # Get current user data from MO
    employee_states = await mo.get_employee_states(employee_uuid)
    assert employee_states
    cpr_number = only({e.cpr_no for e in employee_states})

    if cpr_number is None:
        logger.warning(
            "Cannot synchronise employee without CPR number",
            employee_uuid=employee_uuid,
        )
        return

    mo_engagements = await mo.get_employee_engagements(uuid=employee_uuid)

    # Get current user data from Omada
    raw_omada_users = await omada_api.get_users_by("C_EMPLOYEEID", [cpr_number])
    omada_users = parse_obj_as(
        list[ManualEgedalOmadaUser | EgedalOmadaUser], raw_omada_users
    )
    manual_omada_users = [
        u for u in omada_users if isinstance(u, ManualEgedalOmadaUser) and u.is_manual
    ]

    # Get MO classes configuration
    job_functions = await mo.get_classes("engagement_job_function")

    # Primary class for engagements created for omada users
    primary_types = await mo.get_classes("primary_type")
    primary_type_uuid = primary_types["primary"]

    # Engagement type for engagements created for omada users
    engagement_types = await mo.get_classes("engagement_type")
    engagement_type_uuid = engagement_types["omada_manually_created"]

    # Only process engagements we know Omada is authoritative for (created by us)
    # to avoid deleting those that have nothing to do with Omada.
    mo_omada_engagements = [
        e for e in mo_engagements if e.engagement_type.uuid == engagement_type_uuid
    ]

    # Existing engagements in MO
    existing: defaultdict[ComparableEngagement, set[Engagement]] = defaultdict(set)
    for mo_engagement in mo_omada_engagements:
        comparable_engagement = ComparableEngagement(**mo_engagement.dict())
        existing[comparable_engagement].add(mo_engagement)

    # Desired engagements from Omada
    async def build_comparable_engagement(
        omada_user: ManualEgedalOmadaUser,
        omada_employment: EgedalOmadaEmployment,
    ) -> ComparableEngagement:
        # Engagements for Omada users are linked to the org unit through the org unit's
        # user_key.
        org_unit_uuid = await mo.get_org_unit_with_user_key(omada_employment.org_unit)

        # The org unit's validity is needed to ensure the engagement's validity
        # does not lie outside this interval.
        org_unit_validity = await mo.get_org_unit_validity(org_unit_uuid)
        try:
            job_function_uuid = job_functions[omada_employment.job_title]
        except KeyError:
            # Fallback job function for engagements if the job title from Omada does
            # not exist in MO.
            job_function_uuid = job_functions["not_applicable"]
        return ComparableEngagement(  # type: ignore[call-arg]
            user_key=omada_employment.employment_number,
            person=PersonRef(uuid=employee_uuid),
            org_unit=OrgUnitRef(uuid=org_unit_uuid),
            job_function=JobFunction(uuid=job_function_uuid),
            engagement_type=EngagementType(uuid=engagement_type_uuid),
            primary=Primary(uuid=primary_type_uuid),
            validity=validity_intersection(omada_user.validity, org_unit_validity),
        )

    desired_tuples = await asyncio.gather(
        *(
            build_comparable_engagement(omada_user, omada_employment)
            for omada_user in manual_omada_users
            for omada_employment in omada_user.employments
        )
    )
    desired: set[ComparableEngagement] = set(desired_tuples)

    # Delete excess existing
    excess: set[Engagement] = set()
    for comparable_engagement, engagements in existing.items():
        first, *duplicate = engagements
        excess.update(duplicate)
        if comparable_engagement not in desired:
            excess.add(first)
    if excess:
        logger.info("Deleting excess engagements", engagements=excess)
        await asyncio.gather(*(mo.delete_engagement(a) for a in excess))

    # Create missing desired
    missing_comparable = desired - existing.keys()
    missing_mo = [Engagement(**engagement.dict()) for engagement in missing_comparable]
    if missing_mo:
        logger.info("Creating missing engagements", engagements=missing_mo)
        for missing in missing_mo:
            assert missing.person is not None
            assert missing.org_unit is not None
            assert missing.job_function is not None
            assert missing.engagement_type is not None
            assert missing.primary is not None
            await mo.graphql_client.create_engagement(
                EngagementCreateInput(
                    user_key=missing.user_key,
                    person=missing.person.uuid,
                    org_unit=missing.org_unit.uuid,
                    job_function=missing.job_function.uuid,
                    engagement_type=missing.engagement_type.uuid,
                    primary=missing.primary.uuid,
                    validity=RAValidityInput(
                        from_=missing.validity.from_date,
                        to=missing.validity.to_date,
                    ),
                )
            )
