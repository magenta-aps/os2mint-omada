# SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import cast
from uuid import UUID

import structlog
from more_itertools import only
from pydantic import parse_obj_as
from raclients.modelclient.mo import ModelClient
from ramodels.mo._shared import ITSystemRef
from ramodels.mo._shared import PersonRef
from ramodels.mo.details import ITUser
from ramqp.depends import handle_exclusively_decorator

from .models import EgedalOmadaUser
from os2mint_omada.mo import MO
from os2mint_omada.omada.api import OmadaAPI
from os2mint_omada.sync.models import ComparableMixin

logger = structlog.get_logger(__name__)


class ComparableITUser(ComparableMixin, ITUser):
    @classmethod
    def from_omada(
        cls,
        omada_user: EgedalOmadaUser,
        omada_attr: str,
        employee_uuid: UUID,
        it_system_uuid: UUID,
    ) -> ComparableITUser | None:
        """Construct (comparable) MO IT user for a specific attribute on an Omada user.

        Args:
            omada_user: Omada user.
            omada_attr: Attribute on the Omada user to use as the IT user account name.
            employee_uuid: MO employee UUID.
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

    # Maps from Omada user attribute to IT system user key in MO
    it_user_map: dict[str, str] = {
        "ad_guid": "omada_ad_guid",
        "ad_login": "omada_login",
    }

    # Get MO classes configuration
    it_systems = await mo.get_it_systems(user_keys=it_user_map.values())
    omada_it_systems = [it_systems[user_key] for user_key in it_user_map.values()]

    # Get current user data from MO
    mo_it_users = await mo.get_employee_it_users(
        uuid=employee_uuid,
        it_systems=omada_it_systems,
    )

    # Get current user data from Omada. Note that we are fetching ALL Omada users for
    # the CPR-number to avoid deleting too many IT users
    raw_omada_users = await omada_api.get_users_by("C_EMPLOYEEID", [cpr_number])
    omada_users = parse_obj_as(list[EgedalOmadaUser], raw_omada_users)

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
