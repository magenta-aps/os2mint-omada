# SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

from collections import defaultdict

import structlog
from fastramqpi.raclients.modelclient.mo import ModelClient
from fastramqpi.ramqp.depends import handle_exclusively_decorator
from ramodels.mo import Employee

from os2mint_omada.mo import MO
from os2mint_omada.sync.models import ComparableMixin
from os2mint_omada.sync.models import StripUserKeyMixin

from .models import FrederikshavnOmadaUser

logger = structlog.stdlib.get_logger()


class ComparableEmployee(StripUserKeyMixin, ComparableMixin, Employee):
    @classmethod
    def from_omada(cls, omada_user: FrederikshavnOmadaUser) -> ComparableEmployee:
        """Construct (comparable) MO employee from a omada user.

        Args:
            omada_user: Omada user.

        Returns: Comparable MO employee.
        """
        return cls(  # type: ignore[call-arg]
            givenname=omada_user.first_name,
            surname=omada_user.last_name,
            cpr_no=omada_user.cpr_number,
        )


@handle_exclusively_decorator(key=lambda omada_user, *_, **__: omada_user.cpr_number)
async def sync_employee(
    omada_user: FrederikshavnOmadaUser,
    mo: MO,
    model_client: ModelClient,
) -> None:
    """Synchronise an Omada user to MO.

    Args:
        omada_user: Omada user to synchronise.

    Returns: None.
    """
    logger.info("Synchronising employee", omada_user=omada_user)

    # Find employee in MO
    employee_uuid = await mo.get_employee_uuid_from_cpr(omada_user.cpr_number)

    employee_states: set[Employee] = set()
    if employee_uuid is not None:
        employee_states = await mo.get_employee_states(uuid=employee_uuid)

    # Existing employee states in MO
    existing: defaultdict[ComparableEmployee, set[Employee]] = defaultdict(set)
    for mo_employee_state in employee_states:
        comparable_employee = ComparableEmployee(**mo_employee_state.dict())
        existing[comparable_employee].add(mo_employee_state)

    # Desired employee states from Omada (only one)
    desired = {ComparableEmployee.from_omada(omada_user)}

    # Delete excess existing
    # TODO: Implement when supported by MO

    # Create missing desired
    missing_comparable = desired - existing.keys()
    missing_mo = [
        Employee(uuid=employee_uuid, **employee.dict(exclude={"uuid"}))
        for employee in missing_comparable
    ]
    if missing_mo:
        logger.info("Creating missing Employeee states", employees=missing_mo)
        await model_client.upload(missing_mo)
