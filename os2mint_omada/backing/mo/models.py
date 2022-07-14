# SPDX-FileCopyrightText: 2022 Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from uuid import UUID

from more_itertools import one
from pydantic import BaseModel
from pydantic import validator
from ramodels.mo.details import Address
from ramodels.mo.details import Engagement
from ramodels.mo.details import ITUser


class EmployeeData(BaseModel):
    """Model for employee data from GraphQL."""

    uuid: UUID
    engagements: list[Engagement]
    addresses: list[Address]
    itusers: list[ITUser]

    @validator("engagements", pre=True, each_item=True)
    def convert_engagement(cls, engagement: dict) -> dict:
        """Convert GraphQL engagement to be RA-Models compatible."""
        engagement["person"] = one(engagement["person"])
        engagement["org_unit"] = {"uuid": engagement.pop("org_unit_uuid")}
        return engagement

    @validator("addresses", pre=True, each_item=True)
    def convert_address(cls, address: dict) -> dict:
        """Convert GraphQL address to be RA-Models compatible."""
        address["person"] = one(address["person"])
        return address

    @validator("itusers", pre=True, each_item=True)
    def convert_ituser(cls, ituser: dict) -> dict:
        """Convert GraphQL ituser to be RA-Models compatible."""
        ituser["person"] = one(ituser["person"])
        ituser["itsystem"] = {"uuid": ituser.pop("itsystem_uuid")}
        return ituser
