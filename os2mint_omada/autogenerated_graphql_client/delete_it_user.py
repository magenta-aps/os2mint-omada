from uuid import UUID

from .base_model import BaseModel


class DeleteItUser(BaseModel):
    ituser_delete: "DeleteItUserItuserDelete"


class DeleteItUserItuserDelete(BaseModel):
    uuid: UUID


DeleteItUser.update_forward_refs()
DeleteItUserItuserDelete.update_forward_refs()
