# SPDX-FileCopyrightText: 2022 Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Event(str, Enum):
    """Omada AMQP event type."""

    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    REFRESH = "refresh"
    WILDCARD = "*"


class PayloadType(str, Enum):
    """Omada AMQP payload type."""

    RAW = "raw"
    PARSED = "parsed"


@dataclass
class RoutingKey:
    """Omada AMQP routing key, containing the event and payload type."""

    type: PayloadType
    event: Event

    def __str__(self) -> str:
        """AMQP routing keys are usually expressed in dot-notation."""
        return f"omada.user.{self.type}.{self.event}"

    @classmethod
    def from_str(cls, s: str) -> RoutingKey:
        *_, type, event = s.rsplit(".", maxsplit=2)
        return cls(type=PayloadType(type), event=Event(event))
