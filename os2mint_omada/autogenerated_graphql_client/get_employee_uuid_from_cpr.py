from typing import List
from uuid import UUID

from .base_model import BaseModel


class GetEmployeeUuidFromCpr(BaseModel):
    employees: "GetEmployeeUuidFromCprEmployees"


class GetEmployeeUuidFromCprEmployees(BaseModel):
    objects: List["GetEmployeeUuidFromCprEmployeesObjects"]


class GetEmployeeUuidFromCprEmployeesObjects(BaseModel):
    uuid: UUID


GetEmployeeUuidFromCpr.update_forward_refs()
GetEmployeeUuidFromCprEmployees.update_forward_refs()
GetEmployeeUuidFromCprEmployeesObjects.update_forward_refs()
