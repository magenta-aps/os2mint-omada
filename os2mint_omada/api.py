# SPDX-FileCopyrightText: 2021 Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
import asyncio
from uuid import UUID

import structlog
from fastapi import APIRouter
from fastapi import Response
from starlette import status
from starlette.requests import Request

from os2mint_omada.backing.mo.service import MOService
from os2mint_omada.backing.omada.service import OmadaService
from os2mint_omada.config import MoSettings
from os2mint_omada.models import Context
from os2mint_omada.sync.address import AddressSyncer
from os2mint_omada.sync.engagement import EngagementSyncer
from os2mint_omada.sync.it_user import ITUserSyncer

router = APIRouter()
logger = structlog.get_logger(__name__)


@router.get(
    "/health/ready",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_204_NO_CONTENT: {"description": "Ready"},
        status.HTTP_503_SERVICE_UNAVAILABLE: {"description": "Not ready"},
    },
)
async def readiness_probe(response: Response, request: Request) -> None:
    """Kubernetes readiness probe endpoint."""
    context: Context = request.app.state.context
    ready_checks = (
        context["mo_service"].is_ready(),
        context["omada_service"].is_ready(),
    )
    if not all(await asyncio.gather(*ready_checks)):
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE


@router.post("/sync/mo", status_code=status.HTTP_204_NO_CONTENT)
async def sync_mo(request: Request) -> None:
    """Force-synchronise all MO employees with Omada."""
    logger.info("Synchronising all MO employees")
    context: Context = request.app.state.context
    employees = await context["mo_service"].get_employees()
    for i, employee_uuid in enumerate(employees):
        logger.debug("Synchronising MO user", current=i, total=len(employees))
        try:
            await sync_employee(
                employee_uuid=employee_uuid,
                mo_settings=context["settings"].mo,
                mo_service=context["mo_service"],
                omada_service=context["omada_service"],
            )
        except Exception:
            logger.exception(
                "Failed to synchronise MO user", employee_uuid=employee_uuid
            )


async def sync_employee(
    employee_uuid: UUID,
    mo_settings: MoSettings,
    mo_service: MOService,
    omada_service: OmadaService,
) -> None:
    """Synchronise a MO employee with Omada.

    Args:
        employee_uuid: MO employee UUID.
        mo_settings: MO-specific settings.
        mo_service: MO service.
        omada_service: Omada service.

    Returns: None.
    """
    logger.info("Synchronising MO employee", employee_uuid=employee_uuid)
    await EngagementSyncer(
        settings=mo_settings,
        mo_service=mo_service,
        omada_service=omada_service,
    ).sync(employee_uuid)
    await AddressSyncer(
        settings=mo_settings,
        mo_service=mo_service,
        omada_service=omada_service,
    ).sync(employee_uuid)
    await ITUserSyncer(
        settings=mo_settings,
        mo_service=mo_service,
        omada_service=omada_service,
    ).sync(employee_uuid)
