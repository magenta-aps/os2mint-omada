from uuid import UUID

from .base_model import BaseModel


class CreateAddress(BaseModel):
    address_create: "CreateAddressAddressCreate"


class CreateAddressAddressCreate(BaseModel):
    uuid: UUID


CreateAddress.update_forward_refs()
CreateAddressAddressCreate.update_forward_refs()
