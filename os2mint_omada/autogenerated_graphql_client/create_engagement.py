# Generated by ariadne-codegen on 2024-09-09 14:40
# Source: queries.graphql

from uuid import UUID

from .base_model import BaseModel


class CreateEngagement(BaseModel):
    engagement_create: "CreateEngagementEngagementCreate"


class CreateEngagementEngagementCreate(BaseModel):
    uuid: UUID


CreateEngagement.update_forward_refs()
CreateEngagementEngagementCreate.update_forward_refs()