# SPDX-FileCopyrightText: 2022 Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from typing import Any

import structlog
from aio_pika import IncomingMessage
from fastapi.encoders import jsonable_encoder
from pydantic import ValidationError
from ra_utils.asyncio_utils import with_concurrency
from ramqp import Router
from ramqp.mo import MORouter
from ramqp.mo.models import MORoutingKey
from ramqp.mo.models import ObjectType
from ramqp.mo.models import PayloadType as MOPayload
from ramqp.mo.models import RequestType
from ramqp.mo.models import ServiceType

from os2mint_omada.backing.omada.models import ManualOmadaUser
from os2mint_omada.backing.omada.models import OmadaUser
from os2mint_omada.backing.omada.routing_keys import Event
from os2mint_omada.backing.omada.routing_keys import PayloadType as OmadaPayloadType
from os2mint_omada.backing.omada.routing_keys import RoutingKey
from os2mint_omada.fail_db import FailDB
from os2mint_omada.models import Context
from os2mint_omada.sync.address import AddressSyncer
from os2mint_omada.sync.employee import EmployeeSyncer
from os2mint_omada.sync.engagement import EngagementSyncer
from os2mint_omada.sync.it_user import ITUserSyncer

logger = structlog.get_logger(__name__)
mo_router = MORouter()
omada_router = Router()


#######################################################################################
# Omada Raw
#######################################################################################
async def parse_omada_user(
    event: Event, message: IncomingMessage, context: Context, **_: Any
) -> None:
    """Parse raw omada user from the event generator.

    The user's identity category is identified, and the parsed user is sent back to
    the AMQP system under the related routing key, to be received below.

    Args:
        event: Create/Update/Delete event type.
        message: AMQP message containing the raw Omada user as body.
        context: ASGI lifespan context.
        **_: Additional kwargs, required for RAMQP forwards-compatibility.

    Returns: None.
    """
    # Parse user
    logger.debug("Handling raw omada user", raw=message.body)
    try:
        omada_user = OmadaUser.parse_raw(message.body)
    except ValidationError:
        logger.exception("Failed to parse user", raw=message.body)
        # We don't raise an error in this case, as we will never be able to parse this
        # user, so retrying delivery is never necessary.
        # TODO: Metrics?
        return
    logger.debug("Parsed Omada user", parsed=omada_user)

    # Publish parsed user to AMQP
    await context["omada_service"].amqp_system.publish_message(
        routing_key=RoutingKey(type=OmadaPayloadType.PARSED, event=event),
        payload=jsonable_encoder(omada_user.dict()),
    )


@omada_router.register(RoutingKey(type=OmadaPayloadType.RAW, event=Event.CREATE))
@with_concurrency(parallel=1)  # TODO
async def parse_raw_create(**kwargs: Any) -> None:
    """Handle create events for raw omada users from the event generator."""
    return await parse_omada_user(Event.CREATE, **kwargs)


@omada_router.register(RoutingKey(type=OmadaPayloadType.RAW, event=Event.UPDATE))
@with_concurrency(parallel=1)  # TODO
async def parse_raw_update(**kwargs: Any) -> None:
    """Handle update events for raw omada users from the event generator."""
    return await parse_omada_user(Event.UPDATE, **kwargs)


@omada_router.register(RoutingKey(type=OmadaPayloadType.RAW, event=Event.DELETE))
@with_concurrency(parallel=1)  # TODO
async def parse_raw_delete(**kwargs: Any) -> None:
    """Handle delete events for raw omada users from the event generator."""
    return await parse_omada_user(Event.DELETE, **kwargs)


#######################################################################################
# Omada Parsed
#######################################################################################
@omada_router.register(RoutingKey(type=OmadaPayloadType.PARSED, event=Event.CREATE))
@omada_router.register(RoutingKey(type=OmadaPayloadType.PARSED, event=Event.UPDATE))
@omada_router.register(RoutingKey(type=OmadaPayloadType.PARSED, event=Event.DELETE))
@with_concurrency(parallel=1)  # TODO
async def sync_omada_employee(
    message: IncomingMessage, context: Context, **_: Any
) -> None:
    """Synchronise a manual Omada user to a MO employee.

    Args:
        message: AMQP message containing the parsed Omada user as body.
        context: ASGI lifespan context.
        **_: Additional kwargs, required for RAMQP forwards-compatibility.

    Returns: None.
    """
    try:
        omada_user = ManualOmadaUser.parse_raw(message.body)
    except ValidationError:
        # User is not manual, so we have nothing to do
        return
    await EmployeeSyncer(
        settings=context["settings"].mo,
        mo_service=context["mo_service"],
        omada_service=context["omada_service"],
    ).sync(omada_user)


@omada_router.register(RoutingKey(type=OmadaPayloadType.PARSED, event=Event.CREATE))
@omada_router.register(RoutingKey(type=OmadaPayloadType.PARSED, event=Event.UPDATE))
@omada_router.register(RoutingKey(type=OmadaPayloadType.PARSED, event=Event.DELETE))
@with_concurrency(parallel=1)  # TODO
async def sync_omada_engagements(
    message: IncomingMessage, context: Context, **_: Any
) -> None:
    """Synchronise a manual Omada user to a MO engagements.

    Args:
        message: AMQP message containing the parsed Omada user as body.
        context: ASGI lifespan context.
        **_: Additional kwargs, required for RAMQP forwards-compatibility.

    Returns: None.
    """
    try:
        omada_user = ManualOmadaUser.parse_raw(message.body)
    except ValidationError:
        # User is not manual, so we have nothing to do
        return

    # Find employee in MO
    employee_uuid = await context["mo_service"].get_employee_uuid_from_cpr(
        omada_user.cpr_number
    )
    if employee_uuid is None:
        logger.info("No employee in MO: skipping engagements synchronisation")
        return

    # TODO: Remove this try-catch crap
    #  Should be handled by os2mo-amqp-trigger-failures and the FastRAMQPI library
    try:
        await EngagementSyncer(
            settings=context["settings"].mo,
            mo_service=context["mo_service"],
            omada_service=context["omada_service"],
        ).sync(employee_uuid)
    except Exception as e:
        logger.exception(
            "Failed to synchronise omada engagement",
            omada_user=omada_user,
            employee_uuid=employee_uuid,
        )
        FailDB(settings=context["settings"]).add(omada_user=omada_user, exception=e)


@omada_router.register(RoutingKey(type=OmadaPayloadType.PARSED, event=Event.CREATE))
@omada_router.register(RoutingKey(type=OmadaPayloadType.PARSED, event=Event.UPDATE))
@omada_router.register(RoutingKey(type=OmadaPayloadType.PARSED, event=Event.DELETE))
@with_concurrency(parallel=1)  # TODO
async def sync_omada_addresses(
    message: IncomingMessage, context: Context, **_: Any
) -> None:
    """Synchronise an Omada user's addresses to MO.

    Args:
        message: AMQP message containing the parsed Omada user as body.
        context: ASGI lifespan context.
        **_: Additional kwargs, required for RAMQP forwards-compatibility.

    Returns: None.
    """
    omada_user: OmadaUser = OmadaUser.parse_raw(message.body)

    # Find employee in MO
    employee_uuid = await context["mo_service"].get_employee_uuid_from_service_number(
        omada_user.service_number
    )
    if employee_uuid is None:
        logger.info("No employee in MO: skipping addresses synchronisation")
        return

    await AddressSyncer(
        settings=context["settings"].mo,
        mo_service=context["mo_service"],
        omada_service=context["omada_service"],
    ).sync(employee_uuid)


@omada_router.register(RoutingKey(type=OmadaPayloadType.PARSED, event=Event.CREATE))
@omada_router.register(RoutingKey(type=OmadaPayloadType.PARSED, event=Event.UPDATE))
@omada_router.register(RoutingKey(type=OmadaPayloadType.PARSED, event=Event.DELETE))
@with_concurrency(parallel=1)  # TODO
async def sync_omada_it_users(
    message: IncomingMessage, context: Context, **_: Any
) -> None:
    """Synchronise an Omada user to MO IT users.

    Args:
        message: AMQP message containing the parsed Omada user as body.
        context: ASGI lifespan context.
        **_: Additional kwargs, required for RAMQP forwards-compatibility.

    Returns: None.
    """
    omada_user: OmadaUser = OmadaUser.parse_raw(message.body)

    # Find employee in MO
    employee_uuid = await context["mo_service"].get_employee_uuid_from_service_number(
        omada_user.service_number
    )
    if employee_uuid is None:
        logger.info("No employee in MO: skipping IT user synchronisation")
        return

    await ITUserSyncer(
        settings=context["settings"].mo,
        mo_service=context["mo_service"],
        omada_service=context["omada_service"],
    ).sync(employee_uuid)


#######################################################################################
# MO
#######################################################################################
# TODO: MO ITUsers and Addresses are not watched since the Omada integration is
#  authoritative for these objects, so we do not expect them to be modified. This
#  invariant should be enforced by RBAC.

# TODO: Engagements for manual Omada users are created in the organisational unit with
#  an IT user on the unit containing the UUID of the 'org_unit'/'C_ORGANISATIONSKODE'
#  attribute of the Omada user, and as a fallback on the org unit with the given UUID
#  directly. For this reason, we should also watch changes to IT users on org units,
#  as well as the creation of org units themselves (for the fallback).
#  For now, however, it is assumed that all organisational unit are created in MO
#  before the users appear in Omada.


@mo_router.register(
    MORoutingKey(
        service_type=ServiceType.EMPLOYEE,
        object_type=ObjectType.EMPLOYEE,
        request_type=RequestType.WILDCARD,
    )
)
@with_concurrency(parallel=1)  # TODO
async def sync_mo_engagements(payload: MOPayload, context: Context, **_: Any) -> None:
    """Synchronise a MO user's engagements with Omada.

    Args:
        payload: MOAMQP message payload containing the affected objects.
        context: ASGI lifespan context.
        **_: Additional kwargs, required for RAMQP forwards-compatibility.

    Returns: None.
    """
    employee_uuid = payload.uuid
    await EngagementSyncer(
        settings=context["settings"].mo,
        mo_service=context["mo_service"],
        omada_service=context["omada_service"],
    ).sync(employee_uuid)


@mo_router.register(
    MORoutingKey(
        service_type=ServiceType.EMPLOYEE,
        object_type=ObjectType.ENGAGEMENT,
        request_type=RequestType.WILDCARD,
    )
)
@with_concurrency(parallel=1)  # TODO
async def sync_mo_addresses(payload: MOPayload, context: Context, **_: Any) -> None:
    """Synchronise a MO user's addresses with Omada.

    Args:
        payload: MOAMQP message payload containing the affected objects.
        context: ASGI lifespan context.
        **_: Additional kwargs, required for RAMQP forwards-compatibility.

    Returns: None.
    """
    employee_uuid = payload.uuid
    await AddressSyncer(
        settings=context["settings"].mo,
        mo_service=context["mo_service"],
        omada_service=context["omada_service"],
    ).sync(employee_uuid)


@mo_router.register(
    MORoutingKey(
        service_type=ServiceType.EMPLOYEE,
        object_type=ObjectType.ENGAGEMENT,
        request_type=RequestType.WILDCARD,
    )
)
@with_concurrency(parallel=1)  # TODO
async def sync_mo_it_users(payload: MOPayload, context: Context, **_: Any) -> None:
    """Synchronise a MO user's IT users with Omada.

    Args:
        payload: MOAMQP message payload containing the affected objects.
        context: ASGI lifespan context.
        **_: Additional kwargs, required for RAMQP forwards-compatibility.

    Returns: None.
    """
    employee_uuid = payload.uuid
    await ITUserSyncer(
        settings=context["settings"].mo,
        mo_service=context["mo_service"],
        omada_service=context["omada_service"],
    ).sync(employee_uuid)
