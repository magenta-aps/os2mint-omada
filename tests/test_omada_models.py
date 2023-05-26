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
        "VALIDTO": "9999-12-31T01:00:00+01:00",
        "IDENTITYCATEGORY": {
            "Id": 123,
            "UId": "e61de13e-d6fb-4c9e-90fd-75f9f1e1df5a",
        },
    }


def test_parse_user(omada_user: dict) -> None:
    """Test parsing of a user."""
    parsed = OmadaUser.parse_obj(omada_user)
    # Omada's pseudo-infinity of 31/12/9999 should be converted to None
    assert parsed.valid_to is None
