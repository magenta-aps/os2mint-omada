# Generated by ariadne-codegen on 2024-10-10 13:36
# Source: queries.graphql

from uuid import UUID

from .base_model import BaseModel


class TestingCreateOrgUnit(BaseModel):
    org_unit_create: "TestingCreateOrgUnitOrgUnitCreate"


class TestingCreateOrgUnitOrgUnitCreate(BaseModel):
    uuid: UUID


TestingCreateOrgUnit.update_forward_refs()
TestingCreateOrgUnitOrgUnitCreate.update_forward_refs()
