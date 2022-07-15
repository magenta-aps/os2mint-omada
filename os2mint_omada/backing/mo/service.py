# SPDX-FileCopyrightText: 2021 Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

import asyncio
from contextlib import AbstractAsyncContextManager
from contextlib import AsyncExitStack
from datetime import datetime
from datetime import timedelta
from types import TracebackType
from typing import Collection
from typing import Iterable
from typing import NewType
from typing import Type
from typing import TypeVar
from uuid import UUID

import structlog
from gql import gql
from gql.client import AsyncClientSession
from more_itertools import one
from raclients.graph.client import GraphQLClient
from raclients.modelclient.mo import ModelClient as MoModelClient
from ramodels.mo import Employee
from ramodels.mo.details import Address
from ramodels.mo.details import Engagement
from ramodels.mo.details import ITUser
from ramqp.mo import MOAMQPSystem

from os2mint_omada.backing.mo.models import EmployeeData
from os2mint_omada.config import MoSettings
from os2mint_omada.util import midnight

logger = structlog.get_logger(__name__)

ITSystems = NewType("ITSystems", dict[str, UUID])
MOBaseWithValidity = TypeVar("MOBaseWithValidity", Address, Engagement, ITUser)


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
        """Find employee UUID by CPR number.

        Args:
            cpr: CPR number to find employee for.

        Returns: Employee UUID if matching employee exists, otherwise None.
        """
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
        """Retrieve employee.

        The retrieved fields correspond to the fields which are synchronised from
        Omada, i.e. exactly the fields we are interested in, to check up-to-dateness.

        Args:
            uuid: Employee UUID.

        Returns: Employee if one exists, otherwise None.
        """
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
    ) -> EmployeeData | None:
        """Retrieve data related to an employee.

        The fields on each retrieved object corresponds to the fields necessary to
        upload it back to the MO service API (with changes) through the model client.

        Args:
            uuid: Employee UUID.
            address_types: Only retrieve the given address types, to avoid terminating
             addresses irrelevant to Omada.
            it_systems: Only retrieve IT users for the given IT systems, to avoid
             terminating IT users irrelevant to Omada.

        Returns: EmployeeData object, containing the parsed GraphQL result if the
         employee exists, otherwise None.
        """
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
        employee_data = EmployeeData.parse_obj(obj)
        # Filter IT users. Ideally this would be done directly in GraphQL, but it is
        # not currently supported.
        for it_user in employee_data.itusers.copy():
            if it_user.itsystem.uuid not in it_systems:
                employee_data.itusers.remove(it_user)
        return employee_data

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
        """Get organisational unit with the given UUID, validating that it exists.

        Since some org units are imported into MO with special UUIDs, this check serves
        as a fallback to the omada/mo engagement linking otherwise handled by
        get_org_unit_with_it_system_user_key.

        Args:
            uuid: UUID of the org unit to look up.

        Returns: UUID of the org unit if it exists, otherwise raises KeyError.
        """
        logger.info("Getting org unit with uuid", uuid=uuid)
        # TODO: (#51523) The GraphQL API always returns an org unit (albeit with empty
        #  `objects`) when querying uuids.
        query = gql(
            """
            query OrgUnitQuery($uuids: [UUID!]) {
              org_units(uuids: $uuids) {
                objects {
                  uuid
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
            org_unit = one(result["org_units"])
            obj = one(org_unit["objects"])
        except ValueError as e:
            raise KeyError from e
        return UUID(obj["uuid"])

    async def terminate(
        self, model: MOBaseWithValidity, from_date: datetime | None = None
    ) -> None:
        """Terminate a MO object.

        Args:
            model: Object to terminate.
            from_date: Termination date. If not given, today will be used.

        Notes:
            TODO: Yesterday is currently used pending fix of OS2mo bug #51539.

        Returns: None.
        """
        if from_date is None:
            from_date = midnight() - timedelta(days=1)  # TODO #51539
        logger.info("Terminating object", object=model, from_date=from_date)
        await self.model.post(
            "/service/details/terminate",
            json=dict(
                type=model.type_,
                uuid=model.uuid,
                validity={"to": from_date},
            ),
        )
