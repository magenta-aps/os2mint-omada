# SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from os2mint_omada.sync.models import Validity


def validity_union(*validities: Validity) -> Validity:
    """Calculate union of given validities.

    Args:
        **validities: Validities to union.

    Returns: Validity union.
    """
    starts = [v.start for v in validities]
    ends = [v.end for v in validities]

    start = min(starts)

    if any(e is None for e in ends):
        end = None
    else:
        end = max(ends, default=None)  # type: ignore

    return Validity(start=start, end=end)


def validity_intersection(*validities: Validity) -> Validity:
    """Calculate intersection of given validities.

    Args:
        **validities: Validities to intersect.

    Returns: Validity intersection.
    """
    starts = [v.start for v in validities]
    ends = [v.end for v in validities]

    start = max(starts)
    end = min(filter(None, ends), default=None)

    return Validity(start=start, end=end)
