# SPDX-FileCopyrightText: 2021 Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from contextlib import AsyncExitStack
from functools import partial
from typing import Any

from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator
from ramqp import AMQPSystem
from ramqp.mo import MOAMQPSystem

from os2mint_omada import api
from os2mint_omada.backing.mo.service import MOService
from os2mint_omada.backing.omada.service import OmadaService
from os2mint_omada.config import configure_logging
from os2mint_omada.config import Settings
from os2mint_omada.events import mo_router
from os2mint_omada.events import omada_router
from os2mint_omada.models import Context


def create_app(*_: Any, **kwargs: Any) -> FastAPI:
    """FastAPI application factory.

    Args:
        **kwargs: Additional keyword arguments passed to the settings module.

    Returns: FastAPI application.
    """
    # Config
    settings = Settings(**kwargs)
    configure_logging(settings.log_level)
    context = Context(settings=settings)

    # AMQP
    mo_amqp_system = MOAMQPSystem(
        settings=settings.mo.amqp,
        router=mo_router,
        context=context,
    )
    omada_amqp_system = AMQPSystem(
        settings=settings.omada.amqp,
        router=omada_router,
        context=context,
    )

    # App
    app = FastAPI()
    app.state.context = context
    # Ideally, FastAPI would support the `lifespan=` keyword-argument like Starlette,
    # but that is not supported: https://github.com/tiangolo/fastapi/issues/2943.
    app.router.lifespan_context = partial(
        lifespan, settings, context, mo_amqp_system, omada_amqp_system
    )

    # Routes
    app.include_router(api.router)

    # Metrics
    if settings.enable_metrics:
        Instrumentator().instrument(app).expose(app)

    return app


@asynccontextmanager
async def lifespan(
    settings: Settings,
    context: Context,
    mo_amqp_system: MOAMQPSystem,
    omada_amqp_system: AMQPSystem,
    app: FastAPI,
) -> AsyncGenerator:
    async with AsyncExitStack() as stack:
        mo_service = context["mo_service"] = MOService(
            settings=settings.mo, amqp_system=mo_amqp_system
        )
        omada_service = context["omada_service"] = OmadaService(
            settings=settings.omada, amqp_system=omada_amqp_system
        )

        # Start services last to ensure the context is set up before handling events
        await stack.enter_async_context(mo_service)
        await stack.enter_async_context(omada_service)

        # Yield to keep the AMQP system open until the ASGI application is closed.
        # Control will be returned to here when the ASGI application is shut down.
        yield
