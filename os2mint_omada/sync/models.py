# SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

from datetime import datetime
from datetime import time
from typing import Any
from uuid import UUID

import structlog
from pydantic import BaseModel
from pydantic import validator
from ramodels.mo import Validity

logger = structlog.get_logger(__name__)


class ComparableMixin(BaseModel):
    @validator("uuid", check_fields=False)
    def strip_uuid(cls, uuid: UUID) -> None:
        """Strip UUID to allow for convenient comparison of models."""
        return None

    @validator("validity", check_fields=False)
    def validity_at_midnight(cls, validity: Validity) -> Validity:
        """Normalise validity dates to allow for convenient comparison of models.

        Date(time)s are converted to "midnight" for MO compatibility by removing the
        time-component.
        """

        def at_midnight(date: datetime | None) -> datetime | None:
            if date is None:
                return None
            return datetime.combine(date, time.min)

        return Validity(
            from_date=at_midnight(validity.from_date),
            to_date=at_midnight(validity.to_date),
        )


class StripUserKeyMixin(BaseModel):
    @validator("user_key", check_fields=False)
    def strip_user_key(cls, user_key: Any | None) -> None:
        """Strip user key to allow for convenient comparison of models.

        Should only be used on objects where the user key does not contain actual
        relevant data, but is simply a copy of the UUID (as automatically set by MOBase
        if absent).
        """
        return None


CPR_ONLY_NORMAL_REGEX = r"(0[1-9]|[12][0-9]|3[01])(0[1-9]|1[0-2])(\d{2})(\d{4})"
# https://statens-adm.dk/support/loensupport/brugervejledninger/fiktive-cpr-numre/
CPR_INCL_FICTIVE_REGEX = r"([06][1-9]|[1278][0-9]|[39][01])(0[1-9]|1[0-2])(\d{2})(\d{4})"
