# SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from uuid import UUID

from pydantic import Field

from os2mint_omada.omada.models import OmadaUser
from os2mint_omada.sync.models import CPR_INCL_FICTIVE_REGEX

# All users have a C_TJENESTENR, and SD users additionally have a C_OS2MO_ID. A
# user is a 'manual' user if it isn't an SD user.
#
# | C_TJENESTENR | C_OS2MO_ID | count | manual? |
# |--------------|------------|-------|---------|
# | Yes          | Yes        | 7000  | No      |
# | Yes          | No         | 600   | Yes     |
#
# All users have addresses and IT-users synchronised. Manual users also have
# their employee object and associated engagements synchronised from Omada.
#
# C_TJENESTENR and C_OS2MO_ID are similar, and it is possible to calculate one
# from the other. An example:
#
#   C_TJENESTENR: 1000F
#   C_OS2MO_ID: TF-10005
#


class SilkeborgOmadaUser(OmadaUser):
    """Silkeborg-specific Omada user model."""

    # Employee
    cpr_number: str = Field(
        alias="C_CPRNR",
        min_length=10,
        max_length=10,
        regex=CPR_INCL_FICTIVE_REGEX,
    )

    # Engagement
    service_number: str = Field(alias="C_TJENESTENR")
    os2mo_id: str | None = Field(alias="C_OS2MO_ID")

    # IT User
    ad_guid: UUID = Field(alias="C_OBJECTGUID_I_AD")
    login: str = Field(alias="C_LOGIN")

    # Address
    email: str | None = Field(alias="EMAIL")
    phone_direct: str | None = Field(alias="C_DIREKTE_TLF")
    phone_cell: str | None = Field(alias="CELLPHONE")
    phone_institution: str | None = Field(alias="C_INST_PHONE")

    @property
    def is_manual(self) -> bool:
        """Manual users don't have a C_OS2MO_ID ID."""
        return self.os2mo_id is None


class ManualSilkeborgOmadaUser(SilkeborgOmadaUser):
    """Silkeborg-specific Omada user with additional fields for 'manual' users."""

    # Employee
    first_name: str = Field(alias="C_FORNAVNE")
    last_name: str = Field(alias="LASTNAME")

    # Engagement
    job_title: str | None = Field(alias="JOBTITLE")
    org_unit: UUID = Field(alias="C_ORGANISATIONSKODE")
    is_visible: bool = Field(alias="C_SYNLIG_I_OS2MO", default=True)
