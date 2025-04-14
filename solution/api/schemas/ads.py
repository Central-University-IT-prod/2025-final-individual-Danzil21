from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field

class AdResponse(BaseModel):
    ad_id: UUID = Field(
        ...,
        alias="ad_id",
        description="Уникальный идентификатор объявления"
    )
    ad_title: str
    ad_text: str
    ad_photo_url: Optional[str]
    advertiser_id: UUID

    class Config:
        from_attributes = True
        populate_by_name = True


class AdClickRequest(BaseModel):
    client_id: UUID = Field(
        ...,
        description="UUID клиента, совершившего клик"
    )
