from uuid import UUID

from .base_model import BaseModel


class CreateItUser(BaseModel):
    ituser_create: "CreateItUserItuserCreate"


class CreateItUserItuserCreate(BaseModel):
    uuid: UUID


CreateItUser.update_forward_refs()
CreateItUserItuserCreate.update_forward_refs()
