# SPDX-FileCopyrightText: 2022 Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from _pytest.monkeypatch import MonkeyPatch

from os2mint_omada.config import OmadaSettings
from os2mint_omada.config import Settings


def test_nested_delimiter(
    monkeypatch: MonkeyPatch, omada_settings: OmadaSettings
) -> None:
    monkeypatch.setenv("MO__CLIENT_SECRET", "hunter2")
    settings = Settings(
        omada=omada_settings,
    )
    assert settings.mo.client_secret.get_secret_value() == "hunter2"
