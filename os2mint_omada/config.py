# SPDX-FileCopyrightText: 2021 Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from pydantic import AnyHttpUrl
from pydantic import BaseSettings
from pydantic import Field
from pydantic import UUID4


class Settings(BaseSettings):
    # OS2mo
    mo_url: AnyHttpUrl = Field("http://mo:5000")
    client_id: str = "dipex"
    client_secret: str
    auth_realm: str = "mo"
    auth_server: AnyHttpUrl = Field("http://keycloak:8081/auth")

    # MO IT-system users will be inserted into
    it_system_uuid: UUID4
    it_system_user_key: str
    it_system_name: str

    # Omada OData view: http://omada.example.org/OData/DataObjects/Identity?viewid=xxxxx
    odata_url: AnyHttpUrl

    class Config:
        frozen = True


settings = Settings()
