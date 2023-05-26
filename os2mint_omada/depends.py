# SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from typing import Annotated
from typing import Any
from typing import Callable

from fastapi import Depends
from raclients.modelclient.mo import ModelClient as _ModelClient
from ramqp import AMQPSystem
from ramqp.depends import from_context

from os2mint_omada.mo import MO as _MO
from os2mint_omada.omada.api import OmadaAPI as _OmadaAPI

# Standard FastRAMQPI context TODO: Move to FastRAMQPI framework
UserContext = Annotated[dict[str, Any], Depends(from_context("user_context"))]
ModelClient = Annotated[_ModelClient, Depends(from_context("model_client"))]


def from_user_context(field: str) -> Callable[..., Any]:
    """Construct a Callable which extracts 'field' from the FastRAMQPI user context.

    Args:
        field: The field to extract.

    Returns:
        A callable which extracts 'field' from the FastRAMQPI user context.
    """

    def inner(user_context: UserContext) -> Any:
        return user_context[field]

    return inner


# Omada context
MO = Annotated[_MO, Depends(from_user_context("mo"))]
OmadaAMQPSystem = Annotated[AMQPSystem, Depends(from_user_context("omada_amqp_system"))]
OmadaAPI = Annotated[_OmadaAPI, Depends(from_user_context("omada_api"))]
