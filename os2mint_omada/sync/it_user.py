# SPDX-FileCopyrightText: 2022 Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

import asyncio
from uuid import UUID

import structlog
from pydantic import parse_obj_as
from ramodels.mo import Validity
from ramodels.mo._shared import EngagementRef
from ramodels.mo._shared import ITSystemRef
from ramodels.mo._shared import PersonRef
from ramodels.mo.details import Engagement
from ramodels.mo.details import ITUser
from ramqp.utils import handle_exclusively
from ramqp.utils import sleep_on_error

from os2mint_omada.backing.mo.service import ITSystems
from os2mint_omada.backing.omada.models import OmadaUser
from os2mint_omada.sync.base import ComparableMixin
from os2mint_omada.sync.base import Syncer

logger = structlog.get_logger(__name__)


class ComparableITUser(ComparableMixin, ITUser):
    @classmethod
    def from_omada(
        cls,
        omada_user: OmadaUser,
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
            validity=Validity(
                from_date=omada_user.valid_from,
                to_date=omada_user.valid_to,
            ),
        )


class ITUserSyncer(Syncer):
    @handle_exclusively(key=lambda self, employee_uuid: employee_uuid)
    @sleep_on_error()
    async def sync(self, employee_uuid: UUID) -> None:
        """Synchronise Omada IT users to MO.

        Args:
            employee_uuid: UUID of MO employee to synchronise.

        Returns: None.
        """
        logger.info("Synchronising IT users", employee_uuid=employee_uuid)

        # Get MO classes configuration
        it_systems = await self.mo_service.get_it_systems()
        omada_it_systems = [
            it_systems[user_key] for user_key in self.settings.mo.it_user_map.values()
        ]

        # Get current user data from MO
        mo_it_users = await self.mo_service.get_employee_it_users(
            uuid=employee_uuid,
            it_systems=omada_it_systems,
        )
        mo_engagements = await self.mo_service.get_employee_engagements(
            uuid=employee_uuid
        )

        # Get current user data from Omada. Note that we are fetching Omada users for
        # ALL engagements to avoid deleting too many IT users
        engagements = {e.user_key: e for e in mo_engagements}
        raw_omada_users = await self.omada_service.api.get_users_by_service_numbers(
            service_numbers=engagements.keys()
        )
        omada_users = parse_obj_as(list[OmadaUser], raw_omada_users)

        # Synchronise IT users to MO
        await self.ensure_it_users(
            omada_users=omada_users,
            employee_uuid=employee_uuid,
            engagements=engagements,
            it_users=mo_it_users,
            it_user_map=self.settings.mo.it_user_map,
            it_systems=it_systems,
        )

    async def ensure_it_users(
        self,
        omada_users: list[OmadaUser],
        employee_uuid: UUID,
        engagements: dict[str, Engagement],
        it_users: set[ITUser],
        it_user_map: dict[str, str],
        it_systems: ITSystems,
    ) -> None:
        """Ensure that MO IT users are synchronised with the Omada users.

        Synchronisation is done on ALL Omada user entries for the employee, since total
        knowledge of all of a user's Omada entries is needed to avoid potentially
        deleting it users related to a different Omada user entry.

        Args:
            omada_users: List of Omada users to synchronise.
            employee_uuid: MO employee UUID.
            engagements: Dict from Omada service numbers to MO engagements.
            it_users: Existing MO IT users.
            it_user_map: Maps from Omada user attribute to IT system user key in MO.
            it_systems: IT systems configured in MO.

        Returns: None.
        """
        logger.info("Ensuring IT users", employee_uuid=employee_uuid)
        # Actual IT users in MO
        actual: dict[ComparableITUser, ITUser] = {
            ComparableITUser(**it_user.dict()): it_user for it_user in it_users
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
            delete = (self.mo_service.delete(u) for u in excess_mo_users)
            await asyncio.gather(*delete)

        # Create missing
        missing_it_users = expected - actual.keys()
        if missing_it_users:
            missing_mo_it_users = [
                ITUser(**it_user.dict()) for it_user in missing_it_users
            ]
            logger.info("Creating missing IT users", users=missing_mo_it_users)
            await self.mo_service.model.upload(missing_mo_it_users)
