# Generated by ariadne-codegen on 2024-01-23 19:00
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
    objects: List["TestingGetEmployeeEmployeesObjectsObjects"]


class TestingGetEmployeeEmployeesObjectsObjects(BaseModel):
    cpr_number: Optional[Any]
    given_name: str
    surname: str
    nickname_given_name: Optional[str]
    nickname_surname: Optional[str]
    validity: "TestingGetEmployeeEmployeesObjectsObjectsValidity"
    engagements: List["TestingGetEmployeeEmployeesObjectsObjectsEngagements"]
    addresses: List["TestingGetEmployeeEmployeesObjectsObjectsAddresses"]
    itusers: List["TestingGetEmployeeEmployeesObjectsObjectsItusers"]


class TestingGetEmployeeEmployeesObjectsObjectsValidity(BaseModel):
    from_: Optional[datetime] = Field(alias="from")
    to: Optional[datetime]


class TestingGetEmployeeEmployeesObjectsObjectsEngagements(BaseModel):
    user_key: str
    org_unit: List["TestingGetEmployeeEmployeesObjectsObjectsEngagementsOrgUnit"]
    job_function: "TestingGetEmployeeEmployeesObjectsObjectsEngagementsJobFunction"
    engagement_type: "TestingGetEmployeeEmployeesObjectsObjectsEngagementsEngagementType"
    primary: Optional["TestingGetEmployeeEmployeesObjectsObjectsEngagementsPrimary"]
    validity: "TestingGetEmployeeEmployeesObjectsObjectsEngagementsValidity"


class TestingGetEmployeeEmployeesObjectsObjectsEngagementsOrgUnit(BaseModel):
    user_key: str


class TestingGetEmployeeEmployeesObjectsObjectsEngagementsJobFunction(BaseModel):
    user_key: str


class TestingGetEmployeeEmployeesObjectsObjectsEngagementsEngagementType(BaseModel):
    user_key: str


class TestingGetEmployeeEmployeesObjectsObjectsEngagementsPrimary(BaseModel):
    user_key: str


class TestingGetEmployeeEmployeesObjectsObjectsEngagementsValidity(BaseModel):
    from_: datetime = Field(alias="from")
    to: Optional[datetime]


class TestingGetEmployeeEmployeesObjectsObjectsAddresses(BaseModel):
    value: str
    address_type: "TestingGetEmployeeEmployeesObjectsObjectsAddressesAddressType"
    engagement: Optional[
        List["TestingGetEmployeeEmployeesObjectsObjectsAddressesEngagement"]
    ]
    visibility: Optional["TestingGetEmployeeEmployeesObjectsObjectsAddressesVisibility"]
    validity: "TestingGetEmployeeEmployeesObjectsObjectsAddressesValidity"


class TestingGetEmployeeEmployeesObjectsObjectsAddressesAddressType(BaseModel):
    user_key: str


class TestingGetEmployeeEmployeesObjectsObjectsAddressesEngagement(BaseModel):
    user_key: str


class TestingGetEmployeeEmployeesObjectsObjectsAddressesVisibility(BaseModel):
    user_key: str


class TestingGetEmployeeEmployeesObjectsObjectsAddressesValidity(BaseModel):
    from_: datetime = Field(alias="from")
    to: Optional[datetime]


class TestingGetEmployeeEmployeesObjectsObjectsItusers(BaseModel):
    user_key: str
    itsystem: "TestingGetEmployeeEmployeesObjectsObjectsItusersItsystem"
    engagement: Optional[
        List["TestingGetEmployeeEmployeesObjectsObjectsItusersEngagement"]
    ]
    validity: "TestingGetEmployeeEmployeesObjectsObjectsItusersValidity"


class TestingGetEmployeeEmployeesObjectsObjectsItusersItsystem(BaseModel):
    user_key: str


class TestingGetEmployeeEmployeesObjectsObjectsItusersEngagement(BaseModel):
    user_key: str


class TestingGetEmployeeEmployeesObjectsObjectsItusersValidity(BaseModel):
    from_: datetime = Field(alias="from")
    to: Optional[datetime]


TestingGetEmployee.update_forward_refs()
TestingGetEmployeeEmployees.update_forward_refs()
TestingGetEmployeeEmployeesObjects.update_forward_refs()
TestingGetEmployeeEmployeesObjectsObjects.update_forward_refs()
TestingGetEmployeeEmployeesObjectsObjectsValidity.update_forward_refs()
TestingGetEmployeeEmployeesObjectsObjectsEngagements.update_forward_refs()
TestingGetEmployeeEmployeesObjectsObjectsEngagementsOrgUnit.update_forward_refs()
TestingGetEmployeeEmployeesObjectsObjectsEngagementsJobFunction.update_forward_refs()
TestingGetEmployeeEmployeesObjectsObjectsEngagementsEngagementType.update_forward_refs()
TestingGetEmployeeEmployeesObjectsObjectsEngagementsPrimary.update_forward_refs()
TestingGetEmployeeEmployeesObjectsObjectsEngagementsValidity.update_forward_refs()
TestingGetEmployeeEmployeesObjectsObjectsAddresses.update_forward_refs()
TestingGetEmployeeEmployeesObjectsObjectsAddressesAddressType.update_forward_refs()
TestingGetEmployeeEmployeesObjectsObjectsAddressesEngagement.update_forward_refs()
TestingGetEmployeeEmployeesObjectsObjectsAddressesVisibility.update_forward_refs()
TestingGetEmployeeEmployeesObjectsObjectsAddressesValidity.update_forward_refs()
TestingGetEmployeeEmployeesObjectsObjectsItusers.update_forward_refs()
TestingGetEmployeeEmployeesObjectsObjectsItusersItsystem.update_forward_refs()
TestingGetEmployeeEmployeesObjectsObjectsItusersEngagement.update_forward_refs()
TestingGetEmployeeEmployeesObjectsObjectsItusersValidity.update_forward_refs()
