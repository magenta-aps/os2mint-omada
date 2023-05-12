# SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from contextlib import asynccontextmanager
from typing import Any
from typing import AsyncGenerator

from fastapi import FastAPI
from fastramqpi.main import FastRAMQPI
from ramqp import AMQPSystem

from os2mint_omada import api
from os2mint_omada.config import Settings
from os2mint_omada.mo import MO
from os2mint_omada.omada.api import create_client
from os2mint_omada.omada.api import OmadaAPI
from os2mint_omada.omada.event_generator import OmadaEventGenerator
from os2mint_omada.sync.frederikshavn.events import mo_router as frederikshavn_mo_router
from os2mint_omada.sync.frederikshavn.events import (
    omada_router as frederikshavn_omada_router,
)
from os2mint_omada.sync.silkeborg.events import mo_router as silkeborg_mo_router
from os2mint_omada.sync.silkeborg.events import omada_router as silkeborg_omada_router


def create_app(**kwargs: Any) -> FastAPI:
    """FastRAMQPI application factory.

    Args:
        **kwargs: Additional keyword arguments passed to the settings module.

    Returns: FastAPI application.
    """
    settings = Settings(**kwargs)
    fastramqpi = FastRAMQPI(application_name="omada", settings=settings.fastramqpi)
    fastramqpi.add_context(settings=settings)
    context = fastramqpi.get_context()

    match settings.customer:
        case "frederikshavn":
            mo_router = frederikshavn_mo_router
            omada_router = frederikshavn_omada_router
        case "silkeborg":
            mo_router = silkeborg_mo_router
            omada_router = silkeborg_omada_router
        case _:
            raise ValueError("Improperly configured")

    # FastAPI router
    app = fastramqpi.get_app()
    app.include_router(api.router)

    # MO AMQP
    mo_amqp_system = fastramqpi.get_amqpsystem()
    mo_amqp_system.router.registry.update(mo_router.registry)

    # MO API
    @asynccontextmanager
    async def mo_api() -> AsyncGenerator[None, None]:
        mo = MO(graphql_session=context["graphql_session"])
        fastramqpi.add_context(mo=mo)
        yield

    # priority ensures we start mo api after the graphql_session has been started
    fastramqpi.add_lifespan_manager(mo_api(), priority=1100)

    # Omada AMQP
    omada_amqp_system = AMQPSystem(
        settings=settings.omada.amqp,
        router=omada_router,
        context=context,
    )
    fastramqpi.add_context(omada_amqp_system=omada_amqp_system)
    fastramqpi.add_lifespan_manager(omada_amqp_system, priority=1200)

    # Omada API
    omada_client = create_client(settings.omada)
    # priority ensures the client is started before the event generator tries to use it
    fastramqpi.add_lifespan_manager(omada_client, priority=1300)
    omada_api = OmadaAPI(omada_client)
    fastramqpi.add_context(omada_api=omada_api)

    # Omada event generator
    omada_event_generator = OmadaEventGenerator(
        settings=settings.omada,
        api=omada_api,
        amqp_system=omada_amqp_system,
    )
    fastramqpi.add_lifespan_manager(omada_event_generator, priority=1400)

    return app
