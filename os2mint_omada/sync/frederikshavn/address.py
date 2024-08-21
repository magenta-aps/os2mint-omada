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
from ramodels.mo._shared import AddressType
from ramodels.mo._shared import EngagementRef
from ramodels.mo._shared import PersonRef
from ramodels.mo._shared import Visibility
from ramodels.mo.details import Address

from os2mint_omada.mo import MO
from os2mint_omada.omada.api import OmadaAPI
from os2mint_omada.sync.models import ComparableMixin
from os2mint_omada.sync.models import StripUserKeyMixin

from .models import FrederikshavnOmadaUser

logger = structlog.get_logger(__name__)


class ComparableAddress(StripUserKeyMixin, ComparableMixin, Address):
    @classmethod
    def from_omada(
        cls,
        omada_user: FrederikshavnOmadaUser,
        omada_attr: str,
        employee_uuid: UUID,
        engagement_uuid: UUID,
        address_type_uuid: UUID,
        visibility_uuid: UUID,
    ) -> ComparableAddress | None:
        """Construct (comparable) MO address for a specific attribute on an Omada user.

        Args:
            omada_user: Omada user.
            omada_attr: Attribute on the Omada user to use for the address value.
            employee_uuid: MO employee UUID.
            engagement_uuid: MO engagement UUID.
            address_type_uuid: Type class of the address.
            visibility_uuid: Visibility class of the address.

        Returns: Comparable MO address if the Omada attribute is set, otherwise None.
        """
        omada_value = getattr(omada_user, omada_attr)
        if omada_value is None:
            return None
        return cls(  # type: ignore[call-arg]
            value=omada_value,
            address_type=AddressType(uuid=address_type_uuid),
            person=PersonRef(uuid=employee_uuid),
            engagement=EngagementRef(uuid=engagement_uuid),
            visibility=Visibility(uuid=visibility_uuid),
            validity=omada_user.validity,
        )


@handle_exclusively_decorator(key=lambda employee_uuid, *_, **__: employee_uuid)
async def sync_addresses(
    employee_uuid: UUID,
    mo: MO,
    omada_api: OmadaAPI,
    model_client: ModelClient,
) -> None:
    """Synchronise Omada addresses to MO.

    Args:
        employee_uuid: UUID of MO employee to synchronise.

    Returns: None.
    """
    logger.info("Synchronising addresses", employee_uuid=employee_uuid)

    # Maps from Omada user attribute to employee address type (class) user key in MO
    address_map: dict[str, str] = {
        "email": "OmadaEmailEmployee",
        "phone": "OmadaPhoneEmployee",
        "cellphone": "OmadaMobilePhoneEmployee",
    }

    # Get MO classes configuration
    address_types = await mo.get_classes("employee_address_type")
    omada_address_types = [address_types[user_key] for user_key in address_map.values()]

    # Visibility class for created addresses
    visibility_classes = await mo.get_classes("visibility")
    visibility_uuid = visibility_classes["Public"]

    # Get current user data from MO
    mo_engagements = await mo.get_employee_engagements(uuid=employee_uuid)
    mo_addresses = await mo.get_employee_addresses(
        uuid=employee_uuid,
        address_types=omada_address_types,
    )

    # Get current user data from Omada. Note that we are fetching Omada users for
    # ALL engagements to avoid deleting too many addresses
    engagements = {e.user_key: e for e in mo_engagements}
    raw_omada_users = await omada_api.get_users_by(
        "C_MEDARBEJDERNR_ODATA", engagements.keys()
    )
    omada_users = parse_obj_as(list[FrederikshavnOmadaUser], raw_omada_users)

    # Existing addresses in MO
    existing: defaultdict[ComparableAddress, set[Address]] = defaultdict(set)
    for mo_address in mo_addresses:
        comparable_address = ComparableAddress(**mo_address.dict())
        existing[comparable_address].add(mo_address)

    # Desired addresses from Omada
    desired_with_none: set[ComparableAddress | None] = {
        ComparableAddress.from_omada(
            omada_user=omada_user,
            omada_attr=omada_attr,
            employee_uuid=employee_uuid,
            engagement_uuid=engagements[omada_user.employee_number].uuid,
            address_type_uuid=address_types[mo_address_user_key],
            visibility_uuid=visibility_uuid,
        )
        for omada_user in omada_users
        for omada_attr, mo_address_user_key in address_map.items()
    }
    desired: set[ComparableAddress] = cast(
        set[ComparableAddress], desired_with_none - {None}
    )

    # Delete excess existing
    excess: set[Address] = set()
    for comparable_address, addresses in existing.items():
        first, *duplicate = addresses
        excess.update(duplicate)
        if comparable_address not in desired:
            excess.add(first)
    if excess:
        logger.info("Deleting excess addresses", addresses=excess)
        await asyncio.gather(*(mo.delete(a) for a in excess))

    # Create missing desired
    missing_comparable = desired - existing.keys()
    missing_mo = [Address(**address.dict()) for address in missing_comparable]
    if missing_mo:
        logger.info("Creating missing addresses", addresses=missing_mo)
        await model_client.upload(missing_mo)
