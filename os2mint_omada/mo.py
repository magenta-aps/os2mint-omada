# SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

from itertools import chain
from typing import Collection
from typing import Iterable
from typing import NewType
from typing import Type
from uuid import UUID

import structlog
from fastapi.encoders import jsonable_encoder
from gql import gql
from gql.client import AsyncClientSession
from more_itertools import one
from more_itertools import only
from ramodels.mo import Employee
from ramodels.mo import Validity
from ramodels.mo._shared import EngagementRef
from ramodels.mo._shared import PersonRef
from ramodels.mo._shared import UUIDBase
from ramodels.mo.details import Address
from ramodels.mo.details import Engagement
from ramodels.mo.details import ITUser

from os2mint_omada.util import validity_union

logger = structlog.get_logger(__name__)

ITSystems = NewType("ITSystems", dict[str, UUID])


class MO:
    def __init__(self, graphql_session: AsyncClientSession) -> None:
        """The MO backing service manages the connection to MO's AMQP and API.

        Args:
            graphql_session: MO GraphQL session.
        """
        self.graphql_session = graphql_session

    async def get_it_systems(self, user_keys: Collection[str]) -> ITSystems:
        """Get IT Systems configured in MO.

        Args:
            user_keys: IT systems to fetch.

        Returns: Mapping from IT system user key to UUID.
        """
        logger.debug("Getting MO IT systems")
        query = gql(
            """
            query ITSystemsQuery($user_keys: [String!]) {
              itsystems(user_keys: $user_keys) {
                uuid
                user_key
              }
            }
            """
        )
        dict().values()
        variables = {"user_keys": list(user_keys)}
        result = await self.graphql_session.execute(query, variable_values=variables)
        it_systems = result["itsystems"]
        return ITSystems({s["user_key"]: UUID(s["uuid"]) for s in it_systems})

    async def get_classes(self, facet_user_key: str) -> dict[str, UUID]:
        """Get classes for the given facet user key.

        Args:
            facet_user_key: Facet to retrieve classes for.

        Returns: Mapping from class user key to UUID.
        """
        logger.debug("Getting MO classes", facet=facet_user_key)
        query = gql(
            """
            query ClassesQuery($user_keys: [String!]) {
              facets(user_keys: $user_keys) {
                classes {
                  uuid
                  user_key
                }
              }
            }
            """
        )
        result = await self.graphql_session.execute(
            query,
            variable_values={
                "user_keys": [facet_user_key],
            },
        )
        classes = one(result["facets"])["classes"]
        return {c["user_key"]: UUID(c["uuid"]) for c in classes}

    async def get_employee_uuid_from_user_key(self, user_key: str) -> UUID | None:
        """Find employee UUID by user key.

        Omada users are linked to MO employees through user keys on the employee's
        engagements.

        Args:
            user_key: User key to find employee for.

        Returns: Employee UUID if found, otherwise None.
        """
        logger.debug("Getting MO employee UUID", user_key=user_key)
        query = gql(
            """
            query EmployeeServiceNumberQuery($user_keys: [String!]) {
              engagements(user_keys: $user_keys, from_date: null, to_date: null) {
                objects {
                  employee {
                    uuid
                  }
                }
              }
            }
            """
        )
        result = await self.graphql_session.execute(
            query,
            variable_values={
                "user_keys": [user_key],
            },
        )
        engagements = result["engagements"]
        if not engagements:
            return None
        objects = chain.from_iterable(e["objects"] for e in engagements)
        employees = chain.from_iterable(o["employee"] for o in objects)
        uuids = {e["uuid"] for e in employees}
        uuid = one(uuids)  # it's an error if different UUIDs are returned
        return UUID(uuid)

    async def get_employee_uuid_from_cpr(self, cpr: str) -> UUID | None:
        """Find employee UUID by CPR number.

        Args:
            cpr: CPR number to find employee for.

        Returns: Employee UUID if matching employee exists, otherwise None.
        """
        logger.debug("Getting MO employee UUID", cpr=cpr)
        query = gql(
            """
            query EmployeeCPRQuery($cpr_numbers: [CPR!]) {
              employees(cpr_numbers: $cpr_numbers, from_date: null, to_date: null) {
                uuid
              }
            }
            """
        )
        result = await self.graphql_session.execute(
            query,
            variable_values={
                "cpr_numbers": [cpr],
            },
        )
        employees = result["employees"]
        if not employees:
            return None
        uuids = {e["uuid"] for e in employees}
        uuid = one(uuids)  # it's an error if different UUIDs are returned
        return UUID(uuid)

    async def get_employee_states(self, uuid: UUID) -> set[Employee]:
        """Retrieve employee states.

        The retrieved fields correspond to the fields which are synchronised from
        Omada, i.e. exactly the fields we are interested in, to check up-to-dateness.

        Args:
            uuid: Employee UUID.

        Returns: Set of employee objects; one for each state.
        """
        logger.debug("Getting MO employee", uuid=uuid)
        query = gql(
            """
            query EmployeeQuery($uuids: [UUID!]) {
              employees(uuids: $uuids, from_date: null, to_date: null) {
                objects {
                  uuid
                  givenname
                  surname
                  cpr_no
                }
              }
            }
            """
        )
        result = await self.graphql_session.execute(
            query,
            variable_values=jsonable_encoder(
                {
                    "uuids": [uuid],
                }
            ),
        )
        employee = only(result["employees"])
        if employee is None:
            return set()
        return {Employee.parse_obj(o) for o in employee["objects"]}

    async def get_employee_addresses(
        self, uuid: UUID, engagement_types: Collection[UUID]
    ) -> set[Address]:
        """Retrieve addresses related to an employee.

        Args:
            uuid: Employee UUID.
            engagement_types: Only retrieve addresses for the given engagement types,
             to avoid terminating addresses irrelevant to Omada.

        Returns: Set of addresses related to the employee.
        """
        logger.debug("Getting MO addresses", employee_uuid=uuid)
        query = gql(
            """
            query AddressesQuery($employee_uuids: [UUID!], $address_types: [UUID!]) {
              employees(uuids: $employee_uuids, from_date: null, to_date: null) {
                objects {
                  addresses(address_types: $address_types) {
                    uuid
                    value
                    address_type {
                      uuid
                    }
                    person: employee {
                      uuid
                    }
                    engagement {
                      uuid
                      engagement_type {
                        uuid
                      }
                    }
                    visibility {
                      uuid
                    }
                    validity {
                      from
                      to
                    }
                  }
                }
              }
            }
            """
        )
        result = await self.graphql_session.execute(
            query,
            variable_values=jsonable_encoder(
                {
                    "employee_uuids": [uuid],
                }
            ),
        )
        employee = only(result["employees"])
        if employee is None:
            return set()
        addresses: Iterable[dict] = chain.from_iterable(
            o["addresses"] for o in employee["objects"]
        )

        def filter_engagement_type(address: dict) -> bool:
            """Filter addresses based on engagement type.

            TODO: This should be done server-side when supported by the GraphQL API.
            """
            engagements = address["engagement"]
            if engagements is None:
                return False
            engagement_type_uuids = {
                UUID(e["engagement_type"]["uuid"]) for e in engagements
            }
            return not engagement_type_uuids.isdisjoint(engagement_types)

        addresses = (a for a in addresses if filter_engagement_type(a))

        def convert(address: dict) -> Address:
            """Convert GraphQL address to be RA-Models compatible."""
            address["person"] = one({PersonRef(**p) for p in address["person"]})
            address["engagement"] = only(
                {
                    EngagementRef(uuid=e["uuid"])
                    for e in (address.pop("engagement") or {})
                }
            )

            return Address.parse_obj(address)

        return {convert(address) for address in addresses}

    async def get_employee_engagements(self, uuid: UUID) -> set[Engagement]:
        """Retrieve engagements related to an employee.

        Args:
            uuid: Employee UUID.

        Returns: Set of engagements related to the employee.
        """
        logger.debug("Getting MO engagements", employee_uuid=uuid)
        query = gql(
            """
            query EngagementsQuery($employee_uuids: [UUID!]) {
              employees(uuids: $employee_uuids, from_date: null, to_date: null) {
                objects {
                  engagements {
                    uuid
                    user_key
                    org_unit_uuid
                    person: employee {
                      uuid
                    }
                    job_function {
                      uuid
                    }
                    engagement_type {
                      uuid
                    }
                    primary {
                      uuid
                    }
                    validity {
                      from
                      to
                    }
                  }
                }
              }
            }
            """
        )
        result = await self.graphql_session.execute(
            query,
            variable_values=jsonable_encoder(
                {
                    "employee_uuids": [uuid],
                }
            ),
        )
        employee = only(result["employees"])
        if employee is None:
            return set()
        engagements = chain.from_iterable(o["engagements"] for o in employee["objects"])

        def convert(engagement: dict) -> Engagement:
            """Convert GraphQL engagement to be RA-Models compatible."""
            engagement["person"] = one({PersonRef(**p) for p in engagement["person"]})
            engagement["org_unit"] = {"uuid": engagement.pop("org_unit_uuid")}
            return Engagement.parse_obj(engagement)

        return {convert(engagement) for engagement in engagements}

    async def get_employee_it_users(
        self, uuid: UUID, it_systems: Collection[UUID]
    ) -> set[ITUser]:
        """Retrieve IT users related to an employee.

        Args:
            uuid: Employee UUID.
            it_systems: Only retrieve IT users for the given IT systems, to avoid
             terminating IT users irrelevant to Omada.

        Returns: Set of IT users related to the employee.
        """
        logger.debug("Getting MO IT users", employee_uuid=uuid)
        query = gql(
            """
            query ITUsersQuery($employee_uuids: [UUID!]) {
              employees(uuids: $employee_uuids, from_date: null, to_date: null) {
                objects {
                  itusers {
                    uuid
                    user_key
                    itsystem_uuid
                    person: employee {
                      uuid
                    }
                    engagement {
                      uuid
                    }
                    validity {
                      from
                      to
                    }
                  }
                }
              }
            }
            """
        )
        result = await self.graphql_session.execute(
            query,
            variable_values=jsonable_encoder(
                {
                    "employee_uuids": [uuid],
                }
            ),
        )
        employee = only(result["employees"])
        if employee is None:
            return set()
        it_users = chain.from_iterable(o["itusers"] for o in employee["objects"])

        def convert(it_user: dict) -> ITUser:
            """Convert GraphQL IT user to be RA-Models compatible."""
            it_user["person"] = one({PersonRef(**p) for p in it_user["person"]})
            it_user["itsystem"] = {"uuid": it_user.pop("itsystem_uuid")}
            it_user["engagement"] = only(
                {EngagementRef(**p) for p in (it_user.pop("engagement") or {})}
            )
            return ITUser.parse_obj(it_user)

        converted_it_users = (convert(it_user) for it_user in it_users)
        # Ideally IT users would be filtered directly in GraphQL, but it is not
        # currently supported.
        return {u for u in converted_it_users if u.itsystem.uuid in it_systems}

    async def get_org_unit_with_it_system_user_key(self, user_key: str) -> UUID:
        """Find organisational unit with the given IT system user user_key.

        Args:
            user_key: IT system user_key to find org unit for.

        Returns: UUID of the org unit if found, otherwise raises KeyError.
        """
        logger.debug("Getting org unit with it system", user_key=user_key)
        query = gql(
            """
            query OrgUnitITUserQuery($user_keys: [String!]) {
              itusers(user_keys: $user_keys, from_date: null, to_date: null) {
                objects {
                  org_unit_uuid
                }
              }
            }
            """
        )
        result = await self.graphql_session.execute(
            query,
            variable_values={
                "user_keys": [user_key],
            },
        )
        it_users = result["itusers"]
        if not it_users:
            raise KeyError(f"No organisation unit with {user_key=} found")
        objects = chain.from_iterable(u["objects"] for u in it_users)
        uuids = {o["org_unit_uuid"] for o in objects}
        uuid = one(uuids)  # it's an error if different UUIDs are returned
        return UUID(uuid)

    async def get_org_unit_with_uuid(self, uuid: UUID) -> UUID:
        """Get organisational unit with the given UUID, validating that it exists.

        Args:
            uuid: UUID of the org unit to look up.

        Returns: UUID of the org unit if it exists, otherwise raises KeyError.
        """
        logger.debug("Getting org unit with uuid", uuid=uuid)
        query = gql(
            """
            query OrgUnitQuery($uuids: [UUID!]) {
              org_units(uuids: $uuids, from_date: null, to_date: null) {
                uuid
              }
            }
            """
        )
        result = await self.graphql_session.execute(
            query,
            variable_values=jsonable_encoder(
                {
                    "uuids": [uuid],
                }
            ),
        )
        try:
            org_unit = one(result["org_units"])
        except ValueError as e:
            raise KeyError(f"No organisation unit with {uuid=} found") from e
        return UUID(org_unit["uuid"])

    async def get_org_unit_with_user_key(self, user_key: str) -> UUID:
        """Get organisational unit with the given user key, validating that it exists.

        Args:
            user_key: User key of the org unit to look up.

        Returns: UUID of the org unit if it exists, otherwise raises KeyError.
        """
        logger.debug("Getting org unit with user key", user_key=user_key)
        query = gql(
            """
            query OrgUnitQuery($user_keys: [String!]) {
              org_units(user_keys: $user_keys, from_date: null, to_date: null) {
                uuid
              }
            }
            """
        )
        result = await self.graphql_session.execute(
            query,
            variable_values={
                "user_keys": [user_key],
            },
        )
        try:
            org_unit = one(result["org_units"])
        except ValueError as e:
            raise KeyError(f"No organisation unit with {user_key=} found") from e
        return UUID(org_unit["uuid"])

    async def get_org_unit_validity(self, uuid: UUID) -> Validity:
        """Get organisational unit's validity.

        Args:
            uuid: UUID of the org unit.

        Returns: The org unit's validity.
        """
        logger.debug("Getting org unit validity", uuid=uuid)
        query = gql(
            """
            query OrgUnitValidityQuery($uuids: [UUID!]) {
              org_units(uuids: $uuids, from_date: null, to_date: null) {
                objects {
                  validity {
                    from_date: from
                    to_date: to
                  }
                }
              }
            }
            """
        )
        result = await self.graphql_session.execute(
            query,
            variable_values=jsonable_encoder(
                {
                    "uuids": [uuid],
                }
            ),
        )
        org_unit = one(result["org_units"])
        objs = org_unit["objects"]
        # Consolidate validities from all past/present/future versions of the org unit
        validities = (Validity(**obj["validity"]) for obj in objs)
        return validity_union(*validities)

    async def delete(self, obj: UUIDBase) -> None:
        """Delete a MO object.

        Args:
            obj: Object to delete.
        """
        logger.info("Deleting object", object=obj)
        mutators: dict[Type[UUIDBase], str] = {
            Address: "address_delete",
            Engagement: "engagement_delete",
            ITUser: "ituser_delete",
        }
        mutator = mutators[type(obj)]
        query = gql(
            f"""
            mutation DeleteMutation($uuid: UUID!) {{
              {mutator}(uuid: $uuid) {{
                uuid
              }}
            }}
            """
        )
        await self.graphql_session.execute(
            query,
            variable_values=jsonable_encoder(
                {
                    "uuid": obj.uuid,
                }
            ),
        )
