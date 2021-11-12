# SPDX-FileCopyrightText: 2021 Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from dataclasses import dataclass
from datetime import datetime
from typing import Dict
from typing import Iterator
from typing import Optional
from uuid import UUID

from ramodels.mo import MOBase
from ramodels.mo._shared import Validity
from ramodels.mo.details import Address
from ramodels.mo.details import ITSystemBinding

from os2mint_omada.omada import OmadaITUser
from os2mint_omada.util import as_terminated

address_user_key_to_omada_attr = {
    "EmailEmployee": "EMAIL",
    "PhoneEmployee": "C_DIREKTE_TLF",
    "MobilePhoneEmployee": "CELLPHONE",
    "InstitutionPhoneEmployee": "C_INST_PHONE",
}


@dataclass
class User:
    omada_it_user: Optional[OmadaITUser]
    mo_it_system_binding: Optional[ITSystemBinding]
    mo_addresses: Dict[str, Address]
    mo_person_uuid: UUID


def update(
    user: User, it_system_uuid: UUID, address_class_uuids: Dict[str, UUID]
) -> Iterator[MOBase]:
    """
    Given a list of Omada IT users and MO objects, yield new or updated MO objects such
    that they correspond to the Omada ones.

    Args:
        user: Object containing Omada and MO data for a single user.
        it_system_uuid: UUID of the IT system users are inserted into in MO.
        address_class_uuids: Mapping of address class user keys into their UUIDS.

    Yields: New or updated MO objects.
    """
    now = datetime.utcnow().date()  # time must be midnight when writing

    # CREATE/UPDATE if user exists in Omada.
    # We cannot update bindings -- only addresses -- since the only data stored in the
    # bindings is the user_key, which is exactly the field we use to map the objects.
    if user.omada_it_user:
        if not user.mo_it_system_binding:
            yield ITSystemBinding.from_simplified_fields(
                uuid=None,  # new binding
                user_key=str(user.omada_it_user.C_OBJECTGUID_I_AD),  # account name
                itsystem_uuid=it_system_uuid,
                person_uuid=user.mo_person_uuid,
                from_date=now.isoformat(),
                to_date=None,  # infinity
            )

        for user_key, omada_attribute_name in address_user_key_to_omada_attr.items():
            # Omada returns empty strings for non-existent attributes, which is falsy
            omada_attribute = getattr(user.omada_it_user, omada_attribute_name)
            mo_address = user.mo_addresses.get(user_key)

            # Create address if missing
            if omada_attribute and not mo_address:
                yield Address.from_simplified_fields(
                    uuid=None,  # new address
                    address_type_uuid=address_class_uuids[user_key],
                    value=omada_attribute,
                    person_uuid=user.mo_person_uuid,
                    from_date=now.isoformat(),
                    to_date=None,  # infinity
                )

            # Update address if Omada attribute has changed
            if omada_attribute and mo_address:
                if omada_attribute != mo_address.value:
                    yield mo_address.copy(
                        update=dict(
                            value=omada_attribute,
                            validity=Validity(from_date=now, to_date=None),
                        )
                    )

            # Delete address if Omada attribute was removed
            if not omada_attribute and mo_address:
                yield as_terminated(mo_address, from_date=now)

    # DELETE if user does not exist in Omada, but in MO
    elif not user.omada_it_user and user.mo_it_system_binding:
        yield as_terminated(user.mo_it_system_binding, from_date=now)

        for address in user.mo_addresses.values():
            yield as_terminated(address, from_date=now)


def get_updated_mo_objects(
    mo_it_bindings: Dict[UUID, ITSystemBinding],
    omada_it_users: Dict[str, OmadaITUser],
    mo_user_addresses: Dict[UUID, Dict[str, Address]],
    service_number_to_person: Dict[str, UUID],
    address_classes: Dict[str, UUID],
    it_system_uuid: UUID,
) -> Iterator[MOBase]:
    """
    Given Omada and MO data, yield new or updated MO objects that needs to be send to
    the server, such that they correspond to the Omada data.

    Args:
        mo_it_bindings: MO IT system user bindings.
        omada_it_users: Omada IT users.
        mo_user_addresses: MO user addresses.
        service_number_to_person: Dictionary mapping Omada 'TJENESTENR' to MO person
         UUIDs.
        address_classes: Dictionary mapping address class user keys into their UUIDs.
        it_system_uuid: UUID of the IT system users are inserted into in MO.

    Yields: New or updated MO objects.
    """
    person_to_service_number = {
        person_uuid: service_number
        for service_number, person_uuid in service_number_to_person.items()
    }

    def get_omada_it_user(person_uuid: UUID) -> Optional[OmadaITUser]:
        try:
            service_number = person_to_service_number[person_uuid]
            return omada_it_users[service_number]
        except KeyError:
            return None

    mo_person_uuids = mo_it_bindings.keys()
    omada_person_uuids = set(service_number_to_person[n] for n in omada_it_users.keys())
    for person_uuid in mo_person_uuids | omada_person_uuids:
        user = User(
            omada_it_user=get_omada_it_user(person_uuid),
            mo_it_system_binding=mo_it_bindings.get(person_uuid),
            mo_addresses=mo_user_addresses.get(person_uuid, {}),
            mo_person_uuid=person_uuid,
        )
        yield from update(
            user=user,
            it_system_uuid=it_system_uuid,
            address_class_uuids=address_classes,
        )
