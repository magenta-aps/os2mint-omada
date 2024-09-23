# Generated by ariadne-codegen on 2024-09-09 14:40
# Source: queries.graphql

from uuid import UUID

from .base_model import BaseModel


class DeleteItUser(BaseModel):
    ituser_delete: "DeleteItUserItuserDelete"


class DeleteItUserItuserDelete(BaseModel):
    uuid: UUID


DeleteItUser.update_forward_refs()
DeleteItUserItuserDelete.update_forward_refs()