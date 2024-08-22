# Generated by ariadne-codegen on 2024-08-22 17:44
# Source: queries.graphql

from typing import Any
from typing import List
from typing import Optional
from uuid import UUID

from .base_model import BaseModel


class GetEmployeeStates(BaseModel):
    employees: "GetEmployeeStatesEmployees"


class GetEmployeeStatesEmployees(BaseModel):
    objects: List["GetEmployeeStatesEmployeesObjects"]


class GetEmployeeStatesEmployeesObjects(BaseModel):
    objects: List["GetEmployeeStatesEmployeesObjectsObjects"]


class GetEmployeeStatesEmployeesObjectsObjects(BaseModel):
    uuid: UUID
    givenname: str
    surname: str
    nickname_givenname: Optional[str]
    nickname_surname: Optional[str]
    cpr_no: Optional[Any]


GetEmployeeStates.update_forward_refs()
GetEmployeeStatesEmployees.update_forward_refs()
GetEmployeeStatesEmployeesObjects.update_forward_refs()
GetEmployeeStatesEmployeesObjectsObjects.update_forward_refs()
