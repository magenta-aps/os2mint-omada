# SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
import pytest
from pydantic import ValidationError

from os2mint_omada.sync.silkeborg.models import ManualSilkeborgOmadaUser
from os2mint_omada.sync.silkeborg.models import SilkeborgOmadaUser


@pytest.fixture
def silkeborg_omada_user() -> dict:
    """Silkeborg Omada user."""
    return {
        "Id": 1041094,
        "UId": "38e4a0f1-1290-40e3-ad83-896abd1d3e50",
        "VALIDFROM": "2012-08-27T00:00:00+02:00",
        "VALIDTO": "2022-12-01T01:00:00+01:00",
        "C_TJENESTENR": "v1216",
        "C_OBJECTGUID_I_AD": "74dea272-d90b-47c7-8d99-c8efa372fa03",
        "C_LOGIN": "DRV1216",
        "EMAIL": "Mia.Hansen@silkeborg.dk",
        "C_DIREKTE_TLF": "",
        "CELLPHONE": "",
        "C_FORNAVNE": "Mia",
        "LASTNAME": "Hansen",
        "C_CPRNR": "1709933104",
        "JOBTITLE": "Revisor",
        "C_ORGANISATIONSKODE": "f06ee470-9f17-566f-acbe-e938112d46d9",
        "C_SYNLIG_I_OS2MO": False,
        "C_OS2MO_ID": "DK-1337",
    }


@pytest.fixture
def manual_silkeborg_omada_user() -> dict:
    """Manual Silkeborg Omada user."""
    return {
        "Id": 1041073,
        "UId": "e9802c93-ce17-41e6-b425-5ed3c9e41b4f",
        "VALIDFROM": "2016-06-15T00:00:00+02:00",
        "VALIDTO": "2022-12-03T00:00:00+01:00",
        "C_TJENESTENR": "bbb",
        "C_OBJECTGUID_I_AD": "b71dccac-6611-4bf7-bb09-77c0bf510210",
        "C_LOGIN": "DRV2639",
        "EMAIL": "AndersW.Lemming@silkeborg.dk",
        "C_DIREKTE_TLF": "",
        "CELLPHONE": "12345678",
        "C_INST_PHONE": "",
        "C_FORNAVNE": "Anders W.",
        "LASTNAME": "Lemming",
        "C_CPRNR": "1907792583",
        "JOBTITLE": "",
        "C_ORGANISATIONSKODE": "f06ee470-9f17-566f-acbe-e938112d46d9",
        "C_SYNLIG_I_OS2MO": True,
        "C_OS2MO_ID": None,
    }


def test_parse_user(silkeborg_omada_user: dict) -> None:
    """Test parsing of a user."""
    omada_user = SilkeborgOmadaUser.parse_obj(silkeborg_omada_user)
    assert omada_user.is_manual is False


def test_parse_manual_user(manual_silkeborg_omada_user: dict) -> None:
    """Test parsing of a manual user."""
    omada_user = ManualSilkeborgOmadaUser.parse_obj(manual_silkeborg_omada_user)
    assert omada_user.is_manual is True


def test_cpr_number_validation(silkeborg_omada_user: dict) -> None:
    """Test CPR-number validation."""
    silkeborg_omada_user["C_CPRNR"] = "1234567890"
    with pytest.raises(ValidationError):
        SilkeborgOmadaUser.parse_obj(silkeborg_omada_user)
    # Silkeborg also have users with fictive CPR numbers
    silkeborg_omada_user["C_CPRNR"] = "7606014214"
    SilkeborgOmadaUser.parse_obj(silkeborg_omada_user)
