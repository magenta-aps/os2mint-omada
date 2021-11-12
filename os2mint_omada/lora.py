# SPDX-FileCopyrightText: 2021 Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from uuid import UUID

from os2mint_omada.clients import lora_client
from os2mint_omada.config import settings


async def ensure_it_system(
    uuid: UUID, user_key: str, name: str, organisation_uuid: UUID
) -> UUID:
    """
    Ensure the required IT System exist in LoRa.

    Args:
        uuid: UUID of the IT System. This is required for idempotence.
        user_key: Short, unique key of the IT system.
        name: Name of the IT system.
        organisation_uuid: UUID of the organisation who will own the IT system. Should
         be the root organisation.

    Returns: The UUID of the (potentially created) IT system
    """
    # TODO: This should be handled by os2mo-init instead.
    validity = {
        "from": "1930-01-01",  # the beginning of the universe according to LoRa
        "to": "infinity",
    }
    r = await lora_client.put(
        url=f"{settings.lora_url}/organisation/itsystem/{uuid}",
        json={
            "attributter": {
                "itsystemegenskaber": [
                    {
                        "brugervendtnoegle": user_key,
                        "integrationsdata": "",
                        "itsystemnavn": name,
                        "virkning": validity,
                    }
                ]
            },
            "tilstande": {
                "itsystemgyldighed": [
                    {
                        "gyldighed": "Aktiv",
                        "virkning": validity,
                    }
                ]
            },
            "relationer": {
                "tilhoerer": [
                    {
                        "uuid": str(organisation_uuid),
                        "virkning": validity,
                    }
                ]
            },
        },
    )
    return UUID(r.json()["uuid"])
