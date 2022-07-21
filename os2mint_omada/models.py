# SPDX-FileCopyrightText: 2021 Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from typing import TypedDict

from os2mint_omada.backing.mo.service import MOService
from os2mint_omada.backing.omada.service import OmadaService
from os2mint_omada.config import Settings


class Context(TypedDict, total=False):
    """FastAPI and AMQP System context dict."""

    settings: Settings

    mo_service: MOService
    omada_service: OmadaService
