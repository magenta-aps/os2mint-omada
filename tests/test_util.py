# SPDX-FileCopyrightText: 2021 Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from datetime import datetime
from uuid import uuid4

from ramodels.mo import MOBase
from ramodels.mo._shared import Validity

from os2mint_omada.util import as_terminated


def test_as_terminated() -> None:
    class Model(MOBase):
        validity: Validity

    uuid = uuid4()
    obj = Model(
        uuid=uuid,
        validity=Validity(
            from_date=datetime(2010, 1, 2),
            to_date=None,
        ),
    )
    actual = as_terminated(obj, from_date=datetime(2011, 2, 3))
    expected = Model(
        uuid=uuid,
        validity=Validity(
            from_date=datetime(2010, 1, 2),
            to_date=datetime(2011, 2, 3),
        ),
    )
    assert actual == expected
