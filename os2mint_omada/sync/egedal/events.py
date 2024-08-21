# SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
import structlog
from fastapi import Depends
from fastramqpi.depends import LegacyModelClient
from fastramqpi.ramqp import Router
from fastramqpi.ramqp.depends import RoutingKey
from fastramqpi.ramqp.depends import rate_limit
from fastramqpi.ramqp.mo import MORouter
from fastramqpi.ramqp.mo import PayloadType

from os2mint_omada.omada.event_generator import Event

from ... import depends
from ...depends import CurrentOmadaUser
from .address import sync_addresses
from .employee import sync_employee
from .employee import sync_employee_nickname
from .engagement import sync_engagements
from .it_user import sync_it_users
from .models import EgedalOmadaUser
from .models import ManualEgedalOmadaUser

logger = structlog.stdlib.get_logger()
mo_router = MORouter()
omada_router = Router()


#######################################################################################
# Omada
#######################################################################################
@omada_router.register(Event.WILDCARD, dependencies=[Depends(rate_limit())])
async def sync_omada_employee(
    current_omada_user: CurrentOmadaUser,
    mo: depends.MO,
    model_client: LegacyModelClient,
) -> None:
    # TODO: Dependency-inject user instead
    omada_user = EgedalOmadaUser.parse_obj(current_omada_user)
    if not omada_user.is_manual:
        return
    manual_omada_user = ManualEgedalOmadaUser.parse_obj(omada_user)

    await sync_employee(
        omada_user=manual_omada_user,
        mo=mo,
        model_client=model_client,
    )


@omada_router.register(Event.WILDCARD, dependencies=[Depends(rate_limit())])
async def sync_omada_employee_nicknames(
    routing_key: RoutingKey,
    current_omada_user: CurrentOmadaUser,
    mo: depends.MO,
    model_client: LegacyModelClient,
) -> None:
    # TODO: Dependency-inject user instead
    omada_user = EgedalOmadaUser.parse_obj(current_omada_user)
    if omada_user.is_manual:
        return

    await sync_employee_nickname(
        event=Event(routing_key),
        omada_user=omada_user,
        mo=mo,
        model_client=model_client,
    )


@omada_router.register(Event.WILDCARD, dependencies=[Depends(rate_limit())])
async def sync_omada_engagements(
    current_omada_user: CurrentOmadaUser,
    mo: depends.MO,
    omada_api: depends.OmadaAPI,
    model_client: LegacyModelClient,
) -> None:
    # TODO: Dependency-inject user instead
    omada_user = EgedalOmadaUser.parse_obj(current_omada_user)
    if not omada_user.is_manual:
        return
    manual_omada_user = ManualEgedalOmadaUser.parse_obj(omada_user)

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


@omada_router.register(Event.WILDCARD, dependencies=[Depends(rate_limit())])
async def sync_omada_addresses(
    current_omada_user: CurrentOmadaUser,
    mo: depends.MO,
    omada_api: depends.OmadaAPI,
    model_client: LegacyModelClient,
) -> None:
    # TODO: Dependency-inject user instead
    omada_user = EgedalOmadaUser.parse_obj(current_omada_user)

    # Find employee in MO
    employee_uuid = await mo.get_employee_uuid_from_cpr(omada_user.cpr_number)
    if employee_uuid is None:
        logger.info("No employee in MO: skipping addresses synchronisation")
        return

    await sync_addresses(
        employee_uuid=employee_uuid,
        mo=mo,
        omada_api=omada_api,
        model_client=model_client,
    )


@omada_router.register(Event.WILDCARD, dependencies=[Depends(rate_limit())])
async def sync_omada_it_users(
    current_omada_user: CurrentOmadaUser,
    mo: depends.MO,
    omada_api: depends.OmadaAPI,
    model_client: LegacyModelClient,
) -> None:
    # TODO: Dependency-inject user instead
    omada_user = EgedalOmadaUser.parse_obj(current_omada_user)

    # Find employee in MO
    employee_uuid = await mo.get_employee_uuid_from_cpr(omada_user.cpr_number)
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


@mo_router.register("employee.employee.*", dependencies=[Depends(rate_limit())])
async def sync_mo_engagements(
    payload: PayloadType,
    mo: depends.MO,
    omada_api: depends.OmadaAPI,
    model_client: LegacyModelClient,
) -> None:
    employee_uuid = payload.uuid
    await sync_engagements(
        employee_uuid=employee_uuid,
        mo=mo,
        omada_api=omada_api,
        model_client=model_client,
    )


@mo_router.register("employee.engagement.*", dependencies=[Depends(rate_limit())])
async def sync_mo_addresses(
    payload: PayloadType,
    mo: depends.MO,
    omada_api: depends.OmadaAPI,
    model_client: LegacyModelClient,
) -> None:
    employee_uuid = payload.uuid
    await sync_addresses(
        employee_uuid=employee_uuid,
        mo=mo,
        omada_api=omada_api,
        model_client=model_client,
    )


@mo_router.register("employee.engagement.*", dependencies=[Depends(rate_limit())])
async def sync_mo_it_users(
    payload: PayloadType,
    mo: depends.MO,
    omada_api: depends.OmadaAPI,
    model_client: LegacyModelClient,
) -> None:
    employee_uuid = payload.uuid
    await sync_it_users(
        employee_uuid=employee_uuid,
        mo=mo,
        omada_api=omada_api,
        model_client=model_client,
    )
