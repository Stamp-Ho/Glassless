from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class CommentCreate(BaseModel):
    nickname: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=1, max_length=100)
    content: str = Field(min_length=1, max_length=2000)



class CommentUpdate(BaseModel):
    password: str = Field(min_length=1, max_length=100)
    content: str = Field(min_length=1, max_length=2000)

class CommentDelete(BaseModel):
    password: str = Field(min_length=1, max_length=100)


class CommentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    post_id: int
    nickname: str
    content: str
    created_at: datetime
    updated_at: datetime
