# SPDX-FileCopyrightText: 2021 Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
import httpx
from ra_utils.headers import TokenSettings
from raclients.auth import AuthenticatedAsyncHTTPXClient
from raclients.graph.client import GraphQLClient
from raclients.mo import ModelClient
from raclients.modelclientbase import common_session_factory

from os2mint_omada.config import settings

# The global clients will be closed by close_clients() through the fastapi shutdown
# signal in app.py.
client = httpx.AsyncClient()

_mo_args = dict(
    client_id=settings.client_id,
    client_secret=settings.client_secret,
    auth_realm=settings.auth_realm,
    auth_server=settings.auth_server,
)

mo_client = AuthenticatedAsyncHTTPXClient(**_mo_args)

lora_client = AuthenticatedAsyncHTTPXClient(
    client_id=settings.lora_client_id,
    client_secret=settings.lora_client_secret,
    auth_server=settings.auth_server,
    auth_realm=settings.lora_auth_realm,
)

model_client = ModelClient(
    base_url=settings.mo_url,
    session_factory=common_session_factory(
        token_settings=TokenSettings(
            client_id=settings.client_id,
            client_secret=settings.client_secret,
            auth_realm=settings.auth_realm,
            auth_server=settings.auth_server,
        )
    ),
)
