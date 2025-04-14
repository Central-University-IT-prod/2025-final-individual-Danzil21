from uuid import UUID

from fastapi import HTTPException
from pydantic import BaseModel, Field, field_validator
from pydantic import NonNegativeInt


class AdvertiserResponse(BaseModel):
    advertiser_id: UUID = Field(alias="advertiser_id")
    name: str

    class Config:
        from_attributes = True
        populate_by_name = True
        use_enum_values = True


class AdvertiserUpsert(BaseModel):
    advertiser_id: UUID = Field(..., alias="advertiser_id")
    name: str = Field(
        ...,
        min_length=1,
        description="Название рекламодателя"
    )

    @field_validator("name", mode="before")
    def validate_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise HTTPException(
                status_code=422,
                detail="Название рекламодателя не может быть пустым или состоять только из пробелов"
            )
        return v

    model_config = {
        "populate_by_name": True,
    }


class MLScoreSchema(BaseModel):
    client_id: str
    advertiser_id: str
    score: NonNegativeInt

    class Config:
        from_attributes = True
