# SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

import asyncio
from uuid import UUID

import structlog
from pydantic import parse_obj_as
from raclients.modelclient.mo import ModelClient
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
    ) -> ComparableITUser:
        """Construct (comparable) MO IT user for a specific attribute on an Omada user.

        Args:
            omada_user: Omada user.
            omada_attr: Attribute on the Omada user to use as the IT user account name.
            employee_uuid: MO employee UUID.
            engagement_uuid: MO engagement UUID.
            it_system_uuid: IT system of the IT user.

        Returns: Comparable MO IT user for the Omada attribute.
        """
        return cls(  # type: ignore[call-arg]
            user_key=str(getattr(omada_user, omada_attr)),
            itsystem=ITSystemRef(uuid=it_system_uuid),
            person=PersonRef(uuid=employee_uuid),
            engagement=EngagementRef(uuid=engagement_uuid),
            validity=omada_user.validity,
        )


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

    # Get MO classes configuration
    it_systems = await mo.get_it_systems()
    # Maps from Omada user attribute to IT system user key in MO
    it_user_map: dict[str, str] = {
        "ad_guid": "omada_ad_guid",
        "login": "omada_login",
    }
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
    raw_omada_users = await omada_api.get_users_by_service_numbers(
        service_numbers=engagements.keys()
    )
    omada_users = parse_obj_as(list[SilkeborgOmadaUser], raw_omada_users)

    # Synchronise IT users to MO
    logger.info("Ensuring IT users", employee_uuid=employee_uuid)
    # Actual IT users in MO
    actual: dict[ComparableITUser, ITUser] = {
        ComparableITUser(**it_user.dict()): it_user for it_user in mo_it_users
    }

    # Expected IT users from Omada
    expected: set[ComparableITUser] = {
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

    # Delete excess existing
    excess_it_users = actual.keys() - expected
    if excess_it_users:
        excess_mo_users = [actual[u] for u in excess_it_users]  # with UUID
        logger.info("Deleting excess IT users", it_users=excess_it_users)
        delete = (mo.delete(u) for u in excess_mo_users)
        await asyncio.gather(*delete)

    # Create missing
    missing_it_users = expected - actual.keys()
    if missing_it_users:
        missing_mo_it_users = [ITUser(**it_user.dict()) for it_user in missing_it_users]
        logger.info("Creating missing IT users", users=missing_mo_it_users)
        await model_client.upload(missing_mo_it_users)
