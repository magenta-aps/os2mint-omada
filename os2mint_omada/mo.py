# SPDX-FileCopyrightText: 2021 Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from collections import defaultdict
from uuid import UUID

from gql import gql
from ramodels.mo.details import Address
from ramodels.mo.details import ITUser

from os2mint_omada.clients import graphql_client
from os2mint_omada.clients import mo_client


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
    result = await graphql_client.execute(query)
    return UUID(result["org"]["uuid"])


async def get_classes(organisation_uuid: UUID, facet: str) -> dict[str, UUID]:
    """
    Get classes for the given facet.

    Args:
        organisation_uuid: UUID of the (root) organisation.
        facet: Name of the facet.

    Returns: Dictionary mapping class user keys into their UUIDs.
    """
    r = await mo_client.get(f"/service/o/{organisation_uuid}/f/{facet}/")
    classes = r.json()["data"]["items"]
    return {c["user_key"]: UUID(c["uuid"]) for c in classes}


async def get_it_system_uuid(organisation_uuid: UUID, user_key: str) -> UUID:
    """
    Get the UUID of the MO IT System with the provided user key.

    Args:
        organisation_uuid: UUID of the (root) organisation.
        user_key: User key of the IT system.

    Returns: UUID of the IT System with the provided user key, or KeyError if it does
     not exist.
    """
    r = await mo_client.get(f"/service/o/{organisation_uuid}/it/")
    try:
        return next(UUID(i["uuid"]) for i in r.json() if i["user_key"] == user_key)
    except StopIteration:
        raise KeyError(f"IT System with '{user_key=}' does not exist.")


async def get_it_users(it_system: UUID) -> dict[UUID, ITUser]:
    """
    Get IT users for the given IT system.

    Args:
        it_system: The UUID of the IT system to get users for.

    Returns: Dictionary mapping person UUIDs into ITUser objects.
    """
    r = await mo_client.get("/api/v1/it")
    it_users_for_system = [
        b
        for b in r.json()
        if b["person"] is not None and UUID(b["itsystem"]["uuid"]) == it_system
    ]

    it_users = {
        UUID(b["person"]["uuid"]): ITUser.from_simplified_fields(
            uuid=b["uuid"],
            user_key=b["user_key"],
            itsystem_uuid=b["itsystem"]["uuid"],
            person_uuid=b["person"]["uuid"],
            from_date=b["validity"]["from"],
            to_date=b["validity"]["to"],
        )
        for b in it_users_for_system
    }
    # For simplicity, it is assumed that each user only has *one* MO ITUser for the
    # given IT system. Although there are no guards in MO to maintain this constraint,
    # this precondition should always be true since this integration *should* be the
    # single authoritative source for this IT system.
    assert len(it_users) == len(it_users_for_system)
    # TODO: Clean up the IT Users if assertion doesn't hold

    return it_users


async def get_engagements() -> list[dict]:
    """
    Get user engagements.

    Returns: List of engagement dictionaries.
    """
    r = await mo_client.get("/api/v1/engagement")
    return r.json()


async def get_user_addresses() -> dict[UUID, dict[str, list[Address]]]:
    """
    Get user addresses.

    Returns: Dictionary mapping person UUIDs to a dictionary of lists of their adresses,
     indexed by its user key.
    """
    addresses = await mo_client.get("/api/v1/address")
    addresses_for_persons = (a for a in addresses.json() if a.get("person") is not None)
    user_addresses: dict[UUID, dict[str, list[Address]]] = defaultdict(
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
