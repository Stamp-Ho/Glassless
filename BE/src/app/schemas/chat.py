from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    query: str = Field(min_length=1, max_length=500)
    region: str | None = Field(default=None, max_length=50)
    category: str | None = Field(default=None, max_length=100)


class LocationRef(BaseModel):
    id: int
    name: str
    category: str
    address: str | None


class ChatResponse(BaseModel):
    answer: str
    references: list[LocationRef]
