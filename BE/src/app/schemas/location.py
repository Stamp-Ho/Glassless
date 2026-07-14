from pydantic import BaseModel, ConfigDict, Field


class LocationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    region: str
    category: str
    content_type_id: int
    content_id: str
    name: str
    description: str | None
    address: str | None
    tel: str | None
    image_url: str | None
    mapx: float | None
    mapy: float | None
    raw_cat1: str | None
    raw_cat2: str | None
    raw_cat3: str | None
    rating_avg: float = 0.0
    rating_count: int = 0


class LocationRatingCreate(BaseModel):
    score: int = Field(ge=1, le=5)
    client_id: str = Field(min_length=8, max_length=100)


class LocationRatingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    location_id: int
    score: int
    client_id: str
    rating_avg: float = 0.0
    rating_count: int = 0
