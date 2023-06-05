# SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

import asyncio
import json
import random
from asyncio import CancelledError
from asyncio import Task
from contextlib import AbstractAsyncContextManager
from enum import StrEnum
from types import TracebackType
from typing import Type
from uuid import UUID

import structlog
from fastapi.encoders import jsonable_encoder
from prometheus_client import Gauge
from pydantic import parse_obj_as
from ramqp import AMQPSystem

from os2mint_omada.config import OmadaSettings
from os2mint_omada.omada.api import OmadaAPI
from os2mint_omada.omada.models import OmadaUser
from os2mint_omada.omada.models import RawOmadaUser

logger = structlog.get_logger(__name__)


omada_last_event_generate_timestamp = Gauge(
    "omada_last_event_generate_timestamp",
    "Timestamp of when the Omada event generator last successfully ran.",
    unit="seconds",
)


class Event(StrEnum):
    """Omada AMQP event type."""

    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    REFRESH = "refresh"
    WILDCARD = "*"


class OmadaEventGenerator(AbstractAsyncContextManager):
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
        logger.debug("Starting Omada event scheduler")
        self._scheduler_task: Task = asyncio.create_task(self._scheduler())
        return await super().__aenter__()

    async def __aexit__(
        self,
        __exc_type: Type[BaseException] | None,
        __exc_value: BaseException | None,
        __traceback: TracebackType | None,
    ) -> bool | None:
        """Stop the scheduler task."""
        logger.debug("Stopping Omada event scheduler")
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
                # Wait a random amount of time before retrying, to avoid two or more
                # integrations indefinitely causing timeouts in each other by trying to
                # generate at the same time.
                wait = random.randint(30, 120)
                logger.info("Waiting to resume scheduler", wait=wait)
                await asyncio.sleep(wait)
            except CancelledError:
                logger.info("Stopping Omada scheduler")
                break

    async def generate(self) -> None:
        """Generate Omada events based on the live Omada API view and saved state."""
        # Retrieve raw lists of users from the previous run and API
        old_users_list = self._load_users()
        new_users_list = await self.api.get_users()

        def by_identifier(raw_users: list[RawOmadaUser]) -> dict[UUID, OmadaUser]:
            """Structure by user identifier to allow detecting changes in values."""
            users = parse_obj_as(list[OmadaUser], raw_users)
            users_by_uid = {u.uid: u for u in users}
            return users_by_uid

        old_users = by_identifier(old_users_list)
        new_users = by_identifier(new_users_list)

        # Generate event for each user
        for uid in old_users.keys() | new_users.keys():
            old = old_users.get(uid)
            new = new_users.get(uid)
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
            logger.info("Detected Omada event", change=event, uid=uid)
            assert payload is not None  # mypy is so dumb
            await self.amqp_system.publish_message(
                routing_key=event,
                payload=jsonable_encoder(payload),
            )

        self._save_users(new_users_list)
        omada_last_event_generate_timestamp.set_to_current_time()

    def _save_users(self, users: list[RawOmadaUser]) -> None:
        """Save known Omada users (dicts) to disk."""
        logger.info("Saving known Omada users", num_users=len(users))
        with self.settings.persistence_file.open("w") as file:
            json.dump(jsonable_encoder(users), file)

    def _load_users(self) -> list[RawOmadaUser]:
        """Load known Omada users (dicts) from disk."""
        try:
            with self.settings.persistence_file.open() as file:
                users = json.load(file)
        except FileNotFoundError:
            users = []
        logger.info("Loaded known Omada users", num_users=len(users))
        return users
