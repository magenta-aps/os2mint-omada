# SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel
from pydantic import Extra
from pydantic import Field
from pydantic import validator
from ramodels.mo import Validity

RawOmadaUser = dict[str, Any]


class IdentityCategory(BaseModel):
    """Identifies the type of Omada user."""

    id: str = Field(alias="Id")
    uid: UUID = Field(alias="UId")

    class Config:
        # Allow fields to be populated by both alias and model attribute name
        allow_population_by_field_name = True


class OmadaUser(BaseModel):
    """General Omada user model with base fields."""

    id: int = Field(alias="Id")
    uid: UUID = Field(alias="UId")

    valid_from: datetime = Field(alias="VALIDFROM")
    valid_to: datetime | None = Field(alias="VALIDTO", default=None)

    identity_category: IdentityCategory = Field(alias="IDENTITYCATEGORY")

    @validator("*", pre=True)
    def empty_string_is_none(cls, value: Any) -> Any:
        """Omada often returns empty strings for non-existent attributes."""
        if value == "":
            return None
        return value

    @validator("valid_to")
    def fix_pseudo_infinity(cls, value: datetime | None) -> datetime | None:
        """Convert Omada's pseudo-infinity to "actual"/MO infinity (None)."""
        if value is None or value.year == 9999:
            return None
        return value

    class Config:
        # Allow fields to be populated by both alias and model attribute name
        allow_population_by_field_name = True
        # Preserve extra attributes, allowing the object to be converted to
        # a customer-specific subclasses later.
        extra = Extra.allow

    @property
    def validity(self) -> Validity:
        """Return MO-compatible Validity object."""
        return Validity(
            from_date=self.valid_from,
            to_date=self.valid_to,
        )
