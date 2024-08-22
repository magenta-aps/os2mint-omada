# Generated by ariadne-codegen on 2024-08-22 17:44
# Source: queries.graphql

from typing import List
from typing import Optional
from uuid import UUID

from .base_model import BaseModel


class GetItSystems(BaseModel):
    itsystems: "GetItSystemsItsystems"


class GetItSystemsItsystems(BaseModel):
    objects: List["GetItSystemsItsystemsObjects"]


class GetItSystemsItsystemsObjects(BaseModel):
    current: Optional["GetItSystemsItsystemsObjectsCurrent"]


class GetItSystemsItsystemsObjectsCurrent(BaseModel):
    uuid: UUID
    user_key: str


GetItSystems.update_forward_refs()
GetItSystemsItsystems.update_forward_refs()
GetItSystemsItsystemsObjects.update_forward_refs()
GetItSystemsItsystemsObjectsCurrent.update_forward_refs()
