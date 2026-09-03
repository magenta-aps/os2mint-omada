from typing import List
from uuid import UUID

from .base_model import BaseModel


class GetEmployeeUuidFromEngagement(BaseModel):
    engagements: "GetEmployeeUuidFromEngagementEngagements"


class GetEmployeeUuidFromEngagementEngagements(BaseModel):
    objects: List["GetEmployeeUuidFromEngagementEngagementsObjects"]


class GetEmployeeUuidFromEngagementEngagementsObjects(BaseModel):
    validities: List["GetEmployeeUuidFromEngagementEngagementsObjectsValidities"]


class GetEmployeeUuidFromEngagementEngagementsObjectsValidities(BaseModel):
    person: List["GetEmployeeUuidFromEngagementEngagementsObjectsValiditiesPerson"]


class GetEmployeeUuidFromEngagementEngagementsObjectsValiditiesPerson(BaseModel):
    uuid: UUID


GetEmployeeUuidFromEngagement.update_forward_refs()
GetEmployeeUuidFromEngagementEngagements.update_forward_refs()
GetEmployeeUuidFromEngagementEngagementsObjects.update_forward_refs()
GetEmployeeUuidFromEngagementEngagementsObjectsValidities.update_forward_refs()
GetEmployeeUuidFromEngagementEngagementsObjectsValiditiesPerson.update_forward_refs()
