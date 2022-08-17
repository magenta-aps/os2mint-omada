# SPDX-FileCopyrightText: 2022 Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

import structlog
from ramodels.mo import Employee
from ramqp.utils import handle_exclusively

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
        return cls(
            givenname=omada_user.first_name,
            surname=omada_user.last_name,
            cpr_no=omada_user.cpr_number,
        )


class EmployeeSyncer(Syncer):
    @handle_exclusively(key=lambda self, omada_user: omada_user.cpr_number)
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

        # Get current user data from MO
        if employee_uuid is not None:
            employee = await self.mo_service.get_employee(uuid=employee_uuid)
        else:
            employee = None
        await self.ensure_employee(
            omada_user=omada_user,
            employee=employee,
        )

    async def ensure_employee(
        self, omada_user: ManualOmadaUser, employee: Employee | None
    ) -> None:
        """Ensure that the MO employee is synchronised with the Omada user.

        Note that the employee objects are never terminated, as that is usually not
        done (some argue it being slightly morbid).

        Args:
            omada_user: Manual Omada user.
            employee: (Potentially) pre-existing MO employee. Can be None.

        Returns: None.
        """
        logger.debug(
            "Ensuring employee",
            omada_user=omada_user,
            employee_uuid=getattr(employee, "uuid", None),
        )
        # Actual employee in MO
        if employee is not None:
            actual = ComparableEmployee(**employee.dict())
            uuid = employee.uuid
        else:
            actual = None
            uuid = None

        # Expected employee from Omada
        expected = ComparableEmployee.from_omada(omada_user)

        # Update if outdated
        if actual != expected:
            updated_employee = Employee(uuid=uuid, **expected.dict(exclude={"uuid"}))
            logger.info("Uploading employee", employee=updated_employee)
            await self.mo_service.model.upload([updated_employee])
