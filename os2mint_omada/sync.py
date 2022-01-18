# SPDX-FileCopyrightText: 2021 Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from ramodels.mo import MOBase
from ramodels.mo._shared import Validity
from ramodels.mo.details import Address
from ramodels.mo.details import ITUser

from os2mint_omada.omada import OmadaITUser
from os2mint_omada.util import as_terminated
from os2mint_omada.util import midnight

ADDRESS_USER_KEY_TO_OMADA_ATTR = {
    "EmailEmployee": "email",
    "PhoneEmployee": "phone_direct",
    "MobilePhoneEmployee": "phone_cell",
    "InstitutionPhoneEmployee": "phone_institution",
}


@dataclass
class User:
    omada_it_user: Optional[OmadaITUser]
    mo_it_user: Optional[ITUser]
    mo_addresses: dict[str, list[Address]]
    mo_person_uuid: UUID


def _updated_mo_objects(
    user: User,
    it_system_uuid: UUID,
    address_class_uuids: dict[str, UUID],
    address_visibility_uuid: UUID,
) -> Iterator[MOBase]:
    """
    Given a User containing linked Omada and MO data, yield new or updated MO objects,
    such that they correspond to the Omada data.

    Args:
        user: Object containing Omada and MO data for a single user.
        it_system_uuid: UUID of the IT system users are inserted into in MO.
        address_class_uuids: Mapping of address class user keys into their UUIDS.
        address_visibility_uuid: UUID of the visibility class addresses are created
         with.

    Yields: New or updated MO objects.
    """
    yield from _updated_it_user(user=user, it_system_uuid=it_system_uuid)
    yield from _terminate_excess_addresses(user=user)
    yield from _updated_addresses(
        user=user,
        address_class_uuids=address_class_uuids,
        visibility_uuid=address_visibility_uuid,
    )


def _updated_it_user(user: User, it_system_uuid: UUID) -> Iterator[MOBase]:
    """
    Yield a new or updated (i.e. expired) MO IT User for the given user. The IT User
    binding will always either be created or deleted, never updated, since it only
    contains the user_key, which is exactly the field we use to map the objects.

    Args:
        user: Object containing Omada and MO data for a single user.
        it_system_uuid: UUID of the IT system users are inserted into in MO.

    Yields: Updated MO IT User.
    """
    # Create if user exists in Omada, but not in MO
    if user.omada_it_user and not user.mo_it_user:
        yield ITUser.from_simplified_fields(
            uuid=None,  # new user
            user_key=str(user.omada_it_user.ad_guid),  # account name
            itsystem_uuid=it_system_uuid,
            person_uuid=user.mo_person_uuid,
            from_date=midnight().isoformat(),
            to_date=None,  # infinity
        )
        return

    # Delete if user exists in MO, but not in Omada
    if not user.omada_it_user and user.mo_it_user:
        yield as_terminated(user.mo_it_user)


def _terminate_excess_addresses(user: User) -> Iterator[MOBase]:
    """
    Terminate excess addresses for the user, since omada is authoritative for all
    adresses of these types, and we want at most one.

    Args:
        user: Object containing Omada and MO data for a single user.

    Yields: Excess MO addresses as terminated.
    """
    for user_key, omada_attribute_name in ADDRESS_USER_KEY_TO_OMADA_ATTR.items():
        try:
            excess_mo_addresses = user.mo_addresses[user_key][1:]
        except KeyError:
            continue
        for address in excess_mo_addresses:
            yield as_terminated(address)


def _updated_addresses(
    user: User, address_class_uuids: dict[str, UUID], visibility_uuid: UUID
) -> Iterator[MOBase]:
    """
    Yield new or updated MO addresses for the given user.

    Args:
        user: Object containing Omada and MO data for a single user.
        address_class_uuids: Mapping of address class user keys into their UUIDS.
        visibility_uuid: UUID of the visibility class addresses are created with.

    Yields: Updated MO addresses.
    """
    for user_key, omada_attribute_name in ADDRESS_USER_KEY_TO_OMADA_ATTR.items():
        try:
            mo_address = user.mo_addresses[user_key][0]
        except (KeyError, IndexError):
            mo_address = None

        # Create or update MO address if Omada attribute was added or changed. Omada
        # returns empty strings for non-existent attributes, which is falsy.
        omada_attribute = getattr(user.omada_it_user, omada_attribute_name, None)
        if omada_attribute and (not mo_address or mo_address.value != omada_attribute):
            attributes = dict(
                value=omada_attribute,
                validity=Validity(from_date=midnight(), to_date=None),
            )
            if not mo_address:
                address = dict(
                    uuid=None,  # new address
                    address_type=dict(uuid=address_class_uuids[user_key]),
                    person=dict(uuid=user.mo_person_uuid),
                    visibility=dict(uuid=visibility_uuid),
                    **attributes
                )
            else:
                address = mo_address.copy(update=attributes)
            yield Address.parse_obj(address)

        # Delete MO address if Omada attribute was removed
        if not omada_attribute and mo_address:
            yield as_terminated(mo_address)


def get_updated_mo_objects(
    mo_it_users: dict[UUID, ITUser],
    omada_it_users: list[OmadaITUser],
    mo_user_addresses: dict[UUID, dict[str, list[Address]]],
    mo_engagements: list[dict],
    address_class_uuids: dict[str, UUID],
    it_system_uuid: UUID,
    address_visibility_uuid: UUID,
) -> Iterator[MOBase]:
    """
    Given Omada and MO data, yield new or updated MO objects that needs to be sent to
    the server, such that they correspond to the Omada data.

    Args:
        mo_it_users: MO IT users.
        omada_it_users: Omada IT users.
        mo_user_addresses: Dictionary mapping person UUIDs to a dictionary of lists of
         their adresses, indexed by its user key.
        mo_engagements: List of MO engagement dicts.
        address_class_uuids: Dictionary mapping address class user keys into UUIDs.
        it_system_uuid: UUID of the IT system users are inserted into in MO.
        address_visibility_uuid: UUID of the visibility class addresses are created
         with.

    Yields: New or updated MO objects.
    """
    # Omada and MO users are linked through the 'TJENESTENR' field. However 'TJENESTENR'
    # is not set on the MO users directly, but on their engagement as the 'user_key',
    # so we need to link through that.
    service_number_to_omada = {u.service_number: u for u in omada_it_users}
    person_to_omada = {
        UUID(e["person"]["uuid"]): service_number_to_omada.get(e["user_key"])
        for e in mo_engagements
    }
    mo_person_uuids = mo_it_users.keys()
    omada_person_uuids = person_to_omada.keys()
    for person_uuid in mo_person_uuids | omada_person_uuids:
        user = User(
            omada_it_user=person_to_omada.get(person_uuid),
            mo_it_user=mo_it_users.get(person_uuid),
            mo_addresses=mo_user_addresses.get(person_uuid, {}),
            mo_person_uuid=person_uuid,
        )
        yield from _updated_mo_objects(
            user=user,
            it_system_uuid=it_system_uuid,
            address_class_uuids=address_class_uuids,
            address_visibility_uuid=address_visibility_uuid,
        )
