# SPDX-FileCopyrightText: 2021 Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from datetime import datetime
from datetime import time
from typing import cast
from typing import TypeVar

from ramodels.mo._shared import Validity
from ramodels.mo.details import Address
from ramodels.mo.details import Engagement
from ramodels.mo.details import ITUser

MOBaseWithValidity = TypeVar("MOBaseWithValidity", Address, Engagement, ITUser)


def at_midnight(date: datetime | None) -> datetime | None:
    if date is None:
        return None
    return datetime.combine(date, time.min)


def midnight() -> datetime:
    return cast(datetime, at_midnight(datetime.utcnow()))


def as_terminated(
    model: MOBaseWithValidity, from_date: datetime | None = None
) -> MOBaseWithValidity:
    return model.parse_obj(  # pydantic doesn't validate on .copy()
        model.copy(
            update=dict(
                validity=Validity(
                    from_date=model.validity.from_date,
                    to_date=from_date if from_date is not None else midnight(),
                ),
            )
        )
    )
