# SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from pathlib import Path

from fastramqpi.config import Settings as FastRAMQPISettings
from pydantic import AnyHttpUrl
from pydantic import BaseModel
from pydantic import BaseSettings
from pydantic import validator
from ramqp.config import AMQPConnectionSettings


class OmadaOIDCSettings(BaseModel):
    client_id: str
    client_secret: str
    token_endpoint: AnyHttpUrl
    scope: str


class OmadaBasicAuthSettings(BaseModel):
    username: str
    password: str


class OmadaAMQPConnectionSettings(AMQPConnectionSettings):
    exchange = "omada"
    queue_prefix = "omada"
    prefetch_count = 1  # MO cannot handle too many requests


class OmadaSettings(BaseModel):
    # OData view: http://omada.example.org/OData/DataObjects/Identity?viewid=xxxxx
    url: AnyHttpUrl
    insecure_skip_tls_verify = False
    oidc: OmadaOIDCSettings | None = None
    basic_auth: OmadaBasicAuthSettings | None = None

    amqp: OmadaAMQPConnectionSettings
    interval: int = 1800
    persistence_file: Path = Path("/data/omada.json")

    @validator("persistence_file", always=True)
    def persistence_directory_exists(cls, persistence_file: Path) -> Path:
        if not persistence_file.parent.is_dir():
            raise ValueError("Persistence file's parent directory doesn't exist")
        return persistence_file


class Settings(BaseSettings):
    fastramqpi: FastRAMQPISettings

    omada: OmadaSettings

    class Config:
        frozen = True
        env_nested_delimiter = "__"
