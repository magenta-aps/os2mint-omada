# Generated by ariadne-codegen on 2024-01-23 19:00
# Source: queries.graphql
from typing import Any
from typing import Optional
from typing import Union
from uuid import UUID

from ._testing__create_employee import TestingCreateEmployee
from ._testing__create_employee import TestingCreateEmployeeEmployeeCreate
from ._testing__create_org_unit import TestingCreateOrgUnit
from ._testing__create_org_unit import TestingCreateOrgUnitOrgUnitCreate
from ._testing__create_org_unit_it_user import TestingCreateOrgUnitItUser
from ._testing__create_org_unit_it_user import TestingCreateOrgUnitItUserItuserCreate
from ._testing__get_employee import TestingGetEmployee
from ._testing__get_employee import TestingGetEmployeeEmployees
from ._testing__get_it_system import TestingGetItSystem
from ._testing__get_it_system import TestingGetItSystemItsystems
from ._testing__get_org_unit_type import TestingGetOrgUnitType
from ._testing__get_org_unit_type import TestingGetOrgUnitTypeClasses
from .async_base_client import AsyncBaseClient
from .base_model import UNSET
from .base_model import UnsetType


def gql(q: str) -> str:
    return q


class GraphQLClient(AsyncBaseClient):
    async def _testing__get_employee(
        self, cpr_number: Any
    ) -> TestingGetEmployeeEmployees:
        query = gql(
            """
            query _Testing_GetEmployee($cpr_number: CPR!) {
              employees(filter: {cpr_numbers: [$cpr_number], from_date: null, to_date: null}) {
                objects {
                  objects {
                    cpr_number
                    given_name
                    surname
                    nickname_given_name
                    nickname_surname
                    validity {
                      from
                      to
                    }
                    engagements(filter: {from_date: null, to_date: null}) {
                      user_key
                      org_unit(filter: {from_date: null, to_date: null}) {
                        user_key
                      }
                      job_function(filter: {from_date: null, to_date: null}) {
                        user_key
                      }
                      engagement_type(filter: {from_date: null, to_date: null}) {
                        user_key
                      }
                      primary(filter: {from_date: null, to_date: null}) {
                        user_key
                      }
                      validity {
                        from
                        to
                      }
                    }
                    addresses(filter: {from_date: null, to_date: null}) {
                      value
                      address_type(filter: {from_date: null, to_date: null}) {
                        user_key
                      }
                      engagement(filter: {from_date: null, to_date: null}) {
                        user_key
                      }
                      visibility(filter: {from_date: null, to_date: null}) {
                        user_key
                      }
                      validity {
                        from
                        to
                      }
                    }
                    itusers(filter: {from_date: null, to_date: null}) {
                      user_key
                      itsystem(filter: {from_date: null, to_date: null}) {
                        user_key
                      }
                      engagement(filter: {from_date: null, to_date: null}) {
                        user_key
                      }
                      validity {
                        from
                        to
                      }
                    }
                  }
                }
              }
            }
            """
        )
        variables: dict[str, object] = {"cpr_number": cpr_number}
        response = await self.execute(query=query, variables=variables)
        data = self.get_data(response)
        return TestingGetEmployee.parse_obj(data).employees

    async def _testing__create_employee(
        self,
        cpr_number: Any,
        given_name: str,
        surname: str,
        nickname_given_name: Union[Optional[str], UnsetType] = UNSET,
        nickname_surname: Union[Optional[str], UnsetType] = UNSET,
    ) -> TestingCreateEmployeeEmployeeCreate:
        query = gql(
            """
            mutation _Testing_CreateEmployee($cpr_number: CPR!, $given_name: String!, $surname: String!, $nickname_given_name: String = null, $nickname_surname: String = null) {
              employee_create(
                input: {cpr_number: $cpr_number, given_name: $given_name, surname: $surname, nickname_given_name: $nickname_given_name, nickname_surname: $nickname_surname}
              ) {
                uuid
              }
            }
            """
        )
        variables: dict[str, object] = {
            "cpr_number": cpr_number,
            "given_name": given_name,
            "surname": surname,
            "nickname_given_name": nickname_given_name,
            "nickname_surname": nickname_surname,
        }
        response = await self.execute(query=query, variables=variables)
        data = self.get_data(response)
        return TestingCreateEmployee.parse_obj(data).employee_create

    async def _testing__get_org_unit_type(self) -> TestingGetOrgUnitTypeClasses:
        query = gql(
            """
            query _Testing_GetOrgUnitType {
              classes(filter: {facet_user_keys: "org_unit_type", user_keys: "Afdeling"}) {
                objects {
                  uuid
                }
              }
            }
            """
        )
        variables: dict[str, object] = {}
        response = await self.execute(query=query, variables=variables)
        data = self.get_data(response)
        return TestingGetOrgUnitType.parse_obj(data).classes

    async def _testing__create_org_unit(
        self, user_key: str, org_unit_type: UUID
    ) -> TestingCreateOrgUnitOrgUnitCreate:
        query = gql(
            """
            mutation _Testing_CreateOrgUnit($user_key: String!, $org_unit_type: UUID!) {
              org_unit_create(
                input: {name: "Test Org Unit", user_key: $user_key, org_unit_type: $org_unit_type, validity: {from: "2010-02-03"}}
              ) {
                uuid
              }
            }
            """
        )
        variables: dict[str, object] = {
            "user_key": user_key,
            "org_unit_type": org_unit_type,
        }
        response = await self.execute(query=query, variables=variables)
        data = self.get_data(response)
        return TestingCreateOrgUnit.parse_obj(data).org_unit_create

    async def _testing__get_it_system(
        self, user_key: str
    ) -> TestingGetItSystemItsystems:
        query = gql(
            """
            query _Testing_GetItSystem($user_key: String!) {
              itsystems(filter: {user_keys: [$user_key]}) {
                objects {
                  uuid
                }
              }
            }
            """
        )
        variables: dict[str, object] = {"user_key": user_key}
        response = await self.execute(query=query, variables=variables)
        data = self.get_data(response)
        return TestingGetItSystem.parse_obj(data).itsystems

    async def _testing__create_org_unit_it_user(
        self, user_key: str, it_system: UUID, org_unit: UUID
    ) -> TestingCreateOrgUnitItUserItuserCreate:
        query = gql(
            """
            mutation _Testing_CreateOrgUnitItUser($user_key: String!, $it_system: UUID!, $org_unit: UUID!) {
              ituser_create(
                input: {user_key: $user_key, itsystem: $it_system, org_unit: $org_unit, validity: {from: "2010-02-03"}}
              ) {
                uuid
              }
            }
            """
        )
        variables: dict[str, object] = {
            "user_key": user_key,
            "it_system": it_system,
            "org_unit": org_unit,
        }
        response = await self.execute(query=query, variables=variables)
        data = self.get_data(response)
        return TestingCreateOrgUnitItUser.parse_obj(data).ituser_create
