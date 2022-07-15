# SPDX-FileCopyrightText: 2021 Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from datetime import datetime
from datetime import time
from typing import cast


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
