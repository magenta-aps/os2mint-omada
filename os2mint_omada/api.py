# SPDX-FileCopyrightText: 2021 Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
import asyncio
from uuid import UUID

from fastapi import APIRouter

from os2mint_omada import lora
from os2mint_omada import mo
from os2mint_omada import omada
from os2mint_omada import sync
from os2mint_omada.clients import model_client
from os2mint_omada.config import settings

router = APIRouter()


@router.post("/import/it-users")
async def import_it_users() -> str:
    """
    Import Omada IT users into MO.

    Returns: A greeting, if everything was successful.
    """
    # Set up the IT system and address classes in MO
    root_org = await mo.get_root_org()
    it_system_uuid = await lora.ensure_it_system(
        uuid=settings.it_system_uuid,
        user_key=settings.it_system_user_key,
        name=settings.it_system_name,
        organisation_uuid=root_org,
    )
    assert it_system_uuid == settings.it_system_uuid
    address_classes = asyncio.create_task(mo.ensure_address_classes(root_org=root_org))

    # Get user information from MO and Omada
    mo_it_bindings = asyncio.create_task(mo.get_it_bindings(it_system=it_system_uuid))
    mo_user_addresses = asyncio.create_task(mo.get_user_addresses())
    mo_engagements = asyncio.create_task(mo.get_engagements())
    omada_it_users = asyncio.create_task(
        omada.get_it_users(odata_url=settings.odata_url)
    )

    # Omada and MO users are linked through the 'TJENESTENR' field. However 'TJENESTENR'
    # is not set on the MO users directly, but on their engagement as the 'user_key',
    # so we need to link through that.
    service_number_to_person = {  # 'TJENESTENR' -> Person UUID
        e["user_key"]: UUID(e["person"]["uuid"]) for e in await mo_engagements
    }

    # Synchronise updated objects to MO
    updated_objects = sync.get_updated_mo_objects(
        mo_it_bindings=await mo_it_bindings,
        omada_it_users=await omada_it_users,
        mo_user_addresses=await mo_user_addresses,
        service_number_to_person=service_number_to_person,
        address_class_uuids=await address_classes,
        it_system_uuid=it_system_uuid,
    )
    async with model_client.context():
        await model_client.load_mo_objs(updated_objects)

    return "Have a nice day ^_^"
