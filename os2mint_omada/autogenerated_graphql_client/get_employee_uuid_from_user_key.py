# Generated by ariadne-codegen on 2024-08-21 16:34
# Source: queries.graphql

from typing import List
from uuid import UUID

from .base_model import BaseModel


class GetEmployeeUuidFromUserKey(BaseModel):
    engagements: "GetEmployeeUuidFromUserKeyEngagements"


class GetEmployeeUuidFromUserKeyEngagements(BaseModel):
    objects: List["GetEmployeeUuidFromUserKeyEngagementsObjects"]


class GetEmployeeUuidFromUserKeyEngagementsObjects(BaseModel):
    objects: List["GetEmployeeUuidFromUserKeyEngagementsObjectsObjects"]


class GetEmployeeUuidFromUserKeyEngagementsObjectsObjects(BaseModel):
    person: List["GetEmployeeUuidFromUserKeyEngagementsObjectsObjectsPerson"]


class GetEmployeeUuidFromUserKeyEngagementsObjectsObjectsPerson(BaseModel):
    uuid: UUID


GetEmployeeUuidFromUserKey.update_forward_refs()
GetEmployeeUuidFromUserKeyEngagements.update_forward_refs()
GetEmployeeUuidFromUserKeyEngagementsObjects.update_forward_refs()
GetEmployeeUuidFromUserKeyEngagementsObjectsObjects.update_forward_refs()
GetEmployeeUuidFromUserKeyEngagementsObjectsObjectsPerson.update_forward_refs()
