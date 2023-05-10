# SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0

import structlog
from fastapi import APIRouter
from os2mint_omada.backing.omada.routing_keys import Event
from os2mint_omada.models import Context
from starlette import status
from starlette.requests import Request

router = APIRouter()
logger = structlog.get_logger(__name__)


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
            routing_key=Event.REFRESH,
            payload=raw_omada_user,
        )
