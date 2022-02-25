# SPDX-FileCopyrightText: 2021 Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
import asyncio
from typing import Any

import structlog
from fastapi import APIRouter
from fastapi import Response
from starlette.status import HTTP_429_TOO_MANY_REQUESTS

from os2mint_omada import mo
from os2mint_omada import omada
from os2mint_omada import sync
from os2mint_omada.clients import mo_model_client
from os2mint_omada.config import settings

router = APIRouter()
lock = asyncio.Lock()
logger = structlog.get_logger(__name__)


@router.post("/import/it-users")
async def import_it_users(response: Response) -> dict[str, Any]:
    """
    Import Omada IT users into MO.

    Returns: Dictionary of statistics.
    """
    logger.info("Starting Omada IT user import")
    if lock.locked():
        response.status_code = HTTP_429_TOO_MANY_REQUESTS
        return {"msg": "Already running"}

    async with lock:
        # Get user information from MO and Omada
        root_org_uuid = await mo.get_root_org()
        it_system_uuid = await mo.get_it_system_uuid(
            organisation_uuid=root_org_uuid,
            user_key=settings.it_system_user_key,
        )

        address_classes = await mo.get_classes(
            organisation_uuid=root_org_uuid,
            facet="employee_address_type",
        )
        visibility_classes = await mo.get_classes(
            organisation_uuid=root_org_uuid, facet="visibility"
        )
        mo_it_users = await mo.get_it_users(it_system_uuid)
        mo_user_addresses = await mo.get_user_addresses()
        mo_engagements = await mo.get_engagements()

        omada_it_users = await omada.get_it_users(
            odata_url=settings.odata_url,
            host_header=settings.omada_host_header,
            ntlm_username=settings.omada_ntlm_username,
            ntlm_password=settings.omada_ntlm_password,
        )

        # Synchronise updated objects to MO
        updated_objects = list(
            sync.get_updated_mo_objects(
                mo_it_users=mo_it_users,
                omada_it_users=omada_it_users,
                mo_user_addresses=mo_user_addresses,
                mo_engagements=mo_engagements,
                address_class_uuids=address_classes,
                it_system_uuid=it_system_uuid,
                address_visibility_uuid=visibility_classes["Intern"],
            )
        )
        logger.info("Uploading updates", num_changes=len(updated_objects))
        async with mo_model_client:
            mo_model_client.upload(updated_objects)

        logger.info("Finished importing IT users")
        return dict(
            num_updated_objects=len(updated_objects),
        )


@router.get("/ready")
async def readiness_probe() -> dict[str, str]:
    """
    Kubernetes readiness probe endpoint
    """
    return {"msg": "Omada API ready"}
