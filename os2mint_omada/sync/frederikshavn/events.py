# SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from uuid import UUID

import structlog
from fastapi import APIRouter
from fastapi import Depends
from fastramqpi.events import Event
from fastramqpi.events import Listener
from fastramqpi.ramqp import Router
from fastramqpi.ramqp.depends import rate_limit
from fastramqpi.ramqp.utils import AcknowledgeMessage
from pydantic import ValidationError

from os2mint_omada.omada.event_generator import OmadaEvent
from os2mint_omada.omada.models import OmadaUser

from ... import depends
from ...depends import CurrentOmadaUser
from .address import sync_addresses
from .employee import sync_employee
from .engagement import sync_engagements
from .it_user import sync_it_users
from .models import FrederikshavnOmadaUser

logger = structlog.stdlib.get_logger()
mo_router = APIRouter()
omada_router = Router()

# MO GraphQL event listeners declared by the integration. The `subject` of each
# event is the UUID of the changed object, which we resolve to the affected
# employee before synchronising.
mo_listeners = [
    Listener(
        namespace="mo",
        user_key="person",
        routing_key="person",
        path="/events/mo/person",
    ),
    Listener(
        namespace="mo",
        user_key="engagement",
        routing_key="engagement",
        path="/events/mo/engagement",
    ),
]


def parse_user(omada_user: OmadaUser) -> FrederikshavnOmadaUser:
    try:
        return FrederikshavnOmadaUser.parse_obj(omada_user)
    except ValidationError as exc:
        # A lot of Omada-users in Frederikshavn have a bad CPR-number. Ignore
        # them so it doesn't block the synchronisation of proper users.
        if all(e["loc"] == ("C_CPRNUMBER",) for e in exc.errors()):
            logger.warning(
                "Failed to parse user: ignoring",
                user=omada_user,
                exc=exc,
            )
            raise AcknowledgeMessage()
        raise


#######################################################################################
# Omada
#######################################################################################
@omada_router.register(OmadaEvent.WILDCARD, dependencies=[Depends(rate_limit())])
async def sync_omada_employee(
    current_omada_user: CurrentOmadaUser,
    mo: depends.MO,
) -> None:
    omada_user = parse_user(current_omada_user)
    await sync_employee(
        omada_user=omada_user,
        mo=mo,
    )


@omada_router.register(OmadaEvent.WILDCARD, dependencies=[Depends(rate_limit())])
async def sync_omada_engagements(
    current_omada_user: CurrentOmadaUser,
    mo: depends.MO,
    omada_api: depends.OmadaAPI,
) -> None:
    omada_user = parse_user(current_omada_user)

    # Find employee in MO
    employee_uuid = await mo.get_employee_uuid_from_cpr(omada_user.cpr_number)
    if employee_uuid is None:
        logger.info("No employee in MO: skipping engagements synchronisation")
        return

    await sync_engagements(
        employee_uuid=employee_uuid,
        mo=mo,
        omada_api=omada_api,
    )


@omada_router.register(OmadaEvent.WILDCARD, dependencies=[Depends(rate_limit())])
async def sync_omada_addresses(
    current_omada_user: CurrentOmadaUser,
    mo: depends.MO,
    omada_api: depends.OmadaAPI,
) -> None:
    omada_user = parse_user(current_omada_user)

    # Find employee in MO
    employee_uuid = await mo.get_employee_uuid_from_cpr(omada_user.cpr_number)
    if employee_uuid is None:
        logger.info("No employee in MO: skipping addresses synchronisation")
        return

    await sync_addresses(
        employee_uuid=employee_uuid,
        mo=mo,
        omada_api=omada_api,
    )


@omada_router.register(OmadaEvent.WILDCARD, dependencies=[Depends(rate_limit())])
async def sync_omada_it_users(
    current_omada_user: CurrentOmadaUser,
    mo: depends.MO,
    omada_api: depends.OmadaAPI,
) -> None:
    omada_user = parse_user(current_omada_user)

    # Find employee in MO
    employee_uuid = await mo.get_employee_uuid_from_cpr(omada_user.cpr_number)
    if employee_uuid is None:
        logger.info("No employee in MO: skipping IT user synchronisation")
        return

    await sync_it_users(
        employee_uuid=employee_uuid,
        mo=mo,
        omada_api=omada_api,
    )


#######################################################################################
# MO
#######################################################################################
# TODO: MO ITUsers and Addresses are not watched since the Omada integration is
#  authoritative for these objects, so we do not expect them to be modified. This
#  invariant should be enforced by RBAC.


@mo_router.post("/events/mo/person")
async def sync_mo_engagements(
    event: Event[UUID],
    mo: depends.MO,
    omada_api: depends.OmadaAPI,
) -> None:
    employee_uuid = event.subject
    await sync_engagements(
        employee_uuid=employee_uuid,
        mo=mo,
        omada_api=omada_api,
    )


# In Frederikshavn both addresses and IT-users are linked to engagements, so
# both are synchronised in response to engagement events.
@mo_router.post("/events/mo/engagement")
async def sync_mo_addresses_and_it_users(
    event: Event[UUID],
    mo: depends.MO,
    omada_api: depends.OmadaAPI,
) -> None:
    employee_uuid = await mo.get_employee_uuid_from_engagement(event.subject)
    if employee_uuid is None:
        logger.info("No employee for engagement: skipping synchronisation")
        return
    await sync_addresses(
        employee_uuid=employee_uuid,
        mo=mo,
        omada_api=omada_api,
    )
    await sync_it_users(
        employee_uuid=employee_uuid,
        mo=mo,
        omada_api=omada_api,
    )
