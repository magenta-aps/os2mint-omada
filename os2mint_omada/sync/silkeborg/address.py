# SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

import asyncio
from typing import cast
from uuid import UUID

import structlog
from pydantic import parse_obj_as
from raclients.modelclient.mo import ModelClient
from ramodels.mo._shared import AddressType
from ramodels.mo._shared import EngagementRef
from ramodels.mo._shared import PersonRef
from ramodels.mo._shared import Visibility
from ramodels.mo.details import Address
from ramqp.depends import handle_exclusively_decorator

from .models import SilkeborgOmadaUser
from os2mint_omada.mo import MO
from os2mint_omada.omada.api import OmadaAPI
from os2mint_omada.sync.models import ComparableMixin
from os2mint_omada.sync.models import StripUserKeyMixin

logger = structlog.get_logger(__name__)


class ComparableAddress(StripUserKeyMixin, ComparableMixin, Address):
    @classmethod
    def from_omada(
        cls,
        omada_user: SilkeborgOmadaUser,
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
        # Omada often returns empty strings for non-existent attributes, which is
        # falsy - and therefore also ignored, like None values.
        omada_value = getattr(omada_user, omada_attr)
        if not omada_value:
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
        "email": "EmailEmployee",
        "phone_direct": "PhoneEmployee",
        "phone_cell": "MobilePhoneEmployee",
        "phone_institution": "InstitutionPhoneEmployee",
    }

    # Get MO classes configuration
    address_types = await mo.get_classes("employee_address_type")

    # Engagement type for engagements created for omada users
    engagement_types = await mo.get_classes("engagement_type")
    engagement_type_uuid = engagement_types["omada_manually_created"]

    # Visibility class for created addresses
    visibility_classes = await mo.get_classes("visibility")
    visibility_uuid = visibility_classes["Public"]

    # Get current user data from MO
    mo_engagements = await mo.get_employee_engagements(uuid=employee_uuid)
    mo_addresses = await mo.get_employee_addresses(
        uuid=employee_uuid,
        engagement_types={engagement_type_uuid},
    )

    # Get current user data from Omada. Note that we are fetching Omada users for
    # ALL engagements to avoid deleting too many addresses
    engagements = {e.user_key: e for e in mo_engagements}
    raw_omada_users = await omada_api.get_users_by("C_TJENESTENR", engagements.keys())
    omada_users = parse_obj_as(list[SilkeborgOmadaUser], raw_omada_users)

    # Synchronise addresses to MO
    logger.info("Ensuring addresses", employee_uuid=employee_uuid)
    # Actual addresses in MO
    actual: dict[ComparableAddress, Address] = {
        ComparableAddress(**address.dict()): address for address in mo_addresses
    }

    # Expected addresses from Omada
    expected_with_none: set[ComparableAddress | None] = {
        ComparableAddress.from_omada(
            omada_user=omada_user,
            omada_attr=omada_attr,
            employee_uuid=employee_uuid,
            engagement_uuid=engagements[omada_user.service_number].uuid,
            address_type_uuid=address_types[mo_address_user_key],
            visibility_uuid=visibility_uuid,
        )
        for omada_user in omada_users
        for omada_attr, mo_address_user_key in address_map.items()
    }
    expected: set[ComparableAddress] = cast(
        set[ComparableAddress], expected_with_none - {None}
    )

    # Delete excess existing
    excess_addresses = actual.keys() - expected
    if excess_addresses:
        excess_mo_addresses = [actual[a] for a in excess_addresses]  # with UUID
        logger.info("Deleting excess addresses", address=excess_mo_addresses)
        delete = (mo.delete(a) for a in excess_mo_addresses)
        await asyncio.gather(*delete)

    # Create missing
    missing_addresses = expected - actual.keys()
    if missing_addresses:
        missing_mo_addresses = [
            Address(**address.dict()) for address in missing_addresses  # with UUID
        ]
        logger.info("Creating missing addresses", addresses=missing_mo_addresses)
        await model_client.upload(missing_mo_addresses)
