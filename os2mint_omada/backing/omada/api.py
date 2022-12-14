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

import structlog
from httpx import AsyncClient
from more_itertools import flatten
from raclients.auth import AuthenticatedAsyncHTTPXClient

from os2mint_omada.backing.omada.models import RawOmadaUser
from os2mint_omada.config import OmadaSettings

logger = structlog.get_logger(__name__)


class OmadaAPI(AbstractAsyncContextManager):
    def __init__(self, settings: OmadaSettings) -> None:
        """Facade for the Omada API.

        Args:
            settings: Omada-specific settings.
        """
        super().__init__()
        self.settings = settings
        self.stack = AsyncExitStack()

    async def __aenter__(self) -> OmadaAPI:
        """Setup and start the client for persistent connection to the Omada API."""
        settings = self.settings

        # HTTPX Client
        client_cls: Type[AsyncClient | AuthenticatedAsyncHTTPXClient] = AsyncClient
        client_kwargs: dict[str, Any] = {}
        if settings.host_header:
            client_kwargs["headers"] = {"Host": settings.host_header}
        if settings.oidc is not None:
            client_cls = AuthenticatedAsyncHTTPXClient
            client_kwargs.update(**settings.oidc.dict())
        if settings.insecure_skip_ssl_verify:
            logger.warning("INSECURE: Skipping SSL verification for Omada API!")
            client_kwargs["verify"] = False

        logger.info("Setting up Omada API", client_kwargs=client_kwargs)
        client = client_cls(timeout=30, **client_kwargs)
        self.client: AsyncClient = await self.stack.enter_async_context(client)

        return await super().__aenter__()

    async def __aexit__(
        self,
        __exc_type: Type[BaseException] | None,
        __exc_value: BaseException | None,
        __traceback: TracebackType | None,
    ) -> bool | None:
        """Close the connection to the Oamda API."""
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
        """Retrieve IT users from Omada.

        Args:
            params: Additional parameters passed to the HTTPX client request.

        Returns: List of raw omada users (dicts).
        """
        url = self.settings.url
        logger.info("Getting Omada IT users", odata_url=url, params=params)
        response = await self.client.get(url, params=params)
        response.raise_for_status()
        users = response.json()["value"]
        logger.debug("Retrieved Omada IT users", users=users)
        return users

    async def get_users_by(self, key: str, values: Iterable[str]) -> list[RawOmadaUser]:
        """Convenience wrapper for filtering on multiple criteria simultaneously.

        Args:
            key: Filter key.
            values: Filter value.

        Returns: List of raw omada users matching the filter.
        """
        # Omada does not support OR or IN operators, so we have to do it like this
        get_users = (
            self.get_users(params={"$filter": f"{key} eq {value}"}) for value in values
        )
        users = await asyncio.gather(*get_users)
        return list(flatten(users))

    async def get_users_by_service_numbers(
        self, service_numbers: Iterable[str]
    ) -> list[RawOmadaUser]:
        """Retrieve IT users with the given service number ("C_TJENESTENR").

        Args:
            service_numbers: Service number to retrieve users for.

        Returns: List of raw omada users with the given service number.
        """
        service_number_strings = (f"'{n}'" for n in service_numbers)
        return await self.get_users_by("C_TJENESTENR", service_number_strings)

    async def get_users_by_cpr_numbers(
        self, cpr_numbers: Iterable[str]
    ) -> list[RawOmadaUser]:
        """Retrieve IT users with the given CPR number ("C_CPRNR").

        Args:
            cpr_numbers: CPR number to retrieve users for.

        Returns: List of raw omada users with the given CPR number.
        """
        cpr_number_strings = (f"'{n}'" for n in cpr_numbers)
        return await self.get_users_by("C_CPRNR", cpr_number_strings)
