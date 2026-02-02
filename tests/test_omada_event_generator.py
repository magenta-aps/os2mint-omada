# SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
# mypy: disable-error-code=assignment
from datetime import datetime
from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import call
from uuid import uuid4

from fastapi.encoders import jsonable_encoder

from os2mint_omada.config import OmadaSettings
from os2mint_omada.omada.event_generator import Event
from os2mint_omada.omada.event_generator import OmadaEventGenerator
from os2mint_omada.omada.models import OmadaUser


def get_test_user(id: int) -> OmadaUser:
    return OmadaUser(
        id=id,
        uid=uuid4(),
        valid_from=datetime(2023, 1, 2),
    )


async def test_generate(omada_settings: OmadaSettings):
    """Test that create/update/delete events are detected correctly."""
    # Setup fake users

    old_a = get_test_user(1)
    old_b = get_test_user(2)
    old_c = get_test_user(3)
    old_users = [old_a, old_b, old_c]

    new_a = old_a  # A is unchanged
    new_b = old_b.copy(update=dict(id=99))  # B is changed
    new_d = get_test_user(4)  # D is added
    new_users = [new_a, new_b, new_d]  # C is deleted

    # The "API" returns the new users
    api = MagicMock()
    api.get_users = AsyncMock(return_value=new_users)

    amqp_system = AsyncMock()
    event_generator = OmadaEventGenerator(
        settings=omada_settings, api=api, amqp_system=amqp_system
    )
    # Override loading from disk to "load" the old users
    event_generator._load_users = MagicMock(return_value=old_users)

    await event_generator.generate()

    amqp_system.publish_message.assert_has_awaits(
        calls=[
            call(
                routing_key=Event.CREATE,
                payload=jsonable_encoder(new_d),
            ),
            call(
                routing_key=Event.DELETE,
                payload=jsonable_encoder(old_c),
            ),
            call(
                routing_key=Event.UPDATE,
                payload=jsonable_encoder(new_b),
            ),
        ],
        any_order=True,
    )
