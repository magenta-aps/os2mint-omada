# SPDX-FileCopyrightText: 2021 Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
import asyncio

from fastapi import FastAPI

from os2mint_omada import api
from os2mint_omada import config
from os2mint_omada.clients import client
from os2mint_omada.clients import graphql_client
from os2mint_omada.clients import mo_client
from os2mint_omada.config import settings


def create_app() -> FastAPI:
    app = FastAPI()

    app.include_router(api.router)

    @app.on_event("startup")
    async def setup_logging() -> None:
        config.set_log_level(settings.log_level)

    @app.on_event("shutdown")
    async def close_clients() -> None:
        await asyncio.gather(
            client.aclose(),
            graphql_client.aclose(),
            mo_client.aclose(),
        )

    return app
