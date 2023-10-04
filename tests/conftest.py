# # SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# # SPDX-License-Identifier: MPL-2.0
from pathlib import Path

import pytest
from pydantic import AmqpDsn
from pydantic import AnyHttpUrl
from pydantic import parse_obj_as

from os2mint_omada.config import OmadaAMQPConnectionSettings
from os2mint_omada.config import OmadaSettings


@pytest.fixture
def omada_settings(tmp_path: Path) -> OmadaSettings:
    """Fixed settings so tests work without specific environment variables."""
    return OmadaSettings(
        url=parse_obj_as(AnyHttpUrl, "https://omada.example.com/odata.json"),
        persistence_file=tmp_path.joinpath("omada.json"),
        amqp=OmadaAMQPConnectionSettings(
            url=parse_obj_as(AmqpDsn, "amqp://guest:guest@msg-broker:5672/"),
        ),
    )
