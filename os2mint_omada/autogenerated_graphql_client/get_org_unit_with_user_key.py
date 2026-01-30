from typing import List
from uuid import UUID

from .base_model import BaseModel


class GetOrgUnitWithUserKey(BaseModel):
    org_units: "GetOrgUnitWithUserKeyOrgUnits"


class GetOrgUnitWithUserKeyOrgUnits(BaseModel):
    objects: List["GetOrgUnitWithUserKeyOrgUnitsObjects"]


class GetOrgUnitWithUserKeyOrgUnitsObjects(BaseModel):
    uuid: UUID


GetOrgUnitWithUserKey.update_forward_refs()
GetOrgUnitWithUserKeyOrgUnits.update_forward_refs()
GetOrgUnitWithUserKeyOrgUnitsObjects.update_forward_refs()
