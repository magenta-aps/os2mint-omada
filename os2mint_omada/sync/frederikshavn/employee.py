# SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

import structlog
from raclients.modelclient.mo import ModelClient
from ramodels.mo import Employee
from ramqp.depends import handle_exclusively_decorator

from .models import ManualFrederikshavnOmadaUser
from os2mint_omada.mo import MO
from os2mint_omada.sync.models import ComparableMixin
from os2mint_omada.sync.models import StripUserKeyMixin

logger = structlog.get_logger(__name__)


class ComparableEmployee(StripUserKeyMixin, ComparableMixin, Employee):
    @classmethod
    def from_omada(cls, omada_user: ManualFrederikshavnOmadaUser) -> ComparableEmployee:
        """Construct (comparable) MO employee from a manual omada user.

        Args:
            omada_user: Manual omada user.

        Returns: Comparable MO employee.
        """
        return cls(  # type: ignore[call-arg]
            givenname=omada_user.first_name,
            surname=omada_user.last_name,
            cpr_no=omada_user.cpr_number,
        )


@handle_exclusively_decorator(key=lambda omada_user, *_, **__: omada_user.cpr_number)
async def sync_manual_employee(
    omada_user: ManualFrederikshavnOmadaUser,
    mo: MO,
    model_client: ModelClient,
) -> None:
    """Synchronise an Omada user to MO.

    Args:
        omada_user: (Manual) Omada user to synchronise.

    Returns: None.
    """
    logger.info("Synchronising manual employee", omada_user=omada_user)

    # Find employee in MO
    employee_uuid = await mo.get_employee_uuid_from_cpr(omada_user.cpr_number)

    if employee_uuid is not None:
        logger.info("Not modifying existing employee", employee_uuid=employee_uuid)
        return

    # Get employee objects from MO
    employee_states: set[Employee] = set()
    if employee_uuid is not None:
        employee_states = await mo.get_employee_states(uuid=employee_uuid)

    # Synchronise employee to MO
    logger.info("Ensuring employee", omada_user=omada_user, employee_uuid=employee_uuid)
    # Actual employee states in MO
    actual: dict[ComparableEmployee, Employee] = {
        ComparableEmployee(**employee.dict()): employee for employee in employee_states
    }

    # Expected employee states from Omada (only one)
    expected = {ComparableEmployee.from_omada(omada_user)}

    # Delete excess existing
    # TODO: Implement when supported by MO

    # Create (edit) missing
    missing_employee_states = expected - actual.keys()
    if missing_employee_states:
        missing_mo_employee_states = [
            Employee(uuid=employee_uuid, **employee.dict(exclude={"uuid"}))
            for employee in missing_employee_states
        ]
        logger.info(
            "Creating missing Employeee states",
            employees=missing_mo_employee_states,
        )
        await model_client.upload(missing_mo_employee_states)
