# SPDX-FileCopyrightText: 2022 Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
import json

import structlog
from fastapi.encoders import jsonable_encoder

from os2mint_omada.backing.omada.models import OmadaUser
from os2mint_omada.config import Settings

logger = structlog.get_logger(__name__)


class FailDB:
    """TODO: This should be implemented using os2mo-amqp-trigger-failures."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def add(self, omada_user: OmadaUser, exception: BaseException) -> None:
        logger.warning("Adding user to fail db", omada_user=omada_user)
        with self.settings.failures_file.open("a") as file:
            file.write(repr(exception))
            json.dump(jsonable_encoder(omada_user.dict()), file, indent=2)
