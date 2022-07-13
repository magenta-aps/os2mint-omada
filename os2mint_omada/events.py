# SPDX-FileCopyrightText: 2022 Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from typing import Any
from typing import Union

import structlog
from aio_pika import IncomingMessage
from fastapi.encoders import jsonable_encoder
from pydantic import parse_raw_as
from pydantic import ValidationError
from ra_utils.asyncio_utils import with_concurrency
from ramqp import Router
from ramqp.mo import MORouter
from ramqp.mo.models import MORoutingKey
from ramqp.mo.models import ObjectType
from ramqp.mo.models import PayloadType
from ramqp.mo.models import RequestType
from ramqp.mo.models import ServiceType

from os2mint_omada.backing.omada.models import ManualOmadaUser
from os2mint_omada.backing.omada.models import OmadaUser
from os2mint_omada.backing.omada.routing_keys import Event
from os2mint_omada.backing.omada.routing_keys import IdentityCategory
from os2mint_omada.backing.omada.routing_keys import ParsedRoutingKey
from os2mint_omada.backing.omada.routing_keys import RawRoutingKey
from os2mint_omada.models import Context

logger = structlog.get_logger(__name__)
mo_router = MORouter()
omada_router = Router()


#######################################################################################
# Omada Raw
#######################################################################################
async def parse_omada_user(
    event: Event, message: IncomingMessage, context: Context, **_: Any
) -> None:
    # Parse user
    logger.debug("Handling raw omada user", raw=message.body)
    try:
        omada_user: ManualOmadaUser | OmadaUser = parse_raw_as(
            Union[ManualOmadaUser, OmadaUser], message.body  # type: ignore[arg-type]
        )
    except ValidationError:
        logger.exception("Failed to parse user", raw=message.body)
        return
    if isinstance(omada_user, ManualOmadaUser):
        identity_category = IdentityCategory.MANUAL
    else:
        identity_category = IdentityCategory.NORMAL
    logger.debug("Parsed Omada user", parsed=omada_user)

    # Publish parsed user to AMQP
    routing_key = ParsedRoutingKey(event=event, identity_category=identity_category)
    await context["omada_service"].amqp_system.publish_message(
        routing_key=routing_key,
        payload=jsonable_encoder(omada_user.dict()),
    )


@omada_router.register(RawRoutingKey(event=Event.CREATE))
@with_concurrency(parallel=1)
async def omada_raw_create(**kwargs: Any) -> None:
    return await parse_omada_user(Event.CREATE, **kwargs)


@omada_router.register(RawRoutingKey(event=Event.UPDATE))
@with_concurrency(parallel=1)
async def omada_raw_update(**kwargs: Any) -> None:
    return await parse_omada_user(Event.UPDATE, **kwargs)


@omada_router.register(RawRoutingKey(event=Event.DELETE))
@with_concurrency(parallel=1)
async def omada_raw_delete(**kwargs: Any) -> None:
    return await parse_omada_user(Event.DELETE, **kwargs)


#######################################################################################
# Omada Parsed Normal
#######################################################################################
@omada_router.register(
    ParsedRoutingKey(event=Event.CREATE, identity_category=IdentityCategory.NORMAL)
)
@omada_router.register(
    ParsedRoutingKey(event=Event.UPDATE, identity_category=IdentityCategory.NORMAL)
)
@omada_router.register(
    ParsedRoutingKey(event=Event.DELETE, identity_category=IdentityCategory.NORMAL)
)
@with_concurrency(parallel=1)
async def omada_parsed(message: IncomingMessage, context: Context, **_: Any) -> None:
    logger.debug("Handling parsed normal omada user", user=message.body)
    omada_user = OmadaUser.parse_raw(message.body)
    employee_uuid = await context["mo_service"].get_employee_uuid_from_service_number(
        omada_user.service_number
    )
    if employee_uuid is None:
        logger.info(
            "No employee in MO: skipping", service_number=omada_user.service_number
        )
        return
    await context["syncer"].sync_employee_data(uuid=employee_uuid)


#######################################################################################
# Omada Parsed Manual
#######################################################################################
@omada_router.register(
    ParsedRoutingKey(event=Event.CREATE, identity_category=IdentityCategory.MANUAL)
)
@omada_router.register(
    ParsedRoutingKey(event=Event.CREATE, identity_category=IdentityCategory.MANUAL)
)
@omada_router.register(
    ParsedRoutingKey(event=Event.DELETE, identity_category=IdentityCategory.MANUAL)
)
@with_concurrency(parallel=1)
async def omada_parsed_manual(
    message: IncomingMessage, context: Context, **_: Any
) -> None:
    logger.debug("Handling parsed manual omada user", user=message.body)
    omada_user = ManualOmadaUser.parse_raw(message.body)
    await context["syncer"].sync_manual_employee(omada_user)


#######################################################################################
# MO
#######################################################################################
# MO ITUsers and Addresses are not watched since the Omada integration is authoritative
# for these objects, so we do not expect them to be modified.
# This invariant should be enforced by RBAC.
@mo_router.register(
    MORoutingKey(
        service_type=ServiceType.EMPLOYEE,
        object_type=ObjectType.ENGAGEMENT,
        request_type=RequestType.WILDCARD,
    )
)
@with_concurrency(parallel=1)
async def mo_engagement(payload: PayloadType, context: Context, **_: Any) -> None:
    employee_uuid = payload.uuid
    logger.debug(
        "Handling MO engagement", employee=employee_uuid, engagement=payload.uuid
    )
    await context["syncer"].sync_employee_data(uuid=employee_uuid)
