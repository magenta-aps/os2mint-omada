# SPDX-FileCopyrightText: 2021 Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

import asyncio
from contextlib import AbstractAsyncContextManager
from contextlib import AsyncExitStack
from types import TracebackType
from typing import Collection
from typing import Iterable
from typing import NewType
from typing import Type
from uuid import UUID

import structlog
from gql import gql
from gql.client import AsyncClientSession
from more_itertools import one
from raclients.auth import AuthenticatedAsyncHTTPXClient
from raclients.graph.client import GraphQLClient
from raclients.modelclient.mo import ModelClient as MoModelClient
from ramodels.mo import Employee
from ramqp.mo import MOAMQPSystem

from os2mint_omada.backing.mo.models import MOEmployee
from os2mint_omada.config import MoSettings

logger = structlog.get_logger(__name__)

ITSystems = NewType("ITSystems", dict[str, UUID])


class MOService(AbstractAsyncContextManager):
    def __init__(self, settings: MoSettings, amqp_system: MOAMQPSystem) -> None:
        super().__init__()
        self.settings = settings
        self.amqp_system = amqp_system

        self.stack = AsyncExitStack()

    async def __aenter__(self) -> MOService:
        settings = self.settings
        client_kwargs = dict(
            client_id=settings.client_id,
            client_secret=settings.client_secret.get_secret_value(),
            auth_realm=settings.auth_realm,
            auth_server=settings.auth_server,
        )

        # GraphQL Client
        graphql = GraphQLClient(url=f"{settings.url}/graphql", **client_kwargs)
        self.graphql: AsyncClientSession = await self.stack.enter_async_context(graphql)

        # Model Client
        model = MoModelClient(base_url=settings.url, **client_kwargs)
        self.model: MoModelClient = await self.stack.enter_async_context(model)

        # HTTPX Client
        client = AuthenticatedAsyncHTTPXClient(base_url=settings.url, **client_kwargs)
        self.client: AsyncClientSession = await self.stack.enter_async_context(client)

        # AMQP
        await self.stack.enter_async_context(self.amqp_system)

        return await super().__aenter__()

    async def __aexit__(
        self,
        __exc_type: Type[BaseException] | None,
        __exc_value: BaseException | None,
        __traceback: TracebackType | None,
    ) -> bool | None:
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
        logger.info("Getting MO employee UUID", service_number=service_number)
        query = gql(
            """
            query EmployeeCPRQuery($user_keys: [String!]) {
              engagements(user_keys: $user_keys) {
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
        try:
            engagement = one(result["engagements"])
        except ValueError:
            return None
        obj = one(engagement["objects"])
        employee = one(obj["employee"])
        return UUID(employee["uuid"])

    async def get_employee_uuid_from_cpr(self, cpr: str) -> UUID | None:
        logger.info("Getting MO employee UUID", cpr=cpr)
        query = gql(
            """
            query EmployeeCPRQuery($cpr_numbers: [CPR!]) {
              employees(cpr_numbers: $cpr_numbers) {
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
        try:
            employee = one(result["employees"])
        except ValueError:
            return None
        return UUID(employee["uuid"])

    async def get_employee(self, uuid: UUID) -> Employee | None:
        logger.info("Getting MO employee", uuid=uuid)
        query = gql(
            """
            query EmployeeQuery($uuids: [UUID!]) {
              employees(uuids: $uuids) {
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
            variable_values={
                # UUIDs are not JSON serializable, so they are converted to strings
                "uuids": [str(uuid)],
            },
        )
        try:
            employee_dict = one(result["employees"])
        except ValueError:
            return None
        obj = one(employee_dict["objects"])
        return Employee.parse_obj(obj)

    async def get_employee_data(
        self,
        uuid: UUID,
        address_types: Iterable[UUID],
        it_systems: Collection[UUID],
    ) -> MOEmployee | None:
        logger.info("Getting MO employee data", uuid=uuid)
        query = gql(
            """
            query EmployeeDataQuery($uuids: [UUID!], $address_types: [UUID!]) {
              employees(uuids: $uuids) {
                objects {
                  uuid
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
                  addresses(address_types: $address_types) {
                    uuid
                    value
                    address_type {
                      uuid
                    }
                    person: employee {
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
                  itusers {
                    uuid
                    user_key
                    itsystem_uuid
                    person: employee {
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
            variable_values={
                # UUIDs are not JSON serializable, so they are converted to strings
                "uuids": [str(uuid)],
                "address_types": [str(u) for u in address_types],
            },
        )
        try:
            employee_dict = one(result["employees"])
        except ValueError:
            return None
        obj = one(employee_dict["objects"])
        employee = MOEmployee.parse_obj(obj)
        # Filter IT users. Ideally this would be done directly in GraphQL, but it is
        # not currently supported.
        for it_user in employee.itusers.copy():
            if it_user.itsystem.uuid not in it_systems:
                employee.itusers.remove(it_user)
        return employee

    async def get_org_unit_with_it_system_user_key(self, user_key: str) -> UUID:
        logger.info("Getting org unit with it system", user_key=user_key)
        query = gql(
            """
            query OrgUnitITUserQuery($user_keys: [String!]) {
              itusers(user_keys: $user_keys) {
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
        try:
            it_users = one(result["itusers"])
        except ValueError as e:
            raise KeyError from e
        obj = one(it_users["objects"])
        return UUID(obj["org_unit_uuid"])

    async def get_org_unit_with_uuid(self, uuid: UUID) -> UUID:
        logger.info("Getting org unit with uuid", uuid=uuid)
        query = gql(
            """
            query OrgUnitQuery($uuids: [UUID!]) {
              org_units(uuids: $uuids) {
                uuid
              }
            }
            """
        )
        result = await self.graphql.execute(
            query,
            variable_values={
                # UUIDs are not JSON serializable, so they are converted to strings
                "uuids": [str(uuid)],
            },
        )
        try:
            org_unit = one(result["org_units"])
        except ValueError as e:
            raise KeyError from e
        return UUID(org_unit["uuid"])
