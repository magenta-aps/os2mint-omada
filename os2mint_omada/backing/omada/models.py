# SPDX-FileCopyrightText: 2021 Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from datetime import datetime
from typing import Any
from typing import NewType
from uuid import UUID

from pydantic import BaseModel
from pydantic import Field
from pydantic import validator

RawOmadaUser = NewType("RawOmadaUser", dict[str, Any])


class IdentityCategory(BaseModel):
    id: str = Field(alias="Id")
    uid: UUID = Field(alias="UId")

    class Config:
        # Allow fields to be populated by both alias and model attribute name
        allow_population_by_field_name = True


class OmadaUser(BaseModel):
    """
    Types derived from Omada OData. See: docs/odata.dataobjects.metadata.xml.
    """

    identity_category: IdentityCategory = Field(alias="IDENTITYCATEGORY")

    service_number: str = Field(alias="C_TJENESTENR")
    ad_guid: UUID = Field(alias="C_OBJECTGUID_I_AD")
    login: str = Field(alias="C_LOGIN")

    email: str = Field(alias="EMAIL")
    phone_direct: str = Field(alias="C_DIREKTE_TLF")
    phone_cell: str = Field(alias="CELLPHONE")
    phone_institution: str = Field(alias="C_INST_PHONE")

    valid_from: datetime = Field(alias="VALIDFROM")
    valid_to: datetime | None = Field(alias="VALIDTO", default=None)

    class Config:
        # Allow fields to be populated by both alias and model attribute name
        allow_population_by_field_name = True


class ManualOmadaUser(OmadaUser):
    """
    TODO
    """

    first_name: str = Field(alias="C_FORNAVNE")
    last_name: str = Field(alias="LASTNAME")

    cpr_number: str = Field(alias="C_CPRNR")
    job_title: str = Field(alias="JOBTITLE")

    org_unit: UUID = Field(alias="C_ORGANISATIONSKODE")

    @validator("identity_category")
    def check_is_manual(cls, identity_category: IdentityCategory) -> IdentityCategory:
        """
        TODO
        """
        # Manually created users have ID 561 in Silkeborg
        if identity_category.id != "561":
            raise ValueError("Identity category is not manual")
        return identity_category
