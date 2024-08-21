# Generated by ariadne-codegen on 2024-08-21 16:34
# Source: queries.graphql

from uuid import UUID

from .base_model import BaseModel


class DeleteAddress(BaseModel):
    address_delete: "DeleteAddressAddressDelete"


class DeleteAddressAddressDelete(BaseModel):
    uuid: UUID


DeleteAddress.update_forward_refs()
DeleteAddressAddressDelete.update_forward_refs()
