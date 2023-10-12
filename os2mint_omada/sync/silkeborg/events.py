# SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
import structlog
from pydantic import ValidationError
from ramqp import Router
from ramqp.depends import PayloadBytes
from ramqp.depends import RateLimit
from ramqp.mo import MORouter
from ramqp.mo import PayloadType

from ... import depends
from .address import sync_addresses
from .employee import sync_manual_employee
from .engagement import sync_engagements
from .it_user import sync_it_users
from .models import ManualSilkeborgOmadaUser
from .models import SilkeborgOmadaUser
from os2mint_omada.omada.event_generator import Event

logger = structlog.get_logger(__name__)
mo_router = MORouter()
omada_router = Router()


#######################################################################################
# Omada
#######################################################################################
@omada_router.register(Event.WILDCARD)
async def sync_omada_employee(
    body: PayloadBytes,
    mo: depends.MO,
    model_client: depends.ModelClient,
    _: RateLimit,
) -> None:
    """Synchronise an Omada user to a MO employee.

    Args:
        body: AMQP message body.
        mo: MO API.
        model_client: MO model client.

    Returns: None.
    """
    try:
        omada_user = SilkeborgOmadaUser.parse_raw(body)
        if not omada_user.is_manual:
            return
        manual_omada_user = ManualSilkeborgOmadaUser.parse_obj(omada_user)
    except ValidationError:
        # TODO (#51925): this message should be sent to the ghostoffice for manual
        # processing. For now, we simply drop the message, as we will never be able to
        # parse it without modifying the model.
        logger.exception("Failed to parse user", raw=body)
        return
    await sync_manual_employee(
        omada_user=manual_omada_user,
        mo=mo,
        model_client=model_client,
    )


@omada_router.register(Event.WILDCARD)
async def sync_omada_engagements(
    body: PayloadBytes,
    mo: depends.MO,
    omada_api: depends.OmadaAPI,
    model_client: depends.ModelClient,
    _: RateLimit,
) -> None:
    """Synchronise an Omada user to a MO engagements.

    Args:
        body: AMQP message body.
        mo: MO API.
        omada_api: Omada API.
        model_client: MO model client.

    Returns: None.
    """
    try:
        omada_user = SilkeborgOmadaUser.parse_raw(body)
        if not omada_user.is_manual:
            return
        manual_omada_user = ManualSilkeborgOmadaUser.parse_obj(omada_user)
    except ValidationError:
        # TODO (#51925): this message should be sent to the ghostoffice for manual
        # processing. For now, we simply drop the message, as we will never be able to
        # parse it without modifying the model.
        logger.exception("Failed to parse user", raw=body)
        return

    # Find employee in MO
    employee_uuid = await mo.get_employee_uuid_from_cpr(manual_omada_user.cpr_number)
    if employee_uuid is None:
        logger.info("No employee in MO: skipping engagements synchronisation")
        return

    await sync_engagements(
        employee_uuid=employee_uuid,
        mo=mo,
        omada_api=omada_api,
        model_client=model_client,
    )


@omada_router.register(Event.WILDCARD)
async def sync_omada_addresses(
    body: PayloadBytes,
    mo: depends.MO,
    omada_api: depends.OmadaAPI,
    model_client: depends.ModelClient,
    _: RateLimit,
) -> None:
    """Synchronise an Omada user's addresses to MO.

    Args:
        body: AMQP message body.
        mo: MO API.
        omada_api: Omada API.
        model_client: MO model client.

    Returns: None.
    """
    try:
        omada_user: SilkeborgOmadaUser = SilkeborgOmadaUser.parse_raw(body)
    except ValidationError:
        # TODO (#51925): this message should be sent to the ghostoffice for manual
        # processing. For now, we simply drop the message, as we will never be able to
        # parse it without modifying the model.
        logger.exception("Failed to parse user", raw=body)
        return

    # Find employee in MO
    employee_uuid = await mo.get_employee_uuid_from_user_key(omada_user.service_number)
    if employee_uuid is None:
        logger.info("No employee in MO: skipping addresses synchronisation")
        return

    await sync_addresses(
        employee_uuid=employee_uuid,
        mo=mo,
        omada_api=omada_api,
        model_client=model_client,
    )


@omada_router.register(Event.WILDCARD)
async def sync_omada_it_users(
    body: PayloadBytes,
    mo: depends.MO,
    omada_api: depends.OmadaAPI,
    model_client: depends.ModelClient,
    _: RateLimit,
) -> None:
    """Synchronise an Omada user to MO IT users.

    Args:
        body: AMQP message body.
        mo: MO API.
        omada_api: Omada API.
        model_client: MO model client.

    Returns: None.
    """
    try:
        omada_user: SilkeborgOmadaUser = SilkeborgOmadaUser.parse_raw(body)
    except ValidationError:
        # TODO (#51925): this message should be sent to the ghostoffice for manual
        # processing. For now, we simply drop the message, as we will never be able to
        # parse it without modifying the model.
        logger.exception("Failed to parse user", raw=body)
        return

    # Find employee in MO
    employee_uuid = await mo.get_employee_uuid_from_user_key(omada_user.service_number)
    if employee_uuid is None:
        logger.info("No employee in MO: skipping IT user synchronisation")
        return

    await sync_it_users(
        employee_uuid=employee_uuid,
        mo=mo,
        omada_api=omada_api,
        model_client=model_client,
    )


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


@mo_router.register("employee.employee.*")
async def sync_mo_engagements(
    payload: PayloadType,
    mo: depends.MO,
    omada_api: depends.OmadaAPI,
    model_client: depends.ModelClient,
    _: RateLimit,
) -> None:
    """Synchronise a MO user's engagements with Omada.

    Args:
        payload: MOAMQP message payload containing the affected objects.
        mo: MO API.
        omada_api: Omada API.
        model_client: MO model client.

    Returns: None.
    """
    employee_uuid = payload.uuid
    await sync_engagements(
        employee_uuid=employee_uuid,
        mo=mo,
        omada_api=omada_api,
        model_client=model_client,
    )


@mo_router.register("employee.engagement.*")
async def sync_mo_addresses(
    payload: PayloadType,
    mo: depends.MO,
    omada_api: depends.OmadaAPI,
    model_client: depends.ModelClient,
    _: RateLimit,
) -> None:
    """Synchronise a MO user's addresses with Omada.

    Args:
        payload: MOAMQP message payload containing the affected objects.
        mo: MO API.
        omada_api: Omada API.
        model_client: MO model client.

    Returns: None.
    """
    employee_uuid = payload.uuid
    await sync_addresses(
        employee_uuid=employee_uuid,
        mo=mo,
        omada_api=omada_api,
        model_client=model_client,
    )


@mo_router.register("employee.engagement.*")
async def sync_mo_it_users(
    payload: PayloadType,
    mo: depends.MO,
    omada_api: depends.OmadaAPI,
    model_client: depends.ModelClient,
    _: RateLimit,
) -> None:
    """Synchronise a MO user's IT users with Omada.

    Args:
        payload: MOAMQP message payload containing the affected objects.
        mo: MO API.
        omada_api: Omada API.
        model_client: MO model client.

    Returns: None.
    """
    employee_uuid = payload.uuid
    await sync_it_users(
        employee_uuid=employee_uuid,
        mo=mo,
        omada_api=omada_api,
        model_client=model_client,
    )
