# # SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# # SPDX-License-Identifier: MPL-2.0
from pathlib import Path

import pytest
from _pytest.nodes import Item
from pydantic import AmqpDsn
from pydantic import AnyHttpUrl
from pydantic import parse_obj_as

from os2mint_omada.config import OmadaAMQPConnectionSettings
from os2mint_omada.config import OmadaSettings

pytestmark = pytest.mark.respx(assert_all_called=True)


def pytest_collection_modifyitems(items: list[Item]) -> None:
    """Always assert all respx mocks are called on all tests."""
    for item in items:
        item.add_marker(pytest.mark.respx(assert_all_called=True))


@pytest.fixture
def omada_settings(tmp_path: Path) -> OmadaSettings:
    """Fixed settings so tests work without specific environment variables."""
    return OmadaSettings(
        url=parse_obj_as(AnyHttpUrl, "https://omada.example.com/odata.json"),
        persistence_file=tmp_path.joinpath("omada.json"),
        amqp=OmadaAMQPConnectionSettings(
            url=parse_obj_as(AmqpDsn, "amqp://guest:guest@msg_broker:5672/"),
        ),
    )
