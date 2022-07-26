# SPDX-FileCopyrightText: 2021 Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from datetime import datetime
from datetime import time
from typing import cast

from ramodels.mo import Validity


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


def validity_union(*validities: Validity) -> Validity:
    """Calculate union of given validities.

    Args:
        **validities: Validities to union.

    Returns: Validity union.
    """
    from_dates = [v.from_date for v in validities]
    to_dates = [v.to_date for v in validities]

    from_date = min(from_dates)

    if any(d is None for d in to_dates):
        to_date = None
    else:
        to_date = max(to_dates, default=None)  # type: ignore

    return Validity(from_date=from_date, to_date=to_date)


def validity_intersection(*validities: Validity) -> Validity:
    """Calculate intersection of given validities.

    Args:
        **validities: Validities to intersect.

    Returns: Validity intersection.
    """
    from_dates = [v.from_date for v in validities]
    to_dates = [v.to_date for v in validities]

    from_date = max(from_dates)
    to_date = min(filter(None, to_dates), default=None)

    return Validity(from_date=from_date, to_date=to_date)
