# SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from typing import Any

from pydantic import Field
from pydantic import validator

from os2mint_omada.omada.models import OmadaUser
from os2mint_omada.sync.models import CPR_ONLY_NORMAL_REGEX


class FrederikshavnOmadaUser(OmadaUser):
    """Frederikshavn-specific Omada user model."""

    # Employee
    first_name: str = Field(alias="FIRSTNAME")
    last_name: str = Field(alias="LASTNAME")
    cpr_number: str = Field(
        alias="C_CPRNUMBER",
        min_length=10,
        max_length=10,
        regex=CPR_ONLY_NORMAL_REGEX,
    )

    # Engagement
    employee_number: str = Field(alias="C_MEDARBEJDERNR_ODATA")
    job_title: str | None = Field(alias="C_JOBTITLE_ODATA")
    org_unit: str = Field(alias="C_OUID_ODATA")

    # IT User
    ad_login: str | None = Field(alias="ADLOGON")

    # Address
    email: str | None = Field(alias="EMAIL")
    phone: str | None = Field(alias="C_TELEPHONENUMBER")
    cellphone: str | None = Field(alias="CELLPHONE")

    @validator("cpr_number", pre=True)
    def strip_cpr_dash(cls, cpr_number: Any) -> str:
        """Strip dashes from CPR, e.g. "xxxxxx-xxxx", to be MO-compatible."""
        if not isinstance(cpr_number, str):
            raise ValueError("CPR number not a string")
        return cpr_number.replace("-", "")

    @validator("org_unit")
    def strip_leading_zeroes(cls, value: str) -> str:
        """Strip leading zeroes from org unit numbers to be MO-compatible.

        The organisation unit are 8 character, zero-padded numbers in Opus. These
        numbers are exposed by the Opus webservice directly to Omada. OS2mo imports
        data from Opus through the nightly XML export, however, which does _not_
        zero-pad the numbers. Therefore, the leading zeroes are stripped to be
        MO-compatible.
        """
        return value.lstrip("0")

    @validator("phone", "cellphone")
    def strip_phone_number_spaces(cls, value: str | None) -> str | None:
        """Strip spaces from phone numbers to be MO-compatible."""
        if value is None:
            return None
        return value.replace(" ", "")
