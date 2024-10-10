# Generated by ariadne-codegen on 2024-10-10 13:36
# Source: queries.graphql

from typing import Any
from typing import List
from typing import Optional
from uuid import UUID

from .base_model import BaseModel


class GetCurrentEmployeeState(BaseModel):
    employees: "GetCurrentEmployeeStateEmployees"


class GetCurrentEmployeeStateEmployees(BaseModel):
    objects: List["GetCurrentEmployeeStateEmployeesObjects"]


class GetCurrentEmployeeStateEmployeesObjects(BaseModel):
    current: Optional["GetCurrentEmployeeStateEmployeesObjectsCurrent"]


class GetCurrentEmployeeStateEmployeesObjectsCurrent(BaseModel):
    uuid: UUID
    given_name: str
    surname: str
    nickname_given_name: Optional[str]
    nickname_surname: Optional[str]
    cpr_number: Optional[Any]
    seniority: Optional[Any]


GetCurrentEmployeeState.update_forward_refs()
GetCurrentEmployeeStateEmployees.update_forward_refs()
GetCurrentEmployeeStateEmployeesObjects.update_forward_refs()
GetCurrentEmployeeStateEmployeesObjectsCurrent.update_forward_refs()
