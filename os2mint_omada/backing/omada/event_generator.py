# SPDX-FileCopyrightText: 2022 Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

import asyncio
import json
from asyncio import CancelledError
from asyncio import Task
from contextlib import AbstractAsyncContextManager
from types import TracebackType
from typing import Any
from typing import Type

import structlog
from ramqp import AMQPSystem

from os2mint_omada.backing.omada.api import OmadaAPI
from os2mint_omada.backing.omada.models import RawOmadaUser
from os2mint_omada.backing.omada.routing_keys import Event
from os2mint_omada.backing.omada.routing_keys import PayloadType
from os2mint_omada.backing.omada.routing_keys import RoutingKey
from os2mint_omada.config import OmadaSettings

logger = structlog.get_logger(__name__)


class OmadaEventGenerator(AbstractAsyncContextManager):
    user_identifier: str = "UId"

    def __init__(
        self, settings: OmadaSettings, api: OmadaAPI, amqp_system: AMQPSystem
    ) -> None:
        """Omada event generator.

        The omada event generator periodically retrieves a list of all users in Omada,
        and compares it with the list it retrieved the last time, to calculate events
        which are sent to AMQP.

        Args:
            settings: Omada-specific settings.
            api: OmadaAPI instance.
            amqp_system: Omada AMQP system to send events to.
        """
        self.settings = settings
        self.api = api
        self.amqp_system = amqp_system

    async def __aenter__(self) -> OmadaEventGenerator:
        """Start the scheduler task."""
        logger.info("Starting Omada event scheduler")
        self._scheduler_task: Task = asyncio.create_task(self._scheduler())
        return await super().__aenter__()

    async def __aexit__(
        self,
        __exc_type: Type[BaseException] | None,
        __exc_value: BaseException | None,
        __traceback: TracebackType | None,
    ) -> bool | None:
        """Stop the scheduler task."""
        logger.info("Stopping Omada event scheduler")
        self._scheduler_task.cancel()
        return await super().__aexit__(__exc_type, __exc_value, __traceback)

    async def _scheduler(self) -> None:
        """The scheduler periodically and invokes the event generation logic."""
        logger.info("Starting Omada scheduler", interval=self.settings.interval)
        while True:
            try:
                await self.generate()
                await asyncio.sleep(self.settings.interval)
            except Exception:  # pylint: disable=broad-except
                logger.exception("Failed to generate events")
                logger.info("Resuming scheduler in 5 seconds..")
                await asyncio.sleep(5)
            except CancelledError:
                logger.info("Stopping Omada scheduler")
                break

    async def generate(self) -> None:
        """Generate Omada events based on the live Omada API view and saved state."""
        # Retrieve raw lists of users from the previous run and API
        old_users_list = self._load_users()
        new_users_list = await self.api.get_users()

        # Structure by user's identifier to allow detecting changes in values
        def by_identifier(users: list[RawOmadaUser]) -> dict[Any, RawOmadaUser]:
            return {u[self.user_identifier]: u for u in users}

        old_users = by_identifier(old_users_list)
        new_users = by_identifier(new_users_list)

        # Generate event for each user
        for key in old_users.keys() | new_users.keys():
            old = old_users.get(key)
            new = new_users.get(key)
            # Skip if user is unchanged
            if new == old:
                continue
            # Otherwise, determine change type
            if old is None:
                event = Event.CREATE
                payload = new
            elif new is None:
                event = Event.DELETE
                payload = old
            else:
                event = Event.UPDATE
                payload = new
            # Publish to AMQP
            logger.info(
                "Detected Omada event",
                change=event,
                user_key=key,
                user_identifier=self.user_identifier,
            )
            await self.amqp_system.publish_message(
                routing_key=RoutingKey(type=PayloadType.RAW, event=event),
                payload=payload,
            )

        self._save_users(new_users_list)

    def _save_users(self, users: list[RawOmadaUser]) -> None:
        """Save known Omada users (dicts) to disk."""
        logger.debug("Saving known Omada users", num_users=len(users))
        with self.settings.persistence_file.open("w") as file:
            json.dump(users, file)

    def _load_users(self) -> list[RawOmadaUser]:
        """Load known Omada users (dicts) from disk."""
        try:
            with self.settings.persistence_file.open() as file:
                users = json.load(file)
        except FileNotFoundError:
            users = []
        logger.debug("Loaded known Omada users", num_users=len(users))
        return users
