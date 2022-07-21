# SPDX-FileCopyrightText: 2022 Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

import asyncio
from typing import cast
from uuid import UUID

import structlog
from pydantic import parse_obj_as
from ramodels.mo import Validity
from ramodels.mo._shared import AddressType
from ramodels.mo._shared import PersonRef
from ramodels.mo._shared import Visibility
from ramodels.mo.details import Address

from os2mint_omada.backing.omada.models import OmadaUser
from os2mint_omada.sync.base import ComparableMixin
from os2mint_omada.sync.base import StripUserKeyMixin
from os2mint_omada.sync.base import Syncer

logger = structlog.get_logger(__name__)


class ComparableAddress(StripUserKeyMixin, ComparableMixin, Address):
    @classmethod
    def from_omada(
        cls,
        omada_user: OmadaUser,
        omada_attr: str,
        employee_uuid: UUID,
        address_type_uuid: UUID,
        visibility_uuid: UUID,
    ) -> ComparableAddress | None:
        """Construct (comparable) MO address for a specific attribute on an Omada user.

        Args:
            omada_user: Omada user.
            omada_attr: Attribute on the Omada user to use for the address value.
            employee_uuid: MO employee UUID.
            address_type_uuid: Type class of the address.
            visibility_uuid: Visibility class of the address.

        Returns: Comparable MO address if the Omada attribute is set, otherwise None.
        """
        # Omada often returns empty strings for non-existent attributes, which is
        # falsy - and therefore also ignored, like None values.
        omada_value = getattr(omada_user, omada_attr)
        if not omada_value:
            return None
        return cls(
            value=omada_value,
            address_type=AddressType(uuid=address_type_uuid),
            person=PersonRef(uuid=employee_uuid),
            visibility=Visibility(uuid=visibility_uuid),
            validity=Validity(
                from_date=omada_user.valid_from,
                to_date=omada_user.valid_to,
            ),
        )


class AddressSyncer(Syncer):
    async def sync(self, employee_uuid: UUID) -> None:
        """Synchronise Omada addresses to MO.

        Args:
            employee_uuid: UUID of MO employee to synchronise.

        Returns: None.
        """
        logger.info("Synchronising addresses", employee_uuid=employee_uuid)

        # Get current user data from MO
        address_types = await self.mo_service.get_classes("employee_address_type")
        omada_address_types = [
            address_types[user_key] for user_key in self.settings.address_map.values()
        ]
        mo_addresses = await self.mo_service.get_employee_addresses(
            uuid=employee_uuid,
            address_types=omada_address_types,
        )
        mo_engagements = await self.mo_service.get_employee_engagements(
            uuid=employee_uuid
        )

        # Get current user data from Omada. Note that we are fetching Omada users for
        # ALL engagements to avoid deleting too many addresses
        service_numbers = (e.user_key for e in mo_engagements)
        raw_omada_users = await self.omada_service.api.get_users_by_service_numbers(
            service_numbers
        )
        omada_users = parse_obj_as(list[OmadaUser], raw_omada_users)

        # Get MO classes configuration
        visibility_classes = await self.mo_service.get_classes("visibility")

        # Synchronise addresses to MO
        await self.ensure_addresses(
            omada_users=omada_users,
            employee_uuid=employee_uuid,
            addresses=mo_addresses,
            address_map=self.settings.address_map,
            address_types=address_types,
            visibility_uuid=visibility_classes[self.settings.address_visibility],
        )

    async def ensure_addresses(
        self,
        omada_users: list[OmadaUser],
        employee_uuid: UUID,
        addresses: list[Address],
        address_map: dict[str, str],
        address_types: dict[str, UUID],
        visibility_uuid: UUID,
    ) -> None:
        """Ensure that the MO addresses are synchronised with the Omada users.

        Synchronisation is done on ALL Omada user entries for the employee, since total
        knowledge of all of a user's Omada entries is needed to avoid potentially
        terminating addresses related to a different Omada user entry.

        Args:
            omada_users: List of Omada users to synchronise.
            employee_uuid: MO employee UUID.
            addresses: Existing MO addresses.
            address_map: Maps from Omada user attribute to address type user key in MO.
            address_types: Address types for employee addresses.
            visibility_uuid: Visibility class of the addresses.

        Returns: None.
        """
        logger.debug("Ensuring addresses", employee_uuid=employee_uuid)
        # Actual addresses in MO
        actual: dict[ComparableAddress, Address] = {
            ComparableAddress(**address.dict()): address for address in addresses
        }

        # Expected addresses from Omada
        expected_with_none: set[ComparableAddress | None] = {
            ComparableAddress.from_omada(
                omada_user=omada_user,
                omada_attr=omada_attr,
                employee_uuid=employee_uuid,
                address_type_uuid=address_types[mo_address_user_key],
                visibility_uuid=visibility_uuid,
            )
            for omada_user in omada_users
            for omada_attr, mo_address_user_key in address_map.items()
        }
        expected: set[ComparableAddress] = cast(
            set[ComparableAddress], expected_with_none - {None}
        )

        # Terminate excess existing
        excess_addresses = actual.keys() - expected
        if excess_addresses:
            excess_mo_addresses = [actual[a] for a in excess_addresses]  # with UUID
            logger.info("Terminating excess addresses", address=excess_mo_addresses)
            terminate = (self.mo_service.terminate(a) for a in excess_mo_addresses)
            await asyncio.gather(*terminate)

        # Create missing
        missing_addresses = expected - actual.keys()
        if missing_addresses:
            missing_mo_addresses = [
                Address(**address.dict()) for address in missing_addresses  # with UUID
            ]
            logger.info("Creating missing addresses", addresses=missing_mo_addresses)
            await self.mo_service.model.upload(missing_mo_addresses)
