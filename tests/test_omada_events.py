# SPDX-FileCopyrightText: 2022 Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from unittest.mock import AsyncMock
from unittest.mock import call
from unittest.mock import MagicMock

from os2mint_omada.backing.omada.event_generator import OmadaEventGenerator
from os2mint_omada.backing.omada.routing_keys import Event
from os2mint_omada.backing.omada.routing_keys import RawRoutingKey
from os2mint_omada.config import OmadaSettings


async def test_generate(omada_settings: OmadaSettings):
    old_a = {
        "UId": "A",
        "x": 1,
    }
    old_b = {
        "UId": "B",
        "x": 2,
    }
    old_c = {
        "UId": "C",
        "x": 3,
    }
    old_users = [old_a, old_b, old_c]

    new_a = old_a  # A is unchanged
    new_b = old_b | {"x": 3}  # B is changed: 2 => 3
    new_d = {  # D is added
        "UId": "D",
        "x": 4,
    }
    new_users = [new_a, new_b, new_d]  # C is deleted

    api = MagicMock()
    api.get_users = AsyncMock(return_value=new_users)

    amqp_system = MagicMock()
    amqp_system.publish_message = AsyncMock()

    event_generator = MagicMock(
        wraps=OmadaEventGenerator(
            settings=omada_settings, api=api, amqp_system=amqp_system
        )
    )
    event_generator._save_users(old_users)

    await event_generator.generate()

    amqp_system.publish_message.assert_has_awaits(
        calls=[
            call(RawRoutingKey(event=Event.CREATE), payload=new_d),
            call(RawRoutingKey(event=Event.DELETE), payload=old_c),
            call(RawRoutingKey(event=Event.UPDATE), payload=new_b),
        ],
        any_order=True,
    )
