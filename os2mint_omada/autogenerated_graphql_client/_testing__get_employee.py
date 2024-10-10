# Generated by ariadne-codegen on 2024-10-10 13:36
# Source: queries.graphql

from datetime import datetime
from typing import Any
from typing import List
from typing import Optional

from pydantic import Field

from .base_model import BaseModel


class TestingGetEmployee(BaseModel):
    employees: "TestingGetEmployeeEmployees"


class TestingGetEmployeeEmployees(BaseModel):
    objects: List["TestingGetEmployeeEmployeesObjects"]


class TestingGetEmployeeEmployeesObjects(BaseModel):
    validities: List["TestingGetEmployeeEmployeesObjectsValidities"]


class TestingGetEmployeeEmployeesObjectsValidities(BaseModel):
    cpr_number: Optional[Any]
    given_name: str
    surname: str
    nickname_given_name: Optional[str]
    nickname_surname: Optional[str]
    validity: "TestingGetEmployeeEmployeesObjectsValiditiesValidity"
    engagements: List["TestingGetEmployeeEmployeesObjectsValiditiesEngagements"]
    addresses: List["TestingGetEmployeeEmployeesObjectsValiditiesAddresses"]
    itusers: List["TestingGetEmployeeEmployeesObjectsValiditiesItusers"]


class TestingGetEmployeeEmployeesObjectsValiditiesValidity(BaseModel):
    from_: Optional[datetime] = Field(alias="from")
    to: Optional[datetime]


class TestingGetEmployeeEmployeesObjectsValiditiesEngagements(BaseModel):
    user_key: str
    org_unit: List["TestingGetEmployeeEmployeesObjectsValiditiesEngagementsOrgUnit"]
    job_function: "TestingGetEmployeeEmployeesObjectsValiditiesEngagementsJobFunction"
    engagement_type: (
        "TestingGetEmployeeEmployeesObjectsValiditiesEngagementsEngagementType"
    )
    primary: Optional["TestingGetEmployeeEmployeesObjectsValiditiesEngagementsPrimary"]
    validity: "TestingGetEmployeeEmployeesObjectsValiditiesEngagementsValidity"


class TestingGetEmployeeEmployeesObjectsValiditiesEngagementsOrgUnit(BaseModel):
    user_key: str


class TestingGetEmployeeEmployeesObjectsValiditiesEngagementsJobFunction(BaseModel):
    user_key: str


class TestingGetEmployeeEmployeesObjectsValiditiesEngagementsEngagementType(BaseModel):
    user_key: str


class TestingGetEmployeeEmployeesObjectsValiditiesEngagementsPrimary(BaseModel):
    user_key: str


class TestingGetEmployeeEmployeesObjectsValiditiesEngagementsValidity(BaseModel):
    from_: datetime = Field(alias="from")
    to: Optional[datetime]


class TestingGetEmployeeEmployeesObjectsValiditiesAddresses(BaseModel):
    value: str
    address_type: "TestingGetEmployeeEmployeesObjectsValiditiesAddressesAddressType"
    engagement: Optional[
        List["TestingGetEmployeeEmployeesObjectsValiditiesAddressesEngagement"]
    ]
    ituser: List["TestingGetEmployeeEmployeesObjectsValiditiesAddressesItuser"]
    visibility: Optional[
        "TestingGetEmployeeEmployeesObjectsValiditiesAddressesVisibility"
    ]
    validity: "TestingGetEmployeeEmployeesObjectsValiditiesAddressesValidity"


class TestingGetEmployeeEmployeesObjectsValiditiesAddressesAddressType(BaseModel):
    user_key: str


class TestingGetEmployeeEmployeesObjectsValiditiesAddressesEngagement(BaseModel):
    user_key: str


class TestingGetEmployeeEmployeesObjectsValiditiesAddressesItuser(BaseModel):
    user_key: str


class TestingGetEmployeeEmployeesObjectsValiditiesAddressesVisibility(BaseModel):
    user_key: str


class TestingGetEmployeeEmployeesObjectsValiditiesAddressesValidity(BaseModel):
    from_: datetime = Field(alias="from")
    to: Optional[datetime]


class TestingGetEmployeeEmployeesObjectsValiditiesItusers(BaseModel):
    external_id: Optional[str]
    user_key: str
    itsystem: "TestingGetEmployeeEmployeesObjectsValiditiesItusersItsystem"
    engagement: Optional[
        List["TestingGetEmployeeEmployeesObjectsValiditiesItusersEngagement"]
    ]
    validity: "TestingGetEmployeeEmployeesObjectsValiditiesItusersValidity"


class TestingGetEmployeeEmployeesObjectsValiditiesItusersItsystem(BaseModel):
    user_key: str


class TestingGetEmployeeEmployeesObjectsValiditiesItusersEngagement(BaseModel):
    user_key: str


class TestingGetEmployeeEmployeesObjectsValiditiesItusersValidity(BaseModel):
    from_: datetime = Field(alias="from")
    to: Optional[datetime]


TestingGetEmployee.update_forward_refs()
TestingGetEmployeeEmployees.update_forward_refs()
TestingGetEmployeeEmployeesObjects.update_forward_refs()
TestingGetEmployeeEmployeesObjectsValidities.update_forward_refs()
TestingGetEmployeeEmployeesObjectsValiditiesValidity.update_forward_refs()
TestingGetEmployeeEmployeesObjectsValiditiesEngagements.update_forward_refs()
TestingGetEmployeeEmployeesObjectsValiditiesEngagementsOrgUnit.update_forward_refs()
TestingGetEmployeeEmployeesObjectsValiditiesEngagementsJobFunction.update_forward_refs()
TestingGetEmployeeEmployeesObjectsValiditiesEngagementsEngagementType.update_forward_refs()
TestingGetEmployeeEmployeesObjectsValiditiesEngagementsPrimary.update_forward_refs()
TestingGetEmployeeEmployeesObjectsValiditiesEngagementsValidity.update_forward_refs()
TestingGetEmployeeEmployeesObjectsValiditiesAddresses.update_forward_refs()
TestingGetEmployeeEmployeesObjectsValiditiesAddressesAddressType.update_forward_refs()
TestingGetEmployeeEmployeesObjectsValiditiesAddressesEngagement.update_forward_refs()
TestingGetEmployeeEmployeesObjectsValiditiesAddressesItuser.update_forward_refs()
TestingGetEmployeeEmployeesObjectsValiditiesAddressesVisibility.update_forward_refs()
TestingGetEmployeeEmployeesObjectsValiditiesAddressesValidity.update_forward_refs()
TestingGetEmployeeEmployeesObjectsValiditiesItusers.update_forward_refs()
TestingGetEmployeeEmployeesObjectsValiditiesItusersItsystem.update_forward_refs()
TestingGetEmployeeEmployeesObjectsValiditiesItusersEngagement.update_forward_refs()
TestingGetEmployeeEmployeesObjectsValiditiesItusersValidity.update_forward_refs()
