# SPDX-FileCopyrightText: 2022 Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from unittest.mock import AsyncMock
from unittest.mock import call
from unittest.mock import MagicMock

from os2mint_omada.backing.omada.event_generator import OmadaEventGenerator
from os2mint_omada.backing.omada.routing_keys import Event
from os2mint_omada.backing.omada.routing_keys import PayloadType
from os2mint_omada.backing.omada.routing_keys import RoutingKey
from os2mint_omada.config import OmadaSettings


async def test_generate(omada_settings: OmadaSettings):
    """Test that create/update/delete events are detected correctly."""
    # Setup fake users
    old_a = {"UId": "A", "name": 1}
    old_b = {"UId": "B", "name": 2}
    old_c = {"UId": "C", "name": 3}
    old_users = [old_a, old_b, old_c]

    new_a = old_a  # A is unchanged
    new_b = {"UId": "B", "name": 99}  # B is changed
    new_d = {"UId": "D", "name": 4}  # D is added
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
                routing_key=RoutingKey(type=PayloadType.RAW, event=Event.CREATE),
                payload=new_d,
            ),
            call(
                routing_key=RoutingKey(type=PayloadType.RAW, event=Event.DELETE),
                payload=old_c,
            ),
            call(
                routing_key=RoutingKey(type=PayloadType.RAW, event=Event.UPDATE),
                payload=new_b,
            ),
        ],
        any_order=True,
    )
