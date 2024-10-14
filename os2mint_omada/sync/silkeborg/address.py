# SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

import asyncio
from collections import defaultdict
from uuid import UUID

import structlog
from fastramqpi.ramqp.depends import handle_exclusively_decorator
from pydantic import parse_obj_as

from os2mint_omada.mo import MO
from os2mint_omada.omada.api import OmadaAPI

from ...autogenerated_graphql_client import AddressCreateInput
from ...autogenerated_graphql_client import RAValidityInput
from ..models import Address
from ..models import ComparableAddress
from .models import SilkeborgOmadaUser

logger = structlog.stdlib.get_logger()


@handle_exclusively_decorator(key=lambda employee_uuid, *_, **__: employee_uuid)
async def sync_addresses(
    employee_uuid: UUID,
    mo: MO,
    omada_api: OmadaAPI,
) -> None:
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
    omada_address_types = [address_types[user_key] for user_key in address_map.values()]
    it_systems = await mo.get_it_systems(user_keys=["omada_login"])
    omada_it_system = it_systems["omada_login"]

    # Visibility class for created addresses
    visibility_classes = await mo.get_classes("visibility")
    visibility_uuid = visibility_classes["Public"]

    # Get current user data from MO
    mo_engagements = await mo.get_employee_engagements(uuid=employee_uuid)
    engagements = {e.user_key: e for e in mo_engagements}

    mo_it_users = await mo.get_employee_it_users(
        uuid=employee_uuid,
        it_systems=[omada_it_system],
    )
    it_users = {u.engagement: u for u in mo_it_users}
    assert all(u is not None for u in it_users)

    mo_addresses = await mo.get_employee_addresses(
        uuid=employee_uuid,
        address_types=omada_address_types,
    )

    # Get current user data from Omada. Note that we are fetching Omada users for
    # ALL engagements to avoid deleting too many addresses
    raw_omada_users = await omada_api.get_users_by("C_TJENESTENR", engagements.keys())
    omada_users = parse_obj_as(list[SilkeborgOmadaUser], raw_omada_users)

    # Existing addresses in MO
    existing: defaultdict[ComparableAddress, set[Address]] = defaultdict(set)
    for mo_address in mo_addresses:
        comparable_address = ComparableAddress(**mo_address.dict())
        existing[comparable_address].add(mo_address)

    # Desired addresses from Omada
    desired = set()
    for omada_user in omada_users:
        for omada_attr, mo_address_user_key in address_map.items():
            omada_value = getattr(omada_user, omada_attr)
            if omada_value is None:
                continue
            engagement = engagements[omada_user.service_number].uuid
            c = ComparableAddress(
                value=omada_value,
                address_type=address_types[mo_address_user_key],
                person=employee_uuid,
                visibility=visibility_uuid,
                engagement=engagement,
                it_user=it_users[engagement].uuid,
                validity=omada_user.validity,
            )
            desired.add(c)

    # Delete excess existing
    excess: set[Address] = set()
    for comparable_address, addresses in existing.items():
        first, *duplicate = addresses
        excess.update(duplicate)
        if comparable_address not in desired:
            excess.add(first)
    if excess:
        logger.info("Deleting excess addresses", addresses=excess)
        await asyncio.gather(*(mo.delete_address(a) for a in excess))

    # Create missing desired
    missing_comparable = desired - existing.keys()
    missing_mo = [Address(**address.dict()) for address in missing_comparable]
    if missing_mo:
        logger.info("Creating missing addresses", addresses=missing_mo)
        for missing in missing_mo:
            await mo.graphql_client.create_address(
                AddressCreateInput(
                    value=missing.value,
                    address_type=missing.address_type,
                    person=missing.person,
                    engagement=missing.engagement,
                    ituser=missing.it_user,
                    visibility=missing.visibility,
                    validity=RAValidityInput(
                        from_=missing.validity.start,
                        to=missing.validity.end,
                    ),
                )
            )
