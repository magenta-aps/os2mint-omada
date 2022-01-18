# SPDX-FileCopyrightText: 2021 Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
import re
from typing import Optional
from uuid import UUID

import httpx
from httpx_ntlm import HttpNtlmAuth
from pydantic import AnyHttpUrl
from pydantic import BaseModel
from pydantic import Field
from pydantic import parse_obj_as
from pydantic import validator

from os2mint_omada.clients import client


class OmadaITUser(BaseModel):
    """
    Types derived from Omada OData. See: docs/odata.dataobjects.metadata.xml.
    """

    service_number: str = Field(alias="C_TJENESTENR")
    ad_guid: UUID = Field(alias="C_OBJECTGUID_I_AD")
    login: str = Field(alias="C_LOGIN")
    email: str = Field(alias="EMAIL")
    phone_direct: str = Field(alias="C_DIREKTE_TLF")
    phone_cell: str = Field(alias="CELLPHONE")
    phone_institution: str = Field(alias="C_INST_PHONE")

    @validator("phone_direct", "phone_cell", "phone_institution")
    def check_phone_number(cls, phone_number: str) -> str:
        # From mora.service.address_handler.phone.PhoneAddressHandler.validate_value
        if re.match(r"^\+?\d+$", phone_number):
            return phone_number
        return ""

    class Config:
        # Allow fields to be populated by both alias and model attribute name
        allow_population_by_field_name = True


async def get_it_users(
    odata_url: AnyHttpUrl,
    host_header: Optional[str] = None,
    ntlm_username: Optional[str] = None,
    ntlm_password: Optional[str] = None,
) -> list[OmadaITUser]:
    """
    Get all IT users from the Omada OData view at the given URL.

    For example responses and information about the Omada OData API, see:
      - docs/odata.dataobjects.identity.view.json
      - docs/odata.dataobjects.metadata.xml

    Args:
        odata_url: URL of the Omada OData view.
        host_header: Optional HTTP 'Host' header override. This may be useful if Omada
         is hosted on an internal network without proper DNS configuration.
        ntlm_username: Username used for optional NTLM authentication. Supports the
         'DOMAIN\\USER' format.
        ntlm_password: Password for optional NTLM authentication.

    Returns: List of Omada IT user objects.
    """
    headers = {}
    if host_header is not None:
        headers["Host"] = host_header

    if ntlm_username is not None or ntlm_password is not None:
        auth = HttpNtlmAuth(username=ntlm_username, password=ntlm_password)
    else:
        auth = httpx.USE_CLIENT_DEFAULT

    response = await client.get(odata_url, headers=headers, auth=auth, timeout=30)

    users = response.json()["value"]
    valid_users = (u for u in users if u["C_OBJECTGUID_I_AD"])
    return parse_obj_as(list[OmadaITUser], valid_users)
