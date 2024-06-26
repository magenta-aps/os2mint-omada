# SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

from collections import defaultdict

import structlog
from fastramqpi.raclients.modelclient.mo import ModelClient
from fastramqpi.ramqp.depends import handle_exclusively_decorator
from ramodels.mo import Employee

from os2mint_omada.mo import MO
from os2mint_omada.omada.event_generator import Event
from os2mint_omada.sync.egedal.models import EgedalOmadaUser
from os2mint_omada.sync.egedal.models import ManualEgedalOmadaUser
from os2mint_omada.sync.models import ComparableMixin
from os2mint_omada.sync.models import StripUserKeyMixin

logger = structlog.get_logger(__name__)


class ComparableEmployee(StripUserKeyMixin, ComparableMixin, Employee):
    @classmethod
    def from_omada(cls, omada_user: ManualEgedalOmadaUser) -> ComparableEmployee:
        """Construct (comparable) MO employee from a omada user.

        Args:
            omada_user: Omada user.

        Returns: Comparable MO employee.
        """
        return cls(  # type: ignore[call-arg]
            givenname=omada_user.first_name,
            surname=omada_user.last_name,
            cpr_no=omada_user.cpr_number,
            nickname_givenname=omada_user.nickname_first_name,
            nickname_surname=omada_user.nickname_last_name,
        )


@handle_exclusively_decorator(key=lambda omada_user, *_, **__: omada_user.cpr_number)
async def sync_employee(
    omada_user: ManualEgedalOmadaUser,
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


@handle_exclusively_decorator(key=lambda omada_user, *_, **__: omada_user.cpr_number)
async def sync_employee_nickname(
    event: Event,
    omada_user: EgedalOmadaUser,
    mo: MO,
    model_client: ModelClient,
) -> None:
    """Synchronise Omada nicknames to pre-existing MO employees.

    Args:
        event: Omada event.
        omada_user: Omada user to synchronise.

    Returns: None.
    """
    logger.info("Synchronising employee nicknames", omada_user=omada_user)

    # Find employee in MO
    employee_uuid = await mo.get_employee_uuid_from_cpr(omada_user.cpr_number)
    if employee_uuid is None:
        return

    # Existing employee states in MO
    mo_employee_state = await mo.get_current_employee_state(uuid=employee_uuid)
    if mo_employee_state is None:
        return

    # Desired employee state with nickname from Omada
    if event == Event.DELETE:
        desired_nickname_givenname = None
        desired_nickname_surname = None
    else:
        desired_nickname_givenname = omada_user.nickname_first_name
        desired_nickname_surname = omada_user.nickname_last_name

    desired = mo_employee_state.copy(
        update=dict(
            nickname_givenname=desired_nickname_givenname,
            nickname_surname=desired_nickname_surname,
        )
    )

    # Create missing desired
    if mo_employee_state == desired:
        return
    logger.info("Creating Employeee state with missing nickname", employees=desired)
    await model_client.upload([desired])
