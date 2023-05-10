# SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from os2mint_omada.backing.omada.routing_keys import Event
from os2mint_omada.backing.omada.routing_keys import PayloadType
from os2mint_omada.backing.omada.routing_keys import RoutingKey


def test_routing_key() -> None:
    routing_key = RoutingKey(type=PayloadType.RAW, event=Event.CREATE)
    assert str(routing_key) == "omada.user.raw.create"


def test_routing_key_from_string() -> None:
    routing_key = RoutingKey.from_str("omada.user.parsed.*")
    assert routing_key == RoutingKey(type=PayloadType.PARSED, event=Event.WILDCARD)
