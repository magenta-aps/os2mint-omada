# SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
import pytest

from os2mint_omada.omada.models import OmadaUser


@pytest.fixture
def omada_user() -> dict:
    """Base Omada user, as returned by the API."""
    return {
        "Id": 12345678,
        "UId": "5fe3ef67-c6e5-4d09-bdee-80b9bf40544d",
        "VALIDFROM": "2016-06-15T00:00:00+02:00",
        "VALIDTO": "2022-04-18T22:05:21+02:00",
    }


def test_parse_user(omada_user: dict) -> None:
    """Test parsing of a user."""
    assert OmadaUser.parse_obj(omada_user)


def test_empty_string_is_none(omada_user: dict) -> None:
    """Test that Omada's psuedo-None empty strings are converted to true None."""

    class TestOmadaUser(OmadaUser):
        name: str | None

    omada_user["name"] = ""

    user = TestOmadaUser.parse_obj(omada_user)
    assert user.name is None


def test_fix_pseudo_infinity(omada_user: dict) -> None:
    """Test that Omada's pseudo-infinity of 31/12/9999 is converted to None."""
    omada_user["VALIDTO"] = "9999-12-31T01:00:00+01:00"
    user = OmadaUser.parse_obj(omada_user)
    assert user.valid_to is None
