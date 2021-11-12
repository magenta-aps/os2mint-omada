# SPDX-FileCopyrightText: 2021 Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from collections import defaultdict
from typing import Dict
from typing import List
from uuid import UUID

from gql import gql
from raclients.graph.client import GraphQLClient
from ramodels.mo import FacetClass
from ramodels.mo.details import Address
from ramodels.mo.details import ITSystemBinding

from os2mint_omada.clients import client
from os2mint_omada.clients import model_client
from os2mint_omada.config import settings


async def get_root_org() -> UUID:
    """
    Returns: The UUID of the root organisation.
    """
    query = gql(
        """
        query RootOrgQuery {
            org {
                uuid
            }
        }
        """
    )
    client_args = dict(
        client_id=settings.client_id,
        client_secret=settings.client_secret,
        auth_realm=settings.auth_realm,
        auth_server=settings.auth_server,
    )
    async with GraphQLClient(
        url=f"{settings.mo_url}/graphql",
        client_args=client_args,
    ) as client:
        result = await client.execute(query)
    return UUID(result["org"]["uuid"])


async def ensure_address_classes(root_org: UUID) -> Dict[str, UUID]:
    """
    Ensure the required address classes exist in MO.

    Args:
        root_org: The UUID of the root organisation.

    Returns: Dictionary mapping address class user keys into their UUIDs.
    """
    # TODO: This should be handled by os2mo-init instead.
    employee_address_type = await client.get(
        f"{settings.mo_url}/service/o/{root_org}/f/employee_address_type/"
    )
    employee_address_class_uuids = {
        c["user_key"]: UUID(c["uuid"])
        for c in employee_address_type.json()["data"]["items"]
    }

    # Create missing employee address classes
    required_classes = {
        # user_key: (name, scope)
        "EmailEmployee": ("Email", "EMAIL"),  # should always exist in MO already
        "PhoneEmployee": ("Telefon", "PHONE"),  # should always exist in MO already
        "MobilePhoneEmployee": ("Mobiltelefon", "PHONE"),
        "InstitutionPhoneEmployee": ("Institutionstelefonnummer", "PHONE"),
    }
    create = []
    for user_key in required_classes.keys() - employee_address_class_uuids.keys():
        name, scope = required_classes[user_key]
        create.append(
            FacetClass(
                facet_uuid=employee_address_type.json()["uuid"],
                name=name,
                user_key=user_key,
                scope=scope,
                org_uuid=root_org,
            )
        )
    async with model_client.context():
        await model_client.load_mo_objs(create)

    return employee_address_class_uuids | {f.user_key: f.uuid for f in create}


async def get_it_bindings(it_system: UUID) -> Dict[UUID, ITSystemBinding]:
    """
    Get IT system user bindings for the given IT system.

    Args:
        it_system: The UUID of the IT system to get bindings for.

    Returns: Dictionary mapping binding person UUIDs into ITSystemBinding objects.
    """
    it_bindings = await client.get(f"{settings.mo_url}/api/v1/it")
    it_user_bindings_for_system = [
        b
        for b in it_bindings.json()
        if b["person"] is not None and UUID(b["itsystem"]["uuid"]) == it_system
    ]

    # For simplicity it is assumed that each user only has *one* binding for the given
    # IT system. Although there are no guards in MO to maintain this constraint, this
    # precondition should always be true since this integration *should* be the single
    # authoritative source for this IT system.
    unique_persons = len(set(b["person"]["uuid"] for b in it_user_bindings_for_system))
    assert unique_persons == len(it_user_bindings_for_system)
    return {
        UUID(b["person"]["uuid"]): ITSystemBinding.from_simplified_fields(
            uuid=b["uuid"],
            user_key=b["user_key"],
            itsystem_uuid=b["itsystem"]["uuid"],
            person_uuid=b["person"]["uuid"],
            from_date=b["validity"]["from"],
            to_date=b["validity"]["to"],
        )
        for b in it_user_bindings_for_system
    }


async def get_engagements() -> List[dict]:
    """
    Get user engagements.

    Returns: List of engagement dictionaries.
    """
    r = await client.get(f"{settings.mo_url}/api/v1/engagement")
    return r.json()


async def get_user_addresses() -> Dict[UUID, Dict[str, Address]]:
    """
    Get user addresses.

    Returns: Dictionary mapping user person UUIDs to a dictionary of Addresses indexed
             by user_key.
    """
    addresses = await client.get(f"{settings.mo_url}/api/v1/address")
    user_addresses: Dict[UUID, Dict[str, Address]] = defaultdict(dict)
    for address in addresses.json():
        address_person_uuid = (address.get("person") or {}).get("uuid")
        if not address_person_uuid:
            continue
        address_obj = Address.from_simplified_fields(
            uuid=address["uuid"],
            address_type_uuid=address["address_type"]["uuid"],
            value=address["value"],
            value2=address["value2"],
            visibility_uuid=(address.get("visibility") or {}).get("uuid"),
            person_uuid=address_person_uuid,
            org_unit_uuid=(address.get("org_unit") or {}).get("uuid"),
            engagement_uuid=(address.get("engagement") or {}).get("uuid"),
            from_date=address["validity"]["from"],
            to_date=address["validity"]["to"],
        )
        user_key = address["address_type"]["user_key"]
        user_addresses[UUID(address_person_uuid)][user_key] = address_obj

    return dict(user_addresses)
