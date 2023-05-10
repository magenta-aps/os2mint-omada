# SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

from enum import Enum


class Event(str, Enum):
    """Omada AMQP event type."""

    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    REFRESH = "refresh"
    WILDCARD = "*"
