from pydantic import BaseModel, ConfigDict


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
