# SPDX-FileCopyrightText: 2021 Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from fastapi import FastAPI

from os2mint_omada import api
from os2mint_omada.clients import client
from os2mint_omada.clients import lora_client


def create_app() -> FastAPI:
    app = FastAPI()

    app.include_router(api.router)

    @app.on_event("shutdown")
    async def close_httpx_clients() -> None:
        await client.aclose()
        await lora_client.aclose()

    return app
