# SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
import re
from uuid import UUID

from pydantic import BaseModel
from pydantic import Field
from pydantic import root_validator
from pydantic import validator

from os2mint_omada.omada.models import OmadaUser


class EgedalOmadaEmployment(BaseModel):
    """Nested under the `EMPLOYMENTS` field on the Egedal-specific Omada identities."""

    employment_number: str
    job_title: str
    org_unit: str

    @root_validator(pre=True)
    def extract_fields(cls, values: dict) -> dict:
        """Extract fields embedded in the DisplayName.

        All the required data is present in the 'DisplayName' field, which is a string
        of the format:
          Social- og sundhedsassistent (Sygepleje (V) [SYGEPLEJE (V)]) ID:(00009093) ;
        where 'Social- og sundhedsassistent' is the job title, 'Sygepleje (V)' the
        organisation unit's name, and '00009093' the employment number.
        """
        display_name = values["DisplayName"]
        match = re.match(r"(.+?) \((.+) \[.*?]\) ID:\((\d+)\) ;", display_name)
        if not match:
            raise ValueError(f"Unable to parse {display_name=}")
        job_title, org_unit, employment_number = match.groups()
        return {
            **values,
            "job_title": job_title,
            "org_unit": org_unit,
            "employment_number": employment_number,
        }

    @validator("employment_number")
    def strip_leading_zeroes(cls, value: str) -> str:
        """Strip leading zeroes from employment number to be MO-compatible.

        The employment numbers are 8 character, zero-padded numbers in Opus. These
        numbers are exposed by the Opus webservice directly to Omada. OS2mo imports
        data from Opus through the nightly XML export, however, which does _not_
        zero-pad the numbers. Therefore, the leading zeroes are stripped to be
        MO-compatible.
        """
        return value.lstrip("0")


class EgedalOmadaUser(OmadaUser):
    """Egedal-specific Omada user model."""

    # Employee
    cpr_number: str = Field(alias="C_EMPLOYEEID", min_length=10, max_length=10)
    nickname_first_name: str | None = Field(alias="C_OIS_FIRSTNAME")
    nickname_last_name: str | None = Field(alias="C_OIS_LASTNAME")

    # IT User
    ad_guid: UUID | None = Field(alias="OBJECTGUID")
    ad_login: str | None = Field(alias="C_ADUSERNAME")

    # Address
    email: str | None = Field(alias="EMAIL")
    phone: str | None = Field(alias="PHONE")
    cellphone: str | None = Field(alias="CELLPHONE")

    @property
    def is_manual(self):
        """Manually created users have IdentityCategory ID 561 in Egedal"""
        return self.identity_category.id == "561"


class ManualEgedalOmadaUser(EgedalOmadaUser):
    """Egedal-specific Omada user with additional fields for 'manual' users.

    Manual users not only have addresses and IT users synchronised, but also the
    employee object itself, as well as associated engagements.
    """

    # Employee
    first_name: str = Field(alias="FIRSTNAME")
    last_name: str = Field(alias="LASTNAME")

    # Engagements
    employments: list[EgedalOmadaEmployment] = Field(alias="EMPLOYMENTS")
