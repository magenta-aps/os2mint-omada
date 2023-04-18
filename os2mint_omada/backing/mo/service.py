# SPDX-FileCopyrightText: 2021 Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

import asyncio
from contextlib import AbstractAsyncContextManager
from contextlib import AsyncExitStack
from itertools import chain
from types import TracebackType
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
from raclients.graph.client import GraphQLClient
from raclients.modelclient.mo import ModelClient as MoModelClient
from ramodels.mo import Employee
from ramodels.mo import Validity
from ramodels.mo._shared import EngagementRef
from ramodels.mo._shared import PersonRef
from ramodels.mo._shared import UUIDBase
from ramodels.mo.details import Address
from ramodels.mo.details import Engagement
from ramodels.mo.details import ITUser
from ramqp.mo import MOAMQPSystem

from os2mint_omada.config import MoSettings
from os2mint_omada.util import validity_union

logger = structlog.get_logger(__name__)

ITSystems = NewType("ITSystems", dict[str, UUID])


class MOService(AbstractAsyncContextManager):
    def __init__(self, settings: MoSettings, amqp_system: MOAMQPSystem) -> None:
        """The MO backing service manages the connection to MO's AMQP and API.

        Args:
            settings: MO-specific settings.
            amqp_system: MO AMQP System.
        """
        super().__init__()
        self.settings = settings
        self.amqp_system = amqp_system

        self.stack = AsyncExitStack()

    async def __aenter__(self) -> MOService:
        """Start clients for persistent connections to the MO API and AMQP system."""
        settings = self.settings

        # GraphQL Client
        graphql = GraphQLClient(
            url=f"{settings.url}/graphql/v3",
            **settings.auth.dict(),
            # Ridiculous timeout to support fetching all employee uuids until MO
            # supports pagination/streaming of GraphQL responses.
            httpx_client_kwargs=dict(timeout=300),
            execute_timeout=300,
        )
        self.graphql: AsyncClientSession = await self.stack.enter_async_context(graphql)

        # Model Client
        model = MoModelClient(base_url=settings.url, **settings.auth.dict())
        self.model: MoModelClient = await self.stack.enter_async_context(model)

        # The AMQP system is started last so the API clients, which are used from the
        # AMQP handlers, are ready before messages are received.
        await self.stack.enter_async_context(self.amqp_system)

        return await super().__aenter__()

    async def __aexit__(
        self,
        __exc_type: Type[BaseException] | None,
        __exc_value: BaseException | None,
        __traceback: TracebackType | None,
    ) -> bool | None:
        """Close connections to the MO API and AMQP system."""
        await self.stack.aclose()
        return await super().__aexit__(__exc_type, __exc_value, __traceback)

    async def _is_api_ready(self) -> bool:
        """Check the connection to MO's GraphQL endpoint.

        Returns: Whether the connection is ready.
        """
        query = gql(
            """
            query ReadinessQuery {
              org {
                uuid
              }
            }
            """
        )
        try:
            result = await self.graphql.execute(query)
            if result["org"]["uuid"]:
                return True
        except Exception:  # pylint: disable=broad-except
            logger.exception("Exception occurred during GraphQL healthcheck")
        return False

    async def _is_amqp_ready(self) -> bool:
        """Check the connection to MO's AMQP system.

        Returns: Whether a connection to the AMQP system is established.
        """
        return self.amqp_system.healthcheck()

    async def is_ready(self) -> bool:
        """Check the connection to MO.

        Returns: Whether the MO backing service is reachable.
        """
        return all(await asyncio.gather(self._is_api_ready(), self._is_amqp_ready()))

    async def get_it_systems(self) -> ITSystems:
        """Get IT Systems configured in MO.

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
        variables = {"user_keys": list(self.settings.it_user_map.values())}
        result = await self.graphql.execute(query, variable_values=variables)
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
        result = await self.graphql.execute(
            query,
            variable_values={
                "user_keys": [facet_user_key],
            },
        )
        classes = one(result["facets"])["classes"]
        return {c["user_key"]: UUID(c["uuid"]) for c in classes}

    async def get_employee_uuid_from_service_number(
        self, service_number: str
    ) -> UUID | None:
        """Find employee UUID by Omada service number.

        Omada users are linked to MO employees through user keys on the employee's
        engagements.

        Args:
            service_number: Service number to find employee for.

        Returns: Employee UUID if found, otherwise None.
        """
        logger.info("Getting MO employee UUID", service_number=service_number)
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
        result = await self.graphql.execute(
            query,
            variable_values={
                "user_keys": [service_number],
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
        logger.info("Getting MO employee UUID", cpr=cpr)
        query = gql(
            """
            query EmployeeCPRQuery($cpr_numbers: [CPR!]) {
              employees(cpr_numbers: $cpr_numbers, from_date: null, to_date: null) {
                uuid
              }
            }
            """
        )
        result = await self.graphql.execute(
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
        logger.info("Getting MO employee", uuid=uuid)
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
        result = await self.graphql.execute(
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
        self, uuid: UUID, address_types: Iterable[UUID]
    ) -> set[Address]:
        """Retrieve addresses related to an employee.

        Args:
            uuid: Employee UUID.
            address_types: Only retrieve the given address types, to avoid terminating
             addresses irrelevant to Omada.

        Returns: Set of addresses related to the employee.
        """
        logger.info("Getting MO addresses", employee_uuid=uuid)
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
        result = await self.graphql.execute(
            query,
            variable_values=jsonable_encoder(
                {
                    "employee_uuids": [uuid],
                    "address_types": address_types,
                }
            ),
        )
        employee = only(result["employees"])
        if employee is None:
            return set()
        addresses = chain.from_iterable(o["addresses"] for o in employee["objects"])

        def convert(address: dict) -> Address:
            """Convert GraphQL address to be RA-Models compatible."""
            address["person"] = one({PersonRef(**p) for p in address["person"]})
            address["engagement"] = only(
                {EngagementRef(**p) for p in (address.pop("engagement") or [])}
            )

            return Address.parse_obj(address)

        return {convert(address) for address in addresses}

    async def get_employee_engagements(self, uuid: UUID) -> set[Engagement]:
        """Retrieve engagements related to an employee.

        Args:
            uuid: Employee UUID.

        Returns: Set of engagements related to the employee.
        """
        logger.info("Getting MO engagements", employee_uuid=uuid)
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
        result = await self.graphql.execute(
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
        logger.info("Getting MO IT users", employee_uuid=uuid)
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
        result = await self.graphql.execute(
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
                {EngagementRef(**p) for p in (it_user.pop("engagement") or [])}
            )
            return ITUser.parse_obj(it_user)

        converted_it_users = (convert(it_user) for it_user in it_users)
        # Ideally IT users would be filtered directly in GraphQL, but it is not
        # currently supported.
        return {u for u in converted_it_users if u.itsystem.uuid in it_systems}

    async def get_all_employee_uuids(self) -> set[UUID]:
        """Retrieve a set of all employee UUIDs in MO.

        Returns: Set of MO employee UUIDs.
        """
        logger.info("Getting all MO employees")
        query = gql(
            """
            query EmployeesQuery {
              employees(from_date: null, to_date: null) {
                uuid
              }
            }
            """
        )
        result = await self.graphql.execute(query)
        employees = result["employees"]
        return {UUID(e["uuid"]) for e in employees}

    async def get_org_unit_with_it_system_user_key(self, user_key: str) -> UUID:
        """Find organisational unit with the given IT system user user_key.

        Engagements for manual Omada users are created in the organisational unit which
        has an IT system with user key equal to the 'org_unit'/'C_ORGANISATIONSKODE'
        field on the Omada user. While some org units are imported into MO with the
        UUID from the connected system, it isn't always the case, so in the general
        case we want to link the UUIDs through a special IT system on the org unit.
        Because we cannot know what this IT system is called, we don't filter on the
        name, but error if more than one is returned.

        Args:
            user_key: IT system user_key to find org unit for.

        Returns: UUID of the org unit if found, otherwise raises KeyError.
        """
        logger.info("Getting org unit with it system", user_key=user_key)
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
        result = await self.graphql.execute(
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

        Since some org units are imported into MO with special UUIDs, this check serves
        as a fallback to the omada/mo engagement linking otherwise handled by
        get_org_unit_with_it_system_user_key.

        Args:
            uuid: UUID of the org unit to look up.

        Returns: UUID of the org unit if it exists, otherwise raises KeyError.
        """
        logger.info("Getting org unit with uuid", uuid=uuid)
        query = gql(
            """
            query OrgUnitQuery($uuids: [UUID!]) {
              org_units(uuids: $uuids, from_date: null, to_date: null) {
                uuid
              }
            }
            """
        )
        result = await self.graphql.execute(
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

    async def get_org_unit_validity(self, uuid: UUID) -> Validity:
        """Get organisational unit's validity.

        Args:
            uuid: UUID of the org unit.

        Returns: The org unit's validity.
        """
        logger.info("Getting org unit validity", uuid=uuid)
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
        result = await self.graphql.execute(
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
        await self.graphql.execute(
            query,
            variable_values=jsonable_encoder(
                {
                    "uuid": obj.uuid,
                }
            ),
        )
