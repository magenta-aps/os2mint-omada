# SPDX-FileCopyrightText: 2022 Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
# TODO
from os2mint_omada.sync.address import AddressSyncer


class FakeAddressSyncer(FakeSyncer, AddressSyncer)

async def test_ensure_addresses() -> None:
    AddressSyncer().ensure_addresses(

    )
