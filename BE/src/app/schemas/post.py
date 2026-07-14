from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class PostCategory(str, Enum):
    chat = "잡담"
    review = "후기"
    question = "질문"
    recruiting = "구인"


class PostCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1, max_length=5000)
    password: str = Field(min_length=1, max_length=100)
    category: PostCategory
    location_id: int | None = Field(default=None, ge=1)
    region: str | None = Field(default=None, max_length=100)


class PostUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    content: str | None = Field(default=None, min_length=1, max_length=5000)
    password: str = Field(min_length=1, max_length=100)
    category: PostCategory | None = None
    location_id: int | None = Field(default=None, ge=1)


class PostDelete(BaseModel):
    password: str = Field(min_length=1, max_length=100)


class PostResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    content: str
    category: PostCategory
    location_id: int | None
    region: str | None
    created_at: datetime
    updated_at: datetime


class PostListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    content: str
    category: PostCategory
    location_id: int | None
    region: str | None
    created_at: datetime
    updated_at: datetime
