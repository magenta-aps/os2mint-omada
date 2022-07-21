# SPDX-FileCopyrightText: 2022 Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

from typing import Any
from uuid import UUID

import structlog
from pydantic import BaseModel
from pydantic import validator
from ramodels.mo import Validity

from os2mint_omada.backing.mo.service import MOService
from os2mint_omada.backing.omada.service import OmadaService
from os2mint_omada.config import MoSettings
from os2mint_omada.util import at_midnight

logger = structlog.get_logger(__name__)


class ComparableMixin(BaseModel):
    @validator("uuid", check_fields=False)
    def strip_uuid(cls, uuid: UUID) -> None:
        """Strip UUID to allow for convenient comparison of models."""
        return None

    @validator("validity", check_fields=False)
    def validity_at_midnight(cls, validity: Validity) -> Validity:
        """Normalise validity dates to allow for convenient comparison of models."""
        return Validity(
            from_date=at_midnight(validity.from_date),
            to_date=at_midnight(validity.to_date),
        )


class StripUserKeyMixin(BaseModel):
    @validator("user_key", check_fields=False)
    def strip_user_key(cls, user_key: Any | None) -> None:
        """Strip user key to allow for convenient comparison of models.

        Should only be used on objects where the user key does not contain actual
        relevant data, but is simply a copy of the UUID (as automatically set by MOBase
        if absent).
        """
        return None


class Syncer:
    def __init__(
        self, settings: MoSettings, mo_service: MOService, omada_service: OmadaService
    ) -> None:
        """The logic responsible for taking actions to synchronise MO with Omada.

        Args:
            settings: MO-specific settings.
            mo_service: MO backing service.
            omada_service: Omada backing service.
        """
        self.settings = settings
        self.mo_service = mo_service
        self.omada_service = omada_service
