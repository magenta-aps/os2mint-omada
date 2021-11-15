# SPDX-FileCopyrightText: 2021 Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
import pytest
from respx import MockRouter

from os2mint_omada import omada
from os2mint_omada.config import settings
from os2mint_omada.omada import OmadaITUser


@pytest.fixture
def mock_omada_it_users(respx_mock: MockRouter) -> None:
    data = {
        "value": [
            {
                "Id": 1006456,
                "UId": "719b0b48-f651-40df-b980-f1d79123aa87",
                "CreateTime": "2018-11-05T10:40:16.447+01:00",
                "ChangeTime": "2021-06-02T08:42:45.327+02:00",
                "C_TJENESTENR": "00185",
                "C_OBJECTGUID_I_AD": "9ff2beb8-2283-410f-babc-70d3ec2afa0c",
                "EMAIL": "KristofferMoller.Jensen@silkeborg.dk",
                "EMAIL2": None,
                "C_DIREKTE_TLF": "",
                "CELLPHONE": "",
                "C_INST_PHONE": "",
                "C_LOGIN": "",
            },
            {
                "Id": 1006453,
                "UId": "f6327a33-07e3-468c-b7bb-cb852f25e3a4",
                "CreateTime": "2018-11-05T10:40:15.273+01:00",
                "ChangeTime": "2021-06-02T08:42:45.263+02:00",
                "C_TJENESTENR": "00187",
                "C_OBJECTGUID_I_AD": "1106d3a6-a624-43b5-bdb8-66b746a2a60d",
                "EMAIL": "Gitte.Willumsen@silkeborg.dk",
                "C_DIREKTE_TLF": "89701891",
                "CELLPHONE": "25306035",
                "C_INST_PHONE": "89701000",
                "C_LOGIN": "DR00187",
            },
        ]
    }
    respx_mock.get(settings.odata_url).respond(json=data)


@pytest.mark.asyncio
async def test_get_it_users(mock_omada_it_users: None) -> None:
    expected = [
        OmadaITUser(
            C_TJENESTENR="00185",
            C_OBJECTGUID_I_AD="9ff2beb8-2283-410f-babc-70d3ec2afa0c",
            EMAIL="KristofferMoller.Jensen@silkeborg.dk",
            C_DIREKTE_TLF="",
            CELLPHONE="",
            C_INST_PHONE="",
            C_LOGIN="",
        ),
        OmadaITUser(
            C_TJENESTENR="00187",
            C_OBJECTGUID_I_AD="1106d3a6-a624-43b5-bdb8-66b746a2a60d",
            EMAIL="Gitte.Willumsen@silkeborg.dk",
            C_DIREKTE_TLF="89701891",
            CELLPHONE="25306035",
            C_INST_PHONE="89701000",
            C_LOGIN="DR00187",
        ),
    ]
    actual = await omada.get_it_users(settings.odata_url)

    assert actual == expected
