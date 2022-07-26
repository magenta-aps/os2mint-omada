# SPDX-FileCopyrightText: 2021 Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from datetime import datetime
from typing import Any
from typing import NewType
from uuid import UUID

from pydantic import BaseModel
from pydantic import Extra
from pydantic import Field
from pydantic import validator
from ramodels.mo import Validity

RawOmadaUser = NewType("RawOmadaUser", dict[str, Any])


class IdentityCategory(BaseModel):
    """Identifies the type of user, i.e. 'normal' or 'manual'."""

    id: str = Field(alias="Id")
    uid: UUID = Field(alias="UId")

    class Config:
        # Allow fields to be populated by both alias and model attribute name
        allow_population_by_field_name = True


class OmadaUser(BaseModel):
    """Omada API user with relevant fields.

    Types derived from Omada OData. See: docs/odata.dataobjects.metadata.xml or #42613.
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

    @validator("valid_to")
    def fix_pseudo_infinity(cls, value: datetime | None) -> datetime | None:
        """Convert Omada's pseudo-infinity to actual infinity (None)."""
        if value is None or value.year == 9999:
            return None
        return value

    class Config:
        # Allow fields to be populated by both alias and model attribute name
        allow_population_by_field_name = True
        # Allow extra attributes so potential "manual" fields are preserved, allowing
        # the object to be converted to a ManualOmadaUser later.
        extra = Extra.allow

    @property
    def validity(self) -> Validity:
        """Return MO-compatible Validity object."""
        return Validity(
            from_date=self.valid_from,
            to_date=self.valid_to,
        )


class ManualOmadaUser(OmadaUser):
    """Omada API user with additional fields for 'manual' users.

    Manual users not only have addresses and IT users synchronised, but also the
    employee object itself, as well as associated engagements.
    """

    first_name: str = Field(alias="C_FORNAVNE")
    last_name: str = Field(alias="LASTNAME")

    cpr_number: str = Field(alias="C_CPRNR")
    job_title: str = Field(alias="JOBTITLE")

    org_unit: UUID = Field(alias="C_ORGANISATIONSKODE")

    @validator("identity_category")
    def check_is_manual(cls, identity_category: IdentityCategory) -> IdentityCategory:
        """Validate that the identity category is indeed that of a manual user.

        All users in the Omada OData view have the same set of fields, so a 'normal'
        user could pass validation as a manual one (and vice-versa) unless we check
        the identity category explicitly.
        """
        # Manually created users have ID 561 in Silkeborg
        if identity_category.id != "561":
            raise ValueError("Identity category is not manual")
        return identity_category
