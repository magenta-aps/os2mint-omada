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

from os2mint_omada.clients import mo_client
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
    required_classes = {
        # user_key: (name, scope)
        "EmailEmployee": ("Email", "EMAIL"),  # should always exist in MO already
        "PhoneEmployee": ("Telefon", "PHONE"),  # should always exist in MO already
        "MobilePhoneEmployee": ("Mobiltelefon", "PHONE"),
        "InstitutionPhoneEmployee": ("Institutionstelefonnummer", "PHONE"),
    }

    # Get existing address classes
    r = await mo_client.get(
        f"{settings.mo_url}/service/o/{root_org}/f/employee_address_type/"
    )
    address_type = r.json()
    address_class_keys_to_uuids = {
        c["user_key"]: UUID(c["uuid"]) for c in address_type["data"]["items"]
    }

    # Create missing address classes
    missing_class_keys = required_classes.keys() - address_class_keys_to_uuids.keys()
    missing_classes = {
        user_key: required_classes[user_key] for user_key in missing_class_keys
    }
    create = [
        FacetClass(
            facet_uuid=address_type["uuid"],
            name=name,
            user_key=user_key,
            scope=scope,
            org_uuid=root_org,
        )
        for user_key, (name, scope) in missing_classes.items()
    ]
    async with model_client.context():
        await model_client.load_mo_objs(create)

    return address_class_keys_to_uuids | {f.user_key: f.uuid for f in create}


async def get_it_bindings(it_system: UUID) -> Dict[UUID, ITSystemBinding]:
    """
    Get IT system user bindings for the given IT system.

    Args:
        it_system: The UUID of the IT system to get bindings for.

    Returns: Dictionary mapping binding person UUIDs into ITSystemBinding objects.
    """
    r = await mo_client.get(f"{settings.mo_url}/api/v1/it")
    it_user_bindings_for_system = [
        b
        for b in r.json()
        if b["person"] is not None and UUID(b["itsystem"]["uuid"]) == it_system
    ]

    it_bindings = {
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
    # For simplicity it is assumed that each user only has *one* binding for the given
    # IT system. Although there are no guards in MO to maintain this constraint, this
    # precondition should always be true since this integration *should* be the single
    # authoritative source for this IT system.
    assert len(it_bindings) == len(it_user_bindings_for_system)
    # TODO: Clean up the IT bindings if assertion doesn't hold

    return it_bindings


async def get_engagements() -> List[dict]:
    """
    Get user engagements.

    Returns: List of engagement dictionaries.
    """
    r = await mo_client.get(f"{settings.mo_url}/api/v1/engagement")
    return r.json()


async def get_user_addresses() -> Dict[UUID, Dict[str, List[Address]]]:
    """
    Get user addresses.

    Returns: Dictionary mapping person UUIDs to a dictionary of lists of their adresses,
     indexed by its user key.
    """
    addresses = await mo_client.get(f"{settings.mo_url}/api/v1/address")
    addresses_for_persons = (a for a in addresses.json() if a.get("person") is not None)
    user_addresses: Dict[UUID, Dict[str, List[Address]]] = defaultdict(
        lambda: defaultdict(list)
    )
    for address in addresses_for_persons:
        address_person_uuid = address["person"]["uuid"]
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
        user_addresses[UUID(address_person_uuid)][user_key].append(address_obj)

    # Converting to normal dicts to avoid surprises further down the line
    return {uuid: dict(a) for uuid, a in user_addresses.items()}
