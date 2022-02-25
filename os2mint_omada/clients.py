# SPDX-FileCopyrightText: 2021 Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
import httpx
from raclients.auth import AuthenticatedAsyncHTTPXClient
from raclients.graph.client import PersistentGraphQLClient
from raclients.modelclient.mo import ModelClient as MoModelClient

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

graphql_client = PersistentGraphQLClient(url=f"{settings.mo_url}/graphql", **_mo_args)

mo_client = AuthenticatedAsyncHTTPXClient(base_url=settings.mo_url, **_mo_args)

mo_model_client = MoModelClient(
    base_url=settings.mo_url,
    client_id=settings.client_id,
    client_secret=settings.client_secret,
    auth_realm=settings.auth_realm,
    auth_server=settings.auth_server,
)
