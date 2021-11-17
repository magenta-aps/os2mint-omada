# SPDX-FileCopyrightText: 2021 Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from uuid import UUID

from pydantic import AnyHttpUrl
from pydantic import BaseModel
from pydantic import Field

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

    class Config:
        # Allow fields to be populated by both alias and model attribute name
        allow_population_by_field_name = True


async def get_it_users(odata_url: AnyHttpUrl) -> list[OmadaITUser]:
    """
    Get all IT users from the Omada OData view at the given URL.

    For example responses and information about the Omada OData API, see:
      - docs/odata.dataobjects.identity.view.json
      - docs/odata.dataobjects.metadata.xml

    Args:
        odata_url: URL of the Omada OData view.

    Returns: List of Omada IT user objects.
    """
    r = await client.get(odata_url)  # TODO: set 'timeout=' ?
    return [OmadaITUser.parse_obj(user_json) for user_json in r.json()["value"]]
