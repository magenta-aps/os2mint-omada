# SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
import pytest
from pydantic import ValidationError

from os2mint_omada.backing.omada.models import ManualOmadaUser
from os2mint_omada.backing.omada.models import OmadaUser


def test_omada_user(raw_omada_user: dict) -> None:
    """Test that the model can parse one instance of a raw normal user."""
    assert OmadaUser.parse_obj(raw_omada_user)


def test_omada_user_manual(raw_omada_user_manual: dict) -> None:
    """Test that the model can parse one instance of a raw manual user."""
    assert ManualOmadaUser.parse_obj(raw_omada_user_manual)


def test_omada_user_manual_non_manual(raw_omada_user_manual: dict) -> None:
    """Test that parsing a non-manual user as manual fails validation."""
    raw_omada_user_manual["IDENTITYCATEGORY"]["Id"] = 123
    with pytest.raises(ValidationError):
        ManualOmadaUser.parse_obj(raw_omada_user_manual)


def test_omada_pseudo_infinity(raw_omada_user: dict) -> None:
    """Test that Omada's 'pseudo-infinity' of 31/12/9999 is converted correctly."""
    raw_omada_user["VALIDTO"] = "9999-12-31T01:00:00+01:00"
    parsed = OmadaUser.parse_obj(raw_omada_user)
    assert parsed.valid_to is None
