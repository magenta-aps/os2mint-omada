# SPDX-FileCopyrightText: 2022 Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
import pytest
from pydantic import ValidationError

from os2mint_omada.backing.omada.models import ManualOmadaUser
from os2mint_omada.backing.omada.models import OmadaUser


@pytest.fixture
def omada_user() -> dict:
    return {
        "IDENTITYCATEGORY": {
            "Id": 560,
            "UId": "ac0c67fc-5f47-4112-94e6-446bfb68326a",
        },
        "C_TJENESTENR": "DRV2639",
        "C_OBJECTGUID_I_AD": "9e5aee86-1461-4072-9883-ed43c82db42c",
        "C_LOGIN": "DR00777",
        "EMAIL": "bob@example.com",
        "EMAIL2": "",
        "C_DIREKTE_TLF": "12341234",
        "CELLPHONE": "",
        "C_INST_PHONE": "",
        "C_SYNLIG_I_OS2MO": True,
        "VALIDFROM": "2016-06-15T00:00:00+02:00",
        "VALIDTO": "2022-12-03T00:00:00+01:00",
    }


@pytest.fixture
def omada_user_manual(omada_user: dict) -> dict:
    manual_fields = {
        "IDENTITYCATEGORY": {
            "Id": 561,
            "UId": "270a1807-95ca-40b4-9ce5-475d8961f31b",
        },
        "C_FORNAVNE": "Anders W.",
        "LASTNAME": "Lemming",
        "C_CPRNR": "1707821597",
        "JOBTITLE": "Worker",
        "C_ORGANISATIONSKODE": "5a23d722-1be4-4f00-a200-000001500001",
    }
    return omada_user | manual_fields


def test_omada_user(omada_user: dict) -> None:
    assert OmadaUser.parse_obj(omada_user)


def test_omada_user_manual(omada_user_manual: dict) -> None:
    assert ManualOmadaUser.parse_obj(omada_user_manual)


def test_omada_user_manual_non_manual(omada_user_manual: dict) -> None:
    omada_user_manual["IDENTITYCATEGORY"]["Id"] = 123
    with pytest.raises(ValidationError):
        ManualOmadaUser.parse_obj(omada_user_manual)
