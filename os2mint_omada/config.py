# SPDX-FileCopyrightText: 2021 Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
import logging
from pathlib import Path

import structlog
from pydantic import AnyHttpUrl
from pydantic import BaseModel
from pydantic import BaseSettings
from pydantic import Field
from pydantic import parse_obj_as
from pydantic import SecretStr
from pydantic import validator
from ramqp.config import ConnectionSettings as AMQPConnectionSettings


class MOAMQPConnectionSettings(AMQPConnectionSettings):
    queue_prefix = "omada"


class MoSettings(BaseModel):
    url: AnyHttpUrl = parse_obj_as(AnyHttpUrl, "http://mo-service:5000")
    client_id: str = "omada"
    client_secret: SecretStr
    auth_realm: str = "mo"
    auth_server: AnyHttpUrl = parse_obj_as(
        AnyHttpUrl, "http://keycloak-service:8080/auth"
    )

    amqp: MOAMQPConnectionSettings = Field(default_factory=MOAMQPConnectionSettings)

    # These classes and IT systems should be created by os2mo-init before starting.
    # See init.config.yml for an example that corresponds to these defaults.
    # Maps from Omada user attribute to IT system user key in MO
    it_user_map: dict[str, str] = {
        "ad_guid": "omada_ad_guid",
        "login": "omada_login",
    }
    # Maps from Omada user attribute to employee address type (class) user key in MO
    address_map: dict[str, str] = {
        "email": "EmailEmployee",
        "phone_direct": "PhoneEmployee",
        "phone_cell": "MobilePhoneEmployee",
        "phone_institution": "InstitutionPhoneEmployee",
    }
    # Visibility class for created addresses
    address_visibility = "Intern"
    # Fallback job function for engagements created for manual users if the job title
    # from Omada does not exist in MO.
    manual_job_function_default: str = "not_applicable"
    # Maps from Omada visibility (boolean) to engagement type (class) user key in MO
    # for manual users. Only these engagements types are touched by the integration.
    engagement_type_for_visibility: dict[bool, str] = {
        True: "omada_manually_created",
        False: "omada_manually_created_hidden",
    }
    # Primary class for engagements created for manual users
    manual_primary_class: str = "primary"


class OmadaAMQPConnectionSettings(AMQPConnectionSettings):
    exchange = "omada"
    queue_prefix = "omada"


class OmadaSettings(BaseModel):
    # OData view: http://omada.example.org/OData/DataObjects/Identity?viewid=xxxxx
    url: AnyHttpUrl
    host_header: str | None = None  # http host header override
    ntlm_username: str | None = None
    ntlm_password: str | None = None
    insecure_skip_ssl_verify = False

    amqp: OmadaAMQPConnectionSettings = Field(
        default_factory=OmadaAMQPConnectionSettings
    )
    interval: int = 1800
    persistence_file: Path = Path("/data/omada.json")

    @validator("persistence_file", always=True)
    def persistence_directory_exists(cls, persistence_file: Path) -> Path:
        if not persistence_file.parent.is_dir():
            raise ValueError("Persistence file's parent directory doesn't exist")
        return persistence_file


class Settings(BaseSettings):
    commit_sha: str = Field("HEAD", description="Git commit SHA.")
    commit_tag: str | None = Field(None, description="Git commit tag.")

    log_level: str = "INFO"
    enable_metrics: bool = False
    failures_file: Path = Path("/data/failures.log")

    mo: MoSettings
    omada: OmadaSettings

    class Config:
        frozen = True
        env_nested_delimiter = "__"  # allows setting e.g. MO__AMQP__QUEUE_PREFIX=foo


def configure_logging(log_level_name: str) -> None:
    log_level_value = logging.getLevelName(log_level_name)
    structlog.configure(
        wrapper_class=structlog.make_filtering_bound_logger(log_level_value)
    )
