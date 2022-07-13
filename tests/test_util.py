# SPDX-FileCopyrightText: 2022 Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from datetime import datetime
from typing import Callable
from typing import cast
from uuid import uuid4

from hypothesis import given
from hypothesis import strategies as st
from hypothesis.strategies import composite
from ramodels.mo import MOBase
from ramodels.mo._shared import Validity

from os2mint_omada.util import as_terminated
from os2mint_omada.util import MOBaseWithValidity


@composite
def from_and_to_date(draw: Callable) -> tuple[datetime, datetime]:
    from_date = draw(st.datetimes())
    to_date = draw(st.datetimes(min_value=from_date))
    return from_date, to_date


@given(from_and_to_date())
def test_as_terminated(from_and_to_date: tuple[datetime, datetime]) -> None:
    from_date, to_date = from_and_to_date

    class Model(MOBase):
        validity: Validity

    uuid = uuid4()
    obj = Model(
        uuid=uuid,
        validity=Validity(
            from_date=from_date,
            to_date=None,
        ),
    )
    obj = cast(MOBaseWithValidity, obj)
    actual = as_terminated(obj, from_date=from_date)
    expected = Model(
        uuid=uuid,
        validity=Validity(
            from_date=from_date,
            to_date=from_date,
        ),
    )
    assert actual == expected
