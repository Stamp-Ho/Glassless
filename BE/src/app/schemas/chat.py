from pydantic import BaseModel, Field, field_validator


class ChatRequest(BaseModel):
    query: str = Field(min_length=1, max_length=500)
    region: str | None = Field(default=None, max_length=50)
    category: str | None = Field(default=None, max_length=100)

    @field_validator("region", "category", mode="before")
    @classmethod
    def _normalize_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None


class LocationRef(BaseModel):
    id: int
    name: str
    category: str
    address: str | None


class ChatResponse(BaseModel):
    answer: str
    references: list[LocationRef]
    extracted_region: str | None = None
    extracted_category: str | None = None
    extraction_source: str | None = None
