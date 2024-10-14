# SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

from datetime import datetime
from datetime import time
from uuid import UUID

import structlog
from pydantic import BaseModel
from pydantic import Extra
from pydantic import validator

logger = structlog.stdlib.get_logger()


class StrictBaseModel(BaseModel):
    """Pydantic BaseModel with strict(er) defaults."""

    class Config:
        extra = Extra.forbid
        frozen = True


class Validity(StrictBaseModel):
    start: datetime
    end: datetime | None

    @validator("start", "end")
    def validity_at_midnight(cls, value: datetime | None) -> datetime | None:
        """Normalise validity dates to allow for convenient comparison of models.

        Date(time)s are converted to "midnight" for MO compatibility by removing the
        time-component.
        """
        if value is None:
            return None
        return datetime.combine(value, time.min)


class Address(StrictBaseModel):
    uuid: UUID | None
    value: str
    address_type: UUID
    person: UUID
    visibility: UUID | None
    engagement: UUID | None
    it_user: UUID | None
    validity: Validity


class Employee(StrictBaseModel):
    uuid: UUID | None
    cpr_number: str
    given_name: str
    surname: str
    nickname_given_name: str | None
    nickname_surname: str | None


class Engagement(StrictBaseModel):
    uuid: UUID | None
    user_key: str
    org_unit: UUID
    person: UUID
    job_function: UUID
    engagement_type: UUID
    primary: UUID | None
    validity: Validity


class ITUser(StrictBaseModel):
    uuid: UUID | None
    external_id: str | None
    user_key: str | None
    it_system: UUID
    person: UUID
    engagement: UUID | None
    validity: Validity


class StripUUIDMixin(StrictBaseModel):
    """Strip UUID to allow for convenient comparison of models."""

    @validator("uuid", check_fields=False)
    def strip_uuid(cls, uuid: UUID | None) -> None:
        return None


class ComparableAddress(StripUUIDMixin, Address):
    pass


class ComparableEmployee(StripUUIDMixin, Employee):
    pass


class ComparableEngagement(StripUUIDMixin, Engagement):
    pass


class ComparableITUser(StripUUIDMixin, ITUser):
    pass


CPR_ONLY_NORMAL_REGEX = r"(0[1-9]|[12][0-9]|3[01])(0[1-9]|1[0-2])(\d{2})(\d{4})"
# https://statens-adm.dk/support/loensupport/brugervejledninger/fiktive-cpr-numre/
CPR_INCL_FICTIVE_REGEX = (
    r"([06][1-9]|[1278][0-9]|[39][01])(0[1-9]|1[0-2])(\d{2})(\d{4})"
)
