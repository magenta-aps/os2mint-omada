# SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from uuid import UUID

from pydantic import Field

from os2mint_omada.omada.models import OmadaUser


class SilkeborgOmadaUser(OmadaUser):
    """Silkeborg-specific Omada user model."""

    # Engagement
    service_number: str = Field(alias="C_TJENESTENR")

    # IT User
    ad_guid: UUID | None = Field(alias="C_OBJECTGUID_I_AD")
    login: str | None = Field(alias="C_LOGIN")

    # Address
    email: str | None = Field(alias="EMAIL")
    phone_direct: str | None = Field(alias="C_DIREKTE_TLF")
    phone_cell: str | None = Field(alias="CELLPHONE")
    phone_institution: str | None = Field(alias="C_INST_PHONE")

    @property
    def is_manual(self):
        """Manually created users have IdentityCategory ID 561 in Silkeborg"""
        return self.identity_category.id == "561"


class ManualSilkeborgOmadaUser(SilkeborgOmadaUser):
    """Silkeborg-specific Omada user with additional fields for 'manual' users.

    Manual users not only have addresses and IT users synchronised, but also the
    employee object itself, as well as associated engagements.
    """

    # Employee
    first_name: str = Field(alias="C_FORNAVNE")
    last_name: str = Field(alias="LASTNAME")
    cpr_number: str = Field(alias="C_CPRNR", min_length=10, max_length=10)

    # Engagement
    job_title: str | None = Field(alias="JOBTITLE")
    org_unit: UUID = Field(alias="C_ORGANISATIONSKODE")
    is_visible: bool = Field(alias="C_SYNLIG_I_OS2MO", default=True)
