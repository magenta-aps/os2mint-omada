# SPDX-FileCopyrightText: 2022 Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

from uuid import UUID

import structlog
from ramodels.mo import Employee
from ramqp.utils import handle_exclusively
from ramqp.utils import sleep_on_error

from os2mint_omada.backing.omada.models import ManualOmadaUser
from os2mint_omada.sync.base import ComparableMixin
from os2mint_omada.sync.base import StripUserKeyMixin
from os2mint_omada.sync.base import Syncer

logger = structlog.get_logger(__name__)


class ComparableEmployee(StripUserKeyMixin, ComparableMixin, Employee):
    @classmethod
    def from_omada(cls, omada_user: ManualOmadaUser) -> ComparableEmployee:
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


class EmployeeSyncer(Syncer):
    @handle_exclusively(key=lambda self, omada_user: omada_user.cpr_number)
    @sleep_on_error()
    async def sync(self, omada_user: ManualOmadaUser) -> None:
        """Synchronise an Omada user to MO.

        Args:
            omada_user: (Manual) Omada user to synchronise.

        Returns: None.
        """
        logger.info("Synchronising manual employee", omada_user=omada_user)

        # Find employee in MO
        employee_uuid = await self.mo_service.get_employee_uuid_from_cpr(
            omada_user.cpr_number
        )

        if employee_uuid is not None and self.settings.manual_employees_create_only:
            logger.info("Not modifying existing employee", employee_uuid=employee_uuid)
            return

        # Get employee objects from MO
        if employee_uuid is not None:
            employee_states = await self.mo_service.get_employee_states(
                uuid=employee_uuid
            )
        else:
            employee_states = set()

        await self.ensure_employee(
            omada_user=omada_user,
            employee_uuid=employee_uuid,
            employee_states=employee_states,
        )

    async def ensure_employee(
        self,
        omada_user: ManualOmadaUser,
        employee_uuid: UUID | None,
        employee_states: set[Employee],
    ) -> None:
        """Ensure that the MO employee is synchronised with the Omada user.

        Note that the employee objects are never deleted or terminated, as that is
        usually not done (some argue it being slightly morbid) -- and also not
        supported by MO (yet).

        Args:
            omada_user: Manual Omada user.
            employee_uuid: MO employee UUID. Can be None.
            employee_states: (Potentially) pre-existing MO employee states. Can be
             empty.

        Returns: None.
        """
        logger.info(
            "Ensuring employee",
            omada_user=omada_user,
            employee_uuid=employee_uuid,
        )
        # Actual employee states in MO
        actual: dict[ComparableEmployee, Employee] = {
            ComparableEmployee(**employee.dict()): employee
            for employee in employee_states
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
            await self.mo_service.model.upload(missing_mo_employee_states)
