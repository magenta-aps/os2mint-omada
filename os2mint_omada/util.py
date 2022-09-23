# SPDX-FileCopyrightText: 2021 Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
import asyncio
from contextlib import asynccontextmanager
from datetime import datetime
from datetime import time
from typing import AsyncGenerator
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


@asynccontextmanager
async def sleep_on_error(delay: int = 30) -> AsyncGenerator:
    """Async context manager that delays returning on errors.

    This is used to prevent race-conditions on writes to MO/LoRa, when the upload times
    out initially but is completed by the backend afterwards. The sleep ensures that
    the AMQP message is not retried immediately, causing the handler to act on
    information which could become stale by the queued write. This happens because the
    backend does not implement fairness of requests, such that read operations can
    return soon-to-be stale data while a write operation is queued on another thread.

    Specifically, duplicate objects would be created when a write operation failed to
    complete within the timeout (but would be completed later), and the handler, during
    retry, read an outdated list of existing objects, and thus dispatched another
    (duplicate) write operation.

    See: https://redmine.magenta-aps.dk/issues/51949#note-23.
    """
    try:
        yield
    except Exception:
        await asyncio.sleep(delay)
