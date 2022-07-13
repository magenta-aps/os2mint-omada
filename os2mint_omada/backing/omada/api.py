# SPDX-FileCopyrightText: 2021 Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

import asyncio
from contextlib import AbstractAsyncContextManager
from contextlib import AsyncExitStack
from types import TracebackType
from typing import Any
from typing import Iterable
from typing import Type

import httpx
import structlog
from httpx import AsyncClient
from httpx_ntlm import HttpNtlmAuth
from more_itertools import flatten

from os2mint_omada.backing.omada.models import RawOmadaUser
from os2mint_omada.config import OmadaSettings

logger = structlog.get_logger(__name__)


class OmadaAPI(AbstractAsyncContextManager):
    def __init__(self, settings: OmadaSettings) -> None:
        super().__init__()
        self.settings = settings

        self.stack = AsyncExitStack()

    async def __aenter__(self) -> OmadaAPI:
        settings = self.settings

        # HTTPX Client
        client_kwargs: dict[str, Any] = {}
        if settings.host_header:
            client_kwargs["headers"] = {"Host": settings.host_header}
        if any((settings.ntlm_username, settings.ntlm_password)):
            client_kwargs["auth"] = HttpNtlmAuth(
                username=settings.ntlm_username,
                password=settings.ntlm_password,
            )
        if settings.insecure_skip_ssl_verify:
            logger.warning("INSECURE: Skipping SSL verification for Omada API!")
            client_kwargs["verify"] = False

        logger.info("Setting up Omada API", client_kwargs=client_kwargs)
        client = httpx.AsyncClient(timeout=30, **client_kwargs)
        self.client: AsyncClient = await self.stack.enter_async_context(client)

        return await super().__aenter__()

    async def __aexit__(
        self,
        __exc_type: Type[BaseException] | None,
        __exc_value: BaseException | None,
        __traceback: TracebackType | None,
    ) -> bool | None:
        logger.info("Closing Omada API")
        await self.stack.aclose()
        return await super().__aexit__(__exc_type, __exc_value, __traceback)

    async def is_ready(self) -> bool:
        """Check the connection to Omada's API.

        Returns: Whether the connection can be made.
        """
        try:
            response = await self.client.head(self.settings.url)
            response.raise_for_status()
            return True
        except Exception:  # pylint: disable=broad-except
            logger.exception("Exception occurred during Omada healthcheck")
        return False

    async def get_users(self, params: dict | None = None) -> list[RawOmadaUser]:
        url = self.settings.url
        logger.info("Getting Omada IT users", odata_url=url, params=params)
        response = await self.client.get(url, params=params)
        response.raise_for_status()
        users = response.json()["value"]
        return users

    async def _get_users_by(
        self, key: str, values: Iterable[str]
    ) -> list[RawOmadaUser]:
        # Omada does not support OR or IN operators, so we have to do it like this
        get_users = (
            self.get_users(params={"$filter": f"{key} eq '{value}'"})
            for value in values
        )
        users = await asyncio.gather(*get_users)
        return list(flatten(users))

    async def get_users_by_service_numbers(
        self, service_numbers: Iterable[str]
    ) -> list[RawOmadaUser]:
        return await self._get_users_by("C_TJENESTENR", service_numbers)

    async def get_users_by_cpr_numbers(
        self, cpr_numbers: Iterable[str]
    ) -> list[RawOmadaUser]:
        return await self._get_users_by("C_CPRNR", cpr_numbers)
