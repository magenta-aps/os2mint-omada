# SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
import tenacity
from tenacity import stop_after_delay
from tenacity import wait_fixed


def retry(*args, stop=stop_after_delay(30), wait=wait_fixed(2), **kwargs):
    """Tenacity retry decorator, with defaults useful for testing.

    Args:
        *args: Additional positional arguments passed to tenacity's retry().
        stop: Stop after 30 seconds so the test doesn't run forever.
            The default duration is long since some integrations need multiple rounds
            of AMQP messages to complete, and therefore need a long time to get in a
            consistent state.
        wait: Wait two seconds between assertion attempts.
        **kwargs: Additional keyword arguments passed to tenacity's retry().

    Returns:
        Function decorated with retrying.
    """
    # reraise=True so a false assertion fails the test
    return tenacity.retry(*args, stop=stop, wait=wait, reraise=True, **kwargs)
