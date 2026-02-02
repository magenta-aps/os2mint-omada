from datetime import datetime
from typing import List
from typing import Optional

from .base_model import BaseModel


class GetOrgUnitValidity(BaseModel):
    org_units: "GetOrgUnitValidityOrgUnits"


class GetOrgUnitValidityOrgUnits(BaseModel):
    objects: List["GetOrgUnitValidityOrgUnitsObjects"]


class GetOrgUnitValidityOrgUnitsObjects(BaseModel):
    validities: List["GetOrgUnitValidityOrgUnitsObjectsValidities"]


class GetOrgUnitValidityOrgUnitsObjectsValidities(BaseModel):
    validity: "GetOrgUnitValidityOrgUnitsObjectsValiditiesValidity"


class GetOrgUnitValidityOrgUnitsObjectsValiditiesValidity(BaseModel):
    from_date: datetime
    to_date: Optional[datetime]


GetOrgUnitValidity.update_forward_refs()
GetOrgUnitValidityOrgUnits.update_forward_refs()
GetOrgUnitValidityOrgUnitsObjects.update_forward_refs()
GetOrgUnitValidityOrgUnitsObjectsValidities.update_forward_refs()
GetOrgUnitValidityOrgUnitsObjectsValiditiesValidity.update_forward_refs()
