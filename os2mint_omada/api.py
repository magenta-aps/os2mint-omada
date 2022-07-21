# SPDX-FileCopyrightText: 2021 Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
import asyncio

import structlog
from fastapi import APIRouter
from fastapi import Response
from starlette import status
from starlette.requests import Request

from os2mint_omada.models import Context
from os2mint_omada.sync.address import AddressSyncer
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
    """Force-synchronise all MO employees."""
    logger.info("Synchronising all MO employees")
    context: Context = request.app.state.context
    employees = await context["mo_service"].get_employees()
    for employee_uuid in employees:
        # Engagements are not synchronised to avoid deleting all of them for non-Omada
        # users.
        await AddressSyncer(
            settings=context["settings"].mo,
            mo_service=context["mo_service"],
            omada_service=context["omada_service"],
        ).sync(employee_uuid)
        await ITUserSyncer(
            settings=context["settings"].mo,
            mo_service=context["mo_service"],
            omada_service=context["omada_service"],
        ).sync(employee_uuid)
