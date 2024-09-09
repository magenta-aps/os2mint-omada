# SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from datetime import datetime

from os2mint_omada.sync.models import Validity
from os2mint_omada.util import validity_intersection
from os2mint_omada.util import validity_union


def test_validity_union() -> None:
    actual = validity_union(
        Validity(
            start=datetime(1999, 1, 1),
            end=datetime(2018, 9, 5),
        ),
        Validity(
            start=datetime(2016, 3, 7),
            end=datetime(2022, 8, 4),
        ),
    )

    expected = Validity(
        start=datetime(1999, 1, 1),
        end=datetime(2022, 8, 4),
    )
    assert actual == expected


def test_validity_union_nones() -> None:
    actual = validity_union(
        Validity(
            start=datetime(1999, 1, 1),
            end=datetime(2018, 1, 1),
        ),
        Validity(
            start=datetime(2016, 3, 7),
            end=None,
        ),
    )

    expected = Validity(
        start=datetime(1999, 1, 1),
        end=None,
    )
    assert actual == expected


def test_validity_intersection() -> None:
    actual = validity_intersection(
        Validity(
            start=datetime(1999, 1, 1),
            end=datetime(2018, 9, 5),
        ),
        Validity(
            start=datetime(2016, 3, 7),
            end=datetime(2022, 8, 4),
        ),
    )

    expected = Validity(
        start=datetime(2016, 3, 7),
        end=datetime(2018, 9, 5),
    )
    assert actual == expected


def test_validity_intersection_nones() -> None:
    actual = validity_intersection(
        Validity(
            start=datetime(1999, 1, 1),
            end=datetime(2018, 1, 1),
        ),
        Validity(
            start=datetime(2016, 3, 7),
            end=None,
        ),
    )

    expected = Validity(
        start=datetime(2016, 3, 7),
        end=datetime(2018, 1, 1),
    )
    assert actual == expected
