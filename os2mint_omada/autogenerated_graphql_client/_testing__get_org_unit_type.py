# Generated by ariadne-codegen on 2024-01-19 16:15
# Source: queries.graphql
from typing import List
from uuid import UUID

from .base_model import BaseModel


class TestingGetOrgUnitType(BaseModel):
    classes: "TestingGetOrgUnitTypeClasses"


class TestingGetOrgUnitTypeClasses(BaseModel):
    objects: List["TestingGetOrgUnitTypeClassesObjects"]


class TestingGetOrgUnitTypeClassesObjects(BaseModel):
    uuid: UUID


TestingGetOrgUnitType.update_forward_refs()
TestingGetOrgUnitTypeClasses.update_forward_refs()
TestingGetOrgUnitTypeClassesObjects.update_forward_refs()
