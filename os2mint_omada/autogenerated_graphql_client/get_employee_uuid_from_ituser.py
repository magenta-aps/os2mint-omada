from typing import Annotated
from typing import List
from typing import Literal
from typing import Optional
from typing import Union
from uuid import UUID

from pydantic import Field

from .base_model import BaseModel


class GetEmployeeUuidFromItuser(BaseModel):
    registrations: "GetEmployeeUuidFromItuserRegistrations"


class GetEmployeeUuidFromItuserRegistrations(BaseModel):
    objects: List[
        Annotated[
            Union[
                "GetEmployeeUuidFromItuserRegistrationsObjectsIRegistration",
                "GetEmployeeUuidFromItuserRegistrationsObjectsITUserRegistration",
            ],
            Field(discriminator="typename__"),
        ]
    ]


class GetEmployeeUuidFromItuserRegistrationsObjectsIRegistration(BaseModel):
    typename__: Literal[
        "AddressRegistration",
        "AssociationRegistration",
        "ClassRegistration",
        "EngagementRegistration",
        "FacetRegistration",
        "IRegistration",
        "ITSystemRegistration",
        "KLERegistration",
        "LeaveRegistration",
        "ManagerRegistration",
        "OrganisationUnitRegistration",
        "OwnerRegistration",
        "PersonRegistration",
        "RelatedUnitRegistration",
        "RoleBindingRegistration",
    ] = Field(alias="__typename")


class GetEmployeeUuidFromItuserRegistrationsObjectsITUserRegistration(BaseModel):
    typename__: Literal["ITUserRegistration"] = Field(alias="__typename")
    validities: List[
        "GetEmployeeUuidFromItuserRegistrationsObjectsITUserRegistrationValidities"
    ]


class GetEmployeeUuidFromItuserRegistrationsObjectsITUserRegistrationValidities(
    BaseModel
):
    person_response: Optional[
        "GetEmployeeUuidFromItuserRegistrationsObjectsITUserRegistrationValiditiesPersonResponse"
    ]


class GetEmployeeUuidFromItuserRegistrationsObjectsITUserRegistrationValiditiesPersonResponse(
    BaseModel
):
    uuid: UUID


GetEmployeeUuidFromItuser.update_forward_refs()
GetEmployeeUuidFromItuserRegistrations.update_forward_refs()
GetEmployeeUuidFromItuserRegistrationsObjectsIRegistration.update_forward_refs()
GetEmployeeUuidFromItuserRegistrationsObjectsITUserRegistration.update_forward_refs()
GetEmployeeUuidFromItuserRegistrationsObjectsITUserRegistrationValidities.update_forward_refs()
GetEmployeeUuidFromItuserRegistrationsObjectsITUserRegistrationValiditiesPersonResponse.update_forward_refs()
