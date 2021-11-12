# SPDX-FileCopyrightText: 2021 Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from typing import Dict
from uuid import UUID

from pydantic import AnyHttpUrl
from pydantic import BaseModel

from os2mint_omada.clients import client


class OmadaITUser(BaseModel):
    """
    Types derived from Omada OData. See: docs/odata.dataobjects.metadata.xml.
    """

    # C_TJENESTENR is used to map Omada users to MO users through the 'user_key'
    # attribute on engagements
    C_TJENESTENR: str
    C_OBJECTGUID_I_AD: UUID  # MO ITSystemBinding 'user_key'
    C_LOGIN: str  # TODO: not used for now
    EMAIL: str  # MO EmailEmployee
    C_DIREKTE_TLF: str  # MO PhoneEmployee
    CELLPHONE: str  # MO MobilePhoneEmployee
    C_INST_PHONE: str  # MO InstitutionPhoneEmployee


async def get_it_users(odata_url: AnyHttpUrl) -> Dict[str, OmadaITUser]:
    """
    Get all IT users from the Omada OData view at the given URL.

    For example responses and information about the Omada OData API, see:
      - docs/odata.dataobjects.identity.view.json
      - docs/odata.dataobjects.metadata.xml

    Args:
        odata_url: URL of the Omada OData view.

    Returns: Dictionary mapping 'TJENESTENR' service numbers to Omada IT user objects.
    """
    # No auth so we don't leak MO credentials to Omada
    r = await client.get(odata_url, auth=None)  # TODO: set 'timeout=' ?
    it_users = {}
    for user_json in r.json()["value"]:
        user = OmadaITUser.parse_obj(user_json)
        it_users[user.C_TJENESTENR] = user
    return it_users
