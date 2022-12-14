# SPDX-FileCopyrightText: 2021 Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

import asyncio
from contextlib import AbstractAsyncContextManager
from contextlib import AsyncExitStack
from types import TracebackType
from typing import Type

import structlog
from ramqp import AMQPSystem

from os2mint_omada.backing.omada.api import OmadaAPI
from os2mint_omada.backing.omada.event_generator import OmadaEventGenerator
from os2mint_omada.config import OmadaSettings

logger = structlog.get_logger(__name__)


class OmadaService(AbstractAsyncContextManager):
    def __init__(self, settings: OmadaSettings, amqp_system: AMQPSystem) -> None:
        """The Omada backing service manages the connection to Omada's AMQP and API.

        Args:
            settings: Omada-specific settings.
            amqp_system: Omada AMQP system.
        """
        super().__init__()
        self.settings = settings
        self.amqp_system = amqp_system
        self.stack = AsyncExitStack()

    async def __aenter__(self) -> OmadaService:
        """Start clients for persistent connections to the Omada API and AMQP."""
        settings = self.settings
        logger.info("Starting Omada Service", settings=settings)

        # API
        api = OmadaAPI(settings)
        self.api: OmadaAPI = await self.stack.enter_async_context(api)

        # AMQP
        await self.stack.enter_async_context(self.amqp_system)

        # Event Generator
        event_generator = OmadaEventGenerator(
            settings=settings, api=api, amqp_system=self.amqp_system
        )
        self.event_generator: OmadaEventGenerator = (
            await self.stack.enter_async_context(event_generator)
        )

        return await super().__aenter__()

    async def __aexit__(
        self,
        __exc_type: Type[BaseException] | None,
        __exc_value: BaseException | None,
        __traceback: TracebackType | None,
    ) -> bool | None:
        """Close connections to the Omada API and AMQP system."""
        logger.info("Closing Omada Service")
        await self.stack.aclose()
        return await super().__aexit__(__exc_type, __exc_value, __traceback)

    async def _is_api_ready(self) -> bool:
        """Check that the Omada API is reachable.

        Returns: Whether the API is reachable.
        """
        return await self.api.is_ready()

    async def _is_amqp_ready(self) -> bool:
        """Check the connection to Omada's AMQP system.

        Returns: Whether a connection to the AMQP system is established..
        """
        return self.amqp_system.healthcheck()

    async def is_ready(self) -> bool:
        """Check the connection to the Omada API and AMQP system.

        Returns: Whether the Omada backing service is ready.
        """
        return all(await asyncio.gather(self._is_api_ready(), self._is_amqp_ready()))
