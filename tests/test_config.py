# SPDX-FileCopyrightText: 2022 Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from _pytest.monkeypatch import MonkeyPatch

from os2mint_omada.config import OmadaSettings
from os2mint_omada.config import Settings


def test_nested_delimiter(
    monkeypatch: MonkeyPatch, omada_settings: OmadaSettings
) -> None:
    """Test that settings can be given through FOO__BAR__BAZ variables."""
    monkeypatch.setenv("MO__OIDC__CLIENT_SECRET", "hunter2")
    settings = Settings(
        omada=omada_settings,
    )
    assert settings.mo.oidc.client_secret == "hunter2"
