from typing import Annotated
from typing import List
from typing import Literal
from typing import Union
from uuid import UUID

from pydantic import Field

from .base_model import BaseModel


class GetEmployeeUuidFromEngagement(BaseModel):
    registrations: "GetEmployeeUuidFromEngagementRegistrations"


class GetEmployeeUuidFromEngagementRegistrations(BaseModel):
    objects: List[
        Annotated[
            Union[
                "GetEmployeeUuidFromEngagementRegistrationsObjectsIRegistration",
                "GetEmployeeUuidFromEngagementRegistrationsObjectsEngagementRegistration",
            ],
            Field(discriminator="typename__"),
        ]
    ]


class GetEmployeeUuidFromEngagementRegistrationsObjectsIRegistration(BaseModel):
    typename__: Literal[
        "AddressRegistration",
        "AssociationRegistration",
        "ClassRegistration",
        "FacetRegistration",
        "IRegistration",
        "ITSystemRegistration",
        "ITUserRegistration",
        "KLERegistration",
        "LeaveRegistration",
        "ManagerRegistration",
        "OrganisationUnitRegistration",
        "OwnerRegistration",
        "PersonRegistration",
        "RelatedUnitRegistration",
        "RoleBindingRegistration",
    ] = Field(alias="__typename")


class GetEmployeeUuidFromEngagementRegistrationsObjectsEngagementRegistration(
    BaseModel
):
    typename__: Literal["EngagementRegistration"] = Field(alias="__typename")
    validities: List[
        "GetEmployeeUuidFromEngagementRegistrationsObjectsEngagementRegistrationValidities"
    ]


class GetEmployeeUuidFromEngagementRegistrationsObjectsEngagementRegistrationValidities(
    BaseModel
):
    person_response: "GetEmployeeUuidFromEngagementRegistrationsObjectsEngagementRegistrationValiditiesPersonResponse"


class GetEmployeeUuidFromEngagementRegistrationsObjectsEngagementRegistrationValiditiesPersonResponse(
    BaseModel
):
    uuid: UUID


GetEmployeeUuidFromEngagement.update_forward_refs()
GetEmployeeUuidFromEngagementRegistrations.update_forward_refs()
GetEmployeeUuidFromEngagementRegistrationsObjectsIRegistration.update_forward_refs()
GetEmployeeUuidFromEngagementRegistrationsObjectsEngagementRegistration.update_forward_refs()
GetEmployeeUuidFromEngagementRegistrationsObjectsEngagementRegistrationValidities.update_forward_refs()
GetEmployeeUuidFromEngagementRegistrationsObjectsEngagementRegistrationValiditiesPersonResponse.update_forward_refs()
