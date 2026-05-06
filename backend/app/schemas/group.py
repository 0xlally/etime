"""Pydantic schemas for group MVP APIs."""
from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


GroupVisibility = Literal["private", "invite_code", "public"]
GroupRole = Literal["owner", "admin", "member"]
GroupMessageType = Literal["text", "status_share", "card_share", "system"]


class GroupCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    visibility: GroupVisibility = "invite_code"


class GroupUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    visibility: Optional[GroupVisibility] = None


class GroupJoin(BaseModel):
    invite_code: str = Field(..., min_length=8, max_length=32)


class GroupPublicRequestCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)


class GroupResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    owner_id: int
    invite_code: str
    visibility: str
    created_at: datetime
    updated_at: datetime
    member_count: int = 0
    my_role: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class GroupMemberResponse(BaseModel):
    id: int
    group_id: int
    user_id: int
    username: str
    role: str
    joined_at: datetime
    muted_until: Optional[datetime]
    is_active: bool


class GroupMessageCreate(BaseModel):
    message_type: GroupMessageType = "text"
    content: str = Field(..., min_length=1, max_length=1000)
    metadata_json: Optional[dict[str, Any]] = None

    @field_validator("message_type")
    @classmethod
    def only_text_for_generic_create(cls, value: str) -> str:
        if value != "text":
            raise ValueError("Only text messages can be created here")
        return value


class GroupCardShareCreate(BaseModel):
    content: Optional[str] = Field(None, max_length=1000)
    metadata_json: dict[str, Any] = Field(default_factory=dict)


class GroupMessageResponse(BaseModel):
    id: int
    group_id: int
    user_id: int
    username: str
    message_type: str
    content: str
    metadata_json: Optional[dict[str, Any]]
    created_at: datetime
    deleted_at: Optional[datetime]
