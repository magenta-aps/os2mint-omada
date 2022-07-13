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
    """Convert given datetime to "midnight" - for MO compatibility.

    Args:
        date: Datetime. None is accepted to ease use for 'None' used as infinity.

    Returns: The given date with the time-component removed.
    """
    if date is None:
        return None
    return datetime.combine(date, time.min)


def midnight() -> datetime:
    """Midnight. Hopefully it's not a full moon - scary!

    Returns: Datetime object of the current day's midnight.
    """
    return cast(datetime, at_midnight(datetime.utcnow()))


def as_terminated(
    model: MOBaseWithValidity, from_date: datetime | None = None
) -> MOBaseWithValidity:
    """Terminate a MO object by setting its validity.

    Args:
        model: Object to terminate.
        from_date: Termination date. If not given, today will be used.

    Returns: A copy of the given object with its validity changed for termination.
    """
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
