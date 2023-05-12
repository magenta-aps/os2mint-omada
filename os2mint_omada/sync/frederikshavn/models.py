# SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from pydantic import Field
from pydantic import validator

from os2mint_omada.omada.models import OmadaUser


class FrederikshavnOmadaUser(OmadaUser):
    """Frederikshavn-specific Omada user model.

    `min_length=1` ensures that we do not accept empty strings.
    """

    # Employee
    first_name: str = Field(alias="FIRSTNAME", min_length=1)
    last_name: str = Field(alias="LASTNAME", min_length=1)
    cpr_number: str = Field(alias="C_CPRNUMBER", min_length=10)

    # Engagement
    employee_number: str = Field(alias="C_POSITIONID", min_length=1)
    job_title: str = Field(alias="C_JOBTITLE_ODATA", min_length=1)
    org_unit: str = Field(alias="C_OUID_ODATA", min_length=1)

    # IT User
    ad_login: str = Field(alias="ADLOGON", min_length=1)

    # Address
    email: str = Field(alias="EMAIL")

    @validator("cpr_number")
    def strip_cpr_dash(cls, cpr_number: str) -> str:
        """Strip dashes from CPR, e.g. "xxxxxx-xxxx", to be MO-compatible."""
        return cpr_number.replace("-", "")

    @validator("employee_number", "org_unit")
    def strip_leading_zeroes(cls, value: str) -> str:
        """Strip leading zeroes from employee and org unit numbers to be MO-compatible.

        The employee and organisation unit are 8 character, zero-padded numbers in
        Opus. These numbers are exposed by the Opus webservice directly to Omada. OS2mo
        imports data from Opus through the nightly XML export, however, which does
        _not_ zero-pad the numbers. Therefore, the leading zeroes are stripped to be
        MO-compatible.
        """
        return value.lstrip("0")
