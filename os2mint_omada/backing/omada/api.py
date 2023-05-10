# SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

import asyncio
from typing import Any
from typing import Iterable
from typing import Type

import structlog
from httpx import AsyncClient
from httpx import BasicAuth
from more_itertools import flatten
from raclients.auth import AuthenticatedAsyncHTTPXClient

from os2mint_omada.backing.omada.models import RawOmadaUser
from os2mint_omada.config import OmadaSettings

logger = structlog.get_logger(__name__)


class OmadaAPI:
    def __init__(self, client: AsyncClient | AuthenticatedAsyncHTTPXClient) -> None:
        """Facade for the Omada API.

        Args:
            client: HTTPX Client.
        """
        self.client = client

    async def get_users(self, omada_filter: str | None = None) -> list[RawOmadaUser]:
        """Retrieve IT users from Omada.

        Args:
            omada_filter: Optional Omada filter query.

        Returns: List of raw omada users (dicts).
        """
        params = {}
        if omada_filter is not None:
            params["$filter"] = omada_filter

        logger.info("Getting Omada IT users", params=params)
        response = await self.client.get("", params=params)
        response.raise_for_status()
        users = response.json()["value"]
        logger.info("Retrieved Omada IT users")
        # logger.debug("Retrieved Omada IT users", users=users)
        return users

    async def get_users_by(self, key: str, values: Iterable[str]) -> list[RawOmadaUser]:
        """Convenience wrapper for filtering on multiple criteria simultaneously.

        Args:
            key: Filter key.
            values: Filter value.

        Returns: List of raw omada users matching the filter.
        """
        # Omada does not support OR or IN operators, so we have to do it like this
        get_users = (self.get_users(f"{key} eq {value}") for value in values)
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

    async def get_users_by_cpr_number(self, cpr_number: str) -> list[RawOmadaUser]:
        """Retrieve IT users with the given CPR number ("C_CPRNR").

        Args:
            cpr_number: CPR number to retrieve users for.

        Returns: List of raw omada users with the given CPR number.
        """
        return await self.get_users_by("C_CPRNR", [f"'{cpr_number}'"])


def create_client(
    settings: OmadaSettings,
) -> AsyncClient | AuthenticatedAsyncHTTPXClient:
    """Create HTTPX Client for the Omada API.

    Args:
        settings: Omada-specific settings.

    Returns: HTTPX Client.
    """
    client_cls: Type[AsyncClient | AuthenticatedAsyncHTTPXClient] = AsyncClient
    kwargs: dict[str, Any] = dict(
        base_url=settings.url,
        timeout=60,
    )
    if settings.insecure_skip_tls_verify:
        logger.warning("INSECURE: Skipping TLS verification for Omada API!")
        kwargs["verify"] = False
    if settings.oidc is not None:
        client_cls = AuthenticatedAsyncHTTPXClient
        kwargs.update(**settings.oidc.dict())
    if settings.basic_auth is not None:
        kwargs["auth"] = BasicAuth(**settings.basic_auth.dict())

    logger.debug("Creating Omada client", kwargs=kwargs)
    client = client_cls(**kwargs)
    return client
