# SPDX-FileCopyrightText: 2021 Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
import logging
from typing import Optional

import structlog
from pydantic import AnyHttpUrl
from pydantic import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    log_level: str = "INFO"

    # OS2mo
    mo_url: AnyHttpUrl = Field("http://mo:5000")
    client_id: str = "dipex"
    client_secret: str
    auth_realm: str = "mo"
    auth_server: AnyHttpUrl = Field("http://keycloak:8081/auth")

    # MO IT-system users will be inserted into
    it_system_user_key: str

    # Omada OData view: http://omada.example.org/OData/DataObjects/Identity?viewid=xxxxx
    odata_url: AnyHttpUrl
    omada_host_header: Optional[str] = None  # http host header override
    omada_ntlm_username: Optional[str] = None
    omada_ntlm_password: Optional[str] = None

    class Config:
        frozen = True


settings = Settings()


def set_log_level(log_level_name: str) -> None:
    log_level_value = logging.getLevelName(log_level_name)
    structlog.configure(
        wrapper_class=structlog.make_filtering_bound_logger(log_level_value)
    )
