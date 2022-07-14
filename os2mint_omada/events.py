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
        omada_user: ManualOmadaUser | OmadaUser = parse_raw_as(
            Union[ManualOmadaUser, OmadaUser], message.body  # type: ignore[arg-type]
        )
    except ValidationError:
        logger.exception("Failed to parse user", raw=message.body)
        # We don't raise an error in this case, as we will never be able to parse this
        # user, so retrying delivery is never necessary.
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
@with_concurrency(parallel=1)  # TODO
async def omada_raw_create(**kwargs: Any) -> None:
    """Handle create events for raw omada users from the event generator."""
    return await parse_omada_user(Event.CREATE, **kwargs)


@omada_router.register(RawRoutingKey(event=Event.UPDATE))
@with_concurrency(parallel=1)  # TODO
async def omada_raw_update(**kwargs: Any) -> None:
    """Handle update events for raw omada users from the event generator."""
    return await parse_omada_user(Event.UPDATE, **kwargs)


@omada_router.register(RawRoutingKey(event=Event.DELETE))
@with_concurrency(parallel=1)  # TODO
async def omada_raw_delete(**kwargs: Any) -> None:
    """Handle delete events for raw omada users from the event generator."""
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
@with_concurrency(parallel=1)  # TODO
async def omada_parsed(message: IncomingMessage, context: Context, **_: Any) -> None:
    """Handle all events for parsed non-manual Omada users from the parsing above.

    When a user (related to a single MO engagement) is changed in Omada, the associated
    employee is found in MO, and synchronisation on ALL of its engagements is invoked.
    This is needed since total knowledge of all of a user's Omada entries and MO
    objects is needed to avoid the termination of too many addresses/IT users.

    Args:
        message: AMQP message containing the parsed (normal) Omada user as body.
        context: ASGI lifespan context.
        **_: Additional kwargs, required for RAMQP forwards-compatibility.

    Returns: None.
    """
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
    await context["syncer"].sync_employee_data(employee_uuid=employee_uuid)


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
@with_concurrency(parallel=1)  # TODO
async def omada_parsed_manual(
    message: IncomingMessage, context: Context, **_: Any
) -> None:
    """Handle all events for parsed manual Omada users from the parsing above.

    Contrary to the handling of normal users, when a user identified as 'manual' is
    changed in Omada, we don't synchronise anything but the user's engagements. The
    synchronisation of related objects, such as addresses and IT users, will be
    triggered by the handler for MO engagements below.

    Args:
        message: AMQP message containing the parsed (manual) Omada user as body.
        context: ASGI lifespan context.
        **_: Additional kwargs, required for RAMQP forwards-compatibility.

    Returns: None.
    """
    logger.debug("Handling parsed manual omada user", user=message.body)
    omada_user = ManualOmadaUser.parse_raw(message.body)
    await context["syncer"].sync_manual_employee(omada_user)


#######################################################################################
# MO
#######################################################################################
# TODO: MO ITUsers and Addresses are not watched since the Omada integration is
#  authoritative for these objects, so we do not expect them to be modified. This
#  invariant should be enforced by RBAC.

# TODO: An employees and related engagement is always created together for manual Omada
#  users by this integration, but in case someone manually creates an employee we could
#  look up their CPR number in Omada and trigger synchronisation (creation) of
#  engagements for any matching (manual) Omada user.

# TODO: Engagements for manual Omada users are created in the organisational unit with
#  an IT user on the unit containing the UUID of the 'org_unit'/'C_ORGANISATIONSKODE'
#  attribute of the Omada user, and as a fallback on the org unit with the given UUID
#  directly. For this reason, we should also watch changes to IT users on org units,
#  as well as the creation of org units themselves (for the fallback).


@mo_router.register(
    MORoutingKey(
        service_type=ServiceType.EMPLOYEE,
        object_type=ObjectType.ENGAGEMENT,
        request_type=RequestType.WILDCARD,
    )
)
@with_concurrency(parallel=1)  # TODO
async def mo_engagement(payload: PayloadType, context: Context, **_: Any) -> None:
    """Handle all events for MO engagements.

    Args:
        payload: MOAMQP message payload containing the affected objects.
        context: ASGI lifespan context.
        **_: Additional kwargs, required for RAMQP forwards-compatibility.

    Returns: None.
    """
    # The MOAMQP message payload contains the 'uuid' of the org unit and 'object_uuid'
    # of the engagement.
    employee_uuid = payload.uuid
    logger.debug(
        "Handling MO engagement", employee=employee_uuid, engagement=payload.uuid
    )
    await context["syncer"].sync_employee_data(employee_uuid=employee_uuid)
