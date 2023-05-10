# SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
import asyncio
from uuid import UUID

import structlog
from fastapi import APIRouter
from fastapi import Response
from starlette import status
from starlette.requests import Request

from os2mint_omada.backing.mo.service import MOService
from os2mint_omada.backing.omada.routing_keys import Event
from os2mint_omada.backing.omada.routing_keys import PayloadType as OmadaPayloadType
from os2mint_omada.backing.omada.routing_keys import RoutingKey
from os2mint_omada.backing.omada.service import OmadaService
from os2mint_omada.config import Settings
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
async def sync_mo(request: Request, employees: set[UUID] | None = None) -> None:
    """Force-synchronise MO employees with Omada.

    Synchronises all employees in MO if no list of UUIDs is given.
    """
    logger.info("Synchronising MO employees", employees=employees)
    context: Context = request.app.state.context
    if employees is None:
        employees = await context["mo_service"].get_all_employee_uuids()
    for i, uuid in enumerate(employees):
        logger.info("Synchronising MO user", current=i, total=len(employees))
        try:
            await sync_employee(
                employee_uuid=uuid,
                settings=context["settings"],
                mo_service=context["mo_service"],
                omada_service=context["omada_service"],
            )
        except Exception:
            logger.exception("Failed to synchronise MO user", employee_uuid=uuid)


@router.post("/sync/omada", status_code=status.HTTP_204_NO_CONTENT)
async def sync_omada(request: Request, omada_filter: str) -> None:
    """Force-synchronise Omada user(s) matching the given Omada filter."""
    logger.info("Synchronising Omada users", omada_filter=omada_filter)
    context: Context = request.app.state.context
    omada_service = context["omada_service"]

    raw_omada_users = await omada_service.api.get_users(omada_filter)
    logger.info("Synchronising raw Omada users", omada_users=raw_omada_users)
    for raw_omada_user in raw_omada_users:
        await omada_service.amqp_system.publish_message(
            routing_key=RoutingKey(type=OmadaPayloadType.RAW, event=Event.REFRESH),
            payload=raw_omada_user,
        )


async def sync_employee(
    employee_uuid: UUID,
    settings: Settings,
    mo_service: MOService,
    omada_service: OmadaService,
) -> None:
    """Synchronise a MO employee with Omada.

    Args:
        employee_uuid: MO employee UUID.
        settings: Configuration.
        mo_service: MO service.
        omada_service: Omada service.

    Returns: None.
    """
    logger.info("Synchronising MO employee", employee_uuid=employee_uuid)
    await EngagementSyncer(
        settings=settings,
        mo_service=mo_service,
        omada_service=omada_service,
    ).sync(employee_uuid)
    await AddressSyncer(
        settings=settings,
        mo_service=mo_service,
        omada_service=omada_service,
    ).sync(employee_uuid)
    await ITUserSyncer(
        settings=settings,
        mo_service=mo_service,
        omada_service=omada_service,
    ).sync(employee_uuid)
