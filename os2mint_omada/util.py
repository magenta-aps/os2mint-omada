# SPDX-FileCopyrightText: 2021 Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from datetime import date
from typing import TypeVar

from ramodels.mo._shared import Validity
from ramodels.mo.details import Address
from ramodels.mo.details import ITSystemBinding

MOBaseWithValidity = TypeVar("MOBaseWithValidity", Address, ITSystemBinding)


def as_terminated(model: MOBaseWithValidity, from_date: date) -> MOBaseWithValidity:
    return model.copy(
        update=dict(
            validity=Validity(
                from_date=model.validity.from_date,
                to_date=from_date,
            ),
        )
    )
