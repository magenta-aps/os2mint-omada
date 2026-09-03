from typing import List
from typing import Optional
from uuid import UUID

from .base_model import BaseModel


class GetEmployeeUuidFromItuser(BaseModel):
    itusers: "GetEmployeeUuidFromItuserItusers"


class GetEmployeeUuidFromItuserItusers(BaseModel):
    objects: List["GetEmployeeUuidFromItuserItusersObjects"]


class GetEmployeeUuidFromItuserItusersObjects(BaseModel):
    validities: List["GetEmployeeUuidFromItuserItusersObjectsValidities"]


class GetEmployeeUuidFromItuserItusersObjectsValidities(BaseModel):
    person: Optional[List["GetEmployeeUuidFromItuserItusersObjectsValiditiesPerson"]]


class GetEmployeeUuidFromItuserItusersObjectsValiditiesPerson(BaseModel):
    uuid: UUID


GetEmployeeUuidFromItuser.update_forward_refs()
GetEmployeeUuidFromItuserItusers.update_forward_refs()
GetEmployeeUuidFromItuserItusersObjects.update_forward_refs()
GetEmployeeUuidFromItuserItusersObjectsValidities.update_forward_refs()
GetEmployeeUuidFromItuserItusersObjectsValiditiesPerson.update_forward_refs()
