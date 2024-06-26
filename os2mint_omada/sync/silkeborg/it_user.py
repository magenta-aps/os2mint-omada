# SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import cast
from uuid import UUID

import structlog
from fastramqpi.raclients.modelclient.mo import ModelClient
from fastramqpi.ramqp.depends import handle_exclusively_decorator
from pydantic import parse_obj_as
from ramodels.mo._shared import EngagementRef
from ramodels.mo._shared import ITSystemRef
from ramodels.mo._shared import PersonRef
from ramodels.mo.details import ITUser

from .models import SilkeborgOmadaUser
from os2mint_omada.mo import MO
from os2mint_omada.omada.api import OmadaAPI
from os2mint_omada.sync.models import ComparableMixin

logger = structlog.get_logger(__name__)


class ComparableITUser(ComparableMixin, ITUser):
    @classmethod
    def from_omada(
        cls,
        omada_user: SilkeborgOmadaUser,
        omada_attr: str,
        employee_uuid: UUID,
        engagement_uuid: UUID,
        it_system_uuid: UUID,
    ) -> ComparableITUser | None:
        """Construct (comparable) MO IT user for a specific attribute on an Omada user.

        Args:
            omada_user: Omada user.
            omada_attr: Attribute on the Omada user to use as the IT user account name.
            employee_uuid: MO employee UUID.
            engagement_uuid: MO engagement UUID.
            it_system_uuid: IT system of the IT user.

        Returns: Comparable MO IT user if the Omada attribute is set, otherwise None.
        """
        omada_value = getattr(omada_user, omada_attr)
        if omada_value is None:
            return None
        return cls(  # type: ignore[call-arg]
            user_key=str(omada_value),
            itsystem=ITSystemRef(uuid=it_system_uuid),
            person=PersonRef(uuid=employee_uuid),
            engagement=EngagementRef(uuid=engagement_uuid),
            validity=omada_user.validity,
        )


@handle_exclusively_decorator(key=lambda employee_uuid, *_, **__: employee_uuid)
async def sync_it_users(
    employee_uuid: UUID,
    mo: MO,
    omada_api: OmadaAPI,
    model_client: ModelClient,
) -> None:
    """Synchronise Omada IT users to MO.

    Args:
        employee_uuid: UUID of MO employee to synchronise.

    Returns: None.
    """
    logger.info("Synchronising IT users", employee_uuid=employee_uuid)

    # Maps from Omada user attribute to IT system user key in MO
    it_user_map: dict[str, str] = {
        "ad_guid": "omada_ad_guid",
        "login": "omada_login",
    }

    # Get MO classes configuration
    it_systems = await mo.get_it_systems(user_keys=it_user_map.values())
    omada_it_systems = [it_systems[user_key] for user_key in it_user_map.values()]

    # Get current user data from MO
    mo_it_users = await mo.get_employee_it_users(
        uuid=employee_uuid,
        it_systems=omada_it_systems,
    )
    mo_engagements = await mo.get_employee_engagements(uuid=employee_uuid)

    # Get current user data from Omada. Note that we are fetching Omada users for
    # ALL engagements to avoid deleting too many IT users
    engagements = {e.user_key: e for e in mo_engagements}
    raw_omada_users = await omada_api.get_users_by("C_TJENESTENR", engagements.keys())
    omada_users = parse_obj_as(list[SilkeborgOmadaUser], raw_omada_users)

    # Existing IT users in MO
    existing: defaultdict[ComparableITUser, set[ITUser]] = defaultdict(set)
    for mo_it_user in mo_it_users:
        comparable_it_user = ComparableITUser(**mo_it_user.dict())
        existing[comparable_it_user].add(mo_it_user)

    # Desired IT users from Omada
    desired_with_none: set[ComparableITUser | None] = {
        ComparableITUser.from_omada(
            omada_user=omada_user,
            omada_attr=omada_attr,
            employee_uuid=employee_uuid,
            engagement_uuid=engagements[omada_user.service_number].uuid,
            it_system_uuid=it_systems[mo_it_system_user_key],
        )
        for omada_user in omada_users
        for omada_attr, mo_it_system_user_key in it_user_map.items()
    }
    desired: set[ComparableITUser] = cast(
        set[ComparableITUser], desired_with_none - {None}
    )

    # Delete excess existing
    excess: set[ITUser] = set()
    for comparable_it_user, it_users in existing.items():
        first, *duplicate = it_users
        excess.update(duplicate)
        if comparable_it_user not in desired:
            excess.add(first)
    if excess:
        logger.info("Deleting excess IT users", it_users=excess)
        await asyncio.gather(*(mo.delete(a) for a in excess))

    # Create missing desired
    missing_comparable = desired - existing.keys()
    missing_mo = [ITUser(**it_user.dict()) for it_user in missing_comparable]
    if missing_mo:
        logger.info("Creating missing IT users", users=missing_mo)
        await model_client.upload(missing_mo)
